#!/usr/bin/env python3
"""Earn the original Core ending from authenticated minimal C SRAM, using buttons.

This is a prerequisite producer, not final-chapter acceptance. It never imports
machine state or writes game RAM, and retains every failed attempt separately.
"""
from __future__ import annotations
import argparse
from collections import deque
import json
from pathlib import Path
import traceback
from covenants_journey import CovenantsJourney, C_INPUTS
from region_journey import ROOT, PLAY, DIALOG, DEAD, SAVING, EVENT_PENDING, digest
from return_journey import preserve_pinned_file

BASE = {'HOMURA': (1, 1, 0), 'MIDORI': (4, 2, 1),
        'FUURI': (7, 3, 2), 'KOHAKU': (10, 4, 3)}


class CorePrelude(CovenantsJourney):
    def report(self):
        super().report()
        report = json.loads((self.out/'covenants-journey.json').read_text())
        report.update(suite='covenants-core-prelude',
                      original_core=getattr(self, 'core_evidence', {}),
                      original_story_floor_changes=getattr(self, 'story_floors', []),
                      exported_snapshot=getattr(self, 'exported_snapshot', None))
        (self.out/'covenants-core-prelude.json').write_text(json.dumps(report, indent=2)+'\n')
        (self.out/'controller-inputs.json').write_text(json.dumps(self.inputs, indent=2)+'\n')

    def approach(self, tx, ty, radius):
        """Find a reachable interaction point without walking through an object."""
        blocked, width, height = self.mask()
        start = self.get('py')*width+self.get('px')
        queue, seen = deque([start]), {start}
        goal = None
        while queue:
            point = queue.popleft(); x, y = point%width, point//width
            if abs(x-tx)+abs(y-ty) <= radius:
                goal = x, y; break
            for dx, dy in ((0,-1),(-1,0),(1,0),(0,1)):
                nx, ny = x+dx, y+dy
                if 0<=nx<width and 0<=ny<height:
                    index = ny*width+nx
                    if index not in seen and not blocked[index]:
                        seen.add(index); queue.append(index)
        self.check(goal is not None, 'authored collision leaves reachable interaction approach')
        self.goto(*goal, radius=2)

    def original_select(self, companion):
        form, command, spirit = BASE[companion]
        if self.selected().form_id != form:
            self.owned_select(form)
        self.set_command(command)
        if not self.get('summoned'):
            self.tap('B'); self.settle()
        self.check(self.get('spirit') == spirit, 'original base companion supplies original power')

    def original_object(self, object_id):
        spec = next(o for o in self.campaign_rooms[self.get('room')]['objects'] if o['id'] == object_id)
        self.approach(*spec['at'], max(2, spec.get('range_manhattan',24)-8))
        before = self.get('room_flags')
        if spec.get('companion'):
            self.original_select(spec['companion']); self.ready()
        self.tap(spec.get('input','R')); self.settle()
        if spec.get('sets_flag'):
            bit = 1 << self.campaign['flags'][spec['sets_flag']]
            self.check(self.get('room_flags') == before|bit, object_id+': exactly its original puzzle flag earned')
        self.core_evidence['objects'].append({'id':object_id,'frame':self.e.frame,'room':self.get('room'),'flags':self.get('room_flags')})
        self.snapshot('object-'+object_id)

    def original_next(self, target):
        before = self.get('room')
        self.goto(120,48,radius=2)
        for _ in range(300):
            if self.get('room') != before: break
            self.step(1,'UP')
        self.settle(); self.step(24)
        self.check(self.get('room') == target, f'original north exit {before} reaches {target}')
        self.snapshot('room-'+str(target)+'-entry')

    def walk_toward(self, x, y, dodge=False):
        dx, dy = x-self.get('px'), y-self.get('py'); keys=[]
        if abs(dx)>1: keys.append('RIGHT' if dx>0 else 'LEFT')
        if abs(dy)>1: keys.append('DOWN' if dy>0 else 'UP')
        if dodge and not self.get('roll_cd') and keys: keys.append('SELECT')
        self.step(1, '+'.join(keys) if keys else 0)

    def boss_approach(self, distance):
        # The fixed Core floor has no intervening solids. Single hardware-frame
        # movement avoids two-frame waypoint oscillation under Q8 movement.
        x,y=self.get('boss_x'),self.get('boss_y')+distance
        for _ in range(120):
            if abs(x-self.get('px'))+abs(y-self.get('py'))<=4: return
            self.check(self.get('game_state')==PLAY, 'boss approach remains alive')
            self.walk_toward(x,y)
        raise AssertionError(('Core approach did not converge',self.status(),x,y))

    def wait_original_save(self):
        # Do not advance a reward dialogue while its ordinary save completes.
        for _ in range(1600):
            if self.get('game_state') not in (SAVING,EVENT_PENDING): break
            self.step(1)
        else: raise AssertionError('Original event/save exceeded bounded wait')
        self.check(not self.get('save_failed'), 'original bounded reward saves successfully')

    def original_boss(self):
        states, phases, damage = set(), set(), []
        last_hp = self.get('boss_hp'); swings=0; captured=set()
        self.core_evidence['boss_events']=[]
        self.core_evidence['boss']={'states':[],'phases':[],'damage':damage,'sword_swings':0,'end_hp':self.get('hp')}
        for _ in range(24000):
            if self.get('game_state') in (SAVING,EVENT_PENDING):
                # Keep the earned release dialogue visible after the bounded
                # event/save job, so original reward and ending stay separate.
                self.wait_original_save()
            if self.get('game_state')==DIALOG or self.get('room')!=13: break
            self.check(self.get('game_state') == PLAY, 'original Core boss remains live gameplay')
            state, phase = self.get('boss_state'), self.get('boss_phase')
            states.add(state); phases.add(phase)
            self.core_evidence['boss'].update(states=sorted(states),phases=sorted(phases),sword_swings=swings,end_hp=self.get('hp'))
            hp = self.get('boss_hp')
            if hp != last_hp:
                damage.append({'before':last_hp,'after':hp,'phase':phase,'frame':self.e.frame}); last_hp=hp
            if (phase,state) not in captured:
                captured.add((phase,state)); self.e.screenshot(self.out/f'boss-phase{phase}-state{state}.png')
                self.core_evidence['boss_events'].append({'frame':self.e.frame,'state':state,'phase':phase,'boss_hp':hp,'hero_hp':self.get('hp')})
            if state==4:
                self.boss_approach(42)
                self.original_select(('KOHAKU','FUURI','HOMURA')[phase]); self.ready()
                if self.get('boss_state')==4: self.tap('R')
            elif state==5:
                if not self.get('combo_timer') and not self.get('sword_cd'):
                    self.boss_approach(30)
                    self.step(1,'UP'); self.tap('A'); swings += 1
                else: self.step(2)
            else:
                self.walk_toward(96 if phase==1 else 120,112,
                    dodge=phase==1 and state==0 and self.get('boss_state_ticks')>=34)
            if self.get('hp')<=0:
                self.core_evidence['deaths'].append({'frame':self.e.frame,'status':self.status()})
                self.snapshot('death-'+str(len(self.core_evidence['deaths'])),settle=False)
                raise AssertionError('Original Core route died; evidence retained')
        if self.get('boss_hp')!=last_hp:
            damage.append({'before':last_hp,'after':self.get('boss_hp'),'phase':self.get('boss_phase'),'frame':self.e.frame})
        self.core_evidence['boss']={'states':sorted(states),'phases':sorted(phases),'damage':damage,'sword_swings':swings,'end_hp':self.get('hp')}
        self.check(self.get('boss_hp')==0, 'original Core defeated using starter sword and base companions')
        self.check(phases=={0,1,2}, 'original Core traverses all three phases')
        self.check({16,8}<={row['after'] for row in damage}, 'original Core stops at both authored phase thresholds')
        self.check(self.get('chapter_flags')==7, 'Core clear earned before ending seen')
        self.settle(); self.check(self.get('room')==0, 'Core release dialogue returns to village')
        self.snapshot('core-clear-ending-pending')

    def run_prelude(self):
        self.core_evidence={'objects':[],'deaths':[],'retries':0}
        ancestry={}
        for relative in (self.provenance['fixture_path'],self.provenance['producer_path'],
                         'tests/fixtures/v5-revision8/provenance.json'):
            source=self.prior_root/relative; destination=self.out/'current-c-source'/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            preserve_pinned_file(source,destination,digest(source)); ancestry[relative]=digest(destination)
        self.core_evidence['accepted_C_source_closure']=ancestry
        self.boot()
        self.check(self.minimal and self.get('chapter_flags')==3, 'minimal C begins with only Grove and Sky complete')
        self.check(self.get('max_hp')==6 and not self.get('relic_found') and not self.get('optional_flags'), 'original prelude begins on six-heart route without optional relic or chime')
        self.check(self.quest(57)==3, 'source C has genuinely completed Horizons main story')
        before={c.instance_id:{'form':c.form_id,'level':c.level,'bond':c.bond,'flags':c.flags} for c in self.live()}
        self.travel(0)
        for slot, form in enumerate((1,4,7,10)): self.assign(slot,form)
        self.main_only=True
        self.goto(120,128); self.goto(80,128); self.tap('A'); self.settle(); self.step(24)
        self.check(self.get('room')==9, 'village western marker enters original Core path')
        self.snapshot('core-path-entry')
        for index, objects in enumerate((('slope_rest','cracked_arch'),('west_weight','east_weight'),
                ('well_cap','dry_well','dry_thorns'),('fire_lamp','nature_lamp','wind_lamp','stone_lamp','last_rest'))):
            for object_id in objects: self.original_object(object_id)
            self.original_next(10+index)
        self.original_boss()
        self.goto(120,116); self.tap('A'); self.wait_original_save()
        self.check(self.get('game_state')==DIALOG, 'elder offers original final celebration')
        self.settle()
        self.check(self.get('game_state')==5 and self.get('chapter_flags')==15, 'original ending card and persistent ending bit earned')
        self.snapshot('original-ending-card',settle=False)
        self.tap('START'); self.settle()
        self.check(self.get('game_state')==PLAY and self.get('room')==0, 'Start returns from original ending to playable village')
        self.main_only=False
        self.story_floors=[{'instance_id':c.instance_id,'before':before[c.instance_id],
            'after':{'form':c.form_id,'level':c.level,'bond':c.bond,'flags':c.flags},
            'source':'ordinary original Core reward: creatures_apply_story_floors, not a Covenants grant'}
            for c in self.live() if before[c.instance_id]!={'form':c.form_id,'level':c.level,'bond':c.bond,'flags':c.flags}]
        self.check(len(self.live())==18 and self.collection()==self.old_history, 'Core prelude adds no recruit, evolution, or obtained form')
        self.check(self.old_ids=={c.instance_id for c in self.live()}, 'all eighteen original identities remain exact')
        self.check(bytes(self.state().equipment)==self.old_gear, 'Core prelude retains exact starter equipment and inventory')
        self.check(set(self.main_selections)<={1,4,7,10}, 'original Core uses only four guaranteed base companions')
        self.check(all(not self.quest(q) and not self.state().quests.objectives[q] for q in range(60,64)), 'original ending earns no final-chapter quest or objective')
        self.check(not any(self.state().quests.region_flags[x] for x in (7,22,23)) and not self.state().quests.anchors[7], 'Core prelude earns no Covenants visit, rights, invitations, or anchors')
        campaign_fields=('chapter_flags','room_flags','optional_flags','story_seen','max_hp','relic_found')
        self.core_evidence['campaign_before_cold']={field:self.get(field) for field in campaign_fields}
        self.cold_reboot('original-ending-cold')
        self.check(self.get('chapter_flags')==15 and self.get('game_state')==PLAY, 'ordinary cold reload retains original ending and playable state')
        self.core_evidence['campaign_after_cold']={field:self.get(field) for field in campaign_fields}
        self.check(self.core_evidence['campaign_before_cold']==self.core_evidence['campaign_after_cold'], 'cold reload retains every original puzzle, story, and optional-progress field exactly')
        self.exported_snapshot='original-ending-cold-after'
        self.finished_scope='core-ending'; self.verify_closures()
        self.check(all(digest(self.out/'current-c-source'/relative)==sha for relative,sha in ancestry.items()), 'authenticated C producer, provenance, and SRAM closure remain exact')
        self.report()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--prior-root',type=Path,default=ROOT)
    parser.add_argument('--fixture-kind',choices=('minimal-stage','minimal-water'),default='minimal-stage')
    args=parser.parse_args(); frozen=args.frozen_root.resolve(); pins=json.loads((frozen/'run-status.json').read_text())['candidate']
    assert not args.output.exists(), 'Use a fresh prelude output; never overwrite failed evidence'
    run=CorePrelude(frozen/'candidate/emberbond.gba',frozen/'candidate/emberbond.sym',args.output,
        pins['emberbond.gba'],pins['emberbond.sym'],pins['emberbond.elf'],frozen/'candidate/source-hashes.json',
        pins['source-hashes.json'],source_root=frozen/'runtime-source',prior_root=args.prior_root,
        fixture_kind=args.fixture_kind,timing_mode='strict')
    try: run.run_prelude()
    except Exception as error:
        if run.get('game_state')==DEAD and not run.core_evidence['deaths']:
            run.core_evidence['deaths'].append({'frame':run.e.frame,'status':run.status(),'during':'helper action'})
        run.failures.append({'error':str(error),'traceback':traceback.format_exc(),'status':run.status()})
        run.snapshot('failure',settle=False); raise
    finally: run.close_global_trace(); run.report(); run.e.close()
    return bool(run.failures)

if __name__=='__main__': raise SystemExit(main())
