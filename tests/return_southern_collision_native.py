#!/usr/bin/env python3
"""Focused authenticated-SRAM native Return collision regression.
Both ROMs earn their own controller states; no cross-ROM state load or RAM edit.
The unchanged B menu failures remain reported because this patch owns only LOS.
"""
import argparse,json,hashlib,traceback
from pathlib import Path
from return_journey import ReturnJourney
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline',action='store_true');p.add_argument('--minimal',action='store_true');a=p.parse_args();src=a.source.resolve();rom=src/'build/emberbond.gba';manifest=src/'build/source-hashes.json';fixture=ROOT/'tests/fixtures/v5-revision6'/('underwater-minimal12-town.sav' if a.minimal else 'underwater-all89-town.sav')
r=ReturnJourney(rom,rom.with_suffix('.sym'),a.output,sha(rom),sha(rom.with_suffix('.sym')),sha(rom.with_suffix('.elf')),manifest,sha(manifest),fixture,src,'collect-diagnostic')
try:
 r.boot();r.timing_mode='collect-diagnostic' if a.baseline else 'strict';r.initialize_return();r.southern_arm()
 for index in (9,10):
  r.trial_wrong_side_retry(index);r.begin_return_trial(index);r.solve_return_trial(index);r.snapshot('southern-trial-'+str(index)+'-complete')
 r.finished_scope='collision-only-southern-commands23-and25';r.verify_closures();r.report()
except Exception as e:
 r.failures.append({'error':str(e),'traceback':traceback.format_exc(),'status':r.status()});r.snapshot('failure',settle=False);raise
finally:r.report();r.e.close()
print(json.dumps({'ROM':r.target_sha,'scope':r.finished_scope,'windows':[{k:w[k]for k in ('name','maximum_cycles','raw_exceptions')}for w in r.frame_windows if 'cast-' in w['name']],'failures':r.failures},indent=2))
