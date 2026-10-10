#include "covenants_quests.h"
/* ROM code, one small typed cursor, exclusive existing Save5 scratch. */
static const Save4U8 masks[4]={7,15,15,7};
static const Save4U8 offers[4]={0,70,74,70},claims[4]={70,70,74,0},gear[4]={255,46,255,47};
static const Save4U8 objectives[][4]={{60,1,0,0},{60,2,1,62},{60,4,3,70},{63,1,0,70},{63,2,1,62},{63,4,3,0}};
static int done(const Save5State*s,unsigned q){return s&&save5_quest_state(&s->quests,q)==SAVE5_QUEST_CLAIMED;}
static int visited(const Save5State*s,unsigned room){return s&&(room==0?1:room==62?!!(s->quests.region_flags[6]&1u):room>=70&&room<=77?!!(s->quests.region_flags[7]&(1u<<(room-70))):0);}
unsigned covenants_source_form(unsigned source){return source>=1&&source<=8?120+source:0;}
unsigned covenants_source_family(unsigned source){return source>=1&&source<=8?52+source:0;}
unsigned covenants_source_room(unsigned source){return source>=1&&source<=8?69+source:0;}
int covenants_fulfilled(const Save5State*s,unsigned source){return s&&source>=1&&source<=8&&!!(s->quests.region_flags[22]&(1u<<(source-1)));}
int covenants_source_claimed(const Save5State*s,unsigned source){return s&&source>=1&&source<=8&&!!(s->quests.region_flags[23]&(1u<<(source-1)));}
unsigned covenants_quest_mask(unsigned q){return q>=60&&q<=63?masks[q-60]:0;}
int covenants_quest_available(const Save5State*s,unsigned q){
 if(!s||q<60||q>63||!(s->campaign.chapter_flags&SAVE4_ENDING_SEEN)||!done(s,57))return 0;
 return q==60?1:q==61?done(s,60):q==62?done(s,61):done(s,61)&&done(s,62);
}
int covenants_can_enter(const Save5State*s,unsigned room){
 if(!s||room<70||room>77||!covenants_quest_available(s,60)||(s->quests.objectives[60]&3u)!=3u)return 0;
 if(room==70)return 1;
 if(!visited(s,70)||!done(s,60))return 0;
 return room<74?1:done(s,61);
}
static const Save4U8*objective(unsigned q,unsigned bit){unsigned i;for(i=0;i<sizeof objectives/sizeof objectives[0];++i)if(objectives[i][0]==q&&objectives[i][1]==bit)return objectives[i];return 0;}
const char*covenants_result_message(int result){switch(result){
 case COVENANTS_FULL:return "Storage is full. Your invitation is still ready.";
 case COVENANTS_SPACE_RESERVED:return "Keep room for a missing family or evolution path.";
 case COVENANTS_COVERAGE_LOSS:return "That change would lose a remaining evolution path.";
 case COVENANTS_ID_EXHAUSTED:return "This collection cannot assign another identity.";
 case COVENANTS_LOCKED:return "Complete the marked steps first.";
 case COVENANTS_UNCHANGED:return "Already recorded.";
 case COVENANTS_INVALID:return "That action could not be recorded.";
 default:return "Ready.";}}
static int admission_result(enum CreatureAdmissionStatus r){
 if(creatures_admission_allowed(r))return COVENANTS_CHANGED;
 if(r==CREATURE_ADMISSION_FULL)return COVENANTS_FULL;
 if(r==CREATURE_ADMISSION_RESERVED)return COVENANTS_SPACE_RESERVED;
 if(r==CREATURE_ADMISSION_COVERAGE_LOSS)return COVENANTS_COVERAGE_LOSS;
 if(r==CREATURE_ADMISSION_ID_EXHAUSTED)return COVENANTS_ID_EXHAUSTED;
 return COVENANTS_INVALID;
}
enum { PATCH_NONE,PATCH_VISIT,PATCH_ANCHOR,PATCH_OFFER,PATCH_OBJECTIVE,PATCH_CLAIM,PATCH_COMPLETE,PATCH_INVITE };
static struct {Save5State*live;CovenantsRequest request;Save4U32 token,scene,attempt,admission_token,consumed_scene,consumed_attempt;
 unsigned status,phase,patch,value;int result;} job;
