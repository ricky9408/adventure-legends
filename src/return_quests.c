#include "return_quests.h"
/* ROM policy and one bounded transaction cursor; no full-save/roster clone. */
static const Save4U8 masks[8]={3,7,7,7,7,15,7,15};
static const Save4U8 priors[8][2]={{41,0},{47,0},{48,0},{47,0},{50,0},{49,51},{47,0},{48,50}};
static const Save4U8 gear_sources[8]={255,255,39,255,40,38,37,41};
typedef struct ReturnTrial { Save4U8 family,key,from,room,command[2],level,bond,aid; Save4U16 prerequisite; } ReturnTrial;
static const ReturnTrial trials[13]={
 {1,2,2,54,{1,5},32,60,84,1},
 {2,2,5,54,{2,6},32,60,85,2},
 {3,2,8,57,{3,7},32,60,86,4},
 {4,2,11,61,{4,8},32,60,87,8},
 {5,2,14,56,{9,10},32,60,88,16},
 {6,1,16,55,{11,0},28,45,89,0},
 {6,2,17,60,{11,96},32,60,90,1024},
 {7,2,20,57,{13,14},32,60,91,32},
 {8,2,23,57,{15,16},32,60,92,64},
 {9,2,26,58,{23,24},32,60,93,1},
 {10,2,29,58,{25,26},32,60,94,1},
 {39,1,101,56,{102,0},28,45,95,0},
 {40,1,103,59,{104,0},28,45,96,0},
};
static int done(const Save5State*s,unsigned q){return s&&save5_quest_state(&s->quests,q)==SAVE5_QUEST_CLAIMED;}
static const ReturnTrial *trial_for(unsigned family,unsigned key){
 unsigned i;for(i=0;i<13;++i)if(trials[i].family==family&&trials[i].key==key)return &trials[i];return 0;
}
unsigned return_trial_aid(unsigned family,unsigned key){const ReturnTrial*t=trial_for(family,key);return t?t->aid:255;}
unsigned return_trial_form(unsigned family,unsigned key){const ReturnTrial*t=trial_for(family,key);return t?t->from:0;}
unsigned return_trial_room(unsigned family,unsigned key){const ReturnTrial*t=trial_for(family,key);return t?t->room:0;}
unsigned return_source_family(unsigned token){return token==1||token==17?39:token==2||token==18?40:0;}
unsigned return_source_form(unsigned token){return token==1||token==17?101:token==2||token==18?103:0;}
int return_source_claimed(const Save5State*s,unsigned token){unsigned f=return_source_family(token);return f&&done(s,47+2*(f-39));}
unsigned return_context(const Save5State*s){return (done(s,46)?CREATURE_RETURN_READY:0)|(done(s,51)?CREATURE_RETURN_COMPLETE:0);}
unsigned return_quest_mask(unsigned q){return q>=46&&q<54?masks[q-46]:0;}
unsigned return_recruit_level(const CreatureRoster*r){(void)r;return 28;}
int return_can_enter(const Save5State*s,unsigned room){
 if(!s||room<54||room>61||!done(s,46))return 0;
 if(room!=54&&!(s->quests.region_flags[5]&1u))return 0;
 if(room==56||room==59)return done(s,49);
 if(room==57)return done(s,47);
 if(room>=60)return done(s,48)&&done(s,50);
 return 1;
}
int return_quest_available(const Save5State*s,unsigned q){
 unsigned i;if(!s||!return_quest_mask(q))return 0;
 for(i=0;i<2;++i)if(priors[q-46][i]&&!done(s,priors[q-46][i]-1u))return 0;
 return 1;
}
static int objective_visit(const Save5State*s,unsigned q,unsigned bit){
 static const Save4U8 required[][3]={
  {47,2,2},
  {48,1,8},
  {48,2,8},
  {49,1,16},
  {49,2,16},
  {50,1,32},
  {50,2,4},
  {51,1,64},
  {51,2,64},
  {51,4,128},
  {52,2,8},
  {53,1,1},
  {53,2,4},
  {53,4,8},
  {53,8,16},
 };
 unsigned i;for(i=0;i<sizeof required/sizeof required[0];++i)
  if(q==required[i][0]&&bit==required[i][1])return (s->quests.region_flags[5]&required[i][2])!=0;
 return 1;
}
static int selected_matches(const Save5State*s,unsigned slot,CreatureU32 id,unsigned form,unsigned command){
 const CreatureRoster*r;const CreatureInstance*c;
 if(!s||slot>=160||!id||!form||form>128||!command||command>255)return 0;
 r=&s->roster;c=&r->instances[slot];
 return r->selected_party<4&&r->party[r->selected_party]==slot&&c->instance_id==id&&c->form_id==form&&
  c->selected_command<2&&c->equipped[c->selected_command]==command&&creatures_instance_validate(c)&&
  creatures_command_learned(form,c->level,command);
}
int return_trial_status(const Save5State*s,unsigned slot,CreatureU32 id,
 unsigned family,unsigned key,unsigned form,unsigned command){
 const ReturnTrial*t=trial_for(family,key);const CreatureInstance*c;
 if(!t||!selected_matches(s,slot,id,form,command)||form!=t->from||
  (command!=t->command[0]&&command!=t->command[1]))return RETURN_INVALID;
 c=&s->roster.instances[slot];
 if(!done(s,46)||!(s->quests.region_flags[5]&(1u<<(t->room-54)))||
  (c->trial_flags&t->prerequisite)!=t->prerequisite)return RETURN_LOCKED;
 if(creatures_has_trial_qualified(c,family,key))return RETURN_UNCHANGED;
 return RETURN_CHANGED;
}
static int admission_result(enum CreatureAdmissionStatus r){
 if(creatures_admission_allowed(r))return RETURN_CHANGED;
 if(r==CREATURE_ADMISSION_FULL)return RETURN_FULL;
 if(r==CREATURE_ADMISSION_RESERVED||r==CREATURE_ADMISSION_COVERAGE_LOSS)return RETURN_SPACE_RESERVED;
 if(r==CREATURE_ADMISSION_ID_EXHAUSTED)return RETURN_ID_EXHAUSTED;
 return RETURN_INVALID;
}
const char *return_result_message(int result){
 switch(result){
 case RETURN_FULL:return "Storage is full. Your invitation is still ready.";
 case RETURN_SPACE_RESERVED:return "Keep room for a missing family or evolution path.";
 case RETURN_ID_EXHAUSTED:return "This collection cannot assign another identity.";
 case RETURN_LOCKED:return "Complete the marked steps first.";
 case RETURN_UNCHANGED:return "Already recorded.";
 case RETURN_INVALID:return "That action could not be recorded.";
 default:return "Ready.";
 }
}
enum { RT_PATCH_NONE,RT_PATCH_VISIT,RT_PATCH_ANCHOR,RT_PATCH_OFFER,
 RT_PATCH_OBJECTIVE,RT_PATCH_CLAIM,RT_PATCH_REPEAT,RT_PATCH_TRIAL };
