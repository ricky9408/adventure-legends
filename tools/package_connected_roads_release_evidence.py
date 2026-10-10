#!/usr/bin/env python3
"""Pack compact Connected Roads C4 reports, never relabel failed attempts."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/connected-roads/evidence-c4'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 host=ROOT/'build/connected-roads-host-c4/run-status.json';h=json.loads(host.read_text())
 assert h['result']=='PASS' and h['test_commands']==62 and len(h['runs'])==63
 boundary=ROOT/'build/connected-roads-native/acceptance-c4/report.json';b=json.loads(boundary.read_text());assert b['failures']==0 and len(b['cases'])==812
 for key in ('update_misses','flip_misses','cycle_overruns','publication_spills'):assert not b['native_cadence'][key]
 campaign=ROOT/'build/connected-roads-campaign-c4/player-feedback-campaign.json';c=json.loads(campaign.read_text());assert c['route_complete'] and c['native_cadence_passed'] and not c['failures']
 principal=ROOT/'build/connected-roads-principal-c4/report.json';n=json.loads(principal.read_text());assert not n['failures'] and n['performance']['strict_measured_pacing_pass']
 paths=[host,boundary,campaign,principal,
 ROOT/'build/connected-roads-c4/candidate.json',ROOT/'build/connected-roads-c4/source-hashes.json',
 ROOT/'build/connected-roads-c4-build.log',
 ROOT/'build/connected-roads-pixels-c4/report.json',
 ROOT/'build/connected-roads-save-c4/report.json',
 ROOT/'build/connected-roads-memory-c4/memory-budget.json',
 ROOT/'build/connected-roads-campaign-c4/evolution-power-cuts.json',
 ROOT/'build/connected-roads-campaign-c4/controller-inputs.json.gz',
 ROOT/'build/connected-roads-native/acceptance-c4/controller-inputs.json',
 ROOT/'build/connected-roads-native/acceptance-c4/fixture-provenance.json',
 ROOT/'build/connected-roads-guardian-c4/guardian-native.json',
 ROOT/'build/connected-roads-guardian-c4/guardian-fixture-provenance.json',
 ROOT/'build/connected-roads-guardian-c4/freeze-receipt.json',
 ROOT/'build/connected-roads-magma-return-c4/magma-return-native.json',
 ROOT/'build/connected-roads-magma-return-c4/freeze-receipt.json',
 ROOT/'build/connected-roads-teaser-c4/teaser-report.json']
 power=ROOT/'build/connected-roads-native/late-powers-c4/report.json';power_report=json.loads(power.read_text());assert power_report['failures']==0 and len(power_report['cases'])==47
 for key in ('update_misses','flip_misses','cycle_overruns','publication_spills'):assert not power_report['native_cadence'][key]
 paths += [power,ROOT/'build/connected-roads-notice-host-c4.log']
 paths += [host.parent/r['log'] for r in h['runs']]
 paths += sorted((ROOT/'build/connected-roads-memory-c4').glob('*-overflow.log'))
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for p in paths:
  assert p.is_file(),p
  raw=p.read_bytes();rel=p.relative_to(ROOT);name='--'.join(rel.parts[1:]);name=name if name.endswith('.gz') else name+'.gz'
  t=OUT/name;t.write_bytes(raw if p.suffix=='.gz' else gzip.compress(raw,mtime=0));rows.append({'original_path':str(rel),'file':name,'source_bytes':len(raw),'source_sha256':sha(raw),'compressed_bytes':t.stat().st_size,'compressed_sha256':sha(t.read_bytes()),'encoding':'original-gzip' if p.suffix=='.gz' else 'gzip'})
 (OUT/'index.json').write_text(json.dumps({'scope':'Exact C4 compact acceptance reports and logs. Independent geometry/cache/visual review and late-edge power evidence have their own indexes.','rom_sha256':c['candidate']['rom_sha256'],'runtime_gates_passed':True,'known_rendering_limit':'../NOTICE_CACHE_REVIEW.md','omissions':'Large raw frame traces, compiled host dependencies, full machine states and repetitive per-cut SRAM outputs remain local ignored development artifacts. Source scripts and authenticated fixture inputs are included. Historical binary-helper omissions retain their separate provenance.','files':rows},indent=2)+'\n')
 print(json.dumps({'files':len(rows),'compressed_bytes':sum(r['compressed_bytes'] for r in rows)}))
if __name__=='__main__':main()
