#!/usr/bin/env python3
"""Current native font/corpus proofs; historical GBJ fixtures stay unchanged."""
from pathlib import Path
import argparse,hashlib,json,re,struct,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets'))
import gbj_font as font
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rom',type=Path);parser.add_argument('--symbols',type=Path)
args=parser.parse_args()
assert bool(args.rom)==bool(args.symbols),'--rom and --symbols must be supplied together'
rom=args.rom.read_bytes()if args.rom else None
symbols={v[2]:int(v[0],16)for line in args.symbols.read_text().splitlines()if len(v:=line.split())==3}if args.symbols else {}
rom_tables={'ui':'ui_texts','companion_guide_text':'companion_guide_texts','growth_journal_text':'growth_journal_texts',
 'gear_preview_text':'gear_preview_texts','treasure_text_text':'treasure_text_texts','opening_scene_data':'opening_scene_texts',
 'ending_credits_text':'ending_credits_texts','regional_shop_text':'regional_shop_texts','journey_map_text':'journey_map_texts'}
rom_checked=0;rom_pointers={};rom_endian_negative=False
def rom_read(address,length):
 offset=address-0x08000000;assert 0<=offset<=len(rom)-length,(hex(address),length)
 return rom[offset:offset+length]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(font.NATIVE_FONT)=='02f19467ea7cc235cc06c570b7f6c3b0a12a6f682bc8d74c43f2d323d97bcd12'
assert sha(ROOT/'assets/fonts/pixelmplus/LICENSE_E')=='907e9f5ac24cba6ce2523cd2a66d6ba143e082c685344dfa8d30ef12f67410a0'
assert sha(font.COMPACT_FONT)=='97361b327b410c2cd6e8fe87ed3873387229e76af13829931d6987f267585277'
assert font.native_font().size==12

global_texts={}
for path in (ROOT/'assets').glob('ui_texts*.json'):global_texts.update(json.loads(path.read_text()))
families=[('ui',global_texts,'txt_'),
 ('companion_guide_text',json.loads((ROOT/'assets/companion_guide_text_metrics.json').read_text()),'cg_'),
 ('growth_journal_text',json.loads((ROOT/'assets/growth_journal_metrics.json').read_text()),'gj_'),
 ('gear_preview_text',json.loads((ROOT/'assets/gear_preview_text_metrics.json').read_text()),'gp_'),
 ('treasure_text_text',json.loads((ROOT/'assets/treasure_text_text_metrics.json').read_text()),'tt_'),
 ('opening_scene_data',json.loads((ROOT/'assets/opening_scene_metrics.json').read_text()),'os_'),
 ('ending_credits_text',json.loads((ROOT/'assets/ending_credits_text_metrics.json').read_text()),'ec_'),
 ('regional_shop_text',json.loads((ROOT/'assets/regional_shop_text_metrics.json').read_text()),'rs_'),
 ('journey_map_text',json.loads((ROOT/'assets/journey_map/text_metrics.json').read_text()),'jm_')]
chars=set();checked=0;rows_checked=0;family_counts={}
for family,metadata,prefix in families:
 src=(ROOT/'src'/f'{family}.c').read_text()
 for include in re.findall(r'^#include "([^"]+\.inc)"',src,re.M):src+='\n'+(ROOT/'src'/include).read_text()
 arrays={name:[tuple(map(int,row))for row in re.findall(r'\{(\d+),(\d+),(\d+)\}',data)]
         for name,data in re.findall(r'static const UiRun\s+(\w+)\[\]\s*=\s*\{([^;]+)\};',src)}
 for alias,canonical in re.findall(r'^#define (\w+) (\w+)$',src,re.M):
  assert canonical in arrays,(family,alias,canonical)
  arrays[alias]=arrays[canonical]
 tables=re.findall(r'\{(\d+),(\d+),0,\{(\w+),(\w+)\},\{(\d+),(\d+)\}\}',src)
 assert len(tables)==len(metadata),(family,len(tables),len(metadata))
 for table_index,(w,h,a,b,n,m)in enumerate(tables):
  w,h,n,m=map(int,(w,h,n,m));name=a.removeprefix(prefix).removesuffix('_0');spec=metadata[name]
  text=spec if isinstance(spec,str)else spec['text'];chars.update(text)
  compact=(family=='regional_shop_text'and name.startswith('EFFECT_'))or(family=='gear_preview_text'and name=='UNITS')
  expected=font.render_text(text,h,slim=family=='ui'and h==10,compact=compact)
  if family=='ui'and h==10:assert text.isascii(),('small footer needs Japanese reflow',name)
  assert (w,h)==expected.size,(family,name,w,h,expected.size)
  assert w<=214 and h<=15,(family,name,w,h)
  for align,(array,count)in enumerate(((a,n),(b,m))):
   raw=Image.new('1',(w+align,h));runs=arrays[array]
   assert len(runs)==count or count==0 and runs==[(0,0,0)],(family,name,align)
   for offset,run,mask in runs[:count]:
    assert mask in (1,2,3)and 0<run<=7 and 0<=offset<2048
    for half in range(run):
     y,x=divmod(offset+half,120)
     for bit in (0,1):
      if mask&(1<<bit):
       xx=x*2+bit;assert 0<=xx<w+align and y<h,(family,name,xx,y,w,h)
       raw.putpixel((xx,y),1)
   assert raw.crop((align,0,w+align,h)).tobytes()==expected.tobytes(),(family,name,align)
   rows_checked+=1
  if rom is not None:
   rw,rh,reserved,pa,pb,na,nb=struct.unpack('<HBBIIHH',rom_read(symbols[rom_tables[family]]+table_index*16,16))
   assert (rw,rh,reserved,na,nb)==(w,h,0,n,m),(family,name,'ROM metadata drift')
   for align,(pointer,count)in enumerate(((pa,n),(pb,m))):
    assert pointer%2==0,(family,name,align,'UiRun must remain halfword aligned')
    payload=rom_read(pointer,count*2);raw=Image.new('1',(w+align,h))
    if pointer in rom_pointers:assert payload==rom_pointers[pointer][:len(payload)]
    else:rom_pointers[pointer]=payload
    compiled=[(word&2047,(word>>11)&7,word>>14)for(word,)in struct.iter_unpack('<H',payload)]
    assert compiled==arrays[(a,b)[align]][:count],(family,name,align,'packed ROM field layout drift')
    if payload and not rom_endian_negative:
     # Replay this real compiled array with byte-swapped field words. The
     # independent source tuples must reject a wrong-endian layout, even when
     # the pixels happen to look plausible. No cartridge bytes are changed.
     swapped=[(word&2047,(word>>11)&7,word>>14)for(word,)in struct.iter_unpack('>H',payload)]
     assert swapped!=arrays[(a,b)[align]][:count],(family,name,'endian control ineffective')
     rom_endian_negative=True
    for offset,run,mask in compiled:
     assert mask in (1,2,3)and 0<run<=7
     for half in range(run):
      y,x=divmod(offset+half,120)
      for bit in (0,1):
       if mask&(1<<bit):
        xx=x*2+bit;assert xx<w+align and y<h
        raw.putpixel((xx,y),1)
    assert raw.crop((align,0,w+align,h)).tobytes()==expected.tobytes(),(family,name,align,'ROM pixel drift')
    rom_checked+=1
  checked+=1
 family_counts[family]=len(tables)
