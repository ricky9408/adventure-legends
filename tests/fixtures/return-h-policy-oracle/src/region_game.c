/* Original Reedhaven gameplay. All rewards pass the existing atomic ledger.
 * Host checks are synthetic C runtime tests; controller acceptance is separate. */
#include "region_game.h"
#include "region_art.h"
#include "regional_quests.h"
#include "progression.h"
#include "assets.h"
#ifdef REGION_GAME_HOST_TEST
#include "region_game_test_ui.h"
#else
#include "ui.h"
#endif
#if defined(__arm__)
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
#else
#define COLD
#endif
#define PLAY 1
#define JOURNAL_TAB 5
#define KEY_A 1
#define KEY_DOWN 128
#define KEY_UP 64
#define FOOT 5
#define Q_PRACTICE REGION_QUEST_PRACTICE
#define Q_DRY REGION_QUEST_DRY_ROAD
#define Q_WATER REGION_QUEST_WATER_BOND
#define Q_METAL REGION_QUEST_METAL_BOND
#define Q_POOLS REGION_QUEST_TIDE_POOLS
#define Q_WEAVER REGION_QUEST_WEAVER
#define Q_FRIENDS REGION_QUEST_FRIENDSHIPS
#define Q_LATCH REGION_QUEST_LATCH
#define Q_CRAFT REGION_QUEST_MAIL
#define Q_GARDEN REGION_QUEST_GARDEN
#define Q_RING REGION_QUEST_RING
extern volatile int room,px,py,game_state,summoned,roll_ticks,transition_lock,checkpoint_spawn,camera_x,camera_y;
extern volatile unsigned chapter_flags;
extern int face,keys,journal_tab;
extern void enter_room(int,int),save_game(void),dialogue(int,int,int),toast(int),text(int,int,int,int),centered(int,int,int),box(int,int,int,int);
extern void rect(int,int,int,int,unsigned char),line(int,int,int,int,int),sprite(const unsigned char*,int,int,int,int,int);
unsigned region_game_revision,region_game_journal_selection;
short region_game_crates[2][2];
unsigned char region_game_foundry_step,region_game_pool_levels[2],region_game_valves[2],region_game_garden_step;
static unsigned event_dirty,field_pool_mask,target_flash,door_notice,roll_serial,last_garden_roll;
static int was_rolling;
static const short spawns[6][6][2]={
 {{240,284},{240,52},{104,232},{344,152},{88,128},{344,248}},
 {{240,284},{360,72},{120,232},{0,0},{0,0},{0,0}},
 {{120,132},{0,0},{0,0},{0,0},{0,0},{0,0}},
 {{120,132},{0,0},{0,0},{0,0},{0,0},{0,0}},
 {{120,132},{0,0},{0,0},{0,0},{0,0},{0,0}},
 {{120,132},{0,0},{0,0},{0,0},{0,0},{0,0}}};
