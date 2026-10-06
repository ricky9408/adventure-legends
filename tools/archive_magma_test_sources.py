#!/usr/bin/env python3
"""Archive exact current Magma producer scripts before a dependent native suite.

Fails closed if a report-pinned script has changed. This is provenance packaging,
not a new execution result and never changes the producer report or SRAM.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ADDITIONAL=('tests/test_save5.py','tests/test_creatures.py','tests/test_save4.py','tests/region_combat_tests.py','tests/southern_symbols.py','tests/test_southern_frozen_fixtures.py')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def archive(report):
 report=Path(report).resolve();r=json.loads(report.read_text())
 assert r['controller_only'] is True and r['game_ram_writes']==0 and not r['failures']
 assert r['checks'] and all(c['passed'] is True for c in r['checks'])
 expected=r['test_sources'];extra={p:digest(ROOT/p) for p in ADDITIONAL}
 assert not set(expected)&set(extra)
 all_sources={**expected,**extra};names=[Path(p).name for p in all_sources]
 assert len(names)==len(set(names)), 'Flat historical capture names must be unambiguous'
 for name,sha in all_sources.items():
  source=ROOT/name;assert source.resolve().is_relative_to(ROOT) and digest(source)==sha,('Producer source changed',name)
  target=report.parent/'test-source'/source.name;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert digest(target)==sha,('Refusing to overwrite different archived source',name)
  else:target.write_bytes(source.read_bytes())
 receipt={'recorded_hashes_verified':expected,'additional_imported_observer_sources':extra,'capture_scope':'Exact files verified against successful producer receipt; no source rewrite'}
 target=report.parent/'test-source-capture.json';data=(json.dumps(receipt,indent=2)+'\n').encode()
 if target.exists():assert target.read_bytes()==data,'Existing source-capture receipt differs'
 else:target.write_bytes(data)
 return dict(receipt=str(target),sha256=digest(target),producer_report_sha256=digest(report),files=len(all_sources))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);a=p.parse_args();print(json.dumps(archive(a.report),indent=2))
