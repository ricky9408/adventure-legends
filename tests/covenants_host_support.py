"""Host-only synthetic final-chapter actions rooted in genuine earned C SRAM."""
import ctypes as C,hashlib,json,subprocess
from test_return_history_differential import source_closure
from pathlib import Path
from test_save5 import ROOT,Save,Instance,Roster,A,B,SIZE,BUSY,DONE,FAILED,compare_state
FIXTURE=ROOT/'tests/fixtures/v5-revision8/horizons-all120-64-cold.sav'
FIXTURE_SHA='d0786e3db82cd23c5f9ba948900f3d73340de8df004738d26ad1c2956055994e'
class Request(C.Structure):
 _fields_=[(n,C.c_uint) for n in ('operation','room','quest','bit','source')]
_generation=0
def generation():
 global _generation
 _generation+=1;return _generation

SOURCES=('save4','save5','creatures','creature_data','equipment','equipment_data','covenants_quests')
def runtime_hashes():
 return {p:hashlib.sha256(b).hexdigest() for p,b in source_closure(ROOT,SOURCES).items()}
def build(folder,sanitize=False):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);out=folder/'covenants.so';hashes=runtime_hashes()
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-shared','-fPIC',*[str(ROOT/'src'/f'{n}.c') for n in SOURCES],'-o',str(out)],check=True)
 assert runtime_hashes()==hashes,'source changed during compilation'
 l=C.CDLL(str(out));l.source_hashes=hashes;l.sram=(C.c_ubyte*32768).in_dll(l,'save5_test_sram')
 for n in ('save5_load','save5_store','save5_validate','save5_begin','save5_preflight_begin'):getattr(l,n).argtypes=[C.POINTER(Save)]
 l.save5_validate_revision.argtypes=[C.POINTER(Save),C.c_uint]
 l.covenants_job_begin.argtypes=[C.POINTER(Save),C.POINTER(Request),C.c_uint,C.c_uint]
 l.covenants_job_step.argtypes=[C.c_uint,C.c_uint,C.c_uint,C.c_uint]
 l.creatures_grant.argtypes=[C.POINTER(Roster)]+[C.c_uint]*5
 return l

def source(l):
 raw=FIXTURE.read_bytes();assert hashlib.sha256(raw).hexdigest()==FIXTURE_SHA
 l.covenants_job_cancel();l.save5_test_reset_writer();l.save5_test_fail_after(-1);l.save5_test_corrupt_write(-1,0);l.sram[:]=raw
 s=Save();assert l.save5_load(C.byref(s))==1;assert l.save5_validate(C.byref(s))==1;return s

def runjob(l,s,r,expected=None,scene=None,attempt=1,budget=1024):
 if scene is None:scene=generation()
 before=bytes(s);sram=bytes(l.sram);token=l.covenants_job_begin(C.byref(s),C.byref(r),scene,attempt);assert token,('begin',r.operation,r.source,r.quest,r.room)
 for n in range(2000):
  phase=l.covenants_job_phase(token);status=l.covenants_job_step(token,budget,scene,attempt)
  if phase!=5:assert bytes(s)==before,('early mutation',phase)
  assert bytes(l.sram)==sram,'job wrote SRAM'
  if status!=BUSY:break
 else:raise AssertionError('unbounded transaction')
 assert status==DONE,('failed',r.operation,r.source,r.quest,phase)
 result=l.covenants_job_result(token)
 if expected is not None:assert result==expected,(r.operation,r.source,r.quest,r.bit,result,expected)
 after=bytes(s);assert l.covenants_job_step(token,1024,scene,attempt)==DONE;assert bytes(s)==after
 assert l.save5_validate(C.byref(s)),('post mutation invalid',r.operation,r.source,r.quest,r.room,result)
 return result

def move(l,s,room):
 if room>=70:runjob(l,s,Request(operation=1,room=room),0 if s.quests.region_flags[7]&(1<<(room-70)) else 1)
 s.campaign.room=room;s.campaign.spawn=0
 assert l.save5_validate(C.byref(s)),('host move invalid',room)
def offer(l,s,q,room):
 move(l,s,room);runjob(l,s,Request(operation=3,room=room,quest=q),1)
def objective(l,s,q,bit,room):
 move(l,s,room);return runjob(l,s,Request(operation=4,room=room,quest=q,bit=bit))
def claim(l,s,q,room):
 move(l,s,room);return runjob(l,s,Request(operation=5,room=room,quest=q),3)
def fulfill(l,s,source):
 move(l,s,69+source);return runjob(l,s,Request(operation=6,room=69+source,source=source))
def invite(l,s,source):
 move(l,s,69+source);return runjob(l,s,Request(operation=7,room=69+source,source=source),3)
def enter(l):
 s=source(l);offer(l,s,60,0);objective(l,s,60,1,0);objective(l,s,60,2,62);objective(l,s,60,4,70);claim(l,s,60,70);offer(l,s,61,70);return s

def story(l,recruit=False,reverse=False):
 s=enter(l)
 # Establish reachable inbound visits, then covenants may complete in any order.
 for room in range(71,74):move(l,s,room)
 for i in (range(4,0,-1) if reverse else range(1,5)):
  fulfill(l,s,i)
  if recruit:invite(l,s,i)
 claim(l,s,61,70);offer(l,s,62,74)
 for room in range(75,78):move(l,s,room)
 for i in (range(8,4,-1) if reverse else range(5,9)):
  fulfill(l,s,i)
  if recruit:invite(l,s,i)
 claim(l,s,62,74);offer(l,s,63,70);objective(l,s,63,1,70);objective(l,s,63,2,62);objective(l,s,63,4,0);claim(l,s,63,0)
 return s
