/* One typed branch-grant transaction, sharing the immutable Save5 snapshot.
 * All yielded phases are read-only. Only the exact compare + one-use admitted
 * grant + infallible receipt phase mutates state. Historical synchronous APIs
 * retain their validation and migrations; live repeat invitations use this. */
static struct {
 Save5State *live;
 Save4U32 token,scene;
 CreatureU32 admission_token;
 unsigned source,status,phase;
 int result;
} magma_recruit_job;
void magma_recruit_job_cancel(void){
 /* A revoked token can no longer own the shared admission cursor/scratch. */
 if(magma_recruit_job.token&&save5_preflight_status(magma_recruit_job.token)!=SAVE5_FAILED){
  if(magma_recruit_job.admission_token)creatures_admission_job_cancel();
  save5_preflight_cancel();
 }
 magma_recruit_job.token=0;magma_recruit_job.live=0;
 magma_recruit_job.admission_token=0;magma_recruit_job.status=SAVE5_IDLE;
 magma_recruit_job.result=MAGMA_INVALID;
}
static void magma_recruit_fail(void){magma_recruit_job_cancel();magma_recruit_job.status=SAVE5_FAILED;}
Save4U32 magma_recruit_job_begin(Save5State*s,unsigned source,CreatureU32 scene){
 Save4U32 token;unsigned i=source_index(source);
 if(!s||!scene||i<2||i>=6||magma_recruit_job.status==SAVE5_BUSY)return 0;
 token=save5_preflight_begin(s);if(!token)return 0;
 magma_recruit_job.live=s;magma_recruit_job.token=token;magma_recruit_job.scene=scene;
 magma_recruit_job.source=source;magma_recruit_job.admission_token=0;
 magma_recruit_job.status=SAVE5_BUSY;magma_recruit_job.phase=0;
 magma_recruit_job.result=MAGMA_INVALID;return token;
}
unsigned magma_recruit_job_status(Save4U32 token){
 return token&&token==magma_recruit_job.token?magma_recruit_job.status:SAVE5_FAILED;
}
unsigned magma_recruit_job_phase(Save4U32 token){
 return token&&token==magma_recruit_job.token?magma_recruit_job.phase:255;
}
int magma_recruit_job_result(Save4U32 token){
 return magma_recruit_job_status(token)==SAVE5_DONE?magma_recruit_job.result:MAGMA_INVALID;
}
unsigned magma_recruit_job_step(Save4U32 token,unsigned budget,CreatureU32 scene){
 const Save5State*s;unsigned status,slot,i;int result;
 if(magma_recruit_job_status(token)!=SAVE5_BUSY)return magma_recruit_job_status(token);
 if(!scene||scene!=magma_recruit_job.scene||save5_preflight_status(token)==SAVE5_FAILED){
  magma_recruit_fail();return SAVE5_FAILED;
 }
 if(!budget)return SAVE5_BUSY;
 if(!magma_recruit_job.phase){
  status=save5_preflight_step(token,budget);
  if(status==SAVE5_DONE)magma_recruit_job.phase=1;
  else if(status!=SAVE5_BUSY)magma_recruit_fail();
  return magma_recruit_job.status;
 }
 s=save5_preflight_snapshot(token);if(!s){magma_recruit_fail();return SAVE5_FAILED;}
 i=source_index(magma_recruit_job.source);
 switch(magma_recruit_job.phase){
 case 1:
  if(!magma_branch_hint_available(s,magma_recruit_job.source)){
   magma_recruit_job.result=MAGMA_LOCKED;magma_recruit_job.phase=3;break;
  }
  magma_recruit_job.admission_token=creatures_admission_job_begin(&s->roster,forms[i],CREATURE_EMPTY_SLOT);
  if(!magma_recruit_job.admission_token)magma_recruit_fail();else magma_recruit_job.phase=2;
  break;
 case 2:
  result=creatures_admission_job_step(magma_recruit_job.admission_token,4);
  if(result==CREATURE_ADMISSION_JOB_PENDING)break;
  if(result!=CREATURE_ADMISSION_JOB_COMPLETE){magma_recruit_fail();break;}
  result=admission_result(creatures_admission_job_result(magma_recruit_job.admission_token,0));
  if(result==MAGMA_CHANGED&&s->roster.next_instance_id==0xffffffffu)result=MAGMA_ID_EXHAUSTED;
  magma_recruit_job.result=result==MAGMA_CHANGED?MAGMA_REWARDED:result;
  if(result!=MAGMA_CHANGED){creatures_admission_job_cancel();magma_recruit_job.admission_token=0;}
  magma_recruit_job.phase=3;break;
 case 3:
  if(!save5_preflight_matches(token,magma_recruit_job.live)){magma_recruit_fail();break;}
  if(magma_recruit_job.admission_token){
   result=admission_result(creatures_admission_job_commit_grant(magma_recruit_job.admission_token,
    &magma_recruit_job.live->roster,magma_recruit_level(&s->roster),20,0,0,&slot));
   magma_recruit_job.admission_token=0;
   if(result!=MAGMA_CHANGED){magma_recruit_fail();break;}
   magma_recruit_job.live->quests.region_flags[16]|=(Save4U8)(1u<<(i-2));
  }
  save5_preflight_cancel();magma_recruit_job.status=SAVE5_DONE;break;
 default:magma_recruit_fail();break;
 }
 return magma_recruit_job.status;
}
