/* Magma entry validates the exact synchronous visit input, after the
 * engine's chapter sync / expedition reset and before any scene mutation.
 * A ready token is one-use and is never a caller-supplied validation grant. */
static struct {
 Save4U32 token;
 unsigned phase,area,spawn,revision,chapter,applied,owned,scene;
 int source_room,source_spawn,x,y,facing,resume;
} magma_enter_job;
enum { MAGMA_ENTER_IDLE, MAGMA_ENTER_PREFLIGHT, MAGMA_ENTER_READY, MAGMA_ENTER_ARMED, MAGMA_ENTER_COMMIT };
static COLD int magma_enter_source_matches(void){
 return magma_scene==magma_enter_job.scene&&room==magma_enter_job.source_room&&checkpoint_spawn==magma_enter_job.source_spawn&&
  px==magma_enter_job.x&&py==magma_enter_job.y&&face==magma_enter_job.facing&&
  chapter_flags==magma_enter_job.chapter&&progression_revision==magma_enter_job.revision;
}
COLD void magma_game_cancel_enter(void){
 if(magma_enter_job.token&&save5_preflight_status(magma_enter_job.token)!=SAVE5_FAILED)
  save5_preflight_cancel();
 magma_enter_job.token=0;magma_enter_job.phase=MAGMA_ENTER_IDLE;magma_enter_job.applied=0;
}
COLD int magma_game_enter_pending(void){return magma_enter_job.phase!=MAGMA_ENTER_IDLE;}
COLD int magma_game_request_enter(unsigned area,unsigned spawn){
 /* This exact crossing already has its own source-bound shell-lift owner.
  * Never let a direct generic request create a second pending operation. */
 if(room==46&&area==38&&spawn==4){magma_game_cancel_enter();return 0;}
 sync();
 if(!magma_game_is_room(area)||spawn>=magma_game_spawn_count(area)||
  !magma_can_enter(&adventure_save,area)||(area==38&&spawn==4&&!(adventure_save.quests.region_flags[4]&1))){
  magma_game_cancel_enter();return 0;
 }
 if(magma_game_enter_pending()){
  if(magma_enter_job.owned&&magma_enter_job.phase==MAGMA_ENTER_ARMED&&area==magma_enter_job.area&&
   spawn==magma_enter_job.spawn&&game_state==magma_enter_job.resume&&
   magma_enter_source_matches()&&save5_preflight_status(magma_enter_job.token)==SAVE5_DONE){
   magma_enter_job.phase=MAGMA_ENTER_COMMIT;return 1;
  }
  magma_game_cancel_enter();return 0;
 }
 if(magma_enter_job.owned)return 0;
 magma_enter_job.token=save5_preflight_begin(&adventure_save);
 if(!magma_enter_job.token)return 0;
 magma_enter_job.area=area;magma_enter_job.spawn=spawn;magma_enter_job.scene=magma_scene;
 magma_enter_job.source_room=room;magma_enter_job.source_spawn=checkpoint_spawn;
 magma_enter_job.x=px;magma_enter_job.y=py;magma_enter_job.facing=face;
 magma_enter_job.revision=progression_revision;magma_enter_job.chapter=chapter_flags;
 magma_enter_job.resume=game_state;magma_enter_job.phase=MAGMA_ENTER_PREFLIGHT;return 2;
}
COLD unsigned magma_game_prepare_enter(void){
 unsigned i,status;
 if(!magma_game_enter_pending()||game_state!=10||!magma_enter_source_matches()){
  magma_game_cancel_enter();return SAVE5_FAILED;
 }
 if(magma_enter_job.phase==MAGMA_ENTER_READY){
  if(save5_preflight_status(magma_enter_job.token)==SAVE5_DONE)return SAVE5_DONE;
  magma_game_cancel_enter();return SAVE5_FAILED;
 }
 if(magma_enter_job.phase!=MAGMA_ENTER_PREFLIGHT){magma_game_cancel_enter();return SAVE5_FAILED;}
 /* Each semantic step is capped in Save5. Three steps also retain the same
  * entire-state proof; native first-entry / full-roster timing certifies this
  * fixed per-update bound rather than assuming the budget is a cycle count. */
 for(i=0;i<3;++i){
  status=save5_preflight_step(magma_enter_job.token,1024);
  if(status==SAVE5_DONE){
   /* Keep the last validation slice off the transition/render update. The
    * exact ready token survives; all source/snapshot checks still run. */
   magma_enter_job.phase=MAGMA_ENTER_READY;return SAVE5_BUSY;
  }
  if(status!=SAVE5_BUSY){magma_game_cancel_enter();return SAVE5_FAILED;}
 }
 return SAVE5_BUSY;
}
/* This function owns the entire synchronous lease. No public request can
 * arm it, and no yield separates the first exact check from enter_room.
 * The consumer still checks every saved byte after deterministic engine setup. */
COLD int magma_game_commit_enter(void){
 unsigned area,spawn;int applied;
 if(magma_enter_job.owned||magma_enter_job.phase!=MAGMA_ENTER_READY||game_state!=magma_enter_job.resume||
  !magma_enter_source_matches()||!save5_preflight_matches(magma_enter_job.token,&adventure_save)){
  magma_game_cancel_enter();return 0;
 }
 area=magma_enter_job.area;spawn=magma_enter_job.spawn;
 magma_enter_job.applied=0;magma_enter_job.owned=1;magma_enter_job.phase=MAGMA_ENTER_ARMED;
 enter_room((int)area,(int)spawn);
 applied=magma_enter_job.applied&&room==(int)area&&checkpoint_spawn==(int)spawn;
 magma_enter_job.owned=0;magma_game_cancel_enter();return applied;
}
static COLD int magma_enter_apply(unsigned area,unsigned spawn,int *result){
 unsigned bit;const Save5State *s=save5_preflight_snapshot(magma_enter_job.token);
 if(!magma_enter_job.owned||magma_enter_job.phase!=MAGMA_ENTER_COMMIT||area!=magma_enter_job.area||
  spawn!=magma_enter_job.spawn||room!=(int)area||checkpoint_spawn!=(int)spawn||
  game_state!=magma_enter_job.resume||face!=magma_enter_job.facing||magma_scene!=magma_enter_job.scene||
  chapter_flags!=magma_enter_job.chapter||progression_revision!=magma_enter_job.revision||
  !s||!magma_can_enter(s,area)||(area==38&&spawn==4&&!(s->quests.region_flags[4]&1))||!save5_preflight_matches(magma_enter_job.token,&adventure_save)){
  magma_game_cancel_enter();return 0;
 }
 /* No yield separates the complete proof from magma_visit's exact patch.
  * Original direct magma_visit and magma_game_enter validation remains. */
 bit=1u<<(area-38);*result=(s->quests.region_flags[3]&bit)?MAGMA_UNCHANGED:MAGMA_CHANGED;
 adventure_save.quests.region_flags[3]|=(Save4U8)bit;
 magma_game_cancel_enter();magma_enter_job.applied=1;return 1;
}
