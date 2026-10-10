#!/usr/bin/env python3
"""Real sparse C renderer versus authored palette images: clipping/alignment/masks.

These are host byte contracts, not native frame-performance evidence.
"""
from pathlib import Path
import ctypes as C,json,os,subprocess,tempfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
 manifest=json.loads((ROOT/'assets/feedback_world/manifest.json').read_text());entries=json.loads((ROOT/'assets/feedback_travel_entries.json').read_text())['entries']
 views={}
 for e in entries:
  x,y,w,h=e['footprint'];views.setdefault(e['room'],set()).update((x+w//2-120+d,y+h//2-80+d)for d in(-1,0,1))
 for r in views:views[r].update([(-241,-161),(-1,-1),(0,0),(1,1),(239,159),(240,160),(241,161),(480,320),(2000,2000)])
 cases=0
 with tempfile.TemporaryDirectory(prefix='feedback-rows-')as td:
  td=Path(td);sources=['tests/player_feedback_world_host.c','src/feedback_world.c'];flags=['-std=c99','-O2','-Wall','-Wextra','-Werror','-Isrc','-DGAME_HOST_TEST']
  so=td/'renderer.so';subprocess.run(['cc',*flags,'-shared','-fPIC',*sources,'-o',str(so)],cwd=ROOT,check=True)
  lib=C.CDLL(str(so));pixels=(C.c_ubyte*38400).in_dll(lib,'feedback_pixels')
  for room,cameras in views.items():
   reference=Image.open(ROOT/'assets/feedback_world'/f'overlay-{room:02d}.png')
   for cx,cy in sorted(cameras):
    overlay=reference.crop((cx,cy,cx+240,cy+160)).tobytes();expected=bytearray(c if c else 77 for c in overlay)
    lib.feedback_clear(77);lib.feedback_mask(0,0,0,0,0);lib.feedback_world_draw(room,cx,cy);assert bytes(pixels)==expected,(room,cx,cy,'unmasked');cases+=1
    for l,t,r,b in[(26,29,214,160),(8,31,232,150),(8,31,232,153),(12,42,228,147),(20,38,220,152),(6,99,234,155)]:
     lib.feedback_clear(77);lib.feedback_mask(1,l,t,r,b);lib.feedback_world_draw(room,cx,cy);actual=bytearray(pixels);final=expected.copy()
     for y in range(t,b):actual[y*240+l:y*240+r]=b'\x01'*(r-l);final[y*240+l:y*240+r]=b'\x01'*(r-l)
     assert actual==final,(room,cx,cy,l,t,r,b,'opaque composite');cases+=1
  lib.feedback_clear(77);lib.feedback_world_draw(255,0,0);assert bytes(pixels)==b'M'*38400
  exe=td/'sanitizer';subprocess.run(['cc',*flags,'-fsanitize=address,undefined','-fno-omit-frame-pointer','-DFEEDBACK_WORLD_SANITIZER_MAIN',*sources,'-o',str(exe)],cwd=ROOT,check=True)
  subprocess.run([str(exe)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
 print('PASS',len(entries),'entries,',cases,'exact clipped/aligned/opaque comparisons;',manifest['runs'],'baked runs; ASan/UBSan edge sweep')
if __name__=='__main__':main()
