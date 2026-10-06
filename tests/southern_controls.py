#!/usr/bin/env python3
"""Early native viewport, controller motion, modal, save and selector cadence.

Fresh authenticated N5 cold boot on an explicit ROM/symbol hash pair. All tests
use controller input, read-only ARM descriptors and same-ROM paired snapshots.
Pure expected bitmap construction is an oracle, not synthetic gameplay proof.
"""
import argparse, hashlib, json, math, re
from pathlib import Path
from southern_journey import SouthernJourney, Emulator, N5_SHA, ALL_FORMS, ROOT, PLAY, PAUSE, SAVING, digest

class SouthernControls(SouthernJourney):
    def display_camera(self):
        # mGBA stops at a hardware boundary while the next update may have
        # begun. Authenticate the viewport attached to the actually displayed
        # page, rather than comparing it to not-yet-presented camera variables.
        text=(self.out/'candidate-source-game.c').read_text()
        stride=int(re.search(r"#define CACHE_FIELDS (\d+)",text)[1]);page=int(bool(self.e.read(0x04000000,2)&16))
        addr=self.sym['cache_fields']+4*stride*page
        return self.e.read(addr+4*17),self.e.read(addr+4*18)
    def expected_pixels(self):
        room=self.get('room');d=self.descriptors[room];w,h=d['width'],d['height'];cx,cy=self.display_camera()
        raw=self.e.bytes(d['bitmap'],w*h);expected=bytearray(b''.join(raw[(cy+y)*w+cx:(cy+y)*w+cx+240] for y in range(160)))
        def pixel(x,y,c):
            x-=cx;y-=cy
            if 0<=x<240 and 0<=y<160:expected[y*240+x]=c
        def line(x,y,xx,yy,c):
            assert x==xx or y==yy
            for iy in range(min(y,yy),max(y,yy)+1):
                for ix in range(min(x,xx),max(x,xx)+1):pixel(ix,iy,c)
        if room==30:
            demo=self.get('demo',1)
            for y in range(182,187):
                for x in range(190,195):pixel(x,y,47)
            end=160 if demo else 208;line(192,184,end,184,46);line(end,184,end,192,46)
            if demo:line(192,184,256,184,46);line(256,184,256,192,46)
            if self.quest(24)==3:line(280,194,344,194,56);line(280,195,344,195,47)
        elif room==31:
            assert not self.get('panels',1) and self.get('trial_index',1)!=7
        else:raise AssertionError('Only authored exterior overlays handled by this oracle')
        return bytes(expected)
    def pixel_case(self,label):
        self.check(self.get('game_state')==PLAY and not self.get('toast_ticks') and not self.get('area_ticks'),'pixel check observes clean active viewport')
        expected=self.expected_pixels();page=0x0600a000 if self.e.read(0x04000000,2)&16 else 0x06000000;actual=self.e.bytes(page,38400)
        bad=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
        record={'name':label,'frame':self.e.frame,'displayed_camera':list(self.display_camera()),'next_update_camera':[self.get('camera_x'),self.get('camera_y')],'source_pixels':38400,'rows_compared':160,'mismatches':len(bad),'first_mismatches':bad[:20],'expected_sha256':hashlib.sha256(expected).hexdigest(),'actual_sha256':hashlib.sha256(actual).hexdigest(),'oracle':'exact tested ROM bitmap plus explicitly authored outdoor overlay pixels'}
        self.pixel_cases.append(record);self.report();self.check(not bad,label+' all240x160 displayed pixels match current exact-ROM viewport')
        self.e.screenshot(self.out/(label+'.png'))
        self.check(self.get('obj_count')<=128,'displayed OBJ count remains bounded')
    def raw_window(self,label,count,keys=None,strict=True):
        old=self.get('frame');page=self.e.read(0x04000000,2)&16;trace=[]
        for i in range(count):
            self.step(1,keys(i) if keys else 0);new=self.get('frame');np=self.e.read(0x04000000,2)&16
            trace.append({'hardware_frame':self.e.frame,'update_delta':(new-old)&0xffffffff,'page_flip':np!=page,'render_cycles':self.get('render_cycles'),'state':self.get('game_state'),'obj_count':self.get('obj_count')});old,page=new,np
        row={'name':label,'hardware_frames':count,'game_updates':sum(r['update_delta'] for r in trace),'page_flips':sum(r['page_flip'] for r in trace),'max_cycles':max(r['render_cycles'] for r in trace),'trace':trace};self.frame_windows.append(row);self.report()
        valid=all(r['update_delta']==1 and r['page_flip'] for r in trace) and row['max_cycles']<280896
        if strict:self.check(valid,label+' presents and updates every hardware frame within native cycle budget')
        else:
            self.checks.append({'label':label+' presents and updates every hardware frame within native cycle budget','passed':valid,'frame':self.e.frame})
            if not valid:self.failures.append({'error':'native cadence or cycle budget missed','window':label,'game_updates':row['game_updates'],'page_flips':row['page_flips'],'hardware_frames':count,'max_cycles':row['max_cycles']})
        return row
    def run_earned_save(self,source_report):
        # This optional stress continuation accepts only a completed controller
        # journey from this exact ROM/symbol pair and the authenticated N5 seed.
        path=Path(source_report).resolve();report=json.loads(path.read_text())
        assert report['controller_only'] and not report['failures'] and all(c['passed'] for c in report['checks'])
        assert report['rom_sha256']==self.target_sha and report['symbols_sha256']==self.symbol_sha
        assert report['provenance']['sram_sha256']==N5_SHA
        source=report['snapshots']['08-complete41-independent-reboot'];saved=Path(source['sram_path'])
        assert source['rom_sha256']==self.target_sha and source['symbols_sha256']==self.symbol_sha and digest(saved)==source['sram_sha256']
        self.provenance['same_rom_earned_sram']={'source_report':str(path),'source_report_sha256':digest(path),'snapshot':'08-complete41-independent-reboot','sram_path':str(saved),'sram_sha256':digest(saved),'machine_state_loaded':False}
        self.e.close();self.e=Emulator(self.rom);self.e.load_save(saved);self.e.reset();self.step(150);self.tap('START',2,35);self.settle()
        self.check(self.collection()==ALL_FORMS and len(self.live())==21 and sum(bool(g.item_id) for g in self.state().equipment.bag)==25,'earned stress source independently boots41 histories,21 individuals and25 gear')
        self.check(self.get('room')==30,'earned save boots safe Southern town');self.snapshot('earned41-stress-source')
        self.step(130);self.pixel_case('earned41-clean-town');self.raw_window('earned41-native-idle',120,strict=False)
        self.open_tab(2);self.raw_window('earned41-party-journal',90,strict=False);self.close_menu();self.open_tab(3);self.raw_window('earned41-growth-journal',90,strict=False);self.close_menu()
        self.raw_window('earned41-quick-selector',48,lambda i:'L' if i<30 else 0,strict=False)
        self.approach('rest');self.step(4);row=self.raw_window('earned41-actual-save-dialog',180,lambda i:'A' if i in (0,40,80,120) else 0,strict=False)
        self.check(any(r['state']==SAVING for r in row['trace']),'earned41 save stress observes actual SAVING updates');self.settle();self.snapshot('earned41-controls-complete')
        self.coverage.append('same-rom-earned41-native-save-journals-selector-cadence')
    def run(self,scope=None):
        self.boot();self.step(130);self.pixel_case('town-first-clean-viewport')
        b,w,h=self.mask();candidates=[]
        for y in range(210,261,5):
            for x in range(170,291,5):
                if all(not any(b[yy*w+x-3:yy*w+x+43]) for yy in range(y-3,y+43)):candidates.append((abs(x-240)+abs(y-235),x,y))
        self.check(bool(candidates),'compiled collision has a clear rectangle for fair axis/diagonal movement test')
        _,x,y=min(candidates);self.goto(x,y);self.step(130);self.snapshot('movement-base');vectors={}
        for key in ('RIGHT','RIGHT+DOWN'):
            self.restore('movement-base');self.step(10);start=(self.get('px_q8'),self.get('py_q8'));rows=[]
            for i in range(24):
                self.step(1,key)
                if i in (0,1,2,9,23):self.pixel_case('scroll-'+key.lower().replace('+','-')+'-'+str(i+1))
                rows.append({'frame':self.e.frame,'position_q8':[self.get('px_q8'),self.get('py_q8')],'camera':[self.get('camera_x'),self.get('camera_y')]})
            end=(self.get('px_q8'),self.get('py_q8'));vectors[key]=[end[i]-start[i] for i in range(2)];self.cases.append({'case':'native-movement-'+key,'trace':rows})
        axis=math.hypot(*vectors['RIGHT']);diag=math.hypot(*vectors['RIGHT+DOWN']);self.check(abs(axis-diag)/axis<0.015,'diagonal controller movement is normalized against cardinal movement')
        self.cases.append({'case':'normalized-movement','vectors_q8':vectors,'distance_ratio':diag/axis,'passed':True})
        self.restore('movement-base');self.open_tab(0)
        for tab in range(8):
            self.check(self.get('journal_tab')==tab,'all eight journal pages are reachable')
            self.raw_window('journal-tab-'+str(tab),30);self.e.screenshot(self.out/f'journal-tab-{tab}.png')
            if tab<7:self.tap('A',2,4)
        self.raw_window('journal-close-first-frames',8,lambda i:'B' if i==0 else 0);self.check(self.get('game_state')==PLAY,'journal closes cleanly')
        self.step(130);self.pixel_case('first-clean-viewport-after-journal')
        self.raw_window('quick-selector-open-cycle-close',48,lambda i:'L' if i<30 else 0)
        self.check(not self.get('quickparty_open'),'selector closes on release');self.step(130);self.pixel_case('first-clean-viewport-after-selector')
        self.approach('rest');self.step(4);row=self.raw_window('actual-save-dialog',150,lambda i:'A' if i in (0,35,70,105) else 0,strict=False)
        self.check(any(r['state']==SAVING for r in row['trace']),'save cadence observes actual SAVING state rather than an idle substitute')
        self.settle();self.entry(31);self.step(130);self.pixel_case('field-first-clean-viewport');self.raw_window('field-native-idle',120,strict=False);self.snapshot('controls-complete');self.coverage.append('early-native-viewport-scrolling-normalized-movement-eight-journals-selector-save')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);p.add_argument('--scene-only',action='store_true');p.add_argument('--source-manifest',type=Path);p.add_argument('--earned-report',type=Path,help='Only a completed journey from this exact tested ROM; SRAM only, no machine state')
    a=p.parse_args();run=SouthernControls(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,scene_only=a.scene_only,source_manifest=a.source_manifest)
    try:
        if a.earned_report:run.run_earned_save(a.earned_report)
        else:run.run()
    except Exception as exc:run.failures.append({'error':str(exc),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
    if run.failures:raise SystemExit(1)
if __name__=='__main__':main()
