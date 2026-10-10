"""Source-only host fixture helpers; no native acquisition evidence."""
import ctypes as C,hashlib,os,shlex,subprocess,json,re
from pathlib import Path
from test_save5 import ROOT,Save,Instance,Roster,A,B,SIZE,BUSY,DONE,FAILED,compare_state
FIXTURE=ROOT/'tests/fixtures/v5-revision6/underwater-all89-town.sav'
TRIALS=[{'family': 1, 'key': 2, 'from_form': 2, 'to_form': 3, 'area': 54, 'allowed_predecessor_commands': [1, 5], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 1024, 'prerequisite_mask': 1}, {'family': 2, 'key': 2, 'from_form': 5, 'to_form': 6, 'area': 54, 'allowed_predecessor_commands': [2, 6], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 1024, 'prerequisite_mask': 2}, {'family': 3, 'key': 2, 'from_form': 8, 'to_form': 9, 'area': 57, 'allowed_predecessor_commands': [3, 7], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 1024, 'prerequisite_mask': 4}, {'family': 4, 'key': 2, 'from_form': 11, 'to_form': 12, 'area': 61, 'allowed_predecessor_commands': [4, 8], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 1024, 'prerequisite_mask': 8}, {'family': 5, 'key': 2, 'from_form': 14, 'to_form': 15, 'area': 56, 'allowed_predecessor_commands': [9, 10], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 1024, 'prerequisite_mask': 16}, {'family': 6, 'key': 1, 'from_form': 16, 'to_form': 17, 'area': 55, 'allowed_predecessor_commands': [11], 'level_floor': 28, 'bond_floor': 45, 'wire_mask': 1024, 'prerequisite_mask': 0}, {'family': 6, 'key': 2, 'from_form': 17, 'to_form': 18, 'area': 60, 'allowed_predecessor_commands': [11, 96], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 2048, 'prerequisite_mask': 1024}, {'family': 7, 'key': 2, 'from_form': 20, 'to_form': 21, 'area': 57, 'allowed_predecessor_commands': [13, 14], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 1024, 'prerequisite_mask': 32}, {'family': 8, 'key': 2, 'from_form': 23, 'to_form': 24, 'area': 57, 'allowed_predecessor_commands': [15, 16], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 1024, 'prerequisite_mask': 64}, {'family': 9, 'key': 2, 'from_form': 26, 'to_form': 27, 'area': 58, 'allowed_predecessor_commands': [23, 24], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 1024, 'prerequisite_mask': 1}, {'family': 10, 'key': 2, 'from_form': 29, 'to_form': 30, 'area': 58, 'allowed_predecessor_commands': [25, 26], 'level_floor': 32, 'bond_floor': 60, 'wire_mask': 1024, 'prerequisite_mask': 1}, {'family': 39, 'key': 1, 'from_form': 101, 'to_form': 102, 'area': 56, 'allowed_predecessor_commands': [102], 'level_floor': 28, 'bond_floor': 45, 'wire_mask': 1024, 'prerequisite_mask': 0}, {'family': 40, 'key': 1, 'from_form': 103, 'to_form': 104, 'area': 59, 'allowed_predecessor_commands': [104], 'level_floor': 28, 'bond_floor': 45, 'wire_mask': 1024, 'prerequisite_mask': 0}]
FIXTURE_SHA='41cf371618208e0097fe6ee10393e3185b4bffb2af9dad9e5f81e2663d6673a0'
class Request(C.Structure):
 _fields_=[(n,C.c_uint) for n in ('operation','room','quest','bit','source','slot','family','key','form','command','instance_id')]
SOURCES=('save4','save5','creatures','creature_data','equipment','equipment_data','return_quests','progression_events')
def runtime_hashes():
 found={}
 def visit(path):
  path=Path(path);key=str(path.relative_to(ROOT))
  if key in found:return
  data=path.read_bytes();found[key]=hashlib.sha256(data).hexdigest()
  for name in re.findall(rb'#include\s+"([^"\n]+)"',data):visit(path.parent/name.decode())
 for name in SOURCES:visit(ROOT/'src'/f'{name}.c')
 return found

def build(folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);out=folder/'return.so'
 sources=SOURCES;hashes=runtime_hashes()
 subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+['-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-fPIC','-shared','-Isrc',*[str(ROOT/'src'/f'{x}.c') for x in sources],'-o',str(out)],cwd=ROOT,check=True)
 assert runtime_hashes()==hashes,'sources changed during compile'
 lib=C.CDLL(str(out));lib.source_hashes=hashes;lib.sram=(C.c_ubyte*32768).in_dll(lib,'save5_test_sram')
 for n in ('save5_load','save5_validate','save5_store','save5_begin','save5_preflight_begin'):getattr(lib,n).argtypes=[C.POINTER(Save)]
 lib.save5_validate_revision.argtypes=[C.POINTER(Save),C.c_uint]
 lib.save5_preflight_matches.argtypes=[C.c_uint,C.POINTER(Save)]
 lib.return_job_begin.argtypes=[C.POINTER(Save),C.POINTER(Request),C.c_uint,C.c_uint]
 lib.return_job_step.argtypes=[C.c_uint,C.c_uint,C.c_uint,C.c_uint]
 lib.creatures_grant.argtypes=[C.POINTER(Roster),C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_uint]
 lib.creatures_evolve_to.argtypes=[C.POINTER(Roster),C.c_uint,C.c_uint,C.c_uint,C.c_int,C.c_int]
 lib.creatures_equip.argtypes=[C.POINTER(Instance),C.c_uint,C.c_uint]
 lib.return_context.argtypes=[C.POINTER(Save)]
 return lib