if rom is not None:assert rom_endian_negative,'compiled endian rejection control was not exercised'

cjk={c for c in chars if 0x3400<=ord(c)<=0x9fff}
assert cjk and cjk<=font.native_coverage() and cjk<=font.compact_atlas().keys()
for char in cjk:
 native=font.native_glyph(char);assert native.width==12 and native.getbbox()
 assert {native.getpixel((x,y))for y in range(native.height)for x in range(native.width)}<={0,1}
 assert native.getbbox()[3]<=15
try:font.native_glyph('\U0010ffff')
except ValueError:pass
else:raise AssertionError('unsupported font character silently rendered')

# Mutation reproduces the old pre-check canvas bug: 19 source rows cannot be
# admitted into15 merely because paste has already discarded the last4 rows.
original=font.native_glyph
try:
 font.native_glyph=lambda char:Image.new('1',(12,19),1)
 try:font.render_text('鑑',15)
 except AssertionError:pass
 else:raise AssertionError('tall source glyph was silently clipped')
finally:font.native_glyph=original
try:font.render_text('鑑',10)
except AssertionError:pass
else:raise AssertionError('native12px kanji squeezed into10px footer')

probe='static const UiRun a[]={{1,2,3}};\nstatic const UiRun b[]={ {1,2,3} };\nstatic const UiRun c[]={{1,2,1}};\n'
shared=font.deduplicate_spans(probe)
assert '#define b a' in shared and 'static const UiRun c[]' in shared
assert font.deduplicate_spans(probe)==shared==font.deduplicate_spans(shared)
for triple in ('{2048,1,1}','{0,8,1}','{0,0,1}','{0,1,4}'):
 try:font.deduplicate_spans('static const UiRun bad[]={'+triple+'};\n')
 except AssertionError:pass
 else:raise AssertionError('packed span overflow accepted: '+triple)

opening=json.loads((ROOT/'assets/opening_scene.json').read_text())
assert len(opening['pages'])==8 and all(len(page['lines'])==2 for page in opening['pages'])
campaign=json.loads((ROOT/'assets/campaign_dialogue.json').read_text())['dialogue']
assert all(1<=len(scene['pages'])<=6 and all(len(page)==2 for page in scene['pages'])for scene in campaign.values())
credits=json.loads((ROOT/'assets/ending_credits.json').read_text())['lines']
for name in ('PixelMplus12 Regular','itouhiro / M+ FONTS PROJECT','k8x12 bitmap font','Num Kadoma','GeeBee'):assert name in credits
print(json.dumps({'passed':True,'families':family_counts,'texts':checked,'exact_alignment_roundtrips':rows_checked,
 'compiled_rom_pixel_roundtrips':rom_checked,'compiled_rom_unique_span_pointers':len(rom_pointers),
 'compiled_rom_wrong_endian_negative_rejected':rom_endian_negative,
 'unique_characters':len(chars),'unique_bmp_cjk':len(cjk),'missing_native_glyphs':0,'missing_compact_cjk':0,
 'preclip_height_negative_rejected':True,'unsupported_character_negative_rejected':True,
 'native_kanji_to10px_negative_rejected':True,'packed_span_overflow_negatives':4,
 'span_storage_bytes':2,'span_field_format':'little-endian offset11/count3/mask2',
 'native_size':12,'runtime_font_decoding':False},indent=2))
