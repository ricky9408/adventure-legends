#!/usr/bin/env python3
"""Strict ARM compile/data/stack audit of the complete current world module.

The call graph sums world-owned function frames. External engine, power and
save-job callees require the whole-ROM stack audit; they are listed explicitly.
"""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/covenants-world-review'
def call(args):return subprocess.check_output(args,cwd=ROOT,text=True,stderr=subprocess.STDOUT)
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 prefix=os.environ.get('ARM_PREFIX',str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-'))
 paths=['src/covenants_game.c']+sorted(str(p.relative_to(ROOT)) for p in (ROOT/'src').glob('covenants_*.inc') if p.name!='covenants_engine.inc')
 paths+=['src/covenants_game.h','src/covenants_art.h','src/covenants_powers.h','src/covenants_quests.h','src/progression.h']
 pins={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
 obj=OUT/'arm-world.o'
 flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-pedantic','-fstack-usage','-Isrc']
 call([prefix+'gcc',*flags,'-c','src/covenants_game.c','-o',str(obj)])
 sections=call([prefix+'objdump','-h',str(obj)]);(OUT/'arm-sections.txt').write_text(sections)
 sizes={n:int(s,16) for n,s in re.findall(r'^\s*\d+\s+(\S+)\s+([0-9a-fA-F]+)\s',sections,re.M)}
 assert sizes['.text']==0,sizes
 assert sizes['.bss']+sizes['.data']<=512,sizes
 stack={}
 for line in (OUT/'arm-world.su').read_text().splitlines():
  ident,size,kind=line.split('\t');assert kind=='static';name=ident.rsplit(':',1)[-1].split('.')[0];stack[name]=max(stack.get(name,0),int(size))
 source='\n'.join((ROOT/p).read_text() for p in paths if p.endswith(('.inc','.c')))
 masked=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',lambda m:' '*len(m[0]),source,flags=re.S)
 bodies={}
 for m in re.finditer(r'^(?:static\s+)?COLD\s+[\w\s*]+?\b(\w+)\s*\([^;{}]*\)\s*\{',masked,re.M):
  end=m.end();depth=1
  while depth:depth+=(masked[end]=='{')-(masked[end]=='}');end+=1
  bodies[m[1]]=masked[m.end():end-1]
 assert set(stack)<=set(bodies),(set(stack)-set(bodies))
 calls={name:set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',body))-{'if','while','for','switch','sizeof','return'} for name,body in bodies.items()}
 def longest(name,seen=()):
  assert name not in seen,('recursive path',seen,name)
  children=[longest(c,seen+(name,)) for c in calls[name] if c in stack]
  child=max(children,default=(0,[]),key=lambda x:x[0]);return (stack[name]+child[0],[name]+child[1])
 peak,path=max((longest(n) for n in stack),key=lambda x:x[0])
 assert peak<=512,(peak,path)
 result={'scope':'Complete real world module; world-owned nested frames only. External stack and whole-ROM budgets require separate evidence.','compiler':call([prefix+'gcc','--version']).splitlines()[0],
  'world_rom_code_bytes':sizes['.text.rom'],'world_rodata_bytes':sizes.get('.rodata',0),'new_iwram_code_bytes':sizes['.text'],'world_initialized_bytes':sizes['.data'],'world_bss_bytes':sizes['.bss'],'world_total_writable_bytes':sizes['.data']+sizes['.bss'],'world_budget_bytes':512,
  'per_function_stack':stack,'maximum_world_owned_nested_stack_bytes':peak,'maximum_world_owned_nested_path':path,'external_callees':sorted(set.union(*calls.values())-set(bodies)), 'source_sha256':pins}
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in pins.items()),'Source changed during ARM audit'
 (OUT/'arm-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('per_function_stack','source_sha256','external_callees')},indent=2))
if __name__=='__main__':main()
