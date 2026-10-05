#!/usr/bin/env python3
"""Short opening-village input demo: native ROM video/audio, no game RAM writes.

The 240x160 GBA image is untouched. A separate20px caption margin shows the
controller input for this demonstration; both are integer-upscaled4x for video.
"""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image,ImageDraw,ImageFont
from evolution_tests import EvolutionRun,ROOT

OUT=ROOT/'build/quickparty-demo'
RATE=16777216/280896
class Demo(EvolutionRun):
    def __init__(self):
        super().__init__(ROOT/'build/emberbond.gba',ROOT/'build/emberbond.sym',OUT)
        self.encoder=None;self.count=0;self.cues=[];self.font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',9)
    def begin(self):
        self.encoder=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x180','-r',str(RATE),'-i','-','-vf','scale=960:720:flags=neighbor','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p',str(OUT/'silent.mp4')],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
        self.e.audio_start(OUT/'native-audio.wav')
    def segment(self,n,keys,label):
        self.cues.append({'frame':self.count,'frames':n,'keys':keys,'caption':label})
        for _ in range(n):
            self.raw_step(1,keys)
            assert self.get('room')==0,'opening village only'
            canvas=Image.new('RGB',(240,180),(11,22,38));canvas.paste(self.e.screenshot(),(0,0))
            ImageDraw.Draw(canvas).text((5,164),label,font=self.font,fill=(249,226,158))
            self.encoder.stdin.write(canvas.tobytes());self.count+=1
    def finish(self):
        self.e.audio_stop();self.encoder.stdin.close();assert self.encoder.wait()==0
        target=OUT/'emberbond-quick-companions.mp4'
        subprocess.run(['ffmpeg','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'native-audio.wav'),'-c:v','copy','-c:a','aac','-shortest','-movflags','+faststart',str(target)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        manifest={'rom_sha256':hashlib.sha256(self.rom.read_bytes()).hexdigest(),'controller_only':True,'game_ram_writes':0,'savestate_restores':0,'scope':'Opening village and two starting companions only. No evolved forms, secret locations, boss fights or ending.','frames':self.count,'frame_rate':RATE,'seconds':self.count/RATE,'native_image':'240x160 untouched, plus separate20px input-caption margin, integer-upscaled4x','audio':'Actual native emulator PSG audio','video_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'cues':self.cues}
        (OUT/'capture.json').write_text(json.dumps(manifest,indent=2)+'\n')
        self.e.close()

if __name__=='__main__':
    p=Demo()
    try:
        p.step(90);p.tap('SELECT',4,4);p.dialogs();p.step(160);p.tap('B',2,2);p.step(35)
        p.begin();p.segment(65,0,'B: companion is already called')
        p.segment(45,'L','Hold L: the world waits')
        p.segment(90,'L+RIGHT','L + RIGHT: choose this slot');p.shot('opening-picker-native')
        p.segment(70,0,'Release L: companion changes directly');p.shot('opening-field-native')
        p.segment(65,'L+UP','L + UP: choose another slot');p.segment(55,0,'Release L: no extra B needed')
        p.segment(35,'L+RIGHT','Choose a slot, then cancel')
        p.segment(15,'L+B','B: cancel');p.segment(20,'L','Keep holding: no second selection');p.segment(45,0,'Release L: original companion stays')
        p.segment(6,'L','Short L tap');p.segment(65,0,'Cycle assigned companions')
        p.segment(2,'START','START: open journal');p.segment(4,0,'A: change journal page')
        p.segment(2,'A','A: change journal page');p.segment(4,0,'A: change journal page')
        p.segment(2,'A','A: open party assignment');p.segment(45,0,'LEFT/RIGHT: slot; UP/DOWN: owned ally')
        p.segment(2,'DOWN','DOWN: browse owned companions');p.segment(35,0,'R: swap these two assigned slots')
        p.segment(2,'R','R: assign and save');p.segment(70,0,'Assignments save safely');p.shot('opening-party-native')
        p.segment(2,'B','B: return to play');p.segment(25,0,'The whole world returns')
        p.segment(65,'L+UP','L + UP: use the reordered slot');p.segment(70,0,'Release L: ready to explore')
        p.finish()
    except Exception:
        if p.encoder and p.encoder.poll() is None:p.encoder.stdin.close();p.encoder.wait()
        p.e.close();raise
