#!/usr/bin/env python3
"""Build compact room/dialogue descriptors from the finite campaign design."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];rooms=json.loads((R/'assets/campaign_layouts.json').read_text());dlg=json.loads((R/'assets/campaign_dialogue.json').read_text());flags=rooms['flags'];chap={'GROVE_CLEAR':16,'SKY_CLEAR':17,'CORE_CLEAR':18,'ENDING_SEEN':19}
def mask(v):return sum(1<<{**flags,**chap}[x] for x in v)
def cn(x):return x.upper()
D=list(dlg['dialogue']);roomlist=rooms['rooms'];kind={'wind_vane':0,'weight_socket':1,'cracked_stone':1,'root_socket':4,'burnable':3,'brazier':7,'lamp':8,'rest':9,'sign':10,'optional':11,'return_lantern':8}
powers={'HOMURA':0,'MIDORI':1,'FUURI':2,'KOHAKU':3};spawn={'south':0,'north':1,'elder':3,'east_trail':4,'west_trail':5}
h='''#ifndef EMBER_CAMPAIGN_RULES_H
#define EMBER_CAMPAIGN_RULES_H
#include "ui.h"
typedef struct {short x,y,w,h;unsigned int flags;} CampaignBlock;
typedef struct {short x,y;unsigned char kind,power,range,input;unsigned int set,requires,lit,visible;short dialogue;unsigned char optional,hide_done;} CampaignObject;
typedef struct {short x,y;unsigned char kind,hp;} CampaignEnemy;
typedef struct {short name;unsigned char solid_count,block_count,object_count,enemy_count;const CampaignBlock *solids,*blocks;const CampaignObject *objects;const CampaignEnemy *enemies;unsigned int north_flags;unsigned char north_room,south_room,north_spawn,south_spawn,boss;} CampaignRoom;
typedef struct {short speaker;short lines[12];unsigned char pages;} CampaignDialogue;
enum {\n'''
h+=''.join(' CD_'+x+',\n' for x in D)+' CD_COUNT};\n';h+=''.join('#define CF_'+n+' (1u<<'+str(v)+')\n' for n,v in flags.items());h+='extern const CampaignRoom campaign_rooms[10];\nextern const CampaignDialogue campaign_dialogues[CD_COUNT];\n#endif\n'
c='#include "campaign_rules.h"\n'
for r in roomlist:
 n=r['id'];c+=f'static const CampaignBlock solids_{n}[]={{'+','.join('{'+','.join(map(str,v))+',0}' for v in r['static_solids'])+'};\n'
 c+=f'static const CampaignBlock blocks_{n}[]={{'+(','.join('{'+','.join(map(str,b['rect']))+','+str(mask(b.get('blocking_unless_all',[])))+'}' for b in r['dynamic_solids']) or '{0,0,0,0,0}')+'};\n'
 obs=[]
 for o in r['objects']:
  power=powers.get(o.get('companion'),255);k=3+power if o['kind']=='bond_socket' else kind[o['kind']]
  if o['id']=='well_cap':k=2
  vals=[*o['at'],k,power,o.get('range_manhattan',26),{'A':1,'R':2}.get(o.get('input'),0),mask([o['sets_flag']]) if 'sets_flag'in o else 0,mask(o.get('requires_all',[])),mask(o.get('lit_if_all',[o['sets_flag']] if 'sets_flag'in o else [])),mask([o['visible_if']]) if 'visible_if'in o else 0]
  obs.append('{'+','.join(map(str,vals))+','+('CD_'+o['dialogue'] if 'dialogue'in o else '-1')+','+str(1 if 'sets_optional'in o else 0)+','+str(int(o['kind'] in ['cracked_stone','burnable']))+'}')
 c+=f'static const CampaignObject objects_{n}[]={{'+(','.join(obs) or '{0}')+'};\n'
 c+=f'static const CampaignEnemy enemies_{n}[]={{'+(','.join('{'+','.join(map(str,[*e['at'],2 if e['kind']=='ranger' else 0,e['hp']]))+'}' for e in r['enemies']) or '{0}')+'};\n'
c+='const CampaignRoom campaign_rooms[10]={\n'
for r in roomlist:
 n=r['id'];south=r['exits'][0];north=r['exits'][1];c+='{TX_C_ROOM_'+str(n)+','+','.join(str(len(r[k])) for k in ['static_solids','dynamic_solids','objects','enemies'])+f',solids_{n},blocks_{n},objects_{n},enemies_{n},'+str(mask(north.get('requires_all',[])))+','+','.join(map(str,[north['to_room'],south['to_room'],spawn[north['to_spawn']],spawn[south['to_spawn']],1 if n==8 else 2 if n==13 else 0]))+'},\n'
c+='};\nconst CampaignDialogue campaign_dialogues[CD_COUNT]={\n'
for n,x in dlg['dialogue'].items():c+='{TX_C_'+n+'_SPEAKER,{'+','.join('TX_C_'+n+'_'+str(p)+'_'+str(l) for p,page in enumerate(x['pages']) for l,_ in enumerate(page))+'},'+str(len(x['pages']))+'},\n'
c+='};\n';(R/'src/campaign_rules.h').write_text(h);(R/'src/campaign_rules.c').write_text(c)
print('Generated campaign geometry and',len(D),'dialogues')
