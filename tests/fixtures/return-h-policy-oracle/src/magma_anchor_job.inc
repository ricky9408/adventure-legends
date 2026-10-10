/* Bounded equivalent of the existing deferred magma_anchor call. The rest
 * already warmed both SAVE_PENDING pages and retained its old legal spawn.
 * One shared preflight snapshot, no second state copy or weakened validator. */
static int magma_anchor_source_matches(void){
 return game_state==6&&(pending_anchor_area==38||pending_anchor_area==39)&&
  (unsigned)room==pending_anchor_area&&adventure_save.campaign.room==pending_anchor_area&&
  checkpoint_spawn==3&&adventure_save.campaign.spawn==pending_anchor_spawn&&
  px==magma_anchor_job.x&&py==magma_anchor_job.y&&face==magma_anchor_job.facing&&
  chapter_flags==magma_anchor_job.chapter&&progression_revision==magma_anchor_job.revision&&
  magma_scene==magma_anchor_job.scene;
}
COLD unsigned magma_game_prepare_save_step(void){
 unsigned status,i,bit;const Save5State*s;
 if(!pending_anchor_area){cancel_anchor_job();return SAVE5_FAILED;}
 if(!magma_anchor_job.phase){
  if(game_state!=6||(pending_anchor_area!=38&&pending_anchor_area!=39)||
   (unsigned)room!=pending_anchor_area||adventure_save.campaign.room!=pending_anchor_area||
   checkpoint_spawn!=3||adventure_save.campaign.spawn!=pending_anchor_spawn){cancel_anchor_prepare();return SAVE5_FAILED;}
  magma_anchor_job.token=save5_preflight_begin(&adventure_save);
  if(!magma_anchor_job.token){cancel_anchor_prepare();return SAVE5_FAILED;}
  magma_anchor_job.x=px;magma_anchor_job.y=py;magma_anchor_job.facing=face;
  magma_anchor_job.chapter=chapter_flags;magma_anchor_job.revision=progression_revision;
  magma_anchor_job.scene=magma_scene;magma_anchor_job.phase=1;return SAVE5_BUSY;
 }
 if(!magma_anchor_source_matches()){cancel_anchor_prepare();return SAVE5_FAILED;}
 if(magma_anchor_job.phase==1){
  for(i=0;i<3;i++){
   status=save5_preflight_step(magma_anchor_job.token,1024);
   if(status==SAVE5_DONE){magma_anchor_job.phase=2;return SAVE5_BUSY;}
   if(status!=SAVE5_BUSY){cancel_anchor_prepare();return SAVE5_FAILED;}
  }
  return SAVE5_BUSY;
 }
 s=save5_preflight_snapshot(magma_anchor_job.token);bit=1u<<(pending_anchor_area-38);
 if(magma_anchor_job.phase!=2||!s||!magma_can_enter(s,pending_anchor_area)||
  !(s->quests.region_flags[3]&1u)||!(s->quests.region_flags[3]&bit)||
  !save5_preflight_matches(magma_anchor_job.token,&adventure_save)){
  cancel_anchor_prepare();return SAVE5_FAILED;
 }
 /* Same complete validation, town/visited gate and bit as magma_anchor.
  * No yield/fallible call separates exact comparison from this typed patch. */
 adventure_save.quests.anchors[3]|=(Save4U8)bit;
 cancel_anchor_job();pending_anchor_area=0;adventure_save.campaign.spawn=3;
 return SAVE5_DONE;
}