static const unsigned char spawn_counts[6]={6,3,1,1,1,1};
static const short plates[2][2]={{80,56},{160,104}};
static const short garden_stones[3][2]={{72,72},{120,72},{168,104}};
static int abs_i(int n){return n<0?-n:n;}
static int near_xy(int x,int y,int xx,int yy,int radius){return abs_i(x-xx)+abs_i(y-yy)<radius;}
static int close_to(int x,int y,int radius){return near_xy(px,py,x,y,radius);}
static unsigned state(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
static int done(unsigned q){return state(q)==SAVE5_QUEST_CLAIMED;}
static int ready(unsigned q){return state(q)>=SAVE5_QUEST_READY;}
static void changed(void){region_game_revision++;progression_revision++;}
static void sync_chapter(void){adventure_save.campaign.chapter_flags=(Save4U8)chapter_flags;}
static COLD void checkpoint(void){
 sync_chapter();if(region_game_is_room((unsigned)room)){
  adventure_save.campaign.room=(Save4U8)room;
  adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;
 }
}
static COLD void persist(void){if(event_dirty){checkpoint();changed();save_game();event_dirty=0;}}
static COLD void say(int a,int b){persist();dialogue(a,b,PLAY);}
static COLD int offer(unsigned q){int r;sync_chapter();r=regional_quest_offer(&adventure_save,q);if(r==REGION_QUEST_CHANGED)event_dirty=1;return r!=REGION_QUEST_LOCKED&&r!=REGION_QUEST_INVALID;}
static COLD void objective(unsigned q,unsigned bit){int r=regional_quest_objective(&adventure_save,q,bit);if(r==REGION_QUEST_CHANGED||r==REGION_QUEST_NOW_READY)event_dirty=1;}
static COLD void complete(unsigned q){unsigned b,m=regional_quest_mask(q);if(!offer(q))return;for(b=1;b<=4;b<<=1)if(m&b)objective(q,b);}
static COLD void claim_scene(unsigned q){int r;sync_chapter();r=regional_quest_claim(&adventure_save,q);
 if(r==REGION_QUEST_REWARDED){event_dirty=1;progression_refresh();
  if(q==Q_WATER)say(TX_RG_WATER_JOIN_A,TX_RG_JOIN_SELECT_B);
  else if(q==Q_METAL)say(TX_RG_METAL_JOIN_A,TX_RG_JOIN_SELECT_B);
  else if(q==Q_POOLS)say(TX_RG_TIDE_REWARD_A,TX_RG_TIDE_REWARD_B);
  else say(TX_RG_RECEIVED_A,TX_RG_RECEIVED_B);
 }else if(r==REGION_QUEST_RESERVED)say(TX_MG_RESERVED,TX_MG_RESERVEDB);else if(r==REGION_QUEST_FULL)say(TX_RG_FULL_A,TX_RG_FULL_B);
 else if(r==REGION_QUEST_UNCHANGED)say(TX_RG_RETURN_A,TX_RG_RETURN_B);
 else say(TX_RG_SAVE_RETRY,TX_RG_JOIN_SELECT_B);
}
int region_game_is_room(unsigned area){return area>=16&&area<=21;}
COLD void region_game_reset(void){unsigned solved=ready(Q_WEAVER);
 region_game_foundry_step=(unsigned char)(ready(Q_METAL)?3:0);
 region_game_pool_levels[0]=region_game_pool_levels[1]=(unsigned char)(ready(Q_POOLS)?1:0);
 region_game_valves[0]=region_game_valves[1]=(unsigned char)(ready(Q_POOLS)?1:0);
 region_game_crates[0][0]=80;region_game_crates[0][1]=(short)(solved?56:88);
 region_game_crates[1][0]=(short)(solved?160:144);region_game_crates[1][1]=(short)(solved?104:88);
 region_game_garden_step=(unsigned char)(ready(Q_GARDEN)?3:0);
 field_pool_mask=0;was_rolling=0;roll_serial=0;last_garden_roll=~0u;
 target_flash=0;changed();
}
COLD int region_game_enter(unsigned area,unsigned spawn){int r;
 sync_chapter();if(!region_game_is_room(area)||spawn>=spawn_counts[area-16]||!regional_can_enter(&adventure_save,area))return 0;
 room=(int)area;px=spawns[area-16][spawn][0];py=spawns[area-16][spawn][1];checkpoint_spawn=(int)spawn;
 event_dirty=0;r=regional_visit(&adventure_save,area);if(r==REGION_QUEST_CHANGED)event_dirty=1;
 if((area==16||area==17)&&spawn==2){r=regional_anchor(&adventure_save,area);if(r==REGION_QUEST_CHANGED)event_dirty=1;}
 region_game_reset();door_notice=0;checkpoint();persist();
 if(area>=18){unsigned q=area==18?Q_METAL:area==19?Q_POOLS:area==20?Q_WEAVER:Q_GARDEN;if(state(q)==SAVE5_QUEST_ACTIVE)toast(TX_RG_REENTER_RESET);}
 return 1;
}
static int foot_in(int x,int y,int rx,int ry,int w,int h){return x+FOOT>=rx&&x-FOOT<rx+w&&y+FOOT>=ry&&y-FOOT<ry+h;}
int region_game_solid(int x,int y){const RegionArtRoom*r;unsigned i;if(!region_game_is_room((unsigned)room))return 0;r=&region_art_rooms[room-16];
 if(x<FOOT||y<FOOT||x>=r->width-FOOT||y>=r->height-FOOT)return 1;
 for(i=0;i<r->solid_count;i++){const RegionArtRect*s=&r->solids[i];if(foot_in(x,y,s->x,s->y,s->w,s->h))return 1;}
 if(room==17&&!(adventure_save.quests.objectives[Q_DRY]&2)&&foot_in(x,y,224,152,32,32))return 1;
 if(room==19&&(foot_in(x,y,50,48,28,26)||foot_in(x,y,162,48,28,26)))return 1;
 if(room==20)for(i=0;i<2;i++)if(foot_in(x,y,region_game_crates[i][0]-7,region_game_crates[i][1]-7,14,14))return 1;
 return 0;
}
COLD unsigned region_game_plate_mask(void){unsigned i,j,m=0;for(i=0;i<2;i++)for(j=0;j<2;j++)if(region_game_crates[j][0]==plates[i][0]&&region_game_crates[j][1]==plates[i][1])m|=1u<<i;return m;}
COLD int region_game_try_push(int x,int y,unsigned facing){static const signed char dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};unsigned i;
 if(room!=20||facing>=4||ready(Q_WEAVER))return 0;
 for(i=0;i<2;i++){int a=region_game_crates[i][0]-x,b=region_game_crates[i][1]-y,f=a*dx[facing]+b*dy[facing],side=a*dy[facing]-b*dx[facing];
  if(f>=12&&f<=23&&abs_i(side)<=5){int nx=region_game_crates[i][0]+16*dx[facing],ny=region_game_crates[i][1]+16*dy[facing];
   if(nx<64||nx>176||ny<56||ny>104||(nx==region_game_crates[1-i][0]&&ny==region_game_crates[1-i][1]))return -1;
   region_game_crates[i][0]=(short)nx;region_game_crates[i][1]=(short)ny;changed();return 1;
  }
 }
 return 0;
}
COLD int region_game_target(int*x,int*y,int*radius){if(room!=16)return 0;if(x)*x=440;if(y)*y=280;if(radius)*radius=7;return 1;}
COLD int region_game_practice_hit(unsigned cls,int x,int y){unsigned bit;
 if(game_state!=PLAY||room!=16||cls<1||cls>3||game_weapon_class()!=cls||!near_xy(x,y,440,280,9))return 0;
 target_flash=18;changed();event_dirty=0;
 if(state(Q_PRACTICE)==SAVE5_QUEST_INACTIVE){toast(TX_RG_PRACTICE_FIRST);return 1;}
 if(ready(Q_PRACTICE))return 1;
 bit=1u<<(cls-1);objective(Q_PRACTICE,bit);persist();toast(ready(Q_PRACTICE)?TX_RG_PRACTICE_READY:TX_RG_PRACTICE_HIT);return 1;
}
static COLD int four_wishes(void){unsigned i,m=0;for(i=0;i<CREATURE_ROSTER_CAPACITY;i++){const CreatureInstance*c=&adventure_save.roster.instances[i];unsigned family;
 if(!(c->flags&CREATURE_OCCUPIED))continue;
 family=creatures_legacy_spirit(c->form_id);if(family<4&&(c->trial_flags&(1u<<family)))m|=1u<<family;
 }return m==15;}
