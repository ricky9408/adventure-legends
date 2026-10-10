#include "story_rewards.h"
static struct {
 Save5State *live;
 Save4U32 save_token;
 CreatureU32 story_token;
 unsigned chapters;
 unsigned char phase;
} reward;
unsigned story_rewards_state_bytes(void){return sizeof reward;}
void story_rewards_cancel(void){
 if(reward.save_token&&save5_preflight_status(reward.save_token)!=SAVE5_FAILED){
  if(reward.story_token)creatures_story_job_cancel(reward.story_token);
  save5_preflight_cancel();
 }
 reward.live=0;reward.save_token=reward.story_token=0;reward.phase=0;
}
int story_rewards_begin(Save5State *live,unsigned chapters){
 if(!live||reward.phase)return 0;
 reward.live=live;reward.chapters=chapters;reward.save_token=reward.story_token=0;reward.phase=1;return 1;
}
int story_rewards_pending(void){return reward.phase!=0;}
unsigned story_rewards_step(void){
 const Save5State*s;unsigned status;
 if(!reward.phase)return SAVE5_DONE;
 switch(reward.phase){
 case 1:
  reward.save_token=save5_preflight_begin(reward.live);
  if(!reward.save_token)break;
  reward.phase=2;return SAVE5_BUSY;
 case 2:
  status=save5_preflight_step(reward.save_token,480);
  if(status==SAVE5_BUSY)return status;
  if(status!=SAVE5_DONE)break;
  reward.phase=3;return SAVE5_BUSY;
 case 3:
  s=save5_preflight_snapshot(reward.save_token);if(!s)break;
  reward.story_token=creatures_story_job_begin(&s->roster,reward.chapters);
  if(!reward.story_token)break;
  reward.phase=4;return SAVE5_BUSY;
 case 4:
  if(save5_preflight_status(reward.save_token)!=SAVE5_DONE)break;
  status=(unsigned)creatures_admission_job_step(reward.story_token,4);
  if(status==CREATURE_ADMISSION_JOB_PENDING)return SAVE5_BUSY;
  if(status!=CREATURE_ADMISSION_JOB_COMPLETE||creatures_admission_job_result(reward.story_token,0)==CREATURE_ADMISSION_INVALID)break;
  reward.phase=5;return SAVE5_BUSY;
 case 5:
  if(!save5_preflight_matches(reward.save_token,reward.live)||!creatures_story_job_commit(reward.story_token,&reward.live->roster))break;
  reward.story_token=0;story_rewards_cancel();return SAVE5_DONE;
 default:break;
 }
 story_rewards_cancel();return SAVE5_FAILED;
}
