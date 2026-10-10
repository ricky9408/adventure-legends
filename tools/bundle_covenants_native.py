#!/usr/bin/env python3
"""Bundle only a completely passing native matrix; preserve raw evidence hashes."""
import argparse,gzip,hashlib,json,os
from pathlib import Path
import sys,tarfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from northern_journey import newest_bank
from run_covenants_native import frozen_copy
from run_covenants_acceptance import verified_report

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def relative(p):
 p=Path(p).resolve();return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
def write(p,value):Path(p).write_text(json.dumps(value,indent=2)+'\n')
def compress(source,dest):
 raw=Path(source).read_bytes();Path(dest).parent.mkdir(parents=True,exist_ok=True)
 Path(dest).write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(Path(dest).read_bytes())==raw

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--matrix',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True);a=p.parse_args()
 matrix=a.matrix.resolve();status=json.loads((matrix/'acceptance-status.json').read_text())
 assert status['finished'] and status['all_native_gates_passed'] and len(status['required_reports'])==10
 assert not status['synthetic_engine_fixtures_counted']
 pins=status['candidate'];out=a.output.resolve();fixtures=a.fixtures.resolve();out.mkdir(parents=True,exist_ok=False);fixtures.mkdir(parents=True,exist_ok=False)
 frozen_copy(matrix/'acceptance-status.json',out/'acceptance-status.json')
 reports={};summary=[]
 for row in status['required_reports']:
  source=Path(row['path']);assert sha(source)==row['sha256'];r=json.loads(source.read_text())
  ok,why=verified_report(source,pins,r['suite'],r['finished_scope']);assert ok,(row['name'],why)
  dest=out/row['name'];dest.mkdir();compress(source,dest/(source.name+'.gz'))
  trace=source.parent/Path(r['global_native']['trace_path']).name
  frozen_copy(trace,dest/'native-global.jsonl.gz');assert sha(dest/'native-global.jsonl.gz')==r['global_native']['trace_sha256']
  for key,snapshot in r['snapshots'].items():
   sram=source.parent/Path(snapshot['sram_path']).name
   assert sha(sram)==snapshot['sram_sha256'];compress(sram,dest/'sram'/(key+'.sav.gz'))
   shot=source.parent/Path(snapshot['screenshot']).name
   if shot.is_file():frozen_copy(shot,dest/'screenshots'/(key+'.png'))
  for shot in source.parent.glob('legendary-party-*.png'):frozen_copy(shot,dest/'screenshots'/shot.name)
  # Input provenance lives beside the untouched raw producer report.
  for name in ('current-c-import-contract.json','source-producer.json','source-core-prelude.json','source-final-producer.json'):
   file=source.parent/name
   if file.is_file():compress(file,dest/(name+'.gz'))
  reports[row['name']]=(source,r,dest)
  summary.append({'name':row['name'],'suite':r['suite'],'scope':r['finished_scope'],'raw_report_sha256':sha(source),
    'report_path':relative(dest/(source.name+'.gz')),'strict_frames':r['global_native']['strict_frames'],
    'maximum_cycles':r['global_native']['maximum_cycles'],'maximum_obj_count':r['global_native']['maximum_obj_count'],
    'native_trace_sha256':r['global_native']['trace_sha256'],'failures':0})
 # Freeze the exact helper closure used by the documented final command.
 helper=matrix/'native/helpers';hashes=json.loads((helper/'helper-hashes.json').read_text())
 assert all(sha(helper/name)==h for name,h in hashes.items())
 with tarfile.open(out/'accepted-helper-inputs.tar.gz','w:gz') as tar:
  for name in sorted(hashes):tar.add(helper/name,arcname=name,recursive=False)
  tar.add(helper/'helper-hashes.json',arcname='helper-hashes.json',recursive=False)
 frozen_copy(helper/'helper-hashes.json',out/'helper-hashes.json')
 compress(matrix/'native/candidate/source-hashes.json',out/'runtime-source-hashes.json.gz')
 selection=[
  ('full','12-final-cold-after','covenants-all128-72-cold.sav'),
  ('minimal-stage','12-final-cold-after','covenants-minimal18-stage-declined-cold.sav'),
  ('minimal-water','12-final-cold-after','covenants-minimal18-water-declined-cold.sav'),
  ('late-invitations-stage','late-all8-invitations-cold-after','covenants-late26-stage-cold.sav'),
  ('late-invitations-water','late-all8-invitations-cold-after','covenants-late26-water-cold.sav'),
  ('core-stage','original-ending-cold-after','covenants-core18-stage-cold.sav'),
  ('core-water','original-ending-cold-after','covenants-core18-water-cold.sav')]
 rows=[]
 for stage,key,name in selection:
  source,r,dest=reports[stage];snapshot=r['snapshots'][key];sram=source.parent/Path(snapshot['sram_path']).name
  assert snapshot['sram_export']=='mCore.savedataClone' and snapshot['status']['game_state']==1 and not snapshot.get('interrupted_save')
  assert sha(sram)==snapshot['sram_sha256'] and sram.stat().st_size==32768
  assert int.from_bytes(newest_bank(sram.read_bytes())[12:14],'little')==9
  frozen_copy(sram,fixtures/name)
  rows.append({'path':relative(fixtures/name),'sha256':sha(fixtures/name),'bytes':32768,'stage':stage,'source_snapshot':key,
    'producer_path':relative(dest/(source.name+'.gz')),'producer_raw_sha256':sha(source),
    'ordinary_cold_reload_observed':True,'individual_count':len(snapshot['individuals']),
    'history_count':len(snapshot['obtained_form_ids']),'claimed_quest_count':sum(q==3 for q in snapshot['quests']),
    'gear_count':len(snapshot['gear_items']),'fulfilled':snapshot['fulfilled'],'invitations':snapshot['invitations'],
    'snapshot':snapshot,'source_ancestry':r['provenance']})
 provenance={'schema':1,'save_format':5,'content_revision':9,'candidate':pins,'controller_only':True,
   'game_ram_writes':0,'machine_state_loads':0,'synthetic_fixtures_counted':False,
   'matrix_status_path':relative(out/'acceptance-status.json'),'matrix_status_sha256':sha(out/'acceptance-status.json'),
   'fixtures':rows,'scope':'Exact controller-earned cartridge SRAM, copied byte-for-byte from the complete passing native matrix.',
   'usage':'Use the real save decoder. Copy before emulation. Imports preserve prior earned progress and are never new acquisition credit.'}
 write(fixtures/'provenance.json',provenance)
 write(out/'summary.json',{'schema':1,'candidate':pins,'all_ten_native_reports_passed':True,'release_acceptance':False,
   'matrix_source':str(matrix),'reports':summary,'helper_archive_sha256':sha(out/'accepted-helper-inputs.tar.gz'),
   'fixture_provenance_path':relative(fixtures/'provenance.json'),'fixture_provenance_sha256':sha(fixtures/'provenance.json'),
   'physical_hardware_tested':False,'spoilers':True})
 (out/'README.md').write_text('# Covenants accepted native evidence\n\nThis developer bundle contains final-chapter spoilers. Ten strict controller-only reports pass on one exact ROM. Raw report and trace hashes are preserved; SRAM files are ordinary savedataClone exports. No synthetic engine fixture or machine-state import is counted. Physical hardware and final publication are separate.\n\nRun the recipe in docs/covenants-native-controller-contract.md. The exact tested helpers are preserved in accepted-helper-inputs.tar.gz. Decompressed report/SRAM bytes retain their recorded hashes.\n')
 manifest={str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file()}
 write(out/'bundle-hashes.json',manifest)
 print(json.dumps({'reports':len(summary),'authentic_fixtures':len(rows),'bundle':str(out),'fixtures':str(fixtures)}),flush=True)
if __name__=='__main__':main()
