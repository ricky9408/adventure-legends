#!/usr/bin/env python3
"""Build a fresh paired canary ROM and verify an exact uninstrumented control.
Only the new --output directory is written; production inputs are read-only.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2]
FLAGS='-mcpu=arm7tdmi -mthumb-interwork -mthumb -O2 -g -std=c99 -ffreestanding -fno-builtin -fno-strict-aliasing -fomit-frame-pointer -Wall -Wextra -MMD -MP -fstack-usage'
FILL='''    @ DIAGNOSTIC ONLY: fill only the unused SYSTEM stack before calling C.
    @ No IRQ/SVC/BIOS storage, globals or game progress are touched.
    ldr r0, =0x03007000
    ldr r1, =0x03007F00
    ldr r2, =0xA55AC33C
9:  cmp r0, r1
    strlo r2, [r0], #4
    blo 9b
'''
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--runtime-root',type=Path,default=ROOT);ap.add_argument('--makefile',type=Path,default=ROOT/'Makefile');a=ap.parse_args()
 candidate=a.candidate.resolve();out=a.output.resolve();runtime=a.runtime_root.resolve();manifest=candidate/'source-hashes.json';entries=json.loads(manifest.read_text());expected=sha(candidate/'emberbond.gba')
 assert all(sha(runtime/p)==v for p,v in entries.items()),'Runtime sources must exactly match the chosen candidate manifest'
 out.mkdir(parents=True,exist_ok=False)
 for p in entries:
  target=out/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(runtime/p,target)
 shutil.copyfile(a.makefile.resolve(),out/'Makefile');(out/'tools').mkdir(exist_ok=True)
 for n in ('fix_header.py','freeze_runtime_sources.py'):shutil.copyfile(ROOT/'tools'/n,out/'tools'/n)
 shutil.copyfile(manifest,out/'candidate-source-hashes.json');(out/'control').mkdir();shutil.copyfile(out/'src/startup.s',out/'control/startup.s')
 startup=out/'src/startup.s';s=startup.read_text();needle='    ldr sp, =0x03007F00\n';assert s.count(needle)==1;startup.write_text(s.replace(needle,needle+FILL))
 prefix=str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-');cc=prefix+'gcc'
 p=subprocess.run(['make','-j4','ARM_PREFIX='+prefix,'CFLAGS='+FLAGS,'all'],cwd=out,text=True,capture_output=True);(out/'diagnostic-build.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-g','-x','assembler-with-cpp','-c',str(out/'control/startup.s'),'-o',str(out/'control/startup.o')],check=True)
 line=next(l for l in subprocess.check_output(['make','-pn','ARM_PREFIX='+prefix],cwd=out,text=True).splitlines() if l.startswith('OBJECTS := '));objs=[str(out/('control/startup.o' if p=='build/startup.o' else p)) for p in line.split(':= ',1)[1].split()]
 subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(out/'linker.ld')+',-Map,'+str(out/'control/control.map'),*objs,'-lgcc','-o',str(out/'control/control.elf')],check=True)
 subprocess.run([prefix+'objcopy','-O','binary',str(out/'control/control.elf'),str(out/'control/control.gba')],check=True)
 subprocess.run(['python3',str(out/'tools/fix_header.py'),str(out/'control/control.gba')],check=True)
 actual=sha(out/'control/control.gba');assert actual==expected,(actual,expected)
 newer=json.loads((out/'build/source-hashes.json').read_text());changed=[p for p in entries if entries[p]!=newer[p]];assert changed==['src/startup.s']
 receipt={'candidate_rom_sha256':expected,'candidate_source_manifest_sha256':sha(manifest),'control_rom_sha256':actual,'control_byte_identical_to_candidate':True,'diagnostic_rom_sha256':sha(out/'build/emberbond.gba'),'diagnostic_source_manifest_sha256':sha(out/'build/source-hashes.json'),'runtime_source_changes':changed,'compiler_flags':FLAGS,'source_inputs':len(entries),'script_sha256':sha(Path(__file__))}
 (out/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
