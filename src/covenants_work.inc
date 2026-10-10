/* Each room has different local work. Only completed promises are durable. */
static COLD void reconstruct(void){
 unsigned i=(unsigned)room-70;
 zero_bytes(setting,sizeof setting);moving_state=npc_stage=practice_mode=escort_stage=0;
 movement_ticks=practice_ticks=0;npc_walk_recent=npc_walk_phase=npc_blocked_ticks=0;heat_token=0;moving_x=88;npc_x=npc_y=0;work_area=(unsigned char)room;
 if(i<8){
  if(resident_counts[i]){npc_x=residents[i][0].x;npc_y=residents[i][0].y;}
  if(room==73)moving_x=88;
  if(room==76)moving_x=224;
  if(fulfilled(i)){
   static const unsigned char complete_masks[8]={31,3,3,3,3,3,7,7};
   setting[0]=complete_masks[i];setting[3]=7;npc_stage=4;
   if(room==70){setting[1]=2;setting[2]=1;}
   if(room==71){moving_x=120;npc_x=192;npc_y=232;setting[1]=1;}
   if(room==72){setting[1]=1;movement_ticks=72;}
   if(room==73){moving_x=136;npc_x=176;npc_y=128;}
   if(room==74){setting[1]=setting[2]=1;}
   if(room==75){setting[1]=1;npc_x=208;npc_y=96;}
   if(room==76){moving_x=272;setting[1]=1;npc_x=384;npc_y=128;npc_stage=6;}
   if(room==77){setting[1]=1;setting[4]=3;}
  }
 }
}
COLD void covenants_game_reset(void){
 covenants_game_cancel_event();invalidate_cast();
 if(room==77)game_covenants_spawn_wave(0);
 next_generation(&scene);next_generation(&attempt);next_generation(&geometry);
 reset_confirm=invite_confirm=porch_confirm=0;ambient=0;reconstruct();changed();
}
/* Author the old-town adapter before either arrival bitmap is cached. The
 * fallback tick also uses this for external checkpoint/scene reconstruction.
 * Leaving room77 still tears down its waves before the engine changes room. */
