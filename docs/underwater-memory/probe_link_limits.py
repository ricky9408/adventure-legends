#!/usr/bin/env python3
"""Separate negative diagnostic links. Never changes candidate/linker inputs."""
from pathlib import Path
import argparse,json,subprocess
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'build/underwater-memory-diagnostic';OUT=ROOT/'docs/underwater-memory';ap=argparse.ArgumentParser();ap.add_argument('--diagnostic-root',type=Path,default=SRC);ap.add_argument('--output-dir',type=Path,default=OUT);a=ap.parse_args();SRC=a.diagnostic_root.resolve();OUT=a.output_dir.resolve();OUT.mkdir(parents=True,exist_ok=True);TMP=SRC/'link-limit-probes';TMP.mkdir(exist_ok=True)
prefix=str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-');cc=prefix+'gcc'
line=next(l for l in subprocess.check_output(['make','-pn','ARM_PREFIX='+prefix],cwd=SRC,text=True).splitlines() if l.startswith('OBJECTS := '));objects=[str(SRC/p) for p in line.split(':= ',1)[1].split()]
records=[]
for name,section,flags,size,expected in [('iwram','.iwram.text.probe','ax',512,'IWRAM code overlaps reserved stack space'),('ewram','.bss.probe','aw',256*1024,'EWRAM'),('rom','.rodata.probe','a',32*1024*1024,'ROM')]:
 src=TMP/(name+'.s');obj=TMP/(name+'.o');src.write_text(f'.section {section},"{flags}",%progbits\n.balign 4\n.space {size}\n')
 subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-c',str(src),'-o',str(obj)],check=True,capture_output=True)
 p=subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(SRC/'linker.ld')+',-Map,'+str(TMP/(name+'.map')),*objects,str(obj),'-lgcc','-o',str(TMP/(name+'.elf'))],text=True,capture_output=True)
 log=p.stdout+p.stderr;(OUT/(name+'-overflow-link.log')).write_text(log)
 assert p.returncode and expected in log,(name,p.returncode,log)
 records.append({'probe':name,'additional_bytes':size,'exit_code':p.returncode,'expected_rejection_observed':True,'expected_diagnostic':expected})
(OUT/'link-limit-probes.json').write_text(json.dumps({'production_artifacts_modified':False,'linker_script_modified':False,'probes':records},indent=2)+'\n');print(json.dumps(records,indent=2))
