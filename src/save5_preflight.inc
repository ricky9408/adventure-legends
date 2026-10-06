/* Raw snapshot preflight shares scratch and BankScan with the writer. The
 * snapshot is never encoded or changed while a transaction owns its token.
 * The record walk is equivalent to current full roster validation; parity is
 * adversarially tested against save5_validate, including every empty byte. */
static struct {
 const Save5State *live;
 Save4U32 generation;
 unsigned status, phase, index, stories;
} preflight;
int save5_preflight_active(void) {
 return preflight.status==SAVE5_BUSY||preflight.status==SAVE5_DONE;
}
void save5_preflight_cancel(void) {
 /* Revoke the generation before a load/new scene may reuse this scratch. */
 if(save5_preflight_active()&&preflight.generation<0xffffffffu)++preflight.generation;
 preflight.status=SAVE5_IDLE;preflight.live=0;
}
Save4U32 save5_preflight_begin(const Save5State *s) {
 if(!s||writer_status==SAVE5_BUSY||save5_preflight_active()||preflight.generation==0xffffffffu)return 0;
 ++preflight.generation;
 copy_state(&scratch.state,s);clear_bytes(&scan,sizeof scan);
 preflight.live=s;preflight.status=SAVE5_BUSY;preflight.phase=0;
 preflight.index=preflight.stories=0;return preflight.generation;
}
unsigned save5_preflight_status(Save4U32 token) {
 return token&&token==preflight.generation?preflight.status:SAVE5_FAILED;
}
unsigned save5_preflight_phase(Save4U32 token) {
 return token&&token==preflight.generation?preflight.phase:255;
}
const Save5State *save5_preflight_snapshot(Save4U32 token) {
 return save5_preflight_status(token)==SAVE5_DONE?&scratch.state:0;
}
EquipmentState *save5_preflight_equipment_stage(Save4U32 token) {
 return save5_preflight_status(token)==SAVE5_DONE?&scan.equipment:0;
}
int save5_preflight_matches(Save4U32 token,const Save5State *s) {
 unsigned i;
 if(!s||s!=preflight.live||save5_preflight_status(token)!=SAVE5_DONE)return 0;
 for(i=0;i<sizeof(*s)/4;++i)
  if(((const Save5AliasU32*)s)[i]!=((const Save5AliasU32*)&scratch.state)[i])return 0;
 return 1;
}
static int preflight_collection(const CreatureRoster *r) {
 unsigned i;
 if(!r->next_instance_id||!creatures_party_validate(r))return 0;
 for(i=0;i<16;++i){unsigned bits=r->seen[i],n=0;
  if(r->obtained[i]&(Save4U8)~bits)return 0;
  while(bits){if((bits&1u)&&!creatures_form(i*8+n+1))return 0;bits>>=1;++n;}
 }
 return 1;
}
static int preflight_instance(const CreatureRoster *r,unsigned slot) {
 const CreatureInstance *c=&r->instances[slot];unsigned i,legacy;
 if(!creatures_instance_validate(c))return 0;
 if(!c->form_id)return !r->expedition_bond[slot];
 if(r->expedition_bond[slot]>10||c->instance_id>=r->next_instance_id||
    !((r->obtained[(c->form_id-1)>>3]>>((c->form_id-1)&7))&1u))return 0;
 for(i=0;i<slot;++i)if(c->instance_id==r->instances[i].instance_id)return 0;
 if(c->flags&CREATURE_STORY_LOCKED){
  legacy=creatures_legacy_spirit(c->form_id);
  if(legacy>=4||(preflight.stories&(1u<<legacy))||!(r->rewards[0]&(1u<<legacy)))return 0;
  preflight.stories|=1u<<legacy;
 }
 scan.retained_creatures|=retained_creature_bits(c);
 scan.southern_evidence|=southern_instance_evidence(c);
 magma_instance_evidence(&scan.magma,c);
 underwater_instance_evidence(&scan.underwater,c);
 return 1;
}
static int preflight_equipment_record(const EquipmentState *e,unsigned slot) {
 const EquipmentRecord *r=&e->bag[slot];unsigned mask;
 if(!equipment_record_validate(r))return 0;
 if(!r->item_id)return 1;
 mask=1u<<(r->item_id&7);
 if(!(e->seen[r->item_id>>3]&mask)||(scan.item_owned[r->item_id>>3]&mask))return 0;
 scan.item_owned[r->item_id>>3]|=(Save4U8)mask;return 1;
}
unsigned save5_preflight_step(Save4U32 token,unsigned budget) {
 const Save5State *s=&scratch.state;unsigned i,n,ok=1;
 if(save5_preflight_status(token)!=SAVE5_BUSY)return save5_preflight_status(token);
 if(!budget)return SAVE5_BUSY;
 /* Semantic units are bounded independently of input budget. A giant caller
  * budget cannot silently turn this into synchronous cold validation. */
 switch(preflight.phase){
 case 0:ok=save5_campaign_validate(&s->campaign);break;
 case 1:ok=preflight_collection(&s->roster);break;
 case 2:
  n=budget/160;if(!n)n=1;if(n>8)n=8;
  for(i=0;i<n&&preflight.index<160;++i,++preflight.index)
   if(!preflight_instance(&s->roster,preflight.index)){ok=0;break;}
  if(ok&&preflight.index<160)return SAVE5_BUSY;
  if(preflight.stories!=(s->roster.rewards[0]&15u))ok=0;
  preflight.index=0;break;
 case 3:
  n=budget/16;if(!n)n=1;if(n>16)n=16;
  for(i=0;i<n&&preflight.index<64;++i,++preflight.index)
   if(!quest_objective_validate(&s->quests,preflight.index)){ok=0;break;}
  if(ok&&preflight.index<64)return SAVE5_BUSY;
  preflight.index=0;break;
 case 4:
  ok=quest_fields_validate(&s->quests);
  for(i=0;i<8&&ok;++i)ok=quest_reward_validate(&s->quests,i);
  break;
 case 5:ok=quest_campaign_validate(&s->campaign,&s->quests);break;
 case 6:ok=quest_creatures_validate(&s->quests,s->roster.obtained,s->roster.rewards,scan.retained_creatures)&&
  southern_sources_validate(&s->quests,s->roster.obtained,scan.southern_evidence);break;
 case 7:ok=magma_sources_validate(&s->quests,s->roster.obtained,&scan.magma)&&
  underwater_sources_validate(&s->quests,s->roster.obtained,&scan.underwater);break;
 case 8:
  n=budget/32;if(!n)n=1;if(n>8)n=8;
  for(i=0;i<n&&preflight.index<48;++i,++preflight.index)
   if(!preflight_equipment_record(&s->equipment,preflight.index)){ok=0;break;}
  if(ok&&preflight.index<48)return SAVE5_BUSY;
  preflight.index=0;break;
 case 9:ok=equipment_refs_validate(&s->equipment);break;
 case 10:ok=equipment_reserved_validate(&s->equipment);break;
 case 11:ok=quest_equipment_validate(&s->quests,&s->equipment);break;
 default:preflight.status=SAVE5_FAILED;return SAVE5_FAILED;
 }
 if(!ok)preflight.status=SAVE5_FAILED;
 else if(++preflight.phase==12)preflight.status=SAVE5_DONE;
 return preflight.status;
}
