#!/usr/bin/env python3
"""Package bounded exact-ROM evidence after make test test-tools and gameplay-video.

Raw emulator states, SRAM, traces and videos remain in ignored build/. This tool
writes small reviewable JSON chunks and native spoiler-free preview images.
"""
from pathlib import Path
import argparse, hashlib, json, re, shutil
ROOT=Path(__file__).resolve().parents[1]
REPORTS={
 'first-chapter':'qa/playthrough.json','review':'review/review-tests.json',
 'exploration':'exploration/exploration-tests.json','campaign-minimal':'campaign-qa/campaign-report.json',
 'campaign-optional':'campaign-optional/campaign-report.json','fullscreen':'fullscreen-qa/fullscreen-report.json',
 'evolution-eight':'evolution-qa/evolution-report.json','evolution-six':'evolution-six-hearts/evolution-report.json',
 'evolution-migrated':'evolution-migrated/evolution-report.json','advanced-powers':'advanced-power-qa/advanced-power-report.json',
 'quickparty':'quickparty-qa/quickparty-report.json','quickparty-evolved':'quickparty-evolved-qa/quickparty-report.json',
 'expeditions':'expedition-qa/expedition-report.json','pr5-migration':'pr5-quickparty-migration-qa/quickparty-migration-report.json','regional-journey':'region-journey/region-journey.json',
 'regional-combat':'region-combat/region-combat.json'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--qa-root',type=Path,default=ROOT);p.add_argument('--capture',type=Path,default=ROOT/'build/region-teaser');a=p.parse_args()
 out=ROOT/'docs/reedhaven';out.mkdir(exist_ok=True);build=a.qa_root/'build';rom=sha(build/'emberbond.gba')
 def write(name,obj):
  data=json.dumps(obj,ensure_ascii=False,indent=2)+'\n';assert len(data.encode())<32000,(name,len(data));(out/name).write_text(data)
 def chunks(name,rows):
  batch=[];idx=0
  for row in rows:
   if len(json.dumps(batch+[row],ensure_ascii=False).encode())>20000:
    write(f'{name}-{idx:02}.json',batch);batch=[];idx+=1
   batch.append(row)
  if batch:write(f'{name}-{idx:02}.json',batch)
 def load(rel):
  f=build/rel;r=json.loads(f.read_text());assert r.get('rom_sha256',r.get('candidate',{}).get('rom_sha256'))==rom,(rel,'ROM mismatch');assert not r.get('failures'),(rel,'failed');return r
 def compact(rows):
  return [{k:v for k,v in x.items() if k not in ('trace','initial','final','samples','input_trace') and not isinstance(v,(dict,list))} for x in rows]
 for old in out.glob('*.json'):old.unlink()
 summary={'schema':1,'rom_sha256':rom,'symbols_sha256':sha(build/'emberbond.sym'),'rom_bytes':(build/'emberbond.gba').stat().st_size,'save5_content_revision':2,'normal_game_ram_writes':0,'native_assertions':0,'suites':{},'timing':{},'content':{'enabled_forms':11,'controller_obtained_and_reloaded_forms':11,'live_families':6,'evolution_edges':5,'player_weapon_classes':3,'equipment_slots':5,'earnable_items':13,'regional_quests':11,'total_areas':22,'regional_areas':6,'legendary_forms_obtainable':0,'target_forms':128}}
 for name,path in REPORTS.items():
  r=load(path);rows=r.get('passes',r.get('checks',[]));assert all(x.get('passed',True) for x in rows if isinstance(x,dict))
  summary['suites'][name]={'report':'build/'+path,'report_sha256':sha(build/path),'passes':len(rows),'failures':0};summary['native_assertions']+=len(rows);chunks('assertions-'+name,rows)
  timing=r.get('performance',r.get('timing',r.get('scenes',[])))
  if timing:
   rows=compact(timing);chunks('cadence-'+name,rows);summary['timing'][name]={'windows':len(rows),'maximum_cycles':max(x.get('maximum_cycles',x.get('peak_cycles',x.get('cycles_max',0))) for x in rows)}
  if r.get('save_pending_checks'):
   writes=compact(r['save_pending_checks']);chunks('incremental-save-'+name,writes);summary['timing'][name+'-saves']={'windows':len(writes),'maximum_cycles':max(x.get('max_cycles',0) for x in writes)}
  if 'timings' in r:write('cadence-regional-journey.json',r['timings']);summary['timing'][name]=r['timings']
  if 'frame_windows' in r:
   windows=compact(r['frame_windows']);write('cadence-regional-combat.json',windows);summary['timing'][name]=windows
   chunks('combat-cases',compact(r['cases']));write('combat-coverage.json',r['coverage'])
   collection=r['snapshots']['collection-all-eleven-saved'];assert collection['sram_sha256']=='74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106' and collection['quests']==[3]*11
   summary['collection']={'forms':[1,2,4,5,7,8,10,11,13,14,16],'live_forms':[2,5,8,11,14,16],'instance_count':6,'sram_sha256':'74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106','scope':'Single controller-earned file, all eleven regional quests retained, saved and rebooted'}
 for name in ('minimal','optional'):
  path=f'campaign-performance-{name}/campaign-performance.json';r=load(path);assert r['full_strict_60hz_pass'];summary['timing']['campaign-'+name]={'strict_pass':True,'report_sha256':sha(build/path),'coverage':r['coverage']};chunks('cadence-campaign-'+name,compact(r['scenes']+r['transitions']))
 r=load('quickparty-synthetic-qa/quickparty-report.json');summary['synthetic_faults']={'faults':r['synthetic_faults'],'game_ram_writes':r['synthetic_game_ram_writes'],'separate_from_native_assertions':True}
 capture=json.loads((a.capture/'capture.json').read_text());assert capture['rom_sha256']==rom and not capture['failures'];
 for name in ('reedhaven-native-teaser.mp4','native-town.png','native-gear.png'):
  assert sha(a.capture/name)==capture['files'][name]['sha256']
  if name.endswith('.png'):shutil.copyfile(a.capture/name,out/name)
 cap={k:v for k,v in capture.items() if k in ('rom_sha256','symbols_sha256','controller_only','game_ram_writes','captured_savestate_restores','captured_sram_reloads','scope','captured_frames','frame_rate','hardware_clock_ratio','duration_seconds','state_frame_counts','native_resolution','video_resolution','scaling','audio','native_audio','files','failures')};write('player-teaser.json',cap);summary['player_teaser']={'seconds':capture['duration_seconds'],'frames':capture['captured_frames'],'video_sha256':capture['files']['reedhaven-native-teaser.mp4']['sha256']}
 mapping=(build/'emberbond.map').read_text();sizes={n:int(re.search(r'^\.'+n+r'\s+0x[0-9a-f]+\s+(0x[0-9a-f]+)',mapping,re.M).group(1),16) for n in ('iwram','data','bss')};assert sizes['iwram']<=28*1024 and sizes['data']+sizes['bss']<256*1024;summary['memory_bytes']=sizes
 summary['limits']=['mGBA 0.10.5 only; physical GBA/flash cartridges are not verified','Cold Continue checkpoint decoding is a separate blocking load transition','Native timing windows are representative, not exhaustive maximal crowd proof','The regional two-arrow window has five live enemies but at most two visible and no hostile projectiles','Host/synthetic save corruption and sanitizer checks are separate from controller-only gameplay','Eleven forms are obtainable; the 128-form roster and four additional regional cultures remain unfinished']
 write('summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
