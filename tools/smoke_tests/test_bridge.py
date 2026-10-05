"""Hardware-level regression smoke test for the mGBA wrapper."""
from pathlib import Path
import struct,sys
TOOLS=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(TOOLS))
from mgba_runner import Emulator
OUT=Path(__file__).resolve().parent
rom=bytearray(1024)
struct.pack_into('<I',rom,0,0xea00002e)  # ARM branch from start to offset 0xC0
struct.pack_into('<I',rom,0xc0,0xeafffffe) # Infinite ARM branch, video still advances
rom[0xb2]=0x96
(OUT/'smoke.gba').write_bytes(rom)
with Emulator(OUT/'smoke.gba') as e:
 e.frames(1)
 e.write(0x04000000,0x403,2) # Mode 3 / BG2
 for y in range(160):
  for x in range(240):e.write(0x06000000+2*(y*240+x),(31,31<<5,31<<10)[x//80],2)
 e.frames(2)
 im=e.screenshot(OUT/'smoke-colors.png')
 assert [im.getpixel(p) for p in [(40,80),(120,80),(200,80)]]==[(255,0,0),(0,255,0),(0,0,255)]
 e.frames(2,'A+LEFT')
 assert e.read(0x04000130,2)==0x3de
 e.write(0x02000000,0xdeadbeef);e.state(OUT/'smoke.state');e.write(0x02000000,0);e.state(OUT/'smoke.state',True)
 assert e.read(0x02000000)==0xdeadbeef
 print('PASS: native core video, key bitmask, frame stepping, memory, savestate')
