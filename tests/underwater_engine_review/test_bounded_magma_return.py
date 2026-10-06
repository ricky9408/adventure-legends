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
ROOT=Path(__file__).resolve().parents[2]
SOURCE_ROOT=Path(os.environ.get('UNDERWATER_REVIEW_SOURCE',str(ROOT)))
COMPILE_SOURCES={str(p.relative_to(SOURCE_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE_ROOT/'src').rglob('*') if p.is_file()}
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
RESULT={'scope':'Synthetic host state and input-edge integration; real production functions with entry instrumentation',
 'native_controller_gameplay':False,'native_hardware_timing':False,'emulator_ram_injection':False,
 'dma_emulated':False,'compiler':os.environ.get('HOST_CC','cc'),'checks':[],'source_sha256':{}}
for name in ('game','magma_game','magma_quests','save5','progression'):
 RESULT['source_sha256']['src/'+name+'.c']=hashlib.sha256((SOURCE_ROOT/'src'/f'{name}.c').read_bytes()).hexdigest()
TMP=tempfile.TemporaryDirectory(prefix='deferred-anchor-review-')
SO=Path(TMP.name)/'probe.so'
subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+[
 '-shared','-fPIC','-O0','-g','-std=c99','-fno-builtin','-fno-inline',
 '-finstrument-functions','-Wno-attributes','-Wno-pointer-to-int-cast',
 '-Wno-int-to-pointer-cast','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST',
 '-DGAME_HOST_TEST','-Dmain=gba_main','-I'+str(SOURCE_ROOT/'src'),'-Wl,-Bsymbolic',
 str(OUT/'engine_probe.c'),*[str(SOURCE_ROOT/'src'/f'{n}.c') for n in MODULES],
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
CACHE=(C.c_uint*64).in_dll(L,'cache_fields')
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


# Candidate-A full-engine diagnostics. Every externally edited state is synthetic.
expected=COMPILE_SOURCES
assert all(hashlib.sha256((SOURCE_ROOT/p).read_bytes()).hexdigest()==h for p,h in expected.items()),'Source changed during compilation'
RESULT['manifest_sha256']=hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()
RESULT['scope']='Synthetic full-engine host regression of bounded Magma return; current development source, not candidate-A evidence'
RESULT['source_sha256']=expected
RESULT['modules']=MODULES
class Trial(C.Structure):
 _fields_=[('id',C.c_uint),('generation',C.c_uint),('party_signature',C.c_uint),('index',C.c_ubyte),('slot',C.c_ubyte),('form',C.c_ubyte),('family',C.c_ubyte),('key',C.c_ubyte),('source',C.c_ubyte),('command',C.c_ubyte),('selected_party',C.c_ubyte),('setting',C.c_ubyte*4),('casts',C.c_ubyte),('walk',C.c_ubyte),('order',C.c_ubyte),('failed',C.c_ubyte)]
T=Trial.in_dll(L,'underwater_game_trial')
FULL='tests/fixtures/v5-revision5/magma-all65-town.sav'
legacy_setup=setup
maxima={'event_slices':0,'evolution_slices':0,'event_frames':0,'writer_frames':0}
def setup():
 L.progression_evolution_cancel();L.underwater_game_reset();L.underwater_powers_reset()
 before=legacy_setup(38,True,FULL)
 assert L.underwater_game_can_enter(46)==1
 return before

def frame(buttons=0,draw=False):
 old=get('game_state');c={n:count(n) for n in ('job','preflight','admission','evolve','validate')}
 update(buttons);L.save_frame()
 if old==10:
  assert count('job')-c['job']<=1
  maxima['event_slices']=max(maxima['event_slices'],count('job')-c['job'])
  assert count('validate')==c['validate']
 if old==7:
  slices=count('preflight')-c['preflight']+count('admission')-c['admission']
  assert slices<=3
  assert not(count('evolve')>c['evolve'] and slices)
  maxima['evolution_slices']=max(maxima['evolution_slices'],slices)
  assert count('validate')==c['validate']
 if draw:render()

def settle(buttons=0,draw=False):
 n=0;events=writers=0
 while get('game_state') in (6,10) or L.underwater_game_event_pending() or get('save_requested'):
  assert n<5000,'event/save scheduler failed to terminate'
  events+=get('game_state')==10;writers+=get('game_state')==6
  frame(buttons,draw);n+=1
 maxima['event_frames']=max(maxima['event_frames'],events);maxima['writer_frames']=max(maxima['writer_frames'],writers)
 assert not L.save5_preflight_active()
 return n

def enter(area,spawn=0):
 L.enter_room(area,spawn);L.save_frame();settle()
 assert get('room')==area and get('checkpoint_spawn')==spawn,(area,get('room'),get('checkpoint_spawn'))
 assert not get('save_failed')
 put('transition_lock',0)
 for i in range(6):E[i]=Enemy()
 for i in range(12):SH[i]=Shot()

def at(x,y,face=1):
 put('game_state',1);L.game_region_warp(x,y);assert (get('px'),get('py'))==(x,y)
 put('face',face);put('keys',0);put('pressed',0);L.game_attacks_reset();put('invuln',0);put('hitstop',0);put('roll_ticks',0)

def target(x,y,face=1):
 dx,dy={0:(0,-16),1:(0,16),2:(16,0),3:(-16,0)}[face]
 at(x+dx,y+dy,face);frame(1);settle()
 assert not get('save_failed'),(x,y)
 if get('game_state')==2:
  for _ in range(8):
   frame(1);settle()
   if get('game_state')!=2:break
 assert get('game_state')==1

def selected():return S.roster.instances[S.roster.party[S.roster.selected_party]]
def select_form(form):
 slot=next(i for i,c in enumerate(S.roster.instances) if c.form_id==form)
 party=list(S.roster.party)
 if slot in party:
  n=party.index(slot);S.roster.party[0],S.roster.party[n]=slot,party[0]
 else:S.roster.party[0]=slot
 S.roster.selected_party=0;L.progression_refresh();put('summoned',1)
 return slot

def guarantees():
 setup();enter(46);target(144,104);target(120,72)
 assert S.quests.objectives[38]==3 and ((S.quests.states[9]>>4)&3)==3
 target(340,108);target(340,108);enter(47)
 for x,y in ((176,164),(304,164),(240,192)):
  at(x,y);frame();settle()
 enter(46);target(340,72)
 assert S.quests.objectives[39]==3 and ((S.quests.states[9]>>6)&3)==3
 assert L.save5_validate(C.byref(S))==1

def trial_start():
 guarantees();enter(50);slot=select_form(49);target(48,112)
 assert T.index==0 and T.slot==slot and T.id==selected().instance_id
 return slot

def test_visit():
 setup();before=bytes(S);bank=bytes(SRAM);pose=(get('room'),get('px'),get('py'),get('checkpoint_spawn'));L.probe_reset()
 L.enter_room(46,0)
 assert get('game_state')==10 and bytes(S)==before and bytes(SRAM)==bank
 assert (get('room'),get('px'),get('py'),get('checkpoint_spawn'))==pose
 for _ in range(2):frame(1023,True);assert bytes(S)==before and count('job')==0
 assert list(VALID)==[1,1]
 settle(1023,True)
 assert get('room')==46 and S.campaign.room==46 and S.quests.region_flags[4]==1
 assert count('enemies')==count('shots')==count('ability')==0
 assert count('validate')==0
 assert L.save5_validate(C.byref(S))==1
 record('new_visit_freezes_old_scene_before_validation_and_transition',honest_two_page_warmup=True)

def test_rests():
 for area in (46,47):
  for already in (False,True):
   setup();enter(46)
   if area!=46:enter(area)
   if already:target(80 if area==46 else 64,256)
   at(80 if area==46 else 64,272);put('hero_hp_q4',16);put('hp',1)
   before=bytes(S);bank=bytes(SRAM);checkpoint=get('checkpoint_spawn');L.probe_reset()
   E[0]=Enemy(get('px'),get('py'),5,0,0);SH[0]=Shot(get('px'),get('py'),1,0,8,1)
   enemies=bytes(E);shots=bytes(SH)
   frame(1|256,True)
   assert get('game_state')==10 and get('hero_hp_q4')==16 and get('checkpoint_spawn')==checkpoint
   assert bytes(S)==before and bytes(SRAM)==bank and count('heal')==count('job')==0
   for _ in range(2):frame(1023,True);assert bytes(S)==before and count('heal')==count('job')==0
   settle(1023,True)
   assert get('hero_hp_q4')>16 and get('checkpoint_spawn')==2 and S.campaign.spawn==2
   assert count('heal')==1 and count('enemies')==count('shots')==count('ability')==0
   assert bytes(E)==enemies and bytes(SH)==shots and S.quests.anchors[4]&(1<<(area-46))
   assert count('validate')==0
   record('underwater_rest_delayed_exact_once_with_hostiles_frozen',area=area,already_lit=already)

def test_cancel_and_invalid():
 for stage in (0,3,8,30):
  setup();enter(46);at(80,272);put('hero_hp_q4',16);put('hp',1);before=bytes(S);bank=bytes(SRAM)
  frame(1)
  for _ in range(stage):
   assert get('game_state')==10
   frame()
  L.underwater_game_reset();settle()
  assert bytes(S)==before and bytes(SRAM)==bank and get('hero_hp_q4')==16 and get('checkpoint_spawn')==0
  record('explicit_world_reset_revokes_pending_anchor',pending_frame=stage)
 setup();enter(46);at(80,272);bank=bytes(SRAM);frame(1)
 for _ in range(6):frame()
 S.roster.instances[0].level=0;corrupt=bytes(S)
 settle()
 assert get('save_failed')==1 and bytes(S)==corrupt and bytes(SRAM)==bank
 assert S.quests.anchors[4]==0 and get('checkpoint_spawn')==0
 record('changed_invalid_live_state_fails_before_anchor_or_writer')
 setup();enter(46);at(80,272);before=bytes(S);bank=bytes(SRAM)
 assert L.underwater_game_interact()==1 and L.underwater_game_event_pending()
 put('hero_hp_q4',1);put('hp',1);L.damage_amount(255,255)
 assert get('game_state')==4 and not L.underwater_game_event_pending() and not L.save5_preflight_active()
 assert bytes(S)==before and bytes(SRAM)==bank and not S.quests.anchors[4]
 record('real_death_resets_pre_freeze_world_intent')
 for resume in (0,1):
  setup();enter(46);at(80,272);bank=bytes(SRAM);frame(1);frame();frame();frame()
  L.start_game(resume)
  assert not L.underwater_game_event_pending() and not L.save5_preflight_active()
  assert not S.quests.anchors[4] and bytes(SRAM)==bank
  record('new_game_or_load_revokes_pending_anchor',resume=resume)

def test_rewards():
 guarantees();before=bytes(S.roster);ids=S.roster.next_instance_id
 target(120,72);target(340,72)
 assert bytes(S.roster)==before and S.roster.next_instance_id==ids
 record('multi_intent_guaranteed_quests_claim_once_and_repeated_npc_is_idempotent')


def test_selection_invalidation():
 for mode in ('selected_away_back','unselected_party_away_back','command_away_back','room','death'):
  slot=trial_start();c=selected();identity=c.instance_id;form=c.form_id;command=L.progression_command()
  token=L.underwater_game_action_begin(3)
  assert token and T.index==0
  if mode=='selected_away_back':
   select_form(52);select_form(49)
  elif mode=='unselected_party_away_back':
   S.roster.party[2],S.roster.party[3]=S.roster.party[3],S.roster.party[2];L.progression_selection_changed()
   S.roster.party[2],S.roster.party[3]=S.roster.party[3],S.roster.party[2];L.progression_selection_changed()
  elif mode=='command_away_back':
   original=c.selected_command;assert c.equipped[original^1]!=c.equipped[original]
   c.selected_command^=1;L.progression_selection_changed()
   c.selected_command=original;L.progression_selection_changed()
  elif mode=='room':enter(48)
  else:
   put('invuln',0);put('guard_invuln',0);put('roll_ticks',0);put('stone_guard',0);put('hero_hp_q4',1);put('hp',1);L.damage_amount(255,255)
   assert get('game_state')==4
  assert T.index==255 and T.id==0
  assert L.underwater_game_field_hit(0,command,identity,form,token)==0
  assert S.roster.instances[slot].trial_flags==0
  record('engine_selection_and_lifecycle_revoke_exact_trial_and_old_cast',invalidation=mode)

def trained_echo():
 slot=trial_start();target(72,60);target(168,60)
 assert T.setting[0]==T.setting[1]==1
 c=selected()
 for target_id in (0,1):
  token=L.underwater_game_action_begin(3)
  assert L.underwater_game_field_hit(target_id,L.progression_command(),c.instance_id,c.form_id,token)==1
  assert L.underwater_game_field_hit(target_id,L.progression_command(),c.instance_id,c.form_id,token)==0
  L.save_frame();settle()
 assert c.trial_flags&1 and c.level>=28 and c.bond>=45 and T.index==255
 enter(46);select_form(49)
 return slot

def evolution_open():
 put('game_state',3);put('journal_tab',3);put('keys',0);put('pressed',0);L.probe_reset();before=bytes(S)
 frame(4,True);assert get('game_state')==7 and L.progression_evolution_busy()
 assert bytes(S)==before and count('preflight')==count('admission')==0
 for _ in range(2):frame(0,True);assert bytes(S)==before and count('preflight')==count('admission')==0
 for _ in range(300):
  if not L.progression_evolution_busy():break
  frame(0,True);assert bytes(S)==before
 else:raise AssertionError('opening evolution proof did not terminate')
 assert get('game_state')==7 and get('progression_evolution_reason')==0 and not L.save5_preflight_active()
 return before

def test_evolution_dispatch():
 slot=trained_echo();before=evolution_open();bank=bytes(SRAM);frame(1)
 assert get('game_state')==7 and L.progression_evolution_busy() and bytes(S)==before
 for i in range(300):
  if get('game_state')!=7:break
  frame(0,True)
  if get('game_state')==7:assert bytes(S)==before
 else:raise AssertionError('confirmation proof did not terminate')
 assert get('game_state')==8 and count('evolve')==1 and S.roster.instances[slot].form_id==50
 assert not L.save5_preflight_active() and bytes(SRAM)==bank
 for _ in range(80):frame(1,True)
 settle()
 assert get('game_state')==3 and count('evolve')==1 and loaded().roster.instances[slot].form_id==50
 record('real_update_drives_two_page_bounded_evolution_and_delayed_save',confirmed_frames=i,maximum_slices_per_update=3)

 for mode in ('cancel_chord','direction_chord','selection','room','load','foreign_owner'):
  slot=trained_echo();before=evolution_open();frame(1)
  for _ in range(5):frame()
  if mode=='cancel_chord':frame(1|2);assert get('game_state')==3
  elif mode=='direction_chord':frame(1|16);assert get('game_state')==7 and not L.progression_evolution_busy()
  elif mode=='selection':
   select_form(52);select_form(49);before=bytes(S);frame();assert get('game_state')==3
  elif mode=='room':
   L.enter_room(47,0);L.save_frame();settle();before=bytes(S)
  elif mode=='load':
   L.start_game(1);before=bytes(S)
  else:
   L.save5_preflight_cancel();foreign=L.save5_preflight_begin(C.byref(S));assert foreign
   L.progression_evolution_cancel();assert L.save5_preflight_status(foreign)==1
   frame();assert L.save5_preflight_status(foreign)==1
   L.save5_preflight_cancel()
  assert S.roster.instances[slot].form_id==49 and count('evolve')==0 and not L.progression_evolution_busy()
  assert not L.save5_preflight_active() and bytes(S)==before
  record('real_update_revokes_frozen_evolution_without_commit',invalidation=mode)


def test_anchor_writer_failure():
 for fail_after in (0,3000,6144):
  setup();enter(46);at(80,272);bank=bytes(SRAM);prior=loaded();L.probe_reset()
  L.save5_test_fail_after(fail_after);frame(1);settle()
  assert get('save_failed')==1 and get('save_failure_notice')==1
  assert count('heal')==1 and S.quests.anchors[4]&1 and S.campaign.spawn==2
  old=loaded();assert old.campaign.sequence==prior.campaign.sequence and not old.quests.anchors[4]&1
  active=next(p for p in (0x200,0x1a00)if int.from_bytes(bank[p+8:p+12],'little')==prior.campaign.sequence)
  assert bytes(SRAM)[active:active+6144]==bank[active:active+6144]
  L.save5_test_fail_after(-1);L.save_game();L.save_frame();settle()
  assert get('save_failed')==0 and count('heal')==1 and loaded().campaign.spawn==2
  record('underwater_anchor_writer_failure_retains_valid_live_receipt_and_retry_is_once',fail_after=fail_after)

def test_return_arch():
 # Synthetic trusted transaction setup of guardian progress, never acquisition
 # evidence. The queued arch and recursive entry/save dispatcher are real.
 guarantees()
 L.underwater_quest_objective.argtypes=[C.POINTER(Save),C.c_uint,C.c_uint]
 L.underwater_quest_claim.argtypes=[C.POINTER(Save),C.c_uint]
 for a,bit in ((50,1),(51,2),(52,4),(53,8)):
  enter(a);assert L.underwater_quest_objective(C.byref(S),40,bit) in (1,2)
 assert L.underwater_quest_claim(C.byref(S),40)==3
 enter(53);at(208,128);before=bytes(S);L.probe_reset();frame(1)
 assert get('game_state')==10 and get('room')==53 and bytes(S)==before and count('begin')==0
 for _ in range(2):frame();assert get('room')==53 and bytes(S)==before
 settle()
 assert get('room')==46 and get('checkpoint_spawn')==1 and S.quests.objectives[45]==1
 assert not get('save_failed') and L.save5_validate(C.byref(S))==1
 for a in (48,49,48,46):enter(a)
 assert S.quests.objectives[45]==3 and not L.underwater_game_event_pending() and not get('save_requested')
 assert loaded().quests.objectives[45]==3
 record('return_arch_commits_intent_before_transition_and_entry_queued_objective_before_writer')


def return_setup():
 setup();enter(46);at(240,288);L.probe_reset()
 return bytes(S),bytes(SRAM),(get('room'),get('px'),get('py'),get('checkpoint_spawn'))

def prepare_direct():
 assert L.magma_game_request_return()==2
 put('game_state',10)
 for n in range(500):
  state=L.magma_game_prepare_return()
  if state!=1:break
 else:raise AssertionError('return preflight did not terminate')
 assert state==2 and L.save5_preflight_active()
 return n+1

def test_return_happy():
 before,bank,pose=return_setup();L.enter_room(38,4)
 assert get('game_state')==10 and L.magma_game_return_pending() and L.save5_preflight_active()
 assert bytes(S)==before and bytes(SRAM)==bank
 assert (get('room'),get('px'),get('py'),get('checkpoint_spawn'))==pose
 for _ in range(2):
  frame(1023,True);assert bytes(S)==before and count('preflight')==0
 assert list(VALID)==[1,1]
 settle(1023,True)
 assert get('room')==38 and get('checkpoint_spawn')==4 and (get('px'),get('py'))==(416,240)
 assert count('preflight')>0 and count('validate')==0
 assert count('enemies')==count('shots')==count('ability')==0
 assert not L.magma_game_return_pending() and not L.save5_preflight_active()
 assert loaded().campaign.room==38 and loaded().campaign.spawn==4
 assert L.magma_game_commit_return()==0
 # The just-used private lease cannot make a later direct wrapper trusted.
 S.roster.instances[0].level=0;bad=bytes(S);pose=(get('room'),get('px'),get('py'),get('checkpoint_spawn'))
 assert L.magma_game_enter(38,4)==0 and bytes(S)==bad and count('validate')==1
 assert (get('room'),get('px'),get('py'),get('checkpoint_spawn'))==pose
 record('bounded_return_exact_once_no_full_validator_and_direct_wrapper_still_checked')

def test_return_stale():
 for when in ('before_validation','ready'):
  for kind in ('roster','party','command','quest','equipment','campaign','pose','checkpoint','room','revision','chapter'):
   before,bank,pose=return_setup()
   if when=='ready':prepare_direct()
   else:assert L.magma_game_request_return()==2;put('game_state',10)
   if kind=='roster':S.roster.instances[0].level=0
   elif kind=='party':S.roster.party[0],S.roster.party[1]=S.roster.party[1],S.roster.party[0]
   elif kind=='command':selected().selected_command^=1
   elif kind=='quest':S.quests.variables[0]^=1
   elif kind=='equipment':S.equipment.bag[0].rank^=1
   elif kind=='campaign':S.campaign.spawn=1
   elif kind=='pose':put('px',get('px')+1)
   elif kind=='checkpoint':put('checkpoint_spawn',1)
   elif kind=='room':put('room',47)
   elif kind=='revision':put('progression_revision',get('progression_revision')+1)
   else:put('chapter_flags',get('chapter_flags')^1)
   changed=bytes(S);newpose=(get('room'),get('px'),get('py'),get('checkpoint_spawn'))
   if when=='before_validation':
    for _ in range(500):
     status=L.magma_game_prepare_return()
     if status!=1:break
    assert status in (2,3)
   put('game_state',1);assert L.magma_game_commit_return()==0
   assert bytes(S)==changed and bytes(SRAM)==bank and not L.magma_game_return_pending() and not L.save5_preflight_active()
   assert (get('room'),get('px'),get('py'),get('checkpoint_spawn'))==newpose
   record('bounded_return_changed_state_never_transitions',phase=when,mutation=kind)

def test_return_cancel_ownership():
 for kind in ('explicit','magma_reset','underwater_reset','selection','new_game','load','replacement_entry'):
  before,bank,pose=return_setup();L.enter_room(38,4)
  for _ in range(5):frame()
  assert L.magma_game_return_pending() and L.save5_preflight_active()
  if kind=='explicit':L.magma_game_cancel_return()
  elif kind=='magma_reset':L.magma_game_reset()
  elif kind=='underwater_reset':L.underwater_game_reset()
  elif kind=='selection':S.roster.selected_party=(S.roster.selected_party+1)%4;L.progression_selection_changed();before=bytes(S)
  elif kind=='new_game':L.start_game(0);before=bytes(S)
  elif kind=='load':L.start_game(1);before=bytes(S)
  else:L.enter_room(48,0)
  assert not L.magma_game_return_pending()
  assert L.magma_game_commit_return()==0
  if kind=='replacement_entry':
   settle();assert get('room')==48 and not get('save_failed')
  else:
   assert not L.save5_preflight_active() and bytes(S)==before and bytes(SRAM)==bank
  record('bounded_return_lifecycle_cancellation',invalidation=kind)
 before,bank,pose=return_setup();assert L.magma_game_request_return()==2
 assert L.save5_begin(C.byref(S))==0 and bytes(SRAM)==bank
 L.save5_preflight_cancel();foreign=L.save5_preflight_begin(C.byref(S));assert foreign
 put('game_state',10);assert L.magma_game_prepare_return()==3
 assert L.save5_preflight_status(foreign)==1 and not L.magma_game_return_pending()
 L.magma_game_cancel_return();assert L.save5_preflight_status(foreign)==1
 put('game_state',1);assert L.magma_game_request_return()==0 and L.save5_preflight_status(foreign)==1
 L.save5_preflight_cancel();assert bytes(S)==before and bytes(SRAM)==bank
 record('bounded_return_writer_exclusion_revoked_token_and_foreign_scratch_preserved')

def test_return_request_gate():
 for kind in ('wrong_room','wrong_mode','campaign_room','campaign_spawn','chapter_mirror','missing_visit'):
  before,bank,pose=return_setup()
  if kind=='wrong_room':put('room',47)
  elif kind=='wrong_mode':put('game_state',3)
  elif kind=='campaign_room':S.campaign.room=47
  elif kind=='campaign_spawn':S.campaign.spawn=1
  elif kind=='chapter_mirror':put('chapter_flags',get('chapter_flags')^1)
  else:S.quests.region_flags[3]&=254
  before=bytes(S);assert L.magma_game_request_return()==0
  assert bytes(S)==before and bytes(SRAM)==bank and not L.save5_preflight_active() and not L.magma_game_return_pending()
  record('bounded_return_bad_source_denied_before_snapshot',mutation=kind)
 before,bank,pose=return_setup();assert L.magma_game_request_return()==2
 for _ in range(5):assert L.magma_game_request_return()==2
 put('game_state',10)
 for _ in range(500):
  result=L.magma_game_prepare_return()
  if result!=1:break
 assert result==2 and bytes(S)==before and bytes(SRAM)==bank
 # A direct malformed wrapper never borrows a pending/ready lease.
 S.roster.instances[0].level=0;changed=bytes(S)
 assert L.magma_game_enter(38,4)==0 and bytes(S)==changed
 put('game_state',1);assert L.magma_game_commit_return()==0
 assert bytes(S)==changed and bytes(SRAM)==bank and not L.save5_preflight_active()
 record('bounded_return_repeated_queue_and_ready_lease_do_not_authorize_direct_wrapper')


def test_return_every_live_byte():
 before,bank,pose=return_setup();raw=(C.c_ubyte*C.sizeof(S)).in_dll(L,'adventure_save')
 for offset in range(len(raw)):
  C.memmove(C.addressof(S),before,len(before));put('game_state',1)
  prepare_direct();raw[offset]^=1;changed=bytes(S)
  put('game_state',1);assert L.magma_game_commit_return()==0,offset
  assert bytes(S)==changed and bytes(SRAM)==bank and not L.save5_preflight_active(),offset
  assert (get('room'),get('px'),get('py'),get('checkpoint_spawn'))==pose,offset
 record('bounded_return_every_live_Save5_byte_is_compared_before_transition',bytes_tested=len(raw))

TESTS=[test_return_every_live_byte,test_return_happy,test_return_stale,test_return_cancel_ownership,test_return_request_gate]
errors=[]
for test in TESTS:
 try:test()
 except Exception as e:
  import traceback
  errors.append({'name':test.__name__,'error':repr(e),'traceback':traceback.format_exc()})
  print(errors[-1]['traceback'],file=sys.stderr)
RESULT['maxima']=maxima;RESULT['failures']=errors;RESULT['passed']=not errors
RESULT['sources_still_frozen']=all(hashlib.sha256((SOURCE_ROOT/p).read_bytes()).hexdigest()==h for p,h in expected.items())
assert RESULT['sources_still_frozen'],'Source changed during diagnostics; rerun against a stable source closure'
path=Path(os.environ.get('PROBE_RESULT_NAME',str(ROOT/'build/underwater-engine-review/return.json')))
path.write_text(json.dumps(RESULT,indent=2)+'\n')
print(json.dumps(RESULT,indent=2))
raise SystemExit(bool(errors))
