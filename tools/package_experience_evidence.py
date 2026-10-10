#!/usr/bin/env python3
"""Bundle compact exact polish evidence; never invent missing completed tests."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/experience-polish/evidence-p2'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 host=ROOT/'build/experience-host-p2/run-status.json';h=json.loads(host.read_text());assert h['result']=='PASS' and len(h['runs'])==49
 paths=[host,
 ROOT/'build/experience-native-p2/report.json',ROOT/'build/experience-native-p2/inputs.jsonl.gz',
 ROOT/'build/experience-pixels-p2-r2/report.json',
 ROOT/'build/experience-campaign-p2-r2/player-feedback-campaign.json',ROOT/'build/experience-campaign-p2-r2/evolution-power-cuts.json',ROOT/'build/experience-campaign-p2-r2/controller-inputs.json.gz',
 ROOT/'build/experience-save-p2/report.json',ROOT/'build/experience-memory-p2/memory-budget.json',
 ROOT/'build/experience-ui-regeneration.json',ROOT/'build/experience-bridge-build.log',ROOT/'build/experience-bridge-smoke.log',
 ROOT/'build/experience-shop-p2-provenance-native/shop-experience.json',
 ROOT/'build/experience-audit-navigation/navigation-verification.json',
 ROOT/'build/experience-audit-navigation/p2-native/fresh-village/exploration.json',
 ROOT/'build/experience-audit-navigation/p2-native/fresh-village/inputs.json',
 ROOT/'build/experience-audit-navigation/p2-native/earned-chapter/player-feedback-campaign.json',
 ROOT/'build/experience-audit-navigation/p2-town-matrix/report.json',
 ROOT/'build/experience-teaser-p2-r2/teaser-report.json',
 ROOT/'build/source-hashes.json',ROOT/'dist/experience-candidate.json',
 ROOT/'build/experience-campaign-p2.log',ROOT/'build/experience-pixels-p2.log',ROOT/'build/experience-teaser-p2.log']
 paths += [host.parent/r['log'] for r in h['runs']]
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for p in paths:
  assert p.is_file(),p
  b=p.read_bytes();rel=p.relative_to(ROOT);name='--'.join(rel.parts[1:])
  target=OUT/(name if name.endswith('.gz') else name+'.gz')
  target.write_bytes(b if name.endswith('.gz') else gzip.compress(b,mtime=0))
  rows.append({'source':str(rel),'file':target.name,'source_bytes':len(b),'source_sha256':sha(b),'packed_bytes':target.stat().st_size,'packed_sha256':sha(target.read_bytes()),'encoding':'original-gzip' if name.endswith('.gz') else 'gzip'})
 (OUT/'index.json').write_text(json.dumps({'scope':'Exact P2 compact acceptance reports and host logs. Original P1 cache defect and original audit evidence are separately preserved.','candidate_rom_sha256':sha((ROOT/'build/emberbond.gba').read_bytes()),'omissions':'Large raw native frame traces, compiled host dependencies, full machine states and repetitive per-frame SRAM cuts remain ignored development artifacts. This bundle does not claim complete historical output directories. Source helpers and tested generated R7 fixtures are included separately.','qualification':'Failed command setup/capture probes remain failures. Prepared full-render branches, boot and Continue are not steady gameplay timing evidence.','files':rows},indent=2)+'\n')
 print(json.dumps({'files':len(rows),'packed_bytes':sum(r['packed_bytes'] for r in rows)}))
if __name__=='__main__':main()
