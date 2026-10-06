#!/usr/bin/env python3
"""Actual host-module glyph pixels +2px sampled cumulative collision previews.
Synthetic, stationary targets. Entry/exit-dependent commands71/77 need the
separately tested moving scenarios and intentionally show empty static maps.
"""
from pathlib import Path
import json,subprocess,hashlib,struct
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/underwater-powers-art';OUT.mkdir(parents=True,exist_ok=True)
# Load only the source declaration, without rerunning the acceptance suite.
ns={};source=(ROOT/'tests/test_underwater_powers.py').read_text();exec(source[source.index('SOURCES ='):source.index('INPUT_FILES =')],ns)
sources=['tests/underwater_power_preview.c',*ns['SOURCES'][1:]]
exe=OUT/'preview';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Isrc',*sources,'-o',str(exe)],cwd=ROOT,check=True)
raw=subprocess.check_output([str(exe)],cwd=ROOT);expected=512+24*4*240*160;assert len(raw)==expected
palette=[]
for v, in struct.iter_unpack('<H',raw[:512]):palette.extend([(v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31])
background=(15,30,44);palette[:3]=background
sheet=Image.new('RGB',(520,24*110+40),background);draw=ImageDraw.Draw(sheet)
draw.text((8,6),'SYNTHETIC HOST: warning | active | late | stationary hit union (2px samples)',fill=(226,238,249))
contracts=json.loads((ROOT/'docs/underwater-design/ability_contracts.json').read_text())
for ci,c in enumerate(range(67,91)):
 for j in range(4):
  pixels=raw[512+(ci*4+j)*240*160:512+(ci*4+j+1)*240*160]
  im=Image.frombytes('P',(240,160),pixels);im.putpalette(palette if j<3 else [*background,255,164,83]+[0]*(768-6));im=im.convert('RGB').crop((62,52,182,148))
  sheet.paste(im,(8+j*128,40+ci*110))
 draw.text((8,25+ci*110),f'{c}: {contracts[ci]["primitive"]}',fill=(215,231,245))
sheet.save(OUT/'runtime-shapes-1x.png');sheet.resize((1040,sheet.height*2),Image.Resampling.NEAREST).save(OUT/'runtime-shapes-2x.png')
meta={'kind':'synthetic-host-actual-native-glyph-pixels-and-sampled-cumulative-collision','size':[240,160],'crop':[62,52,182,148],'grid_spacing_px':2,'phase':'neutral target, each cast starts fresh','stationary_exceptions':[71,77],'scope':'Actual C power tick/draw with synthetic object upload, collision and roster. No companion body, world art, gameplay acquisition, OAM scanline or controller proof.','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
(OUT/'runtime-shapes.json').write_text(json.dumps(meta,indent=2)+'\n');print(OUT/'runtime-shapes-1x.png')
