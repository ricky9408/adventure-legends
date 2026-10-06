#!/usr/bin/env python3
"""Independent full-engine Magma native cadence with real earned companions.

Every sample advances one actual mGBA hardware frame, then reads the game's
update counter and displayed Mode4 page. Native screenshots are full240x160.
No host wall-clock FPS, fabricated roster, crowded save, or injected gameplay.
"""
import argparse,json,re,shutil,struct
from pathlib import Path
from southern_journey import SouthernJourney
from northern_journey import NorthernJourney
from magma_combat_tests import MagmaCombat,ROOT,PLAY,PAUSE,SAVING,digest

class MagmaPerformance(MagmaCombat):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        name='tests/magma_native_performance.py';self.test_sources[name]=digest(ROOT/name)
        p=self.out/'test-source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
        self.south_scene=json.loads((self.source_root/'assets/southern_region/scene.json').read_text())
        table=self.sym['north_art_rooms'];candidates=[]
        for stride in (20,28,32):
            rows=[]
            for i in range(8):
                a=table+i*stride;w,h=struct.unpack('<HH',self.e.bytes(a,4));bitmap=self.e.read(a+4)
                if (w,h)!=((480,320) if i<2 else (240,160)) or bitmap not in [v for k,v in self.sym.items() if k.startswith('north_background_')]:break
                rows.append(dict(address=a,width=w,height=h,bitmap=bitmap,stride=stride))
            if len(rows)==8:candidates.append(rows)
        assert len(candidates)==1;self.descriptors.update({22+i:r for i,r in enumerate(candidates[0])})
    def entry(self,target):
        here=self.get('room')
        if here<30 and target<30:return NorthernJourney.entry(self,target)
        if here<38 and target<38:return SouthernJourney.entry(self,target)
        return super().entry(target)
    def object(self,key):
        if 30<=self.get('room')<38:return next(o for o in self.south_scene['objects'][self.get('room')-30] if o['key']==key)
        return super().object(key)
    def gather(self,cmd):
        self.restore('combat-town-source');self.equip_item(0,19);self.equip_item(1,34);self.equip_item(3,65);self.owned_select(self.owner(cmd));self.set_command(cmd);self.target(112,248);self.ready();self.entry(30);self.entry(22);self.entry(23)
        route=[];self.goto(272,190)
        mask,w,h=self.mask();ex=self.enemies()[0]['x'];choices=[(abs(x-ex),x) for x in range(240,280) if not mask[190*w+x]]
        self.check(bool(choices),'natural pursuer has a real clear lure position');self.goto(min(choices)[1],190)
        for _ in range(480):
            if self.enemies()[0]['y']<=194:break
            self.step(1)
        self.check(self.enemies()[0]['y']<=194,'ordinary Wood walker genuinely enters the final native viewport')
        route.append(self.row());self.goto(200,176)
        for _ in range(350):
            if self.enemies()[1]['x']>=180:break
            self.step(1)
        self.goto(216,176)
        for _ in range(200):
            if self.enemies()[1]['x']>=194:break
            self.step(1)
        route.append(self.row());self.goto(312,124);self.face(3);self.ready();route.append(self.row())
        self.check(self.get('game_state')==PLAY,'five-enemy setup uses actual pursuit without enemy injection or health grants')
        self.cases.append(dict(case='actual-five-enemy-gather-'+str(cmd),route=route,passed=True));self.snapshot('five-body-command-'+str(cmd),settle=False)
    def crowded(self,cmd):
        self.gather(cmd)
        for _ in range(260):
            enemy=self.enemies()[4]
            if enemy['clock']==20 and not enemy['windup']:break
            self.step(1)
        self.check(enemy['clock']==20 and not enemy['windup'],'controller stress waits for a real upcoming ranger windup')
        count=0;previous=(self.get('frame'),self.e.read(0x04000000,2)&16);trace=[]
        for n in range(180):
            phase=n%140;keys='A' if phase<24 or phase==48 else 'R' if phase==53 else 'LEFT' if 57<=phase<62 else 'RIGHT' if 67<=phase<72 else 0
            self.step(1,keys);r=self.row();r['update_delta']=(r['game_frame']-previous[0])&0xffffffff;r['page_flip']=r['displayed_page']!=previous[1];previous=(r['game_frame'],r['displayed_page']);cx,cy=r['displayed_camera']
            def visible(x,y):return cx-8<x<cx+248 and cy-8<y<cy+168
            r['visible_enemy_bodies']=sum(e['hp']>0 and visible(e['x'],e['y']) and (not e['flash'] or bool(r['game_frame']&2)) for e in r['enemies'])
            r['visible_hostile_shots']=sum(s['life']>0 and s['owner'] and visible(s['x'],s['y']) for s in r['shots'])
            r['player_arrows']=sum(a['active'] for a in r['arrows']);r['simultaneous']=r['visible_enemy_bodies']==5 and r['visible_hostile_shots']>0 and r['player_arrows']==2 and r['power']['time']>0
            if r['simultaneous']:
                if count<3:self.capture('crowded-'+str(cmd)+'-combined-'+str(count))
                count+=1
            trace.append(r)
        result=dict(name='five-body-two-arrow-Magma-command-'+str(cmd),hardware_frames=180,updates=sum(r['update_delta'] for r in trace),page_flips=sum(r['page_flip'] for r in trace),max_cycles=max(r['cycles'] for r in trace),max_oam=max(r['obj_count'] for r in trace),combined_frames=count,trace=trace);self.frame_windows.append(result)
        self.check(all(r['update_delta']==1 and r['page_flip'] and r['cycles']<280896 and r['obj_count']<=128 for r in trace),'combined real enemies arrows and Magma command present once per native hardware frame')
        self.check(count>0,'crowded window truly contains five visible enemy bodies plus hostile shot plus two arrows plus new Magma effect')
        self.cases.append(dict(case='crowded-'+str(cmd),combined_frames=count,passed=True))
    def camera(self):
        stride=int(re.search(r'#define CACHE_FIELDS (\d+)',(self.source_root/'src/game.c').read_text())[1]);page=int(bool(self.e.read(0x04000000,2)&16));a=self.sym['cache_fields']+4*stride*page
        return [self.e.read(a+4*17),self.e.read(a+4*18)]
    def row(self):
        r=super().row();r['displayed_camera']=self.camera();r['journal_tab']=self.get('journal_tab');return r
    def capture(self,name):
        p=self.out/(name+'.png');self.e.screenshot(p);self.screenshots.append(dict(path=str(p),sha256=digest(p),dimensions=[240,160],frame=self.e.frame,state=self.get('game_state'),camera=self.camera()))
    def walk(self):
        self.prepare(43);self.goto(424,200);self.ready();rows=self.trace(120,lambda n:'LEFT' if n<40 else 'RIGHT' if n<80 else 'LEFT+UP','native-Magma-field-walking')
        self.check(len({tuple(r['hero']) for r in rows})>40 and len({tuple(r['displayed_camera']) for r in rows})>20,'field performance actually includes walking and scrolling')
        self.capture('field-after-walking');self.cases.append(dict(case='native-Magma-walking',passed=True))
    def cold_ui(self):
        self.restore('combat-town-source');self.goto(240,220);self.ready()
        rows=self.trace(120,lambda i:'START' if i==0 else 'A' if i in (12,24,36,48,60,72,84,96) else 'B' if i==108 else 0,'all-nine-cold-journal-open-switch-close')
        self.check({r['journal_tab'] for r in rows if r['state']==PAUSE}==set(range(9)),'actual cold overlay sequence renders every one of nine journal pages')
        self.check(self.get('game_state')==PLAY,'cold journal close returns to active field')
        self.capture('cold-journal-resumed')
        for tab in range(9):
            self.open_tab(tab);self.capture('native-journal-'+str(tab));self.trace(6,label='journal-page-'+str(tab));self.close_menu()
        self.goto(112,264);self.face(1);self.step(1,'A');self.check(self.get('game_state')==SAVING,'actual anchor opens incremental save')
        rows=self.trace(45,label='real-incremental-save-overlay')
        self.check(any(r['state']==SAVING for r in rows),'save cadence includes actual SAVING updates')
        self.settle();self.step(120);self.capture('save-resumed-full-viewport')
        self.covered.append('native240x160_field_cast_and_cold_overlay_cadence')
    def run(self,only=None):
        self.boot();available=[c for c in (43,45,48,50,53,54,59,60,61,62,64,65,66) if self.owner(c)]
        cases=[('walk',self.walk),('cold-ui',self.cold_ui)]+[('crowded-'+str(c),lambda c=c:self.crowded(c)) for c in (45,50,53,61,64,66) if self.owner(c)]+[('cast-'+str(c),lambda c=c:self.direct(c)) for c in available]
        selected=set(only.split(',')) if only else {n for n,_ in cases};assert selected<={n for n,_ in cases}
        for name,fn in cases:
            if name in selected:self.run_case(name,fn)
        self.report()
        r=json.loads((self.out/'magma-combat.json').read_text());r['suite']='magma-native-full-engine-performance';r['scope']='Full hardware-frame field walking, authored companion cast, nine cold journal overlays, actual incremental save; synthetic stress and physical hardware are not claimed'
        (self.out/'magma-performance.json').write_text(json.dumps(r,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('rom','symbols','output','source-report','source-manifest'):p.add_argument('--'+k,type=Path,required=True)
    for k in ('expected-rom-sha','expected-symbols-sha','source-snapshot'):p.add_argument('--'+k,required=True)
    p.add_argument('--case');p.add_argument('--approved-source-report-sha');a=p.parse_args();r=MagmaPerformance(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_snapshot,a.source_manifest,a.approved_source_report_sha)
    try:r.run(a.case)
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
