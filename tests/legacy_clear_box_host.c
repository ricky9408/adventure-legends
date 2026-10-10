/* Differential proof only: no emulator pacing or controller acceptance claim. */
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
#define COLD
#define FOOT 5
#define Q_DRY REGION_QUEST_DRY_ROAD
volatile int room,bridge_open,torches;
volatile unsigned room_flags,chapter_flags;
Save5State adventure_save;
short region_game_crates[2][2],trial_parcels[2][2];
static unsigned unsupported_calls;
/* These references belong to production solid()'s later-room dispatch. The
 * proof never calls them: the certificate must fail closed outside 0..37. */
int magma_game_solid(int x,int y){(void)x;(void)y;unsupported_calls++;return 1;}
int underwater_game_solid(int x,int y){(void)x;(void)y;unsupported_calls++;return 1;}
int return_game_solid(int x,int y){(void)x;(void)y;unsupported_calls++;return 1;}
int ab(int n);
#include "production_predicates.inc"
#include "legacy_clear_box.inc"

static unsigned prefix[321][481];
static uint64_t point_checks,small_box_checks,large_box_checks,invalid_checks;
static unsigned state_checks,parcel_pair_states,crate_pair_states;
static unsigned rng=0x19600824u;
static unsigned random_u(void){rng=rng*1664525u+1013904223u;return rng;}
static void fail(const char *kind,int x0,int y0,int x1,int y1,int want,int got){
 fprintf(stderr,"%s room=%d box=(%d,%d)-(%d,%d) want=%d got=%d "
         "flags=%u/%u bridge=%d torches=%d crates=%d,%d;%d,%d "
         "parcels=%d,%d;%d,%d\n",kind,room,x0,y0,x1,y1,want,got,
         room_flags,chapter_flags,bridge_open,torches,
         region_game_crates[0][0],region_game_crates[0][1],
         region_game_crates[1][0],region_game_crates[1][1],
         trial_parcels[0][0],trial_parcels[0][1],
         trial_parcels[1][0],trial_parcels[1][1]);
 exit(1);
}
static void check_box(int x0,int y0,int x1,int y1,int width,int height,const char *kind){
 int expected=0,got;
 if(x0>=0&&y0>=0&&x1>=x0&&y1>=y0&&x1<width&&y1<height){
  unsigned occupied=prefix[y1+1][x1+1]-prefix[y0][x1+1]
                    -prefix[y1+1][x0]+prefix[y0][x0];
  expected=!occupied;
 }
 got=legacy_game_clear_box(x0,y0,x1,y1);
 if(got!=expected)fail(kind,x0,y0,x1,y1,expected,got);
}
static void state_proof(unsigned area,int thorough){
 int width,height,x,y;unsigned n;Save5State saved;
 short saved_crates[2][2],saved_parcels[2][2];
 unsigned rf=room_flags,cf=chapter_flags;int bridge=bridge_open,torch=torches;
 room=(int)area;
 width=area==1||area==16||area==17||area==22||area==23||area==30||area==31?480:240;
 height=width==480?320:160;
 saved=adventure_save;
 memcpy(saved_crates,region_game_crates,sizeof saved_crates);
 memcpy(saved_parcels,trial_parcels,sizeof saved_parcels);
 memset(prefix[0],0,sizeof prefix[0]);
 for(y=0;y<height;y++){
  unsigned row_sum=0;prefix[y+1][0]=0;
  for(x=0;x<width;x++){
   int value=solid(x,y),got=legacy_game_clear_box(x,y,x,y);
   if(got!=!value)fail("point",x,y,x,y,!value,got);
   row_sum+=(unsigned)(value!=0);prefix[y+1][x+1]=prefix[y][x+1]+row_sum;
   point_checks++;
  }
 }
 /* Every 2x2 box, including the final in-world row and column, in every
  * dynamic state. Baseline/equivalence-class states also test every 9x9 and
  * 17x13 box, covering normal player feet and larger power-stamp bounds. */
 for(y=0;y<height-1;y++)for(x=0;x<width-1;x++){
  check_box(x,y,x+1,y+1,width,height,"2x2");small_box_checks++;
  if(thorough&&x+8<width&&y+8<height){
   check_box(x,y,x+8,y+8,width,height,"9x9");small_box_checks++;
  }
  if(thorough&&x+16<width&&y+12<height){
   check_box(x,y,x+16,y+12,width,height,"17x13");small_box_checks++;
  }
 }
 for(n=0;n<(thorough?6000u:80u);n++){
  int x0=(int)(random_u()%(unsigned)width),y0=(int)(random_u()%(unsigned)height);
  int x1=(int)(random_u()%(unsigned)width),y1=(int)(random_u()%(unsigned)height),t;
  if(x0>x1){t=x0;x0=x1;x1=t;}if(y0>y1){t=y0;y0=y1;y1=t;}
  check_box(x0,y0,x1,y1,width,height,"large");large_box_checks++;
 }
 if(thorough){
  int xs[]={INT_MIN,-100000,-1,0,4,5,11,12,227,228,width-6,width-1,width,INT_MAX};
  int ys[]={INT_MIN,-100000,-1,0,4,5,23,24,27,28,31,32,38,39,43,44,147,148,152,153,height-6,height-1,height,INT_MAX};
  unsigned a,b,c,d;
  for(a=0;a<sizeof xs/sizeof *xs;a++)for(b=0;b<sizeof ys/sizeof *ys;b++)
   for(c=0;c<sizeof xs/sizeof *xs;c++)for(d=0;d<sizeof ys/sizeof *ys;d++){
    check_box(xs[a],ys[b],xs[c],ys[d],width,height,"signed/boundary");invalid_checks++;
   }
  /* Every complete row/column and every prefix/suffix of world bounds. */
  for(x=0;x<width;x++){
   check_box(x,0,x,height-1,width,height,"column");
   check_box(x,5,width-6,height-6,width,height,"suffix");large_box_checks+=2;
  }
  for(y=0;y<height;y++){
   check_box(0,y,width-1,y,width,height,"row");
   check_box(5,y,width-6,height-6,width,height,"suffix");large_box_checks+=2;
  }
 }
 if(room!=(int)area||room_flags!=rf||chapter_flags!=cf||bridge_open!=bridge||torches!=torch
    ||memcmp(&saved,&adventure_save,sizeof saved)
    ||memcmp(saved_crates,region_game_crates,sizeof saved_crates)
    ||memcmp(saved_parcels,trial_parcels,sizeof saved_parcels)){
  fprintf(stderr,"Read-only contract violated\n");exit(2);
 }
 state_checks++;
}
static unsigned bit_subset(unsigned mask,unsigned ordinal){
 unsigned value=0,bit;
 for(bit=1;bit;bit<<=1)if(mask&bit){if(ordinal&1u)value|=bit;ordinal>>=1;}
 return value;
}
static void dynamic_pair_proof(unsigned area){
 int x0,y0,x1,y1,lo=area==15?72:64,hi=area==15?168:176;
 short (*objects)[2]=area==15?trial_parcels:region_game_crates;
 for(y0=56;y0<=104;y0+=16)for(x0=lo;x0<=hi;x0+=16)
  for(y1=56;y1<=104;y1+=16)for(x1=lo;x1<=hi;x1+=16){
   objects[0][0]=(short)x0;objects[0][1]=(short)y0;
   objects[1][0]=(short)x1;objects[1][1]=(short)y1;
   state_proof(area,0);
   if(area==15)parcel_pair_states++;else crate_pair_states++;
  }
 /* Full signed-short extrema and off-lattice live values: certificates do not
  * assume that reset/progression has normalized transient geometry. */
 {static const short values[]={SHRT_MIN,-256,-13,-12,-11,-10,-1,0,5,11,12,13,63,64,65,72,73,159,160,227,228,239,240,480,SHRT_MAX};
  unsigned i;
  for(i=0;i<sizeof values/sizeof *values;i++){
   objects[0][0]=values[i];objects[0][1]=values[(i+7)%25];
   objects[1][0]=values[(i+11)%25];objects[1][1]=values[(i+19)%25];
   state_proof(area,0);
  }
 }
}
int main(void){
 unsigned area,n,i;static const int integer_states[]={0,1,2,3,4,-1,INT_MIN,INT_MAX};
 memset(&adventure_save,0,sizeof adventure_save);
 trial_parcels[0][0]=88;trial_parcels[0][1]=88;
 trial_parcels[1][0]=136;trial_parcels[1][1]=88;
 region_game_crates[0][0]=80;region_game_crates[0][1]=88;
 region_game_crates[1][0]=144;region_game_crates[1][1]=88;
 for(area=0;area<38;area++){
  if(area>=4&&area<14){
   const CampaignRoom *r=&campaign_rooms[area-4];unsigned mask=0,bit_count=0,bit;
   for(i=0;i<r->block_count;i++)mask|=r->blocks[i].flags;
   for(bit=1;bit;bit<<=1)if(mask&bit)bit_count++;
   for(n=0;n<(1u<<bit_count);n++){
    unsigned progress=bit_subset(mask,n);
    room_flags=progress&65535u;chapter_flags=progress>>16;
    state_proof(area,1);
    /* All unrelated bits set must leave every point/box result unchanged. */
    room_flags|=~mask;chapter_flags|=(~mask)>>16;state_proof(area,0);
   }
   room_flags=chapter_flags=0;
  }else if(area==1||area==2){
   for(i=0;i<sizeof integer_states/sizeof *integer_states;i++){
    if(area==1)bridge_open=integer_states[i];else torches=integer_states[i];
    state_proof(area,1);
   }
  }else if(area==17){
   adventure_save.quests.objectives[Q_DRY]=0;state_proof(area,1);
   adventure_save.quests.objectives[Q_DRY]=2;state_proof(area,1);
   room=17;
   /* Every representable live objective value, whole sluice bounds and
    * four immediately adjacent strips, independently production. */
   for(n=0;n<65536;n++){
    static const int boxes[][4]={{219,147,260,188},{218,147,218,188},
     {219,146,260,146},{261,147,261,188},{219,189,260,189},
     {220,150,230,159},{225,153,255,182}};
    adventure_save.quests.objectives[Q_DRY]=(Save4U16)n;
    for(i=0;i<sizeof boxes/sizeof *boxes;i++){
     const int *b=boxes[i];int x,y,want=1,got;
     for(y=b[1];y<=b[3]&&want;y++)for(x=b[0];x<=b[2];x++)if(solid(x,y)){want=0;break;}
     got=legacy_game_clear_box(b[0],b[1],b[2],b[3]);
     if(got!=want)fail("objective",b[0],b[1],b[2],b[3],want,got);
     large_box_checks++;
    }
   }
  }else state_proof(area,1);
 }
 dynamic_pair_proof(15);dynamic_pair_proof(20);
 {static const int invalid_rooms[]={INT_MIN,-100000,-1,38,39,40,45,46,53,54,61,62,100000,INT_MAX};
  for(i=0;i<sizeof invalid_rooms/sizeof *invalid_rooms;i++){
   room=invalid_rooms[i];
   if(legacy_game_clear_box(110,110,120,120)||legacy_game_clear_box(INT_MIN,INT_MIN,INT_MAX,INT_MAX))return 3;
   invalid_checks+=2;
  }
 }
 if(unsupported_calls){fprintf(stderr,"Unsupported reference dispatched\n");return 4;}
 printf("{\"states\":%u,\"point_checks\":%llu,\"small_box_checks\":%llu,"
        "\"large_box_checks\":%llu,\"signed_boundary_checks\":%llu,"
        "\"parcel_pair_states\":%u,\"crate_pair_states\":%u,"
        "\"all_objective_u16_values\":65536,\"equality_mismatches\":0,"
        "\"read_only\":true}\n",state_checks,(unsigned long long)point_checks,
        (unsigned long long)small_box_checks,(unsigned long long)large_box_checks,
        (unsigned long long)invalid_checks,parcel_pair_states,crate_pair_states);
 return 0;
}
