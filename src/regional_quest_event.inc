/* Engine-private Southern/Magma offer/objective/claim transaction.
 * One authored action names one quest and at most eight ordered operations.
 * Public synchronous quest APIs are untouched. The projection is only a UI /
 * same-action branch view, never a validation certificate. Every mutation
 * needs the existing complete immutable preflight and an exact live compare.
 * All code stays in ROM; only this small cursor lives in EWRAM. */
enum { RQ_OFFER=1,RQ_OBJECTIVE,RQ_CLAIM,RQ_DISCOVER,RQ_COLLECT=1,RQ_VALIDATE,RQ_PLAN,
 RQ_ADMISSION,RQ_READY };
static struct {
 Save4U32 token,admission,revision,chapter;
 unsigned char phase,q,count,cursor,projected,staged,claim,gear;
 unsigned char op[8],bit[8],party[4],selected,form,commands[3];
 Save4U16 projected_bits,staged_bits;
 CreatureU32 identity[4];
 int area,x,y,facing,spawn,active,dialog_a,dialog_b,result;
 unsigned char dialog,persist,changed,failed,discovered;
} rq;
static COLD void rq_cancel(void){
 if(rq.token&&save5_preflight_status(rq.token)!=SAVE5_FAILED){
  if(rq.admission)creatures_admission_job_cancel();
  save5_preflight_cancel();
 }
 rq.token=rq.admission=0;rq.phase=rq.count=rq.dialog=rq.persist=rq.failed=0;
}
static COLD unsigned rq_state(unsigned q){
 return rq.phase&&q==rq.q?rq.projected:save5_quest_state(&adventure_save.quests,q);
}
static COLD unsigned rq_objectives(unsigned q){
 return rq.phase&&q==rq.q?rq.projected_bits:adventure_save.quests.objectives[q];
}
static COLD int rq_source_matches(void){unsigned i,slot;const CreatureInstance*c;
 if(room!=rq.area||px!=rq.x||py!=rq.y||face!=rq.facing||checkpoint_spawn!=rq.spawn||
  summoned!=rq.active||adventure_save.roster.selected_party!=rq.selected)return 0;
 for(i=0;i<4;i++)if(adventure_save.roster.party[i]!=rq.party[i]||
  (rq.party[i]<160&&adventure_save.roster.instances[rq.party[i]].instance_id!=rq.identity[i]))return 0;
 slot=rq.selected<4?rq.party[rq.selected]:255;c=slot<160?&adventure_save.roster.instances[slot]:0;
 if(rq.form!=(c?c->form_id:0)||rq.commands[0]!=(c?c->equipped[0]:0)||
    rq.commands[1]!=(c?c->equipped[1]:0)||rq.commands[2]!=(c?c->selected_command:0))return 0;
 return 1;
}
static COLD int rq_apply(const Save5State*s,unsigned op,unsigned bit,unsigned *st,unsigned *bits){
 unsigned mask=RQ_MASK(rq.q);
 if(!mask||(op==RQ_OBJECTIVE&&(!bit||(bit&(bit-1))||!(mask&bit))))return RQ_INVALID;
 if(!RQ_AVAILABLE(s,rq.q))return RQ_LOCKED;
 if(op==RQ_OFFER){if(*st)return RQ_UNCHANGED;*st=SAVE5_QUEST_ACTIVE;return RQ_CHANGED;}
 if(op==RQ_OBJECTIVE){
  if(!*st)return RQ_LOCKED;
  if(*st>=SAVE5_QUEST_READY||(*bits&bit))return RQ_UNCHANGED;
  if(rq.q==RQ_FIRST+2&&(*bits&(bit-1))!=bit-1)return RQ_LOCKED;
  *bits|=bit;
  if(*bits==mask){*st=SAVE5_QUEST_READY;return RQ_NOW_READY;}
  return RQ_CHANGED;
 }
 if(op==RQ_DISCOVER){
  if(!RQ_DISCOVERY||(rq.q!=28&&rq.q!=29)||bit!=(rq.q==29?1u:2u))return RQ_INVALID;
  if(!(s->quests.region_flags[2]&4u)||*st<SAVE5_QUEST_READY)return RQ_LOCKED;
  return s->quests.region_flags[18]&bit?RQ_UNCHANGED:RQ_CHANGED;
 }
 if(op!=RQ_CLAIM)return RQ_INVALID;
 if(*st==SAVE5_QUEST_CLAIMED)return RQ_UNCHANGED;
 return *st==SAVE5_QUEST_READY&&*bits==mask?RQ_REWARDED:RQ_LOCKED;
}
static COLD int rq_enqueue(unsigned q,unsigned op,unsigned bit){unsigned i,st,bits,slot,mask=RQ_MASK(q);const CreatureInstance*c;int result;
 /* Validate wide caller values before byte storage. An invalid request must
  * never become a different valid operation after narrowing on replay. */
 if(!mask||game_state!=PLAY||op<RQ_OFFER||op>RQ_DISCOVER||
  ((op==RQ_OFFER||op==RQ_CLAIM)&&bit)||
  (op==RQ_OBJECTIVE&&(!bit||(bit&(bit-1))||!(mask&bit)))||
  (op==RQ_DISCOVER&&(!RQ_DISCOVERY||(q!=28&&q!=29)||bit!=(q==29?1u:2u)))){
  if(rq.phase)rq.failed=1;
  return RQ_INVALID;
 }
 if(!rq.phase){
  rq.q=(unsigned char)q;rq.count=rq.cursor=rq.claim=rq.changed=rq.failed=rq.discovered=0;
  rq.gear=255;rq.dialog=rq.persist=0;rq.token=rq.admission=0;
  rq.projected=(unsigned char)save5_quest_state(&adventure_save.quests,q);
  rq.projected_bits=adventure_save.quests.objectives[q];rq.phase=RQ_COLLECT;
  rq.area=room;rq.x=px;rq.y=py;rq.facing=face;rq.spawn=checkpoint_spawn;rq.active=summoned;
  rq.selected=adventure_save.roster.selected_party;
  for(i=0;i<4;i++){rq.party[i]=adventure_save.roster.party[i];rq.identity[i]=rq.party[i]<160?adventure_save.roster.instances[rq.party[i]].instance_id:0;}
  slot=rq.selected<4?rq.party[rq.selected]:255;c=slot<160?&adventure_save.roster.instances[slot]:0;
  rq.form=c?c->form_id:0;rq.commands[0]=c?c->equipped[0]:0;
  rq.commands[1]=c?c->equipped[1]:0;rq.commands[2]=c?c->selected_command:0;
 }
 if(rq.phase!=RQ_COLLECT||rq.q!=q||rq.count==8||rq.claim||!rq_source_matches()){
  rq.failed=1;return RQ_INVALID;
 }
 rq.op[rq.count]=(unsigned char)op;rq.bit[rq.count++]=(unsigned char)bit;
 st=rq.projected;bits=rq.projected_bits;result=rq_apply(&adventure_save,op,bit,&st,&bits);
 rq.projected=(unsigned char)st;rq.projected_bits=(Save4U16)bits;
 if(op==RQ_CLAIM)rq.claim=1;
 return result;
}
/* Seal runs after the complete authored action, before EVENT_PENDING. Small
 * pose/identity authority was captured at its first operation; legal changes
 * in that same action are part of the final immutable Save5 snapshot. */
