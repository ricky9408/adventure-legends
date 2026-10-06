#!/usr/bin/env python3
"""Compare independent-ROM modal pixels/OAM and first resume frames via SRAM only.

Each ROM independently boots identical authenticated controller-earned SRAM.
No machine state crosses ROMs; every emitted snapshot owns a same-ROM SRAM pair.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from northern_journey import *

class ModalRun(NorthernJourney):
    def __init__(self,*args,source_report,**kwargs):
        super().__init__(*args,**kwargs)
        source_path=Path(source_report).resolve();source=json.loads(source_path.read_text())
        assert source['controller_only'] and not source['failures'] and all(c['passed'] for c in source['checks'])
        src=source['snapshots']['07-all-northern-quests'];saved=Path(src['sram_path'])
        if not saved.is_file():saved=source_path.parent/saved.name
        assert digest(saved)==src['sram_sha256']
        self.e.load_save(saved);self.e.reset();self.step(150);self.tap('START',2,35);self.settle()
        self.provenance={'fixture_path':str(saved),'sram_sha256':src['sram_sha256'],'source_report':str(source_path),
            'source_report_sha256':digest(source_path),'source_rom_sha256':source['rom_sha256'],'source_machine_state_loaded':False,
            'scope':'Identical controller-earned pre-evolution SRAM independently booted on each target'}
        self.scenes={};self.resumes={}
    def align(self):
        for _ in range(170):
            if self.get('frame')%84==0:return
            self.step(1)
        raise AssertionError('Cannot align harmless idle/modal animation sampling')
    def capture(self,name,modal=True):
        shot=self.e.screenshot(self.out/(name+'.png'));oam=self.oam()
        if modal:self.check(not any(o['priority'] in (1,2) for o in oam),'modal has exactly the intended HUD OAM, with all world actors hidden')
        self.scenes[name]={'rgb_sha256':hashlib.sha256(shot.tobytes()).hexdigest(),'oam':oam,'state':self.get('game_state'),
            'journal_tab':self.get('journal_tab'),'frame_phase':self.get('frame')%84,'screenshot':name+'.png'}
        self.snapshot(name,settle=False)
    def check_companion_cache(self):
        if not self.get('summoned'):return
        form=self.selected().form_id
        if form not in NEW_FORMS:return
        code=self.get('gfx_companion_frame');local=code-self.get('spirit')*16
        self.check(0<=local<16,'first visible resumed companion uses a normal current walk pose')
        direction,frame=divmod(local,4);index=NEW_FORMS.index(form)
        raw=self.e.bytes(self.sym['northern_creature_direction_frames']+((index*4+direction)*4+frame)*256,256)
        tiled=b''.join(raw[(ty+y)*16+tx:(ty+y)*16+tx+8] for ty in (0,8) for tx in (0,8) for y in range(8))
        actual=self.e.bytes(0x06014000+6400,256)
        self.check(actual==tiled,'first resumed companion cache contains exact current-form ROM pixels')
    def resume(self,label,key='B'):
        self.align();rows=[]
        if key=='A':
            self.step(1,'A');self.capture(label+'-input',modal=False)
            for _ in range(160):
                if self.get('game_state')==PLAY:break
                self.step(1)
            self.check(self.get('game_state')==PLAY,'normal death retry completes its required save before active resume')
            key=0
        for n in range(3):
            self.step(1,key if n==0 else 0);self.capture(label+'-'+str(n),modal=False)
            world=[o for o in self.oam() if o['priority'] in (1,2)]
            self.check(self.get('game_state')==PLAY,'resume input returns to active gameplay')
            if n>=1:self.check(bool(world),'first presented resume frame restores visible world OAM without an extra blank frame')
            if world:self.check_companion_cache()
            rows.append({'frame':self.e.frame,'world_oam_count':len(world),'current_form':self.selected().form_id})
        self.resumes[label]=rows
    def run(self):
        self.owned_select(19);self.act(104,208);self.ready();self.goto(120,208);self.align();self.snapshot('modal-source-ready')
        self.open_tab(0)
        for tab in range(7):
            self.check(self.get('journal_tab')==tab,'controller reaches expected modal tab')
            self.align();self.capture('pause-tab-'+str(tab))
            if tab<6:self.tap('A',1,5)
        self.resume('pause-resume')
        self.goto(104,208);self.act(104,208);self.open_tab(3);self.tap('SELECT',1,5)
        self.check(self.get('game_state')==CONFIRM,'actual earned evolution opens confirmation');self.align();self.capture('evolution-confirm')
        self.tap('B',1,4);self.check(self.get('game_state')==PAUSE,'decline returns to journal');self.resume('declined-evolution-resume')
        self.open_tab(3);self.tap('SELECT',1,4);self.tap('A',1,0)
        self.check(self.get('game_state')==8,'actual confirmation starts evolution animation')
        for target in (16,40,72):
            for _ in range(100):
                if self.get('evolution_tick')>=target:break
                self.step(1)
            self.check(self.get('evolution_tick')==target,'evolution sampled at exact active-animation tick')
            self.capture('evolution-animation-'+str(target))
        self.settle();self.check(self.selected().form_id==20,'native confirmed evolution completes');self.resume('evolved-form-resume')
        self.entry(23);self.goto(272,252)
        for _ in range(400):
            if self.get('game_state')==DEAD:break
            self.step(10)
        self.check(self.get('game_state')==DEAD,'natural enemy damage reaches modal death');self.align();self.capture('ordinary-death')
        self.resume('death-retry-resume','A')
        result={'suite':'northern-modal-native-pixels','rom_sha256':self.target_sha,'symbols_sha256':self.symbol_sha,
            'controller_only':True,'game_ram_writes':0,'source_machine_state_loaded':False,'scenes':self.scenes,'resumes':self.resumes}
        (self.out/'modal-scenes.json').write_text(json.dumps(result,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('rom','symbols','output','source-report'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True)
    p.add_argument('--compare',type=Path,help='Prior independently booted modal-scenes.json; no state is loaded from it')
    a=p.parse_args();run=ModalRun(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,source_report=a.source_report)
    try:
        run.run()
        if a.compare:
            before=json.loads(a.compare.read_text());comparisons=[]
            for name,scene in run.scenes.items():
                old=before['scenes'][name];same=scene['rgb_sha256']==old['rgb_sha256'] and scene['oam']==old['oam']
                comparisons.append({'scene':name,'pixels_identical':scene['rgb_sha256']==old['rgb_sha256'],'visible_oam_identical':scene['oam']==old['oam'],'passed':same})
            result={'before_rom_sha256':before['rom_sha256'],'after_rom_sha256':run.target_sha,'cross_rom_machine_states_loaded':False,'comparisons':comparisons}
            (run.out/'modal-equivalence.json').write_text(json.dumps(result,indent=2)+'\n')
            run.check(all(c['passed'] for c in comparisons),'every modal and first-resume native pixel/OAM scene matches independent prior ROM')
    except Exception as e:run.failures.append({'error':str(e),'status':run.status()});run.snapshot('modal-failure',settle=False);raise
    finally:run.report();run.e.close()
if __name__=='__main__':main()
