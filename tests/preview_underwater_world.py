#!/usr/bin/env python3
"""Synthetic host render of real world/overlay functions. Not player media,
not emulator screenshots, and not native controller evidence."""
import ctypes as C,importlib.util,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import test_underwater_game as W
spec=importlib.util.spec_from_file_location('palette',ROOT/'assets/generate_assets.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
OUT=ROOT/'docs/underwater-runtime/host-previews';OUT.mkdir(parents=True,exist_ok=True)
t=W.UnderwaterWorld();t.setUp();t.sources();pix=(C.c_ubyte*38400).in_dll(W.L,'underwater_host_pixels')
settings=[(1,1,0,0),(1,0,0,0),(1,0,0,0),(1,0,0,0),(1,0,0,0),(1,1,0,0),(1,1,0,0),(1,2,0,0),(1,0,0,0),(0,0,0,0),(3,0,0,0),(1,3,1,0),(1,3,0,0),(2,0,0,0),(1,3,0,0),(7,0,0,0)]
sheet=Image.new('RGB',(480,16*176),(11,40,51));d=ImageDraw.Draw(sheet);diffs=[]
for i in range(16):
 t.start(17+i//2,1+i%2);camera=(120,80) if W.v('room') in(48,51) else(0,0)
 frames=[]
 for configured in (False,True):
  if configured:
   v=W.trial();v.setting[:]=settings[i]
   if i==8:v.order=2
   if i==9:v.casts=7;v.order=3
  assert W.L.capture_world(*camera)==1
  im=Image.frombytes('P',(240,160),bytes(pix));im.putpalette(P.PAL);im=im.convert('RGB');frames.append(im)
  im.save(OUT/f'trial-{i:02}-{int(configured)}.png')
  sheet.paste(im,(240*int(configured),i*176+16))
 diff=sum(a!=b for a,b in zip(frames[0].tobytes(),frames[1].tobytes()))
 diffs.append({'trial':i,'different_channel_values':diff});assert diff>40
 d.text((4,i*176+2),f'{i:02} original / configured geometry (synthetic host)',fill=(239,225,176))
sheet.save(OUT/'all-trials-native.png');sheet.resize((960,16*352),Image.Resampling.NEAREST).save(OUT/'all-trials-2x.png')
(OUT/'receipt.json').write_text(json.dumps({'kind':'synthetic host render, developer-only, no controller/hardware claim','coverage':diffs},indent=2)+'\n')
print(OUT/'all-trials-native.png')
