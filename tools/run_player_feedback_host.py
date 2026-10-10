#!/usr/bin/env python3
"""Current feedback host/sanitizer regressions; native controls/cadence are separate."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 manifest=ROOT/'build/source-hashes.json';runtime=json.loads(manifest.read_text())
 def unchanged():return all(sha(ROOT/k)==v for k,v in runtime.items())
 assert unchanged()
 names=['test_save4','test_save5','test_economy','test_economy_history','test_creatures','test_progression_events','test_equipment','test_weapon_actions','test_gear_runtime','test_player_feedback_gear_cache','test_gear_numbers','test_gear_hearts','test_quickparty_scan','test_player_feedback_menu','test_player_feedback_party_pixels','test_player_feedback_world','test_player_feedback_box','test_player_feedback_porch','test_northern_powers','test_southern_powers','test_southern_beam_table','test_magma_powers','test_underwater_powers','test_return_powers','test_horizons_powers','test_player_feedback_host_mapping','test_player_feedback_engine','test_shop_experience','test_save_feedback','test_covenants_catalog','test_covenants_history','test_covenants_transactions','test_covenants_powerloss','test_covenants_sanitizers','test_covenants_art','test_covenants_creature_art','test_covenants_camera','test_covenants_engine','test_covenants_field_dispatch','test_covenants_presentation','test_covenants_party_notice','test_covenants_world','test_covenants_powers','test_covenants_practice_geometry','check_covenants_geometry','check_covenants_world_arm','check_covenants_field_feasibility','test_story_rewards','test_story_reward_finish']
 report={'scope':__doc__,'result':'RUNNING','runtime_manifest_sha256':sha(manifest),'candidate':{n:sha(ROOT/'build'/n)for n in('emberbond.gba','emberbond.elf','emberbond.sym')},'runs':[]}
 def save():(out/'run-status.json').write_text(json.dumps(report,indent=2)+'\n')
 save()
 for i,name in enumerate(names):
  assert unchanged(),'Runtime changed between checks'
  cmd=[sys.executable,'tests/'+name+'.py'];log=out/(f'{i:02d}-'+name+'.log');helper=ROOT/cmd[1];before=sha(helper);start=time.monotonic();row={'command':cmd,'helper_sha256':before,'log':log.name,'status':'RUNNING'};report['runs'].append(row);save()
  with log.open('w')as f:r=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
  row.update(exit_code=r.returncode,seconds=round(time.monotonic()-start,3),log_sha256=sha(log),runtime_unchanged=unchanged(),helper_unchanged=before==sha(helper));row['status']='PASS'if not r.returncode and row['runtime_unchanged']and row['helper_unchanged']else'FAIL';print(log.name,row['status'],flush=True);save()
  if not row['runtime_unchanged']:report['result']='FAIL';save();return 1
 report['result']='PASS'if all(x['status']=='PASS'for x in report['runs'])else'FAIL';save();return report['result']!='PASS'
if __name__=='__main__':raise SystemExit(main())
