"""Fresh-input opening adapter for the earned journey; no skip or save injection.

The old G4 route remains byte-for-byte in its original control flow when the
ROM lacks opening_scene_begin. The new title-to-opening counter reset is named
explicitly, while its display/CPU cost and every opening presentation frame
remain observable. Only fresh A edges advance authored pages.
"""
import hashlib
import json
import re
from pathlib import Path
from mgba_runner import keymask

class OpeningJourneyMixin:
    def tap(self, keys, hold=2, release=2):
        opening='opening_scene_begin' in self.sym
        if opening and self.mode=='boot' and self.get('game_state')==0 and keymask(keys)==1:
            assert hold>=1
            self._opening_pending=True
            self._opening_started=self.e.frame
            self.mode='opening_activation'
            self.raw_step(1,keys)
            self.mode='journey'
            if hold>1:self.step(hold-1,keys)
            self.step(release)
            return
        return super().tap(keys,hold,release)

    def dialogs(self,reward=None):
        if getattr(self,'_opening_pending',False):
            self.check(self.get('game_state')==14,'new ROM enters its required opening scene instead of bypassing it')
            self.check(self.e.read(self.sym['opening_page'],1)==0,'released title A leaves the first opening page visible')
            header=(Path(self.source_root)/'src/opening_scene.h').read_text()
            count=int(re.search(r'#define\s+OPENING_SCENE_PAGES\s+(\d+)',header).group(1))
            self.check(1<=count<=32,'opening page count comes from candidate-paired authored source')
            pristine=self.provenance['initial_sram_sha256']
            pages=[]
            for expected in range(count):
                self.check(self.get('game_state')==14 and self.e.read(self.sym['opening_page'],1)==expected,
                           f'opening page {expected+1} is reached by one fresh A edge')
                first=self.e.frame
                self.step(90)
                image=self.out/f'opening-page-{expected+1:02d}.png'
                self.e.screenshot(image)
                self.check(hashlib.sha256(self.e.bytes(0x0e000000,32768)).hexdigest()==pristine,
                           'viewing the opening leaves initial SRAM untouched')
                self.check(self.get('chapter_flags')==self.get('room_flags')==0,
                           'the opening grants no story or puzzle progress')
                pages.append({'page':expected,'first_hardware_frame':first,'viewed_through':self.e.frame,
                              'screenshot':str(image),'screenshot_sha256':hashlib.sha256(image.read_bytes()).hexdigest()})
                self.tap('A',2,4)
            self._opening_pending=False
            self.settle_save();self.drain_background()
            self.check(self.get('game_state')==1 and self.get('room')==0,
                       'viewing every opening page reaches normal village play')
            self.check(self.get('chapter_flags')==self.get('room_flags')==0,
                       'opening completion keeps campaign progression unearned')
            record={'candidate':self.candidate,'controller_only':True,'game_ram_writes':0,'machine_state_imports':0,
                    'skip_used':False,'pages':pages,'start_hardware_frame':self._opening_started,
                    'end_hardware_frame':self.e.frame,'presentation_phase':'journey',
                    'activation_phase':'opening_activation; logical counter reset only, no display/budget waiver'}
            (self.out/'opening-scene.json').write_text(json.dumps(record,indent=2)+'\n')
            self.coverage.append('complete-authored-opening-through-fresh-A-pages')
        return super().dialogs(reward)