static COLD int rest_here(void){int x=room==16?104:120,y=216,r;if(!close_to(x,y,24))return 0;
 r=regional_anchor(&adventure_save,(unsigned)room);if(r==REGION_QUEST_LOCKED)return 0;
 game_health_fill();checkpoint_spawn=2;event_dirty=1;say(TX_RG_REST_A,TX_RG_REST_B);return 1;
}
static COLD int try_door(unsigned target,unsigned spawn){sync_chapter();if(!regional_can_enter(&adventure_save,target)){if(!door_notice){say(TX_RG_LOCKED_A,TX_RG_LOCKED_B);door_notice=45;}return 1;}persist();enter_room((int)target,(int)spawn);return 1;}
static COLD int reset_interaction(int y){if(!close_to(32,y,22))return 0;
 if((room==18&&ready(Q_METAL))||(room==19&&ready(Q_POOLS))||(room==20&&ready(Q_WEAVER))||(room==21&&ready(Q_GARDEN)))toast(TX_RG_FIXED);
 else{region_game_reset();toast(TX_RG_RESET);}return 1;
}
COLD int region_game_interact(void){int r;event_dirty=0;sync_chapter();if(game_state!=PLAY)return 0;
 if(room==1){if(!close_to(168,248,18)||!game_region_entry_safe())return 0;
  if(!(chapter_flags&SAVE4_GROVE_CLEAR)){say(TX_RG_ENTRY_A,TX_RG_ENTRY_B);return 1;}enter_room(16,0);return 1;
 }
 if(!region_game_is_room((unsigned)room))return 0;
 if(room==16){
  if(face==1&&px>=76&&px<=100&&py>=115&&py<=128)return try_door(20,0);
  if(face==1&&close_to(344,145,17))return try_door(18,0);
  if(face==1&&close_to(344,230,18))return try_door(21,0);
  if(rest_here())return 1;
  if(close_to(320,150,23)){
   if(!done(Q_PRACTICE)){if(ready(Q_PRACTICE))claim_scene(Q_PRACTICE);else{offer(Q_PRACTICE);say(TX_RG_PRACTICE_A,TX_RG_PRACTICE_B);}return 1;}
   if(!done(Q_CRAFT)){if(ready(Q_CRAFT))claim_scene(Q_CRAFT);else if(offer(Q_CRAFT))say(TX_RG_CRAFT_A,TX_RG_CRAFT_B);else say(TX_RG_CRAFT_WAIT_A,TX_RG_CRAFT_WAIT_B);return 1;}
   say(TX_RG_RETURN_A,TX_RG_RETURN_B);return 1;
  }
  if(close_to(88,136,23)){if(done(Q_WEAVER))say(TX_RG_RETURN_A,TX_RG_RETURN_B);else if(ready(Q_WEAVER))say(TX_RG_STORE_HINT_A,TX_RG_STORE_HINT_B);else{offer(Q_WEAVER);say(TX_RG_WEAVER_A,TX_RG_WEAVER_B);}return 1;}
  if(close_to(264,236,23)){if(ready(Q_DRY)&&!done(Q_DRY))claim_scene(Q_DRY);else if(done(Q_DRY))say(TX_RG_RETURN_A,TX_RG_RETURN_B);else{offer(Q_DRY);say(TX_RG_DRY_A,TX_RG_DRY_B);}return 1;}
  if(close_to(182,234,23)){if(done(Q_FRIENDS))say(TX_RG_RETURN_A,TX_RG_RETURN_B);else if(offer(Q_FRIENDS)&&four_wishes()){complete(Q_FRIENDS);claim_scene(Q_FRIENDS);}else say(TX_RG_FRIENDS_A,TX_RG_FRIENDS_B);return 1;}
  if(close_to(432,240,23)||close_to(456,240,23)){unsigned cls=abs_i(px-432)<=abs_i(px-456)?2:3;r=regional_claim_rack(&adventure_save,cls);
   if(r==REGION_QUEST_REWARDED){event_dirty=1;say(TX_RG_RACK_A,TX_RG_RACK_B);}else if(r==REGION_QUEST_RESERVED)say(TX_MG_RESERVED,TX_MG_RESERVEDB);else if(r==REGION_QUEST_FULL)say(TX_RG_FULL_A,TX_RG_FULL_B);else say(TX_RG_PRACTICE_A,TX_RG_PRACTICE_B);return 1;}
  if(close_to(408,240,23)||close_to(416,264,23)){say(TX_RG_PRACTICE_A,TX_RG_PRACTICE_B);return 1;}
  if(close_to(400,152,18)){say(TX_RG_WELCOME_A,TX_RG_WELCOME_B);return 1;}
  if(close_to(64,128,18)){say(TX_RG_WEAVER_A,TX_RG_WEAVER_B);return 1;}
  if(close_to(376,248,18)){say(TX_RG_GARDEN_A,TX_RG_GARDEN_B);return 1;}
 }
 if(room==17){
  if(face==1&&close_to(360,56,18))return try_door(19,0);
  if(rest_here())return 1;
  if(close_to(264,200,24)){offer(Q_DRY);if(!ready(Q_DRY))objective(Q_DRY,1);persist();toast(done(Q_DRY)?TX_RG_FIXED:TX_RG_DRY_HANDLE);return 1;}
  if(close_to(348,268,24)){offer(Q_WATER);if(done(Q_WATER))say(TX_RG_RETURN_A,TX_RG_RETURN_B);else say(TX_RG_BASIN_A,TX_RG_BASIN_B);return 1;}
  if(close_to(184,72,24)){
   if(done(Q_WATER)){say(TX_RG_RETURN_A,TX_RG_RETURN_B);return 1;}offer(Q_WATER);
   if((adventure_save.quests.objectives[Q_WATER]&3)==3){objective(Q_WATER,4);claim_scene(Q_WATER);}else say(TX_RG_BASIN_A,TX_RG_BASIN_B);return 1;
  }
  if(close_to(84,44,22)&&!close_to(60,40,21)){offer(Q_WATER);say(TX_RG_BASIN_A,TX_RG_BASIN_B);return 1;}
  if(close_to(60,40,21)){if(ready(Q_WEAVER))claim_scene(Q_WEAVER);else say(TX_RG_NOOK_WAIT_A,TX_RG_NOOK_WAIT_B);return 1;}
  if(close_to(296,120,25)||close_to(424,104,25)||close_to(384,80,18)){say(TX_RG_FIELD_POOL_A,TX_RG_FIELD_POOL_B);return 1;}
 }
 if(room==18){
  if(reset_interaction(128))return 1;
  if(close_to(96,64,24)){
   if(!done(Q_METAL)){offer(Q_METAL);if(ready(Q_METAL))claim_scene(Q_METAL);else say(TX_RG_FOUNDRY_A,TX_RG_FOUNDRY_B);}
   else if(ready(Q_RING))claim_scene(Q_RING);else{offer(Q_RING);say(TX_RG_BELL_REPAIR_A,TX_RG_BELL_REPAIR_B);}
   return 1;
  }
  if(close_to(184,56,24)){if(ready(Q_LATCH))claim_scene(Q_LATCH);else{offer(Q_LATCH);say(TX_RG_LATCH_A,TX_RG_LATCH_B);}return 1;}
  if(close_to(48,56,25)||close_to(80,104,24)){
   if(!done(Q_METAL)){offer(Q_METAL);say(TX_RG_FORGE_HINT_A,TX_RG_FORGE_HINT_B);}else if(offer(Q_CRAFT))say(TX_RG_CRAFT_A,TX_RG_CRAFT_B);else say(TX_RG_CRAFT_WAIT_A,TX_RG_CRAFT_WAIT_B);return 1;}
  if(close_to(152,104,24)){if(offer(Q_CRAFT))say(TX_RG_CRAFT_A,TX_RG_CRAFT_B);else say(TX_RG_CRAFT_WAIT_A,TX_RG_CRAFT_WAIT_B);return 1;}
 }
 if(room==19){unsigned i;
  if(reset_interaction(132))return 1;
  for(i=0;i<2;i++){int x=i?176:64;if(close_to(x,112,24)){
   if(ready(Q_POOLS)){claim_scene(Q_POOLS);return 1;}offer(Q_POOLS);region_game_valves[i]^=1u;changed();
   if(region_game_valves[i]&&(!region_game_pool_levels[0]||!region_game_pool_levels[1])){region_game_pool_levels[0]=region_game_pool_levels[1]=0;toast(TX_RG_POOL_DRAIN);}
   else if(region_game_valves[0]&&region_game_valves[1]&&region_game_pool_levels[0]&&region_game_pool_levels[1]){complete(Q_POOLS);claim_scene(Q_POOLS);return 1;}
   else toast(region_game_valves[i]?TX_RG_POOL_OPEN:TX_RG_POOL_CLOSED);
   persist();return 1;
  }}
  if(close_to(64,64,29)||close_to(176,64,29)){if(ready(Q_POOLS))claim_scene(Q_POOLS);else{offer(Q_POOLS);say(TX_RG_TIDE_A,TX_RG_TIDE_B);}return 1;}
 }
 if(room==20){
  if(reset_interaction(128))return 1;
  r=region_game_try_push(px,py,(unsigned)face);if(r){offer(Q_WEAVER);persist();toast(r>0?TX_RG_CRATE_MOVED:TX_RG_CRATE_BLOCKED);return 1;}
  if(close_to(208,80,24)){if(ready(Q_WEAVER))say(TX_RG_STORE_HINT_A,TX_RG_STORE_HINT_B);else{offer(Q_WEAVER);if(region_game_plate_mask()==3){complete(Q_WEAVER);say(TX_RG_STORE_HINT_A,TX_RG_STORE_HINT_B);}else say(TX_RG_WEAVER_A,TX_RG_WEAVER_B);}return 1;}
  if(close_to(120,40,24)||close_to(80,56,22)||close_to(160,104,22)){offer(Q_WEAVER);say(TX_RG_WEAVER_A,TX_RG_WEAVER_B);return 1;}
 }
 if(room==21){
  if(reset_interaction(132))return 1;
  if(close_to(184,48,24)){if(ready(Q_GARDEN))claim_scene(Q_GARDEN);else{offer(Q_GARDEN);say(TX_RG_GARDEN_A,TX_RG_GARDEN_B);}return 1;}
  if(close_to(64,120,24)){offer(Q_GARDEN);say(TX_RG_GARDEN_A,TX_RG_GARDEN_B);return 1;}
 }
 return 0;
}
static int fire_power(unsigned c){return c==1||c==5;}
static int root_power(unsigned c){return c==2||c==6;}
static int wind_power(unsigned c){return c==3||c==7;}
static int stone_power(unsigned c){return c==4||c==8;}
static int water_power(unsigned c){return c==9||c==10;}
static COLD int wrong(void){toast(TX_RG_WRONG_POWER);persist();return 1;}
COLD int region_game_power(unsigned command){CreatureInstance*c;event_dirty=0;sync_chapter();
 if(game_state!=PLAY||!summoned||!region_game_is_room((unsigned)room)||command!=progression_command())return 0;
 c=progression_selected();if(!c||!creatures_command_learned(c->form_id,c->level,command))return 0;
 if(room==17){
  if(close_to(240,199,27)){
   if(ready(Q_DRY))return 0;
   if(!root_power(command))return wrong();
   offer(Q_DRY);
   if(!(adventure_save.quests.objectives[Q_DRY]&1)){toast(TX_RG_DRY_NEED_HANDLE);persist();return 1;}
   objective(Q_DRY,2);changed();persist();toast(TX_RG_DRY_OPEN);return 1;
  }
  if(close_to(84,44,27)){if(done(Q_WATER))return 0;if(!root_power(command))return wrong();offer(Q_WATER);objective(Q_WATER,1);changed();persist();toast(TX_RG_BASIN_REEDS);return 1;}
  if(close_to(184,72,28)){if(done(Q_WATER))return 0;if(!wind_power(command))return wrong();offer(Q_WATER);objective(Q_WATER,2);changed();persist();toast(TX_RG_BASIN_WIND);return 1;}
  if(close_to(296,120,28)||close_to(424,104,28)){unsigned i=close_to(296,120,28)?0:1;if(!water_power(command))return wrong();
   if(command==10&&done(Q_POOLS)){field_pool_mask=3;changed();game_region_warp(i?296:424,i?140:124);toast(TX_RG_WATER_LINK);return 1;}
   field_pool_mask|=1u<<i;changed();toast(TX_RG_POOL_FILLED);return 1;
  }
 }
 if(room==18){
  if(!done(Q_METAL)&&(close_to(48,56,28)||close_to(80,104,27)||close_to(96,64,27))){int matched=0;
   if(ready(Q_METAL)){toast(TX_RG_FOUNDRY_DONE);return 1;}offer(Q_METAL);
   if(close_to(48,56,28)&&fire_power(command)){region_game_foundry_step=1;matched=1;toast(TX_RG_FOUNDRY_HEAT);}
   else if(close_to(80,104,27)&&water_power(command)&&region_game_foundry_step==1){region_game_foundry_step=2;matched=1;toast(TX_RG_FOUNDRY_COOL);}
   else if(close_to(96,64,27)&&wind_power(command)&&region_game_foundry_step==2){region_game_foundry_step=3;matched=1;if(regional_quest_variable(&adventure_save,Q_METAL,3)==REGION_QUEST_CHANGED)event_dirty=1;complete(Q_METAL);toast(TX_RG_FOUNDRY_DONE);}
   if(!matched){region_game_foundry_step=0;toast(TX_RG_FOUNDRY_RETRY);}changed();persist();return 1;
  }
  if(close_to(184,56,27)){if(command!=11)return wrong();
   if(!offer(Q_LATCH)){toast(TX_RG_LOCKED_A);return 1;}if(done(Q_LATCH))return 0;complete(Q_LATCH);claim_scene(Q_LATCH);return 1;}
  if(close_to(96,64,27)&&done(Q_METAL)){
   if(command!=11)return wrong();
   if(!done(Q_LATCH)){toast(TX_RG_BELL_NEED_LATCH);return 1;}
   if(done(Q_RING))return 0;
   complete(Q_RING);claim_scene(Q_RING);return 1;
  }
  if(close_to(48,56,28)&&done(Q_METAL)){if(!fire_power(command))return wrong();if(!offer(Q_CRAFT)){toast(TX_RG_CRAFT_WAIT_A);return 1;}if(ready(Q_CRAFT))return 0;objective(Q_CRAFT,1);persist();toast(TX_RG_CRAFT_HEAT);return 1;}
  if(close_to(152,104,27)){if(!stone_power(command))return wrong();if(!offer(Q_CRAFT)){toast(TX_RG_CRAFT_WAIT_A);return 1;}
   if(ready(Q_CRAFT))return 0;
   if(!(adventure_save.quests.objectives[Q_CRAFT]&1)){toast(TX_RG_CRAFT_COLD);persist();return 1;}
   objective(Q_CRAFT,2);persist();toast(TX_RG_CRAFT_READY);return 1;
  }
 }
 if(room==19){unsigned i;for(i=0;i<2;i++)if(close_to(i?176:64,64,29)){
  if(ready(Q_POOLS))return 0;
  if(!water_power(command))return wrong();
  offer(Q_POOLS);
  if(region_game_valves[i])toast(TX_RG_POOL_LEAK);else{region_game_pool_levels[i]=1;changed();toast(TX_RG_POOL_FILLED);}persist();return 1;
 }}
 return 0;
}
COLD void region_game_tick(void){unsigned i;int sensor=-1;if(game_state!=PLAY)return;
 if(target_flash&&!--target_flash)changed();
 if(door_notice)door_notice--;
 if(!region_game_is_room((unsigned)room))return;
 if(room==21){
  if(roll_ticks&&!was_rolling)roll_serial++;
  was_rolling=roll_ticks!=0;
  if(state(Q_GARDEN)==SAVE5_QUEST_ACTIVE){
   for(i=0;i<3;i++)if(close_to(garden_stones[i][0],garden_stones[i][1],11)){sensor=(int)i;break;}
   if(roll_ticks&&sensor>=0&&roll_serial!=last_garden_roll){
    last_garden_roll=roll_serial;event_dirty=0;
    if((unsigned)sensor==region_game_garden_step){region_game_garden_step++;if(region_game_garden_step==3){if(regional_quest_variable(&adventure_save,Q_GARDEN,3)==REGION_QUEST_CHANGED)event_dirty=1;complete(Q_GARDEN);persist();toast(TX_RG_GARDEN_DONE);}else toast(TX_RG_GARDEN_STEP);}
    else{region_game_garden_step=(unsigned char)(sensor==0?1:0);toast(TX_RG_GARDEN_RETRY);}changed();
   }
  }
 }
 if(transition_lock||game_state!=PLAY)return;
 if(room==16){
  if((keys&KEY_DOWN)&&px>=224&&px<=255&&py>=298){enter_room(1,3);return;}
  if(keys&KEY_UP){
   if(px>=224&&px<=255&&py<=32){try_door(17,0);return;}
   if(px>=332&&px<=355&&py>=136&&py<=148){try_door(18,0);return;}
   if(px>=76&&px<=99&&py>=115&&py<=128){try_door(20,0);return;}
   if(px>=332&&px<=355&&py>=218&&py<=236){try_door(21,0);return;}
  }
 }else if(room==17){
  if((keys&KEY_DOWN)&&px>=224&&px<=255&&py>=298){enter_room(16,1);return;}
  if((keys&KEY_UP)&&px>=348&&px<=371&&py>=43&&py<=62){try_door(19,0);return;}
 }else if((keys&KEY_DOWN)&&px>=108&&px<=131&&py>=143){int target=room==19?17:16,spawn=room==18?3:room==19?1:room==20?4:5;enter_room(target,spawn);}
}
COLD int region_game_name(void){static const int names[6]={TX_RG_ROOM_TOWN,TX_RG_ROOM_BASIN,TX_RG_ROOM_FOUNDRY,TX_RG_ROOM_TIDE,TX_RG_ROOM_STORE,TX_RG_ROOM_GARDEN};return region_game_is_room((unsigned)room)?names[room-16]:0;}
static const int quest_names[11]={TX_RG_Q0,TX_RG_Q1,TX_RG_Q2,TX_RG_Q3,TX_RG_Q4,TX_RG_Q5,TX_RG_Q6,TX_RG_Q7,TX_RG_Q8,TX_RG_Q9,TX_RG_Q10};
static const int clues[11][2]={{TX_RG_PRACTICE_A,TX_RG_PRACTICE_B},{TX_RG_DRY_A,TX_RG_DRY_B},{TX_RG_BASIN_A,TX_RG_BASIN_B},{TX_RG_FOUNDRY_A,TX_RG_FOUNDRY_B},{TX_RG_TIDE_A,TX_RG_TIDE_B},{TX_RG_WEAVER_A,TX_RG_WEAVER_B},{TX_RG_FRIENDS_A,TX_RG_FRIENDS_B},{TX_RG_LATCH_A,TX_RG_LATCH_B},{TX_RG_CRAFT_A,TX_RG_CRAFT_B},{TX_RG_GARDEN_A,TX_RG_GARDEN_B},{TX_RG_BELL_REPAIR_A,TX_RG_BELL_REPAIR_B}};
COLD int region_game_quest_text(void){unsigned q;for(q=0;q<11;q++)if(state(q)==SAVE5_QUEST_READY)return quest_names[q];if(!done(Q_WATER))return TX_RG_Q2;if(!done(Q_METAL))return TX_RG_Q3;for(q=0;q<11;q++)if(state(q)==SAVE5_QUEST_ACTIVE)return quest_names[q];return TX_RG_JOURNAL;}
static COLD void numeral(unsigned n,int x,int y){static const unsigned char digits[10][5]={{7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},{5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},{7,5,7,5,7},{7,5,7,1,7}};unsigned d,xx,yy;if(n>=10){numeral(n/10,x,y);x+=8;}d=n%10;for(yy=0;yy<5;yy++)for(xx=0;xx<3;xx++)if(digits[d][yy]&(4>>xx))rect(x+(int)xx*2,y+(int)yy*2,2,2,PAL_GOLD4);}
COLD void region_game_draw_journal(void){static const int states[4]={TX_RG_UNSEEN,TX_RG_ACTIVE,TX_RG_READY,TX_RG_CLAIMED};unsigned q=region_game_journal_selection%11,s=state(q),bit,x=20;
 box(8,31,224,122);centered(TX_RG_JOURNAL,34,PAL_GOLD3);text(quest_names[q],18,54,PAL_GOLD4);text(states[s],173,54,PAL_TEAL2);
 if(s==0){text(TX_RG_NOT_OFFERED_A,14,76,PAL_GOLD4);text(TX_RG_NOT_OFFERED_B,14,94,PAL_GOLD4);}
 else if(q==Q_WEAVER&&s==2){text(TX_RG_STORE_HINT_A,14,76,PAL_GOLD4);text(TX_RG_STORE_HINT_B,14,94,PAL_GOLD4);}
 else if(s==3){text(TX_RG_RETURN_A,14,76,PAL_GOLD4);text(TX_RG_RETURN_B,14,94,PAL_GOLD4);}
 else{text(clues[q][0],14,76,PAL_GOLD4);text(clues[q][1],14,94,PAL_GOLD4);}
 text(TX_RG_OBJECTIVES,18,115,PAL_TEAL2);x=88;
 for(bit=1;bit<=4;bit<<=1)if(regional_quest_mask(q)&bit){rect((int)x,118,8,8,(adventure_save.quests.objectives[q]&bit)?PAL_GOLD3:PAL_STONE1);x+=13;}
 numeral(q+1,190,118);centered(TX_RG_JOURNAL_KEYS,138,PAL_TEAL2);
}
COLD int region_game_menu_input(int input){if(journal_tab!=JOURNAL_TAB)return 0;if(input&KEY_UP){region_game_journal_selection=(region_game_journal_selection+10)%11;changed();return 1;}if(input&KEY_DOWN){region_game_journal_selection=(region_game_journal_selection+1)%11;changed();return 1;}return 0;}
COLD void region_game_draw_actors(void){unsigned m;if(room==1){if(chapter_flags&SAVE4_GROVE_CLEAR)region_actor(REGION_SPR_SIGN_WORKSHOP,168,248);return;}
 if(room==16){
  region_actor(REGION_SPR_NPC_SMITH,320,150);region_actor(REGION_SPR_NPC_WEAVER,88,136);region_actor(REGION_SPR_NPC_WARDEN,264,236);region_actor(REGION_SPR_NPC_APPRENTICE,416,264);region_actor(REGION_SPR_NPC_REST_KEEPER,182,234);
  region_actor((adventure_save.quests.anchors[0]&1)?REGION_SPR_REST_LIT:REGION_SPR_REST_IDLE,104,216);
  region_actor(REGION_SPR_RACK_SWORD,408,240);region_actor(REGION_SPR_RACK_LANCE,432,240);region_actor(REGION_SPR_RACK_BOW,456,240);region_actor(target_flash?REGION_SPR_TARGET_HIT:REGION_SPR_TARGET_READY,440,280);
  region_actor(REGION_SPR_SIGN_WORKSHOP,400,152);region_actor(REGION_SPR_SIGN_WEAVER,64,128);region_actor(REGION_SPR_SIGN_GARDEN,376,248);
 }else if(room==17){
  region_actor((adventure_save.quests.anchors[0]&2)?REGION_SPR_REST_LIT:REGION_SPR_REST_IDLE,120,216);
  region_actor((adventure_save.quests.objectives[Q_DRY]&1)?REGION_SPR_SLUICE_OPEN:REGION_SPR_SLUICE_CLOSED,264,200);
  region_actor((field_pool_mask&1)?REGION_SPR_POOL_HIGH:REGION_SPR_POOL_LOW,296,120);region_actor((field_pool_mask&2)?REGION_SPR_POOL_HIGH:REGION_SPR_POOL_LOW,424,104);
  region_actor(ready(Q_WEAVER)?REGION_SPR_SPINDLE_LIT:REGION_SPR_SPINDLE_IDLE,60,40);
  region_actor((adventure_save.quests.objectives[Q_WATER]&1)?REGION_SPR_REED_PARTED:REGION_SPR_REED_SCREEN,84,44);
  if(!done(Q_WATER))region_form_actor(13,184,72);else region_actor(REGION_SPR_BELL_RING,184,72);
  region_actor(REGION_SPR_NPC_WARDEN,348,268);region_actor(REGION_SPR_SIGN_TIDE,384,80);
 }else if(room==18){
  if(ready(Q_METAL)&&!done(Q_METAL))region_form_actor(16,96,64);else region_actor((region_game_foundry_step==3||done(Q_RING))?REGION_SPR_BELL_RING:REGION_SPR_BELL_IDLE,96,64);
  region_actor((region_game_foundry_step||(adventure_save.quests.objectives[Q_CRAFT]&1))?REGION_SPR_FURNACE_LIT:REGION_SPR_FURNACE_IDLE,48,56);
  region_actor(done(Q_LATCH)?REGION_SPR_LATCH_OPEN:REGION_SPR_LATCH_CLOSED,184,56);
  region_actor(region_game_foundry_step>=2?REGION_SPR_PLATE_DOWN:REGION_SPR_PLATE_UP,80,104);region_actor(ready(Q_CRAFT)?REGION_SPR_PLATE_DOWN:REGION_SPR_PLATE_UP,152,104);region_actor(REGION_SPR_RESET_IDLE,32,128);
 }else if(room==19){
  region_actor(region_game_pool_levels[0]?REGION_SPR_POOL_HIGH:REGION_SPR_POOL_LOW,64,64);region_actor(region_game_pool_levels[1]?REGION_SPR_POOL_HIGH:REGION_SPR_POOL_LOW,176,64);
  region_actor(region_game_valves[0]?REGION_SPR_SLUICE_OPEN:REGION_SPR_SLUICE_CLOSED,64,112);region_actor(region_game_valves[1]?REGION_SPR_SLUICE_OPEN:REGION_SPR_SLUICE_CLOSED,176,112);region_actor(REGION_SPR_RESET_IDLE,32,132);
 }else if(room==20){m=region_game_plate_mask();region_actor((m&1)?REGION_SPR_PLATE_DOWN:REGION_SPR_PLATE_UP,80,56);region_actor((m&2)?REGION_SPR_PLATE_DOWN:REGION_SPR_PLATE_UP,160,104);
  region_actor(REGION_SPR_CRATE,region_game_crates[0][0],region_game_crates[0][1]);region_actor(REGION_SPR_CRATE,region_game_crates[1][0],region_game_crates[1][1]);region_actor(m==3?REGION_SPR_SPINDLE_LIT:REGION_SPR_SPINDLE_IDLE,208,80);region_actor(m==3?REGION_SPR_LATCH_OPEN:REGION_SPR_LATCH_CLOSED,120,40);region_actor(REGION_SPR_RESET_IDLE,32,128);
 }else if(room==21){unsigned i;for(i=0;i<3;i++)region_actor(region_game_garden_step>i?REGION_SPR_STEP_LIT:REGION_SPR_STEP_IDLE,garden_stones[i][0],garden_stones[i][1]);region_actor(ready(Q_GARDEN)?REGION_SPR_BELL_RING:REGION_SPR_BELL_IDLE,184,48);region_actor(REGION_SPR_SIGN_GARDEN,64,120);region_actor(REGION_SPR_RESET_IDLE,32,132);}
}
COLD void region_game_draw_overlay(void){int x,y;if(room==17&&(adventure_save.quests.objectives[Q_DRY]&2))for(y=152;y<184;y+=16)for(x=224;x<256;x+=16)sprite(region_sprites[REGION_SPR_BRIDGE_ROOT],x-camera_x,y-camera_y,16,16,0);
 if(room==18){if(region_game_foundry_step>=1)line(96,64,122,64,PAL_GOLD3);if(region_game_foundry_step>=2){line(80,104,80,124,PAL_GOLD3);line(80,124,171,124,PAL_GOLD3);}if(region_game_foundry_step>=3){line(171,124,171,56,PAL_GOLD3);line(171,56,184,56,PAL_GOLD3);}}
 if(room==19&&region_game_pool_levels[0]&&region_game_pool_levels[1]){line(64,98,176,98,PAL_WATER4);if(ready(Q_POOLS))line(120,48,120,98,PAL_GOLD3);}
 if(room==20&&region_game_plate_mask()==3){line(160,104,188,104,PAL_GOLD3);line(188,104,188,78,PAL_GOLD3);line(188,78,208,78,PAL_GOLD3);}
 if(room==21&&state(Q_GARDEN)==SAVE5_QUEST_ACTIVE&&region_game_garden_step<3){x=garden_stones[region_game_garden_step][0];y=garden_stones[region_game_garden_step][1];line(x-11,y+7,x+11,y+7,PAL_GOLD3);}
}
