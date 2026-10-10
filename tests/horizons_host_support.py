"""Synthetic host transactions beginning at independently earned H SRAM."""
import ctypes as C,hashlib,subprocess,re
from pathlib import Path
from test_save5 import ROOT,Save,Instance,Roster,A,B,SIZE,BUSY,DONE,FAILED,compare_state
FIXTURE=ROOT/'tests/fixtures/v5-revision7/return-h-earned104-52.sav'
FIXTURE_SHA='bdbe06929d9e9e047c487a49e14a961e8e15ed11dff7086334a5cf6818ba1fce'
class Request(C.Structure):
 _fields_=[(n,C.c_uint) for n in ('operation','room','quest','bit','source','slot','family','key','form','command','instance_id')]
BASES=(105,107,109,111,113,114,115,116,117,118,119,120)
ROOMS=(62,63,66,68,63,64,65,67,69,66,62,68)
TRIAL_ROOMS=(64,67,66,68)
_generation=0
def generation():
 global _generation
 _generation+=1;return _generation

def runtime_hashes():
 found={}
 def visit(path):
  key=str(path.relative_to(ROOT))
  if key in found:return
  raw=path.read_bytes();found[key]=hashlib.sha256(raw).hexdigest()
  for inc in re.findall(rb'^\s*#include\s+"([^\"]+)"',raw,re.M):visit(path.parent/inc.decode())
 for name in ('save4','save5','creatures','creature_data','equipment','equipment_data','horizons_quests'):visit(ROOT/'src'/f'{name}.c')
 return found

def build(folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);out=folder/'horizons.so';hashes=runtime_hashes()
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-shared','-fPIC',*[str(ROOT/'src'/f'{n}.c') for n in ('save4','save5','creatures','creature_data','equipment','equipment_data','horizons_quests')],'-o',str(out)],check=True)
 assert runtime_hashes()==hashes,'source changed while compiling'
 l=C.CDLL(str(out));l.source_hashes=hashes;l.sram=(C.c_ubyte*32768).in_dll(l,'save5_test_sram')
 for n in ('save5_load','save5_store','save5_validate','save5_begin','save5_preflight_begin'):getattr(l,n).argtypes=[C.POINTER(Save)]
 l.save5_validate_revision.argtypes=[C.POINTER(Save),C.c_uint]
 l.horizons_job_begin.argtypes=[C.POINTER(Save),C.POINTER(Request),C.c_uint,C.c_uint]
 l.horizons_job_step.argtypes=[C.c_uint,C.c_uint,C.c_uint,C.c_uint]
 l.creatures_grant.argtypes=[C.POINTER(Roster)]+[C.c_uint]*5
 l.creatures_evolve_to.argtypes=[C.POINTER(Roster),C.c_uint,C.c_uint,C.c_uint,C.c_int,C.c_int]
 l.creatures_equip.argtypes=[C.POINTER(Instance),C.c_uint,C.c_uint]
 l.horizons_context.argtypes=[C.POINTER(Save)]
 return l

def source(l):
 data=FIXTURE.read_bytes();assert hashlib.sha256(data).hexdigest()==FIXTURE_SHA
 l.horizons_job_cancel();l.save5_test_reset_writer();l.save5_test_fail_after(-1);l.save5_test_corrupt_write(-1,0);l.sram[:]=data
 s=Save();assert l.save5_load(C.byref(s))==1;assert l.save5_validate(C.byref(s))==1;return s

def runjob(l,s,r,expected=None,scene=None,attempt=1,budget=1024):
 if scene is None:scene=generation()
 before=bytes(s);sram=bytes(l.sram);token=l.horizons_job_begin(C.byref(s),C.byref(r),scene,attempt);assert token,('begin',r.operation,r.source,r.quest,r.room)
 for n in range(2000):
  phase=l.horizons_job_phase(token);status=l.horizons_job_step(token,budget,scene,attempt)
  if phase!=6:assert bytes(s)==before,('early mutation',phase)
  assert bytes(l.sram)==sram,'job wrote SRAM'
  if status!=BUSY:break
 else:raise AssertionError('unbounded transaction')
 assert status==DONE,('failed',r.operation,r.source,r.quest,phase)
 result=l.horizons_job_result(token)
 if expected is not None:assert result==expected,(r.operation,r.source,r.quest,r.bit,result,expected)
 after=bytes(s);assert l.horizons_job_step(token,1024,scene,attempt)==DONE;assert bytes(s)==after
 assert l.save5_validate(C.byref(s)),('post mutation invalid',r.operation,r.source,r.quest,r.room,result)
 return result

def move(l,s,room):
 if room>=62:runjob(l,s,Request(operation=1,room=room),0 if s.quests.region_flags[6]&(1<<(room-62)) else 1)
 s.campaign.room=room;s.campaign.spawn=0
 assert l.save5_validate(C.byref(s)),('host move invalid',room)

def objective(l,s,q,bit,room):
 move(l,s,room);return runjob(l,s,Request(operation=5,room=room,quest=q,bit=bit))
def claim(l,s,q,room):
 move(l,s,room);return runjob(l,s,Request(operation=6,room=room,quest=q),3)
def invite(l,s,index):
 move(l,s,ROOMS[index]);return runjob(l,s,Request(operation=7,source=index+1,family=index+41,room=ROOMS[index]),3)
def select(l,s,form,command=None):
 slot=next(i for i,c in enumerate(s.roster.instances) if c.form_id==form);c=s.roster.instances[slot]
 s.roster.party[:]=[slot,255,255,255];s.roster.selected_party=0;command=command or form+1
 i=next((i for i,v in enumerate(c.equipped) if v==command),None)
 if i is None:assert l.creatures_equip(C.byref(c),0,command);i=0
 c.selected_command=i;return slot,c.instance_id

def main(l,reverse=False):
 s=source(l);objective(l,s,54,1,60);objective(l,s,54,2,62);invite(l,s,0);claim(l,s,54,62)
 for q in ((56,55) if reverse else (55,56)):
  if q==55:
   objective(l,s,55,1,63);objective(l,s,55,2,63);objective(l,s,55,4,64);invite(l,s,1);claim(l,s,55,63)
  else:
   # Five-Cup's inbound route requires already visited Loadsong.
   move(l,s,63);objective(l,s,56,1,65);objective(l,s,56,2,65);objective(l,s,56,4,66);invite(l,s,2);claim(l,s,56,65)
 objective(l,s,57,1,67);objective(l,s,57,2,67);objective(l,s,57,4,68);invite(l,s,3);claim(l,s,57,62)
 return s

def complete(l):
 s=main(l)
 for i in range(4,12):invite(l,s,i)
 for q,steps,room in ((58,[(1,64),(2,69),(4,65)],65),(59,[(1,63),(2,66),(4,69),(8,60)],60)):
  for bit,area in steps:objective(l,s,q,bit,area)
  claim(l,s,q,room)
 for i in range(4):
  move(l,s,TRIAL_ROOMS[i]);slot,id=select(l,s,BASES[i]);runjob(l,s,Request(operation=10,room=TRIAL_ROOMS[i],family=41+i,key=1,slot=slot,instance_id=id,form=BASES[i],command=BASES[i]+1),3)
  assert l.creatures_evolve_to(C.byref(s.roster),slot,BASES[i]+1,l.horizons_context(C.byref(s)),1,1)==0
  assert l.save5_validate(C.byref(s))
 return s
