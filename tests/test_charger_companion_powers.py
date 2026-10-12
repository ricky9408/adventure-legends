#!/usr/bin/env python3
"""Run real companion casts against established ordinary actors and the charger.

The existing suites retain their independent damage/window/geometry/identity
oracles, boss APIs, and explicit ranger-only effects. Only ordinary fixture kind
changes in charger mode. This is host evidence, not controller play.
"""
from pathlib import Path
import argparse,ast,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
SUITES=('northern','southern','magma','underwater','return','horizons','covenants')
def sources(name):
 tree=ast.parse((ROOT/'tests'/('test_'+name+'_powers.py')).read_text())
 for node in tree.body:
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SOURCES'for t in node.targets):return ast.literal_eval(node.value)
 raise AssertionError(name+' source list missing')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'build/charger-companion-powers');p.add_argument('--suites',default=','.join(SUITES));a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 rows=[];inputs=set()
 for name in a.suites.split(','):
  assert name in SUITES;files=[*sources(name),'tests/charger_power_hooks.c'];inputs.update(files)
  for actor in ('ordinary','charger'):
   for mode in ('strict','sanitized'):
    label=name+'-'+actor+'-'+mode;exe=a.output/label
    flags=['-fsanitize=address,undefined','-fno-omit-frame-pointer']if mode=='sanitized'else[]
    kind=['-DCHARGER_POWER_REGRESSION']if actor=='charger'else[]
    # Mach-O dead stripping and ELF section GC keep unused synthetic bridges
    # out; both linkers still reject unresolved symbols in the tested path.
    gc='-Wl,-dead_strip'if sys.platform=='darwin'else'-Wl,--gc-sections'
    cmd=['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-ffunction-sections','-fdata-sections',gc,'-Isrc','-Itests','-DTEST_POWER_'+name.upper(),*kind,*flags,*files,'-o',str(exe)]
    log=a.output/(label+'.log')
    with log.open('w')as f:
     c=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
     r=subprocess.run([str(exe)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})if not c.returncode else c
    row={'suite':name,'actor':actor,'mode':mode,'passed':r.returncode==0,'log':str(log),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()};rows.append(row);print(label,'PASS'if row['passed']else'FAIL',flush=True)
    if not row['passed']:print(log.read_text()[-6000:])
 inputs.update(str(p.relative_to(ROOT))for p in (ROOT/'src').glob('*.h'));inputs.update(('tests/ordinary_enemy_fixture.h','tests/test_charger_companion_powers.py'))
 report={'scope':__doc__,'runs':rows,'passed':all(r['passed']for r in rows),'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()for n in sorted(inputs)}}
 (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');return not report['passed']
if __name__=='__main__':raise SystemExit(main())
