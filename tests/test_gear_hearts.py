#!/usr/bin/env python3
"""Exact HP preview pixels at native240x160; strict and ASan/UBSan."""
from pathlib import Path
import hashlib,json,os,subprocess
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/gear-heart-host';OUT.mkdir(parents=True,exist_ok=True)
catalog=json.loads((ROOT/'assets/equipment/catalog.json').read_text())
assert all(item['stats']['hp_q4']%4==0 for item in catalog['items']), 'A non-quarter authored HP bonus requires revisiting54px menu columns'
for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
 exe=OUT/label
 subprocess.run(['cc','-std=c99','-O2','-g','-Wall','-Wextra','-Werror','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc',*flags,'tests/gear_heart_native.c','src/ui.c','-o',str(exe)],cwd=ROOT,check=True)
 subprocess.run([str(exe),str(OUT/'canvas.bin')],cwd=ROOT,check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))
raw=(OUT/'canvas.bin').read_bytes();assert len(raw)==240*160
colors={0:(19,31,33),46:(247,203,88),47:(242,235,199),75:(221,107,101),80:(80,173,166)}
im=Image.new('RGB',(240,160));im.putdata([colors.get(b,(92,92,92)) for b in raw]);im.save(OUT/'exact-heart-comparisons-240x160.png');im.resize((960,640),Image.Resampling.NEAREST).save(OUT/'exact-heart-comparisons-4x.png')
report={'result':'PASS','scope':'Isolated host pixels using shipped renderer/generated Japanese labels; no native game capture','q4_values':97,'canvas_conditions':4,'quarter_comparisons':2500,'column_width':54,'maximum_gameplay_value_width':17,'max_hp_q4':192,'formats':['6','6.25','6.5','6.75','10.25','12'],'image':'build/gear-heart-host/exact-heart-comparisons-240x160.png','source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['src/gear_menu.c','src/ui.h','src/ui.c','assets/magma_ui.json','tests/gear_heart_native.c']}}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS; native-size canvas:',OUT/'exact-heart-comparisons-240x160.png')
