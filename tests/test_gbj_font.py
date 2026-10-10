#!/usr/bin/env python3
"""Independent source-atlas and native-size GBJ regression tests."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets'))
from gbj_font import glyph,render_text,fallback_glyph,fallback,latin_fallback
HASHES={
 'GBJ.json':'5ecb03715593756be3c3135bbf4ec18bbde2d57ca3fe65b3011eef7b88ef661c',
 'GBJ.png':'39acffbbb65988a079f9375be66a0446d1db537ac70adb2ae8ef48663ee720fd',
 'GBJ-Slim.json':'38abc3619047c14169a369ec30a842ee7122642adaaae84cb6488ca07ab78063',
 'GBJ-Slim.png':'96fe782302852d7cba95c1fa1e218bdb7155620549d59345a71ccc8eb6e6f379'}
for name,want in HASHES.items():assert hashlib.sha256((ROOT/'assets/fonts/gbj'/name).read_bytes()).hexdigest()==want,name
checked=0
for slim,name in [(False,'GBJ'),(True,'GBJ-Slim')]:
 atlas=Image.open(ROOT/'assets/fonts/gbj'/f'{name}.png').convert('RGB')
 mapping=json.loads((ROOT/'assets/fonts/gbj'/f'{name}.json').read_text())['mapping']
 for char,code in mapping.items():
  actual=glyph(char,slim);i=code-32;origin=(i%16*8,i//16*8)
  # Independent expected source pixels: original dark ink only, with metadata
  # omitted and exact original tile bearings. Test ALL rows, including dakuten.
  for y in range(8):
   for x in range(8):
    rgb=atlas.getpixel((origin[0]+x,origin[1]+y))
    expected=rgb in ((7,24,33),(0,0,0))
    assert bool(actual.getpixel((x,y)) if x<actual.width else 0)==expected,(char,x,y)
  checked+=1
assert glyph('a') is None and glyph('森') is None and glyph('^') is not None
# Kana-region ASCII locations must not be accidentally rendered as wrong kana.
assert glyph('[') is None and glyph('.') is None
for s in ['森の灯が、消えかけている。','ギジズゼゾ / ぱぴぷぺぽ','A B L R START 0123456789','GeeBee https://geebeegb.itch.io/gbj']:
 for slim in (False,True):
  im=render_text(s,15,slim);assert im.getbbox() and im.width<=214
print(f'PASS {checked} official atlas mappings, original hashes, full pixel equality, unsupported-character fallback and mixed baseline bounds')

# Independently padded actual-raster check catches metric/monochrome edge drift.
chars=set(chr(i) for i in range(32,127))
for path in (ROOT/'assets').glob('ui_texts*.json'):
 for text in json.loads(path.read_text()).values():chars.update(text)
for ch in chars:
 if glyph(ch) is not None:continue
 f=latin_fallback() if ord(ch)<128 else fallback()
 padded=Image.new('1',(80,60));ImageDraw.Draw(padded).text((20,19 if ord(ch)<128 else 18),ch,font=f,fill=1)
 actual=fallback_glyph(ch);b=padded.getbbox()
 if b:
  assert sum(bool(v) for v in actual.getdata())==sum(bool(v) for v in padded.getdata()),repr(ch)
print(f'PASS padded actual-raster fallback coverage for {len(chars)} characters, including all printable ASCII')
