#!/usr/bin/env python3
"""Pinned Return G static budget and negative linker checks; no runtime edits."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess
ROOT=Path(__file__).resolve().parents[1]
C_SHA='6db7ebbbe452b69606addabc6f07a322c00bc5d47df9103875483ad135fe6608'
M_SHA='588ef3b212730660ea79e1bef183a60767e01b370f913f205837b3e011c540a4'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--candidate',type=Path,default=ROOT/'build/return-candidate-g-source')
 p.add_argument('--diagnostic',type=Path,default=ROOT/'build/return-g-memory-diagnostic')
 p.add_argument('--output',type=Path,default=ROOT/'docs/return-memory-candidate-G')
 a=p.parse_args();c=a.candidate.resolve();d=a.diagnostic.resolve();o=a.output.resolve();o.mkdir(parents=True,exist_ok=True)
 receipt=json.loads((d/'build-receipt.json').read_text());assert receipt['candidate_rom_sha256']==C_SHA and receipt['candidate_source_manifest_sha256']==M_SHA
 assert sha(c/'build/emberbond.gba')==sha(d/'control/control.gba')==C_SHA
 assert sha(c/'build/source-hashes.json')==M_SHA
 assert sha(d/'build/emberbond.gba')==receipt['diagnostic_rom_sha256']
 cm=json.loads((c/'build/source-hashes.json').read_text());dm=json.loads((d/'build/source-hashes.json').read_text())
 assert len(cm)==len(dm)==1418 and cm.keys()==dm.keys()
 assert all(sha(c/n)==h for n,h in cm.items()) and all(sha(d/n)==h for n,h in dm.items())
 changes=[n for n in cm if cm[n]!=dm[n]];assert changes==['src/startup.s']
 baseline_path=ROOT/'docs/underwater-memory/candidate-k/memory-budget.json';baseline=json.loads(baseline_path.read_text())
 assert baseline['rom_bytes']==9777176 and baseline['candidate_rom_sha256']=='df3733446cda3d41c2e78da134b25cd446846d6283e4ac5dc47b3fcaa3f98607'
 sections={};mapping=(c/'build/emberbond.map').read_text()
 for n in ('text','iwram','data','bss'):
  match=re.search(r'^\.'+n+r'\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)',mapping,re.M);assert match
  sections[n]={'start':int(match[1],16),'bytes':int(match[2],16)}
 rom=(c/'build/emberbond.gba').stat().st_size;ewram=sum(sections[n]['bytes'] for n in ('data','bss'));span=sections['bss']['start']+sections['bss']['bytes']-0x02000000;iwram=sections['iwram']['bytes'];gap=0x03007000-sections['iwram']['start']-iwram
 rows=[]
 for f in sorted((d/'build').glob('*.su')):
  for line in f.read_text().splitlines():
   loc,b,k=line.split('\t');rows.append({'location':loc,'function':loc.rsplit(':',1)[1],'bytes':int(b),'qualifier':k,'object':f.stem})
 rows.sort(key=lambda r:(-r['bytes'],r['location']))
 (o/'stack-usage.tsv').write_text('location\tbytes\tqualifier\tobject\n'+''.join(f'{r["location"]}\t{r["bytes"]}\t{r["qualifier"]}\t{r["object"]}\n' for r in rows))
 growth={'rom':rom-baseline['rom_bytes'],'ewram_sections':ewram-baseline['ewram_data_plus_bss_bytes'],'ewram_occupied_span':span-(baseline['sections']['bss']['start']+baseline['sections']['bss']['bytes']-0x02000000),'iwram':iwram-baseline['iwram_code_bytes']}
 targets={'rom_increment_2MiB':growth['rom']<=2*1024*1024,'ewram_increment_4KiB':growth['ewram_occupied_span']<=4096,'iwram_no_growth':growth['iwram']<=0}
 hardware={'rom_within_32MiB':rom<=32*1024*1024,'ewram_span_within_256KiB':span<=256*1024,'iwram_code_below_stack_floor':gap>=0}
 assert all(targets.values()) and all(hardware.values())
 report={'candidate_rom_sha256':C_SHA,'candidate_source_manifest_sha256':M_SHA,'candidate_elf_sha256':sha(c/'build/emberbond.elf'),'candidate_map_sha256':sha(c/'build/emberbond.map'),'source_inputs':len(cm),'source_change_only':changes,'diagnostic_build_receipt_sha256':sha(d/'build-receipt.json'),'baseline_evidence_sha256':sha(baseline_path),'baseline_rom_bytes':baseline['rom_bytes'],'baseline_rom_sha256':baseline['candidate_rom_sha256'],'sections':sections,'rom_bytes':rom,'rom_hardware_limit_bytes':32*1024*1024,'rom_hardware_remaining_bytes':32*1024*1024-rom,'ewram_data_plus_bss_bytes':ewram,'ewram_alignment_padding_bytes':span-ewram,'ewram_occupied_span_bytes':span,'ewram_hardware_limit_bytes':256*1024,'ewram_hardware_remaining_bytes':256*1024-span,'iwram_code_bytes':iwram,'iwram_code_end':hex(0x03000000+iwram),'gap_to_reserved_stack_floor_bytes':gap,'system_stack_range':['0x03007000','0x03007f00'],'system_stack_reserved_bytes':3840,'upper_256_bytes_excluded_from_probe':True,'incremental_growth_bytes':growth,'original_targets_bytes':{'rom':2*1024*1024,'ewram':4096,'iwram':0},'original_target_checks':targets,'original_target_remaining_bytes':{'rom':2*1024*1024-growth['rom'],'ewram_occupied_span':4096-growth['ewram_occupied_span'],'iwram_net_reduction':-growth['iwram']},'hardware_checks':hardware,'gcc_stack_records':len(rows),'non_static_records':[r for r in rows if r['qualifier']!='static'],'largest_individual_frames':rows[:25],'limitations':['GCC reports individual frames, not aggregate call-chain stack, assembly/libgcc paths, or an exhaustive proof.','Original zero IWRAM target is evaluated as net growth versus delivered Underwater; IWRAM code is changed, not byte-identical.','Native diagnostic timing is never release timing.']}
 prefix=str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-')
 nm=subprocess.check_output([prefix+'nm','-S','--size-sort',str(c/'build/emberbond.elf')],text=True)
 objects=[]
 for line in nm.splitlines():
  bits=line.split()
  if len(bits)==4 and bits[3] in ('adventure_save','scratch','scan','admission_job','evolution_job','preflight','magma_return_job','job') and bits[2].lower()=='b':
   objects.append({'name':bits[3],'address':bits[0],'bytes':int(bits[1],16)})
 report['selected_persistent_ewram_objects']=objects
 report['compiler_version']=subprocess.check_output([prefix+'gcc','--version'],text=True).splitlines()[0]
 report['diagnostic_build_log_sha256']=sha(d/'diagnostic-build.log')
 (o/'memory-budget.json').write_text(json.dumps(report,indent=2)+'\n')
 for src,dst in ((d/'build-receipt.json','diagnostic-build-receipt.json'),(d/'diagnostic-build.log','diagnostic-build.log'),(d/'src/startup.s','diagnostic-startup.s')):shutil.copyfile(src,o/dst)
 prefix=str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-');cc=prefix+'gcc';tmp=d/'return-link-limit-probes';tmp.mkdir(exist_ok=True)
 line=next(l for l in subprocess.check_output(['make','-pn','ARM_PREFIX='+prefix],cwd=d,text=True).splitlines() if l.startswith('OBJECTS := '));objects=[str(d/f) for f in line.split(':= ',1)[1].split()]
 diagnostic_iwram_bytes=int(re.search(r'^\.iwram\s+0x[0-9a-f]+\s+(0x[0-9a-f]+)',(d/'build/emberbond.map').read_text(),re.M)[1],16)
 diagnostic_gap=0x7000-diagnostic_iwram_bytes
 probes=[]
 for n,s,flags,size,expected in [('iwram','.iwram.text.probe','ax',diagnostic_gap+64,'IWRAM code overlaps reserved stack space'),('ewram','.bss.probe','aw',256*1024,'EWRAM'),('rom','.rodata.probe','a',32*1024*1024,'ROM')]:
  source=tmp/(n+'.s');obj=tmp/(n+'.o');source.write_text(f'.section {s},"{flags}",%progbits\n.balign 4\n.space {size}\n')
  subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-c',str(source),'-o',str(obj)],check=True,capture_output=True)
  res=subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(d/'linker.ld')+',-Map,'+str(tmp/(n+'.map')),*objects,str(obj),'-lgcc','-o',str(tmp/(n+'.elf'))],text=True,capture_output=True)
  log=res.stdout+res.stderr;(o/(n+'-overflow-link.log')).write_text(log);assert res.returncode and expected in log
  probes.append({'probe':n,'additional_bytes':size,'exit_code':res.returncode,'expected_rejection':expected,'observed':True})
 (o/'link-limit-probes.json').write_text(json.dumps({'runtime_files_changed':False,'candidate_rom_sha256_after':sha(c/'build/emberbond.gba'),'diagnostic_rom_sha256_after':sha(d/'build/emberbond.gba'),'linker_sha256':sha(d/'linker.ld'),'probes':probes},indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
