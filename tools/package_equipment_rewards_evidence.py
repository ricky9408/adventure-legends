#!/usr/bin/env python3
"""Seal exact I4 acceptance evidence after every finite gate succeeds."""
from pathlib import Path
import gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/equipment-rewards/evidence-i4'
ROM='cab76cd98317dfa1dbeaf2713cb4bab42bcdf0973c60cefe3de7e1fbf1aaeddc'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
 host=read('build/equipment-rewards-host-i4/report.json')
 retained=read('build/equipment-rewards-host-i4/retained-62/run-status.json');assert retained['test_commands']==62
 accepted_path=ROOT/'build/equipment-rewards-host-i4/reconciliation/accepted-receipt.json'
 assert sha(accepted_path)=='d0ff20380de5ade2a6476b0e80ee757d31aa265e7fc94f3e300167e0876f7e72'
 accepted=json.loads(accepted_path.read_text());assert accepted['status']=='PASS_AFTER_INFRASTRUCTURE_RETRY'and accepted['counts']['accepted_test_commands_after_retry']==88
 assert accepted['candidate']['emberbond.gba']==ROM
 for r in accepted['original_reports']:assert sha(ROOT/r['path'])==r['sha256']
 assert [r['name']for r in host['runs']if r['status']!='PASS']==['retained-62']
 assert [r['name']for r in retained['runs']if r['status']!='PASS']==['test_connected_roads_engine']
 failure=accepted['original_failed_test']['parsed_setup_failure'];assert not failure['game_assertions_started']and not failure['overwritten_mappings']and failure['errno']==17
 retry=accepted['retry'];assert retry['status']=='PASS'and retry['full_parsed_result']['passed']and not retry['game_assertion_failure_retries']and not retry['forced_mappings']
 assert sha(ROOT/retry['log']['path'])==retry['log']['sha256']and sha(ROOT/retry['execution_receipt']['path'])==retry['execution_receipt']['sha256']
 flow=read('build/treasure-player-flow/i4-summary.json');assert flow['candidate']['rom_sha256']==ROM and flow['native_player_flow_status']=='PASS'
 fresh=flow['main20_fresh_acceptance'];assert fresh['complete']and fresh['accepted']and fresh['all_four_treasures']and fresh['base_companions_at_homecoming']==20
 assert not any(fresh[k]for k in ['game_ram_writes','machine_state_imports','historical_progress_imports','update_misses','flip_misses','cycle_overruns'])
 assert flow['focused_matrix']['passed']and not flow['focused_matrix']['pacing_exceptions']and not flow['focused_matrix']['mGBA_faults']
 capacity=flow['full_capacity'];assert capacity['synthetic']and capacity['codec_valid']and capacity['gameplay_passed']and capacity['performance_passed']
 assert not any(capacity[k]for k in ['missed_updates','missed_flips','cycle_overruns'])and flow['cold_save_reward_audit']['all_pass']
 principal=read('build/equipment-rewards-principal-i4/report.json');assert principal['complete']and not principal['failures']and principal['performance']['strict_measured_pacing_pass']
 for name in ('readable','passive'):
  p=read(f'build/equipment-rewards-{name}-i4/report.json');assert p['complete']and not p['failures']and p['exact_files_unchanged']and not p['performance']['pacing_exceptions']
 review=read('build/reward-integration-review/i4/review.json');assert review['status']=='PASS'and not review['findings']
 media=read('build/equipment-rewards-teaser-i4/verification-receipt.json');assert media['passed']and not media['soundtrack_changed']
 memory=read('build/equipment-rewards-memory-i4/memory-budget.json');assert all(memory['checks'].values())and len(memory['negative_link_probes'])==3 and all(x['exit_code']!=0 for x in memory['negative_link_probes'])
 clean=read('build/equipment-rewards-clean-i4/verification.json');assert clean['result']=='PASS'and all(x['identical']for x in clean['files'].values())
 runtime=read('build/equipment-rewards-i4/source-hashes.json');assert all(sha(ROOT/k)==v for k,v in runtime.items())and sha(ROOT/'build/equipment-rewards-i4/emberbond.gba')==ROM
 paths=[
 'build/equipment-rewards-i4/candidate.json','build/equipment-rewards-i4/source-hashes.json',
 'build/equipment-rewards-host-i4/report.json','build/equipment-rewards-host-i4/retained-62/run-status.json',
 'build/equipment-rewards-principal-i4/report.json','build/equipment-rewards-readable-i4/report.json','build/equipment-rewards-passive-i4/report.json',
 'build/treasure-player-flow/i4-summary.json','build/treasure-player-flow/I4_REVIEW.md','build/treasure-player-flow/i4-cold-save-reward-audit.json',
 'build/treasure-player-flow/i4-fresh-complete-01/summary.json','build/treasure-player-flow/i4-fresh-complete-01/timing-report.json',
 'build/treasure-player-flow/i4-fresh-complete-01/helper-source-hashes.json',
 'build/treasure-player-flow/i4-matrix/report.json','build/treasure-player-flow/i4-full-capacity-room44/diagnostic.json','build/treasure-player-flow/i4-full-capacity-room44/prepared-provenance.json',
 'build/reward-integration-review/i4/review.json','build/reward-integration-review/i4/REVIEW.md','build/reward-integration-review/i4/report.json','build/reward-integration-review/i4/immediate-equip.json','build/reward-integration-review/i4/helper-manifest.json','build/reward-integration-review/i4/renderer-successor-report.json','build/reward-integration-review/i4/portability.json',
 'build/equipment-rewards-teaser-i4/verification-receipt.json','build/equipment-rewards-memory-i4/memory-budget.json','build/equipment-rewards-clean-i4/verification.json',
 'build/equipment-rewards-i4-build.log','build/readable-integration-receipt.json',
 # Preserve the rejected timing decisions without relabeling them.
 'build/treasure-player-flow/i2-fresh-complete-01/timing-report.json','build/treasure-player-flow/i3-full-capacity-room44-03/diagnostic.json',
 'build/treasure-player-flow/snapshot-unroll8-full-capacity/diagnostic.json']
 for section in ('original','regions'):
  base=f'build/treasure-player-flow/i4-fresh-complete-01/{section}/'
  paths.extend(base+n for n in ('report.json','controller-inputs.jsonl.gz','native-frames.jsonl.gz'))
 paths.extend(str(p.relative_to(ROOT))for folder in ('reconciliation','setup-retry')for p in (ROOT/'build/equipment-rewards-host-i4'/folder).iterdir()if p.is_file()and p.suffix in ('.json','.md','.py','.log'))
 paths.extend('build/equipment-rewards-host-i4/'+r['log']for r in host['runs'])
 paths.extend('build/equipment-rewards-host-i4/retained-62/'+r['log']for r in retained['runs'])
 paths.extend(str(p.relative_to(ROOT))for p in (ROOT/'build/equipment-rewards-memory-i4').glob('*-overflow.log'))
 paths.extend(str(p.relative_to(ROOT))for p in (ROOT/'build/reward-integration-review/i4').glob('*.log'))
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for name in sorted(set(paths)):
  p=ROOT/name;assert p.is_file(),name;data=p.read_bytes();dest='--'.join(Path(name).parts[1:]);dest+= ''if p.suffix=='.gz'else'.gz';q=OUT/dest
  q.write_bytes(data if p.suffix=='.gz'else gzip.compress(data,mtime=0));rows.append({'original_path':name,'file':dest,'source_bytes':len(data),'source_sha256':hashlib.sha256(data).hexdigest(),'compressed_bytes':q.stat().st_size,'compressed_sha256':sha(q),'encoding':'original-gzip'if p.suffix=='.gz'else'gzip'})
 for name,source in [('native-gear-preview.png','build/equipment-rewards-teaser-i4/native-equipment-preview.png'),('native-treasure-receipt.png','build/treasure-player-flow/i4-matrix/earned-G7-village-treasure-0-receipt.png')]:
  shutil.copy2(ROOT/source,OUT/name);rows.append({'original_path':source,'file':name,'source_sha256':sha(ROOT/source),'compressed_sha256':sha(OUT/name),'source_bytes':(ROOT/source).stat().st_size,'compressed_bytes':(OUT/name).stat().st_size,'encoding':'PNG'})
 index={'scope':'Exact I4 finite acceptance reports; developer material can contain spoilers. Export verification and Library receipts are separate.','rom_sha256':ROM,'runtime_gates_passed':True,'host_status':'PASS_AFTER_INFRASTRUCTURE_RETRY; original FAIL reports preserved; no game assertion failure retried','host_test_commands':62+len(host['runs'])-1,'native_source_count':len(runtime),'fresh_main_route_forms':20,'not_claimed':['fresh acquisition/player review of all128 forms','physical GBA or other emulator releases','perceptual musical quality','absence of inherited cold-load/live-OBJ limitations','GitHub publication'], 'omissions':'Large repeated fixtures, compiled tools/ROM/ELF, repetitive per-cut SRAM and non-main raw native traces remain ignored development artifacts. Current source, controller recipes and pinned input saves ship; historical omissions preserve prior provenance.','files':rows}
 (OUT/'index.json').write_text(json.dumps(index,indent=2)+'\n');print(json.dumps({'files':len(rows),'bytes':sum(r['compressed_bytes']for r in rows),'host_test_commands':index['host_test_commands']}))
if __name__=='__main__':main()
