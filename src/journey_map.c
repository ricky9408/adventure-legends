#include "journey_map.h"
#include "journey_map_text.h"
#include "assets.h"
#include "progression.h"
#include "connected_roads.h"
#include "travel_feedback.h"
#include "campaign_rules.h"
#include "regional_quests.h"
#include "northern_quests.h"
#include "southern_quests.h"
#include "magma_quests.h"
#include "underwater_quests.h"
#include "return_quests.h"
#include "horizons_quests.h"
#include "covenants_quests.h"

extern volatile int room,bridge_open,torches;
extern volatile unsigned chapter_flags,room_flags,story_seen;
extern int seen_temple,seen_boss;
extern int horizons_game_route_allowed(unsigned,unsigned);
extern int covenants_game_route_allowed(unsigned,unsigned);
extern void box(int,int,int,int),rect(int,int,int,int,unsigned char);
extern void text(int,int,int,int),centered(int,int,int);

enum { JM_GATE_NONE,JM_GATE_TARGET,JM_GATE_BRIDGE,JM_GATE_TORCHES };
typedef struct {unsigned char room,target,spawn,kind,direction,gate;} MapInterior;
#include "journey_map_data.inc"

/* All labels, topology and code are ROM. Only this small cursor/knowledge
 * and displayed-exit cache is transient EWRAM; it never enters the save codec or IWRAM. */
static struct {
 unsigned known[3];
 unsigned char place,region,selection,exit,overview,from_list,count,valid,origin,home_count;
 JourneyMapExit exits[12],home_exits[12];
} map;
static const unsigned char region_first[9]={0,16,22,30,38,46,54,62,70};
static const unsigned char region_last[9]={15,21,29,37,45,53,61,69,77};
static const short place_names[78]={
 TX_VILLAGE,TX_FOREST,TX_TEMPLE,TX_BOSS,
 TX_C_ROOM_4,TX_C_ROOM_5,TX_C_ROOM_6,TX_C_ROOM_7,TX_C_ROOM_8,
 TX_C_ROOM_9,TX_C_ROOM_10,TX_C_ROOM_11,TX_C_ROOM_12,TX_C_ROOM_13,
 TX_T_ROOM_WIND,TX_T_ROOM_STONE,
 TX_RG_ROOM_TOWN,TX_RG_ROOM_BASIN,TX_RG_ROOM_FOUNDRY,TX_RG_ROOM_TIDE,TX_RG_ROOM_STORE,TX_RG_ROOM_GARDEN,
 TX_NT_ROOM22,TX_NT_ROOM23,TX_NT_ROOM24,TX_NT_ROOM25,TX_NT_ROOM26,TX_NT_ROOM27,TX_NT_ROOM28,TX_NT_ROOM29,
 TX_ST_ROOM30,TX_ST_ROOM31,TX_ST_ROOM32,TX_ST_ROOM33,TX_ST_ROOM34,TX_ST_ROOM35,TX_ST_ROOM36,TX_ST_ROOM37,
 TX_MG_ROOM38,TX_MG_ROOM39,TX_MG_ROOM40,TX_MG_ROOM41,TX_MG_ROOM42,TX_MG_ROOM43,TX_MG_ROOM44,TX_MG_ROOM45,
 TX_UW_ROOM46,TX_UW_ROOM47,TX_UW_ROOM48,TX_UW_ROOM49,TX_UW_ROOM50,TX_UW_ROOM51,TX_UW_ROOM52,TX_UW_ROOM53,
 TX_RT_ROOM54,TX_RT_ROOM55,TX_RT_ROOM56,TX_RT_ROOM57,TX_RT_ROOM58,TX_RT_ROOM59,TX_RT_ROOM60,TX_RT_ROOM61,
 TX_HZ_ROOM62,TX_HZ_ROOM63,TX_HZ_ROOM64,TX_HZ_ROOM65,TX_HZ_ROOM66,TX_HZ_ROOM67,TX_HZ_ROOM68,TX_HZ_ROOM69,
 TX_CV_ROOM70,TX_CV_ROOM71,TX_CV_ROOM72,TX_CV_ROOM73,TX_CV_ROOM74,TX_CV_ROOM75,TX_CV_ROOM76,TX_CV_ROOM77
};
static unsigned region_of(unsigned a){return a<16?0:a<22?1:2+(a-22)/8;}

