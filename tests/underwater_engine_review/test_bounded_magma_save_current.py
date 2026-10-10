#!/usr/bin/env python3
"""Current linked-engine bounded Magma SAVE scheduler checks.
Synthetic host state/input edges and inert hardware backing only. No native
controller, timing or pixel claim. Setup definitions are copied from the
historical current-engine probe; its assertions and result remain separate.
"""
import ctypes as C
import hashlib
import json
import re
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE_ROOT=Path(os.environ.get('UNDERWATER_REVIEW_SOURCE',str(ROOT)))
MANIFEST_PATH=os.environ.get('UNDERWATER_REVIEW_MANIFEST')
EXPECTED=json.loads(Path(MANIFEST_PATH).read_text()) if MANIFEST_PATH else {str(p.relative_to(SOURCE_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE_ROOT/'src').rglob('*') if p.is_file()}
assert all(hashlib.sha256((SOURCE_ROOT/p).read_bytes()).hexdigest()==h for p,h in EXPECTED.items())
sys.path.insert(0,str(ROOT/'tests'))
from test_save5 import Save
OUT=Path(__file__).resolve().parent
MODULES=['game','assets','ui','world','campaign_art','campaign_rules','save4',
 'creatures','creature_data','save5','progression','evolution_art','advanced_powers',
 'trials','trial_art','quickparty','equipment','equipment_data','combat_rules',
 'weapon_actions','gear_runtime','gear_menu','regional_quests','regional_creature_art',
 'regional_powers','region_art','region_game','northern_creature_art','northern_powers',
 'northern_power_art','southern_powers','southern_power_art','southern_creature_art',
 'south_art','south_game','southern_quests','progression_events','north_art','north_game',
 'northern_quests','magma_game','magma_art','magma_quests','magma_creature_art',
 'magma_powers','magma_power_art','underwater_game','underwater_quests',
 'underwater_art','underwater_powers','underwater_power_art','underwater_creature_art']
# Full current-engine probes link actual Return dependencies; old snapshots
# that predate Return retain their original module closure.
if (SOURCE_ROOT/'src/return_game.c').is_file():
 MODULES += ['return_game','return_art','return_quests','return_creature_art','return_powers','return_power_art','return_legacy_powers']
RESULT={'scope':'Synthetic host state and input-edge integration; real production functions with entry instrumentation',
 'native_controller_gameplay':False,'native_hardware_timing':False,'emulator_ram_injection':False,
 'dma_emulated':False,'bitmap_metric':'full static paint or exact matching other-page DMA3 request observed before actor draw','compiler':os.environ.get('HOST_CC','cc'),'checks':[],'source_sha256':{}}
for name in MODULES:
 RESULT['source_sha256']['src/'+name+'.c']=hashlib.sha256((SOURCE_ROOT/'src'/f'{name}.c').read_bytes()).hexdigest()
TMP=tempfile.TemporaryDirectory(prefix='deferred-anchor-review-')
SO=Path(TMP.name)/'probe.so'
subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+[
 '-shared','-fPIC','-O0','-g','-std=c99','-fno-builtin','-fno-inline',
 '-finstrument-functions','-Wno-attributes','-Wno-pointer-to-int-cast',
 '-Wno-int-to-pointer-cast','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST',
 '-DGAME_HOST_TEST','-Dmain=gba_main','-I'+str(SOURCE_ROOT/'src'),'-Wl,-Bsymbolic',
 str(OUT/'engine_probe_bounded_magma.c'),*[str(SOURCE_ROOT/'src'/f'{n}.c') for n in MODULES],
 '-o',str(SO)],cwd=ROOT,check=True)