COLD int RQ_SEAL(void){
 if(rq.phase!=RQ_COLLECT||rq.failed||!rq_source_matches()){rq_cancel();return 0;}
 rq.revision=progression_revision;rq.chapter=chapter_flags;
 rq.token=save5_preflight_begin(&adventure_save);
 if(!rq.token){rq_cancel();return 0;}
 rq.phase=RQ_VALIDATE;return 1;
}
COLD int RQ_PENDING(void){return rq.phase!=0;}
COLD void RQ_CANCEL(void){rq_cancel();}
static COLD int rq_bound(void){
 return rq_source_matches()&&progression_revision==rq.revision&&chapter_flags==rq.chapter;
}
static COLD int rq_admission_result(enum CreatureAdmissionStatus result){
 if(creatures_admission_allowed(result))return RQ_CHANGED;
 if(result==CREATURE_ADMISSION_FULL)return RQ_FULL;
 if(result==CREATURE_ADMISSION_RESERVED||result==CREATURE_ADMISSION_COVERAGE_LOSS)return RQ_RESERVED;
 return result==CREATURE_ADMISSION_ID_EXHAUSTED?RQ_ID_EXHAUSTED:RQ_INVALID;
}
COLD unsigned RQ_PREPARE(void){const Save5State*s;EquipmentState*gear;
 unsigned status,i,st,bits;int result;
 if(!rq.phase||rq.failed||game_state!=10||!rq_bound()||save5_preflight_status(rq.token)==SAVE5_FAILED){rq_cancel();return SAVE5_FAILED;}
 if(rq.phase==RQ_READY)return SAVE5_DONE;
 if(rq.phase==RQ_VALIDATE){
  for(i=0;i<1;i++){
   status=save5_preflight_step(rq.token,1024);
   if(status==SAVE5_DONE){s=save5_preflight_snapshot(rq.token);rq.staged=(unsigned char)save5_quest_state(&s->quests,rq.q);rq.staged_bits=s->quests.objectives[rq.q];rq.cursor=rq.changed=0;rq.phase=RQ_PLAN;return SAVE5_BUSY;}
   if(status!=SAVE5_BUSY){rq_cancel();return SAVE5_FAILED;}
  }
  return SAVE5_BUSY;
 }
 s=save5_preflight_snapshot(rq.token);if(!s){rq_cancel();return SAVE5_FAILED;}
 if(rq.phase==RQ_PLAN){
  if(rq.cursor==rq.count){rq.phase=RQ_READY;return SAVE5_BUSY;}
  st=rq.staged;bits=rq.staged_bits;
  result=rq_apply(s,rq.op[rq.cursor],rq.bit[rq.cursor],&st,&bits);
  rq.staged=(unsigned char)st;rq.staged_bits=(Save4U16)bits;
  if(result==RQ_CHANGED||result==RQ_NOW_READY){rq.changed=1;
   if(rq.op[rq.cursor]==RQ_DISCOVER)rq.discovered|=rq.bit[rq.cursor];
  }
  if(rq.op[rq.cursor++]!=RQ_CLAIM)return SAVE5_BUSY;
  rq.result=result;
  if(result!=RQ_REWARDED)return SAVE5_BUSY;
  if(rq.q<RQ_FIRST+2){
   rq.admission=creatures_admission_job_begin(&s->roster,RQ_FORM(rq.q),CREATURE_EMPTY_SLOT);
   if(!rq.admission){rq_cancel();return SAVE5_FAILED;}
   rq.phase=RQ_ADMISSION;return SAVE5_BUSY;
  }
  rq.phase=RQ_ADMISSION; /* gear-only claims share the same staging phase */
 }
 if(rq.phase==RQ_ADMISSION){
  if(rq.admission){
   result=creatures_admission_job_step(rq.admission,4);
   if(result==CREATURE_ADMISSION_JOB_PENDING)return SAVE5_BUSY;
   if(result!=CREATURE_ADMISSION_JOB_COMPLETE){rq_cancel();return SAVE5_FAILED;}
   result=rq_admission_result(creatures_admission_job_result(rq.admission,0));
   /* Preserve each region's synchronous identity/capacity precedence. */
   if(RQ_ID_FIRST&&s->roster.next_instance_id==0xffffffffu)result=RQ_ID_EXHAUSTED;
   if(result==RQ_CHANGED&&s->roster.next_instance_id==0xffffffffu)result=RQ_ID_EXHAUSTED;
   if(result!=RQ_CHANGED){rq.result=result;creatures_admission_job_cancel();rq.admission=0;rq.phase=RQ_READY;return SAVE5_BUSY;}
  }
  rq.gear=(unsigned char)RQ_GEAR(rq.q);
  if(rq.gear!=255){
   gear=save5_preflight_equipment_stage(rq.token);if(!gear){rq_cancel();return SAVE5_FAILED;}
   *gear=s->equipment;
   result=equipment_claim(gear,equipment_reward_item(rq.gear),rq.gear,0);
   if(result!=EQUIPMENT_OK&&result!=EQUIPMENT_DUPLICATE&&result!=EQUIPMENT_ALREADY_CLAIMED){
    rq.result=result==EQUIPMENT_FULL?RQ_FULL:RQ_INVALID;
    if(rq.admission)creatures_admission_job_cancel();
    rq.admission=0;rq.gear=255;
   }
  }
  rq.phase=RQ_READY;return SAVE5_BUSY;
 }
 rq_cancel();return SAVE5_FAILED;
}
/* No yield from the complete live-state proof through admitted grant, staged
 * gear and receipt. Admission has its own full-roster exact comparison and
 * consumes the token even when a stale attempt fails. */
