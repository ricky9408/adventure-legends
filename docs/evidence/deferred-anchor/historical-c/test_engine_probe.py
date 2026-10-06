#!/usr/bin/env python3
"""Independent synthetic full-engine deferred-anchor checks.

Loads real SRAM fixtures then deliberately edits host state and supplies direct
host input edges. All production modules remain unchanged and are instrumented
at function entry. Inert low-address backing memory permits the real cache and
OBJ routines to execute; DMA/timers/display are NOT emulated. These are neither
native controller gameplay nor hardware timing/pixel correctness evidence.
"""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[3]
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
 'magma_powers','magma_power_art']
RESULT={'scope':'Synthetic host state and input-edge integration; real production functions with entry instrumentation',
 'native_controller_gameplay':False,'native_hardware_timing':False,'emulator_ram_injection':False,
 'dma_emulated':False,'compiler':os.environ.get('HOST_CC','cc'),'checks':[],'source_sha256':{}}
for name in ('game','magma_game','magma_quests','save5','progression'):
 RESULT['source_sha256']['src/'+name+'.c']=hashlib.sha256((ROOT/'src'/f'{name}.c').read_bytes()).hexdigest()
TMP=tempfile.TemporaryDirectory(prefix='deferred-anchor-review-')
SO=Path(TMP.name)/'probe.so'
subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+[
 '-shared','-fPIC','-O0','-g','-std=c99','-fno-builtin','-fno-inline',
 '-finstrument-functions','-Wno-attributes','-Wno-pointer-to-int-cast',
 '-Wno-int-to-pointer-cast','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST',
 '-DGAME_HOST_TEST','-Dmain=gba_main','-Isrc','-Wl,-Bsymbolic',
 str(OUT/'engine_probe.c'),*[str(ROOT/'src'/f'{n}.c') for n in MODULES],
 '-o',str(SO)],cwd=ROOT,check=True)
L=C.CDLL(str(SO));assert L.probe_map()==1,'cannot map synthetic host backing memory'
for name in ('save5_load','save5_store','save5_validate'):
 getattr(L,name).argtypes=[C.POINTER(Save)];getattr(L,name).restype=C.c_int
L.save5_test_fail_after.argtypes=[C.c_int]
S=Save.in_dll(L,'adventure_save');SRAM=(C.c_ubyte*32768).in_dll(L,'save5_test_sram')
OLD=(C.c_ubyte*256).in_dll(L,'save4_test_sram');OLD[:]=b'\xff'*256
CACHE=(C.c_uint*60).in_dll(L,'cache_fields')
VALID=(C.c_int*2).in_dll(L,'cache_valid')
class Enemy(C.Structure):_fields_=[(n,C.c_int)for n in ('x','y','hp','flash','kind')]
class Shot(C.Structure):_fields_=[(n,C.c_int)for n in ('x','y','dx','dy','life','owner')]
E=(Enemy*6).in_dll(L,'enemies');SH=(Shot*12).in_dll(L,'shots')
def get(n):return C.c_int.in_dll(L,n).value
def put(n,v):C.c_int.in_dll(L,n).value=v
def count(n):return get('probe_'+n)
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

