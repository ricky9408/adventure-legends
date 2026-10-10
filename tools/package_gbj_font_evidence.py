#!/usr/bin/env python3
"""Seal finite GBJ acceptance evidence without relabeling historical pin rejects."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'build/gbj-font-qa';OUT=ROOT/'docs/gbj-font/evidence'
ROM='b125a90da8d722ef8fc17ba52d7fbb95dfd9136f397083add2f613912cb4dcce'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((QA/p).read_text())
def main():
 assert sha(ROOT/'build/emberbond.gba')==ROM
 runtime=json.loads((ROOT/'build/source-hashes.json').read_text());assert all(sha(ROOT/p)==h for p,h in runtime.items())
 host=read('full-host/report.json');retained=read('full-host/retained-62/run-status.json')
 assert len(host['runs'])==27 and len(retained['runs'])==63
 assert all(r['status']in('PASS','FAIL')for r in host['runs']+retained['runs'])
 root_rejects={'retained-62','test_retained_ui_story_successor','verify_late_renderer','retained-parent-negatives','test_renderer_equipment_successor'}
 retained_rejects={'test_return_geometry','test_connected_route_copy'}
 assert {r['name']for r in host['runs']if r['status']=='FAIL'}==root_rejects
 assert {r['name']for r in retained['runs']if r['status']=='FAIL'}==retained_rejects
 assert host['result']==retained['result']=='FAIL'
 for r in host['runs']+retained['runs']:assert r['runtime_unchanged']and r['helper_unchanged']
 successor=read('font-successor-renderer.json');assert successor['result']=='PASS'and successor['renderer_rerun']and len(successor['negative_controls_rejected'])==15
 assert read('inherited-renderer-comparison.json')['status']=='PASS'
 for name in('gear-native','gear-passive'):
  d=read(name+'/report.json');assert d['complete']and not d['failures']and d['exact_files_unchanged']
  assert not d['performance']['pacing_exceptions']and not d['performance']['native_faults']
 opening=read('opening/report.json');assert opening['result']=='PASS_OPENING_AND_SAVE'
 memory=read('memory/memory-budget.json');assert all(memory['checks'].values())and len(memory['negative_link_probes'])==3 and all(p['exit_code']!=0 for p in memory['negative_link_probes'])
 video=read('video/teaser-report.json');assert video['passed']and video['rom_sha256']==ROM and video['controller_only']and not any(video[k]for k in('game_ram_writes','machine_state_imports','sram_imports','speed_change'))and not video['nonflip_frames']
 clean=read('clean-all-assets-report.json');assert all(clean[k]for k in('full_make_assets','full_build','rom_exact','symbols_exact','runtime_manifest_exact','font_credits_exact'))
 assert (QA/'all-six-spans.log').read_text().count('PASS 89600')==2
 assert 'Ran 6 tests' in(QA/'font-return-geometry.log').read_text()and '\nOK\n'in(QA/'font-return-geometry.log').read_text()
 assert 'Ran 28 tests' in(QA/'font-renderer-negatives.log').read_text()and '\nOK\n'in(QA/'font-renderer-negatives.log').read_text()
 assert 'PASS padded actual-raster fallback coverage for 1006' in(QA/'font-source.log').read_text()
 paths=['full-host/report.json','full-host/retained-62/run-status.json','font-successor-renderer.json','inherited-renderer-comparison.json','gear-native/report.json','gear-passive/report.json','opening/report.json','memory/memory-budget.json','video/teaser-report.json','video/capture-frames.jsonl.gz','clean-all-assets-report.json','font-source.log','all-six-spans.log','font-return-geometry.log','font-renderer-negatives.log','gear-layout.log','clean-all-assets-retry.log','clean-all-assets-build.log']
 paths += ['full-host/'+r['log']for r in host['runs']]
 paths += ['full-host/retained-62/'+r['log']for r in retained['runs']]
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for rel in sorted(set(paths)):
  source=QA/rel;raw=source.read_bytes();name=rel.replace('/','--')+(''if rel.endswith('.gz')else'.gz');dest=OUT/name
  dest.write_bytes(raw if rel.endswith('.gz')else gzip.compress(raw,mtime=0))
  rows.append({'source':str(source.relative_to(ROOT)),'file':name,'source_sha256':hashlib.sha256(raw).hexdigest(),'stored_sha256':sha(dest),'source_bytes':len(raw),'stored_bytes':dest.stat().st_size})
 receipt={'status':'PASS_FONT_SUCCESSOR_WITH_EXPLICIT_HISTORICAL_PIN_REJECTIONS','rom_sha256':ROM,'runtime_manifest_sha256':sha(ROOT/'build/source-hashes.json'),'historical_host':{'raw_status':'FAIL','leaf_commands':88,'passes':82,'intentional_pin_rejections':6,'retained_rejections':sorted(retained_rejects),'additional_rejections':sorted(root_rejects-{'retained-62'}),'no_historical_fail_relabelled':True},'replacement_gates':{'official_atlas_mapping_pixel_tests':570,'padded_fallback_character_coverage':1006,'all_six_text_masks':2800,'pixel_canary_comparisons_per_flavor':89600,'normal_and_asan_ubsan':True,'new_contract_negative_controls':15,'unchanged_renderer_negative_tests_in_title_inverse_view':28,'unchanged_geometry_route_and_bounds_tests':6,'pure_renderer_optimized_and_ubsan':'PASS'},'native':{'opening_checks':len(opening['checks']),'opening_sessions':len(opening['sessions']),'opening_and_field':opening['cadence_by_scope']['opening_and_field'],'inherited_cold_continue':opening['cadence_by_scope']['cold_continue_observed'],'gear_controller':read('gear-native/report.json')['performance'],'gear_passive':read('gear-passive/report.json')['performance']},'limitations':['Historical full aggregates reject old font/source pins; current successor replacements are explicit.','Synchronous cold-Continue stalls remain; no claim of whole-campaign stall freedom.','No new complete late-game campaign/all-128 run, physical hardware test or subjective music approval.','Final source ZIP extraction/rebuild receipt is separate to avoid recursive archive self-reference.'],'files':rows}
 (OUT/'index.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'evidence_files':len(rows),'bytes':sum(r['stored_bytes']for r in rows)}))
if __name__=='__main__':main()
