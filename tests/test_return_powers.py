#!/usr/bin/env python3
"""Strict/sanitized synthetic Return powers; ARM placement/resource evidence."""
from pathlib import Path
import subprocess,os,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/return-powers-host';OUT.mkdir(parents=True,exist_ok=True)
SOURCES=['tests/return_powers_host.c','src/return_powers.c','src/return_power_art.c','src/creatures.c','src/creature_data.c','src/gear_runtime.c','src/combat_rules.c']
art_before=(ROOT/'src/return_power_art.c').read_bytes()
subprocess.run(['python3','assets/generate_return_powers.py'],cwd=ROOT,check=True)
assert (ROOT/'src/return_power_art.c').read_bytes()==art_before,'Power art must roundtrip deterministically'
# Release module must be warning-free under unmodified standard flags.
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Isrc','-c','src/return_powers.c','-o',str(OUT/'warning-check.o')],cwd=ROOT,check=True)
for name,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
 exe=OUT/name
 subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc',*flags,*SOURCES,'-o',str(exe)],cwd=ROOT,check=True)
 subprocess.run([str(exe)],cwd=ROOT,check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
if arm.exists():
 objs=[]
 for s in SOURCES[1:3]:
  o=OUT/(Path(s).stem+'.o');subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-std=c99','-O2','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fstack-usage','-Isrc','-c',s,'-o',str(o)],cwd=ROOT,check=True);objs.append(str(o))
 prefix=str(arm).removesuffix('gcc');sizes=subprocess.check_output([prefix+'size',*objs],text=True);sections=subprocess.check_output([prefix+'objdump','-h',*objs],text=True);stack='\n'.join(p.read_text() for p in OUT.glob('*.su'));rows=[x.split() for x in sizes.splitlines()[1:]];ram=sum(int(x[1])+int(x[2]) for x in rows);max_stack=max(int(x.split('\t')[1]) for x in stack.splitlines() if x);assert ram<=512 and max_stack<=128 and '.iwram' not in sections
 report={'scope':'synthetic-host-and-ARM-object-only-not-native-gameplay','ram_bytes':ram,'rom_bytes':sum(int(x[0]) for x in rows),'IWRAM_growth':0,'resident_OBJ_growth':0,'maximum_objects':2,'maximum_mark_draws':25,'maximum_function_stack':max_stack,'stack_excludes_external_callbacks_and_IRQ':True,'source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in SOURCES},'sizes':sizes,'stack':stack}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(sizes)
