#!/usr/bin/env python3
"""Build a concise measured attribution from the immutable Return B profiles."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/return-stall-attribution-b';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cases=[('menu',374,376,'Companion journal, tab 2'),('menu',380,382,'Progression, tab 3'),('menu',386,388,'Equipment, tab 4'),('sail',4698,4700,'Base-wind post-save redraw, room 57'),('command13',49246,49248,'Command 13 first cast, trial 7')]
summary={'candidate':'Return B','ROM_sha256':'5eb5e511b978d198e089ff559f9e742b6b7a81973d38de801ef3c433f0687fc0','frame_limit_cycles':280896,'no_game_ram_writes':True,'no_production_edits':True,'cases':[]}
for tag,start,observed,label in cases:
 path=ROOT/f'build/return-stall-profile-b-{tag}-final/profile-report.json';d=json.loads(path.read_text());assert d['complete_emulator_state_equal'] and d['control_trace_equal'] and not d['original_cadence_mismatches'] and not d['overflow'] and not d['reentered']
 loop=next(r for r in d['update_to_render_loops'] if r['entry_frame']==start);trace=next(r for r in d['trace'] if r['hardware_frame']==observed);groups=defaultdict(list)
 for r in d['records']:
  if loop['begin']<=r['begin'] and r['end']<=loop['end']:groups[r['name']].append(r['cycles'])
 inclusive={name:{'calls':len(vals),'cycles':sum(vals),'max_cycles':max(vals)} for name,vals in groups.items()}
 exclusive=[]
 for r in sorted(loop['functions'],key=lambda r:r['cycles'],reverse=True):
  f=d['functions'][r['index']] if r['index']<len(d['functions']) else {'name':'unmapped','owner':''}
  exclusive.append(dict(name=f['name'],owner=f['owner'],cycles=r['cycles']))
 summary['cases'].append(dict(label=label,profile_report=str(path.relative_to(ROOT)),profile_report_sha256=sha(path),source_report=d['source_report'],source_report_sha256=d['source_report_sha256'],loop_entry_hardware_frame=start,loop_exit_hardware_frame=loop['exit_frame'],missed_presentation_hardware_frame=observed,input=next(v['keys'] for v in d['inputs'] if v['frame']==start),observed_frame=trace,inclusive=inclusive,exclusive=exclusive,loop_cycles=loop['cycles'],all_loop_cycles_attributed=loop['cycles']==sum(v['cycles'] for v in exclusive),main_cycle_measurement_overhead=trace['cycles']-loop['cycles'],profile_end_sha256=d['profile_end_sha256'],control_end_sha256=d['control_end_sha256']))
(OUT/'attribution.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'output':str(OUT/'attribution.json'),'sha256':sha(OUT/'attribution.json'),'cases':len(summary['cases'])},indent=2))
