#!/usr/bin/env python3
"""Chapter9 original scenery: deterministic bytes, exact foot geometry and ROM.
These are host/resource tests, not a substitute for native controller testing.
"""
from pathlib import Path
from PIL import Image,ImageFont
import hashlib,json,subprocess,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets'))
import generate_covenants_region as art
class CovenantsArt(unittest.TestCase):
 def test_regeneration_collision_all_dynamics_and_safe_shortcuts(self):
  # build() runs the real full11x11 foot flood through all integer positions,
  # every-pixel row-lookup equivalence and actual visible target coverage.
  generated=art.build()
  for path,data in generated.items():self.assertEqual(path.read_bytes(),data,str(path))
 def test_native_palette_scene_identity_and_transparency(self):
  rasters=[]
  for r in json.loads((art.OUT/'geometry.json').read_text())['rooms']:
   p=art.OUT/(r['key']+'.png');im=Image.open(p)
   self.assertEqual(im.mode,'P');self.assertEqual(im.size,(r['width'],r['height']));self.assertNotIn(0,im.tobytes());self.assertEqual(hashlib.sha256(im.tobytes()).hexdigest(),r['bitmap_sha256']);rasters.append(r['bitmap_sha256'])
   # Humans/rest/legends are dynamic/OAM-only; raw and developer staging differ.
   self.assertNotEqual(im.tobytes(),Image.open(art.OUT/(r['key']+'_staged.png')).tobytes())
  self.assertEqual(len(set(rasters)),8)
  for name in art.NAMES:
   im=Image.open(art.OUT/'sprites'/(name.lower()+'.png'));self.assertEqual(im.size,(16,16));self.assertIn(0,im.tobytes());self.assertGreater(sum(v!=0 for v in im.tobytes()),12)
 def test_dialogue_pair_and_japanese_native_width(self):
  ja=json.loads((ROOT/'assets/covenants_ui_texts.json').read_text());en=json.loads((art.OUT/'ui_english_developer.json').read_text());self.assertEqual(set(ja),set(en))
  f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',12,index=0)
  for k,v in ja.items():self.assertLessEqual(f.getbbox(v)[2],220,(k,v));self.assertTrue(k.startswith('CV_'))
  for prefix in ['TRIAL','AFTER','INVITE']:
   for i in range(1,9):
    for suffix in ['A','B']:self.assertIn(f'CV_{prefix}{i}{suffix}',ja)
  for prefix in ['PORCH','PORCH_ASK','HOME','LETTER','END_INVITED','END_WAITING']:
   for suffix in ['A','B']:self.assertIn(f'CV_{prefix}_{suffix}',ja)
 def test_exact_arm_rom_and_no_ram(self):
  cc=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc';self.assertTrue(cc.exists(),'ARM compiler is required for resource acceptance')
  out=ROOT/'build/covenants-art-host';out.mkdir(parents=True,exist_ok=True);obj=out/'covenants_art.o'
  subprocess.run([str(cc),'-mcpu=arm7tdmi','-mthumb','-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-Isrc','-c','src/covenants_art.c','-o',str(obj)],cwd=ROOT,check=True)
  prefix=str(cc).removesuffix('gcc');size=subprocess.check_output([prefix+'size',str(obj)],text=True);fields=size.splitlines()[1].split();rom=int(fields[0]);self.assertEqual(int(fields[1])+int(fields[2]),0);self.assertLessEqual(rom,1300000)
  sections=subprocess.check_output([prefix+'objdump','-h',str(obj)],text=True);self.assertNotIn('.iwram',sections)
  inc=list((ROOT/'src/covenants_art_data').glob('*.inc'));self.assertLess(max(p.stat().st_size for p in inc),30000)
  report={'scope':'Exact ARM art object only; chapter link size and runtime allocation are separate','rom_bytes':rom,'budget_bytes':1300000,'data_bytes':int(fields[1]),'bss_bytes':int(fields[2]),'iwram_bytes':0,'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [ROOT/'src/covenants_art.c',ROOT/'src/covenants_art.h',*inc]}}
  (art.OUT/'arm_resources.json').write_text(json.dumps(report,indent=1)+'\n')
if __name__=='__main__':unittest.main()
