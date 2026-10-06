#!/usr/bin/env python3
"""Controller-only native-ROM companion/trial journey.

No game RAM writes. The ROM and symbols are copied and hashed before testing;
all state branches pair the machine state with SRAM. A supplied SRAM migration
fixture is input data, never evidence that a collection/evolution was obtained.
Use --rom and --symbols from the same immutable candidate.
"""
from __future__ import annotations
import argparse
from collections import deque
import ctypes as C
import hashlib
import json
import struct
from pathlib import Path
import sys
from campaign_tests import CampaignRun, PLAY, DIALOG, PAUSE, ROOT
from test_creatures import Roster
from test_save4 import CampaignSave

SAVE_PENDING, EVOLVE_CONFIRM, EVOLVE_ANIM = 6, 7, 8
ENABLED = {1, 2, 4, 5, 7, 8, 10, 11}
BASE = (1, 4, 7, 10)
EVOLVED = (2, 5, 8, 11)
AIDS = ((184,280,0),(296,208,0),(320,72,0),(80,136,1),(400,136,1),(304,280,1))

class NativeSave(C.Structure):
    _fields_ = [('campaign', CampaignSave), ('roster', Roster)]

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class EvolutionRun(CampaignRun):
    def __init__(self, rom, symbols, output, optional=True, exhaustive=False):
        super().__init__(rom, symbols, output, optional, exhaustive)
        self.save_checks = []
        self.auto_save = True
        self.manual_save_control = True
        self.world_solids = json.loads((ROOT/'assets/world_manifest.json').read_text())['static_collision_rectangles']
        self.candidate = {'rom_sha256': digest(self.rom), 'symbols_sha256': digest(self.symbol_path),
                          'rom_bytes': self.rom.stat().st_size}
        (self.out/'candidate.json').write_text(json.dumps(self.candidate,indent=2)+'\n')

    def raw_step(self, count, keys=0):
        super().step(count, keys)
        if self.get('room') == 1:
            assert 0 <= self.get('camera_x') <= 240 and 0 <= self.get('camera_y') <= 160, self.status()

    def step(self, count, keys=0):
        self.raw_step(count, keys)
        # Continue decoding is a documented blocking load, not a steady-game
        # frame. Wait for it explicitly before measuring incremental writes.
        if self.auto_save:
            for _ in range(180):
                if not (self.get('game_state')==PLAY and self.get('frame')==0):break
                self.raw_step(1,0)
            else:raise AssertionError('Cold Continue did not finish')
        if self.auto_save and self.get('game_state') == SAVE_PENDING:
            self.settle_save()

    def settle_save(self, intrusive=False):
        if self.get('game_state') != SAVE_PENDING:
            return
        fields = ('room','px','py','hp','ability_cd','heal_cd','boss_hp','boss_armor','dpage')
        frozen = {n:self.get(n) for n in fields if self.has(n)}
        initial = self.e.frame
        deltas, flips, cycles = [], [], []
        frame = self.get('frame'); page = self.e.read(0x04000000,2)&16
        for _ in range(180):
            if self.get('game_state') != SAVE_PENDING:
                break
            self.raw_step(1,'A+R+RIGHT+START+SELECT' if intrusive else 0)
            current = self.get('frame'); newpage = self.e.read(0x04000000,2)&16
            deltas.append((current-frame)&0xffffffff); flips.append(page != newpage)
            cycles.append(self.get('render_cycles')); frame,page=current,newpage
            assert all(self.get(n)==v for n,v in frozen.items()), ('save failed to freeze gameplay',frozen,self.status())
        else:
            self.check(False,'transactional save terminates within 180 hardware frames')
        self.raw_step(1,0)
        cold_prefix=0
        if getattr(self,'loading_checkpoint',False):
            while cold_prefix<len(deltas) and deltas[cold_prefix]==0 and not flips[cold_prefix]:cold_prefix+=1
        self.save_checks.append({'cold_load_overlap_samples':cold_prefix,'steady_max_cycles':max(cycles[cold_prefix:],default=0),'start_frame':initial,'frames':len(deltas),'simulation_deltas':deltas,
                                 'display_flips':sum(flips),'max_cycles':max(cycles,default=0),
                                 'input_stress':intrusive,'frozen_fields':frozen,
                                 'resume_state':self.get('game_state')})
        self.check(not self.get('save_failed'),'transactional save completes without failure')
        self.check(bool(deltas[cold_prefix:]) and all(d==1 for d in deltas[cold_prefix:]) and all(flips[cold_prefix:]),'transactional save writer updates and presents every native59.73Hz frame after any documented cold-load overlap')

    def reopen(self,save):
        self.loading_checkpoint=True
        try:return super().reopen(save)
        finally:self.loading_checkpoint=False

    def roster(self):
        return Roster.from_buffer_copy(self.e.bytes(self.sym['adventure_save']+NativeSave.roster.offset,C.sizeof(Roster)))

    def instance(self, family):
        matches=[c for c in self.roster().instances if c.flags&1 and c.form_id in (BASE[family],EVOLVED[family])]
        assert len(matches)==1, (family,[c.form_id for c in self.roster().instances if c.flags&1])
        return matches[0]

    def roster_contract(self):
        r=self.roster(); forms=[c.form_id for c in r.instances if c.flags&1]
        self.check(set(forms)<=ENABLED,'no reserved form appears in the living roster')
        self.check(len(forms)==len(set(forms)),'story companion instances are not duplicated')
        self.check(all(i==255 or (i<160 and r.instances[i].flags&1) for i in r.party),'party entries reference obtained instances')
        return forms

    def snapshot(self,name):
        path=super().snapshot(name)
        self.snapshots[name].update({'state_sha256':digest(path),'sram_sha256':digest(path.with_suffix('.state.sav')),
                                    'candidate':getattr(self,'candidate',{}),
                                    'progression_forms':[self.e.read(self.sym['progression_forms']+i*4) for i in range(4)]})
        return path

    def dialogs(self,reward=None):
        self.settle_save()
        return super().dialogs(reward)

    def valid_point(self,room,x,y,margin=5,exits=False):
        if room==1:
            if not (12<=x<468 and 24<=y<308):return False
            for rect in self.world_solids:
                if isinstance(rect,dict):rect=rect.get('rect',rect.get('bounds'))
                a,b,w,h=rect
                if a<=x<a+w and b<=y<b+h:return False
            return not (156<=y<176 and (not self.get('bridge_open') or not 228<=x<252))
        if room in (14,15):
            if not (12<=x<228 and 44<=y<148):return False
            if room==15:
                for i in range(2):
                    a=self.e.read(self.sym['trial_parcels']+i*4,2);b=self.e.read(self.sym['trial_parcels']+i*4+2,2)
                    if abs(x-a)<12 and abs(y-b)<12:return False
            return True
        return super().valid_point(room,x,y,margin,exits)

    def navigate(self,x,y,radius=2,exits=False):
        room=self.get('room')
        radius=max(radius,2) # A2px route grid must admit both coordinate parities
        if room not in (1,14,15):return super().navigate(x,y,radius,exits)
        start=self.get('px'),self.get('py'); queue=deque([start]);prior={start:None};found=None
        while queue:
            p=queue.popleft()
            if abs(p[0]-x)+abs(p[1]-y)<=radius:found=p;break
            for dx,dy in ((0,-2),(-2,0),(2,0),(0,2)):
                q=p[0]+dx,p[1]+dy
                if q not in prior and self.valid_point(room,*q,exits=exits):prior[q]=p;queue.append(q)
        assert found is not None, ('no controller route',room,start,(x,y),self.status())
        path=[]
        while found!=start:path.append(found);found=prior[found]
        last=start;direction=None
        for p in reversed(path):
            d=p[0]-last[0],p[1]-last[1]
            if direction is not None and d!=direction:self.goto(*last)
            direction,last=d,p
        self.goto(*last)

    def growth(self,family):
        if self.get('game_state')==PLAY:self.tap('START')
        self.check(self.get('game_state')==PAUSE,'Start opens journal for companion growth')
        for _ in range(7):
            if self.get('journal_tab')==3:break
            self.tap('A')
        self.check(self.get('journal_tab')==3,'growth is the fourth journal tab')
        for _ in range(4):
            if self.get('spirit')==family:break
            self.tap('L')
        self.check(self.get('spirit')==family,'growth L selects requested companion')

    def evolve(self,family):
        self.growth(family);before=bytes(self.instance(family))
        self.shot(f'growth-{family}-ready');self.snapshot(f'evolution-{family}-ready')
        self.tap('SELECT');self.check(self.get('game_state')==EVOLVE_CONFIRM,f'family {family}: eligible Select opens confirmation')
        self.shot(f'evolution-{family}-confirmation');self.tap('B')
        self.check(self.get('game_state')==PAUSE and bytes(self.instance(family))==before,f'family {family}: decline leaves every instance byte unchanged')
        self.tap('SELECT');self.tap('A')
        self.check(self.get('game_state')==EVOLVE_ANIM,f'family {family}: explicit confirmation starts animation')
        self.shot(f'evolution-{family}-before')
        tick=self.get('frame');page=self.e.read(0x04000000,2)&16;deltas=[];flips=[];cycles=[]
        for i in range(120):
            if self.get('game_state')!=EVOLVE_ANIM:break
            self.raw_step(1)
            now=self.get('frame');shown=self.e.read(0x04000000,2)&16
            deltas.append((now-tick)&0xffffffff);flips.append(shown!=page);cycles.append(self.get('render_cycles'));tick,page=now,shown
            if i==40:self.shot(f'evolution-{family}-after')
        self.settle_save();self.step(2)
        self.check(bool(deltas) and all(d==1 for d in deltas) and all(flips),f'family {family}: evolution animation updates and presents each native59.73Hz frame')
        self.scenes.append({'scene':f'evolution-{family}-animation','hardware_frames':len(deltas),'simulation_updates':sum(deltas),'display_flips':sum(flips),'maximum_cycles':max(cycles)})
        self.check(self.get('game_state')==PAUSE,f'family {family}: animation returns to paused journal after save')
        c=self.instance(family);old=type(c).from_buffer_copy(before)
        self.check(c.form_id==EVOLVED[family],f'family {family}: obtains its authored evolved form')
        self.check((c.instance_id,c.xp,c.bond,c.trial_flags,c.cosmetic_seed)==(old.instance_id,old.xp,old.bond,old.trial_flags,old.cosmetic_seed),f'family {family}: evolution preserves personal identity and earned progression')
        self.check(c.equipped[c.selected_command]==family+1,f'family {family}: evolution keeps the previously equipped original command')
        self.tap('R');c=self.instance(family)
        self.check(c.equipped[c.selected_command]==family+5,f'family {family}: journal R equips newly learned evolved command')
        self.tap('R');c=self.instance(family)
        self.check(c.equipped[c.selected_command]==family+1,f'family {family}: journal R selects original command')
        self.tap('R');c=self.instance(family)
        self.check(c.equipped[c.selected_command]==family+5,f'family {family}: journal R restores evolved command')
        self.save_interruption_case(family)
        self.tap('B');self.reload_roster(f'evolved-{family}');self.snapshot(f'evolved-{family}')

    def save_interruption_case(self,family):
        """Power-loss copies at every actual hardware-frame writer boundary."""
        original=self.snapshot(f'command-{family}-before-interruption')
        before=bytes(self.instance(family));legacy=self.e.bytes(0x0e000000,512)
        self.auto_save=False;self.tap('R',1,1)
        after=bytes(self.instance(family));self.check(before!=after,'controller command change creates a real save transaction')
        frozen={n:self.get(n) for n in ('px','py','hp','ability_cd','heal_cd','dpage')}
        samples=[]
        for i in range(180):
            samples.append(self.save(f'command-{family}-power-cut-{i:02d}'))
            if self.get('game_state')!=SAVE_PENDING:break
            self.raw_step(1,'A+RIGHT+R+SELECT+START')
            self.check(all(self.get(n)==v for n,v in frozen.items()),f'command {family} write tick{i}: mixed inputs cannot change gameplay or dialogue')
        else:self.check(False,'command save finishes')
        self.raw_step(1);self.auto_save=True
        self.check(self.e.bytes(0x0e000000,512)==legacy,'save5 transaction preserves every legacy SRAM byte')
        complete=self.snapshot(f'command-{family}-after-interruption')
        recovered=[]
        for i,path in enumerate(samples):
            self.reopen(path);self.dialogs();c=bytes(self.instance(family))
            self.check(c in (before,after),f'command {family} power-cut tick{i}: reboot sees only old or complete new instance')
            recovered.append({'frame_offset':i,'sha256':digest(path),'new':c==after})
        self.check(recovered[-1]['new'],'committed transaction becomes visible after independent reboot')
        self.observations[f'command_{family}_interruption']=recovered
        self.restore(original) # Continue with the advanced command selected.

    def partial_optional_reload(self,name,family):
        state=self.snapshot(name+'-partial');r=self.roster();save=self.save(name+'-partial')
        self.reopen(save);self.dialogs()
        self.check(self.get('room')==0,name+': optional-room checkpoint normalizes to safe village on reboot')
        after=self.roster();r.selected_party=after.selected_party # L selection since last checkpoint is not itself a save
        self.check(bytes(after)==bytes(r) and not self.instance(family).trial_flags&(1<<family),name+': partial puzzle cannot grant trial or growth on reload')
        self.restore(state)

    def reload_roster(self,name):
        self.settle_save();state=self.snapshot(name+'-before-reload');before=bytes(self.roster());save=self.save(name)
        self.reopen(save);self.dialogs()
        self.check(bytes(self.roster())==before,name+': independent SRAM reload preserves complete roster')
        self.check(self.get('loaded_save_version')==5,name+': independently reopens save5')
        self.restore(state)

    def grove_trials(self):
        self.nextroom(1)
        for i,(x,y,family) in enumerate(AIDS):
            self.navigate(x,y,radius=16);self.select(1-family);self.ready();before=bytes(self.roster());self.tap('R')
            self.check(bytes(self.roster())==before,f'grove aid {i}: wrong family awards nothing')
            self.select(family);self.ready();self.tap('R');self.dialogs()
            self.check(self.roster().lifetime_field_aid[0]&(1<<i),f'grove aid {i}: correct controller power restores object')
            self.reload_roster(f'grove-aid-{i}')
            c=self.instance(family);kills=self.get('kills');ledger=self.roster().lifetime_field_aid[0]
            self.ready();self.tap('R');self.dialogs();after=self.instance(family)
            combat_kills=self.get('kills')-kills
            self.check(after.trial_flags==c.trial_flags and self.roster().lifetime_field_aid[0]==ledger and 0<=after.xp-c.xp<=60*combat_kills,
                       f'grove aid {i}: repeat awards no trial/aid progress beyond legitimate encounter XP')
            self.shot(f'grove-trial-aid-{i}')
        for family in (0,1):self.check(self.instance(family).trial_flags&(1<<family),f'family {family}: three aid objects complete personal trial')
        self.navigate(240,292);self.nextroom(0,'DOWN')

    def enter_optional(self,room):
        self.hub(4 if room==14 else 9)
        self.navigate(204,64,radius=10) if room==14 else self.navigate(208,120,radius=10)
        self.tap('A');self.dialogs()
        self.check(self.get('room')==room,f'controller discovers optional room {room}')
        self.snapshot(f'trial-{room}-entry');self.shot(f'trial-{room}-entry')

    def leave_optional(self,target):
        self.navigate(120,136);self.nextroom(target,'DOWN')
        if self.get('py')>136:self.goto(y=134) # Leave the authored return landing before BFS's no-exit margin
        self.nextroom(0,'DOWN')

    def wind_trial(self):
        self.enter_optional(14);self.select(2);self.navigate(88,80,radius=1);self.ready();self.tap('R')
        self.check(self.e.bytes(self.sym['trial_vanes'],3)==bytes((1,0,0)),'wind trial first controller pulse rotates only nearest vane')
        self.partial_optional_reload('wind-loom',2)
        self.navigate(32,120,radius=4);self.tap('A')
        self.check(self.e.bytes(self.sym['trial_vanes'],3)==bytes(3),'wind trial reset clears partial orientation')
        for x,y,n in ((88,80,2),(88,128,1)):
            self.navigate(x,y,radius=1)
            for _ in range(n):self.ready();self.tap('R');self.dialogs()
        self.check(self.e.bytes(self.sym['trial_vanes'],3)==bytes((2,1,0)),'wind loom reaches authored solved orientations')
        self.check(self.instance(2).trial_flags&4,'wind loom grants Fuuri personal trial')
        before=bytes(self.instance(2));self.ready();self.tap('R')
        self.check(bytes(self.instance(2))==before,'completed wind trial is idempotent')
        self.reload_roster('wind-trial-complete');self.shot('wind-trial-complete');self.leave_optional(4)

    def stone_trial(self):
        self.enter_optional(15);self.select(3);self.navigate(200,80,radius=1);self.ready();before=bytes(self.roster());self.tap('R')
        self.check(bytes(self.roster())==before,'amber arch refuses power before both parcels reach plates')
        self.navigate(88,104,radius=1);self.step(1,'UP');self.step(1);self.tap('A')
        self.partial_optional_reload('amber-workshop',3)
        self.navigate(32,120,radius=4);self.tap('A')
        self.check([self.e.read(self.sym['trial_parcels']+i*2,2) for i in range(4)]==[88,88,136,88],'amber reset restores original parcel positions')
        # A parcel moves one grid cell per press, with actual collision detours.
        for x,y,face in ((88,104,'UP'),(88,88,'UP'),(120,88,'RIGHT'),(152,72,'DOWN')):
            self.navigate(x,y,radius=1);self.step(1,face);self.step(1);self.tap('A')
        parcels=[self.e.read(self.sym['trial_parcels']+i*2,2) for i in range(4)]
        self.check(parcels==[88,56,152,104],'both controller-pushed parcels occupy distinct plates')
        self.navigate(200,80,radius=1);self.ready();self.tap('R');self.dialogs()
        self.check(self.instance(3).trial_flags&8,'amber arch grants Kohaku personal trial')
        before=bytes(self.instance(3));self.ready();self.tap('R')
        self.check(bytes(self.instance(3))==before,'completed amber trial is idempotent')
        self.reload_roster('stone-trial-complete');self.shot('stone-trial-complete');self.leave_optional(9)

    def ending_card_case(self):
        """Internal spoiler-bearing regression: final actors match owned forms."""
        base=self.snapshot('before-evolved-ending-card');roster=bytes(self.roster())
        self.goto(y=116);self.goto(x=120);self.tap('A');self.dialogs('evolved-ending')
        for replay in range(2):
            self.check(self.get('game_state')==5 and self.get('chapter_flags')&8,'evolved ending reaches the committed final card')
            self.step(4);raw=self.e.bytes(0x07000000,1024);shown=[]
            for i in range(128):
                a0,a1,a2,_=struct.unpack_from('<HHHH',raw,i*8)
                if a0&0x300==0x200:continue
                shown.append((a1&511,a0&255,a2&1023))
            for family in range(4):
                form=self.instance(family).form_id
                self.check(form==EVOLVED[family],f'ending actor {family}: branch still owns evolved form')
                rowmajor=self.e.bytes(self.sym['evolution_companion_direction_frames']+family*4096,256)
                tiled=bytes(rowmajor[(ty+y)*16+tx+x] for ty in (0,8) for tx in (0,8) for y in range(8) for x in range(8))
                offset=12352+family*256;actual=self.e.bytes(0x06014000+offset,256)
                self.check(actual==tiled,f'ending replay{replay} actor{family}: VRAM exactly matches owned evolved idle sprite')
                self.check((91+family*20,100,512+offset//32) in shown,f'ending replay{replay} actor{family}: correct sprite is actually presented in OAM')
            self.shot(f'internal-evolved-ending-{replay}')
            self.check(bytes(self.roster())==roster,'ending and replay preserve every creature instance and collection record')
            self.tap('START');self.check(self.get('game_state')==PLAY and self.get('room')==0,'evolved final card returns to village')
            if replay==0:self.tap('START');self.tap('R');self.dialogs('evolved-ending-replay')
        self.restore(base)

    def run(self):
        self.first_chapter();self.roster_contract();self.grove_trials();self.evolve(0);self.evolve(1)
        self.chapter_two();self.wind_trial();self.evolve(2)
        self.chapter_three();self.stone_trial();self.evolve(3)
        r=self.roster();obtained={i+1 for i in range(128) if r.obtained[i//8]&(1<<(i%8))}
        self.check(obtained==ENABLED,'real controller journey obtains exactly all eight enabled forms')
        self.check(set(self.roster_contract())==set(EVOLVED),'four personally evolved companions form the final party')
        self.snapshot('all-evolved-village');self.save('all-evolved-checkpoint');self.ending_card_case();self.report()

    def run_migrated(self,source,source_report):
        """Continue an authentic old-build checkpoint, then earn every evolution."""
        source=Path(source).resolve();report_path=Path(source_report).resolve();evidence=json.loads(report_path.read_text())
        self.check(evidence.get('controller_only') is True and not evidence.get('failures'),'migration fixture originates in a passing controller-only prior-build run')
        matches=[v for v in evidence.get('snapshots',{}).values() if v.get('sram_path') and ((Path(v['sram_path']) if Path(v['sram_path']).is_absolute() else report_path.parent/Path(v['sram_path'])).resolve()==source)]
        self.check(bool(matches),'migration fixture is paired with a documented prior-build machine state')
        if matches[0].get('sram_sha256'):self.check(digest(source)==matches[0]['sram_sha256'],'portable migration fixture matches its pinned controller-produced SRAM hash')
        original=source.read_bytes()
        self.observations['migration_source']={'path':str(source),'sha256':digest(source),'report':str(report_path),'report_sha256':digest(report_path),
            'prior_rom_sha256':evidence['rom_sha256'],'provenance':'actual prior-ROM controller route, unchanged SRAM input; no injected collection'}
        self.reopen(source);self.dialogs()
        self.check(self.get('loaded_save_version')==4 and self.get('chapter_flags')&7==7,'authentic save4 campaign resumes all earned chapters')
        self.check(set(self.roster_contract())==set(BASE),'save4 migration synthesizes exactly the four earned original companions')
        self.check(self.e.bytes(0x0e000000,512)==original[:512],'first save5 write preserves every original legacy bank byte')
        self.grove_trials();self.evolve(0);self.evolve(1);self.wind_trial();self.evolve(2);self.stone_trial();self.evolve(3)
        r=self.roster();obtained={i+1 for i in range(128) if r.obtained[i//8]&(1<<(i%8))}
        self.check(obtained==ENABLED,'migrated campaign independently earns exactly all eight forms through controller trials/evolutions')
        self.check(digest(source)==self.observations['migration_source']['sha256'],'migration never rewrites authentic source input')
        self.snapshot('all-evolved-village');self.save('all-evolved-checkpoint');self.ending_card_case();self.report()

    def report(self):
        super().report()
        base=json.loads((self.out/'campaign-report.json').read_text())
        base.update({'suite':'evolution-and-trial-controller-journey','save_pending_checks':getattr(self,'save_checks',[]),
                     'candidate':getattr(self,'candidate',{}),'fixture_policy':'controller evidence only; no synthetic roster or game RAM injection'})
        (self.out/'evolution-report.json').write_text(json.dumps(base,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'build/evolution-qa');p.add_argument('--six-hearts',action='store_true');p.add_argument('--legacy-save',type=Path);p.add_argument('--legacy-report',type=Path)
    a=p.parse_args();r=EvolutionRun(a.rom,a.symbols,a.output,not a.six_hearts)
    try:
        if a.legacy_save:
            if not a.legacy_report:p.error('--legacy-save requires --legacy-report provenance')
            r.run_migrated(a.legacy_save,a.legacy_report)
        else:r.run()
    except Exception as exc:
        r.failures.append({'error':str(exc),'status':r.status()});r.shot('failure');raise
    finally:r.report();r.e.close()
    return int(bool(r.failures))

if __name__=='__main__':raise SystemExit(main())
