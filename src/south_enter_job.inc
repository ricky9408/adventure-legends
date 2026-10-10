/* Southern entry validates the exact synchronous visit input, after the
 * engine's chapter sync / expedition reset and before any scene mutation.
 * A ready token is one-use and is never a caller-supplied validation grant. */
static struct {
 Save4U32 token;
 unsigned phase,area,spawn,revision,chapter,applied,owned;
 int source_room,source_spawn,x,y,facing,resume;
} south_enter_job;
enum { SOUTH_ENTER_IDLE, SOUTH_ENTER_PREFLIGHT, SOUTH_ENTER_READY, SOUTH_ENTER_ARMED, SOUTH_ENTER_COMMIT };
static COLD int south_enter_source_matches(void){
 return room==south_enter_job.source_room&&checkpoint_spawn==south_enter_job.source_spawn&&
  px==south_enter_job.x&&py==south_enter_job.y&&face==south_enter_job.facing&&
  chapter_flags==south_enter_job.chapter&&progression_revision==south_enter_job.revision;
}
COLD void south_game_cancel_enter(void){
 if(south_enter_job.token&&save5_preflight_status(south_enter_job.token)!=SAVE5_FAILED)
  save5_preflight_cancel();
 south_enter_job.token=0;south_enter_job.phase=SOUTH_ENTER_IDLE;south_enter_job.applied=0;
}
COLD int south_game_enter_pending(void){return south_enter_job.phase!=SOUTH_ENTER_IDLE;}
COLD int south_game_request_enter(unsigned area,unsigned spawn){
 sync();
 if(!south_game_is_room(area)||spawn>=counts[area-30]||
  !southern_can_enter(&adventure_save,area)){
  south_game_cancel_enter();return 0;
 }
 if(south_game_enter_pending()){
  if(south_enter_job.owned&&south_enter_job.phase==SOUTH_ENTER_ARMED&&area==south_enter_job.area&&
   spawn==south_enter_job.spawn&&game_state==south_enter_job.resume&&
   south_enter_source_matches()&&save5_preflight_status(south_enter_job.token)==SAVE5_DONE){
   south_enter_job.phase=SOUTH_ENTER_COMMIT;return 1;
  }
  south_game_cancel_enter();return 0;
 }
 if(south_enter_job.owned)return 0;
 south_enter_job.token=save5_preflight_begin(&adventure_save);
 if(!south_enter_job.token)return 0;
 south_enter_job.area=area;south_enter_job.spawn=spawn;
 south_enter_job.source_room=room;south_enter_job.source_spawn=checkpoint_spawn;
 south_enter_job.x=px;south_enter_job.y=py;south_enter_job.facing=face;
 south_enter_job.revision=progression_revision;south_enter_job.chapter=chapter_flags;
 south_enter_job.resume=game_state;south_enter_job.phase=SOUTH_ENTER_PREFLIGHT;return 2;
}
COLD unsigned south_game_prepare_enter(void){
 unsigned i,status;
 if(!south_game_enter_pending()||game_state!=10||!south_enter_source_matches()){
  south_game_cancel_enter();return SAVE5_FAILED;
 }
 if(south_enter_job.phase==SOUTH_ENTER_READY){
  if(save5_preflight_status(south_enter_job.token)==SAVE5_DONE)return SAVE5_DONE;
  south_game_cancel_enter();return SAVE5_FAILED;
 }
 if(south_enter_job.phase!=SOUTH_ENTER_PREFLIGHT){south_game_cancel_enter();return SAVE5_FAILED;}
 /* Each semantic step is capped in Save5. Three steps also retain the same
  * entire-state proof; native first-entry / full-roster timing certifies this
  * fixed per-update bound rather than assuming the budget is a cycle count. */
 for(i=0;i<3;++i){
  status=save5_preflight_step(south_enter_job.token,1024);
  if(status==SAVE5_DONE){
   /* Keep the last validation slice off the transition/render update. The
    * exact ready token survives; all source/snapshot checks still run. */
   south_enter_job.phase=SOUTH_ENTER_READY;return SAVE5_BUSY;
  }
  if(status!=SAVE5_BUSY){south_game_cancel_enter();return SAVE5_FAILED;}
 }
 return SAVE5_BUSY;
}
/* This function owns the entire synchronous lease. No public request can
 * arm it, and no yield separates the first exact check from enter_room.
 * The consumer still checks every saved byte after deterministic engine setup. */
COLD int south_game_commit_enter(void){
 unsigned area,spawn;int applied;
 if(south_enter_job.owned||south_enter_job.phase!=SOUTH_ENTER_READY||game_state!=south_enter_job.resume||
  !south_enter_source_matches()||!save5_preflight_matches(south_enter_job.token,&adventure_save)){
  south_game_cancel_enter();return 0;
 }
 area=south_enter_job.area;spawn=south_enter_job.spawn;
 south_enter_job.applied=0;south_enter_job.owned=1;south_enter_job.phase=SOUTH_ENTER_ARMED;
 enter_room((int)area,(int)spawn);
 applied=south_enter_job.applied&&room==(int)area&&checkpoint_spawn==(int)spawn;
 south_enter_job.owned=0;south_game_cancel_enter();return applied;
}
static COLD int south_enter_apply(unsigned area,unsigned spawn,int *result){
 unsigned bit;const Save5State *s=save5_preflight_snapshot(south_enter_job.token);
 if(!south_enter_job.owned||south_enter_job.phase!=SOUTH_ENTER_COMMIT||area!=south_enter_job.area||
  spawn!=south_enter_job.spawn||room!=(int)area||checkpoint_spawn!=(int)spawn||
  game_state!=south_enter_job.resume||face!=south_enter_job.facing||
  chapter_flags!=south_enter_job.chapter||progression_revision!=south_enter_job.revision||
  !s||!southern_can_enter(s,area)||!save5_preflight_matches(south_enter_job.token,&adventure_save)){
  south_game_cancel_enter();return 0;
 }
 /* No yield separates the complete proof from southern_visit's exact patch.
  * Original direct southern_visit and south_game_enter validation remains. */
 bit=1u<<(area-30);*result=(s->quests.region_flags[2]&bit)?SOUTH_UNCHANGED:SOUTH_CHANGED;
 adventure_save.quests.region_flags[2]|=(Save4U8)bit;
 south_game_cancel_enter();south_enter_job.applied=1;return 1;
}
