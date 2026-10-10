#include "horizons_quests.h"
/* ROM-only bounded handlers; no second full save, roster, or proof allocation. */
static const Save4U8 masks[6]={7,15,15,15,7,15};
static const Save4U8 priors[6][2]={{52,0},{55,0},{55,0},{56,57},{55,0},{55,0}};
static const Save4U8 gear_sources[6]={255,42,43,255,44,45};
static const Save4U8 claim_rooms[6]={62,63,65,62,65,60};
static const Save4U8 bases[12]={105,107,109,111,113,114,115,116,117,118,119,120};
static const Save4U8 rooms[12]={62,63,66,68,63,64,65,67,69,66,62,68};
static const Save4U8 trial_rooms[4]={64,67,66,68};
static const Save4U8 objectives[][4]={
 {54,1,0,60},{54,2,1,62},{54,4,3,62},
 {55,1,0,63},{55,2,1,63},{55,4,3,64},{55,8,7,63},
 {56,1,0,65},{56,2,1,65},{56,4,3,66},{56,8,7,66},
 {57,1,0,67},{57,2,1,67},{57,4,3,68},{57,8,7,68},
 {58,1,0,64},{58,2,0,69},{58,4,3,65},{59,1,0,63},{59,2,0,66},{59,4,0,69},{59,8,7,60}
};
static int done(const Save5State*s,unsigned q){return s&&save5_quest_state(&s->quests,q)==SAVE5_QUEST_CLAIMED;}
static unsigned source_index(unsigned source){return source>=1&&source<=12?source-1:source>=33&&source<=44?source-33:255;}
unsigned horizons_source_family(unsigned source){unsigned i=source_index(source);return i<12?41+i:0;}
unsigned horizons_source_form(unsigned source){unsigned i=source_index(source);return i<12?bases[i]:0;}
unsigned horizons_source_room(unsigned source){unsigned i=source_index(source);return i<12?rooms[i]:0;}
int horizons_source_claimed(const Save5State*s,unsigned source){unsigned i=source_index(source);return s&&i<12&&!!(s->quests.region_flags[12+(i>>3)]&(1u<<(i&7)));}
unsigned horizons_recruit_level(const CreatureRoster*r){(void)r;return 32;}
unsigned horizons_context(const Save5State*s){return done(s,54)?CREATURE_HORIZONS_READY:0;}
unsigned horizons_quest_mask(unsigned q){return q>=54&&q<=59?masks[q-54]:0;}
int horizons_quest_available(const Save5State*s,unsigned q){unsigned i;if(!s||q<54||q>59)return 0;
 for(i=0;i<2;++i)if(priors[q-54][i]&&!done(s,priors[q-54][i]-1u))return 0;
 return 1;
}
static int visited(const Save5State*s,unsigned room){return s&&(room==60?!!(s->quests.region_flags[5]&64u):room>=62&&room<=69?!!(s->quests.region_flags[6]&(1u<<(room-62))):0);}
int horizons_can_enter(const Save5State*s,unsigned room){
 if(!s||room<62||room>69||!done(s,51))return 0;
 if(room==62)return 1;
 if(!(s->quests.region_flags[6]&1u)||!done(s,54))return 0;
 return room==67||room==68?done(s,55)&&done(s,56):1;
}
unsigned horizons_trial_aid(unsigned family,unsigned key){return family>=41&&family<=44&&key==1?97+family-41:255;}
unsigned horizons_trial_form(unsigned family,unsigned key){return family>=41&&family<=44&&key==1?bases[family-41]:0;}
unsigned horizons_trial_room(unsigned family,unsigned key){return family>=41&&family<=44&&key==1?trial_rooms[family-41]:0;}
static const Save4U8*objective(unsigned q,unsigned bit){unsigned i;for(i=0;i<sizeof objectives/sizeof objectives[0];++i)if(objectives[i][0]==q&&objectives[i][1]==bit)return objectives[i];return 0;}
static int selected_matches(const Save5State*s,unsigned slot,CreatureU32 id,unsigned form,unsigned command){
 const CreatureRoster*r;const CreatureInstance*c;
 if(!s||slot>=160||!id||!form||form>128||!command||command>255)return 0;
 r=&s->roster;c=&r->instances[slot];return r->selected_party<4&&r->party[r->selected_party]==slot&&
 c->instance_id==id&&c->form_id==form&&c->selected_command<2&&c->equipped[c->selected_command]==command&&
 creatures_instance_validate(c)&&creatures_command_learned(form,c->level,command);
}
int horizons_trial_status(const Save5State*s,unsigned slot,CreatureU32 id,unsigned family,unsigned key,unsigned form,unsigned command){
 if(!horizons_trial_form(family,key)||form!=horizons_trial_form(family,key)||command!=form+1u||!selected_matches(s,slot,id,form,command))return HORIZONS_INVALID;
 if(!done(s,54)||!horizons_source_claimed(s,family-40)||!visited(s,horizons_trial_room(family,key)))return HORIZONS_LOCKED;
 return creatures_has_trial_qualified(&s->roster.instances[slot],family,key)?HORIZONS_UNCHANGED:HORIZONS_CHANGED;
}
static int admission_result(enum CreatureAdmissionStatus r){
 if(creatures_admission_allowed(r))return HORIZONS_CHANGED;
 if(r==CREATURE_ADMISSION_FULL)return HORIZONS_FULL;
 if(r==CREATURE_ADMISSION_RESERVED)return HORIZONS_SPACE_RESERVED;
 if(r==CREATURE_ADMISSION_COVERAGE_LOSS)return HORIZONS_COVERAGE_LOSS;
 if(r==CREATURE_ADMISSION_ID_EXHAUSTED)return HORIZONS_ID_EXHAUSTED;
 return HORIZONS_INVALID;
}
const char*horizons_result_message(int result){switch(result){
 case HORIZONS_FULL:return "Storage is full. Your invitation is still ready.";
 case HORIZONS_SPACE_RESERVED:return "Keep room for a missing family or evolution path.";
 case HORIZONS_COVERAGE_LOSS:return "That change would lose a remaining evolution path.";
 case HORIZONS_ID_EXHAUSTED:return "This collection cannot assign another identity.";
 case HORIZONS_LOCKED:return "Complete the marked steps first.";
 case HORIZONS_UNCHANGED:return "Already recorded.";
 case HORIZONS_INVALID:return "That action could not be recorded.";
 default:return "Ready.";}}
