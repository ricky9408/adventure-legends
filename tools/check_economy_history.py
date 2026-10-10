#!/usr/bin/env python3
"""Reproduce immutable9 only from the pinned accepted E source closure."""
import argparse,ctypes as C,hashlib,json,re,subprocess,tempfile
from pathlib import Path
from check_horizons_history import render
from generate_creature_history import render_v8
ROOT=Path(__file__).resolve().parents[1]
ORACLE=ROOT/'tests/fixtures/covenants-e-policy-oracle'
MANIFEST_SHA='d2f88221207319fbb50f82deb5d61e9b51259be7ba3eae99f9756c97b6564fb0'
def verify_oracle():
 raw=(ORACLE/'manifest.json').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==MANIFEST_SHA,'Accepted E manifest changed'
 m=json.loads(raw)
 for name,sha in m['files'].items():assert hashlib.sha256((ORACLE/name).read_bytes()).hexdigest()==sha,name
 return m
PROBE=r'''
#include "creatures.c"
unsigned frozen_field(unsigned id,unsigned key){
 const CreatureForm*f=creatures_form(id);const CreatureEvolution*e;
 if(!f)return 0;
 e=f->tier>1?incoming_evolution(id):0;
 switch(key){case 0:return f->family;case 1:return f->polarity;case 2:return e?e->min_level:1;
 case 3:return creatures_trial_allowed_mask(id,9);case 4:return f->learnset_count;case 5:return f->rarity;
 case 6:return e&&((f->family>=17&&f->family<=24)||(e->chapter_flags&(4096|8192|16384)))?e->min_bond:0;
 case 7:return e&&((f->family>=17&&f->family<=24)||(e->chapter_flags&(4096|8192|16384)))?e->trial_flag:0;}
 return 0;
}
unsigned frozen_learn(unsigned id,unsigned n,unsigned key){const CreatureForm*f=creatures_form(id);const CreatureLearn*l;
 if(!f||n>=f->learnset_count)return 0;
 l=&creature_learnsets[f->learnset_offset+n];return key?l->ability_id:l->level;}
unsigned frozen_dependencies(void){return sizeof trial_policy/sizeof trial_policy[0];}
unsigned frozen_dependency(unsigned n,unsigned k){const CreatureTrialPolicy*p=&trial_policy[n];return k==0?p->family:k==1?p->mask:p->prerequisite;}
'''
def creature_snapshot():
 with tempfile.TemporaryDirectory(prefix='frozen-e-snapshot-') as tmp:
  d=Path(tmp);(d/'probe.c').write_text(PROBE)
  so=d/'probe.so'
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC','-I'+str(ORACLE/'src'),str(d/'probe.c'),str(ORACLE/'src/creature_data.c'),'-o',str(so)],check=True)
  l=C.CDLL(str(so));forms=[]
  for id in range(1,129):
   f=lambda k:l.frozen_field(id,k)
   assert f(0)
   forms.append(dict(id=id,family=f(0),polarity=f(1),revision_bits=0,min_level=f(2),trial_mask=f(3),min_bond=f(6),required_trial=f(7),rarity=f(5),learn=[[l.frozen_learn(id,n,0),l.frozen_learn(id,n,1)]for n in range(f(4))]))
  dependencies=[dict(family=l.frozen_dependency(i,0),mask=l.frozen_dependency(i,1),prerequisite=l.frozen_dependency(i,2))for i in range(l.frozen_dependencies())]
 return dict(schema=2,content_revision=9,forms=forms,trial_dependencies=dependencies)
def render_creatures(data):
 text=render_v8(dict(data,content_revision=8)).replace('revision8','revision9').replace('creatures-v8','creatures-v9').replace('CreatureRevision8Constraint','CreatureRevision9Constraint')
 for f in data['forms']:
  prefix='    {'+', '.join(map(str,(f['id'],f['family'],f['polarity'],len(f['learn']),f['min_level'])))+', '
  text=text.replace(prefix+'128, ',prefix+'0, ')
 text+='static const CreatureU8 revision9_legendary[129] = {'+','.join('[%d]=1'%f['id'] for f in data['forms']if f['rarity'])+'};\n'
 return text

def outputs():
 src=(ORACLE/'src/save5.c').read_text()
 policy=render(src.replace('quest_masks[64]','quest_masks[54]')).replace('history7_','history9_').replace('content7','content9').replace('before content8','before content10').replace('exact H','exact Covenants E').replace('return-h-policy-oracle','covenants-e-policy-oracle').replace('quest_masks[54]','quest_masks[64]')
 policy=re.sub(r'\bhorizons_','history9_horizons_',policy);policy=re.sub(r'\bcovenant(s?)_',r'history9_covenant\1_',policy)
 policy=re.sub(r'creatures_form_allowed_revision\((\d+),7\)',r'creatures_form_allowed_revision(\1,9)',policy)
 horizons='/* Frozen accepted E content9; never resolve live Horizons rows. */\n'+re.sub(r'\bhorizons_','history9_horizons_',(ORACLE/'src/save5_horizons_policy.inc').read_text())
 covenants='/* Frozen accepted E content9 covenant rights and receipts. */\n'+re.sub(r'\bcovenant(s?)_',r'history9_covenant\1_',(ORACLE/'src/save5_covenants_policy.inc').read_text())
 equipment=(ORACLE/'src/equipment_data.c').read_text()
 quests=[int(x)for x in re.search(r'equipment_source_quest\[48\] = \{([^}]+)',src)[1].split(',')]
 ids=[int(x)for x in re.search(r'equipment_authored_ids\[EQUIPMENT_AUTHORED_COUNT\] = \{([^}]+)',equipment)[1].split(',')]
 text='''/* Immutable accepted E equipment/source identities. */
static const Save5HistoryVersion save5_policy9_version={64,48,77,
 {[0]=63,[1]=255,[2]=255,[3]=255,[4]=255,[5]=255,[6]=255,[7]=255,
 [8]=255,[9]=127,[10]=63,[11]=3,[12]=255,[13]=15,[14]=255,[15]=15,
 [16]=15,[17]=255,[18]=3,[19]=7,[20]=3,[21]=7,[22]=255,[23]=255},
 {[0]=3,[1]=3,[2]=3,[3]=3,[4]=3,[5]=3,[6]=3,[7]=3}};
static const Save5HistoryItem save5_policy9_items[48]={
'''
 for n,id in enumerate(ids):
  row=re.search(r'\['+str(id)+r'\] = \{'+str(id)+r', (\d+), \d+, (\d+),',equipment)
  text+=' {%d,%d,%d,%d,%d},\n'%(id,int(row[1]),int(row[2]),0 if n==0 else 1 if quests[n]<0 else 2,quests[n])
 text+='};\n'
 data=creature_snapshot()
 return {'src/save5_revision9_policy.inc':policy,'src/save5_revision9_horizons.inc':horizons,'src/save5_revision9_covenants.inc':covenants,'src/save5_revision9_equipment.inc':text,'assets/history/creatures-v9.json':json.dumps(data,indent=2)+'\n','src/creature_history_v9.inc':render_creatures(data)}
def main():
 a=argparse.ArgumentParser();a.add_argument('--write',action='store_true');args=a.parse_args();verify_oracle()
 for name,content in outputs().items():
  p=ROOT/name
  if args.write:p.write_text(content)
  else:assert p.read_text()==content,'Immutable9 reproduction changed: '+name
 print('Accepted E closure and immutable content9 snapshot verified')
if __name__=='__main__':main()
