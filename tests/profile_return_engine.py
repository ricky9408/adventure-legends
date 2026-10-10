#!/usr/bin/env python3
"""Link only an instrumented Return-power object into an immutable engine build.
All other objects remain byte-identical; this is a separate diagnostic ROM.
"""
from pathlib import Path
import argparse,subprocess,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--engine-source',type=Path,required=True);p.add_argument('--power-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--no-instrument',action='store_true');a=p.parse_args();base=a.engine_source.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 prefix=str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-')
 src=a.power_source.read_text()
 profile='''\nvolatile unsigned return_power_profile[7][3];
extern unsigned cycle_now(void);
static void profile_end(unsigned i,unsigned t){unsigned n=cycle_now()-t;return_power_profile[i][0]++;return_power_profile[i][1]+=n;if(n>return_power_profile[i][2])return_power_profile[i][2]=n;}
'''
 if not a.no_instrument:src=src.replace('typedef struct {int x,y,hp,flash,kind;} Enemy;',profile+'\ntypedef struct {int x,y,hp,flash,kind;} Enemy;')
 defs=[('return_power','int','unsigned command','command',0,False),('geometry','void','void','',1,True),('return_powers_tick','void','void','',2,False),('return_powers_draw','void','void','',3,False),('return_powers_intercept_shot','int','unsigned i,int x,int y,int tx,int ty,int eligible','i,x,y,tx,ty,eligible',4,False),('clear','int','int x,int y,int tx,int ty','x,y,tx,ty',5,True),('return_powers_overlap','int','int x,int y,int radius','x,y,radius',6,False)]
 for name,ret,args,call,idx,static in ([] if a.no_instrument else defs):
  pat=r'(?:static )?'+ret+' '+name+r'\('+re.escape(args)+r'\)\{';m=re.search(pat,src);assert m,name
  inner='profile_inner_'+name;scope='static ' if static else ''
  decl='static __attribute__((noinline)) '+ret+' '+inner+'('+args+');\n'
  wrapper=scope+'__attribute__((noinline)) '+ret+' '+name+'('+args+'){unsigned t=cycle_now();'+('int r=' if ret=='int' else '')+inner+'('+call+');profile_end('+str(idx)+',t);'+('return r;' if ret=='int' else '')+'}\n'
  src=src[:m.start()]+decl+wrapper+'static __attribute__((noinline)) '+ret+' '+inner+'('+args+'){'+src[m.end():]
 (out/'return_powers.c').write_text(src)
 flags='-mcpu=arm7tdmi -mthumb-interwork -mthumb -O2 -g -std=c99 -ffreestanding -fno-builtin -fno-strict-aliasing -fomit-frame-pointer -Wall -Wextra -Werror'.split()
 obj=out/'return_powers.o';subprocess.run([prefix+'gcc',*flags,'-I'+str(base/'src'),'-c',str(out/'return_powers.c'),'-o',str(obj)],check=True)
 line=next(l for l in subprocess.check_output(['make','-pn','ARM_PREFIX='+prefix],cwd=base,text=True).splitlines() if l.startswith('OBJECTS := '));names=line.split(':= ',1)[1].split();objects=[str(obj) if Path(n).name=='return_powers.o' else str(base/n) for n in names]
 elf=out/'profile.elf';rom=out/'profile.gba';sym=out/'profile.sym'
 subprocess.run([prefix+'gcc','-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(base/'linker.ld')+',-Map,'+str(out/'profile.map'),*objects,'-lgcc','-o',str(elf)],check=True)
 subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True);sym.write_text(subprocess.check_output([prefix+'nm','-n',str(elf)],text=True))
 receipt={'diagnostic_only':True,'instrumented':not a.no_instrument,'original_engine_ROM':sha(base/'build/emberbond.gba'),'power_source':str(a.power_source),'power_source_sha256':sha(a.power_source),'profile_ROM_sha256':sha(rom),'profile_symbols_sha256':sha(sym),'profile_ELF_sha256':sha(elf),'categories':[] if a.no_instrument else [v[0] for v in defs],'counters':None if a.no_instrument else '7x3 u32: calls,total inclusive cycles,max inclusive cycles','note':('Uninstrumented replacement power object; all other engine objects unchanged. Synthetic fixture feasibility only.' if a.no_instrument else 'Instrumentation has nested timer overhead and noinline effects. Other engine objects are unchanged. Not release cadence acceptance.')}
 (out/'profile-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
