/* Read-only ordinary A focus, in the authored handler order. */
typedef struct {unsigned char area;short x,y;} HintPoint;
static const HintPoint hint_points[]={
 {46,80,256},{46,120,72},{46,96,104},{46,144,104},{46,340,72},{46,340,108},{46,160,176},{46,304,176},{46,240,240},{46,240,104},{46,384,128},{46,384,160},{46,64,72},{46,64,104},{46,416,72},{46,416,108},{46,240,272},
 {47,64,256},{47,64,112},{47,112,112},{47,240,164},{47,352,160},{47,376,184},{47,392,240},{47,416,264},
 {48,112,92},{48,144,92},{48,368,208},{48,368,256},{48,64,224},{48,96,224},{48,304,80},{48,272,80},{48,336,80},{48,240,80},{48,280,224},{48,432,256},{48,368,112},
 {49,120,48},{49,144,52},{49,172,52},{49,208,64},{49,208,96},{49,64,56},{49,80,88},{49,112,88},{49,64,88},
 {50,120,104},{50,88,72},{50,152,72},
 {51,240,80},{51,160,80},{51,160,112},{51,144,96},{51,384,64},{51,416,64},{51,400,96},
 {52,80,72},{52,160,72},{52,120,112},
 {53,176,80},{53,120,112},{53,208,112},
};
static COLD int hint_at(int xx,int yy,unsigned relaxed,int*x,int*y){if(!target_reach(xx,yy,relaxed))return 0;if(x)*x=xx;if(y)*y=yy;return 1;}
COLD int underwater_game_target_hint(int*x,int*y){
 unsigned pass,i;int xx,yy;
 if(!underwater_game_is_room((unsigned)room)||game_state!=PLAY||event_count)return 0;
 reset_point(&xx,&yy);
 for(pass=0;pass<2;pass++){
  if(hint_at(xx,yy,pass,x,y))return 1;
  if(projection||underwater_game_trial.index<16)continue;
  if(room>=48){int large=room==48||room==51,ly=large?240:112;
   if(hint_at(large?80:48,ly,pass,x,y)||hint_at(large?400:192,ly,pass,x,y))return 1;
  }
  for(i=0;i<sizeof hint_points/sizeof hint_points[0];i++){
   const HintPoint*p=&hint_points[i];unsigned visible=1;
   if(p->area!=room||!target_reach(p->x,p->y,pass))continue;
   /* A hint never reveals a branch prop that its draw layer hides. */
   if(room==46){if(p->x==64)visible=branch_visible&1;else if(p->x==416)visible=branch_visible&2;}
   else if(room==47&&(p->x==392||p->x==416))visible=branch_visible&8;
   else if(room==48){if(p->x==368)visible=p->y==112?0:branch_visible&4;else if(p->y==80&&(p->x==304||p->x==272||p->x==336))visible=branch_visible&32;}
   else if(room==49){if(p->x==208)visible=branch_visible&16;else if(p->y==88)visible=branch_visible&128;else if(p->x==64&&p->y==56)visible=adventure_save.quests.region_flags[21]>=3;}
   else if(room==51&&(p->x==384||p->x==416||p->x==400))visible=branch_visible&64;
   if(room==53&&p->x==208){if(road_region_managed(53,46)||underwater_game_guardian_stage!=4)continue;return 0;}
   if(!visible)return 0;
   if(x)*x=p->x;if(y)*y=p->y;return 1;
  }
 }
 return 0;
}
