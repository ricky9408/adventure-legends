/* Exact authored second-A branch invitation, frozen by the engine while its
 * typed transaction advances. No reward, save or invitation consumption until
 * the terminal grant. The source pose and scene cannot be redirected. */
static CreatureU32 magma_scene=1;
static struct {
 Save4U32 token;
 CreatureU32 scene;
 unsigned source,revision,chapter,status;
 int area,x,y,facing,spawn,result;
} magma_recruit_event;
int magma_game_event_pending(void){return magma_recruit_event.token!=0;}
void magma_game_cancel_event(void){
 if(magma_recruit_event.token){
  unsigned bit=1u<<(magma_recruit_event.source-MAGMA_SOURCE_FIELD_0);
  magma_recruit_job_cancel();second&=(unsigned char)~bit;
  if(magma_recruit_event.source==MAGMA_SOURCE_FIELD_1)spill=0;
 }
 magma_recruit_event.token=0;
}
static int magma_recruit_bound(void){
 return magma_recruit_event.scene==magma_scene&&room==magma_recruit_event.area&&
  px==magma_recruit_event.x&&py==magma_recruit_event.y&&face==magma_recruit_event.facing&&
  checkpoint_spawn==magma_recruit_event.spawn&&chapter_flags==magma_recruit_event.chapter&&
  progression_revision==magma_recruit_event.revision;
}
static int magma_queue_recruit(unsigned source){
 Save4U32 token;
 if(magma_game_event_pending())return 1;
 if(source<MAGMA_SOURCE_FIELD_0||source>MAGMA_SOURCE_FIELD_3||!magma_scene)return 0;
 token=magma_recruit_job_begin(&adventure_save,source,magma_scene);if(!token)return 0;
 magma_recruit_event.token=token;magma_recruit_event.scene=magma_scene;magma_recruit_event.source=source;
 magma_recruit_event.area=room;magma_recruit_event.x=px;magma_recruit_event.y=py;
 magma_recruit_event.facing=face;magma_recruit_event.spawn=checkpoint_spawn;
 magma_recruit_event.chapter=chapter_flags;magma_recruit_event.revision=progression_revision;
 magma_recruit_event.status=SAVE5_BUSY;magma_recruit_event.result=MAGMA_INVALID;return 1;
}
COLD unsigned magma_game_prepare_event(void){
 unsigned status;
 if(!magma_game_event_pending()||game_state!=10||!magma_recruit_bound()){
  magma_game_cancel_event();return SAVE5_FAILED;
 }
 status=magma_recruit_job_step(magma_recruit_event.token,640,magma_recruit_event.scene);
 if(status==SAVE5_BUSY)return status;
 if(status!=SAVE5_DONE){magma_game_cancel_event();return SAVE5_FAILED;}
 magma_recruit_event.result=magma_recruit_job_result(magma_recruit_event.token);
 magma_recruit_event.status=SAVE5_DONE;return SAVE5_DONE;
}
/* Called by the engine immediately after restoring PLAY. The transaction has
 * already committed on its final bounded step; this only presents the result. */
COLD int magma_game_commit_event(void){
 unsigned source;int r;
 if(!magma_game_event_pending()||magma_recruit_event.status!=SAVE5_DONE||game_state!=PLAY||
    !magma_recruit_bound()){magma_game_cancel_event();return 0;}
 source=magma_recruit_event.source;r=magma_recruit_event.result;
 magma_recruit_job_cancel();magma_recruit_event.token=0;
 if(r==MAGMA_REWARDED){
  second&=(unsigned char)~(1u<<(source-MAGMA_SOURCE_FIELD_0));
  if(source==MAGMA_SOURCE_FIELD_1)spill=0;
  dirty=1;progression_refresh();persist();toast(TX_MG_RECRUITED);
 }else result(r);
 return 1;
}
