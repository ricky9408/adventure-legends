/* Exact union differential proof. No emulator or native pacing claim. */
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "asset_collisions.h"
#include "world.h"
#include "campaign_rules.h"
#include "progression.h"
#include "trials.h"
#include "region_art.h"
#include "region_game.h"
#include "regional_quests.h"
#include "north_art.h"
#include "north_game.h"
#include "south_art.h"
#include "south_game.h"
#include "magma_game.h"
#include "magma_art.h"
#include "return_game.h"
#include "return_art.h"
#define COLD
#define FOOT 5
#define Q_DRY REGION_QUEST_DRY_ROAD
volatile int room,bridge_open,torches;
volatile unsigned room_flags,chapter_flags;
Save5State adventure_save;
short region_game_crates[2][2],trial_parcels[2][2];
static unsigned unsupported_calls;
void collision_magma_state(unsigned trial,unsigned lesson,unsigned screen);
unsigned collision_magma_digest(void);
int underwater_game_solid(int x,int y){(void)x;(void)y;unsupported_calls++;return 1;}
void collision_return_state(unsigned a,unsigned b,unsigned c,unsigned unrelated);
void collision_return_copy(unsigned char out[6]);
int horizons_game_solid(int x,int y){(void)x;(void)y;unsupported_calls++;return 1;}
int ab(int n);
#include "production_predicates.inc"
#ifndef COLLISION_RECTS_INCLUDE
#define COLLISION_RECTS_INCLUDE "collision_rects.inc"
#endif
#include COLLISION_RECTS_INCLUDE

#define MAX_RECTS 256
#define MARGIN 16
#define GRID_W (480+2*MARGIN)
#define GRID_H (320+2*MARGIN)
static int difference[GRID_H+1][GRID_W+1];

static uint64_t actual_point_checks,query_point_checks,query_checks,capacity_checks,invalid_checks;
static unsigned states,parcel_pair_states,crate_pair_states,full_range_queries,near_queries;
static unsigned near_24_overflows,near_max_rects,maximum_rects;
static int near_max_room,near_max_query[4];
static unsigned cast_queries,cast_48_overflows,cast_max_rects,cast_room_max[62],cast_room_overflow[62];
static unsigned magma_states,return_states;
static int cast_room_query[62][4];
static unsigned rng=0x19600824u;
static unsigned random_u(void){rng=rng*1664525u+1013904223u;return rng;}
static void fail(const char *kind,int x0,int y0,int x1,int y1,int want,int got){
 fprintf(stderr,"%s room=%d query=(%d,%d)-(%d,%d) want=%d got=%d flags=%u/%u bridge=%d torches=%d\n",
         kind,room,x0,y0,x1,y1,want,got,room_flags,chapter_flags,bridge_open,torches);
 exit(1);
}
/* Guard both ends and every byte beyond cap. The input capacity is real, even
 * though guarded storage is deliberately larger to make accidental writes observable. */
