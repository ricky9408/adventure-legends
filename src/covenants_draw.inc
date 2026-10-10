static COLD void rr(int x,int y,int w,int h,int color){rect(x-camera_x,y-camera_y,w,h,(unsigned char)color);}
static COLD void rl(int x,int y,int xx,int yy,int color){line(x-camera_x,y-camera_y,xx-camera_x,yy-camera_y,color);}
static COLD void outline(int x,int y,int w,int h,int color){rr(x,y,w,1,color);rr(x,y+h-1,w,1,color);rr(x,y,1,h,color);rr(x+w-1,y,1,h,color);}
static COLD void mark(int x,int y,int complete){
 int c=complete?PAL_PINE3:PAL_GOLD2;
 outline(x-5,y-5,11,11,c);rr(x-2,y-2,5,5,complete?PAL_GOLD4:PAL_WOOD1);
}
static COLD void arrow(int x,int y,int dx,int dy){
 rl(x,y,x+dx,y+dy,PAL_WATER2);rl(x+dx,y+dy,x+dx-dx/3-dy/3,y+dy-dy/3+dx/3,PAL_WATER2);
 rl(x+dx,y+dy,x+dx-dx/3+dy/3,y+dy-dy/3-dx/3,PAL_WATER2);
}
static COLD void ra(unsigned sprite,int x,int y){covenants_actor(sprite,x,y);}
static COLD void rf(unsigned form,int x,int y){region_form_actor(form,x,y);}
static COLD unsigned walking_sprite(unsigned sprite){
 unsigned beat=(npc_walk_phase/2)&3;
 if(!npc_walk_recent||beat==0||beat==2)return sprite;
 if(sprite==COVENANTS_SPR_WALKER)return beat==1?COVENANTS_SPR_WALKER_STEP_A:COVENANTS_SPR_WALKER_STEP_B;
 if(sprite==COVENANTS_SPR_SEED_KEEPER)return beat==1?COVENANTS_SPR_SEED_KEEPER_STEP_A:COVENANTS_SPR_SEED_KEEPER_STEP_B;
 if(sprite==COVENANTS_SPR_PASSENGER)return beat==1?COVENANTS_SPR_PASSENGER_STEP_A:COVENANTS_SPR_PASSENGER_STEP_B;
 return sprite;
}
COLD void covenants_game_draw_actors(void){
 unsigned i=(unsigned)room-70,j;if(i>=8)return;
 ra(COVENANTS_SPR_RESET,resets[i][0],resets[i][1]);
 if(!owned(i))rf(121+i,invitations[i][0],invitations[i][1]);
 else ra(COVENANTS_SPR_WAITING_PLACE,invitations[i][0],invitations[i][1]);
 if(fulfilled(i))ra(COVENANTS_SPR_FULFILLED,invitations[i][0]-16,invitations[i][1]);
 for(j=0;j<manual_counts[i];j++)ra(fulfilled(i)?COVENANTS_SPR_PRACTICE:COVENANTS_SPR_MANUAL,manual_points[i][j][0],manual_points[i][j][1]);
 for(j=0;j<resident_counts[i];j++){
  unsigned sprite=residents[i][j].sprite;int x=residents[i][j].x,y=residents[i][j].y;
  if(!j&&(i==1||i==3||i==5||i==6)){x=npc_x;y=npc_y;sprite=walking_sprite(sprite);}
  ra(sprite,x,y);
 }
 if(i==0||i==4)ra((adventure_save.quests.anchors[7]&(i?2:1))?COVENANTS_SPR_REST_LIT:COVENANTS_SPR_REST,80,272);
 if(i==2){unsigned k;ra(setting[1]?COVENANTS_SPR_VENT_OPEN:COVENANTS_SPR_VENT_CLOSED,336,88);for(k=0;k<3;k++)ra(movement_ticks>=24*(k+1)?COVENANTS_SPR_BOWL_COOL:COVENANTS_SPR_BOWL,144+k*120,104);}
}
static COLD void draw_dynamic(void){
 if(room==71){
  rr(moving_x,104,24,16,PAL_WOOD2);rr(moving_x+2,106,20,11,PAL_ROSE3);
  rl(moving_x,103,moving_x+24,103,PAL_GOLD4);rl(moving_x+4,105,moving_x+4,118,PAL_WOOD1);
 }else if(room==73){
  rr(moving_x,96,16,12,PAL_STONE2);rr(moving_x+2,97,12,3,PAL_STONE4);
  rl(moving_x+8,96,moving_x+8,80,PAL_WOOD2);rl(80,80,160,80,PAL_WOOD2);
 }else if(room==76){
  rr(moving_x,48,24,12,PAL_WOOD2);rr(moving_x+2,50,20,8,PAL_GOLD2);
  for(int x=4;x<24;x+=5)rl(moving_x+x,50,moving_x+x,57,PAL_WOOD1);
  rl(224,46,296,46,PAL_WOOD2);
 }
}
static COLD void draw_work(void){
 if(room==70){
  /* Unequal communities are shown as two and one cups, not a timing race. */
  for(unsigned k=0;k<3;k++){outline(132+k*8,231,6,8,PAL_WOOD2);if(k<setting[1])rr(133+k*8,235,4,3,PAL_WATER3);}
  for(unsigned k=0;k<3;k++){outline(324+k*8,263,6,8,PAL_WOOD2);if(k<setting[2])rr(325+k*8,267,4,3,PAL_WATER3);}
  rr(134,225,4,3,PAL_GOLD3);rr(142,225,4,3,PAL_GOLD3);rr(326,257,4,3,PAL_GOLD3);
 }else if(room==71){
  int shade=moving_x==120&&!moving_state;
  outline(88,186,18,12,shade?PAL_PINE3:PAL_GOLD2);outline(152,186,18,12,shade?PAL_PINE3:PAL_GOLD2);
  rr(114,177,12,25,PAL_GOLD4);
 }else if(room==73){
  mark(88,136,(setting[3]&1)!=0);mark(128,136,(setting[3]&2)!=0);
 }else if(room==74){
  for(unsigned j=0;j<2;j++){
   int x,y,w,h;if(setting[1+j]==1){x=j?272:200;y=136;w=8;h=56;}
   else if(setting[1+j]==2){x=j?232:208;y=184;w=40;h=8;}
   else{x=j?304:136;y=168;w=40;h=8;}
   rr(x,y,w,h,j?PAL_ROSE3:PAL_WATER3);outline(x,y,w,h,PAL_WOOD2);
  }
  for(int y=128;y<=176;y+=12){rl(240-(y-112)*120/128,y,240-(y-112)*120/128-5,y+5,PAL_GOLD2);rl(240+(y-112)*120/128,y,240+(y-112)*120/128+5,y+5,PAL_GOLD2);}
  mark(120,216,(setting[3]&1)!=0);mark(360,240,(setting[3]&2)!=0);mark(240,168,(setting[3]&4)!=0);
 }else if(room==75){
  int left=setting[1]==1?84:setting[1]==2?112:64,right=(setting[0]&2)?156:124;
  for(int y=116;y<140;y+=4)rl(left,y,left+31,y,PAL_PINE3);
  for(int y=184;y<208;y+=4)rl(right,y,right+31,y,PAL_PINE3);
  outline(120,144,16,32,shade_geometry()?PAL_GOLD4:PAL_ROSE3);
 }else if(room==76){
  mark(224,72,npc_stage>=3);mark(384,128,npc_stage>=6);
  rl(368,112,400,112,setting[1]?PAL_GOLD4:PAL_WOOD2);
 }else if(room==77){
  outline(104,103,32,9,setting[1]?PAL_GOLD4:PAL_WOOD2);
  for(unsigned k=0;k<3;k++)rr(108+k*9,88,6,4,setting[4]>k?PAL_GOLD3:PAL_STONE2);
 }
}
COLD void covenants_game_draw_overlay(void){
 unsigned i=(unsigned)room-70,j;if(i>=8)return;
 for(j=0;j<sizeof doors/sizeof doors[0];j++)if(doors[j].area==room&&!road_region_managed((unsigned)room,doors[j].to)){
  int dx=doors[j].key==RIGHT?8:doors[j].key==LEFT?-8:0,dy=doors[j].key==DOWN?8:doors[j].key==UP?-8:0;
  arrow(doors[j].x-dx,doors[j].y-dy,dx,dy);
 }
 draw_dynamic();draw_work();
 for(j=0;j<station_counts[i];j++){const StationTarget*t=&station_targets[i][j];mark(t->x,t->y,(setting[0]&(1u<<t->station))!=0);}
 if(practice_mode)for(j=0;j<practices[i].count;j++)mark(practices[i].target[j][0],practices[i].target[j][1],(setting[10]&(1u<<j))!=0);
 if(practice_ticks){
  const short*p=covenants_practice_shortcuts[i];
  if(p[2]>0){rr(p[0]-5,p[1]-5,p[2]+10,p[3]+10,PAL_WOOD2);rr(p[0]-3,p[1]-3,p[2]+6,p[3]+6,PAL_GOLD2);for(int y=p[1]-1;y<p[1]+p[3]+4;y+=6)rl(p[0]-3,y,p[0]+p[2]+2,y,PAL_WOOD1);}
  else if(i==2){outline(344,88,72,18,PAL_GOLD3);rl(352,96,404,96,PAL_ROSE3);}
  else if(i==4){for(int y=232;y>=128;y-=16)arrow(120,y,8,-8);}
  else if(i==7){rl(76,110,102,110,PAL_FIRE2);rl(138,110,164,110,PAL_FIRE2);}
 }
}
/* Flat homecoming pieces belong below actors. Mode4 pair writes preserve the
 * neighbour byte and transparent source pixels; no extra tile allocation. */
