#!/usr/bin/env python3
"""Current journey/opening host gate, including all 62 retained regressions.

Host checks establish state, geometry, text and pixel contracts. Actual native
input, save migration, frame pacing and the earned journey are separate gates.
"""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 manifest=ROOT/'build/source-hashes.json';runtime=json.loads(manifest.read_text())
 def unchanged():return all((ROOT/k).is_file()and sha(ROOT/k)==v for k,v in runtime.items())
 assert unchanged(),'Current source must match the frozen build'
 commands=[('retained-62',[sys.executable,'tools/run_connected_roads_host.py','--journey-story-ui-successor','--output',str(out/'retained-62')],{})]
 names=['test_journey_goals','test_journey_arrival_latch','test_journey_map','test_companion_guide','test_shared_text_spans','test_play_notice_cache','test_retained_ui_story_successor','test_regional_quest_events','verify_late_renderer']
 commands += [(n,[sys.executable,'tests/'+n+'.py'],{}) for n in names]
 commands += [('retained-parent-negatives',[sys.executable,'tests/test_retained_ui_successor.py','--journey-story-ui-successor'],{}),('regional-quest-ubsan',[sys.executable,'tests/test_regional_quest_events.py'],{'QUEST_SANITIZE':'1'})]
 report={'scope':__doc__,'result':'RUNNING','runtime_manifest_sha256':sha(manifest),'candidate':{n:sha(ROOT/'build'/n)for n in ('emberbond.gba','emberbond.elf','emberbond.sym')},'runs':[]}
 def save():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 save()
 for i,(name,cmd,extra)in enumerate(commands):
  assert unchanged();helper=ROOT/cmd[1];before=sha(helper);log=out/(f'{i:02d}-'+name+'.log');t=time.monotonic()
  row={'name':name,'command':cmd,'environment':extra,'helper_sha256':before,'log':log.name,'status':'RUNNING'};report['runs'].append(row);save()
  with log.open('w')as f:r=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1',**extra})
  row.update(exit_code=r.returncode,seconds=round(time.monotonic()-t,3),log_sha256=sha(log),runtime_unchanged=unchanged(),helper_unchanged=sha(helper)==before)
  row['status']='PASS'if not r.returncode and row['runtime_unchanged']and row['helper_unchanged']else'FAIL';print(name,row['status'],flush=True);save()
  if not row['runtime_unchanged']:break
 report['result']='PASS'if len(report['runs'])==len(commands)and all(r['status']=='PASS'for r in report['runs'])else'FAIL';save();return report['result']!='PASS'
if __name__=='__main__':raise SystemExit(main())