static int snapshot(int x0,int y0,int x1,int y1,short result[][4],unsigned cap,int invalid){
 short guarded[MAX_RECTS+2][4];int count;unsigned i;
 memset(guarded,0x5a,sizeof guarded);
 count=game_collision_rects(x0,y0,x1,y1,guarded+1,cap);
 query_checks++;
 if(count < -1 || count > (int)cap || (invalid&&count!=-1))fail("count",x0,y0,x1,y1,-1,count);
 for(i=0;i<4;i++)if(guarded[0][i]!=0x5a5a)fail("leading canary",x0,y0,x1,y1,0,1);
 for(i=(cap<=MAX_RECTS?cap:MAX_RECTS)+1;i<MAX_RECTS+2;i++){
  unsigned j;for(j=0;j<4;j++)if(guarded[i][j]!=0x5a5a)fail("capacity canary",x0,y0,x1,y1,0,1);
 }
 if(invalid){
  for(i=1;i<MAX_RECTS+2;i++){unsigned j;for(j=0;j<4;j++)if(guarded[i][j]!=0x5a5a)fail("invalid wrote output",x0,y0,x1,y1,0,1);}
 }else if(count>=0){
  for(i=0;i<(unsigned)count;i++){
   const short *r=guarded[i+1];
   if(r[0]<x0||r[1]<y0||r[2]>x1||r[3]>y1||r[0]>r[2]||r[1]>r[3])fail("unclipped rectangle",x0,y0,x1,y1,0,1);
  }
  for(i=(unsigned)count+1;i<MAX_RECTS+2;i++){
   unsigned j;for(j=0;j<4;j++)if(guarded[i][j]!=0x5a5a)fail("write beyond count",x0,y0,x1,y1,0,1);
  }
 }
 if(result&&cap<=MAX_RECTS)memcpy(result,guarded+1,cap*sizeof guarded[0]);
 return count;
}
static int contains(short rects[][4],int count,int x,int y){
 int i;for(i=0;i<count;i++)if(x>=rects[i][0]&&x<=rects[i][2]&&y>=rects[i][1]&&y<=rects[i][3])return 1;
 return 0;
}
static void assert_point(short rects[][4],int count,int x,int y,const char *kind){
 int want=solid(x,y)!=0,got=contains(rects,count,x,y);
 if(want!=got)fail(kind,x,y,x,y,want,got);
 query_point_checks++;
}
static void capacity_proof(int x0,int y0,int x1,int y1,short baseline[][4],int count){
 unsigned cap;short limited[MAX_RECTS][4];
 for(cap=1;cap<=(unsigned)count+1&&cap<=MAX_RECTS;cap++){
  int got=snapshot(x0,y0,x1,y1,limited,cap,0);
  if(got!=(cap<(unsigned)count?-1:count))fail("overflow must fail closed",x0,y0,x1,y1,cap<(unsigned)count?-1:count,got);
  /* A -1 result is never interpreted as occupancy. Prefix is only checked to
   * establish bounded writes before overflow, not to grant a partial shortcut. */
  if(memcmp(limited,baseline,(cap<(unsigned)count?cap:(unsigned)count)*sizeof limited[0]))fail("unstable prefix",x0,y0,x1,y1,0,1);
  capacity_checks++;
 }
}
static void small_query(int x0,int y0,int x1,int y1){
 short rects[MAX_RECTS][4],limited[24][4];int x,y,count=snapshot(x0,y0,x1,y1,rects,MAX_RECTS,0),got;
 if(count<0)fail("unexpected supported overflow",x0,y0,x1,y1,0,count);
 for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++)assert_point(rects,count,x,y,"clipped union");
 got=game_collision_rects(x0,y0,x1,y1,limited,24);
 if(got!=(count>24?-1:count))fail("near-query capacity",x0,y0,x1,y1,count>24?-1:count,got);
 if(got>=0&&memcmp(limited,rects,(unsigned)count*sizeof limited[0]))fail("near-query result",x0,y0,x1,y1,0,1);
 near_queries++;
 if(count>24)near_24_overflows++;
 if((unsigned)count>near_max_rects){near_max_rects=(unsigned)count;near_max_room=room;near_max_query[0]=x0;near_max_query[1]=y0;near_max_query[2]=x1;near_max_query[3]=y1;}
}
static void wide_query(int x0,int y0,int x1,int y1){
 short rects[MAX_RECTS][4];int count=snapshot(x0,y0,x1,y1,rects,MAX_RECTS,0),xs[2*MAX_RECTS+2],ys[2*MAX_RECTS+2];
 unsigned nx=0,ny=0,i,j;int k;
 if(count<0)fail("wide query unsupported",x0,y0,x1,y1,0,count);
 xs[nx++]=x0;xs[nx++]=x1;ys[ny++]=y0;ys[ny++]=y1;
 /* Each returned edge and each neighbor is checked, including signed-short
  * extrema. Production bounds make every point outside the finite room solid. */
 for(k=0;k<count;k++){xs[nx++]=rects[k][0];xs[nx++]=rects[k][2];ys[ny++]=rects[k][1];ys[ny++]=rects[k][3];}
 for(i=0;i<nx;i++)for(j=0;j<ny;j++){
  int dx,dy;for(dy=-1;dy<=1;dy++)for(dx=-1;dx<=1;dx++){
   int x=xs[i]+dx,y=ys[j]+dy;if(x>=x0&&x<=x1&&y>=y0&&y<=y1)assert_point(rects,count,x,y,"full signed-short edge");
  }
 }
 capacity_proof(x0,y0,x1,y1,rects,count);full_range_queries++;
}
static void cast_distribution(int width,int height){
 int x,y;
 for(y=0;y<height;y++)for(x=0;x<width;x++){
  int x0=x<64?0:x-64,y0=y<64?0:y-64,x1=x+64,y1=y+64;
  short rects[MAX_RECTS][4];int count=snapshot(x0,y0,x1,y1,rects,MAX_RECTS,0),limited,i;
  if(count<0)fail("cast query supported overflow",x0,y0,x1,y1,0,count);
  limited=snapshot(x0,y0,x1,y1,0,48,0);
  if(limited!=(count>48?-1:count))fail("cast cap48",x0,y0,x1,y1,count>48?-1:count,limited);
  if((unsigned)count>cast_max_rects)cast_max_rects=(unsigned)count;
  if((unsigned)count>cast_room_max[room]){cast_room_max[room]=(unsigned)count;cast_room_query[room][0]=x0;cast_room_query[room][1]=y0;cast_room_query[room][2]=x1;cast_room_query[room][3]=y1;}
  cast_queries++;if(count>48){cast_48_overflows++;cast_room_overflow[room]++;}
  for(i=0;i<count;i++){
   assert_point(rects,count,rects[i][0],rects[i][1],"cast top left");
   assert_point(rects,count,rects[i][2],rects[i][3],"cast bottom right");
  }
 }
}
static void full_int_inputs(void){
 static const int values[]={INT_MIN,-32769,-32768,-1,0,1,32767,32768,INT_MAX};
 unsigned a,b,c,d;short rects[MAX_RECTS][4];
 for(a=0;a<9;a++)for(b=0;b<9;b++)for(c=0;c<9;c++)for(d=0;d<9;d++){
  int x0=values[a],y0=values[b],x1=values[c],y1=values[d];
  int invalid=x0<-32768||y0<-32768||x1>32767||y1>32767||x1<x0||y1<y0;
  int count=snapshot(x0,y0,x1,y1,rects,MAX_RECTS,invalid);
  if(!invalid){
   if(count<0)fail("valid short input rejected",x0,y0,x1,y1,0,count);
   assert_point(rects,count,x0,y0,"input corner");assert_point(rects,count,x1,y1,"input corner");
   assert_point(rects,count,x0,y1,"input corner");assert_point(rects,count,x1,y0,"input corner");
  }
  invalid_checks++;
 }
 snapshot(0,0,239,159,rects,0,1);snapshot(0,0,239,159,rects,257,1);snapshot(0,0,239,159,rects,UINT_MAX,1);
 if(game_collision_rects(0,0,239,159,0,256)!=-1)fail("null output",0,0,239,159,-1,0);
 invalid_checks+=4;
}
static void state_proof(unsigned area,int thorough){
 int width=area>=54?return_art_rooms[area-54].width:area>=38?magma_art_rooms[area-38].width:
  area>=30?south_art_rooms[area-30].width:area>=22?north_art_rooms[area-22].width:
  area==1||area==16||area==17?480:240,height=width==480?320:160;
 short rects[MAX_RECTS][4],saved_crates[2][2],saved_parcels[2][2];
 unsigned char saved_return[6],after_return[6];ReturnTrialProof saved_trial=return_game_trial;
 Save5State saved;MagmaPuzzle saved_magma=magma_game_puzzle;unsigned magma_before=collision_magma_digest();unsigned rf=room_flags,cf=chapter_flags,n;int bridge=bridge_open,torch=torches,count,x,y,i;
 room=(int)area;saved=adventure_save;collision_return_copy(saved_return);
 memcpy(saved_crates,region_game_crates,sizeof saved_crates);memcpy(saved_parcels,trial_parcels,sizeof saved_parcels);
 count=snapshot(-MARGIN,-MARGIN,width+MARGIN-1,height+MARGIN-1,rects,MAX_RECTS,0);
 if(count<0)fail("whole room overflow",0,0,width,height,0,count);
 if((unsigned)count>maximum_rects)maximum_rects=(unsigned)count;
 memset(difference,0,sizeof difference);
 for(i=0;i<count;i++){
  int l=rects[i][0]+MARGIN,t=rects[i][1]+MARGIN,r=rects[i][2]+MARGIN+1,d=rects[i][3]+MARGIN+1;
  difference[t][l]++;difference[t][r]--;difference[d][l]--;difference[d][r]++;
 }
 for(y=0;y<height+2*MARGIN;y++)for(x=0;x<width+2*MARGIN;x++){
  int want=solid(x-MARGIN,y-MARGIN)!=0,got;
  if(x)difference[y][x]+=difference[y][x-1];
  if(y)difference[y][x]+=difference[y-1][x];
  if(x&&y)difference[y][x]-=difference[y-1][x-1];
  got=difference[y][x]!=0;
  if(want!=got)fail("whole occupied union",x-MARGIN,y-MARGIN,x-MARGIN,y-MARGIN,want,got);
  actual_point_checks++;
 }
 capacity_proof(-MARGIN,-MARGIN,width+MARGIN-1,height+MARGIN-1,rects,count);
 for(n=0;n<(thorough?120u:12u);n++){
  int l=(int)(random_u()%(unsigned)(width+16))-8,t=(int)(random_u()%(unsigned)(height+16))-8;
  int r=l+(int)(random_u()%49u),d=t+(int)(random_u()%49u);
  small_query(l,t,r,d);
 }
 if(thorough){
  /* Cover overlapping 49x49 neighborhoods at an eight-pixel stride. These
   * include the 24-slot caller's near-query limits and all obstacle seams. */
  for(y=-8;y<height+8;y+=8)for(x=-8;x<width+8;x+=8){
   short near[MAX_RECTS][4];int nrect=snapshot(x-24,y-24,x+24,y+24,near,MAX_RECTS,0),limited;
   if(nrect<0)fail("near geometry count",x-24,y-24,x+24,y+24,0,nrect);
   limited=snapshot(x-24,y-24,x+24,y+24,0,24,0);
   if(limited!=(nrect>24?-1:nrect))fail("near bounded overflow",x,y,x,y,nrect>24?-1:nrect,limited);
   near_queries++;if(nrect>24)near_24_overflows++;
   if((unsigned)nrect>near_max_rects){near_max_rects=(unsigned)nrect;near_max_room=room;near_max_query[0]=x-24;near_max_query[1]=y-24;near_max_query[2]=x+24;near_max_query[3]=y+24;}
   assert_point(near,nrect,x,y,"near center");
  }
  cast_distribution(width,height);
  wide_query(SHRT_MIN,SHRT_MIN,SHRT_MAX,SHRT_MAX);
  wide_query(SHRT_MIN,0,SHRT_MAX,height-1);wide_query(0,SHRT_MIN,width-1,SHRT_MAX);
 }
 collision_return_copy(after_return);
 if(room!=(int)area||room_flags!=rf||chapter_flags!=cf||bridge_open!=bridge||torches!=torch
    ||memcmp(&saved,&adventure_save,sizeof saved)||memcmp(saved_crates,region_game_crates,sizeof saved_crates)
    ||memcmp(saved_parcels,trial_parcels,sizeof saved_parcels)||magma_before!=collision_magma_digest()||memcmp(&saved_magma,&magma_game_puzzle,sizeof saved_magma)
    ||memcmp(saved_return,after_return,sizeof saved_return)||memcmp(&saved_trial,&return_game_trial,sizeof saved_trial))fail("game state mutated",0,0,0,0,0,1);
 states++;if(area>=38&&area<=45)magma_states++;if(area>=54)return_states++;
}
static unsigned bit_subset(unsigned mask,unsigned ordinal){
 unsigned value=0,bit;for(bit=1;bit;bit<<=1)if(mask&bit){if(ordinal&1u)value|=bit;ordinal>>=1;}return value;
}
static void dynamic_pair_proof(unsigned area){
 int x0,y0,x1,y1,lo=area==15?72:64,hi=area==15?168:176;short (*objects)[2]=area==15?trial_parcels:region_game_crates;
 for(y0=56;y0<=104;y0+=16)for(x0=lo;x0<=hi;x0+=16)for(y1=56;y1<=104;y1+=16)for(x1=lo;x1<=hi;x1+=16){
  objects[0][0]=(short)x0;objects[0][1]=(short)y0;objects[1][0]=(short)x1;objects[1][1]=(short)y1;
  state_proof(area,0);if(area==15)parcel_pair_states++;else crate_pair_states++;
 }
 {static const short values[]={SHRT_MIN,-256,-13,-12,-11,-10,-1,0,5,11,12,13,63,64,65,72,73,159,160,227,228,239,240,480,SHRT_MAX};
  unsigned i,j;for(i=0;i<25;i++)for(j=0;j<25;j++){
   objects[0][0]=values[i];objects[0][1]=values[j];objects[1][0]=values[(i+11)%25];objects[1][1]=values[(j+19)%25];
   state_proof(area,0);
  }
 }
}
int main(int argc,char **argv){
 unsigned area,n,i;static const int integer_states[]={0,1,2,3,4,-1,INT_MIN,INT_MAX};
 memset(&adventure_save,0,sizeof adventure_save);
 trial_parcels[0][0]=88;trial_parcels[0][1]=88;trial_parcels[1][0]=136;trial_parcels[1][1]=88;
 region_game_crates[0][0]=80;region_game_crates[0][1]=88;region_game_crates[1][0]=144;region_game_crates[1][1]=88;
 if(argc>1){
  area=(unsigned)atoi(argv[1]);collision_magma_state(255,144,128);collision_return_state(0,0,0,0);
  state_proof(area,0);if(!area)small_query(27,66,27,66);return 0;
 }
 for(area=0;area<22;area++){
  if(area>=4&&area<14){
   const CampaignRoom *r=&campaign_rooms[area-4];unsigned mask=0,bit_count=0,bit;
   for(i=0;i<r->block_count;i++)mask|=r->blocks[i].flags;
   for(bit=1;bit;bit<<=1)if(mask&bit)bit_count++;
   for(n=0;n<(1u<<bit_count);n++){
    unsigned progress=bit_subset(mask,n);room_flags=progress&65535u;chapter_flags=progress>>16;state_proof(area,1);
    room_flags|=~mask;chapter_flags|=(~mask)>>16;state_proof(area,0);
   }
   room_flags=chapter_flags=0;
  }else if(area==1||area==2){
   for(i=0;i<8;i++){if(area==1)bridge_open=integer_states[i];else torches=integer_states[i];state_proof(area,1);}
  }else if(area==17){
   adventure_save.quests.objectives[Q_DRY]=0;state_proof(area,1);adventure_save.quests.objectives[Q_DRY]=2;state_proof(area,1);
   for(n=0;n<65536;n++){
    static const int points[][2]={{218,147},{219,146},{219,147},{219,188},{260,147},{260,188},{261,188},{260,189},{224,152},{239,167},{255,183}};
    short rects[MAX_RECTS][4];int count;adventure_save.quests.objectives[Q_DRY]=(Save4U16)n;
    count=snapshot(218,146,261,189,rects,MAX_RECTS,0);if(count<0)return 2;
    for(i=0;i<sizeof points/sizeof *points;i++)assert_point(rects,count,points[i][0],points[i][1],"all objective values");
   }
  }else state_proof(area,1);
  full_int_inputs();
 }
 for(area=22;area<38;area++){state_proof(area,1);full_int_inputs();}
 dynamic_pair_proof(15);dynamic_pair_proof(20);
 /* Actual Magma module, every legal movable-prop location and all two-prop
  * cell pairs, including overlapping cells; invalid cell bytes fail closed. */
 for(area=38;area<=45;area++){
  unsigned a,b;
  collision_magma_state(255,144,128);memset(&magma_game_puzzle,0,sizeof magma_game_puzzle);
  if(area==38||area==39){
   for(a=0;a<256;a++){
    collision_magma_state(255,area==38?a:144,area==39?a:128);
    state_proof(area,a==(area==38?144u:128u)||a==(area==38?168u:152u)||a==(area==38?192u:176u));
   }
  }else if(area==40){
   for(a=0;a<256;a++){
    collision_magma_state(a,144,128);magma_game_puzzle.cell[0]=(unsigned char)(a%35);
    state_proof(area,a<3||a==255);
   }
   for(a=0;a<256;a++){
    collision_magma_state(a&1u,144,128);magma_game_puzzle.cell[0]=(unsigned char)a;state_proof(area,0);
   }
  }else if(area>=42&&area<=44){
   for(a=0;a<35;a++)for(b=0;b<(area==42?1u:35u);b++){
    magma_game_puzzle.cell[0]=(unsigned char)a;magma_game_puzzle.cell[1]=(unsigned char)b;
    magma_game_puzzle.heat=(unsigned char)(a*7);magma_game_puzzle.brace=(unsigned char)(b*7);state_proof(area,a==14&&b==0);
   }
   for(a=35;a<256;a++){
    magma_game_puzzle.cell[0]=(unsigned char)a;magma_game_puzzle.cell[1]=(unsigned char)(290-a);state_proof(area,0);
   }
  }else state_proof(area,1);
  full_int_inputs();
 }

 /* All Return geometry-equivalence classes, plus every pair of representable
  * live mechanism bytes in room55 and every room57 screen byte. */
 for(area=54;area<=61;area++){
  for(n=0;n<(area==55?4u:area==57?2u:1u);n++){
   collision_return_state(n&1u,(n>>1)&1u,area==57?n:0,0);state_proof(area,1);
  }
  collision_return_state(255,255,255,255);state_proof(area,0);full_int_inputs();
 }
 room=55;
 for(n=0;n<65536;n++){
  static const int points[][2]={{82,88},{83,88},{92,51},{100,80},{116,100},{130,88},{131,88},{140,51},{148,80},{164,100},{88,92},{136,92}};
  short rects[MAX_RECTS][4];int count;unsigned char before[6],after[6];
  collision_return_state(n&255u,n>>8,n^255u,n);collision_return_copy(before);
  count=snapshot(80,48,165,103,rects,MAX_RECTS,0);if(count<0)return 4;
  for(i=0;i<sizeof points/sizeof *points;i++)assert_point(rects,count,points[i][0],points[i][1],"all Return setting-byte pairs");
  collision_return_copy(after);if(memcmp(before,after,sizeof before))return 5;
 }
 for(n=0;n<256;n++){collision_return_state(n,n^255u,n,n);state_proof(57,0);}
 {static const int invalid_rooms[]={INT_MIN,-100000,-1,46,47,48,49,50,51,52,53,62,69,70,100000,INT_MAX};
  short rects[MAX_RECTS][4];for(i=0;i<sizeof invalid_rooms/sizeof *invalid_rooms;i++){
   room=invalid_rooms[i];snapshot(100,100,120,120,rects,256,1);snapshot(INT_MIN,INT_MIN,INT_MAX,INT_MAX,rects,256,1);invalid_checks+=2;
  }
 }
 if(unsupported_calls){fprintf(stderr,"Unsupported production dispatch called\n");return 3;}
 printf("{\"states\":%u,\"exhaustive_world_margin_points\":%llu,\"query_point_checks\":%llu,\"snapshot_queries\":%llu,\"capacity_checks\":%llu,\"invalid_boundary_checks\":%llu,\"parcel_pair_states\":%u,\"crate_pair_states\":%u,\"object_extreme_pair_states\":1250,\"all_objective_u16_values\":65536,\"full_signed_short_queries\":%u,\"near_queries\":%u,\"near_24_overflows\":%u,\"maximum_near_rectangles\":%u,\"maximum_near_room\":%d,\"maximum_near_query\":[%d,%d,%d,%d],\"maximum_whole_room_rectangles\":%u,\"equality_mismatches\":0,\"read_only\":true,\"magma_states\":%u,\"return_states\":%u,\"return_setting_byte_pairs\":65536,\"cast_queries\":%u,\"cast_48_overflows\":%u,\"cast_max_rectangles\":%u,\"cast_room_distributions\":[",
 states,(unsigned long long)actual_point_checks,(unsigned long long)query_point_checks,(unsigned long long)query_checks,(unsigned long long)capacity_checks,(unsigned long long)invalid_checks,parcel_pair_states,crate_pair_states,full_range_queries,near_queries,near_24_overflows,near_max_rects,near_max_room,near_max_query[0],near_max_query[1],near_max_query[2],near_max_query[3],maximum_rects,magma_states,return_states,cast_queries,cast_48_overflows,cast_max_rects);
 for(area=0;area<62;area++)if(cast_room_max[area]){
  if(area)printf(",");
  printf("{\"room\":%u,\"max_rectangles\":%u,\"cap48_overflows\":%u,\"max_query\":[%d,%d,%d,%d]}",area,cast_room_max[area],cast_room_overflow[area],cast_room_query[area][0],cast_room_query[area][1],cast_room_query[area][2],cast_room_query[area][3]);
 }
 printf("]}\n");
 return 0;
}
