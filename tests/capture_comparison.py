#!/usr/bin/env python3
"""Render an honest split-screen using two controller-reached emulator states.
Requires immutable before/after folders from performance_tests.py. No RAM writes.
"""
from pathlib import Path
import argparse,sys,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--before',type=Path,default=ROOT/'build/perf-baseline')
p.add_argument('--after',type=Path,default=ROOT/'build/perf-optimized-v3')
p.add_argument('--output',type=Path,default=ROOT/'build/qa/motion-comparison.mp4')
a=p.parse_args();a.output.parent.mkdir(exist_ok=True,parents=True)
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,17);small=ImageFont.truetype(fontpath,13)
proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','960x392','-r','59.7275','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output)],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
try:
 for scene,label in [('village_motion','Directional steps / normalized diagonal movement'),('forest_companion','Following companions / shadows / foreground depth'),('boss_armored','Guardian + projectiles / ~30 Hz to one update per GBA frame')]:
  before=Emulator(a.before/'emberbond.gba');after=Emulator(a.after/'emberbond.gba')
  before.state(a.before/'captures'/f'{scene}.state',True);after.state(a.after/'captures'/f'{scene}.state',True)
  for f in range(300):
   if scene=='village_motion': key=('UP' if f%160<75 else 'DOWN')
   elif scene=='forest_companion':key=('LEFT' if f%100<50 else 'RIGHT')
   else:key=('LEFT' if f%96<48 else 'RIGHT')
   before.frames(1,key);after.frames(1,key)
   canvas=Image.new('RGB',(960,392),'#121a2c');d=ImageDraw.Draw(canvas)
   d.text((12,7),'FIRST PLAYABLE',font=font,fill='#b4bbcc');d.text((492,7),'POLISHED ORIGINAL GBA BUILD',font=font,fill='#ffdc93')
   d.text((12,34),label,font=small,fill='#d9dfeb')
   canvas.paste(before.screenshot().resize((480,320),Image.Resampling.NEAREST),(0,64));canvas.paste(after.screenshot().resize((480,320),Image.Resampling.NEAREST),(480,64))
   proc.stdin.write(canvas.tobytes())
  before.close();after.close()
finally:
 proc.stdin.close();rc=proc.wait()
assert rc==0
print(a.output)