COLD void covenants_game_prepare_old_scene(void){
 if((room==0||room==62)&&work_area!=room){covenants_game_reset();if(room==62){npc_x=416;npc_y=32;}}
}
COLD int covenants_game_enter(unsigned a,unsigned s){
 int x,y;
 if(!covenants_game_spawn(a,s,&x,&y)||!spawn_allowed(a,s)||!(adventure_save.quests.region_flags[7]&(1u<<(a-70))))return 0;
 room=a;checkpoint_spawn=s;covenants_game_reset();px=x;py=y;
 adventure_save.campaign.room=(Save4U8)a;adventure_save.campaign.spawn=(Save4U8)s;dirty=1;persist();return 1;
}
COLD int covenants_game_is_sanctuary(void){
 return(room==70&&(adventure_save.quests.anchors[7]&1)&&near(px,py,80,256,32))||
       (room==74&&(adventure_save.quests.anchors[7]&2)&&near(px,py,80,256,32));
}
COLD void covenants_game_selection_changed(void){
 if(!covenants_game_is_room((unsigned)room)&&room!=0&&room!=62&&!event_count)return;
 covenants_game_cancel_event();invalidate_cast();invite_confirm=porch_confirm=0;
 practice_mode=0;setting[10]=setting[11]=0;
 next_generation(&attempt);changed();
}
COLD void covenants_game_menu_abandoned(void){
 if(invite_confirm||porch_confirm){invite_confirm=porch_confirm=0;invalidate_cast();next_generation(&attempt);changed();}
}
COLD unsigned covenants_game_enemy_spawns(unsigned a,const CovenantsEnemySpawn**out){
 (void)a;if(out)*out=0;return 0; /* Refuge waves require explicit local consent. */
}
static COLD int wrong(int message){toast(message);return 0;}
static COLD int body_clear(int x,int y,int width,int height){
 const CovenantsArtRoom*r=&covenants_art_rooms[(unsigned)room-70];unsigned i;
 if(x<0||y<0||x+width>r->width||y+height>r->height||game_region_actor_overlap(x,y,x+width-1,y+height-1))return 0;
 /* Moving raw bodies need raw-art overlap, not a second foot dilation. */
 for(i=0;i<r->solid_count;i++){const CovenantsArtRect*s=&r->solids[i];
  if(x<s->x+s->w&&x+width>s->x&&y<s->y+s->h&&y+height>s->y)return 0;
 }
 if(!(room==76&&npc_stage==3)&&npc_x+5>=x&&npc_x-5<x+width&&npc_y+5>=y&&npc_y-5<y+height)return 0;
 return 1;
}
static COLD int begin_motion(int goal){
 if(moving_state)return wrong(TX_CV_CLEAR);
 setting[7]=(unsigned char)((moving_x-(room==76?224:88))/(room==71?32:24));
 setting[8]=(unsigned char)((goal-(room==76?224:88))/(room==71?32:24));
 moving_state=1;geometry_changed();return 1;
}
static COLD void motion_tick(void){
 int start=room==76?224:88,goal=start+(moving_state==2?setting[7]:setting[8])*(room==71?32:24);
 int nx=moving_x+(moving_x<goal?1:-1),y=room==71?104:room==73?96:48,w=room==73?16:24,h=room==71?16:12;
 if(!moving_state)return;
 if(moving_x==goal){moving_state=0;return;}
 if(!body_clear(nx,y,w,h)){
  if(moving_state==1){moving_state=2;toast(TX_CV_CLEAR);}return;
 }
 moving_x=(short)nx;
 if(room==76&&npc_stage==3){npc_x=moving_x+12;npc_y=44;}
 if(moving_x==goal){moving_state=0;toast(TX_CV_TRACE);}
 geometry_changed();
}
static COLD void npc_wait_for_space(void){
 if(npc_blocked_ticks<255)npc_blocked_ticks++;
 if(npc_blocked_ticks==10)toast(TX_CV_CLEAR); /* Ten movement attempts, about half a second. */
}
static COLD int npc_step(int tx,int ty,int require_player){
 int nx=npc_x,ny=npc_y;
 if(nx==tx&&ny==ty)return 1;
 if(require_player&&!near(px,py,npc_x,npc_y,38))return 0;
 if(ambient%3)return 0;
 if(nx!=tx)nx+=nx<tx?1:-1;else ny+=ny<ty?1:-1;
 if(covenants_game_solid(nx,ny))return 0;
 if(game_region_actor_overlap(nx-4,ny-4,nx+4,ny+4)){npc_wait_for_space();return 0;}
 npc_blocked_ticks=0;
 npc_x=(short)nx;npc_y=(short)ny;return nx==tx&&ny==ty;
}
static COLD void practice_expiry(void){
 const short*p;unsigned i=(unsigned)room-70;
 if(!practice_ticks||i>=8)return;
 if(practice_ticks>1){practice_ticks--;return;}
 p=covenants_practice_shortcuts[i];
 if(p[2]>0&&(game_region_actor_overlap(p[0]-5,p[1]-5,p[0]+p[2]+4,p[1]+p[3]+4)||
    (npc_x+5>=p[0]&&npc_x-5<p[0]+p[2]&&npc_y+5>=p[1]&&npc_y-5<p[1]+p[3])))return;
 practice_ticks=0;practice_mode=0;geometry_changed();
}
/* The two tall sound screens stop diagonal rays into resting alcoves. The
 * center ray is deliberately open, so ringing is still shared in the court. */