static COLD int rq_commit_patch(void){const Save5State*s;EquipmentState*gear;unsigned slot;int result;
 if(rq.phase!=RQ_READY||rq.failed||game_state!=PLAY||!rq_bound()||!save5_preflight_matches(rq.token,&adventure_save))return 0;
 s=save5_preflight_snapshot(rq.token);gear=save5_preflight_equipment_stage(rq.token);
 if(!s||!gear)return 0;
 if(rq.claim&&rq.result==RQ_REWARDED){
  if(rq.admission){
   result=rq_admission_result(creatures_admission_job_commit_grant(rq.admission,&adventure_save.roster,RQ_LEVEL(&s->roster),20,0,0,&slot));
   rq.admission=0;if(result!=RQ_CHANGED)return 0;
  }
  if(rq.gear!=255)adventure_save.equipment=*gear;
  rq.staged=SAVE5_QUEST_CLAIMED;
  adventure_save.quests.rewards[rq.q>>3]|=(Save4U8)(1u<<(rq.q&7));
  rq.changed=1;
 }
 if(RQ_DISCOVERY)adventure_save.quests.region_flags[18]|=rq.discovered;
 save5_quest_set_state(&adventure_save.quests,rq.q,rq.staged);
 adventure_save.quests.objectives[rq.q]=rq.staged_bits;
 save5_preflight_cancel();rq.token=0;return 1;
}
