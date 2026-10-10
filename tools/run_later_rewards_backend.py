#!/usr/bin/env python3
"""Finite backend regression set; controller journey and presentation are separate."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'build/later-rewards-regression');parser.add_argument('--full-cuts',action='store_true');a=parser.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 source={str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'src').glob('*'))if p.is_file()}
 names=['test_later_rewards','test_later_rewards_codec','test_save5','test_save5_history','test_save5_history_differential','test_economy','test_economy_history','test_equipment','test_weapon_actions','test_gear_runtime','test_player_feedback_gear_cache','test_gear_numbers','test_gear_hearts','test_regional_quest_events','test_underwater_transactions','test_magma_recruit_transactions','test_shop_experience','test_save_feedback','test_player_feedback_menu','test_return_history_differential','test_underwater_history_differential','test_covenants_history','test_horizons_history']
 report={'scope':__doc__,'source_sha256':source,'runs':[],'result':'RUNNING'}
 def write():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 write()
 for i,name in enumerate(names):
  cmd=[sys.executable,'tests/'+name+'.py']
  if name=='test_later_rewards'and a.full_cuts:cmd.append('--full-cuts')
  log=out/f'{i:02d}-{name}.log';t=time.monotonic()
  with log.open('w')as f:r=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
  unchanged=all(sha(ROOT/k)==v for k,v in source.items())
  row={'command':cmd,'exit_code':r.returncode,'seconds':round(time.monotonic()-t,3),'log':log.name,'log_sha256':sha(log),'source_unchanged':unchanged,'helper_sha256':sha(ROOT/'tests'/f'{name}.py')};report['runs'].append(row);write();print(name,'PASS'if r.returncode==0 and unchanged else'FAIL',flush=True)
  if not unchanged:break
 report['result']='PASS'if len(report['runs'])==len(names)and all(not x['exit_code']and x['source_unchanged']for x in report['runs'])else'FAIL';write();return report['result']!='PASS'
if __name__=='__main__':raise SystemExit(main())
