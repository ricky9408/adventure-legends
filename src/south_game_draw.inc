/* Included by south_game.c: renderer uses the parent's bounded region cache. */
COLD void south_game_draw_actors(void){unsigned i;
if(!south_game_is_room((unsigned)room))return;
if(room==30){south_actor(SOUTH_SPR_GUIDE,144,160);
south_actor(SOUTH_SPR_TAILOR,112,160);
south_actor(SOUTH_SPR_MARKET,312,176);
south_actor(SOUTH_SPR_RAIN,64,208);
south_actor(SOUTH_SPR_PORTER,352,224);
south_actor(SOUTH_SPR_CURATOR,400,192);
south_actor(SOUTH_SPR_GUIDE,48,160);
south_actor((adventure_save.quests.anchors[2]&1)?SOUTH_SPR_REST_LIT:SOUTH_SPR_REST,112,208);
south_actor(SOUTH_SPR_FERRY,240,264);
south_actor(demo?SOUTH_SPR_MIRROR_BACK:SOUTH_SPR_MIRROR_SLASH,192,176);
south_actor(quiet?SOUTH_SPR_SHADE_OPEN:SOUTH_SPR_CLOCK,240,176);
south_actor(SOUTH_SPR_TRIAL,432,208);
if(!hood&&!(adventure_save.quests.objectives[22]&2))south_actor(SOUTH_SPR_HOOD,192,240);
if(adventure_save.quests.objectives[22]&2)south_actor(SOUTH_SPR_DONE,192,208);
for(i=0;i<3;i++)south_actor((adventure_save.quests.objectives[25]&(1u<<i))?SOUTH_SPR_SHADE_OPEN:SOUTH_SPR_SHADE_CLOSED,280+(int)i*32,208);
if(adventure_save.quests.objectives[26]&1)south_actor(SOUTH_SPR_DONE,144,128);
if(adventure_save.quests.objectives[26]&2)south_actor(SOUTH_SPR_DONE,320,128);
if(adventure_save.quests.objectives[27]&1)south_actor(SOUTH_SPR_DONE,128,248);
if(adventure_save.quests.objectives[27]&2)south_actor(SOUTH_SPR_DONE,384,248);
if(!done(22))region_form_actor(79,176,160);
if(done(24))south_actor(SOUTH_SPR_BEACON,400,216);
}else if(room==31){south_actor(SOUTH_SPR_CURATOR,352,160);
south_actor((adventure_save.quests.anchors[2]&2)?SOUTH_SPR_REST_LIT:SOUTH_SPR_REST,80,248);
south_actor(SOUTH_SPR_TRIAL,240,240);
south_actor(panels&1?SOUTH_SPR_SHADE_OPEN:SOUTH_SPR_SHADE_CLOSED,384,240);
south_actor(panels&2?SOUTH_SPR_SHADE_OPEN:SOUTH_SPR_SHADE_CLOSED,416,240);
if(adventure_save.quests.objectives[23]&1)south_actor(SOUTH_SPR_DONE,304,192);
if(adventure_save.quests.objectives[23]&2)south_actor(SOUTH_SPR_DONE,352,192);
if(roots&1)south_actor(SOUTH_SPR_DONE,128,224);
if(roots&2)south_actor(SOUTH_SPR_DONE,160,224);
if(drain)south_actor(SOUTH_SPR_DONE,128,80);
if(runnel)south_actor(SOUTH_SPR_DONE,224,144);
region_form_actor(25,144,208);
region_form_actor(28,160,80);
region_form_actor(83,400,208);
region_form_actor(89,256,112);
if(adventure_save.quests.region_flags[18]&1)region_form_actor(87,288,96);
if(!done(23))region_form_actor(85,336,144);
}else{south_actor(SOUTH_SPR_RESET,32,132);
if(room==32){south_actor(ready(29)?SOUTH_SPR_DONE:SOUTH_SPR_GATE,208,64);
south_actor(loft&1?SOUTH_SPR_SHADE_OPEN:SOUTH_SPR_SHADE_CLOSED,72,80);
south_actor(loft&2?SOUTH_SPR_SHADE_OPEN:SOUTH_SPR_SHADE_CLOSED,168,80);
south_actor(SOUTH_SPR_TAILOR,208,112);
south_actor(SOUTH_SPR_TRIAL,208,132);
if(adventure_save.quests.objectives[28]&2){south_actor(SOUTH_SPR_DONE,176,48);
south_actor(SOUTH_SPR_AWNING,48,48);
}
if(adventure_save.quests.region_flags[18]&2)region_form_actor(91,120,112);
}
else if(room==33){south_actor(sun?SOUTH_SPR_SHADE_OPEN:SOUTH_SPR_SHADE_CLOSED,208,48);
south_actor(SOUTH_SPR_CLOCK,208,80);
south_actor(SOUTH_SPR_TRIAL,32,104);
for(i=0;i<3;i++)if(pins&(1u<<i))south_actor(SOUTH_SPR_DONE,56+(int)i*56,48);
if(sun)region_form_actor(81,40,72);
if(pins==7)region_form_actor(93,176,96);
}
else if(room<=36){if(room==36)south_actor((adventure_save.quests.objectives[24]&4)?SOUTH_SPR_DONE:SOUTH_SPR_GATE,208,112);
south_actor((adventure_save.quests.objectives[24]&(1u<<(room-34)))?SOUTH_SPR_DONE:SOUTH_SPR_GATE,208,56);
south_actor(south_game_puzzle.mirror[0]?SOUTH_SPR_MIRROR_BACK:SOUTH_SPR_MIRROR_SLASH,room==36?80:112,room==36?104:56);
if(room==34)south_actor((adventure_save.quests.objectives[24]&1)?SOUTH_SPR_DONE:SOUTH_SPR_WATER_LENS,112,104);
else{south_actor(south_game_puzzle.mirror[1]?SOUTH_SPR_MIRROR_BACK:SOUTH_SPR_MIRROR_SLASH,room==36?80:112,room==36?48:104);
south_actor(south_game_puzzle.shade?SOUTH_SPR_SHADE_CLOSED:SOUTH_SPR_SHADE_OPEN,176,room==35?80:104);
south_actor((adventure_save.quests.objectives[24]&(room==35?2:4))?SOUTH_SPR_DONE:room==35?SOUTH_SPR_CATCH:SOUTH_SPR_RECEIVER,192,room==35?104:48);
if(room==35)south_actor(SOUTH_SPR_TRIAL,208,132);
}
}else{south_actor(SOUTH_SPR_HANDLE,120,112);
south_actor(south_game_puzzle.shade?SOUTH_SPR_SHADE_CLOSED:SOUTH_SPR_SHADE_OPEN,192,112);
south_actor(south_game_machine_stage==5?SOUTH_SPR_BEACON:south_game_machine_stage==3&&!south_game_puzzle.shade?SOUTH_SPR_MACHINE_OPEN:south_game_machine_stage==1?SOUTH_SPR_MACHINE_WARN:SOUTH_SPR_MACHINE_IDLE,machine_x,64);
}
}
if(trial_index<10)for(i=0;i<3;i++)if(room==trials[trial_index].area[i]&&(trial_bits&(1u<<i)))south_actor(SOUTH_SPR_DONE,trials[trial_index].xy[i][0],trials[trial_index].xy[i][1]);
}
static void world_line(int x,int y,int xx,int yy,int c){line(x-camera_x,y-camera_y,xx-camera_x,yy-camera_y,c);
}
COLD void south_game_draw_overlay(void){unsigned i,n;
SouthBeam b[4];
if(room>=34&&room<=36){n=south_puzzle_beam(&south_game_puzzle,(unsigned)room,b);
for(i=0;i<n;i++){line(b[i].x1,b[i].y1,b[i].x2,b[i].y2,PAL_GOLD3);
if(b[i].end_kind!=SOUTH_BEAM_MIRROR)rect(b[i].x2-2,b[i].y2-2,5,5,b[i].end_kind==SOUTH_BEAM_RECEIVER?PAL_WATER4:PAL_ROSE4);
}if(room==35){rect(77,53,7,7,PAL_WATER4);
rect(79,55,3,3,PAL_GOLD3);
}if(room!=34){int y=south_game_puzzle.shade?(room==35?104:48):(room==35?56:104);
line(152,y-8,152,y+8,PAL_WOOD1);
line(154,y-8,154,y+8,PAL_FIRE2);
}}
if(room==30){rect(190-camera_x,182-camera_y,5,5,PAL_GOLD4);
world_line(192,184,demo?160:208,184,PAL_GOLD3);
world_line(demo?160:208,184,demo?160:208,192,PAL_GOLD3);
if(demo){world_line(192,184,256,184,PAL_GOLD3);
world_line(256,184,256,192,PAL_GOLD3);
}
if(done(24)){world_line(280,194,344,194,PAL_WATER4);
world_line(280,195,344,195,PAL_GOLD4);
}}
if(room==31){if(panels&1)rect(376-camera_x,220-camera_y,24,5,PAL_PURPLE1);
if(panels&2)rect(400-camera_x,220-camera_y,24,5,PAL_PURPLE1);
if(trial_index==7)for(i=0;i<3;i++)if(trial_revealed&(1u<<i)){int x=trials[7].xy[i][0],y=trials[7].xy[i][1];
world_line(x-7,y+4,x+7,y+4,PAL_WATER4);
}}
if(room==32){if(loft&1)line(72,48,72,72,PAL_GOLD3);
if(loft&2)line(168,48,168,72,PAL_GOLD3);
}
if(room==33){for(i=0;i<3;i++)rect(202+(int)i*4,136,3,3,i==moisture?PAL_WATER4:PAL_STONE1);
for(i=0;i<3;i++)rect(202+(int)i*4,88,3,3,i==alignment?PAL_GOLD3:PAL_STONE1);
}
if(room==37){if(south_game_machine_stage==1){line(64,76,176,76,PAL_GOLD3);
line(64,76,56,100,PAL_GOLD3);
line(176,76,184,100,PAL_GOLD3);
line(56,100,184,100,PAL_GOLD3);
}else if(south_game_machine_stage==2){rect(machine_x-18,76,36,24,PAL_ROSE4);
line(machine_x,68,machine_x,98,PAL_GOLD4);
}else if(south_game_machine_stage==3&&!south_game_puzzle.shade){line(machine_x-14,50,machine_x+14,50,PAL_WATER4);
line(machine_x-14,78,machine_x+14,78,PAL_WATER4);
}if(south_game_machine_stage&&south_game_machine_stage<5){rect(83,36,74,4,PAL_STONE1);
rect(84,37,south_game_machine_hp/2,2,PAL_GOLD3);
}}
}
