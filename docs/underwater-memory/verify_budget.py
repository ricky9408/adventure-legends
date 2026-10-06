#!/usr/bin/env python3
"""Read-only candidate accounting plus explicit proposal comparison.
The 2MiB original chapter target is reported as failed, never silently raised.
"""
from pathlib import Path
import argparse,hashlib,json,re
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
C=ROOT/'build/underwater-candidate-a';D=ROOT/'build/underwater-memory-diagnostic/build'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 global C,D,OUT
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,default=C);ap.add_argument('--stack-build',type=Path,default=D);ap.add_argument('--output-dir',type=Path,default=OUT);ap.add_argument('--expected-sha',default='0d7fd78733405a6fc8ec6eeca68ad207dfb11b91dcfe44a8d67f312552b46675');a=ap.parse_args();C=a.candidate.resolve();D=a.stack_build.resolve();OUT=a.output_dir.resolve();OUT.mkdir(parents=True,exist_ok=True)
 assert sha(D.parent/'control/control.gba')==a.expected_sha,'Stack-usage objects must reproduce the candidate in control link'
 assert sha(C/'emberbond.gba')==a.expected_sha
 mapping=(C/'emberbond.map').read_text();sections={}
 for name in ('text','iwram','data','bss'):
  match=re.search(r'^\.'+name+r'\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)',mapping,re.M);assert match
  sections[name]={'start':int(match[1],16),'bytes':int(match[2],16)}
 baseline=json.loads((ROOT/'docs/underwater-design/accepted-magma-baseline.json').read_text())
 old=baseline['artifacts']['Adventure-Legends-Emberbond.gba']['bytes'];size=(C/'emberbond.gba').stat().st_size;delta=size-old
 assertions={
  'rom_within_32MiB_hardware_window':size<=32*1024*1024,
  'iwram_code_ends_at_or_before_reserved_stack_floor':sections['iwram']['start']+sections['iwram']['bytes']<=0x03007000,
  'ewram_data_and_bss_within_256KiB':sections['bss']['start']+sections['bss']['bytes']<=0x02040000,
  'system_stack_reserve_is_3840_bytes':0x03007F00-0x03007000==3840,
 }
 assert all(assertions.values())
 rows=[]
 for p in sorted(D.glob('*.su')):
  for line in p.read_text().splitlines():
   location,n,kind=line.split('\t');rows.append({'location':location,'function':location.rsplit(':',1)[1],'bytes':int(n),'qualifier':kind,'object':p.stem})
 rows.sort(key=lambda r:(-r['bytes'],r['location']))
 (OUT/'stack-usage.tsv').write_text('location\tbytes\tqualifier\tobject\n'+''.join(f'{r["location"]}\t{r["bytes"]}\t{r["qualifier"]}\t{r["object"]}\n' for r in rows))
 report={
  'candidate_rom_sha256':sha(C/'emberbond.gba'),'candidate_elf_sha256':sha(C/'emberbond.elf'),'candidate_map_sha256':sha(C/'emberbond.map'),
  'rom_bytes':size,'rom_hard_limit_bytes':32*1024*1024,'rom_hard_limit_remaining_bytes':32*1024*1024-size,'sections':sections,
  'ewram_data_plus_bss_bytes':sections['data']['bytes']+sections['bss']['bytes'],'ewram_remaining_bytes':256*1024-sections['data']['bytes']-sections['bss']['bytes'],
  'iwram_code_bytes':sections['iwram']['bytes'],'gap_to_reserved_system_stack_bytes':0x7000-sections['iwram']['bytes'],'system_stack_reserved_bytes':3840,
  'hard_limit_assertions':assertions,'prior_magma_rom_bytes':old,'prior_magma_rom_sha256':baseline['artifacts']['Adventure-Legends-Emberbond.gba']['sha256'],
  'chapter_delta_bytes':delta,'original_chapter_target_bytes':2*1024*1024,'original_chapter_target_met':delta<=2*1024*1024,'original_target_exceeded_bytes':max(0,delta-2*1024*1024),
  'proposed_adjusted_chapter_budget_bytes':int(2.5*1024*1024),'proposed_adjusted_budget_would_fit':delta<=int(2.5*1024*1024),'proposed_adjusted_budget_headroom_bytes':int(2.5*1024*1024)-delta,
  'budget_status':'Original 2MiB chapter target exceeded. 2.5MiB is an explicit proposed adjustment, not a retroactive original-budget pass.',
  'adjustment_rationale':'Four 480x320 maps plus four 240x160 maps, collision masks and localized room art, 196632 bytes of creature art, Japanese UI glyph masks, and chapter gameplay code. No map reduction or quality loss was silently substituted.',
  'stack_usage_function_records':len(rows),'non_static_stack_records':[r for r in rows if r['qualifier']!='static'],'largest_individual_frames':rows[:25],
  'static_stack_limitation':'Individual GCC frames do not sum callees, capture unseen assembly/library paths, or prove the maximum call-chain depth.'}
 (OUT/'memory-budget.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('largest_individual_frames','sections')},indent=2))
if __name__=='__main__':main()
