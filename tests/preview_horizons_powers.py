#!/usr/bin/env python3
"""Contact sheet rasterized from the real host renderer, not guessed shapes.
Run tests/test_horizons_powers.py first. This artifact is synthetic-host evidence,
not a screenshot of production/native gameplay.
"""
from pathlib import Path
import os,sys,subprocess,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'assets'))
from magma_palette import PAL
out=ROOT/'assets/horizons_powers';raw=ROOT/'build/horizons-powers-host/runtime-shapes.bin'
subprocess.run([str(ROOT/'build/horizons-powers-host/strict')],check=True,env=dict(os.environ,HORIZONS_POWER_PREVIEW=str(raw)))
data=raw.read_bytes();assert len(data)==16*4*104*80
sheet=Image.new('RGB',(864,836),(24,31,43));draw=ImageDraw.Draw(sheet)
forms=json.loads((ROOT/'docs/horizons-design/shared_horizons_plan.json').read_text())['forms']
for i,f in enumerate(forms):
 x=(i%2)*432;y=(i//2)*104
 draw.text((x+8,y+2),f"{f['signature_command']}  {f['name']} / {f['ability']['name']}",fill=(255,240,204))
 for k in range(4):
  n=(i*4+k)*104*80;im=Image.frombytes('P',(104,80),data[n:n+104*80]);im.putpalette(PAL);sheet.paste(im.convert('RGB'),(x+8+k*104,y+18))
  # Small neutral cross at the immutable cast origin, never a power pixel.
  ax=x+8+k*104+32;ay=y+18+40;draw.line((ax-2,ay,ax+2,ay),fill=(100,113,130));draw.line((ax,ay-2,ax,ay+2),fill=(100,113,130))
sheet.save(out/'runtime_shapes_native.png')
print(out/'runtime_shapes_native.png')
