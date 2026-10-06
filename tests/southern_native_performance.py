#!/usr/bin/env python3
"""Controller-earned five-enemy Southern effects, UI and native pixel cadence.

Runs the complete engine, never a synthetic crowded save. Uses exact ROM/ELF
and authenticated controller SRAM provenance from southern_combat_tests.
"""
import argparse, hashlib, json, re
from pathlib import Path
from southern_combat_tests import SouthernCombat, OWNERS, ROOT, PLAY, PAUSE, SAVING
from southern_controls import SouthernControls

class SouthernPerformance(SouthernCombat):
    def display_camera(self):
        text=(self.out/'candidate-source-game.c').read_text();stride=int(re.search(r"#define CACHE_FIELDS (\d+)",text)[1]);page=int(bool(self.e.read(0x04000000,2)&16));addr=self.sym['cache_fields']+4*stride*page
        return self.e.read(addr+4*17),self.e.read(addr+4*18)
    expected_pixels=SouthernControls.expected_pixels
    pixel_case=SouthernControls.pixel_case
    def sample(self,previous):
        frame=self.get('frame');page=self.e.read(0x04000000,2)&16;cx,cy=self.display_camera();state=self.get('game_state');picker=self.get('quickparty_open');enemies=self.enemies()
        def visible(x,y):return cx-8<x<cx+248 and cy-8<y<cy+168
        def world(x,y):
            if not visible(x,y) or state in (3,4,7,8):return False
            sx,sy=x-8-cx,y-8-cy
            return not ((picker and sx+16>26 and sx<214 and sy+16>29 and sy<160) or (state==2 and sy+16>99) or (state==6 and sx+16>37 and sx<203 and sy+16>77 and sy<111))
        r=dict(hardware_frame=self.e.frame,game_frame=frame,update_delta=(frame-previous[0])&0xffffffff,page_flip=page!=previous[1],cycles=self.get('render_cycles'),camera=[cx,cy],obj_count=self.get('obj_count'),state=state,journal_tab=self.get('journal_tab'),live_enemies=sum(e['hp']>0 for e in enemies),visible_enemy_bodies=sum(e['hp']>0 and world(e['x'],e['y']) and (not e['flash'] or bool(frame&2)) for e in enemies),visible_hostile_shots=sum(bool(s['life'] and s['owner'] and world(s['x'],s['y'])) for s in self.shots()),player_arrows=sum(a['active'] for a in self.arrows()),southern_effect=self.get('southern_power_time'),southern_kind=self.get('southern_power_kind'),hp_q4=self.hp_q4(),keys=0)
        return r,(frame,page)
    def window(self,label,count,keys=None,require_combined=False):
        previous=(self.get('frame'),self.e.read(0x04000000,2)&16);trace=[];captures=[]
        for n in range(count):
            key=keys(n) if keys else 0;self.step(1,key);r,previous=self.sample(previous);r['keys']=key;trace.append(r)
            if r['player_arrows']==2 and r['southern_effect']>0 and r['visible_enemy_bodies']==5 and r['visible_hostile_shots'] and len(captures)<3:
                path=self.out/(label+'-combined-'+str(len(captures))+'.png');self.e.screenshot(path);captures.append(dict(path=str(path),**r))
        result=dict(case=label,hardware_frames=len(trace),game_updates=sum(r['update_delta'] for r in trace),page_flips=sum(r['page_flip'] for r in trace),maximum_cycles=max(r['cycles'] for r in trace),maximum_oam=max(r['obj_count'] for r in trace),maximum_visible_enemy_bodies=max(r['visible_enemy_bodies'] for r in trace),maximum_visible_hostile_shots=max(r['visible_hostile_shots'] for r in trace),simultaneous_five_bodies_two_arrows_new_effect_hostile_frames=sum(r['player_arrows']==2 and r['southern_effect']>0 and r['visible_enemy_bodies']==5 and r['visible_hostile_shots']>0 for r in trace),camera_positions=len({tuple(r['camera']) for r in trace}),captures=captures,trace=trace,timing_source='GBA hardware frame counter, real main-loop update counter and displayed Mode4 page, never host wall-clock FPS')
        self.frame_windows.append(result);self.report()
        self.check(all(r['update_delta']==1 and r['page_flip'] for r in trace) and result['maximum_cycles']<280896,label+' presents one update and page flip per actual hardware frame')
        self.check(result['maximum_oam']<=128,'native OAM is within128slots')
        if require_combined:self.check(bool(captures),label+' actually combines five visible enemy bodies, hostile projectile, two arrows and Southern effect')
        return result
    def gather(self,cmd):
        self.restore('candidate-town-source');self.equip_item(0,19);self.equip_item(1,34);self.equip_item(3,65);self.owned_select(OWNERS[cmd]);self.set_command(cmd);self.use('rest');self.ready();self.entry(22);self.entry(23)
        route=[];self.goto(272,190)
        for _ in range(420):
            if self.enemies()[0]['y']<=205:break
            self.step(1)
        route.append(self.row());self.goto(200,176)
        for _ in range(350):
            if self.enemies()[1]['x']>=180:break
            self.step(1)
        self.goto(216,176)
        for _ in range(200):
            if self.enemies()[1]['x']>=194:break
            self.step(1)
        route.append(self.row());self.goto(312,124);self.face(3);self.ready();route.append(self.row())
        self.check(self.get('game_state')==PLAY,'five-enemy stress setup uses natural pursuit without death or enemy injection')
        self.cases.append(dict(case='controller-five-enemy-gather-'+str(cmd),route=route,passed=True));self.snapshot('five-enemy-command-'+str(cmd),settle=False)
    def combat(self,cmd):
        self.gather(cmd);self.step(30)
        def keys(n):
            phase=n%140
            return 'A' if phase<24 or phase==48 else 'R' if phase==53 else 'LEFT' if 57<=phase<62 else 'RIGHT' if 67<=phase<72 else 0
        self.window('five-body-new-effect-'+str(cmd),180,keys,True)
    def cold_ui(self,kind=None):
        for kind in ([kind] if kind else ('town-journal','rest-save','field-journal')):
            self.restore('candidate-town-source')
            if kind=='field-journal':self.entry(31);self.goto(240,200);self.ready()
            if kind=='rest-save':self.approach('rest');keys=lambda i:'A' if i in (0,40,80,120) else 0;count=160
            else:
                schedule={0:'START',5:'A',10:'A',15:'A',20:'A',25:'A',30:'A',35:'A',65:'B'};keys=lambda i:schedule.get(i,0);count=95
            r=self.window('cold-'+kind,count,keys)
            if kind=='rest-save':self.check(any(x['state']==SAVING for x in r['trace']),'native save cadence contains actual SAVING state')
            else:self.check({x['journal_tab'] for x in r['trace'] if x['state']==PAUSE}==set(range(8)),'cold journal displays all eight real pages')
            self.settle();self.step(130)
            self.pixel_case('resume-'+kind)
            self.check(any(o['priority']==1 for o in self.oam()),'resumed world submits genuine actor OAM')
        self.coverage.append('native-cold-eight-journals-rest-save-full-viewport-resume')
    def companion_pixels(self):
        def tiled(raw):return b''.join(raw[(ty+y)*16+tx:(ty+y)*16+tx+8] for ty in (0,8) for tx in (0,8) for y in range(8))
        self.prepare(23,(240,224),1,False);self.step(1,'R');rows=[]
        for n in range(26):
            self.step(1);p=self.power();code=self.get('gfx_companion_frame');form=self.selected().form_id;direction=code%16//4;index=[25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94].index(form)
            casting=code>=32768
            ptr=self.sym['southern_creature_ability_frames']+((index*4+direction)*2+((code//65536)&1))*256 if casting else self.sym['southern_creature_direction_frames']+((index*4+direction)*4+code%4)*256
            actual=self.e.bytes(0x06014000+6400,256);expected=tiled(self.e.bytes(ptr,256));self.check(actual==expected,'actual selected Southern companion tile bytes match exact ROM pose')
            rows.append(dict(frame=self.e.frame,power=p,code=code,casting=casting,form=form,expected_sha256=hashlib.sha256(expected).hexdigest(),actual_sha256=hashlib.sha256(actual).hexdigest()))
        self.check(any(r['casting'] for r in rows) and not rows[-1]['casting'],'Southern cast animation recovers to ordinary locomotion')
        self.cases.append(dict(case='Leafbound-selected-pixels-and-recovery',trace=rows,passed=True))
    def run(self,only=None):
        self.boot();cases=[('combat-'+str(c),lambda c=c:self.combat(c)) for c in (38,42,30,24,32)] + [('cold-'+k,lambda k=k:self.cold_ui(k)) for k in ('town-journal','rest-save','field-journal')] + [('companion-pixels',self.companion_pixels)]
        selected=set(only.split(',')) if only else {n for n,_ in cases};assert selected<={n for n,_ in cases}
        for n,f in cases:
            if n in selected:self.run_case(n,f)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','elf','output','source-report','source-manifest'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+key,required=True)
    p.add_argument('--case');a=p.parse_args();r=SouthernPerformance(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_manifest,a.elf)
    try:r.run(a.case)
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