L=C.CDLL(str(SO))
if L.probe_map()!=1:
 address=C.c_size_t.in_dll(L,'probe_map_error_address').value
 error=C.c_int.in_dll(L,'probe_map_error_number').value
 overlaps=[]
 # Only overlapping address ranges and their generic tag are reported; no
 # unrelated process map paths or environment data enter the test evidence.
 try:
  for line in Path('/proc/self/maps').read_text().splitlines():
   columns=line.split();left,right=(int(v,16) for v in columns[0].split('-'))
   if left<address+0x20000 and right>address:
    overlaps.append({'start':left,'end':right,'tag':'[heap]' if columns[-1]=='[heap]' else 'other'})
 except OSError:pass
 detail={'kind':'synthetic-address-reservation','errno':error,'address':address,
         'length':0x20000,'mapped_before_failure':C.c_uint.in_dll(L,'probe_map_success_count').value,
         'overlaps':overlaps,'game_assertions_started':False,'overwritten_mappings':False}
 print('DEFERRED_PROBE_SETUP_FAILURE_JSON='+json.dumps(detail,sort_keys=True),file=sys.stderr)
 raise SystemExit(78)
RESULT['synthetic_mapping']={'map_fixed_noreplace':True,'ranges':4,'bytes_per_range':0x20000,
                             'overwritten_mappings':False}

for name in ('save5_load','save5_store','save5_validate'):
 getattr(L,name).argtypes=[C.POINTER(Save)];getattr(L,name).restype=C.c_int
L.save5_test_fail_after.argtypes=[C.c_int]
S=Save.in_dll(L,'adventure_save');SRAM=(C.c_ubyte*32768).in_dll(L,'save5_test_sram')
OLD=(C.c_ubyte*256).in_dll(L,'save4_test_sram');OLD[:]=b'\xff'*256
CACHE_FIELD_COUNT=int(re.search(r'#define\s+CACHE_FIELDS\s+(\d+)',(SOURCE_ROOT/'src/game.c').read_text())[1])
assert CACHE_FIELD_COUNT in (32,34),'Retained indices require an explicit adapter for any other layout'
CACHE=(C.c_uint*(2*CACHE_FIELD_COUNT)).in_dll(L,'cache_fields')
RESULT['cache_fields_per_page']=CACHE_FIELD_COUNT
VALID=(C.c_int*2).in_dll(L,'cache_valid')
class Enemy(C.Structure):_fields_=[(n,C.c_int)for n in ('x','y','hp','flash','kind')]
class Shot(C.Structure):_fields_=[(n,C.c_int)for n in ('x','y','dx','dy','life','owner')]
E=(Enemy*6).in_dll(L,'enemies');SH=(Shot*12).in_dll(L,'shots')
def get(n):return C.c_int.in_dll(L,n).value
def put(n,v):C.c_int.in_dll(L,n).value=v
def count(n):return get('probe_'+n)+(get('probe_copy') if n=='render' else 0)
def loaded():
 s=Save();assert L.save5_load(C.byref(s))==1;return s
def update(buttons=0):
 put('keys',buttons);put('pressed',buttons);put('music_tick',-1000);L.update();put('pressed',0)
def render():
 L.render();put('page',get('page')^1)
def drain():
 for _ in range(250):
  if get('game_state')!=6:return
  update(1023)
 raise AssertionError('writer failed to terminate')
