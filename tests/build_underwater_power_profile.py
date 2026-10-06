#!/usr/bin/env python3
"""Paired, separate H diagnostic: power timing counters, never a release ROM."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,re
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();c=a.candidate.resolve();out=a.output.resolve();runtime=c/'runtime-source';entries=json.loads((c/'source-hashes.json').read_text())
 assert all(sha(runtime/f)==h for f,h in entries.items());out.mkdir(parents=True,exist_ok=False)
 for f in entries:
  q=out/f;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(runtime/f,q)
 shutil.copyfile(ROOT/'Makefile',out/'Makefile');(out/'tools').mkdir(exist_ok=True)
 for f in ('fix_header.py','freeze_runtime_sources.py'):shutil.copyfile(ROOT/'tools'/f,out/'tools'/f)
 s=(out/'src/underwater_powers.c').read_text();(out/'control').mkdir();(out/'control/underwater_powers.c').write_text(s)
 profile='''\n/* DIAGNOSTIC ONLY: count,inclusive cycles,max inclusive cycles. */
volatile unsigned underwater_power_profile[7][3];
extern unsigned cycle_now(void);
static void profile_end(unsigned i,unsigned started){unsigned elapsed=cycle_now()-started;underwater_power_profile[i][0]++;underwater_power_profile[i][1]+=elapsed;if(elapsed>underwater_power_profile[i][2])underwater_power_profile[i][2]=elapsed;}
static __attribute__((noinline)) int profile_box(int x,int y,int tx,int ty){unsigned n=cycle_now();int r=underwater_game_clear_box(x,y,tx,ty);profile_end(5,n);return r;}
static __attribute__((noinline)) int profile_ray(int x,int y,int tx,int ty){unsigned n=cycle_now();int r=underwater_game_supercover(x,y,tx,ty);profile_end(6,n);return r;}
'''
 # Route only power-side box/ray calls, leaving the hot world functions intact.
 s=s.replace('underwater_game_clear_box(', 'profile_box(').replace('underwater_game_supercover(', 'profile_ray(')
 s=s.replace('typedef struct {int x,y,hp,flash,kind;} Enemy;',profile+'\ntypedef struct {int x,y,hp,flash,kind;} Enemy;')
 defs=[('underwater_power','int','unsigned command','command',0,False),('geometry','void','void','',1,True),('certify_box','void','void','',2,True),('clear','int','int x,int y,int tx,int ty','x,y,tx,ty',3,True),('field_overlap','int','int x,int y,int radius','x,y,radius',4,True)]
 for name,ret,args,call,idx,static in defs:
  pat=r'(?:static (?:__attribute__\(\(noinline\)\) )?)?'+ret+r' '+name+r'\('+re.escape(args)+r'\)\{'
  match=re.search(pat,s);assert match,name
  scope='static ' if static else '';inner='profile_inner_'+name
  reset='unsigned j;for(j=0;j<21;j++)((volatile unsigned*)underwater_power_profile)[j]=0;' if idx==0 else ''
  declaration='static __attribute__((noinline)) '+ret+' '+inner+'('+args+');\n'
  wrapper=scope+'__attribute__((noinline)) '+ret+' '+name+'('+args+'){unsigned started;'+('int result;' if ret=='int' else '')+reset+'started=cycle_now();'+('result=' if ret=='int' else '')+inner+'('+call+');profile_end('+str(idx)+',started);'+('return result;' if ret=='int' else '')+'}\n'
  s=s[:match.start()]+declaration+wrapper+'static __attribute__((noinline)) '+ret+' '+inner+'('+args+'){'+s[match.end():]
 (out/'src/underwater_powers.c').write_text(s)
 prefix=str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-');result=subprocess.run(['make','-j4','ARM_PREFIX='+prefix,'all'],cwd=out,text=True,capture_output=True);(out/'profile-build.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
 # Rebuild just the original power object and relink an exact uninstrumented H.
 line=next(l for l in subprocess.check_output(['make','-pn','ARM_PREFIX='+prefix],cwd=out,text=True).splitlines() if l.startswith('OBJECTS := '));objects=line.split(':= ',1)[1].split()
 flags='-mcpu=arm7tdmi -mthumb-interwork -mthumb -O2 -g -std=c99 -ffreestanding -fno-builtin -fno-strict-aliasing -fomit-frame-pointer -Wall -Wextra'.split()
 subprocess.run([prefix+'gcc',*flags,'-Isrc','-c','control/underwater_powers.c','-o','control/underwater_powers.o'],cwd=out,check=True)
 objects=['control/underwater_powers.o' if o=='build/underwater_powers.o' else o for o in objects]
 subprocess.run([prefix+'gcc','-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,linker.ld,-Map,control/control.map',*objects,'-lgcc','-o','control/control.elf'],cwd=out,check=True)
 subprocess.run([prefix+'objcopy','-O','binary','control/control.elf','control/control.gba'],cwd=out,check=True);subprocess.run(['python3','tools/fix_header.py','control/control.gba'],cwd=out,check=True)
 assert sha(out/'control/control.gba')==sha(c/'emberbond.gba'),'Uninstrumented control must exactly match chosen candidate'
 d={'diagnostic_only':True,'candidate_rom_sha256':sha(c/'emberbond.gba'),'control_rom_sha256':sha(out/'control/control.gba'),'control_byte_identical':True,'profile_rom_sha256':sha(out/'build/emberbond.gba'),'profile_symbols_sha256':sha(out/'build/emberbond.sym'),'counter_symbol':'underwater_power_profile','counter_layout':'7 rows of 3 unsigned32: calls,total inclusive cycles,max inclusive cycles','counter_categories':['cast','geometry','certify_box','clear','field_overlap','clear_box','supercover'],'resets':'Each cast attempt','instrumentation_source_sha256':sha(out/'src/underwater_powers.c'),'caveat':'Inclusive nested timer overhead, wrappers may affect compiler inlining; diagnostic cadence is not release acceptance'}
 (out/'profile-build-receipt.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
if __name__=='__main__':main()
