/* Rest validates the exact old checkpoint using the existing Save5 scratch.
 * No anchor bit, heal or checkpoint is applied until bounded full validation
 * and an exact live-state comparison have both succeeded. */
static struct {
 Save4U32 token;
 unsigned phase,revision,chapter;
 int area,spawn,x,y,facing;
} south_rest_job;
enum { SOUTH_REST_IDLE, SOUTH_REST_PREFLIGHT, SOUTH_REST_READY };
static int south_rest_source_matches(void){
 return room==south_rest_job.area&&checkpoint_spawn==south_rest_job.spawn&&
  px==south_rest_job.x&&py==south_rest_job.y&&face==south_rest_job.facing&&
  chapter_flags==south_rest_job.chapter&&progression_revision==south_rest_job.revision;
}
void south_game_cancel_rest(void){
 if(south_rest_job.token&&save5_preflight_status(south_rest_job.token)!=SAVE5_FAILED)
  save5_preflight_cancel();
 south_rest_job.token=0;south_rest_job.phase=SOUTH_REST_IDLE;
}
int south_game_rest_pending(void){return south_rest_job.phase!=SOUTH_REST_IDLE;}
COLD int south_game_request_rest(void){
 unsigned bit;
 if(south_game_rest_pending()){
  if(south_rest_source_matches())return 1;
  south_game_cancel_rest();return 0;
 }
 if(game_state!=PLAY||(room!=30&&room!=31)||
  !close(room==30?112:80,room==30?208:248)||
  adventure_save.campaign.room!=room||adventure_save.campaign.spawn!=checkpoint_spawn||
  adventure_save.campaign.chapter_flags!=chapter_flags)return 0;
 bit=1u<<(room-30);
 if(!southern_can_enter(&adventure_save,(unsigned)room)||
  !(adventure_save.quests.region_flags[2]&bit))return 0;
 south_rest_job.token=save5_preflight_begin(&adventure_save);
 if(!south_rest_job.token)return 0;
 south_rest_job.area=room;south_rest_job.spawn=checkpoint_spawn;
 south_rest_job.x=px;south_rest_job.y=py;south_rest_job.facing=face;
 south_rest_job.chapter=chapter_flags;south_rest_job.revision=progression_revision;
 south_rest_job.phase=SOUTH_REST_PREFLIGHT;return 1;
}
COLD unsigned south_game_prepare_rest(void){
 unsigned status;
 if(!south_game_rest_pending())return SAVE5_FAILED;
 if(game_state!=10||!south_rest_source_matches()){south_game_cancel_rest();return SAVE5_FAILED;}
 if(south_rest_job.phase==SOUTH_REST_READY){
  if(save5_preflight_status(south_rest_job.token)==SAVE5_DONE)return SAVE5_DONE;
  south_game_cancel_rest();return SAVE5_FAILED;
 }
 status=save5_preflight_step(south_rest_job.token,1024);
 if(status==SAVE5_DONE)south_rest_job.phase=SOUTH_REST_READY;
 else if(status!=SAVE5_BUSY){south_game_cancel_rest();return SAVE5_FAILED;}
 return status;
}
COLD int south_game_commit_rest(void){
 const Save5State*s;unsigned bit;
 if(south_rest_job.phase!=SOUTH_REST_READY||game_state!=PLAY||!south_rest_source_matches()){
  south_game_cancel_rest();return 0;
 }
 s=save5_preflight_snapshot(south_rest_job.token);bit=1u<<(south_rest_job.area-30);
 if(!s||!southern_can_enter(s,(unsigned)south_rest_job.area)||!(s->quests.region_flags[2]&bit)||
  !save5_preflight_matches(south_rest_job.token,&adventure_save)){
  south_game_cancel_rest();return 0;
 }
 /* The snapshot has passed the complete current Save5 policy, including the
  * Southern town gate. This is exactly southern_anchor's typed bit operation,
  * not an unvalidated shortcut or a caller-supplied trusted flag. No yield or
  * fallible operation separates comparison from this deterministic patch. */
 adventure_save.quests.anchors[2]|=(Save4U8)bit;
 south_game_cancel_rest();
 game_health_fill();checkpoint_spawn=2;dirty=1;
 say(TX_ST_REST_A,TX_ST_REST_B);return 1;
}
