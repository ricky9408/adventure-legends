/* The shell-lift return is a bounded read-only validation of the exact old
 * checkpoint. It owns the existing Save5 scratch, never a second state copy.
 * The only privileged path is a one-use private lease scoped synchronously to
 * our call of enter_room. Direct magma_game_enter callers still validate. */
static struct {
 Save4U32 token;
 unsigned phase, revision, chapter;
 int source_room,source_spawn,x,y,resume_state;
 unsigned char applying;
} magma_return_job;
enum { MAGMA_RETURN_IDLE, MAGMA_RETURN_PREFLIGHT, MAGMA_RETURN_READY };
static int magma_return_source_matches(void){
 return room==magma_return_job.source_room&&checkpoint_spawn==magma_return_job.source_spawn&&
  px==magma_return_job.x&&py==magma_return_job.y&&chapter_flags==magma_return_job.chapter&&
  progression_revision==magma_return_job.revision;
}
void magma_game_cancel_return(void){
 if(magma_return_job.token&&save5_preflight_status(magma_return_job.token)!=SAVE5_FAILED)
  save5_preflight_cancel();
 magma_return_job.token=0;magma_return_job.phase=MAGMA_RETURN_IDLE;
 magma_return_job.applying=0;
}
int magma_game_return_pending(void){return magma_return_job.phase!=MAGMA_RETURN_IDLE;}
COLD int magma_game_request_return(void){
 if(magma_return_job.applying==1){
  if(!magma_return_source_matches()||game_state!=magma_return_job.resume_state)return 0;
  magma_return_job.applying=2;return 1;
 }
 if(magma_return_job.applying)return 0;
 if(magma_return_job.phase!=MAGMA_RETURN_IDLE){
  if(magma_return_source_matches())return 2;
  magma_game_cancel_return();return 0;
 }
 if(room!=46||game_state!=PLAY||adventure_save.campaign.room!=46||
  adventure_save.campaign.spawn!=checkpoint_spawn||adventure_save.campaign.chapter_flags!=chapter_flags||
  !(adventure_save.quests.region_flags[3]&1)||!(adventure_save.quests.region_flags[4]&1)||
  !magma_can_enter(&adventure_save,38))return 0;
 magma_return_job.token=save5_preflight_begin(&adventure_save);
 if(!magma_return_job.token)return 0;
 magma_return_job.source_room=room;magma_return_job.source_spawn=checkpoint_spawn;
 magma_return_job.x=px;magma_return_job.y=py;magma_return_job.resume_state=game_state;
 magma_return_job.chapter=chapter_flags;magma_return_job.revision=progression_revision;
 magma_return_job.phase=MAGMA_RETURN_PREFLIGHT;return 2;
}
COLD unsigned magma_game_prepare_return(void){
 unsigned status;
 if(!magma_game_return_pending())return SAVE5_FAILED;
 if(!magma_return_source_matches()||game_state!=10){magma_game_cancel_return();return SAVE5_FAILED;}
 if(magma_return_job.phase==MAGMA_RETURN_READY){
  if(save5_preflight_status(magma_return_job.token)==SAVE5_DONE)return SAVE5_DONE;
  magma_game_cancel_return();return SAVE5_FAILED;
 }
 status=save5_preflight_step(magma_return_job.token,1024);
 if(status==SAVE5_DONE)magma_return_job.phase=MAGMA_RETURN_READY;
 else if(status!=SAVE5_BUSY){magma_game_cancel_return();return SAVE5_FAILED;}
 return status;
}
/* Called only after restoring the frozen operation's original engine mode.
 * Exact comparison is immediately adjacent to the deterministic transition;
 * no yield or callback can retain the lease after this function returns. */
COLD int magma_game_commit_return(void){
 int applied;
 if(magma_return_job.phase!=MAGMA_RETURN_READY||game_state!=magma_return_job.resume_state||
  !magma_return_source_matches()||!save5_preflight_matches(magma_return_job.token,&adventure_save)){
  magma_game_cancel_return();return 0;
 }
 save5_preflight_cancel();magma_return_job.token=0;magma_return_job.phase=MAGMA_RETURN_IDLE;
 magma_return_job.applying=1;enter_room(38,4);
 applied=magma_return_job.applying==3&&room==38&&checkpoint_spawn==4;
 magma_return_job.applying=0;return applied;
}
static int magma_return_consume(unsigned area,unsigned spawn){
 if(magma_return_job.applying!=2||area!=38||spawn!=4||room!=38||checkpoint_spawn!=4)return 0;
 magma_return_job.applying=3;return 1;
}