def setup(area=39,lit=False,fixture='tests/fixtures/v5-revision4/southern-minimal8-town.sav'):
 L.save5_test_reset_writer();L.magma_game_reset();L.quickparty_reset(0)
 SRAM[:]=(ROOT/fixture).read_bytes();L.save5_test_fail_after(-1)
 assert L.save5_load(C.byref(S))==1
 # Explicit synthetic host setup: authored Southern bytes are decoded, then
 # enter/visit bits and current area are constructed for this isolated check.
 S.quests.region_flags[3]|=3;S.quests.anchors[3]=(S.quests.anchors[3]&~3)|(1<<(area-38)if lit else 0)
 S.campaign.room=area;S.campaign.spawn=0
 for n,v in {'room':area,'checkpoint_spawn':0,'chapter_flags':S.campaign.chapter_flags,
  'bridge_open':S.campaign.bridge,'torches':S.campaign.torches,'relic_found':S.campaign.relic,
  'camp_unlocked':S.campaign.camp,'room_flags':S.campaign.room_flags,
  'optional_flags':S.campaign.optional_flags,'story_seen':S.campaign.story_seen,
  'game_state':1,'has_save':1,'save_requested':0,'save_begin_pending':0,'save_failed':0,
  'save_failure_notice':0,'face':1,'keys':0,'pressed':0,'page':0,'summoned':0,
  'max_hp':6,'invuln':0,'guard_invuln':0,'stone_guard':0,'roll_ticks':0,
  'roll_cd':0,'ability_cd':0,'heal_cd':0,'hitstop':0,'transition_lock':0,
  'area_ticks':0,'transition':0,'power_effect':0,'toast_ticks':0,'walk':0,
  'quickparty_open':0,'journal_tab':0}.items():put(n,v)
 L.progression_refresh();L.game_health_refresh(1);L.game_attacks_reset()
 L.advanced_reset();L.regional_powers_reset();L.northern_powers_reset()
 L.southern_powers_reset();L.magma_powers_reset();L.magma_game_reset()
 for i in range(6):E[i]=Enemy()
 for i in range(12):SH[i]=Shot()
 x,y=(112,264)if area==38 else(80,280)
 L.game_region_warp(x,y);put('keys',0);L.game_attacks_reset();put('hero_hp_q4',16);put('hp',1)
 assert L.save5_validate(C.byref(S))==1
 assert L.save5_store(C.byref(S))==1
 L.save5_test_reset_writer();L.save5_test_fail_after(-1);L.probe_reset()
 VALID[:]=[0,0]
 return bytes(SRAM)
def record(name,**data):RESULT['checks'].append({'name':name,'passed':True,**data})


