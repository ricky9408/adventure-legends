/* No caller-controlled validated flag. One private job owns the immutable raw
 * Save5 snapshot; exact state and request identity survive every yielded frame.
 * Every preparation step is read-only. Only phase6 can change durable state. */
static struct {
 Save5State *live;
 UnderwaterRequest request;
 Save4U32 token, scene, admission_token;
 unsigned status, phase, gear_source, gear_last, patch, new_value;
 int result;
 CreatureInstance individual;
} underwater_job;
enum { UW_PATCH_NONE, UW_PATCH_VISIT, UW_PATCH_ANCHOR, UW_PATCH_OFFER,
 UW_PATCH_OBJECTIVE, UW_PATCH_CLAIM, UW_PATCH_FIELD, UW_PATCH_REPEAT,
 UW_PATCH_DISCOVERY, UW_PATCH_TRIAL };
static int underwater_request_valid(const UnderwaterRequest *r) {
 UnderwaterRequest extra;
 if(!r)return 0;
 extra=*r;extra.operation=0;
 switch(r->operation){
 case UW_REQUEST_VISIT:case UW_REQUEST_ANCHOR:
  if(r->room<46||r->room>53||(r->operation==UW_REQUEST_ANCHOR&&r->room>47))return 0;
  extra.room=0;break;
 case UW_REQUEST_QUEST_OFFER:case UW_REQUEST_QUEST_CLAIM:
  if(!underwater_quest_mask(r->quest))return 0;
  extra.quest=0;break;
 case UW_REQUEST_QUEST_OBJECTIVE:case UW_REQUEST_QUEST_PROGRESS:
  if(!r->bit||(r->bit&(r->bit-1))||!(r->bit&underwater_quest_mask(r->quest)))return 0;
  extra.quest=extra.bit=0;break;
 case UW_REQUEST_FIELD_RECRUIT:case UW_REQUEST_REPEAT_RECRUIT:
  if(source_index(r->source)>=8||(r->operation==UW_REQUEST_FIELD_RECRUIT&&r->source<3))return 0;
  extra.source=0;break;
 case UW_REQUEST_DISCOVER:
  if((r->family!=23&&r->family!=24)||!r->bit||(r->bit&(r->bit-1))||
     !(r->bit&(r->family==23?3u:7u)))return 0;
  extra.family=extra.bit=0;break;
 case UW_REQUEST_TRIAL_STATUS:case UW_REQUEST_TRIAL_COMPLETE:
  if(r->slot>=160||!r->instance_id||underwater_trial_aid(r->family,r->key)==255||
     underwater_source_family(r->source)!=r->family)return 0;
  extra.slot=extra.instance_id=extra.family=extra.key=extra.source=0;break;
 default:return 0;
 }
 return !(extra.room|extra.quest|extra.bit|extra.source|extra.slot|extra.family|extra.key|extra.instance_id);
}
void underwater_job_cancel(void) {
 if(underwater_job.admission_token)creatures_admission_job_cancel();
 if(underwater_job.token&&save5_preflight_status(underwater_job.token)!=SAVE5_FAILED)
  save5_preflight_cancel();
 underwater_job.status=SAVE5_IDLE;underwater_job.live=0;
 underwater_job.admission_token=0;underwater_job.result=UNDERWATER_INVALID;
}
Save4U32 underwater_job_begin(Save5State *s,const UnderwaterRequest *r,CreatureU32 scene) {
 Save4U32 token;
 if(!s||!scene||underwater_job.status==SAVE5_BUSY||!underwater_request_valid(r))return 0;
 token=save5_preflight_begin(s);if(!token)return 0;
 underwater_job.live=s;underwater_job.request=*r;underwater_job.scene=scene;
 underwater_job.token=token;underwater_job.admission_token=0;
 underwater_job.status=SAVE5_BUSY;underwater_job.phase=0;
 underwater_job.patch=UW_PATCH_NONE;underwater_job.result=UNDERWATER_INVALID;
 return token;
}
unsigned underwater_job_status(Save4U32 token) {
 return token&&token==underwater_job.token?underwater_job.status:SAVE5_FAILED;
}
unsigned underwater_job_phase(Save4U32 token) {
 return token&&token==underwater_job.token?underwater_job.phase:255;
}
int underwater_job_result(Save4U32 token) {
 return underwater_job_status(token)==SAVE5_DONE?underwater_job.result:UNDERWATER_INVALID;
}
static void underwater_job_fail(void) {
 if(underwater_job.admission_token)creatures_admission_job_cancel();
 if(save5_preflight_status(underwater_job.token)!=SAVE5_FAILED)save5_preflight_cancel();
 underwater_job.admission_token=0;
 underwater_job.status=SAVE5_FAILED;underwater_job.result=UNDERWATER_INVALID;
}
static void underwater_prepare_result(int result,unsigned patch,unsigned value) {
 underwater_job.result=result;underwater_job.patch=patch;
 underwater_job.new_value=value;underwater_job.phase=6;
}
static void underwater_prepare_request(const Save5State *s) {
 const UnderwaterRequest *r=&underwater_job.request;
 unsigned index=source_index(r->source),st,mask,bit,i,terminal=0;
 const CreatureInstance *c;
 switch(r->operation){
 case UW_REQUEST_VISIT:
  if(!underwater_can_enter(s,r->room)){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  bit=1u<<(r->room-46);
  underwater_prepare_result(s->quests.region_flags[4]&bit?UNDERWATER_UNCHANGED:UNDERWATER_CHANGED,
   UW_PATCH_VISIT,s->quests.region_flags[4]|bit);break;
 case UW_REQUEST_ANCHOR:
  bit=1u<<(r->room-46);
  if(!town(s)||!(s->quests.region_flags[4]&bit)){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  underwater_prepare_result(s->quests.anchors[4]&bit?UNDERWATER_UNCHANGED:UNDERWATER_CHANGED,
   UW_PATCH_ANCHOR,s->quests.anchors[4]|bit);break;
 case UW_REQUEST_QUEST_OFFER:case UW_REQUEST_QUEST_OBJECTIVE:case UW_REQUEST_QUEST_PROGRESS:case UW_REQUEST_QUEST_CLAIM:
  if(!underwater_quest_available(s,r->quest)){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  st=save5_quest_state(&s->quests,r->quest);mask=underwater_quest_mask(r->quest);
  if(r->operation==UW_REQUEST_QUEST_OFFER){underwater_prepare_result(st?UNDERWATER_UNCHANGED:UNDERWATER_CHANGED,UW_PATCH_OFFER,1);break;}
  if(r->operation==UW_REQUEST_QUEST_CLAIM){
   if(st==SAVE5_QUEST_CLAIMED){underwater_prepare_result(UNDERWATER_UNCHANGED,0,0);break;}
   if(st!=SAVE5_QUEST_READY||s->quests.objectives[r->quest]!=mask){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
   underwater_prepare_result(UNDERWATER_REWARDED,UW_PATCH_CLAIM,0);
   if(r->quest<40)underwater_job.phase=2;
   else if(r->quest>=41){
    EquipmentState *gear=save5_preflight_equipment_stage(underwater_job.token);
    if(!gear){underwater_job_fail();return;}
    *gear=s->equipment;
    underwater_job.gear_source=r->quest==45?35:r->quest-10;
    underwater_job.gear_last=r->quest==45?36:r->quest-10;
    underwater_job.phase=4;
   }
   break;
  }
  if(!st&&r->operation!=UW_REQUEST_QUEST_PROGRESS){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  if(st>=SAVE5_QUEST_READY||(s->quests.objectives[r->quest]&r->bit)){underwater_prepare_result(UNDERWATER_UNCHANGED,0,0);break;}
  if(r->quest==40&&(s->quests.objectives[r->quest]&(r->bit-1))!=r->bit-1){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  mask=s->quests.objectives[r->quest]|r->bit;
  underwater_prepare_result(mask==underwater_quest_mask(r->quest)?UNDERWATER_NOW_READY:UNDERWATER_CHANGED,UW_PATCH_OBJECTIVE,mask);break;
 case UW_REQUEST_FIELD_RECRUIT:case UW_REQUEST_REPEAT_RECRUIT:
  if(r->operation==UW_REQUEST_FIELD_RECRUIT&&underwater_source_claimed(s,r->source)){underwater_prepare_result(UNDERWATER_UNCHANGED,0,0);break;}
  if(!town(s)||!(s->quests.region_flags[4]&visits[index])){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  if(r->operation==UW_REQUEST_FIELD_RECRUIT){
   if((index==6&&s->quests.region_flags[20]!=3)||(index==7&&s->quests.region_flags[21]!=7)){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
   underwater_prepare_result(UNDERWATER_REWARDED,UW_PATCH_FIELD,0);
  } else {
   if(!underwater_source_claimed(s,r->source)){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
   for(i=0;i<160;++i){unsigned f=s->roster.instances[i].form_id;
    if(f==base_form(index)+1u||f==base_form(index)+2u){terminal=1;break;}}
   if(!terminal){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
   underwater_prepare_result(UNDERWATER_REWARDED,UW_PATCH_REPEAT,0);
  }
  underwater_job.phase=2;break;
 case UW_REQUEST_DISCOVER:
  index=r->family-3;mask=r->family==23?3:7;bit=r->family==23?32:8;
  if(!town(s)||!(s->quests.region_flags[4]&bit)){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  if(s->quests.region_flags[index]&r->bit){underwater_prepare_result(UNDERWATER_UNCHANGED,0,0);break;}
  if((s->quests.region_flags[index]&(r->bit-1))!=r->bit-1){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  bit=s->quests.region_flags[index]|r->bit;
  underwater_prepare_result(bit==mask?UNDERWATER_NOW_READY:UNDERWATER_CHANGED,UW_PATCH_DISCOVERY,bit);break;
 case UW_REQUEST_TRIAL_STATUS:case UW_REQUEST_TRIAL_COMPLETE:
  c=&s->roster.instances[r->slot];
  if(c->instance_id!=r->instance_id||!creatures_form(c->form_id)||creatures_form(c->form_id)->family!=r->family){underwater_prepare_result(UNDERWATER_INVALID,0,0);break;}
  if(!town(s)||!done(s,38)||!done(s,39)||!underwater_source_claimed(s,r->source)){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  if(creatures_has_trial_qualified(c,r->family,r->key)){underwater_prepare_result(UNDERWATER_UNCHANGED,0,0);break;}
  if(c->form_id!=base_form(index)){underwater_prepare_result(UNDERWATER_LOCKED,0,0);break;}
  if(r->operation==UW_REQUEST_TRIAL_STATUS){underwater_prepare_result(UNDERWATER_CHANGED,0,0);break;}
  underwater_job.individual=*c;underwater_job.phase=5;break;
 default:underwater_job_fail();break;
 }
}
static void underwater_commit_patch(void) {
 Save5State *s=underwater_job.live;const UnderwaterRequest *r=&underwater_job.request;
 unsigned index=source_index(r->source),slot;int result;
 const Save5State *snapshot=save5_preflight_snapshot(underwater_job.token);
 if(!snapshot||!save5_preflight_matches(underwater_job.token,s)){underwater_job_fail();return;}
 /* This exact comparison is the last preparation. No asynchronous yield or
  * callback occurs between it, core's one-use commit and infallible receipts. */
 if(underwater_job.admission_token){
  result=admission_result(creatures_admission_job_commit_grant(underwater_job.admission_token,&s->roster,
   underwater_recruit_level(&snapshot->roster),20,0,0,&slot));
  underwater_job.admission_token=0;
  if(result!=UNDERWATER_CHANGED){underwater_job_fail();return;}
 }
 if(underwater_job.result==UNDERWATER_CHANGED||underwater_job.result==UNDERWATER_NOW_READY||underwater_job.result==UNDERWATER_REWARDED){
  switch(underwater_job.patch){
  case UW_PATCH_VISIT:s->quests.region_flags[4]=(Save4U8)underwater_job.new_value;break;
  case UW_PATCH_ANCHOR:s->quests.anchors[4]=(Save4U8)underwater_job.new_value;break;
  case UW_PATCH_OFFER:save5_quest_set_state(&s->quests,r->quest,SAVE5_QUEST_ACTIVE);break;
  case UW_PATCH_OBJECTIVE:
   s->quests.objectives[r->quest]=(Save4U16)underwater_job.new_value;
   save5_quest_set_state(&s->quests,r->quest,underwater_job.result==UNDERWATER_NOW_READY?SAVE5_QUEST_READY:SAVE5_QUEST_ACTIVE);break;
  case UW_PATCH_CLAIM:
   if(r->quest>=41)s->equipment=*save5_preflight_equipment_stage(underwater_job.token);
   save5_quest_set_state(&s->quests,r->quest,SAVE5_QUEST_CLAIMED);
   s->quests.rewards[r->quest>>3]|=(Save4U8)(1u<<(r->quest&7));break;
  case UW_PATCH_FIELD:s->quests.region_flags[10]|=(Save4U8)(1u<<(index-2));break;
  case UW_PATCH_REPEAT:s->quests.region_flags[17]|=(Save4U8)(1u<<index);break;
  case UW_PATCH_DISCOVERY:s->quests.region_flags[r->family-3]=(Save4U8)underwater_job.new_value;break;
  case UW_PATCH_TRIAL:s->roster.instances[r->slot]=underwater_job.individual;break;
  default:break;
  }
 }
 save5_preflight_cancel();underwater_job.status=SAVE5_DONE;
}
unsigned underwater_job_step(Save4U32 token,unsigned budget,CreatureU32 scene) {
 const Save5State *s;unsigned state,result,form;
 if(underwater_job_status(token)!=SAVE5_BUSY)return underwater_job_status(token);
 if(!budget)return SAVE5_BUSY;
 if(!scene||scene!=underwater_job.scene){underwater_job_fail();return SAVE5_FAILED;}
 if(underwater_job.phase==0){
  state=save5_preflight_step(token,budget);
  if(state==SAVE5_FAILED||state==SAVE5_IDLE)underwater_job_fail();
  else if(state==SAVE5_DONE)underwater_job.phase=1;
  return underwater_job.status;
 }
 s=save5_preflight_snapshot(token);if(!s){underwater_job_fail();return SAVE5_FAILED;}
 switch(underwater_job.phase){
 case 1:underwater_prepare_request(s);break;
 case 2:
  form=underwater_job.patch==UW_PATCH_CLAIM?base_form(underwater_job.request.quest-38):underwater_source_form(underwater_job.request.source);
  underwater_job.admission_token=creatures_admission_job_begin(&s->roster,form,CREATURE_EMPTY_SLOT);
  if(!underwater_job.admission_token)underwater_job_fail();else underwater_job.phase=3;
  break;
 case 3:
  state=creatures_admission_job_step(underwater_job.admission_token,4);
  if((int)state<0){underwater_job_fail();break;}
  if(state!=1)break;
  result=(unsigned)admission_result(creatures_admission_job_result(underwater_job.admission_token,0));
  if(result==UNDERWATER_CHANGED&&s->roster.next_instance_id==0xffffffffu)result=UNDERWATER_ID_EXHAUSTED;
  if(result!=UNDERWATER_CHANGED){creatures_admission_job_cancel();underwater_job.admission_token=0;underwater_prepare_result((int)result,0,0);}
  else underwater_job.phase=6;
  break;
 case 4:{
  EquipmentState *gear=save5_preflight_equipment_stage(token);
  if(!gear){underwater_job_fail();break;}
  result=equipment_claim(gear,equipment_reward_item(underwater_job.gear_source),underwater_job.gear_source,0);
  if(result==EQUIPMENT_FULL)underwater_prepare_result(UNDERWATER_FULL,0,0);
  else if(result!=EQUIPMENT_OK&&result!=EQUIPMENT_DUPLICATE&&result!=EQUIPMENT_ALREADY_CLAIMED)underwater_job_fail();
  else if(++underwater_job.gear_source>underwater_job.gear_last)underwater_job.phase=6;
  break;}
 case 5:{
  CreatureInstance *trained=&underwater_job.individual;CreatureU32 xp=creatures_xp_threshold(28);
  if(!creatures_mark_trial_qualified(trained,underwater_job.request.family,underwater_job.request.key)||
    (trained->xp<xp&&!creatures_add_xp(trained,xp-trained->xp))){underwater_job_fail();break;}
  if(trained->bond<45)trained->bond=45;
  if(!creatures_instance_validate(trained)){underwater_job_fail();break;}
  underwater_prepare_result(UNDERWATER_REWARDED,UW_PATCH_TRIAL,0);break;
 }
 case 6:underwater_commit_patch();break;
 default:underwater_job_fail();break;
 }
 return underwater_job.status;
}