static COLD int cross_side(int ax,int ay,int bx,int by,int cx,int cy){
 int v=(bx-ax)*(cy-ay)-(by-ay)*(cx-ax);return (v>0)-(v<0);
}
static COLD int segment_cross(int ax,int ay,int bx,int by,int cx,int cy,int dx,int dy){
 int a=cross_side(ax,ay,bx,by,cx,cy),b=cross_side(ax,ay,bx,by,dx,dy);
 int c=cross_side(cx,cy,dx,dy,ax,ay),d=cross_side(cx,cy,dx,dy,bx,by);
 if((ax>bx?ax:bx)<(cx<dx?cx:dx)||(cx>dx?cx:dx)<(ax<bx?ax:bx)||
    (ay>by?ay:by)<(cy<dy?cy:dy)||(cy>dy?cy:dy)<(ay<by?ay:by))return 0;
 return a*b<=0&&c*d<=0;
}
static COLD int screen_stops(int tx,int ty,unsigned side){
 int x,y,w,h;unsigned pose=setting[1+side];
 if(pose==1){x=side?272:200;y=136;w=8;h=56;}
 else if(pose==2){x=side?232:208;y=184;w=40;h=8;}
 else{x=side?304:136;y=168;w=40;h=8;}
 return segment_cross(240,112,tx,ty,x,y,x+w,y)||segment_cross(240,112,tx,ty,x+w,y,x+w,y+h)||
        segment_cross(240,112,tx,ty,x+w,y+h,x,y+h)||segment_cross(240,112,tx,ty,x,y+h,x,y);
}
static COLD unsigned sound_observation(void){
 unsigned left=screen_stops(120,240,0)||screen_stops(120,240,1);
 unsigned right=screen_stops(360,240,0)||screen_stops(360,240,1);
 unsigned center=!(screen_stops(240,240,0)||screen_stops(240,240,1));
 return left|(right<<1)|(center<<2);
}
static COLD int shade_geometry(void){
 int left=setting[1]==1?84:setting[1]==2?112:64;
 int right=(setting[0]&2)?156:124;
 /* Beds at84..99 and156..171 are shaded; the120..135 walking gap stays lit. */
 return left<=84&&left+32>=100&&right<=156&&right+32>=172&&
        left+32<=120&&right>=136;
}
static COLD void work_tick(void){
 unsigned i=(unsigned)room-70;
 if(i>=8||fulfilled(i)||event_count)return;
 if(room==70){
  if(setting[0]==31&&setting[1]==2&&setting[2]==1&&setting[3]==3)complete_covenant();
 }else if(room==71){
  if(setting[0]==3&&moving_x==120&&!moving_state&&setting[3]==3&&npc_stage==1){
   if(npc_step(192,232,1)){npc_stage=3;complete_covenant();}
  }
 }else if(room==72){
  if(setting[0]==3&&setting[1]==1&&movement_ticks<72){movement_ticks++;if(!(movement_ticks%24))changed();}
  if(movement_ticks==72&&setting[3]==7&&setting[1]==1)complete_covenant();
 }else if(room==73){
  if(setting[0]==3&&npc_stage>=1&&npc_stage<=3){
   int target=npc_stage==1?88:npc_stage==2?128:176;
   if(npc_step(target,128,1)){
    if(npc_stage<3){
     if(!(keys&240)&&near(px,py,npc_x,npc_y,38))movement_ticks++;else movement_ticks=0;
     if(movement_ticks>=24){setting[3]|=1u<<(npc_stage-1);movement_ticks=0;npc_stage++;begin_motion(npc_stage==2?112:136);}
    }else if(setting[3]==3&&!moving_state&&moving_x==136){npc_stage=4;complete_covenant();}
   }
  }
 }else if(room==74){
  if(setting[0]==3&&setting[3]==7&&sound_observation()==7)complete_covenant();
 }else if(room==75){
  if(setting[0]==3&&shade_geometry()&&npc_stage==1){
   if(npc_step(208,208,1))npc_stage=2;
  }else if(setting[0]==3&&shade_geometry()&&npc_stage==2&&npc_step(208,96,1)){
   npc_stage=4;complete_covenant();
  }
 }else if(room==76){
  if(npc_stage==1){if(npc_step(232,128,1))npc_stage=2;}
  else if(npc_stage==2){
   if(npc_step(232,72,1)){npc_stage=7;changed();}
  }else if(npc_stage==7){
   /* Explicit boarding uses the owned stationary hull as a walking surface.
    * It never transports the player or bypasses unrelated art collision. */
   int tx=236,ty=44,nx=npc_x,ny=npc_y;
   if(near(px,py,npc_x,npc_y,38)&&ambient%3==0){
    if(nx!=tx)nx+=nx<tx?1:-1;else if(ny!=ty)ny+=ny<ty?1:-1;
    if(!covenants_game_geometry_solid((unsigned)room,nx,ny)){if(game_region_actor_overlap(nx-4,ny-4,nx+4,ny+4))npc_wait_for_space();else{npc_blocked_ticks=0;npc_x=nx;npc_y=ny;}}
    if(npc_x==tx&&npc_y==ty){npc_stage=3;changed();}
   }
  }else if(npc_stage==3&&moving_x==272&&!moving_state&&(setting[0]&4)&&setting[1]){
   /* Walk off the far bow via its clear side; do not step through the bank. */
   int tx=264,ty=44,nx=npc_x;
   if(ambient%3==0){
    if(nx!=tx)nx+=nx<tx?1:-1;
    if(!covenants_game_geometry_solid((unsigned)room,nx,ty)){if(game_region_actor_overlap(nx-4,ty-4,nx+4,ty+4))npc_wait_for_space();else{npc_blocked_ticks=0;npc_x=nx;npc_y=ty;}}
    if(npc_x==tx){npc_stage=4;changed();}
   }
  }else if(npc_stage==4){if(npc_step(264,128,0))npc_stage=5;}
  else if(npc_stage==5&&npc_step(384,128,0)){npc_stage=6;if(setting[0]==7&&setting[1])complete_covenant();}

 }
}
