#!/usr/bin/env python3
"""Native PLAY-strip differential around an actual owned Return91 cast.

Actual controller input reaches and performs the cast. Separate presentation
branches use an ordinary menu round trip to establish clean bitmap pages, then
freeze animation and change only Return91 hint state and the QA bypass. Caches
are never invalidated by the helper. These branches do not claim acquisition.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
from player_feedback_native import Run,sha,LIMIT

class Probe(Run):
    def restore_branch(self,path):
        self.e.state(path,load=True);self.state_loads+=1
        self.cases.append({'case':'prepared-state-restore','path':path.name,'load_number':self.state_loads})
    def frozen_frames(self,n,capture=False):
        samples=[];views={}
        for i in range(n):
            self.put('frame',240,reason='paired presentation-only fixed animation clock')
            self.step(1,'L',phase='prepared_render');samples.append(self.frames[-1])
            if capture and i>=n-2:
                page=int(bool(self.e.read(0x04000000,2)&16));views[page]=(self.e.screenshot(),self.e.bytes(0x07000000,1024))
        self.check('prepared strip presentation never skips an update or page flip',all(f['delta']==1 and f['flip'] and f['cycles']<=LIMIT for f in samples),{'frames':len(samples),'peak_cycles':max(f['cycles'] for f in samples)})
        return views
    def pages(self,name):return [self.e.read(self.sym[name]+4*p) for p in (0,1)]
    def tap(self,k,hold=2,release=3):
        command=0
        if k=='R':
            s=self.save_state();c=s.roster.instances[s.roster.party[s.roster.selected_party]];command=c.equipped[c.selected_command]
        if command!=91:return super().tap(k,hold,release)
        before=self.out/'controller-before-return91.state';self.e.state(before)
        super().tap(k,hold,release);self.wait(lambda:self.g('return_power_kind')==91 and self.g('return_power_time')>0,8)
        resume=self.out/'controller-after-return91.state';self.e.state(resume);lifetime=self.g('return_power_time')
        self.restore_branch(resume)
        self.put('return_power_time',0,reason='presentation-only hidden hint while obtaining clean pages; genuine cast identity retained')
        # The ordinary menu round trip genuinely redraws clean field pages.
        # No host invalidation or clean/raw provenance flag is injected.
        super().tap('START');super().tap('START');self.step(3,phase='prepared_render')
        self.step(2,'L+B',phase='prepared_render');self.frozen_frames(8)
        self.check('controller cancellation freezes a clean field without picker',self.g('game_state')==1 and not self.g('quickparty_open'))
        bottom=(7,27,29,31,33,35,37,42)
        clear=all(not self.e.read(self.sym['cache_fields']+4*(45*p+i)) for p in (0,1) for i in bottom)
        self.check('first hint starts from two valid genuinely clean bitmap pages',all(self.pages('cache_valid')) and clear)
        if 'play_strip_clean' in self.sym:
            self.check('first hint starts before either raw strip has been captured',self.pages('play_strip_clean')==[1,1] and self.pages('play_strip_valid')==[0,0],{'clean':self.pages('play_strip_clean'),'raw':self.pages('play_strip_valid')})
        clean=self.out/'prepared-clean-before-first-hint.state';self.e.state(clean);results=[]
        cases=[('first-hint-appears',clean,lifetime),('final-hint-disappears',self.out/'prepared-first-hint-active.state',0),('hint-reappears',self.out/'prepared-final-hint-gone.state',lifetime)]
        for name,base,new_time in cases:
            branches=[]
            for disabled in (0,1):
                self.restore_branch(base);self.put('play_strip_disabled',disabled,reason='native full-render reference bypass')
                start=self.g('play_strip_reuses');before_keys=[[self.e.read(self.sym['cache_fields']+4*(45*p+i)) for i in range(45)] for p in (0,1)]
                raw_before=self.pages('play_strip_valid');self.put('return_power_kind',91,reason='presentation-only already controller-cast Return91 hint identity');self.put('return_power_time',new_time,reason='presentation-only known Return91 hint transition')
                views=self.frozen_frames(10,capture=True);delta=self.g('play_strip_reuses')-start
                after_keys=[[self.e.read(self.sym['cache_fields']+4*(45*p+i)) for i in range(45)] for p in (0,1)]
                self.check(name+(' optimized reuses both actual pages' if not disabled else ' bypass performs full redraw'),delta==2 if not disabled else delta==0,{'reuses':delta,'changed_keys':[[i for i in range(45) if before_keys[p][i]!=after_keys[p][i]] for p in (0,1)],'raw_before':raw_before,'raw_after':self.pages('play_strip_valid')})
                self.check(name+' captures both visible page parities',set(views)=={0,1})
                if not disabled and name=='first-hint-appears':
                    self.check('first hint captures raw provenance on both pages',self.pages('play_strip_valid')==[1,1]);self.e.state(self.out/'prepared-first-hint-active.state')
                if not disabled and name=='final-hint-disappears':self.e.state(self.out/'prepared-final-hint-gone.state')
                branches.append((views,delta))
            for page in (0,1):
                a=branches[0][0][page];b=branches[1][0][page];equal=a[0].tobytes()==b[0].tobytes() and a[1]==b[1]
                record={'transition':name,'page':page,'passed':equal,'optimized_reuses':branches[0][1],'full_render_reuses':branches[1][1],'optimized_rgb_sha256':hashlib.sha256(a[0].tobytes()).hexdigest(),'full_render_rgb_sha256':hashlib.sha256(b[0].tobytes()).hexdigest(),'oam_equal':a[1]==b[1]};results.append(record)
                self.check(name+' page '+str(page)+' cached output equals full renderer',equal,record)
                if not equal:
                    a[0].save(self.out/(name+'-page'+str(page)+'-cached.png'));b[0].save(self.out/(name+'-page'+str(page)+'-full.png'))
        self.cases.append({'case':'native-play-strip-equivalence','scope':'prepared presentation branches around an actual controller cast; genuine clean pages; no cache invalidations','results':results})
        self.restore_branch(resume)
    def finish(self):
        for c in self.cases:
            if c.get('case')=='native-power-cooldowns':c['controller_only']=False;c['scope']='Controller selections with explicitly logged same-ROM presentation branches'
        return super().finish()

def main():
    p=argparse.ArgumentParser()
    for name in ('rom','symbols','output','earned-shop-save'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+name,required=True)
    a=p.parse_args();r=Probe(a);r.hashes['probe_script_sha256']=sha(__file__);shutil.copyfile(__file__,r.out/'test-source/tests/player_feedback_strip_probe.py');r.section('field_strip_equivalence',r.power_cooldowns);d=r.finish();return int(bool(d['failures']) or not d['performance']['strict_measured_pacing_pass'])
if __name__=='__main__':raise SystemExit(main())