def source(lib):
 data=FIXTURE.read_bytes();assert hashlib.sha256(data).hexdigest()==FIXTURE_SHA
 lib.return_job_cancel();lib.save5_test_reset_writer();lib.save5_test_fail_after(-1);lib.sram[:]=data
 s=Save();assert lib.save5_load(C.byref(s))==1;assert lib.save5_validate(C.byref(s))==1
 return s
_generation=0
def generation():
 global _generation
 _generation+=1;return _generation

def runjob(lib,s,request,expected=None,scene=None,attempt=1):
 if scene is None:scene=generation()
 before=bytes(s);sram=bytes(lib.sram);token=lib.return_job_begin(C.byref(s),C.byref(request),scene,attempt);assert token,('begin',request.operation)
 for n in range(300):
  phase=lib.return_job_phase(token);status=lib.return_job_step(token,1024,scene,attempt)
  if phase!=6:assert bytes(s)==before,('early mutation',phase)
  assert bytes(lib.sram)==sram,'job writes SRAM'
  if status!=BUSY:break
 else:raise AssertionError('job unbounded')
 assert status==DONE,('failed',request.operation,phase)
 result=lib.return_job_result(token)
 if expected is not None:assert result==expected,(request.operation,result,expected)
 after=bytes(s);assert lib.return_job_step(token,1024,scene,attempt)==DONE;assert bytes(s)==after
 assert lib.save5_validate(C.byref(s)),('post mutation invalid',request.operation,request.quest,request.room,result)
 return result

def initial_chapter(lib):
 s=source(lib);changes=[]
 def act(name,r,expected):
  old=Save.from_buffer_copy(bytes(s));runjob(lib,s,r,expected);changes.append((name,old,Save.from_buffer_copy(bytes(s))))
 def quest(q,mask,source=0):
  for bit in (1,2,4,8):
   if mask&bit:act(f'objective{q}:{bit}',Request(operation=5,quest=q,bit=bit),2 if bit==1<<(mask.bit_length()-1) else 1)
  act(f'claim{q}',Request(operation=6,quest=q,source=source),3)
 quest(46,3);act('arrival54',Request(operation=1,room=54),1);act('visit55',Request(operation=1,room=55),1)
 quest(47,7,1);act('visit57',Request(operation=1,room=57),1);act('visit58',Request(operation=1,room=58),1)
 quest(49,7,2);act('visit59',Request(operation=1,room=59),1);act('visit56',Request(operation=1,room=56),1)
 quest(48,7);quest(50,7);act('visit60',Request(operation=1,room=60),1);act('visit61',Request(operation=1,room=61),1)
 quest(51,15);quest(52,7);quest(53,15)
 for room in (54,55):act(f'anchor{room}',Request(operation=2,room=room),1)
 return s,changes

def select(lib,s,form,command):
 slot=next(i for i,c in enumerate(s.roster.instances) if c.form_id==form)
 c=s.roster.instances[slot];s.roster.party[:]=[slot,255,255,255];s.roster.selected_party=0
 index=next((i for i,x in enumerate(c.equipped) if x==command),None)
 if index is None:assert lib.creatures_equip(C.byref(c),0,command);index=0
 c.selected_command=index
 return slot,c.instance_id

def trials(lib,s):
 changes=[];rows=TRIALS
 for t in rows:
  slot,id=select(lib,s,t['from_form'],t['allowed_predecessor_commands'][0]);old=Save.from_buffer_copy(bytes(s))
  r=Request(operation=9,room=t['area'],slot=slot,instance_id=id,family=t['family'],key=t['key'],form=t['from_form'],command=t['allowed_predecessor_commands'][0])
  runjob(lib,s,r,3);changes.append((f'trial{t["family"]}:{t["key"]}',old,Save.from_buffer_copy(bytes(s))))
  same=bytes(s);runjob(lib,s,r,0);assert bytes(s)==same
  old=Save.from_buffer_copy(bytes(s));assert lib.creatures_evolve_to(C.byref(s.roster),slot,t['to_form'],lib.return_context(C.byref(s)),1,1)==0
  assert lib.save5_validate(C.byref(s));changes.append((f'evolution{t["to_form"]}',old,Save.from_buffer_copy(bytes(s))))
 return changes
