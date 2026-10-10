#!/usr/bin/env python3
"""Exact Horizons legacy-row oracle and unchanged power behavior; host evidence only."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--power-source',type=Path,default=ROOT/'src/horizons_powers.c');p.add_argument('--output',type=Path,default=ROOT/'build/horizons-power-rows');a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);power=a.power_source.resolve()
common=['-std=c99','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-ffunction-sections','-fdata-sections','-I'+str(ROOT/'src'),'-O1','-g','-Wl,--gc-sections']
art=['src/north_art.c','src/south_art.c'];runtime=['tests/horizons_power_cache_host.c',str(power),'src/horizons_power_art.c','src/creatures.c','src/creature_data.c','src/gear_runtime.c','src/combat_rules.c',*art];results=[]
for mode,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
 for label,sources,extra in [('synthetic-corners',['tests/horizons_power_rows_exact.c'],['-Wno-unused-function']),('real-all16-rooms',['tests/horizons_power_rows_exact.c',*art],['-DREAL_ART']),('rectangle-rays',['tests/horizons_power_rect_exact.c'],[]),('all16-commands-and-cache',runtime,[])]:
  target=out/(mode+'-'+label);command=['cc',*common,*flags,*extra,'-DPOWER_SOURCE="'+str(power)+'"',*sources,'-o',str(target)]
  subprocess.run(command,cwd=ROOT,check=True);log=subprocess.check_output([str(target)],cwd=ROOT,text=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'));(out/(mode+'-'+label+'.log')).write_text(log);print(mode,label,log.splitlines()[-1],flush=True);results.append(dict(mode=mode,case=label,result='passed',output=log))
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
sources=[power,ROOT/'tests/horizons_power_rows_exact.c',Path(__file__),ROOT/'tests/horizons_powers_host.c',ROOT/'tests/horizons_power_cache_host.c',ROOT/'tests/horizons_power_rect_exact.c',ROOT/'src/collision_rects.h',ROOT/'src/north_art.c',ROOT/'src/north_art.h',ROOT/'src/south_art.c',ROOT/'src/south_art.h'];sources += sorted((ROOT/'src/north_art_data').glob('*.inc'))+sorted((ROOT/'src/south_art_data').glob('*.inc'))
report={'scope':__doc__,'power_source':str(power),'source_sha256':{str(x.relative_to(ROOT)):sha(x)for x in sources},'results':results,'native_gameplay_evidence':False}
arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
if arm.exists():
 obj=out/'horizons_powers.o';subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-std=c99','-O2','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage','-I'+str(ROOT/'src'),'-c',str(power),'-o',str(obj)],check=True);prefix=str(arm).removesuffix('gcc');sizes=subprocess.check_output([prefix+'size',str(obj)],text=True);sections=subprocess.check_output([prefix+'objdump','-h',str(obj)],text=True);stack=(out/'horizons_powers.su').read_text();row=sizes.splitlines()[1].split();ram=int(row[1])+int(row[2]);maximum=max(int(x.split('\t')[1])for x in stack.splitlines());assert ram<=1024 and maximum<=128 and '.iwram'not in sections;report['ARM']={'rom_bytes':int(row[0]),'ram_bytes':ram,'maximum_function_stack':maximum,'IWRAM_growth':0,'resident_OBJ_growth':0,'sizes':sizes,'stack':stack}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
