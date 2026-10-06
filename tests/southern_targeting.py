#!/usr/bin/env python3
"""Controller regression for the authored town stall/porter targeting conflict."""
import argparse
from pathlib import Path
from southern_journey import SouthernJourney

class SouthernTargeting(SouthernJourney):
    def run(self,scope=None):
        self.boot();self.snapshot('town-before-targeting')
        for label,x,y in (('authored-stall-approach',344,224),('closer-boundary-approach',343,216)):
            self.restore('town-before-targeting');self.goto(x,y,radius=3)
            # Facing by a single controller frame avoids the harness's nearer
            # fixture approach used elsewhere. Record the real sampled point.
            self.step(1,'UP');self.step(2);position=[self.get('px'),self.get('py')];self.tap('A');self.settle()
            got=self.state().quests.objectives[25]&4;porter=self.quest(27)
            self.cases.append({'case':label,'position':position,'face':1,'q25_objectives':self.state().quests.objectives[25],'q27_state':porter,'passed':bool(got) and not porter});self.snapshot(label)
            self.check(got and not porter,'Up toward stall awards its objective without sideways porter interception')
        self.restore('town-before-targeting');self.goto(344,224,radius=3);self.face(3);self.tap('A');self.settle()
        self.check(self.quest(27)==1 and not self.state().quests.objectives[25],'deliberately facing Right reaches porter normally')
        self.snapshot('porter-deliberate-right');self.coverage.append('native-authored-stall-porter-directional-regression')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);p.add_argument('--scene-only',action='store_true');p.add_argument('--source-manifest',type=Path)
    a=p.parse_args();run=SouthernTargeting(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,scene_only=a.scene_only,source_manifest=a.source_manifest)
    try:run.run()
    except Exception as exc:run.failures.append({'error':str(exc),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
if __name__=='__main__':main()
