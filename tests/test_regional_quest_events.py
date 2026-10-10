#!/usr/bin/env python3
"""Synthetic host contracts for the real engine-private bounded quest queues.
The host-only probes enqueue typed operations; no probe enters the shipping ROM.
This is state/ownership/fault coverage, not earned controller evidence.
"""
from pathlib import Path
import ast,ctypes as C,json,os,subprocess,tempfile,unittest
from test_save5 import Save,compare_state
ROOT=Path(__file__).resolve().parents[1]
TMP=tempfile.TemporaryDirectory(prefix='regional-quest-events-');OUT=Path(TMP.name)

def build(region,synthetic=False):
 out=OUT/(region+('-48' if synthetic else ''));out.mkdir()
 if region=='south':
  tree=ast.parse((ROOT/'tests/test_south_game.py').read_text())
  harness=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HARNESS' for t in n.targets))
  ui=json.loads((ROOT/'assets/southern_region/ui_additions.json').read_text());ui.update(MG_RESERVED='',MG_RESERVEDB='')
 else:
  harness=(ROOT/'tests/magma_game_host.c').read_text();ui=json.loads((ROOT/'assets/magma_region/dialogue.json').read_text())
 (out/f'{region}_game_test_ui.h').write_text('enum{'+','.join('TX_'+k+'='+str(3000+i) for i,k in enumerate(ui))+'};\n')
 harness+='\n#include "'+region+'_game.c"\n'
 harness+=r'''
int probe_queue(unsigned q,unsigned op,unsigned bit){return rq_enqueue(q,op,bit);}
unsigned probe_state(unsigned q){return rq_state(q);}
unsigned probe_bits(unsigned q){return rq_objectives(q);}
unsigned probe_phase(void){return rq.phase;}
unsigned probe_bytes(void){return sizeof rq;}
int probe_result(void){return rq.result;}
int probe_patch(void){int r=rq_commit_patch();rq_cancel();return r;}
int probe_fullgear(void){unsigned i;for(i=1;i<48;i++){memset(&adventure_save.equipment.bag[i],0,sizeof(EquipmentRecord));adventure_save.equipment.bag[i].item_id=99+i;adventure_save.equipment.bag[i].quantity=1;adventure_save.equipment.seen[(99+i)>>3]|=1u<<((99+i)&7);}adventure_save.equipment.equipped[0]=0;for(i=1;i<5;i++)adventure_save.equipment.equipped[i]=255;return save5_validate(&adventure_save);}
'''
 (out/'host.c').write_text(harness)
 sources=[ROOT/'src'/f'{s}.c' for s in [region+'_art','magma_quests','southern_quests','northern_quests','save5','save4','equipment','equipment_data','creatures','creature_data']]
 if synthetic:
  data=(ROOT/'src/equipment_data.c').read_text();marker='const EquipmentDefinition equipment_definitions[EQUIPMENT_DEFINITION_CAPACITY] = {\n'
  rows=''.join(f'    [{i}] = {{{i}, 1, 0, 0, 255, {{0, 0}}, {{0, 0, 0, 0, 0, 0, 0, 0}}}},\n' for i in range(100,147))
  path=out/'equipment_data.c';path.write_text(data.replace(marker,marker+rows));sources[sources.index(ROOT/'src/equipment_data.c')]=path
 cmd=['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC','-D'+region.upper()+'_GAME_HOST_TEST','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-I'+str(ROOT/'src'),'-I'+str(out),str(out/'host.c'),*map(str,sources)]
 if region=='magma':cmd+=['-Wl,--wrap=magma_anchor']
 if os.environ.get('QUEST_SANITIZE'):cmd+=['-fsanitize=undefined','-fno-sanitize-recover=all']
 subprocess.run(cmd+['-o',str(out/'test.so')],check=True)
 lib=C.CDLL(str(out/'test.so'));lib.sram=(C.c_ubyte*32768).in_dll(lib,'save5_test_sram');lib.region=region;lib.first=22 if region=='south' else 30
 lib.prefix='southern' if region=='south' else 'magma'
 lib.fixture=ROOT/('tests/fixtures/v5-revision3/northern-all21-town.sav' if region=='south' else 'tests/fixtures/v5-revision4/southern-minimal8-town.sav')
 lib.seal=getattr(lib,region+'_game_quest_seal');lib.pending=getattr(lib,region+'_game_quest_pending');lib.prepare=getattr(lib,region+'_game_quest_prepare');lib.cancel=getattr(lib,region+'_game_quest_cancel');lib.finish=getattr(lib,region+'_game_quest_commit')
 lib.save5_store.argtypes=[C.POINTER(Save)];lib.save5_load.argtypes=[C.POINTER(Save)];lib.save5_validate.argtypes=[C.POINTER(Save)]
 for name in ['offer','objective','claim']:
  getattr(lib,lib.prefix+'_quest_'+name).argtypes=[C.POINTER(Save),C.c_uint]+([C.c_uint] if name=='objective' else [])
 return lib

