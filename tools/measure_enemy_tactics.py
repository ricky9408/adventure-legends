#!/usr/bin/env python3
"""Compare the cartridge to its pinned pre-review enemy engine and check ROM placement."""
from pathlib import Path
import argparse,json,subprocess,tempfile,re
ROOT=Path(__file__).resolve().parents[1]
def run(args):return subprocess.check_output(args,cwd=ROOT,text=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--arm-prefix',required=True);p.add_argument('--baseline',default='cc5e88edcd27722d4e48c449fcc8d7d94f87f733');p.add_argument('--output',type=Path,default=ROOT/'build/enemy-tactics-host/resources.json');a=p.parse_args()
 gcc=a.arm_prefix+'gcc';size=a.arm_prefix+'size';objdump=a.arm_prefix+'objdump'
 flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-g','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Isrc']
 objects=re.search(r'^OBJECTS := (.+)$',(ROOT/'Makefile').read_text(),re.M)[1].replace('$(BUILD)','build').split()
 def sections(path):
  lines=run([size,'-A',str(path)]).splitlines()
  return {r[0]:int(r[1])for l in lines if len(r:=l.split())>=3 and r[0].startswith('.')}
 with tempfile.TemporaryDirectory(prefix='enemy-budget-')as temp:
  t=Path(temp)
  for stem in ('game','magma_game'):
   src=t/(stem+'.c');src.write_text(run(['git','show',a.baseline+':src/'+stem+'.c']))
   subprocess.run([gcc,*flags,'-c',str(src),'-o',str(t/(stem+'.o'))],cwd=ROOT,check=True)
  prior=[str(t/(Path(o).name))if Path(o).name in ('game.o','magma_game.o')else o for o in objects if not o.endswith('/enemy_tactics.o')]
  baseline=t/'baseline.elf';subprocess.run([gcc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,linker.ld',*prior,'-lgcc','-o',str(baseline)],cwd=ROOT,check=True)
  before=sections(baseline);after=sections(ROOT/'build/emberbond.elf')
  obj=t/'enemy_tactics.o';subprocess.run([gcc,*flags,'-fstack-usage','-c','src/enemy_tactics.c','-o',str(obj)],cwd=ROOT,check=True)
  module=sections(obj);assert not module.get('.text')and not module.get('.data')and not module.get('.bss')
  assert '.text.rom' in module and after['.iwram']<=0x7000
  stack=max(int(l.split('\t')[1])for l in obj.with_suffix('.su').read_text().splitlines()if l)
  report={'baseline_commit':a.baseline,'before':{s:before[s]for s in ('.text','.iwram','.data','.bss')},'after':{s:after[s]for s in ('.text','.iwram','.data','.bss')},'delta':{s:after[s]-before[s]for s in ('.text','.iwram','.data','.bss')},'IWRAM_free_before_stack_reserve':0x7000-after['.iwram'],'module':{s:module.get(s,0)for s in ('.text','.text.rom','.rodata','.data','.bss')},'module_max_function_stack_bytes':stack,'resident_OBJ_layout_unchanged':run(['git','diff',a.baseline,'--','src/obj_layout.h'])=='','native_budget_scope':'See separate controller run; object size is not timing evidence'}
  assert report['delta']['.data']==report['delta']['.bss']==0 and report['resident_OBJ_layout_unchanged']
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