# Real update -> real A interaction -> immediate freeze, in both anchor rooms.
for area in (38,39):
 for lit in (False,True):
  before=setup(area,lit);roster=bytes(S.roster);quests=bytes(S.quests);equip=bytes(S.equipment)
  # Synthetic imminent enemy and hostile projectile at the rest approach.
  E[0]=Enemy(get('px'),get('py'),5,0,0);SH[0]=Shot(get('px'),get('py'),1,0,8,1)
  enemies=bytes(E);shots=bytes(SH);pose=(get('px'),get('py'));calls=[]
  update(1|256)
  assert get('game_state')==6 and get('save_begin_pending')==3
  assert count('anchor')==count('begin')==count('step')==count('enemies')==count('shots')==count('tick')==count('ability')==0
  assert bytes(E)==enemies and bytes(SH)==shots
  assert get('hero_hp_q4')>16 and get('checkpoint_spawn')==3
  assert S.campaign.spawn==0 and bytes(SRAM)==before and L.save5_validate(C.byref(S))==1
  rev=(get('magma_game_revision'),get('progression_revision'));render();calls.append(count('render'))
  update(1023);assert get('save_begin_pending')==2 and count('anchor')==0
  render();calls.append(count('render'));warm=bytes(CACHE)
  assert list(VALID)==[1,1] and calls==[1,2]
  update(1023)
  assert get('save_begin_pending')==1 and count('anchor')==1 and count('begin')==0
  assert count('anchor_modes')==1<<6 and S.campaign.spawn==3 and get('checkpoint_spawn')==3
  assert S.quests.anchors[3]&(1<<(area-38))
  assert rev==(get('magma_game_revision'),get('progression_revision'))
  assert not L.magma_game_save_prepare_pending() and L.magma_game_prepare_save()==0 and count('anchor')==1
  render();calls.append(count('render'));assert calls==[1,2,2] and bytes(CACHE)==warm
  assert bytes(SRAM)==before and (get('px'),get('py'))==pose
  update(1023);assert count('begin')==1 and get('save_begin_pending')==0
  assert count('step')==0 and bytes(SRAM)==before
  render();calls.append(count('render'));assert calls==[1,2,2,2]
  drain();assert get('game_state')==1 and get('save_failed')==0
  after=loaded();assert after.campaign.room==area and after.campaign.spawn==3
  assert bytes(S.roster)==roster and bytes(S.equipment)==equip
  assert count('enemies')==count('shots')==count('tick')==count('ability')==0
  assert bytes(E)==enemies and bytes(SH)==shots
  record('full_engine_warmup_and_exact_once',area=area,already_lit=lit,render_static_cumulative=calls,
   anchor_mode=6,old_bank_unchanged_until_writer=True,no_hostile_or_R_update=True,no_rewards_duplicated=True)

# Priorities are tested through real input dispatch, not direct rest calls.
for keys,want_mode in [(1|8,3),(1|512,1),(1|4,1)]:
 before=setup();update(keys)
 assert not L.magma_game_save_prepare_pending() and count('anchor')==count('begin')==0
 assert get('game_state')==want_mode and S.campaign.spawn==0 and get('checkpoint_spawn')==0
 assert bytes(SRAM)==before
 record('simultaneous_input_precedence',buttons=keys,game_state=want_mode)

# Cancel/reset/redirect between enqueue and the dedicated proof must fail closed.
for kind in ('reset','wrong_room','wrong_campaign_room','wrong_campaign_spawn','wrong_checkpoint','invalid_roster'):
 before=setup();update(1);assert get('save_begin_pending')==3
 if kind=='reset':L.magma_game_reset()
 elif kind=='wrong_room':put('room',38)
 elif kind=='wrong_campaign_room':S.campaign.room=38
 elif kind=='wrong_campaign_spawn':S.campaign.spawn=1
 elif kind=='wrong_checkpoint':put('checkpoint_spawn',1)
 elif kind=='invalid_roster':S.roster.instances[0].level=0
 update();update()
 assert get('game_state')==1 and get('save_failed')==get('save_failure_notice')==1
 assert not L.magma_game_save_prepare_pending() and count('begin')==count('step')==0
 assert count('anchor')==(kind=='invalid_roster') and S.quests.anchors[3]&2==0
 assert bytes(SRAM)==before
 if kind not in ('wrong_room','wrong_checkpoint'):assert get('checkpoint_spawn')==0
 record('prepare_failure_no_snapshot_or_write',failure=kind,anchor_calls=count('anchor'))

# Explicit wrong-mode prepare consumes queue and cannot commit.
before=setup();assert L.magma_game_interact()==1
assert L.magma_game_save_prepare_pending() and get('game_state')==1
assert L.magma_game_prepare_save()==0 and get('checkpoint_spawn')==0
assert count('anchor')==0 and S.campaign.spawn==0 and bytes(SRAM)==before
record('wrong_mode_prepare_cancels_without_validation')