class RegionalQuestEvents(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.libs=[build('south'),build('magma')];cls.fullgear=[build('south',True),build('magma',True)]
 def live(self,l):return Save.in_dll(l,'adventure_save')
 def fresh(self,l):
  l.cancel();l.sram[:]=l.fixture.read_bytes();self.assertEqual(l.fresh(),1);self.assertEqual(l.entry(30 if l.region=='south' else 38,0),1)
  if l.region=='magma':self.assertEqual(l.host_settle_save(),1)
  C.c_int.in_dll(l,'game_state').value=1
  return self.live(l)
 def ready(self,l,q=None):
  s=self.fresh(l);q=l.first if q is None else q
  self.assertEqual(getattr(l,l.prefix+'_quest_offer')(C.byref(s),q),1)
  mask=getattr(l,l.prefix+'_quest_mask')(q)
  for b in [1,2,4,8]:
   if mask&b:self.assertIn(getattr(l,l.prefix+'_quest_objective')(C.byref(s),q,b),(1,2))
  self.assertEqual(l.save5_validate(C.byref(s)),1);return s
 def advance(self,l):
  C.c_int.in_dll(l,'game_state').value=10
  for i in range(150):
   status=l.prepare()
   if status!=1:return status,i+1
  self.fail('unbounded preparation')
 def finish_patch(self,l):
  self.assertEqual(l.seal(),1);self.assertEqual(self.advance(l)[0],2);result=l.probe_result();C.c_int.in_dll(l,'game_state').value=1;self.assertEqual(l.probe_patch(),1);return result
 def test_projection_chain_and_exact_synchronous_parity(self):
  for l in self.libs:
   for q in [l.first,l.first+1,l.first+3,l.first+4,l.first+5,l.first+6,l.first+7]:
    s=self.fresh(l)
    # Magma Q33 requires Q30 and Q37 requires caldera; unavailable parity is also checked.
    oracle=Save.from_buffer_copy(bytes(s));before=bytes(s);seq=[(1,0),(2,1),(2,2),(3,0)]
    results=[]
    for op,bit in seq:
     f=getattr(l,l.prefix+'_quest_'+{1:'offer',2:'objective',3:'claim'}[op]);args=[C.byref(oracle),q]+([bit] if op==2 else [])
     results.append(f(*args));l.probe_queue(q,op,bit)
    self.assertEqual(bytes(s),before);self.assertEqual(l.probe_state(q),min(l.save5_quest_state(C.byref(oracle.quests),q),2));self.assertEqual(l.probe_bits(q),oracle.quests.objectives[q])
    self.assertEqual(self.finish_patch(l),results[-1]);self.assertEqual(bytes(s),bytes(oracle),(l.region,q));self.assertEqual(l.save5_validate(C.byref(s)),1);self.assertFalse(l.pending())
 def test_southern_same_action_discovery_reads_projected_objectives(self):
  l=self.libs[0];s=self.fresh(l);self.assertEqual(l.southern_visit(C.byref(s),32),1);oracle=Save.from_buffer_copy(bytes(s));before=bytes(s)
  l.southern_quest_offer(C.byref(oracle),29);l.southern_quest_objective(C.byref(oracle),29,1);l.southern_quest_objective(C.byref(oracle),29,2);self.assertEqual(l.southern_discover(C.byref(oracle),0),1)
  for op,b in [(1,0),(2,1),(2,2),(4,1)]:l.probe_queue(29,op,b)
  self.assertEqual(bytes(s),before);self.finish_patch(l);self.assertEqual(bytes(s),bytes(oracle));self.assertEqual(l.save5_validate(C.byref(s)),1)
 def test_no_mutation_until_commit_and_exact_once(self):
  for l in self.libs:
   s=self.ready(l);before=bytes(s);sram=bytes(l.sram);self.assertLessEqual(l.probe_bytes(),160)
   l.probe_queue(l.first,3,0);self.assertEqual(l.seal(),1)
   C.c_int.in_dll(l,'game_state').value=10
   for _ in range(150):
    status=l.prepare();self.assertEqual(bytes(s),before);self.assertEqual(bytes(l.sram),sram)
    if status!=1:break
   self.assertEqual(status,2);C.c_int.in_dll(l,'game_state').value=1;self.assertEqual(l.probe_patch(),1);after=bytes(s);self.assertEqual(l.probe_patch(),0);self.assertEqual(bytes(s),after)
 def test_cancel_all_phases_retry_and_writer_ownership(self):
  for l in self.libs:
   for count in [0,1,8,20,35,55]:
    s=self.ready(l);before=bytes(s);l.probe_queue(l.first,3,0);self.assertEqual(l.seal(),1);C.c_int.in_dll(l,'game_state').value=10
    for _ in range(count):
     if l.prepare()!=1:break
    l.cancel();self.assertEqual(bytes(s),before);self.assertFalse(l.pending());self.assertEqual(l.probe_patch(),0)
    C.c_int.in_dll(l,'game_state').value=1;l.probe_queue(l.first,3,0);self.assertEqual(self.finish_patch(l),3);self.assertEqual(l.save5_validate(C.byref(s)),1)
 def test_source_and_live_changes_rejected(self):
  for l in self.libs:
   for mutation in ['room','px','py','face','checkpoint_spawn','summoned','chapter_flags','progression_revision','party','identity','save','death','reset','reload']:
    s=self.ready(l);l.probe_queue(l.first,3,0);self.assertEqual(l.seal(),1);self.assertEqual(self.advance(l)[0],2)
    C.c_int.in_dll(l,'game_state').value=1
    if mutation=='party':s.roster.selected_party=(s.roster.selected_party+1)%4
    elif mutation=='identity':s.roster.instances[0].instance_id+=700
    elif mutation=='save':s.economy.gold+=1
    elif mutation=='death':C.c_int.in_dll(l,'game_state').value=4
    elif mutation=='reset':getattr(l,l.region+'_game_reset')()
    elif mutation=='reload':out=Save();self.assertEqual(l.save5_load(C.byref(out)),1)
    else:C.c_uint.in_dll(l,mutation).value+=1
    before=bytes(s);self.assertEqual(l.probe_patch(),0,(l.region,mutation));self.assertEqual(bytes(s),before)
 def test_invalid_noop_public_contract_and_async_failure(self):
  for l in self.libs:
   for malformed in ['empty','roster','gear','quest','economy']:
    s=self.ready(l);q=l.first
    if malformed=='empty':s.roster.instances[159].level=1
    elif malformed=='roster':s.roster.instances[0].level=0
    elif malformed=='gear':s.equipment.reserved[0]=1
    elif malformed=='quest':s.quests.objectives[63]=65535
    else:s.economy.reserved[0]=1
    before=bytes(s);self.assertEqual(getattr(l,l.prefix+'_quest_offer')(C.byref(s),q),-1);self.assertEqual(bytes(s),before)
    l.probe_queue(q,1,0);self.assertEqual(l.seal(),1);self.assertEqual(self.advance(l)[0],3);self.assertEqual(bytes(s),before);self.assertFalse(l.pending())
 def test_full_reserved_id_exhaustion_and_gear_atomicity(self):
  for l in self.libs+self.fullgear:
   modes=['gear'] if l in self.fullgear else ['full','reserved','id','full_id']
   for mode in modes:
    s=self.ready(l)
    if mode=='gear':self.assertEqual(l.probe_fullgear(),1)
    elif mode in ['full','full_id']:
     l.creatures_grant.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_uint]
     while l.creatures_grant(C.byref(s.roster),1,30,20,0,0)<160:pass
    elif mode=='reserved':
     l.creatures_grant.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_uint]
     if l.region=='south':self.assertLess(l.creatures_grant(C.byref(s.roster),79,30,20,0,0),160)
     l.creatures_grant_admitted.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p]
     while l.creatures_grant_admitted(C.byref(s.roster),1,30,20,0,0,None) in [0,1]:pass
    if mode in ['id','full_id']:s.roster.next_instance_id=0xffffffff
    self.assertEqual(l.save5_validate(C.byref(s)),1,(l.region,mode))
    oracle=Save.from_buffer_copy(bytes(s));expected=getattr(l,l.prefix+'_quest_claim')(C.byref(oracle),l.first)
    if not(l.region=='magma' and mode=='reserved'):self.assertNotEqual(expected,3,(l.region,mode))
    before=bytes(s);l.probe_queue(l.first,3,0);self.assertEqual(self.finish_patch(l),expected,(l.region,mode));self.assertEqual(bytes(s),bytes(oracle))
    if expected!=3:self.assertEqual(bytes(s),before)
 def test_queue_misuse_and_preseal_authority_changes_fail_closed(self):
  for l in self.libs:
   for mode in ['overflow','another_quest','after_claim','pose','form','command','party']:
    s=self.ready(l);before=bytes(s);l.probe_queue(l.first,1,0)
    if mode=='overflow':
     for _ in range(9):l.probe_queue(l.first,1,0)
    elif mode=='another_quest':l.probe_queue(l.first+1,1,0)
    elif mode=='after_claim':l.probe_queue(l.first,3,0);l.probe_queue(l.first,1,0)
    elif mode=='pose':C.c_int.in_dll(l,'px').value+=1
    elif mode=='party':s.roster.selected_party=(s.roster.selected_party+1)%4;before=bytes(s)
    else:
     member=s.roster.instances[s.roster.party[s.roster.selected_party]]
     if mode=='form':member.form_id+=1
     else:member.selected_command^=1
     before=bytes(s)
    self.assertEqual(l.seal(),0,(l.region,mode));self.assertEqual(bytes(s),before);self.assertFalse(l.pending())
 def test_wide_and_invalid_operation_parameters_never_replay_as_bytes(self):
  for l in self.libs:
   for op,bit in [(0,0),(257,0),(258,1),(2,257),(2,256),(2,0),(2,3),(2,16),(1,256),(3,256),(4,257)]:
    for existing in [False,True]:
     s=self.fresh(l);before=bytes(s)
     if existing:l.probe_queue(l.first,1,0)
     self.assertEqual(l.probe_queue(l.first,op,bit),-1,(l.region,op,bit))
     self.assertEqual(l.seal(),0);self.assertFalse(l.pending());self.assertEqual(bytes(s),before)
 def test_background_writer_preemption_and_foreign_owner_preservation(self):
  for l in self.libs:
   for prior_steps in [0,12,28]:
    s=self.ready(l);before=bytes(s);self.assertEqual(l.save5_store(C.byref(s)),1);self.assertEqual(l.save5_begin(C.byref(s)),1);l.save5_set_preemptible(1)
    for _ in range(prior_steps):
     if l.save5_status()!=1:break
     l.save5_step(1024)
    self.assertEqual(l.save5_status(),1,('expected active writer',l.region,prior_steps))
    l.probe_queue(l.first,3,0);self.assertEqual(l.seal(),1);self.assertEqual(l.save5_take_preempted(),1);self.assertEqual(l.save5_status(),0);self.assertEqual(bytes(s),before)
    self.assertEqual(self.advance(l)[0],2);C.c_int.in_dll(l,'game_state').value=1;self.assertEqual(l.probe_patch(),1);self.assertEqual(l.save5_validate(C.byref(s)),1)
    self.assertEqual(l.save5_store(C.byref(s)),1);loaded=Save();self.assertEqual(l.save5_load(C.byref(loaded)),1);self.assertEqual(compare_state(loaded),compare_state(s))
   s=self.ready(l);before=bytes(s);self.assertEqual(l.save5_begin(C.byref(s)),1);l.save5_set_preemptible(0);l.probe_queue(l.first,3,0);self.assertEqual(l.seal(),0);self.assertEqual(l.save5_status(),1);self.assertEqual(bytes(s),before)
   l.save5_test_reset_writer();token=l.save5_preflight_begin(C.byref(s));self.assertNotEqual(token,0);l.probe_queue(l.first,3,0);self.assertEqual(l.seal(),0);self.assertEqual(l.save5_preflight_status(token),1);self.assertEqual(bytes(s),before);l.save5_preflight_cancel()
 def test_interrupted_sram_preserves_old_or_complete_reward(self):
  for l in self.libs:
   s=self.ready(l);self.assertEqual(l.save5_store(C.byref(s)),1);old=Save();self.assertEqual(l.save5_load(C.byref(old)),1);baseline=bytes(l.sram)
   l.probe_queue(l.first,3,0);self.assertEqual(self.finish_patch(l),3);new=Save.from_buffer_copy(bytes(s))
   for cutoff in [0,1,20,256,1024,4096,6144,6148]:
    l.sram[:]=baseline;l.save5_test_reset_writer();l.save5_test_fail_after(cutoff);l.save5_store(C.byref(new));l.save5_test_fail_after(-1);loaded=Save();self.assertEqual(l.save5_load(C.byref(loaded)),1);self.assertIn(compare_state(loaded),[compare_state(old),compare_state(new)],(l.region,cutoff))

if __name__=='__main__':unittest.main(verbosity=2)
