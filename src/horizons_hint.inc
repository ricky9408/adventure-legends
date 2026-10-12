/* Read-only ordinary A focus, in the authored handler order. */
typedef struct {unsigned char area;short x,y;} HintPoint;
static const HintPoint hint_points[]={
 {62,88,80},{62,384,80},{62,72,256},{62,208,208},{62,272,208},{62,120,208},
 {63,80,96},{63,352,96},{63,136,80},
 {64,32,96},{64,56,104},{64,120,104},{64,176,104},{64,120,40},{64,176,120},
 {65,80,256},{65,96,176},{65,336,208},{65,352,272},
 {66,48,96},{66,176,80},{66,48,288},
 {67,368,176},{67,352,224},{67,352,256},{67,112,256},{67,288,240},
 {68,72,136},{68,120,96},
 {69,40,80},{69,48,104},{69,80,104},
};
static COLD int hint_at(int xx,int yy,unsigned relaxed,int*x,int*y){if(!target_reach(xx,yy,relaxed))return 0;if(x)*x=xx;if(y)*y=yy;return 1;}
COLD int horizons_game_target_hint(int*x,int*y){
 unsigned pass,i;int xx,yy;CreatureInstance*c=active();
 if(!horizons_game_is_room((unsigned)room)||game_state!=PLAY||event_count)return 0;
 reset_point(&xx,&yy);
 for(pass=0;pass<2;pass++){
  if(hint_at(xx,yy,pass,x,y))return 1;
  for(i=0;i<sizeof doors/sizeof doors[0];i++)if(doors[i].area==room&&!road_region_managed((unsigned)room,doors[i].to)&&target_reach(doors[i].x,doors[i].y,pass))return 0;
  if(proof.mode){
   if(proof.mode==MODE_INITIAL||proof.mode==MODE_REPEAT){const SourceDef*d=&sources[proof.index];
    if(hint_at(d->invite[0],d->invite[1],pass,x,y)||hint_at(d->manual[0],d->manual[1],pass,x,y))return 1;
    if(proof.index==7&&hint_at(80,144,pass,x,y))return 1;
    if(proof.index==8&&hint_at(192,32,pass,x,y))return 1;
   }else{const TrialDef*d=work_trial();if(hint_at(d->manual[0],d->manual[1],pass,x,y)||hint_at(d->lectern[0],d->lectern[1],pass,x,y))return 1;}
   continue; /* Other room actors are hidden during this work projection. */
  }
  for(i=0;i<4;i++)if(trials[i].area==room&&c&&(c->form_id==trials[i].form||c->form_id==trials[i].form+1u)&&hint_at(trials[i].lectern[0],trials[i].lectern[1],pass,x,y))return 1;
  if(room==63&&practice_eligible(0)&&hint_at(336,128,pass,x,y))return 1;
  for(i=0;i<12;i++)if(sources[i].area==room&&hint_at(sources[i].invite[0],sources[i].invite[1],pass,x,y))return 1;
  for(i=0;i<sizeof hint_points/sizeof hint_points[0];i++){
   const HintPoint*p=&hint_points[i];if(p->area!=room)continue;
   if(room==68&&p->x==72&&!(bits(57)&4))continue;
   if(hint_at(p->x,p->y,pass,x,y))return 1;
  }
 }
 return 0;
}
