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
 r.boot();r.timing_mode='collect-diagnostic' if a.baseline else 'strict';r.initialize_return();r.northern_arm()
 if not a.minimal:
  r.begin_return_trial(7);r.trial_cast(7,0);r.snapshot('command13-first-hit');r.check(r.trial().stage==1 and r.trial().casts==1,'command13 first genuine field hit advances only its first stage');r.target(368,112);r.goto(416,112,radius=4);r.step(4);r.settle();r.trial_cast(7,1);r.snapshot('command13-trial-complete')
 r.finished_scope='collision-only-minimal-northern' if a.minimal else 'collision-only-full-northern-and-command13';r.verify_closures();r.report()
except Exception as e:
 r.failures.append({'error':str(e),'traceback':traceback.format_exc(),'status':r.status()});r.snapshot('failure',settle=False);raise
finally:r.report();r.e.close()
print(json.dumps({'ROM':r.target_sha,'scope':r.finished_scope,'windows':[{k:w[k]for k in ('name','maximum_cycles','raw_exceptions')}for w in r.frame_windows if 'cast-' in w['name']],'failures':r.failures},indent=2))
