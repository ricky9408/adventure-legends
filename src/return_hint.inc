/* Read-only ordinary A focus, in the authored handler order. */
typedef struct {unsigned char area;short x,y;} HintPoint;
static const HintPoint hint_points[]={
 {54,72,256},{54,240,240},{54,240,72},{54,272,240},
 {55,40,116},{55,64,112},{55,176,112},{55,208,80},
 {56,288,256},{56,432,256},{56,240,96},{56,240,208},
 {57,352,272},{57,304,272},{57,432,272},{57,320,208},{57,400,240},{57,304,240},
 {58,368,272},{58,400,240},{58,80,80},{58,160,80},{58,128,144},{58,432,256},{58,240,240},
 {59,120,104},{59,64,56},{59,192,56},
 {60,120,104},{60,208,112},
 {61,64,56},{61,176,56},
};
static COLD int hint_at(int xx,int yy,unsigned relaxed,int*x,int*y){if(!target_reach(xx,yy,relaxed))return 0;if(x)*x=xx;if(y)*y=yy;return 1;}
COLD int return_game_target_hint(int*x,int*y){
 unsigned pass,i;int xx,yy;
 if(!return_game_is_room((unsigned)room)||game_state!=PLAY||event_count)return 0;
 reset_point(&xx,&yy);
 for(pass=0;pass<2;pass++){
  if(hint_at(xx,yy,pass,x,y))return 1;
  if(return_game_trial.index<13)continue;
  for(i=0;i<13;i++)if(trials[i].area==room&&hint_at(trials[i].lectern[0],trials[i].lectern[1],pass,x,y))return 1;
  for(i=0;i<sizeof hint_points/sizeof hint_points[0];i++){
   const HintPoint*p=&hint_points[i];
   if(p->area!=room)continue;
   if(room==58&&p->x==368&&!repeat_active)continue;
   if(room==58&&p->x==432){if(road_region_managed(58,59))continue;if(target_reach(p->x,p->y,pass))return 0;continue;}
   if(room==60&&p->x==208){if(road_region_managed(60,61))continue;if(target_reach(p->x,p->y,pass))return 0;continue;}
   if(!target_reach(p->x,p->y,pass))continue;
   if((room==55&&p->x==208&&done(47)&&!repeat_active&&(repeat_used&1))||(room==58&&p->x==400&&done(49)&&!repeat_active&&(repeat_used&2)))return 0;
   if(x)*x=p->x;if(y)*y=p->y;return 1;
  }
 }
 return 0;
}