# Later bank failure retains valid live progress; old committed bank survives.
for fail_after in (0,50,3000,6144):
 before=setup();prior=loaded();active=next(p for p in (0x200,0x1a00)if int.from_bytes(before[p+8:p+12],'little')==prior.campaign.sequence);update(1);update();update()
 assert S.campaign.spawn==3 and S.quests.anchors[3]&2
 L.save5_test_fail_after(fail_after);update();drain()
 assert get('game_state')==1 and get('save_failed')==get('save_failure_notice')==1,(fail_after,get('game_state'),get('save_failed'),get('save_failure_notice'),L.save5_test_write_count())
 old=loaded();assert old.campaign.spawn==0 and old.campaign.sequence==prior.campaign.sequence
 assert not(old.quests.anchors[3]&2)
 assert bytes(SRAM)[active:active+6144]==before[active:active+6144]
 assert S.campaign.spawn==3 and get('checkpoint_spawn')==3 and S.quests.anchors[3]&2
 assert L.save5_validate(C.byref(S))==1 and count('anchor')==1
 # Failure is persistent in a modal; retry reuses live proof without duplication.
 put('game_state',3)
 for _ in range(130):update()
 assert get('save_failure_notice')==1
 L.save5_test_fail_after(-1);L.save_game();L.save_frame();assert get('save_begin_pending')==1
 drain();now=loaded()
 assert get('game_state')==3 and get('save_failed')==get('save_failure_notice')==0
 assert now.campaign.spawn==3 and now.quests.anchors[3]&2 and now.campaign.sequence==prior.campaign.sequence+1
 assert count('anchor')==1
 record('write_failure_and_safe_retry',fail_after=fail_after,retains_live_anchor=True,old_bank_loadable=True)

# Reset/load/new-game production entry points cancel uncommitted pending proof.
for resume in (0,1):
 before=setup();update(1);L.start_game(resume)
 assert not L.magma_game_save_prepare_pending() and count('anchor')==0
 assert not(S.quests.anchors[3]&2)
 assert bytes(SRAM)==before
 L.save_frame();assert get('save_begin_pending')==1;drain()
 assert get('save_failed')==0 and loaded().campaign.spawn==0
 record('start_game_cancels_pending',resume=resume,room=get('room'))
# Death reset is unreachable after a real rest's immediate freeze. Exercise the
# production death routine from an explicitly synthetic pre-freeze boundary.
before=setup();assert L.magma_game_interact()==1
put('hero_hp_q4',1);put('hp',1);L.damage_amount(255,255)
assert get('game_state')==4 and not L.magma_game_save_prepare_pending(),{n:get(n)for n in ('game_state','hero_hp_q4','invuln','guard_invuln','roll_ticks','stone_guard')}
assert get('checkpoint_spawn')==0 and S.campaign.spawn==0 and not(S.quests.anchors[3]&2)
assert bytes(SRAM)==before
L.save_frame();assert get('save_begin_pending')==1;drain()
assert get('game_state')==4 and get('save_failed')==0 and loaded().campaign.spawn==0
record('synthetic_pre_freeze_death_cancels_pending')

# Multiple synthetic calls cannot duplicate a queued interaction or its heal.
before=setup();assert L.magma_game_interact()==1
rev=(get('magma_game_revision'),get('progression_revision'));put('hero_hp_q4',16);put('hp',1)
assert L.magma_game_interact()==1 and get('hero_hp_q4')==16
assert rev==(get('magma_game_revision'),get('progression_revision')) and count('anchor')==0
L.save_frame();update();update();assert count('anchor')==1
update();drain();assert get('save_failed')==0
record('duplicate_queue_calls_do_not_reheal_or_revalidate')

# Distinct prior doorway checkpoints are restored precisely, not to a default.
for checkpoint in (0,1,2,3):
 setup(lit=checkpoint==3);put('checkpoint_spawn',checkpoint);S.campaign.spawn=checkpoint
 assert L.save5_validate(C.byref(S))==1
 assert L.magma_game_interact()==1
 assert S.campaign.spawn==checkpoint
 L.magma_game_reset()
 assert get('checkpoint_spawn')==checkpoint and S.campaign.spawn==checkpoint
 assert not L.magma_game_save_prepare_pending()
 record('restores_exact_prior_checkpoint',checkpoint=checkpoint)

# A full controller-earned snapshot is decoded, then unlit/current-area state
# is intentionally modified for synthetic regression only, never provenance.
full='build/magma-bringup-09/09-all65-earned-town.sav'
if (ROOT/full).exists():
 before=setup(38,False,full);roster=bytes(S.roster);update(1);render();update();render();update();render()
 assert count('anchor')==1 and count('render')==2
 assert bytes(S.roster)==roster and bytes(SRAM)==before
 update();drain();assert get('save_failed')==0 and loaded().campaign.spawn==3
 record('large_roster_synthetic_regression',fixture=full,
  fixture_sha256=hashlib.sha256((ROOT/full).read_bytes()).hexdigest(),native_claim=False)
RESULT['passed']=True
(OUT/os.environ.get('PROBE_RESULT_NAME','engine-probe-results.json')).write_text(json.dumps(RESULT,indent=2)+'\n')
print(json.dumps(RESULT,indent=2))
