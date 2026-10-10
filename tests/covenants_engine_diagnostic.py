#!/usr/bin/env python3
"""Whole-ROM synthetic engine scenes. NOT controller obtainability or release acceptance.

A genuine C import is advanced by host typed transactions into clearly synthetic
fixtures. The native engine then cold-loads each fixture and receives buttons.
No machine states or game-RAM writes; the invented completion is never counted
as a controller-earned collection. Every measured hardware frame retains the
one-update/page-flip/cycles/OAM/audio gates. Loader frames are recorded separately.
"""
from pathlib import Path
import argparse,ctypes as C,gzip,hashlib,json,shutil,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
from run_covenants_native import frozen_copy
import covenants_host_support as host
MUSIC=('music_faults','music_recoveries','music_stopped','music_irq_count','music_irq_late_max','music_track')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--candidate',type=Path,default=ROOT/'build');parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);candidate=out/'candidate';candidate.mkdir()
 for name in ('emberbond.gba','emberbond.elf','emberbond.sym','source-hashes.json'):frozen_copy(a.candidate/name,candidate/name)
 pins={p.name:sha(p)for p in candidate.iterdir()};manifest=json.loads((candidate/'source-hashes.json').read_text())
 assert all(sha(ROOT/f)==h for f,h in manifest.items()),'Build/source closure differs before diagnostic'
 runtime=out/'runtime-source'
 for name,digest in manifest.items():
  source=ROOT/name;destination=runtime/name;destination.parent.mkdir(parents=True,exist_ok=True);frozen_copy(source,destination);assert sha(destination)==digest,('Source changed while freezing diagnostic',name)
 helpers=out/'helpers';helper_hashes={}
 for module in list(sys.modules.values()):
  name=getattr(module,'__file__',None)
  if name and Path(name).is_file() and Path(name).resolve().is_relative_to(ROOT):
   source=Path(name).resolve();relative=source.relative_to(ROOT);destination=helpers/relative;destination.parent.mkdir(parents=True,exist_ok=True);frozen_copy(source,destination);helper_hashes[str(relative)]=sha(destination)
 for source in (Path(__file__).resolve(),ROOT/'tools/mgba_bridge.c',ROOT/'tools/mgba_bridge.so',host.FIXTURE):
  relative=source.relative_to(ROOT);destination=helpers/relative;destination.parent.mkdir(parents=True,exist_ok=True);frozen_copy(source,destination);helper_hashes[str(relative)]=sha(destination)
 (helpers/'hashes.json').write_text(json.dumps(helper_hashes,indent=2)+'\n')
 host.ROOT=runtime;host.FIXTURE=helpers/host.FIXTURE.relative_to(ROOT)
 sym={parts[2]:int(parts[0],16)for line in(candidate/'emberbond.sym').read_text().splitlines()if len(parts:=line.split())==3}
 report={'scope':__doc__,'synthetic_fixture':True,'controller_earned_128':False,'release_acceptance':False,'game_ram_writes':0,'machine_state_loads':0,'candidate':pins,'frozen_runtime_source':str(runtime),'helper_manifest_sha256':sha(helpers/'hashes.json'),'fixture_host_source':host.runtime_hashes(),'import_sha256':host.FIXTURE_SHA,'cases':[],'exceptions':[],'hardware_frames':0,'measured_frames':0,'maximum_cycles':0,'maximum_oam':0,'finished':False}
 def save_report():(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 save_report();stream=gzip.open(out/'hardware-frames.jsonl.gz','wt',encoding='utf8')
 try:
  with tempfile.TemporaryDirectory(prefix='covenants-native-seed-')as temp:
   lib=host.build(temp);master=host.story(lib,recruit=True)
   assert sum(bool(c.flags&1)for c in master.roster.instances)==72
   commands=[12,122,123,124,125,126,127,128]
   for area,form,command in zip(range(70,78),range(121,129),commands):
    s=host.Save.from_buffer_copy(bytes(master));slot=next(i for i,c in enumerate(s.roster.instances)if c.form_id==form)
    c=s.roster.instances[slot]
    if command in list(c.equipped):c.selected_command=list(c.equipped).index(command)
    else:c.equipped[0]=command;c.selected_command=0
    s.roster.party[:]=[slot,0,1,2];s.roster.selected_party=0;s.campaign.room=area;s.campaign.spawn=0;s.campaign.spirit=0
    assert lib.save5_validate(C.byref(s))==1,('invalid synthetic fixture',area,form)
    lib.save5_test_reset_writer();lib.save5_test_fail_after(-1);assert lib.save5_store(C.byref(s))==1
    fixture=out/f'synthetic-room{area}-form{form}.sav';fixture.write_bytes(bytes(lib.sram))
    case={'room':area,'form':form,'command':command,'fixture_sha256':sha(fixture),'checks':[],'maximum_cycles':0,'maximum_oam':0,'screenshots':[],'native_tile_checks':0,'walk_frames':[],'cast_poses':[]};report['cases'].append(case)
    with Emulator(candidate/'emberbond.gba')as e:
     e.load_save(fixture);e.reset()
     get=lambda n:e.read(sym[n])
     last_tile_code=[None]
     def tiles():
      code=get('gfx_companion_frame')
      if get('game_state')!=1 or not get('summoned') or get('spirit')!=form-69 or code==last_tile_code[0]:return
      last_tile_code[0]=code;low=code&0x0fffffff;direction=(low//4)&3;gait=low&3
      if code>=268435456:
       pose=(code-268435456)//536870912;assert pose<3
       address=sym['covenants_creature_art_cast']+(((form-121)*4+direction)*3+pose)*256
       if pose not in case['cast_poses']:case['cast_poses'].append(pose)
      else:
       address=sym['covenants_creature_art_walk']+(((form-121)*4+direction)*4+gait)*256
       if gait not in case['walk_frames']:case['walk_frames'].append(gait)
      source=e.bytes(address,256);expected=bytearray(256)
      for y in range(16):
       for x in range(16):expected[((y//8)*2+x//8)*64+(y%8)*8+x%8]=source[y*16+x]
      actual=e.bytes(0x06014000+6400,256)
      assert actual==expected,(form,'native OBJ bytes differ',code,direction,gait)
      case['native_tile_checks']+=1
     def step(n,keys=0,measured=True):
      for _ in range(n):
       before=get('frame');display=e.read(0x04000000,2);oldstate=get('game_state');e.frames(1,keys)
       row={'room_case':area,'hardware_frame':e.frame,'measured':measured,'keys':keys,'before_state':oldstate,'after_state':get('game_state'),'update_delta':(get('frame')-before)&0xffffffff,'page_flip':bool((display^e.read(0x04000000,2))&16),'cycles':get('render_cycles'),'oam':get('obj_count'),'power_age':get('covenants_power_age'),'power_time':get('covenants_power_time'),'music':{n:get(n)for n in MUSIC}}
       report['hardware_frames']+=1
       if measured:
        report['measured_frames']+=1;case['maximum_cycles']=max(case['maximum_cycles'],row['cycles']);case['maximum_oam']=max(case['maximum_oam'],row['oam']);report['maximum_cycles']=max(report['maximum_cycles'],row['cycles']);report['maximum_oam']=max(report['maximum_oam'],row['oam']);tiles()
        if row['update_delta']!=1 or not row['page_flip'] or row['cycles']>=280896 or row['oam']>128 or any(row['music'][n]for n in MUSIC[:3]):report['exceptions'].append(row)
       stream.write(json.dumps(row,separators=(',',':'))+'\n')
     def check(ok,label):
      case['checks'].append({'label':label,'passed':bool(ok),'hardware_frame':e.frame});assert ok,(area,form,label)
     def tap(k):step(1,k);step(1,0)
     def shot(label):
      p=out/f'room{area}-form{form}-{label}.png';e.screenshot(p);case['screenshots'].append(p.name)
     step(160,measured=False);check(get('game_state')==0 and get('has_save')==1,'valid synthetic save reaches title')
     step(1,8,False);step(1,0,False)
     for _ in range(320):
      if get('game_state')==1 and get('room')==area and not get('save_begin_pending') and not get('save_completion_pending') and not get('save_requested'):break
      step(1,0,False)
     else:raise AssertionError(('cold load failed',area,get('game_state')))
     step(4,0,False);check(get('game_state')==1 and get('room')==area,'cold Continue enters authored room')
     step(32);shot('idle')
     if not get('summoned'):tap(2)
     tap(256);check(get('covenants_power_kind')==command and get('covenants_power_time')>0,'R starts real engine signature with shared cooldown')
     age=get('covenants_power_age');time=get('covenants_power_time');cd=get('ability_cd')
     step(16,512);step(1,0);check((get('covenants_power_age'),get('covenants_power_time'),get('ability_cd'))==(age,time,cd),'hold-L viewing freezes power and cooldown')
     tap(8);check(get('game_state')==3,'Start opens journal')
     step(12);check((get('covenants_power_age'),get('covenants_power_time'),get('ability_cd'))==(age,time,cd),'journal viewing preserves cast')
     for tab in range(1,13):
      tap(1);check(get('journal_tab')==tab,'bounded journal tab '+str(tab))
      if tab in (2,3,12):shot('journal'+str(tab))
     step(12);check((get('covenants_power_age'),get('covenants_power_time'),get('ability_cd'))==(age,time,cd),'all journal pages preserve attempted action')
     tap(8);check(get('game_state')==1,'journal closes to play')
     step(8);shot('cast')
     tap(2);check(not get('summoned') and get('covenants_power_time')==0 and get('ability_cd')>0,'B dismiss revokes power without refund')
     step(260);tap(2);tap(256);check(get('covenants_power_time')>0,'power can cast again after shared cooldown')
     step(get('covenants_power_time')+4);check(get('covenants_power_time')==0,'native cast reaches authored settle and expiry')
     step(48)
     check(set(case['walk_frames'])=={0,1,2,3} and set(case['cast_poses'])=={0,1,2},'native OBJ readback covers all gait frames and cast poses')
     step(get('ability_cd')+2);tap(256);check(get('covenants_power_time')>0,'third cast begins for actual selection test')
     step(16,512);step(1,512|16);step(1,0)
     check(get('covenants_power_time')==0 and get('ability_cd')>0,'actual hold-L selection revokes without refund')
     step(30);check(not any(get(n)for n in MUSIC[:3]),'existing music has no fault recovery or stop')
    save_report()
  report['finished']=True;report['all_checks_passed']=all(c['passed']for row in report['cases']for c in row['checks']);report['cadence_passed']=not report['exceptions'];report['candidate_still_exact']=all(sha(candidate/n)==h for n,h in pins.items());report['runtime_still_exact']=all(sha(runtime/n)==h for n,h in manifest.items());report['helpers_still_exact']=all(sha(helpers/n)==h for n,h in helper_hashes.items());save_report()
 finally:stream.close();save_report()
 print(json.dumps({k:report[k]for k in ('finished','all_checks_passed','cadence_passed','hardware_frames','measured_frames','maximum_cycles','maximum_oam')},indent=2))
 return 0 if report['all_checks_passed'] and report['cadence_passed']else 1
if __name__=='__main__':raise SystemExit(main())