# Keep the archived single-update prepare assertions in their original file.
# This test proves the new explicit BUSY -> READY yield -> DONE schedule.
import traceback,faulthandler
faulthandler.enable()
EXPECTED=EXPECTED or {str(p.relative_to(SOURCE_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE_ROOT/'src').rglob('*') if p.is_file()}
RESULT.update(scope=__doc__,contract='stage3 warms; stage2 remains until exact DONE; stage1 begins writer on a separate update',failures=[])
RESULT['source_sha256']=EXPECTED
RESULT['observer_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),OUT/'engine_probe_bounded_magma.c')}
BUSY,DONE,FAILED=1,2,3
BASE='tests/fixtures/v5-revision4/southern-minimal8-town.sav'
FULL='tests/fixtures/v5-revision7/return-all104-town.sav'
assert hashlib.sha256((ROOT/FULL).read_bytes()).hexdigest()=='d482466d04050c3d7f2e8eb8e1960729c9b9b33aa3e32440d186a4b54b854a69'
POWER_FIELDS=('advanced_time_left','northern_power_time','southern_power_time','magma_power_time','underwater_power_time','return_power_time','ability_cd','roll_cd','heal_cd')
original_setup=setup

def setup(area=39,lit=False,fixture=BASE):
 bank=original_setup(area,lit,fixture)
 L.underwater_powers_reset();L.return_powers_reset()
 return bank

def begin(area=39,lit=False,fixture=BASE,hostiles=False):
 bank=setup(area,lit,fixture);old=bytes(loaded());L.probe_reset()
 if hostiles:
  E[0]=Enemy(get('px'),get('py'),5,0,0);SH[0]=Shot(get('px'),get('py'),1,0,8,1)
 enemies,shots=bytes(E),bytes(SH)
 update(1|256)
 assert get('game_state')==6 and get('save_begin_pending')==3
 assert S.campaign.spawn==0 and get('checkpoint_spawn')==3
 assert bytes(SRAM)==bank and count('begin')==count('step')==count('anchor_step')==0
 assert bytes(E)==enemies and bytes(SH)==shots
 render();update(1023);assert get('save_begin_pending')==2;render()
 assert count('render')==2 and list(VALID)==[1,1]
 return bank,old,bytes(S)

def unchanged_gameplay(pose,enemies,shots,timers):
 assert (get('px'),get('py'),get('room'),get('face'),get('summoned'))==pose
 assert bytes(E)==enemies and bytes(SH)==shots
 assert tuple(get(n) for n in POWER_FIELDS)==timers
 assert count('enemies')==count('shots')==count('tick')==count('ability')==0

def finish_proof(bank,queued,freeze=False):
 slices=0
 pose=tuple(get(n) for n in ('px','py','room','face','summoned'))
 enemies,shots=bytes(E),bytes(SH);timers=tuple(get(n) for n in POWER_FIELDS)
 power_ticks=count('power_ticks')
 warm=bytes(CACHE)
 while get('save_begin_pending')==2:
  assert slices<1000,'bounded proof did not terminate'
  update(1023);slices+=1
  assert get('game_state')==6 and count('begin')==count('step')==0 and bytes(SRAM)==bank
  assert count('power_ticks')==power_ticks
  if freeze:unchanged_gameplay(pose,enemies,shots,timers)
  if get('save_begin_pending')==2:
   assert bytes(S)==queued and S.campaign.spawn==0
   assert L.magma_game_save_prepare_pending()
  else:assert get('save_begin_pending')==1 and not get('save_completion_pending')
  render();assert count('render')==2 and bytes(CACHE)==warm
 assert slices>1 and count('anchor_step')==slices
 assert count('anchor')==count('anchor_sync')==0 and count('preflight_begin')==1
 assert not L.magma_game_save_prepare_pending() and not L.save5_preflight_active()
 return slices

def synchronous_oracle(area,lit,fixture):
 setup(area,lit,fixture);update(1)
 assert get('save_begin_pending')==3 and L.magma_game_prepare_save()==1
 expected=bytes(S)
 assert count('anchor')==1 and S.campaign.spawn==3
 return expected

def test_full_schedule():
 global heavy_steps,cut_fixture
 for fixture in (BASE,FULL):
  for area in (38,39):
   for lit in (False,True):
    expected=synchronous_oracle(area,lit,fixture)
    bank,old,queued=begin(area,lit,fixture,True)
    put('ability_max',17)
    for n in ('ability_cd','roll_cd','heal_cd'):put(n,17)
    pose=tuple(get(n) for n in ('px','py','room','face','summoned'));enemies,shots=bytes(E),bytes(SH);timers=tuple(get(n) for n in POWER_FIELDS)
    slices=finish_proof(bank,queued,True)
    assert bytes(S)==expected and S.quests.anchors[3]&(1<<(area-38))
    live=bytes(S);assert L.magma_game_prepare_save_step()==FAILED and L.magma_game_prepare_save()==0 and bytes(S)==live
    update(1023);assert get('save_begin_pending')==0 and count('begin')==1 and count('step')==0 and bytes(SRAM)==bank
    drain();assert get('game_state')==1 and not get('save_failed')
    unchanged_gameplay(pose,enemies,shots,timers)
    saved=loaded();assert saved.campaign.spawn==3 and saved.campaign.room==area
    assert bytes(saved.roster)==bytes(S.roster) and bytes(saved.quests)==bytes(S.quests) and bytes(saved.equipment)==bytes(S.equipment)
    assert count('begin')==1 and bytes(S.roster)==bytes(Save.from_buffer_copy(queued).roster)
    if fixture==FULL and area==39 and not lit:heavy_steps=slices
    if fixture==BASE and area==39 and not lit:cut_fixture=(bank,old,expected,bytes(saved))
    record('bounded_save_exact_schedule_and_synchronous_oracle',fixture=fixture,area=area,lit=lit,busy_and_done_updates=slices,writer_begins=1,static_page_requests=2)

def test_failure_and_ownership():
 for phase in (1,heavy_steps-1):
  for kind in ('reset','explicit_cancel','old_sync_call','room','campaign_room','campaign_spawn','checkpoint','pose','facing','chapter','revision','live_bytes','foreign_lease'):
   bank,old,queued=begin(fixture=FULL)
   for _ in range(phase):update()
   assert get('save_begin_pending')==2 and L.save5_preflight_active()
   foreign=0
   if kind=='reset':L.magma_game_reset()
   elif kind=='explicit_cancel':L.magma_game_cancel_save_prepare();L.magma_game_cancel_save_prepare()
   elif kind=='old_sync_call':assert L.magma_game_prepare_save()==0
   elif kind=='room':put('room',38)
   elif kind=='campaign_room':S.campaign.room=38
   elif kind=='campaign_spawn':S.campaign.spawn=1
   elif kind=='checkpoint':put('checkpoint_spawn',1)
   elif kind=='pose':put('px',get('px')+1)
   elif kind=='facing':put('face',0)
   elif kind=='chapter':put('chapter_flags',get('chapter_flags')^1)
   elif kind=='revision':put('progression_revision',get('progression_revision')+1)
   elif kind=='live_bytes':S.campaign.sequence^=1
   else:
    L.save5_preflight_cancel();foreign=L.save5_preflight_begin(C.byref(S));assert foreign
   changed=bytes(S)
   for _ in range(1000):
    update(1023)
    assert bytes(S)==changed and bytes(SRAM)==bank and count('begin')==count('step')==0
    if get('save_completion_pending'):break
   else:raise AssertionError('stale proof did not fail')
   assert get('save_completion_pending')==FAILED and get('game_state')==6
   update();assert get('game_state')==1 and get('save_failed')==get('save_failure_notice')==1
   assert not L.magma_game_save_prepare_pending() and bytes(S)==changed and bytes(SRAM)==bank
   if kind not in ('room','checkpoint'):assert get('checkpoint_spawn')==0
   if foreign:assert L.save5_preflight_status(foreign)==BUSY;L.save5_preflight_cancel()
   else:assert not L.save5_preflight_active()
   record('bounded_save_stale_cancel_and_lease_rollback',phase_updates=phase,mutation=kind)
 # Malformed state before the first captured proof must fail strict validation.
 bank,old,queued=begin();S.roster.instances[0].level=0;changed=bytes(S)
 while not get('save_completion_pending'):update()
 update();assert get('save_failed') and bytes(S)==changed and bytes(SRAM)==bank and get('checkpoint_spawn')==0 and count('begin')==0
 record('bounded_save_invalid_first_capture_rejected')

def test_duplicates_resets_and_reentry():
 for action in ('reset','new','load','same_room_reentry'):
  bank,old,queued=begin(fixture=FULL);update();assert L.save5_preflight_active()
  if action=='reset':L.magma_game_reset()
  elif action=='new':L.start_game(0)
  elif action=='load':L.start_game(1)
  else:L.enter_room(39,0)
  assert not L.magma_game_save_prepare_pending() and not (S.quests.anchors[3]&2)
  assert bytes(SRAM)==bank
  if action=='reset':assert get('checkpoint_spawn')==0 and S.campaign.spawn==0
  # New/load/entry may schedule their own independent save after cancellation.
  if action=='same_room_reentry':
   settle_all();assert get('room')==39 and get('checkpoint_spawn')==0 and not get('save_failed')
   assert not S.quests.anchors[3]&2 and loaded().campaign.spawn==0
  record('bounded_save_engine_lifecycle_cancels_uncommitted_anchor',action=action)
 bank=setup();assert L.magma_game_interact()==1
 rev=(get('magma_game_revision'),get('progression_revision'));put('hero_hp_q4',16);put('hp',1)
 for _ in range(3):assert L.magma_game_interact()==1
 assert get('hero_hp_q4')==16 and rev==(get('magma_game_revision'),get('progression_revision'))
 L.save_frame();render();update();render();queued=bytes(S);finish_proof(bank,queued)
 assert L.magma_game_prepare_save_step()==FAILED and S.campaign.spawn==3
 record('bounded_save_duplicate_interactions_and_commit_at_most_once')

def settle_all():
 for _ in range(2000):
  if get('game_state') not in (6,10) and not get('save_requested'):break
  update();L.save_frame()
 else:raise AssertionError('replacement event/save did not terminate')
 assert not L.save5_preflight_active()

def test_general_entry_replacement():
 for warm_updates in (0,5):
  bank=setup(fixture=FULL)
  L.enter_room(38,0)
  assert get('game_state')==10 and L.magma_game_enter_pending() and get('room')==39
  for _ in range(warm_updates):update()
  assert get('game_state')==10
  L.enter_room(39,0)
  assert get('game_state')==10 and not L.magma_game_save_prepare_pending()
  assert bytes(SRAM)==bank
  settle_all()
  assert get('game_state')==1 and get('room')==39 and get('checkpoint_spawn')==0 and not get('save_failed')
  assert not L.magma_game_enter_pending() and not L.magma_game_save_prepare_pending()
  assert not S.quests.anchors[3]&2 and loaded().campaign.spawn==0
  record('bounded_save_general_entry_replacement_preserves_caller_mode',warm_updates=warm_updates)

def test_power_cuts():
 bank,old,prepared,final=cut_fixture
 # The engine has already produced this exact typed state and final bank.
 # Exhaust every durable byte cut with the real synchronous codec, separately
 # from representative full-engine scheduler failure/retry checks below.
 SRAM[:]=bank;L.save5_test_reset_writer();L.save5_test_fail_after(-1);candidate=Save.from_buffer_copy(prepared)
 assert L.save5_store(C.byref(candidate))==1;total=L.save5_test_write_count()
 for cut in range(total+1):
  SRAM[:]=bank;L.save5_test_reset_writer();L.save5_test_fail_after(cut);candidate=Save.from_buffer_copy(prepared)
  result=L.save5_store(C.byref(candidate));observed=bytes(loaded())
  assert observed in (old,final),(cut,result)
  if result:assert observed==final,cut
 L.save5_test_reset_writer();L.save5_test_fail_after(-1)
 record('bounded_save_prepared_state_every_durable_cut',cuts=total+1,scope='Real codec on the exact engine-prepared state; no controller or hardware claim')
 for cut in (0,1,31,32,1024,3072,6144,total):
  bank,old,queued=begin();finish_proof(bank,queued);L.save5_test_fail_after(cut);update();drain()
  observed=bytes(loaded());assert observed in (old,final)
  assert S.campaign.spawn==3 and S.quests.anchors[3]&2 and get('checkpoint_spawn')==3
  if get('save_failed'):
   L.save5_test_fail_after(-1);put('game_state',3);L.save_game();L.save_frame();drain()
   assert not get('save_failed') and loaded().campaign.spawn==3
  record('bounded_save_linked_writer_cut_and_safe_retry',cut=cut,old_or_new_valid=True)

import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=('all','power-cuts'),default='all');args=parser.parse_args()
RESULT['selected_case']=args.case
tests=(test_full_schedule,test_power_cuts) if args.case=='power-cuts' else (test_full_schedule,test_failure_and_ownership,test_duplicates_resets_and_reentry,test_general_entry_replacement,test_power_cuts)
try:
 for test in tests:
  print('BEGIN',test.__name__,flush=True);test()
 assert len(RESULT['checks'])==(17 if args.case=='power-cuts' else 51)
 RESULT['passed']=True
except BaseException as error:
 RESULT['passed']=False;RESULT['failures'].append({'error':repr(error),'traceback':traceback.format_exc()})
 raise
finally:
 RESULT['sources_still_frozen']=all(hashlib.sha256((SOURCE_ROOT/p).read_bytes()).hexdigest()==h for p,h in EXPECTED.items())
 if not RESULT['sources_still_frozen']:RESULT['passed']=False
 output=Path(os.environ.get('PROBE_RESULT_NAME',str(ROOT/'build/current-host-evidence/bounded-magma-save.json')))
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(RESULT,indent=2)+'\n')
 print(json.dumps({'passed':RESULT['passed'],'checks':len(RESULT['checks']),'output':str(output),'sources_still_frozen':RESULT['sources_still_frozen']}),flush=True)
assert RESULT['sources_still_frozen']
