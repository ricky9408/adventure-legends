#!/usr/bin/env python3
"""Compare a naturally cleared native save error with forced full repaint.

Inactive SRAM corruption is an explicit fault fixture. Save retry uses actual
controller input. Same-ROM presentation branches are logged and are not
controller acquisition evidence.
"""
import argparse, hashlib, json, shutil
from pathlib import Path
from player_feedback_native import Run, sha

class Probe(Run):
    def check(self,label,value,detail=None):
        super().check(label,value,detail)
        if label=='A retry clears save error after native successful commit' and value:
            self.compare_clear('controls-after-retry')
            self.tap('B');self.tap('B')
            self.check('controller returns to play after retry',self.g('game_state')==1)
            self.compare_clear('field-after-retry')
            self.step(90)
            self.check('saved badge expires with no unresolved error',self.g('saved_ticks')==0 and not self.g('save_failed'))
            self.compare_clear('field-after-badge-expiry')
    def compare_clear(self,name):
        state=self.out/(name+'.state');self.e.state(state);results=[]
        for force in (False,True):
            self.e.state(state,load=True);self.state_loads+=1
            if force:
                for offset in (0,4):self.put('cache_valid',0,offset=offset,reason='reference forces complete repaint after natural error dismissal')
            self.step(6,phase='prepared_render');image=self.e.screenshot();oam=self.e.bytes(0x07000000,1024)
            path=self.out/(name+('-full' if force else '-cached')+'.png');image.save(path)
            results.append((image.tobytes(),oam,sha(path)))
        equal=results[0][:2]==results[1][:2]
        row={'view':name,'pixels_and_oam_equal':equal,'cached_png_sha256':results[0][2],'full_png_sha256':results[1][2],'status':self.state()}
        self.cases.append({'case':'save-error-dismissal-render','comparison':row})
        self.check(name+' leaves exact clean pixels after error dismissal',equal,row)
        self.e.state(state,load=True);self.state_loads+=1

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','symbols','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+name,required=True)
    a=p.parse_args();r=Probe(a);r.hashes['probe_script_sha256']=sha(__file__)
    shutil.copyfile(__file__,r.out/'test-source/tests/player_feedback_badge_probe.py')
    r.section('save_error_dismissal',r.save_fault);d=r.finish()
    return int(bool(d['failures']) or not d['exact_files_unchanged'])
if __name__=='__main__':raise SystemExit(main())
