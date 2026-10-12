/* Pure focus selection follows the same strict-first A handler order. */
typedef struct {unsigned char area;short x,y;} HintPoint;
static const HintPoint inspect_hint_points[]={
 {70,144,240},{70,336,272},{71,96,192},{71,160,192},
 {72,144,104},{72,272,104},{72,384,104},
 {74,120,216},{74,360,240},{74,240,168}
};
static COLD int hint_at(int xx,int yy,unsigned relaxed,int*x,int*y){if(!target_reach(xx,yy,relaxed))return 0;if(x)*x=xx;if(y)*y=yy;return 1;}
COLD int covenants_game_target_hint(int*x,int*y){
 unsigned i=(unsigned)room-70,pass,j;
 if(i>=8||game_state!=PLAY||event_count)return 0;
 for(pass=0;pass<2;pass++){
  if(hint_at(resets[i][0],resets[i][1],pass,x,y))return 1;
  for(j=0;j<sizeof doors/sizeof doors[0];j++)if(doors[j].area==room&&!road_region_managed((unsigned)room,doors[j].to)&&target_reach(doors[j].x,doors[j].y,pass))return 0;
  if((i==0||i==4)&&hint_at(80,272,pass,x,y))return 1;
  if(hint_at(invitations[i][0],invitations[i][1],pass,x,y))return 1;
  for(j=0;j<manual_counts[i];j++)if(hint_at(manual_points[i][j][0],manual_points[i][j][1],pass,x,y))return 1;
  if(!fulfilled(i))for(j=0;j<sizeof inspect_hint_points/sizeof inspect_hint_points[0];j++){
   const HintPoint*p=&inspect_hint_points[j];if(p->area==room&&hint_at(p->x,p->y,pass,x,y))return 1;
  }
  for(j=0;j<resident_counts[i];j++){
   int xx=residents[i][j].x,yy=residents[i][j].y;
   if(!j&&(i==1||i==3||i==5||i==6)){xx=npc_x;yy=npc_y;}
   if(hint_at(xx,yy,pass,x,y))return 1;
  }
 }
 return 0;
}
