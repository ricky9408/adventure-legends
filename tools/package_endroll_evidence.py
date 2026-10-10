#!/usr/bin/env python3
"""Seal current ending-roll evidence; preserve font-only results as historical."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'build/endroll-qa';OUT=ROOT/'docs/endroll/evidence'
ROM='a94e9dee47f4de0a2f984d6a90b3d80e2c9a6a512157bf10ff2f1e65f088b684'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((QA/p).read_text())
def main():
 assert sha(ROOT/'build/emberbond.gba')==ROM
 runtime=json.loads((ROOT/'build/source-hashes.json').read_text());assert len(runtime)==1947 and all(sha(ROOT/k)==v for k,v in runtime.items())
 native=read('native/pass2/report.json');summary=read('native/pass2/acceptance-summary.json');assert native['complete']and not native['failures']and summary['result']=='PASS'and summary['checks']==100 and summary['rom_sha256']==ROM
 assert summary['measured_frames']==7660 and summary['ending_bad_frame_count']==0 and summary['primary_replay_and_first_completion_ram_writes']==0
 c=read('contract-renderer.json');assert c['result']=='PASS'and c['renderer_rerun']and len(c['negative_controls'])==16
 assert read('inherited-renderer.json')['status']=='PASS'
 memory=read('memory/memory-budget.json');assert all(memory['checks'].values())and all(r['exit_code']!=0 for r in memory['negative_link_probes'])
 gear={}
 for name in('gear-controller','gear-passive'):
  d=read(name+'/report.json');assert d['complete']and not d['failures']and d['exact_files_unchanged']and not d['performance']['pacing_exceptions'];gear[name]={'checks':d['checks'],'performance':d['performance']}
 host=(QA/'host.log').read_text();assert host.count('PASS 23349')==2 and host.count('PASS 202682')==2
 assert (QA/'font-spans.log').read_text().count('PASS 89600')==2
 assert (QA/'play-cache.log').read_text().count('PASS: 72270')==2
 assert 'PASS actual menu C:'in(QA/'menu.log').read_text()
 video=read('video/teaser-report.json');assert video['passed']and video['rom_sha256']==ROM and not video['story_card_in_recording']and not video['fresh_acquisition_claimed']and video['controller_only']and not video['game_ram_writes']and not video['machine_state_imports']and not video['nonflip_frames']
 paths=['native/pass2/report.json','native/pass2/acceptance-summary.json','native/pass2/native-frames.jsonl.gz','native/pass2/inputs.jsonl.gz','native/pass2/preparation-writes.jsonl.gz','contract-renderer.json','inherited-renderer.json','memory/memory-budget.json','gear-controller/report.json','gear-passive/report.json','host.log','font-source.log','font-spans.log','play-cache.log','menu.log','video/teaser-report.json','video/preview-review.json','video/capture-frames.jsonl.gz','memory/iwram-overflow.log','memory/ewram-overflow.log','memory/rom-overflow.log']
 paths.extend(str(p.relative_to(QA))for p in(QA/'native/pass2').glob('*.json')if str(p.relative_to(QA))not in paths)
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for rel in sorted(set(paths)):
  p=QA/rel
  assert p.exists(),rel
  raw=p.read_bytes();name=rel.replace('/','--')+(''if rel.endswith('.gz')else'.gz');dest=OUT/name;dest.write_bytes(raw if rel.endswith('.gz')else gzip.compress(raw,mtime=0))
  rows.append({'source':str(p.relative_to(ROOT)),'file':name,'source_sha256':hashlib.sha256(raw).hexdigest(),'stored_sha256':sha(dest),'source_bytes':len(raw),'stored_bytes':dest.stat().st_size})
 report={'status':'PASS_CURRENT_ENDROLL_SUCCESSOR','rom_sha256':ROM,'runtime_manifest_sha256':sha(ROOT/'build/source-hashes.json'),'contract_sha256':c['endroll_contract_sha256'],'native_summary':summary,'current_gear_regressions':gear,'host':{'endroll_state_updates_per_flavor':202682,'endroll_clipped_frames_per_flavor':23349,'existing_font_canary_comparisons_per_flavor':89600,'play_notice_comparisons_per_flavor':72270,'normal_and_sanitized':True,'menu_regressions':'PASS','memory_and_negative_link_checks':'PASS','contract_rejection_controls':16},'previous_full_host_scope':'The complete 88-command font-only host aggregate is preserved under docs/gbj-font/evidence for its own b125a90 ROM. It was not rerun wholesale for this ending-only successor; unchanged runtime sources are byte-authenticated and current ending/menu/cache/gear/font/save/renderer checks are listed here. Historical pin failures are not relabeled.','omissions':'Selected spoiler-safe PNGs are under docs/endroll/screenshots. Full native image sets, ROM/ELF, compiled bridges and WAV masters remain development outputs; recipes and exact hashes are provided.', 'limits':['Authentic historical saves seed native ending tests; no fresh full-game acquisition claimed.','Cold-load/migration pacing, physical hardware and subjective audio quality remain qualified.','The single deliberate inactive-SRAM fault is a separate diagnostic, not normal-controller gameplay.','Final exact source ZIP rebuild/repackage receipt is separate to avoid archive self-reference.'],'files':rows}
 (OUT/'index.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'files':len(rows),'bytes':sum(r['stored_bytes']for r in rows)}))
if __name__=='__main__':main()
