#!/usr/bin/env python3
"""Exact-candidate earned21-individual storage and quick-selector stress.

Imports only SRAM from a completed controller journey with this exact ROM and
symbol hash pair; never imports a machine state from another run or candidate.
No gameplay memory writes, synthetic roster entries or fabricated progression.
"""
import argparse, json, shutil
from pathlib import Path
from southern_controls import SouthernControls
from southern_journey import digest, ROOT

class SouthernSelector(SouthernControls):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        source=ROOT/'tests/southern_controls.py';self.test_sources['tests/southern_controls.py']=digest(source)
        shutil.copyfile(source,self.out/'test-source'/source.name);self.report()
    def selection_window(self,label,count,keys):
        last=self.get('frame');page=self.e.read(0x04000000,2)&16;trace=[]
        for i in range(count):
            self.step(1,keys(i));now=self.get('frame');newpage=self.e.read(0x04000000,2)&16;r=self.roster();candidate=self.get('quickparty_menu_candidate')
            trace.append({'hardware_frame':self.e.frame,'update_delta':(now-last)&0xffffffff,'page_flip':newpage!=page,'render_cycles':self.get('render_cycles'),'obj_count':self.get('obj_count'),'selected_party':r.selected_party,'selected_form':r.instances[r.party[r.selected_party]].form_id,'quickparty_open':self.get('quickparty_open'),'menu_candidate':candidate,'candidate_form':r.instances[candidate].form_id if candidate<160 else None,'px':self.get('px'),'py':self.get('py')});last,page=now,newpage
        row={'name':label,'hardware_frames':count,'game_updates':sum(x['update_delta'] for x in trace),'page_flips':sum(x['page_flip'] for x in trace),'max_cycles':max(x['render_cycles'] for x in trace),'trace':trace};self.frame_windows.append(row);self.report()
        good=all(x['update_delta']==1 and x['page_flip'] and x['obj_count']<=128 for x in trace) and row['max_cycles']<280896
        self.checks.append({'label':label+' updates/presents each hardware frame inside native cycle/OBJ budgets','passed':good,'frame':self.e.frame})
        if not good:self.failures.append({'error':'selector cadence or cycle budget missed','window':label,'game_updates':row['game_updates'],'page_flips':row['page_flips'],'hardware_frames':count,'max_cycles':row['max_cycles']})
        return row
    def run(self,source_report):
        self.run_earned_save(source_report)
        before_transition=(bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))
        self.step(130);self.raw_window('earned41-first-journal-open-tabs-close',128,lambda i:'START' if i==0 else 'A' if i in (12,24,36,48,60,72,84) else 'B' if i==96 else 0,strict=False)
        self.check(self.get('game_state')==1 and self.get('journal_tab')==7,'frame-sampled first-open sequence visits all eight journal tabs and closes normally')
        self.check((bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))==before_transition,'journal opening, tab changes and close mutate no retained content')
        self.open_tab(2);before=bytes(self.roster());owned={c.form_id for c in self.live()}
        row=self.selection_window('earned21-storage-all-candidates',120,lambda i:'DOWN' if i%4==0 else 0)
        self.check(owned<={x['candidate_form'] for x in row['trace']},'ordinary journal scroll visits every one of21 genuinely owned individual candidates')
        self.check(bytes(self.roster())==before,'browsing all owned storage candidates mutates no individual or party data');self.close_menu();self.ready();self.step(20)
        xy=(self.get('px'),self.get('py'));directions=('UP','RIGHT','DOWN','LEFT')
        row=self.selection_window('earned21-four-slot-selector-commits',96,lambda i:'L+'+directions[i//24] if i%24<16 else 0)
        self.check({x['selected_party'] for x in row['trace']}=={0,1,2,3},'four explicit L-direction releases commit each actual active slot')
        self.check((self.get('px'),self.get('py'))==xy and not self.get('quickparty_open'),'selector owns directional input and closes without moving the hero')
        self.check(len(self.live())==21,'storage browsing and selection preserve21 retained individuals')
        self.snapshot('earned21-selection-complete');self.coverage.append('all21-owned-storage-candidates-and-four-native-selector-commits')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','output','earned-report'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);p.add_argument('--source-manifest',type=Path)
    a=p.parse_args();run=SouthernSelector(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,source_manifest=a.source_manifest)
    try:run.run(a.earned_report)
    except Exception as exc:run.failures.append({'error':str(exc),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
    if run.failures:raise SystemExit(1)
if __name__=='__main__':main()