static struct {
 Save5State*live;ReturnRequest request;
 Save4U32 token,scene,attempt,admission_token,consumed_scene,consumed_attempt;
 unsigned status,phase,patch,value;
 int result;CreatureInstance individual;
} job;
static int request_valid(const ReturnRequest*r){
 ReturnRequest extra;if(!r)return 0;extra=*r;extra.operation=0;
 switch(r->operation){
 case RETURN_REQUEST_VISIT:case RETURN_REQUEST_ANCHOR:
  if(r->room<54||r->room>61||(r->operation==RETURN_REQUEST_ANCHOR&&r->room>55))return 0;
  extra.room=0;break;
 case RETURN_REQUEST_QUEST_OFFER:case RETURN_REQUEST_QUEST_CLAIM:
  if(!return_quest_mask(r->quest))return 0;
  if(r->operation==RETURN_REQUEST_QUEST_CLAIM&&(r->quest==47||r->quest==49)){
   if(r->source!=(r->quest==47?1u:2u))return 0;
   extra.source=0;
  }
  extra.quest=0;break;
 case RETURN_REQUEST_QUEST_OBJECTIVE:case RETURN_REQUEST_QUEST_PROGRESS:
  if(!r->bit||(r->bit&(r->bit-1))||!(r->bit&return_quest_mask(r->quest)))return 0;
  extra.quest=extra.bit=0;break;
 case RETURN_REQUEST_REPEAT_RECRUIT:
  if((r->source!=17&&r->source!=18)||r->family!=return_source_family(r->source)||
   r->room!=(r->source==17?55u:58u)||r->command!=(r->source==17?102u:104u)||
   r->slot>=160||!r->instance_id||r->form<return_source_form(r->source)||r->form>return_source_form(r->source)+1u)return 0;
  extra.source=extra.family=extra.room=extra.command=extra.slot=extra.instance_id=extra.form=0;break;
 case RETURN_REQUEST_TRIAL_STATUS:case RETURN_REQUEST_TRIAL_COMPLETE:{
  const ReturnTrial*t=trial_for(r->family,r->key);
  if(!t||r->slot>=160||!r->instance_id||r->room!=t->room||r->form!=t->from||
   (r->command!=t->command[0]&&r->command!=t->command[1])||!r->command)return 0;
  extra.slot=extra.instance_id=extra.family=extra.key=extra.room=extra.form=extra.command=0;break;}
 default:return 0;
 }
 return !(extra.room|extra.quest|extra.bit|extra.source|extra.slot|extra.family|extra.key|extra.form|extra.command|extra.instance_id);
}
void return_job_cancel(void){
 if(job.admission_token)creatures_admission_job_cancel();
 if(job.token&&save5_preflight_status(job.token)!=SAVE5_FAILED)save5_preflight_cancel();
 job.status=SAVE5_IDLE;job.live=0;job.admission_token=0;job.result=RETURN_INVALID;
}
static void fail(void){return_job_cancel();job.status=SAVE5_FAILED;}
Save4U32 return_job_begin(Save5State*s,const ReturnRequest*r,CreatureU32 scene,CreatureU32 attempt){
 Save4U32 token;
 if(!s||!scene||!attempt||job.status==SAVE5_BUSY||!request_valid(r)||
  (r->operation==RETURN_REQUEST_REPEAT_RECRUIT&&job.consumed_scene&&
   (scene<job.consumed_scene||(scene==job.consumed_scene&&attempt<=job.consumed_attempt))))return 0;
 token=save5_preflight_begin(s);if(!token)return 0;
 job.live=s;job.request=*r;job.scene=scene;job.attempt=attempt;job.token=token;
 job.admission_token=0;job.status=SAVE5_BUSY;job.phase=0;job.patch=RT_PATCH_NONE;job.result=RETURN_INVALID;
 return token;
}
unsigned return_job_status(Save4U32 token){return token&&token==job.token?job.status:SAVE5_FAILED;}
unsigned return_job_phase(Save4U32 token){return token&&token==job.token?job.phase:255;}
int return_job_result(Save4U32 token){return return_job_status(token)==SAVE5_DONE?job.result:RETURN_INVALID;}
static void prepare_result(int result,unsigned patch,unsigned value){job.result=result;job.patch=patch;job.value=value;job.phase=6;}
static void prepare(const Save5State*s){
 const ReturnRequest*r=&job.request;unsigned bit,state,mask,source;int result;
 switch(r->operation){
 case RETURN_REQUEST_VISIT:
  if(!return_can_enter(s,r->room)){prepare_result(RETURN_LOCKED,0,0);break;}
  bit=1u<<(r->room-54);prepare_result(s->quests.region_flags[5]&bit?RETURN_UNCHANGED:RETURN_CHANGED,RT_PATCH_VISIT,s->quests.region_flags[5]|bit);break;
 case RETURN_REQUEST_ANCHOR:
  bit=1u<<(r->room-54);
  if(!done(s,46)||!(s->quests.region_flags[5]&bit)){prepare_result(RETURN_LOCKED,0,0);break;}
  prepare_result(s->quests.anchors[5]&bit?RETURN_UNCHANGED:RETURN_CHANGED,RT_PATCH_ANCHOR,s->quests.anchors[5]|bit);break;
 case RETURN_REQUEST_QUEST_OFFER:case RETURN_REQUEST_QUEST_OBJECTIVE:case RETURN_REQUEST_QUEST_PROGRESS:case RETURN_REQUEST_QUEST_CLAIM:
  if(!return_quest_available(s,r->quest)){prepare_result(RETURN_LOCKED,0,0);break;}
  state=save5_quest_state(&s->quests,r->quest);mask=return_quest_mask(r->quest);
  if(r->operation==RETURN_REQUEST_QUEST_OFFER){prepare_result(state?RETURN_UNCHANGED:RETURN_CHANGED,RT_PATCH_OFFER,0);break;}
  if(r->operation!=RETURN_REQUEST_QUEST_CLAIM){
   if(!objective_visit(s,r->quest,r->bit)){prepare_result(RETURN_LOCKED,0,0);break;}
   if(!state&&r->operation!=RETURN_REQUEST_QUEST_PROGRESS){prepare_result(RETURN_LOCKED,0,0);break;}
   if(state>=SAVE5_QUEST_READY||(s->quests.objectives[r->quest]&r->bit)){prepare_result(RETURN_UNCHANGED,0,0);break;}
   bit=s->quests.objectives[r->quest]|r->bit;
   prepare_result(bit==mask?RETURN_NOW_READY:RETURN_CHANGED,RT_PATCH_OBJECTIVE,bit);break;
  }
  if(state==SAVE5_QUEST_CLAIMED){prepare_result(RETURN_UNCHANGED,0,0);break;}
  if(state!=SAVE5_QUEST_READY||s->quests.objectives[r->quest]!=mask){prepare_result(RETURN_LOCKED,0,0);break;}
  prepare_result(RETURN_REWARDED,RT_PATCH_CLAIM,0);
  if(r->quest==47||r->quest==49){job.phase=2;break;}
  source=gear_sources[r->quest-46];
  if(source!=255){EquipmentState*stage=save5_preflight_equipment_stage(job.token);if(!stage){fail();break;}*stage=s->equipment;job.phase=4;}
  break;
 case RETURN_REQUEST_REPEAT_RECRUIT:
  if(!selected_matches(s,r->slot,r->instance_id,r->form,r->command)){prepare_result(RETURN_INVALID,0,0);break;}
  if(!return_source_claimed(s,r->source)||!(s->quests.region_flags[5]&(1u<<(r->room-54)))){prepare_result(RETURN_LOCKED,0,0);break;}
  prepare_result(RETURN_REWARDED,RT_PATCH_REPEAT,0);job.phase=2;break;
 case RETURN_REQUEST_TRIAL_STATUS:case RETURN_REQUEST_TRIAL_COMPLETE:
  result=return_trial_status(s,r->slot,r->instance_id,r->family,r->key,r->form,r->command);
  if(result!=RETURN_CHANGED||r->operation==RETURN_REQUEST_TRIAL_STATUS){prepare_result(result,0,0);break;}
  job.individual=s->roster.instances[r->slot];job.phase=5;break;
 default:fail();break;
 }
}
static void commit(void){
 Save5State*s=job.live;const ReturnRequest*r=&job.request;unsigned slot;int result;
 if(!save5_preflight_snapshot(job.token)||!save5_preflight_matches(job.token,s)){fail();return;}
 if(job.admission_token){
  result=admission_result(creatures_admission_job_commit_grant(job.admission_token,&s->roster,28,25,0,0,&slot));job.admission_token=0;
  if(result!=RETURN_CHANGED){fail();return;}
 }
 if(job.result==RETURN_CHANGED||job.result==RETURN_NOW_READY||job.result==RETURN_REWARDED){
  switch(job.patch){
  case RT_PATCH_VISIT:s->quests.region_flags[5]=(Save4U8)job.value;break;
  case RT_PATCH_ANCHOR:s->quests.anchors[5]=(Save4U8)job.value;break;
  case RT_PATCH_OFFER:save5_quest_set_state(&s->quests,r->quest,SAVE5_QUEST_ACTIVE);break;
  case RT_PATCH_OBJECTIVE:s->quests.objectives[r->quest]=(Save4U16)job.value;save5_quest_set_state(&s->quests,r->quest,job.result==RETURN_NOW_READY?SAVE5_QUEST_READY:SAVE5_QUEST_ACTIVE);break;
  case RT_PATCH_CLAIM:
   if(gear_sources[r->quest-46]!=255)s->equipment=*save5_preflight_equipment_stage(job.token);
   save5_quest_set_state(&s->quests,r->quest,SAVE5_QUEST_CLAIMED);s->quests.rewards[r->quest>>3]|=(Save4U8)(1u<<(r->quest&7));break;
  case RT_PATCH_REPEAT:s->quests.region_flags[11]|=(Save4U8)(1u<<(r->family-39));job.consumed_scene=job.scene;job.consumed_attempt=job.attempt;break;
  case RT_PATCH_TRIAL:s->roster.instances[r->slot]=job.individual;break;
  default:break;
  }
 }
 save5_preflight_cancel();job.status=SAVE5_DONE;
}
unsigned return_job_step(Save4U32 token,unsigned budget,CreatureU32 scene,CreatureU32 attempt){
 const Save5State*s;unsigned status,form;int result;
 if(return_job_status(token)!=SAVE5_BUSY)return return_job_status(token);
 if(!scene||scene!=job.scene||!attempt||attempt!=job.attempt){fail();return SAVE5_FAILED;}
 if(!budget)return SAVE5_BUSY;
 if(!job.phase){status=save5_preflight_step(token,budget);if(status==SAVE5_FAILED||status==SAVE5_IDLE)fail();else if(status==SAVE5_DONE)job.phase=1;return job.status;}
 s=save5_preflight_snapshot(token);if(!s){fail();return SAVE5_FAILED;}
 switch(job.phase){
 case 1:prepare(s);break;
 case 2:
  form=return_source_form(job.request.source);job.admission_token=creatures_admission_job_begin(&s->roster,form,CREATURE_EMPTY_SLOT);
  if(!job.admission_token)fail();else job.phase=3;break;
 case 3:
  status=creatures_admission_job_step(job.admission_token,4);if((int)status<0){fail();break;}if(status!=1)break;
  result=admission_result(creatures_admission_job_result(job.admission_token,0));
  if(result==RETURN_CHANGED&&s->roster.next_instance_id==0xffffffffu)result=RETURN_ID_EXHAUSTED;
  if(result!=RETURN_CHANGED){creatures_admission_job_cancel();job.admission_token=0;prepare_result(result,0,0);}else job.phase=6;break;
 case 4:{
  unsigned source=gear_sources[job.request.quest-46];EquipmentState*stage=save5_preflight_equipment_stage(token);
  if(!stage){fail();break;}status=equipment_claim(stage,equipment_reward_item(source),source,0);
  if(status==EQUIPMENT_FULL)prepare_result(RETURN_FULL,0,0);
  else if(status!=EQUIPMENT_OK&&status!=EQUIPMENT_DUPLICATE&&status!=EQUIPMENT_ALREADY_CLAIMED)fail();else job.phase=6;
  break;}
 case 5:{
  const ReturnTrial*t=trial_for(job.request.family,job.request.key);CreatureInstance*c=&job.individual;CreatureU32 xp=creatures_xp_threshold(t->level);
  if(!creatures_mark_trial_qualified(c,t->family,t->key)||(c->xp<xp&&!creatures_add_xp(c,xp-c->xp))){fail();break;}
  if(c->bond<t->bond)c->bond=t->bond;
  if(!creatures_instance_validate(c)){fail();break;}
  prepare_result(RETURN_REWARDED,RT_PATCH_TRIAL,0);break;}
 case 6:commit();break;
 default:fail();break;
 }
 return job.status;
}
