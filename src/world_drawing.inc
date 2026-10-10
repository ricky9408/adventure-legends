COLD void draw_world(void){int i;if((unsigned)room-70u<8u){copy_covenants();covenants_game_draw_overlay();}
 else if((unsigned)room-62u<8u){copy_horizons();horizons_game_draw_overlay();}
 else if((unsigned)room-54u<8u){copy_return();return_game_draw_overlay();}
 else if((unsigned)(room-46)<8u){copy_underwater();underwater_game_draw_overlay();}
 else if(((unsigned)(room-38)<8u)){copy_magma();magma_game_draw_overlay();if(room==38){int x=416-camera_x,y=224-camera_y;line(x-13,y+7,x+13,y+7,PAL_WATER4);line(x-11,y+9,x+11,y+9,PAL_WATER3);}}
 else if(south_game_is_room((unsigned)room)){copy_south();south_game_draw_overlay();}
 else if(north_game_is_room((unsigned)room)){copy_north();north_game_draw_overlay();}
 else if(region_game_is_room((unsigned)room)){copy_region();region_game_draw_overlay();}
 else if(room==1){copy_overworld();if(bridge_open){int x=WORLD_BRIDGE_X-camera_x,y=WORLD_RIVER_Y-camera_y;rect(x-2,y-2,28,24,PAL_PINE3);for(i=0;i<6;i++){rect(x-1,y-2+i*4,26,3,PAL_WOOD3);rect(x+2,y-2+i*4,20,1,GOLD);}line(x-2,y-4,x-2,y+23,GREEN);line(x+26,y-4,x+26,y+23,GREEN);}}
 else if(trials_is_room(room)){REG32(0x040000D4)=(u32)trials_background(room);REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;}
 else if(room>=4&&room<14){REG32(0x040000D4)=(u32)campaign_backgrounds[room-4];REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;}else copy_bg(room);
 if(room==2){if(torches!=3){rect(99,27,42,13,INK);for(i=101;i<141;i+=6)rect(i,27,2,15,GOLD);}else{rect(108,25,24,9,INK);line(108,33,132,33,GOLD);}}
 if(room>=4&&room<14)draw_campaign_background();
 if(room==0||room==16||room==17||room==18||room==20||room==22||room==30||room==38||room==46)return_game_draw_old_overlay();
 if(room==60||room==61)horizons_game_draw_old_overlay();
 if(room==0||room==62)covenants_game_draw_old_overlay();
 trials_draw_background(room,camera_x,camera_y);
 feedback_world_draw((unsigned)room,camera_x,camera_y);
 /* Fences are world pixels and must belong to the cached notice underlay. */
 game_roads_draw();
 if(game_state==PLAY&&area_ticks){int x=(240-ui_texts[room_name()].width)/2;text(room_name(),x+1,23,INK);text(room_name(),x,22,CREAM);}
 capture_play_strip();
}