enum { PATCH_NONE,PATCH_VISIT,PATCH_ANCHOR,PATCH_OFFER,PATCH_OBJECTIVE,PATCH_CLAIM,PATCH_INITIAL,PATCH_REPEAT,PATCH_TRIAL };
static struct {Save5State*live;HorizonsRequest request;
 Save4U32 token,scene,attempt,admission_token,consumed_scene,consumed_attempt;
 unsigned status,phase,patch,value;int result;CreatureInstance individual;} job;
static int source_operation(unsigned op){return op==HORIZONS_REQUEST_INITIAL_RECRUIT||op==HORIZONS_REQUEST_REPEAT_RECRUIT;}
static int request_valid(const HorizonsRequest*r){
 HorizonsRequest x;unsigned i;const Save4U8*o;if(!r)return 0;x=*r;x.operation=0;
 switch(r->operation){
 case HORIZONS_REQUEST_VISIT:case HORIZONS_REQUEST_ANCHOR:
  if(r->room<62||r->room>69||(r->operation==HORIZONS_REQUEST_ANCHOR&&r->room!=62&&r->room!=65))return 0;
  x.room=0;break;
 case HORIZONS_REQUEST_QUEST_OFFER:case HORIZONS_REQUEST_QUEST_CLAIM:
  if(!horizons_quest_mask(r->quest))return 0;
  if(r->operation==HORIZONS_REQUEST_QUEST_CLAIM&&r->room!=claim_rooms[r->quest-54])return 0;
  if(r->operation==HORIZONS_REQUEST_QUEST_OFFER&&r->room!=60&&(r->room<62||r->room>69))return 0;
  x.room=x.quest=0;break;
 case HORIZONS_REQUEST_QUEST_OBJECTIVE:case HORIZONS_REQUEST_QUEST_PROGRESS:
  o=objective(r->quest,r->bit);if(!o||r->room!=o[3]||(r->quest<=57&&r->bit==(r->quest==54?4u:8u)))return 0;
  x.room=x.quest=x.bit=0;break;
 case HORIZONS_REQUEST_INITIAL_RECRUIT:case HORIZONS_REQUEST_REPEAT_RECRUIT:
  i=source_index(r->source);if(i>=12||r->family!=41+i||r->room!=rooms[i])return 0;
  if(r->operation==HORIZONS_REQUEST_INITIAL_RECRUIT){if(r->source>12)return 0;}
  else{
   if(r->source<33||r->slot>=160||!r->instance_id||r->command!=bases[i]+1u||
      (r->form!=bases[i]&&(i>=4||r->form!=bases[i]+1u)))return 0;
   x.slot=x.instance_id=x.command=x.form=0;
  }
  x.room=x.source=x.family=0;break;
 case HORIZONS_REQUEST_TRIAL_STATUS:case HORIZONS_REQUEST_TRIAL_COMPLETE:
  if(!horizons_trial_form(r->family,r->key)||r->room!=horizons_trial_room(r->family,r->key)||
   r->form!=horizons_trial_form(r->family,r->key)||r->command!=r->form+1u||r->slot>=160||!r->instance_id)return 0;
  x.room=x.family=x.key=x.form=x.command=x.slot=x.instance_id=0;break;
 default:return 0;
 }
 return !(x.room|x.quest|x.bit|x.source|x.slot|x.family|x.key|x.form|x.command|x.instance_id);
}
void horizons_job_cancel(void){
 /* Loading or replacing a job can revoke our lease before delayed cleanup.
  * A stale owner must not cancel another job's admission cursor or scratch. */
 if(job.token&&save5_preflight_status(job.token)!=SAVE5_FAILED){
  if(job.admission_token)creatures_admission_job_cancel();
  save5_preflight_cancel();
 }
 job.status=SAVE5_IDLE;job.live=0;job.admission_token=0;job.result=HORIZONS_INVALID;
}
static void fail(void){horizons_job_cancel();job.status=SAVE5_FAILED;}
Save4U32 horizons_job_begin(Save5State*s,const HorizonsRequest*r,CreatureU32 scene,CreatureU32 attempt){
 Save4U32 token;if(!s||!scene||!attempt||job.status==SAVE5_BUSY||!request_valid(r)||
  (source_operation(r->operation)&&job.consumed_scene&&(scene<job.consumed_scene||(scene==job.consumed_scene&&attempt<=job.consumed_attempt))))return 0;
 token=save5_preflight_begin(s);if(!token)return 0;
 job.live=s;job.request=*r;job.scene=scene;job.attempt=attempt;job.token=token;job.admission_token=0;
 job.status=SAVE5_BUSY;job.phase=0;job.patch=PATCH_NONE;job.result=HORIZONS_INVALID;return token;
}
unsigned horizons_job_status(Save4U32 token){return token&&token==job.token?job.status:SAVE5_FAILED;}
unsigned horizons_job_phase(Save4U32 token){return token&&token==job.token?job.phase:255;}
int horizons_job_result(Save4U32 token){return horizons_job_status(token)==SAVE5_DONE?job.result:HORIZONS_INVALID;}
static void result(int code,unsigned patch,unsigned value){job.result=code;job.patch=patch;job.value=value;job.phase=6;}
static void prepare(const Save5State*s){
 const HorizonsRequest*r=&job.request;unsigned bit,state,mask,i;const Save4U8*o;int code;
 if(r->operation!=HORIZONS_REQUEST_VISIT&&r->room!=s->campaign.room){result(HORIZONS_INVALID,0,0);return;}
 switch(r->operation){
 case HORIZONS_REQUEST_VISIT:
  if(!horizons_can_enter(s,r->room)){result(HORIZONS_LOCKED,0,0);break;}
  bit=1u<<(r->room-62);result(s->quests.region_flags[6]&bit?HORIZONS_UNCHANGED:HORIZONS_CHANGED,PATCH_VISIT,s->quests.region_flags[6]|bit);break;
 case HORIZONS_REQUEST_ANCHOR:
  bit=r->room==62?1u:2u;if(!horizons_can_enter(s,r->room)||!visited(s,r->room)){result(HORIZONS_LOCKED,0,0);break;}
  result(s->quests.anchors[6]&bit?HORIZONS_UNCHANGED:HORIZONS_CHANGED,PATCH_ANCHOR,s->quests.anchors[6]|bit);break;
 case HORIZONS_REQUEST_QUEST_OFFER:case HORIZONS_REQUEST_QUEST_OBJECTIVE:case HORIZONS_REQUEST_QUEST_PROGRESS:case HORIZONS_REQUEST_QUEST_CLAIM:
  if(!horizons_quest_available(s,r->quest)||!visited(s,r->room)){result(HORIZONS_LOCKED,0,0);break;}
  state=save5_quest_state(&s->quests,r->quest);mask=horizons_quest_mask(r->quest);
  if(r->operation==HORIZONS_REQUEST_QUEST_OFFER){result(state?HORIZONS_UNCHANGED:HORIZONS_CHANGED,PATCH_OFFER,0);break;}
  if(r->operation!=HORIZONS_REQUEST_QUEST_CLAIM){
   if(!state&&r->operation!=HORIZONS_REQUEST_QUEST_PROGRESS){result(HORIZONS_LOCKED,0,0);break;}
   if(state>=SAVE5_QUEST_READY||(s->quests.objectives[r->quest]&r->bit)){result(HORIZONS_UNCHANGED,0,0);break;}
   o=objective(r->quest,r->bit);if(!o||(s->quests.objectives[r->quest]&o[2])!=o[2]){result(HORIZONS_LOCKED,0,0);break;}
   bit=s->quests.objectives[r->quest]|r->bit;result(bit==mask?HORIZONS_NOW_READY:HORIZONS_CHANGED,PATCH_OBJECTIVE,bit);break;
  }
  if(state==SAVE5_QUEST_CLAIMED){result(HORIZONS_UNCHANGED,0,0);break;}
  if(state!=SAVE5_QUEST_READY||s->quests.objectives[r->quest]!=mask){result(HORIZONS_LOCKED,0,0);break;}
  result(HORIZONS_REWARDED,PATCH_CLAIM,0);
  if(gear_sources[r->quest-54]!=255){EquipmentState*stage=save5_preflight_equipment_stage(job.token);if(!stage){fail();break;}*stage=s->equipment;job.phase=4;}
  break;
 case HORIZONS_REQUEST_INITIAL_RECRUIT:
  i=source_index(r->source);if(horizons_source_claimed(s,r->source)){result(HORIZONS_UNCHANGED,0,0);break;}
  if(!visited(s,r->room)||!horizons_can_enter(s,r->room)){result(HORIZONS_LOCKED,0,0);break;}
  if(i<4){unsigned q=54+i;
   if(!horizons_quest_available(s,q)||save5_quest_state(&s->quests,q)!=SAVE5_QUEST_ACTIVE||s->quests.objectives[q]!=(i?7u:3u)){result(HORIZONS_LOCKED,0,0);break;}
  }else if(!done(s,54)){result(HORIZONS_LOCKED,0,0);break;}
  result(HORIZONS_REWARDED,PATCH_INITIAL,0);job.phase=2;break;
 case HORIZONS_REQUEST_REPEAT_RECRUIT:
  i=source_index(r->source);
  if(!selected_matches(s,r->slot,r->instance_id,r->form,r->command)){result(HORIZONS_INVALID,0,0);break;}
  if(!horizons_source_claimed(s,r->source)||!visited(s,r->room)||!done(s,i<4?54+i:54)){result(HORIZONS_LOCKED,0,0);break;}
  result(HORIZONS_REWARDED,PATCH_REPEAT,0);job.phase=2;break;
 case HORIZONS_REQUEST_TRIAL_STATUS:case HORIZONS_REQUEST_TRIAL_COMPLETE:
  code=horizons_trial_status(s,r->slot,r->instance_id,r->family,r->key,r->form,r->command);
  if(code!=HORIZONS_CHANGED||r->operation==HORIZONS_REQUEST_TRIAL_STATUS){result(code,0,0);break;}
  job.individual=s->roster.instances[r->slot];job.phase=5;break;
 default:fail();break;
 }
}
static void commit(void){
 Save5State*s=job.live;const HorizonsRequest*r=&job.request;unsigned slot,i=source_index(r->source);int code;
 if((source_operation(r->operation)&&i>=12)||!save5_preflight_snapshot(job.token)||!save5_preflight_matches(job.token,s)){fail();return;}
 if(job.admission_token){
  code=admission_result(creatures_admission_job_commit_grant(job.admission_token,&s->roster,32,30,0,0,&slot));job.admission_token=0;
  if(code!=HORIZONS_CHANGED){fail();return;}
 }
 if(job.result==HORIZONS_CHANGED||job.result==HORIZONS_NOW_READY||job.result==HORIZONS_REWARDED){switch(job.patch){
  case PATCH_VISIT:s->quests.region_flags[6]=(Save4U8)job.value;break;
  case PATCH_ANCHOR:s->quests.anchors[6]=(Save4U8)job.value;break;
  case PATCH_OFFER:save5_quest_set_state(&s->quests,r->quest,SAVE5_QUEST_ACTIVE);break;
  case PATCH_OBJECTIVE:s->quests.objectives[r->quest]=(Save4U16)job.value;save5_quest_set_state(&s->quests,r->quest,job.result==HORIZONS_NOW_READY?SAVE5_QUEST_READY:SAVE5_QUEST_ACTIVE);break;
  case PATCH_CLAIM:
   if(gear_sources[r->quest-54]!=255)s->equipment=*save5_preflight_equipment_stage(job.token);
   save5_quest_set_state(&s->quests,r->quest,SAVE5_QUEST_CLAIMED);s->quests.rewards[r->quest>>3]|=(Save4U8)(1u<<(r->quest&7));break;
  case PATCH_INITIAL:case PATCH_REPEAT:
   s->quests.region_flags[(job.patch==PATCH_INITIAL?12:14)+((r->family-41)>>3)]|=(Save4U8)(1u<<(i&7));
   if(job.patch==PATCH_INITIAL&&i<4){s->quests.objectives[54+i]=masks[i];save5_quest_set_state(&s->quests,54+i,SAVE5_QUEST_READY);}
   job.consumed_scene=job.scene;job.consumed_attempt=job.attempt;break;
  case PATCH_TRIAL:s->roster.instances[r->slot]=job.individual;break;
  default:break;
 }}
 save5_preflight_cancel();job.status=SAVE5_DONE;
}
unsigned horizons_job_step(Save4U32 token,unsigned budget,CreatureU32 scene,CreatureU32 attempt){
 const Save5State*s;unsigned status;int code;if(horizons_job_status(token)!=SAVE5_BUSY)return horizons_job_status(token);
 if(!scene||scene!=job.scene||!attempt||attempt!=job.attempt){fail();return SAVE5_FAILED;}
 if(!budget)return SAVE5_BUSY;
 if(!job.phase){status=save5_preflight_step(token,budget);if(status==SAVE5_FAILED||status==SAVE5_IDLE)fail();else if(status==SAVE5_DONE)job.phase=1;return job.status;}
 s=save5_preflight_snapshot(token);if(!s){fail();return SAVE5_FAILED;}
 switch(job.phase){
 case 1:prepare(s);break;
 case 2:job.admission_token=creatures_admission_job_begin(&s->roster,horizons_source_form(job.request.source),CREATURE_EMPTY_SLOT);
  if(!job.admission_token)fail();else job.phase=3;break;
 case 3:
  status=creatures_admission_job_step(job.admission_token,4);if((int)status<0){fail();break;}if(status!=1)break;
  code=admission_result(creatures_admission_job_result(job.admission_token,0));
  if(code==HORIZONS_CHANGED&&s->roster.next_instance_id==0xffffffffu)code=HORIZONS_ID_EXHAUSTED;
  if(code!=HORIZONS_CHANGED){creatures_admission_job_cancel();job.admission_token=0;result(code,0,0);}else job.phase=6;break;
 case 4:{
  unsigned source=gear_sources[job.request.quest-54];EquipmentState*stage=save5_preflight_equipment_stage(token);
  if(!stage){fail();break;}status=equipment_claim(stage,equipment_reward_item(source),source,0);
  if(status==EQUIPMENT_FULL)result(HORIZONS_FULL,0,0);else if(status!=EQUIPMENT_OK)fail();else job.phase=6;break;}
 case 5:{
  CreatureInstance*c=&job.individual;CreatureU32 xp=creatures_xp_threshold(34);
  if(c->xp<xp&&!creatures_add_xp(c,xp-c->xp)){fail();break;}
  if(c->bond<60)c->bond=60;
  if(!creatures_mark_trial_qualified(c,job.request.family,job.request.key)||!creatures_instance_validate(c)){fail();break;}
  result(HORIZONS_REWARDED,PATCH_TRIAL,0);break;}
 case 6:commit();break;
 default:fail();break;
 }
 return job.status;
}
