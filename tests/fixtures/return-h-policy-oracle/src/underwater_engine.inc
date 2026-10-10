/* Main-engine scheduling/render bridges. Cold helpers stay in ROM. */
static int event_resume_state,event_warmup;
COLD int event_frame(void){
 if(game_state==EVENT_PENDING)return 1;
 if(game_state==SAVE_PENDING||!(south_game_enter_pending()||magma_game_enter_pending()||return_game_event_pending()||magma_game_event_pending()||underwater_game_event_pending()||magma_game_return_pending()||south_game_rest_pending()))return 0;
 event_resume_state=game_state;event_warmup=2;game_attacks_suspend();
 game_state=EVENT_PENDING;return 1;
}
COLD void event_step(void){
 unsigned status,area,spawn;int returning,resting,homeward,branch,entering,magma_entering;
 if((pressed&KEY_B)&&magma_game_event_pending()){magma_game_cancel_event();game_state=event_resume_state;return;}
 if(event_warmup){event_warmup--;return;}
 entering=south_game_enter_pending();magma_entering=magma_game_enter_pending();homeward=return_game_event_pending();branch=magma_game_event_pending();returning=magma_game_return_pending();resting=south_game_rest_pending();
 status=entering?south_game_prepare_enter():magma_entering?magma_game_prepare_enter():homeward?return_game_prepare_event():returning?magma_game_prepare_return():resting?south_game_prepare_rest():branch?magma_game_prepare_event():underwater_game_prepare_event();if(status==SAVE5_BUSY)return;
 game_state=event_resume_state;
 if(status==SAVE5_FAILED){save_failed=save_failure_notice=1;toast(TX_UW_NOT_YET);return;}
 if(entering){if(!south_game_commit_enter()){save_failed=save_failure_notice=1;toast(TX_UW_NOT_YET);return;}}
 else if(magma_entering){if(!magma_game_commit_enter()){save_failed=save_failure_notice=1;toast(TX_UW_NOT_YET);return;}}
 else if(homeward){if(return_game_take_transition(&area,&spawn))enter_room((int)area,(int)spawn);}
 else if(returning){if(!magma_game_commit_return()){save_failed=save_failure_notice=1;toast(TX_UW_NOT_YET);return;}}
 else if(resting){if(!south_game_commit_rest()){save_failed=save_failure_notice=1;toast(TX_UW_NOT_YET);return;}}
 else if(branch){if(!magma_game_commit_event()){save_failed=save_failure_notice=1;toast(TX_UW_NOT_YET);return;}}
 else if(underwater_game_take_transition(&area,&spawn))enter_room((int)area,(int)spawn);
 save_frame();
}
COLD int underwater_portal_interact(void){if(room!=38||!near(px,py,416,224,23)||!game_region_entry_safe())return 0;if(!underwater_game_can_enter(46)){dialogue(TX_UW_PORTAL_WAIT_A,TX_UW_PORTAL_WAIT_B,PLAY);return 1;}enter_room(46,0);return 1;}
COLD int underwater_hint_text(void){unsigned h=underwater_powers_hint();return h==1?TX_UW_AIM_SIDE:h==2?TX_UW_AIM_CORNER:h==3?TX_UW_AIM_AXIS:0;}
COLD void copy_underwater(void){const UnderwaterArtRoom*r=&underwater_art_rooms[room-46];int y;if(COPY_OPAQUE_MODAL_BITMAP&&copy_modal_background(r->bitmap,r->bitmap_odd,r->width))return;if(r->width==240){REG32(0x040000D4)=(u32)r->bitmap;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}for(y=0;y<160;y++){const u8*src=((camera_x&1)?r->bitmap_odd:r->bitmap)+(camera_y+y)*r->width+camera_x-(camera_x&1);REG32(0x040000D4)=(u32)src;REG32(0x040000D8)=(u32)(screen+y*120);REG32(0x040000DC)=0x80000000|120;}}
COLD void draw_underwater_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(underwater_game_name(),35,GOLD);rect(mx,my,120,80,PAL_WATER3);rect(mx+12,my+12,96,56,PAL_STONE4);for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;rect(x,y,10,10,(adventure_save.quests.region_flags[4]&(1u<<i))?GOLD:PAL_STONE2);if(room==46+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
