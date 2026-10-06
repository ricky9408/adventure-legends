"""Executable DESIGN model. It is not cartridge code or gameplay evidence."""
from dataclasses import dataclass,field
from pathlib import Path
import copy,json
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[2]/'adventure-legends-magma'
T={v['form_id']:v for v in json.loads((BASE/'assets/creatures/terminal-topology.json').read_text())['forms']}

def coverage(forms):
 families={}
 for f in forms:
  if f not in T:raise ValueError('unknown identity')
  row=T[f];families.setdefault(row['family_id'],[]).append(row['reachable_terminal_mask'])
 viable=0
 for masks in families.values():
  # At most two immutable terminal opportunities per family. Match distinct instances.
  eligible_a=[i for i,m in enumerate(masks) if m&1]
  eligible_b=[i for i,m in enumerate(masks) if m&2]
  viable+=2 if any(a!=b for a in eligible_a for b in eligible_b) else int(bool(eligible_a or eligible_b))
 n=len(forms)
 return {'occupied':n,'viable':viable,'excess':n-viable,'free':160-n,'missing':72-viable,'safe':n<=160 and n-viable<=88}
def admitted(before,after):
 b,a=coverage(before),coverage(after)
 if a['occupied']>160:return False
 if a['safe']:return True
 return not b['safe'] and a['excess']<=b['excess'] and a['viable']>=b['viable']
@dataclass
class Instance:
 iid:int
 form:int
 trials:int=0
 level:int=26
 bond:int=20
@dataclass
class State:
 instances:list=field(default_factory=list)
 histories:set=field(default_factory=set)
 first_sources:set=field(default_factory=set)
 first_extras:set=field(default_factory=set)
 consumed_attempts:set=field(default_factory=set)
 field_aids:set=field(default_factory=set)
 next_id:int=1
 event_xp:int=0
 def grant(self,family,attempt,repeat=False):
  base=49+(family-17)*3
  if family not in range(17,25):return 'INVALID'
  if (family,attempt,repeat) in self.consumed_attempts:return 'UNCHANGED'
  if not repeat and family in self.first_sources:return 'UNCHANGED'
  if repeat and (family not in self.first_sources or not any(i.form in [base+1,base+2] for i in self.instances)):return 'LOCKED'
  if self.next_id>=2**32-1:return 'ID_EXHAUSTED'
  before=[i.form for i in self.instances]
  if not admitted(before,before+[base]):return 'RESERVED_OR_FULL'
  self.instances.append(Instance(self.next_id,base));self.next_id+=1
  self.histories.add(base);self.consumed_attempts.add((family,attempt,repeat))
  (self.first_extras if repeat else self.first_sources).add(family)
  if not repeat and family>=19:
   self.field_aids.add(78+family-19);self.event_xp+=120
  return 'GRANTED'
 def trial(self,slot,iid,family,key,proof=True):
  if family not in range(17,25) or key not in [1,2] or slot not in range(len(self.instances)):return 'INVALID'
  i=self.instances[slot];base=49+(family-17)*3
  if i.iid!=iid or i.form not in [base,base+1,base+2]:return 'INVALID'
  bit=1<<(key-1)
  if i.trials&bit:return 'UNCHANGED'
  if i.form!=base or family not in self.first_sources or not proof:return 'LOCKED'
  i.trials|=bit;i.level=max(i.level,28);i.bond=max(i.bond,45)
  aid=62+2*(family-17)+key-1
  if aid not in self.field_aids:self.field_aids.add(aid);self.event_xp+=100
  return 'TRAINED'
 def evolve(self,slot,iid,target,confirmed):
  if slot not in range(len(self.instances)):return 'INVALID'
  i=self.instances[slot]
  if i.iid!=iid:return 'INVALID'
  family=17+(i.form-49)//3;base=49+(family-17)*3
  if i.form!=base or target not in [base+1,base+2]:return 'NO_EDGE'
  bit=1<<(target-base-1)
  if not(i.trials&bit) or i.level<28 or i.bond<45:return 'LOCKED'
  if not confirmed:return 'DEFERRED'
  before=[x.form for x in self.instances];after=before[:];after[slot]=target
  if not admitted(before,after):return 'RESERVED'
  i.form=target;self.histories.add(target);return 'EVOLVED'