static COLD void floor_stamp(unsigned image,int x,int y){
 extern void sprite(const unsigned char*,int,int,int,int,int);
 /* Same transparent16px art and anchor, using the shared paired-pixel blitter. */
 sprite(covenants_sprites[image],x-8-camera_x,y-15-camera_y,16,16,0);
}
COLD void covenants_game_draw_old_actors(void){
 if(!done(57))return;
 if(room==62){
  ra(COVENANTS_SPR_NOTICE,416,32);
  if(state(63)&&(bits(63)&1)&&!(bits(63)&2))ra(walking_sprite(COVENANTS_SPR_PASSENGER),npc_x,npc_y);
 }
}
COLD void covenants_game_draw_old_overlay(void){
 if(!done(57))return;
 if(room==62&&!road_region_managed(62,70)&&(bits(60)&3)==3)arrow(416,40,0,-12);
 if(room==0&&done(63)){
  floor_stamp(COVENANTS_SPR_PORCH_LEFT,96,136);floor_stamp(COVENANTS_SPR_PORCH_MARKS,112,136);floor_stamp(COVENANTS_SPR_PORCH_RIGHT,128,136);
 }
}
COLD void covenants_game_draw_journal(void){
 unsigned sel=covenants_game_journal_selection%12,q,b,x=82;
 box(8,31,224,122);centered(TX_CV_JOURNAL,34,PAL_GOLD3);
 if(sel<4){
  q=60+sel;text(quest_names[sel],14,54,PAL_GOLD4);
  text(state(q)==3?TX_CV_RECEIVED:state(q)==2?TX_CV_READY:state(q)?TX_CV_ACTIVE:TX_CV_UNSEEN,14,71,PAL_TEAL2);
  text(quest_clues[sel][0],14,90,PAL_GOLD4);text(quest_clues[sel][1],14,107,PAL_GOLD4);
  for(b=1;b<=8;b<<=1)if(covenants_quest_mask(q)&b){rect(x,126,8,5,bits(q)&b?PAL_GOLD3:PAL_STONE1);x+=13;}
 }else{
  unsigned i=sel-4,visited=(adventure_save.quests.region_flags[7]>>i)&1;
  text(visited?progression_name_id(121+i):TX_CV_UNSEEN,14,54,PAL_GOLD4);
  text(room_names[i],14,70,PAL_TEAL2);
  text(owned(i)?TX_CV_OWNED:fulfilled(i)?TX_CV_INVITE_LATER:TX_CV_ACTIVE,14,86,PAL_GOLD4);
  text(visited?trial_clues[i][0]:TX_CV_CLUE61A,14,102,PAL_GOLD4);
  text(fulfilled(i)?TX_CV_WORK_DONE:visited?trial_clues[i][1]:TX_CV_CLUE61B,14,118,PAL_TEAL2);
 }
 centered(TX_CV_KEYS,136,PAL_TEAL2);
}
COLD int covenants_game_menu_input(int pressed){
 if(journal_tab!=12)return 0;
 if(pressed&UP){covenants_game_journal_selection=(covenants_game_journal_selection+11)%12;changed();return 1;}
 if(pressed&DOWN){covenants_game_journal_selection=(covenants_game_journal_selection+1)%12;changed();return 1;}
 return 0;
}