/* Deliberately use pure quest predicates. Several similarly named game
 * helpers call sync() and would mutate campaign bytes while inspecting. */
static int target_open(unsigned a,unsigned spawn){
 if(a<16)return 1;
 if(a<22)return regional_can_enter(&adventure_save,a);
 if(a<30)return northern_can_enter(&adventure_save,a);
 if(a<38)return southern_can_enter(&adventure_save,a);
 if(a<46)return magma_can_enter(&adventure_save,a);
 if(a<54)return underwater_can_enter(&adventure_save,a);
 if(a<62)return return_can_enter(&adventure_save,a);
 if(a<70)return horizons_game_route_allowed(a,spawn);
 return a<78?covenants_game_route_allowed(a,spawn):0;
}
static int route_open(unsigned gate,unsigned target,unsigned spawn){
 if(gate==ROAD_GATE_NONE)return 1;
 if(gate==ROAD_GATE_GROVE)return !!(chapter_flags&SAVE4_GROVE_CLEAR);
 if(gate==ROAD_GATE_SKY)return !!(chapter_flags&SAVE4_SKY_CLEAR);
 return target_open(target,spawn);
}
static unsigned position_direction(unsigned area,int x,int y){
 unsigned w=map_sizes[area][0],h=map_sizes[area][1];
 int horizontal=x<(int)(w/3)?-1:x>(int)(2*w/3)?1:0;
 int vertical=y<(int)(h/3)?-1:y>(int)(2*h/3)?1:0;
 if(vertical<0)return horizontal<0?JOURNEY_NW:horizontal>0?JOURNEY_NE:JOURNEY_N;
 if(vertical>0)return horizontal<0?JOURNEY_SW:horizontal>0?JOURNEY_SE:JOURNEY_S;
 return horizontal<0?JOURNEY_W:horizontal>0?JOURNEY_E:JOURNEY_CENTER;
}
static unsigned road_direction(unsigned index,unsigned first,unsigned end){
 const ConnectedRoad*r=&connected_roads[index];unsigned i;
 for(i=first;i<end;i++)if(i!=index&&connected_roads[i].edge==r->edge&&!(connected_roads[i].reserved&ROAD_ARRIVAL_ONLY)){
  static const unsigned char side[4][2]={{JOURNEY_N_LEFT,JOURNEY_N_RIGHT},{JOURNEY_E_TOP,JOURNEY_E_BOTTOM},{JOURNEY_S_LEFT,JOURNEY_S_RIGHT},{JOURNEY_W_TOP,JOURNEY_W_BOTTOM}};
  return side[r->edge][r->center>connected_roads[i].center];
 }
 return r->edge;
}
static int secret_visible(const TravelEntry*e){
 /* Concealed shortcut positions are not drawn before their discovery. */
 if(e->room==32&&e->target==30&&e->spawn==4)return save5_quest_state(&adventure_save.quests,29)>=SAVE5_QUEST_READY;
 if((e->room==39&&e->target==40)||(e->room==40&&e->target==39))return !!(adventure_save.quests.objectives[35]&2);
 if(e->room==36&&e->target==31)return !!(adventure_save.quests.objectives[24]&4);
 if(e->room==44&&e->target==39)return !!(adventure_save.quests.objectives[32]&4);
 return 1;
}
static unsigned travel_kind(const TravelEntry*e){
 if(e->action==TRAVEL_FERRY||(e->room==30&&e->target==22))return JOURNEY_FERRY;
 if(e->action==TRAVEL_LIFT||(e->room==38&&e->target==30))return JOURNEY_LIFT;
 if(e->action==TRAVEL_DIVE)return JOURNEY_DIVE;
 if((e->room==39&&e->target==40)||(e->room==40&&e->target==39)||
    (e->room==32&&e->target==30&&e->spawn==4)||(e->room==36&&e->target==31)||
    (e->room==44&&e->target==39))return JOURNEY_PASSAGE;
 return JOURNEY_DOOR;
}
static int campaign_north_open(const CampaignRoom*c){
 unsigned i,required=c->north_flags,bits=room_flags|(chapter_flags<<16);
 /* Some passages (notably the stone arch) close inside the room rather than
  * on its doorway. All original chapter blocks belong to that northward path. */
 for(i=0;i<c->block_count;i++)required|=c->blocks[i].flags;
 return (bits&required)==required;
}
static int map_exit_query(unsigned area,unsigned index,JourneyMapExit*out){
 unsigned i,first,end,count=0;JourneyMapExit e;
 if(area>=78)return 0;
#define EMIT(value) do{if(count++==index&&out){e=(value);*out=e;return 1;}}while(0)
 connected_road_range(area,&first,&end);
 for(i=first;i<end;i++){
  const ConnectedRoad*r=&connected_roads[i];if(r->reserved&ROAD_ARRIVAL_ONLY)continue;
  EMIT(((JourneyMapExit){r->target,JOURNEY_ROAD,(unsigned char)road_direction(i,first,end),(unsigned char)route_open(r->gate,r->target,r->spawn),1}));
 }
 for(i=0;i<connected_door_count;i++){
  const ConnectedDoor*d=&connected_doors[i];if(d->room!=area)continue;
  EMIT(((JourneyMapExit){d->target,(d->room==55||d->target==55)?JOURNEY_STAIRS:JOURNEY_DOOR,
     (unsigned char)position_direction(area,d->x+d->w/2,d->y+d->h/2),
     (unsigned char)route_open(d->gate,d->target,d->spawn),1}));
 }
 for(i=0;i<travel_entry_count;i++){
  const TravelEntry*t=&travel_entries[i];unsigned named=1;
  if(t->room!=area||connected_road_managed(area,t->target)||!secret_visible(t))continue;
  /* Trial signs disclose an entrance, not an undiscovered room/reward name. */
  if(t->action==TRAVEL_TRIAL)named=(unsigned)room==t->target||
      !!(adventure_save.roster.lifetime_field_aid[0]&(t->target==14?64u:128u));
  EMIT(((JourneyMapExit){t->target,(unsigned char)travel_kind(t),
     (unsigned char)position_direction(area,t->x+t->w/2,t->y+t->h/2),
     (unsigned char)target_open(t->target,t->spawn),(unsigned char)named}));
 }
 if(area>=4&&area<14){
  const CampaignRoom*c=&campaign_rooms[area-4];
  if(c->north_room)EMIT(((JourneyMapExit){c->north_room,JOURNEY_DOOR,JOURNEY_N,(unsigned char)campaign_north_open(c),1}));
  if(!connected_road_managed(area,c->south_room))EMIT(((JourneyMapExit){c->south_room,JOURNEY_DOOR,JOURNEY_S,1,1}));
 }
 for(i=0;i<sizeof map_interiors/sizeof map_interiors[0];i++){
  const MapInterior*d=&map_interiors[i];unsigned open;
  if(d->room!=area||connected_road_managed(area,d->target))continue;
  if(count++==index&&out){
   open=d->gate==JM_GATE_NONE?1:d->gate==JM_GATE_BRIDGE?!!bridge_open:
        d->gate==JM_GATE_TORCHES?torches==3:target_open(d->target,d->spawn);
   *out=(JourneyMapExit){d->target,d->kind,d->direction,(unsigned char)open,1};return 1;
  }
 }
#undef EMIT
 return out?0:(int)count;
}
int journey_map_exit(unsigned area,unsigned index,JourneyMapExit*out){return out?map_exit_query(area,index,out):0;}
static int recorded(unsigned a){
 unsigned g;if(a==(unsigned)room||a<2)return 1;
 if(a>=16){g=region_of(a);return !!(adventure_save.quests.region_flags[g-1]&(1u<<(a-region_first[g])));}
 if(a==2)return seen_temple||(chapter_flags&SAVE4_GROVE_CLEAR);
 if(a==3)return seen_boss||(chapter_flags&SAVE4_GROVE_CLEAR);
 if(a==14||a==15)return !!(adventure_save.roster.lifetime_field_aid[0]&(a==14?64u:128u));
 if(a<=8){if(chapter_flags&SAVE4_SKY_CLEAR)return 1;if(a==4)return !!(chapter_flags&SAVE4_GROVE_CLEAR);
  if(a==5)return !!(story_seen&SAVE4_SEEN_SKY_INTRO);
  return a==6?!!(room_flags&CF_SKY_VANE):a==7?!!(room_flags&CF_SKY_PATROL_CLEAR):
      (room_flags&(CF_RELAY_LEFT|CF_RELAY_RIGHT|CF_RELAY_FIRE))==(CF_RELAY_LEFT|CF_RELAY_RIGHT|CF_RELAY_FIRE);
 }
 if(chapter_flags&SAVE4_CORE_CLEAR)return 1;
 if(a==9)return !!(chapter_flags&SAVE4_SKY_CLEAR);
 if(a==10)return !!(room_flags&CF_CORE_PATH_OPEN);
 if(a==11)return (room_flags&(CF_WEIGHT_WEST|CF_WEIGHT_EAST))==(CF_WEIGHT_WEST|CF_WEIGHT_EAST);
 if(a==12)return (room_flags&(CF_ROOT_CHANNEL|CF_THORNS_BURNED))==(CF_ROOT_CHANNEL|CF_THORNS_BURNED);
 return (room_flags&(CF_LAMP_FIRE|CF_LAMP_NATURE|CF_LAMP_WIND|CF_LAMP_STONE))==(CF_LAMP_FIRE|CF_LAMP_NATURE|CF_LAMP_WIND|CF_LAMP_STONE);
}
int journey_map_is_known(unsigned a){return a<78&&!!(map.known[a>>5]&(1u<<(a&31)));}
static void mark_known(unsigned a){map.known[a>>5]|=1u<<(a&31);}
static unsigned places(unsigned region,unsigned index){unsigned a;for(a=region_first[region];a<=region_last[region];a++)if(journey_map_is_known(a)){if(!index--)return a;}return 255;}
static unsigned place_count(unsigned region){unsigned n=0;while(places(region,n)!=255)n++;return n;}
static void prepare_exits(void){unsigned n=0;while(n<12&&journey_map_exit(map.place,n,&map.exits[n]))n++;map.count=(unsigned char)n;map.exit=0;}
static void select_place(unsigned a){unsigned i;map.region=(unsigned char)region_of(a);for(i=0;places(map.region,i)!=255;i++)if(places(map.region,i)==a){map.selection=(unsigned char)i;return;}map.selection=0;}
static void build_knowledge(void){unsigned a,i,seeds[3]={0,0,0};map.known[0]=map.known[1]=map.known[2]=0;
 /* Generated public adjacency bitsets make this one bounded78-room pass.
  * Only the seven concealed entrances need their live discovery checks. */
 for(a=0;a<78;a++)if(recorded(a)){
  mark_known(a);seeds[a>>5]|=1u<<(a&31);
  for(i=0;i<3;i++)map.known[i]|=map_known_adjacency[a][i];
 }
 for(i=0;i<sizeof map_knowledge_special/sizeof map_knowledge_special[0];i++){
  const TravelEntry*t=&travel_entries[map_knowledge_special[i]];
  if(!(seeds[t->room>>5]&(1u<<(t->room&31)))||!secret_visible(t))continue;
  if(t->action!=TRAVEL_TRIAL||(unsigned)room==t->target||(adventure_save.roster.lifetime_field_aid[0]&(t->target==14?64u:128u)))mark_known(t->target);
 }
}
void journey_map_begin(void){map.valid=0;}
void journey_map_open(void){unsigned i,a=(unsigned)room<78?(unsigned)room:0;
 if(!map.valid||map.origin!=a){
  build_knowledge();map.place=(unsigned char)a;prepare_exits();map.origin=(unsigned char)a;map.home_count=map.count;
  for(i=0;i<map.count;i++)map.home_exits[i]=map.exits[i];map.valid=1;
 }
 map.place=map.origin;map.count=map.home_count;
 for(i=0;i<map.count;i++)map.exits[i]=map.home_exits[i];
 select_place(map.place);map.exit=map.overview=map.from_list=0;
}
void journey_map_reset(void){journey_map_begin();journey_map_open();}
unsigned journey_map_selected_place(void){return map.place;}
unsigned journey_map_selected_exit(void){return map.exit;}
unsigned journey_map_overview(void){return map.overview;}
int journey_map_input(int input){unsigned n,direction=(unsigned)input&240u;
 if(input&2){if(map.overview){journey_map_open();return 1;}if(map.from_list){map.overview=1;return 1;}return 0;}
 if(input&4)return 1;
 if(direction&&direction!=16&&direction!=32&&direction!=64&&direction!=128)return 1;
 if(map.overview){
  if(direction==16||direction==32){unsigned i;for(i=0;i<9;i++){map.region=(unsigned char)((map.region+(direction==16?1:8))%9);if(place_count(map.region))break;}map.selection=0;}
  else if(direction){n=place_count(map.region);if(n)map.selection=(unsigned char)((map.selection+(direction==128?1:n-1))%n);}
  else if(input&1){n=places(map.region,map.selection);if(n<78){map.place=(unsigned char)n;map.overview=0;map.from_list=1;prepare_exits();}}
 }else if(direction==64||direction==128){n=map.count;if(n)map.exit=(unsigned char)((map.exit+(direction==128?1:n-1))%n);}
 else if(direction==16||direction==32){map.overview=1;select_place(map.place);return journey_map_input(input);}
 else if(input&1){map.overview=1;select_place(map.place);}
 return 1;
}
static void jm_center(unsigned id,int y,unsigned char color){journey_map_text(id,(240-journey_map_texts[id].width)/2,y,color);}
static void scroll_marks(unsigned first,unsigned end,unsigned total){if(first)rect(224,63,3,2,PAL_GOLD3);if(end<total)rect(224,134,3,2,PAL_GOLD3);}
void journey_map_draw(void){unsigned i,first,total;JourneyMapExit e;
 box(8,31,224,123);
 if(map.overview){
  jm_center(JM_REGION_0+map.region,35,PAL_GOLD3);jm_center(JM_LIST_NOTE,50,PAL_TEAL2);
  total=place_count(map.region);first=map.selection>3?map.selection-3:0;
  for(i=first;i<total&&i<first+4;i++){unsigned a=places(map.region,i);int y=64+(int)(i-first)*18;
   if(i==map.selection)rect(13,y,211,18,PAL_STONE2);
   if(a==(unsigned)room)rect(16,y+5,4,4,PAL_HEART);
   else{rect(16,y+5,4,4,PAL_TEAL2);rect(17,y+6,2,2,i==map.selection?PAL_STONE2:1);}
   text(place_names[a],23,y,i==map.selection?PAL_GOLD3:PAL_GOLD4);
  }
  scroll_marks(first,first+4,total);jm_center(JM_LIST_KEYS,139,PAL_TEAL2);return;
 }
 centered(place_names[map.place],35,PAL_GOLD3);
 journey_map_text(map.place==(unsigned)room?JM_CURRENT:JM_RECORD,16,50,PAL_TEAL2);
 journey_map_text(JM_CLOSE,224-journey_map_texts[JM_CLOSE].width,50,PAL_TEAL2);
 total=map.count;first=map.exit/2*2;
 for(i=first;i<total&&i<first+2;i++){
  int y=64+(int)(i-first)*34;e=map.exits[i];
  if(i==map.exit)rect(13,y-1,211,31,PAL_STONE2);
  journey_map_text(JM_N_ROAD+e.direction*7+e.kind,18,y,e.open?PAL_TEAL2:PAL_STONE4);
  journey_map_text(e.open?JM_OPEN:JM_CLOSED,187,y,e.open?PAL_TEAL2:PAL_GOLD3);
  if(e.named&&journey_map_is_known(e.target))text(place_names[e.target],18,y+14,i==map.exit?PAL_GOLD3:PAL_GOLD4);
  else journey_map_text(JM_UNKNOWN,18,y+14,PAL_GOLD4);
 }
 if(!total)jm_center(JM_EMPTY,91,PAL_GOLD4);
 scroll_marks(first,first+2,total);jm_center(JM_DETAIL_KEYS,139,PAL_TEAL2);
}