typedef char covenants_job_cursor_budget[(sizeof job<=256)?1:-1];
static int source_operation(unsigned op){return op==COVENANTS_REQUEST_COVENANT_COMPLETE||op==COVENANTS_REQUEST_UNIQUE_INVITE;}
static int request_valid(const CovenantsRequest*r){
 CovenantsRequest x;const Save4U8*o;if(!r)return 0;x=*r;x.operation=0;
 switch(r->operation){
 case COVENANTS_REQUEST_VISIT:case COVENANTS_REQUEST_ANCHOR:
  if(r->room<70||r->room>77||(r->operation==COVENANTS_REQUEST_ANCHOR&&r->room!=70&&r->room!=74))return 0;
  x.room=0;break;
 case COVENANTS_REQUEST_QUEST_OFFER:case COVENANTS_REQUEST_QUEST_CLAIM:
  if(!covenants_quest_mask(r->quest)||r->room!=(r->operation==COVENANTS_REQUEST_QUEST_OFFER?offers:claims)[r->quest-60])return 0;
  x.room=x.quest=0;break;
 case COVENANTS_REQUEST_ORDINARY_OBJECTIVE:
  o=objective(r->quest,r->bit);if(!o||r->room!=o[3])return 0;x.room=x.quest=x.bit=0;break;
 case COVENANTS_REQUEST_COVENANT_COMPLETE:case COVENANTS_REQUEST_UNIQUE_INVITE:
  if(!covenants_source_form(r->source)||r->room!=covenants_source_room(r->source))return 0;
  x.room=x.source=0;break;
 default:return 0;
 }return !(x.room|x.quest|x.bit|x.source);
}
void covenants_job_cancel(void){
 if(job.token&&save5_preflight_status(job.token)!=SAVE5_FAILED){
  if(job.admission_token)creatures_admission_job_cancel();
  save5_preflight_cancel();
 }
 job.status=SAVE5_IDLE;job.live=0;job.admission_token=0;job.result=COVENANTS_INVALID;
}
static void fail(void){covenants_job_cancel();job.status=SAVE5_FAILED;}
Save4U32 covenants_job_begin(Save5State*s,const CovenantsRequest*r,CreatureU32 scene,CreatureU32 attempt){
 Save4U32 token;if(!s||!scene||!attempt||job.status==SAVE5_BUSY||!request_valid(r)||
  (source_operation(r->operation)&&job.consumed_scene&&(scene<job.consumed_scene||(scene==job.consumed_scene&&attempt<=job.consumed_attempt))))return 0;
 token=save5_preflight_begin(s);if(!token)return 0;
 job.live=s;job.request=*r;job.scene=scene;job.attempt=attempt;job.token=token;job.admission_token=0;
 job.status=SAVE5_BUSY;job.phase=0;job.patch=PATCH_NONE;job.result=COVENANTS_INVALID;return token;
}
unsigned covenants_job_status(Save4U32 token){return token&&token==job.token?job.status:SAVE5_FAILED;}
unsigned covenants_job_phase(Save4U32 token){return token&&token==job.token?job.phase:255;}
int covenants_job_result(Save4U32 token){return covenants_job_status(token)==SAVE5_DONE?job.result:COVENANTS_INVALID;}
static void result(int code,unsigned patch,unsigned value){job.result=code;job.patch=patch;job.value=value;job.phase=5;}
static void prepare(const Save5State*s){
 const CovenantsRequest*r=&job.request;unsigned bit,state,q;const Save4U8*o;
 if(r->operation!=COVENANTS_REQUEST_VISIT&&r->room!=s->campaign.room){result(COVENANTS_INVALID,0,0);return;}
 switch(r->operation){
 case COVENANTS_REQUEST_VISIT:
  if(!covenants_can_enter(s,r->room)){result(COVENANTS_LOCKED,0,0);break;}
  bit=1u<<(r->room-70);result(s->quests.region_flags[7]&bit?COVENANTS_UNCHANGED:COVENANTS_CHANGED,PATCH_VISIT,s->quests.region_flags[7]|bit);break;
 case COVENANTS_REQUEST_ANCHOR:
  bit=r->room==70?1u:2u;if(!covenants_can_enter(s,r->room)||!visited(s,r->room)){result(COVENANTS_LOCKED,0,0);break;}
  result(s->quests.anchors[7]&bit?COVENANTS_UNCHANGED:COVENANTS_CHANGED,PATCH_ANCHOR,s->quests.anchors[7]|bit);break;
 case COVENANTS_REQUEST_QUEST_OFFER:case COVENANTS_REQUEST_ORDINARY_OBJECTIVE:case COVENANTS_REQUEST_QUEST_CLAIM:
  if(!covenants_quest_available(s,r->quest)||!visited(s,r->room)){result(COVENANTS_LOCKED,0,0);break;}
  state=save5_quest_state(&s->quests,r->quest);
  if(r->operation==COVENANTS_REQUEST_QUEST_OFFER){result(state?COVENANTS_UNCHANGED:COVENANTS_CHANGED,PATCH_OFFER,0);break;}
  if(r->operation==COVENANTS_REQUEST_ORDINARY_OBJECTIVE){
   if(!state){result(COVENANTS_LOCKED,0,0);break;}
   if(state>=SAVE5_QUEST_READY||(s->quests.objectives[r->quest]&r->bit)){result(COVENANTS_UNCHANGED,0,0);break;}
   o=objective(r->quest,r->bit);if(!o||(s->quests.objectives[r->quest]&o[2])!=o[2]){result(COVENANTS_LOCKED,0,0);break;}
   bit=s->quests.objectives[r->quest]|r->bit;result(bit==covenants_quest_mask(r->quest)?COVENANTS_NOW_READY:COVENANTS_CHANGED,PATCH_OBJECTIVE,bit);break;
  }
  if(state==SAVE5_QUEST_CLAIMED){result(COVENANTS_UNCHANGED,0,0);break;}
  if(state!=SAVE5_QUEST_READY||s->quests.objectives[r->quest]!=covenants_quest_mask(r->quest)){result(COVENANTS_LOCKED,0,0);break;}
  result(COVENANTS_REWARDED,PATCH_CLAIM,0);
  if(gear[r->quest-60]!=255){EquipmentState*stage=save5_preflight_equipment_stage(job.token);if(!stage){fail();break;}*stage=s->equipment;job.phase=4;}break;
 case COVENANTS_REQUEST_COVENANT_COMPLETE:
  if(covenants_fulfilled(s,r->source)){result(COVENANTS_UNCHANGED,0,0);break;}
  q=r->source<=4?61u:62u;
  if(!covenants_quest_available(s,q)||!visited(s,r->room)||save5_quest_state(&s->quests,q)!=SAVE5_QUEST_ACTIVE){result(COVENANTS_LOCKED,0,0);break;}
  bit=s->quests.objectives[q]|(1u<<((r->source-1)&3));result(bit==15?COVENANTS_NOW_READY:COVENANTS_CHANGED,PATCH_COMPLETE,bit);break;
 case COVENANTS_REQUEST_UNIQUE_INVITE:
  if(covenants_source_claimed(s,r->source)){result(COVENANTS_UNCHANGED,0,0);break;}
  if(!covenants_fulfilled(s,r->source)||!visited(s,r->room)||!covenants_can_enter(s,r->room)){result(COVENANTS_LOCKED,0,0);break;}
  result(COVENANTS_REWARDED,PATCH_INVITE,0);job.phase=2;break;
 default:fail();break;
 }
}
static void commit(void){
 Save5State*s=job.live;const CovenantsRequest*r=&job.request;unsigned slot,q;int code;
 if(!save5_preflight_snapshot(job.token)||!save5_preflight_matches(job.token,s)){fail();return;}
 if(job.admission_token){
  code=admission_result(creatures_admission_job_commit_grant(job.admission_token,&s->roster,36,60,0,0,&slot));job.admission_token=0;
  if(code!=COVENANTS_CHANGED){fail();return;}
 }
 if(job.result==COVENANTS_CHANGED||job.result==COVENANTS_NOW_READY||job.result==COVENANTS_REWARDED){switch(job.patch){
 case PATCH_VISIT:s->quests.region_flags[7]=(Save4U8)job.value;break;
 case PATCH_ANCHOR:s->quests.anchors[7]=(Save4U8)job.value;break;
 case PATCH_OFFER:save5_quest_set_state(&s->quests,r->quest,SAVE5_QUEST_ACTIVE);break;
 case PATCH_OBJECTIVE:s->quests.objectives[r->quest]=(Save4U16)job.value;save5_quest_set_state(&s->quests,r->quest,job.result==COVENANTS_NOW_READY?SAVE5_QUEST_READY:SAVE5_QUEST_ACTIVE);break;
 case PATCH_CLAIM:
  if(gear[r->quest-60]!=255)s->equipment=*save5_preflight_equipment_stage(job.token);
  save5_quest_set_state(&s->quests,r->quest,SAVE5_QUEST_CLAIMED);s->quests.rewards[r->quest>>3]|=(Save4U8)(1u<<(r->quest&7));break;
 case PATCH_COMPLETE:
  q=r->source<=4?61u:62u;s->quests.region_flags[22]|=(Save4U8)(1u<<(r->source-1));s->quests.objectives[q]=(Save4U16)job.value;
  save5_quest_set_state(&s->quests,q,job.result==COVENANTS_NOW_READY?SAVE5_QUEST_READY:SAVE5_QUEST_ACTIVE);
  job.consumed_scene=job.scene;job.consumed_attempt=job.attempt;break;
 case PATCH_INVITE:s->quests.region_flags[23]|=(Save4U8)(1u<<(r->source-1));job.consumed_scene=job.scene;job.consumed_attempt=job.attempt;break;
 default:break;
 }}save5_preflight_cancel();job.status=SAVE5_DONE;
}
unsigned covenants_job_step(Save4U32 token,unsigned budget,CreatureU32 scene,CreatureU32 attempt){
 const Save5State*s;unsigned status;int code;if(covenants_job_status(token)!=SAVE5_BUSY)return covenants_job_status(token);
 if(!scene||scene!=job.scene||!attempt||attempt!=job.attempt){fail();return SAVE5_FAILED;}
 if(!budget)return SAVE5_BUSY;
 if(!job.phase){status=save5_preflight_step(token,budget);if(status==SAVE5_FAILED||status==SAVE5_IDLE)fail();else if(status==SAVE5_DONE)job.phase=1;return job.status;}
 s=save5_preflight_snapshot(token);if(!s){fail();return SAVE5_FAILED;}
 switch(job.phase){
 case 1:prepare(s);break;
 case 2:job.admission_token=creatures_admission_job_begin(&s->roster,covenants_source_form(job.request.source),CREATURE_EMPTY_SLOT);if(!job.admission_token)fail();else job.phase=3;break;
 case 3:
  status=creatures_admission_job_step(job.admission_token,4);if((int)status<0){fail();break;}if(status!=1)break;
  code=admission_result(creatures_admission_job_result(job.admission_token,0));
  if(code==COVENANTS_CHANGED&&s->roster.next_instance_id==0xffffffffu)code=COVENANTS_ID_EXHAUSTED;
  if(code!=COVENANTS_CHANGED){creatures_admission_job_cancel();job.admission_token=0;result(code,0,0);}else job.phase=5;break;
 case 4:{unsigned source=gear[job.request.quest-60];EquipmentState*stage=save5_preflight_equipment_stage(token);
  if(!stage){fail();break;}status=equipment_claim(stage,equipment_reward_item(source),source,0);
  if(status==EQUIPMENT_FULL)result(COVENANTS_FULL,0,0);else if(status!=EQUIPMENT_OK)fail();else job.phase=5;break;}
 case 5:commit();break;
 default:fail();break;
 }return job.status;
}
