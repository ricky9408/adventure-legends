#!/usr/bin/env python3
"""Current connected-roads host/sanitizer/art regression aggregate.

Retains every current Player Feedback host check and adds changed route,
scenery, trial navigation and historical-return checks. Native timing is separate.
"""
import argparse,ast,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);flags=p.add_mutually_exclusive_group();flags.add_argument('--journey-ui-successor',action='store_true');flags.add_argument('--journey-story-ui-successor',action='store_true');flags.add_argument('--soundtrack-successor',action='store_true');a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 manifest=ROOT/'build/source-hashes.json';runtime=json.loads(manifest.read_text());base=ROOT/'tools/run_player_feedback_host.py'
 names=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(base.read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='names' for t in n.targets))
 extras=['test_connected_roads_geometry','test_connected_roads_engine','test_connected_road_art','test_trials','test_region_art','test_north_art','test_south_art','test_magma_art','test_underwater_art','test_return_geometry','test_horizons_geometry','test_underwater_return_spawns','test_connected_route_copy']
 names=list(dict.fromkeys(names+extras));assert len(names)==62
 def unchanged():return all(sha(ROOT/k)==v for k,v in runtime.items())
 assert unchanged()
 report={'scope':__doc__,'result':'RUNNING','baseline_aggregate_sha256':sha(base),'runtime_manifest_sha256':sha(manifest),'candidate':{n:sha(ROOT/'build'/n) for n in ('emberbond.gba','emberbond.elf','emberbond.sym')},'runs':[]}
 def save():(out/'run-status.json').write_text(json.dumps(report,indent=2)+'\n')
 save();fixture_dir=out/'checkpoint-fixtures';environment={**os.environ,'CONNECTED_ROAD_FIXTURES':str(fixture_dir),'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'}
 commands=[('fixture-preparation',[sys.executable,'tests/connected_roads_fixtures.py','--output',str(fixture_dir)])]+[(n,[sys.executable,'tests/'+n+'.py']) for n in names]
 if a.journey_ui_successor or a.journey_story_ui_successor:
  selected='--journey-story-ui-successor' if a.journey_story_ui_successor else '--journey-ui-successor'
  for name,cmd in commands:
   if name in ('test_return_geometry','test_connected_route_copy'):cmd.append(selected)
  report['explicit_retained_ui_successor']={'flag':selected,'scope':'Separately pinned verifier; original assertions and historical source remain unchanged.'}
 if a.soundtrack_successor:
  # Current geometry/authoring plus authenticated historical font/renderer
  # proofs. Do not route current pixels through obsolete G5 corpus pins.
  for name,cmd in commands:
   if name in ('test_return_geometry','test_connected_route_copy'):cmd[1]='tests/test_soundtrack_geometry.py'
  report['explicit_soundtrack_successor']={'scope':'Current geometry and authoring; old pixel tests run separately on authenticated historical-only corpus. All current gameplay checks remain actual current code.'}
 for index,(name,cmd) in enumerate(commands):
  assert unchanged(),'Runtime changed between checks';helper=ROOT/cmd[1];before=sha(helper);log=out/(f'{index:02d}-'+name+'.log');start=time.monotonic();row={'name':name,'command':cmd,'helper_sha256':before,'log':log.name,'status':'RUNNING','is_test':name!='fixture-preparation'};report['runs'].append(row);save()
  with log.open('w') as f:r=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env=environment)
  row.update(exit_code=r.returncode,seconds=round(time.monotonic()-start,3),log_sha256=sha(log),runtime_unchanged=unchanged(),helper_unchanged=sha(helper)==before);row['status']='PASS' if not r.returncode and row['runtime_unchanged'] and row['helper_unchanged'] else 'FAIL';print(name,row['status'],flush=True);save()
  if not row['runtime_unchanged'] or (name=='fixture-preparation' and r.returncode):report['result']='FAIL';save();return 1
 report['test_commands']=sum(r['is_test'] for r in report['runs']);report['result']='PASS' if all(r['status']=='PASS' for r in report['runs']) else 'FAIL';save();return int(report['result']!='PASS')
if __name__=='__main__':raise SystemExit(main())
