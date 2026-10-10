/* Original Northern chapter. Bounded reversible mechanisms, no required Earth
 * companion/evolution, and no transient arrangement in the save codec. */
#include "north_game.h"
#include "north_art.h"
#include "northern_quests.h"
#include "progression.h"
#include "connected_roads.h"
#include "assets.h"
#ifdef NORTH_GAME_HOST_TEST
#include "north_game_test_ui.h"
#else
#include "ui.h"
#endif
#if defined(__arm__)
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
#else
#define COLD
#endif
#define PLAY 1
#define UP 64
#define DOWN 128
#define JOURNAL_TAB 6
extern volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
extern volatile unsigned chapter_flags;
extern int face,keys,journal_tab;
extern void enter_room(int,int),save_game(void),dialogue(int,int,int),toast(int),text(int,int,int,int),centered(int,int,int),box(int,int,int,int);
extern void rect(int,int,int,int,unsigned char),line(int,int,int,int,int);
unsigned north_game_revision,north_game_journal_selection;
NorthPuzzle north_game_puzzle;
unsigned char north_game_machine_stage,north_game_machine_ticks,north_game_machine_hp;
static unsigned char forecast,tender_steps,heat_held,fragile_step,compass_step,machine_couplings,machine_hit,door_notice;
static unsigned dirty;
static const short spawns[8][5][2]={{{240,284},{240,36},{104,208},{88,144},{384,144}},{{240,284},{400,72},{80,264},{0,0},{0,0}},{{120,132}},{{120,132}},{{120,132}},{{120,132}},{{120,132}},{{120,132}}};
static const unsigned char counts[8]={5,3,1,1,1,1,1,1};
static int ab(int n){return n<0?-n:n;}
static int near(int x,int y,int xx,int yy,int r){return ab(x-xx)+ab(y-yy)<r;}
static int close(int x,int y){return near(px,py,x,y,24);}
static unsigned state(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
static int done(unsigned q){return state(q)==3;}
static int ready(unsigned q){return state(q)>=2;}
static void changed(void){north_game_revision++;progression_revision++;}
static void sync(void){adventure_save.campaign.chapter_flags=(Save4U8)chapter_flags;}
static COLD void persist(void){if(dirty){sync();if(north_game_is_room((unsigned)room)){adventure_save.campaign.room=(Save4U8)room;adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;}changed();save_game();dirty=0;}}
static COLD void say(int a,int b){persist();dialogue(a,b,PLAY);}
static COLD int offer(unsigned q){int r=northern_quest_offer(&adventure_save,q);if(r==NORTH_CHANGED)dirty=1;return r!=NORTH_LOCKED&&r!=NORTH_INVALID;}
static COLD void objective(unsigned q,unsigned bit){int r=northern_quest_objective(&adventure_save,q,bit);if(r==NORTH_CHANGED||r==NORTH_NOW_READY){dirty=1;changed();}}
static COLD void claim(unsigned q){int r=northern_quest_claim(&adventure_save,q);
 if(r==NORTH_REWARDED){dirty=1;progression_refresh();say(q==21?TX_NT_RETURN_A:TX_NT_RECEIVED_A,q==21?TX_NT_RETURN_B:TX_NT_RECEIVED_B);}
 else if(r==NORTH_RESERVED)say(TX_MG_RESERVED,TX_MG_RESERVEDB);else if(r==NORTH_FULL)say(TX_NT_FULL_A,TX_NT_FULL_B);else if(r==NORTH_UNCHANGED)say(TX_NT_RETURN_A,TX_NT_RETURN_B);else say(TX_NT_LOCKED_A,TX_NT_LOCKED_B);
}
static const int quest_names[11]={TX_NT_Q11,TX_NT_Q12,TX_NT_Q13,TX_NT_Q14,TX_NT_Q15,TX_NT_Q16,TX_NT_Q17,TX_NT_Q18,TX_NT_Q19,TX_NT_Q20,TX_NT_Q21};
static const int clues[11][2]={{TX_NT_CLUE11A,TX_NT_CLUE11B},{TX_NT_CLUE12A,TX_NT_CLUE12B},{TX_NT_CLUE13A,TX_NT_CLUE13B},{TX_NT_CLUE14A,TX_NT_CLUE14B},{TX_NT_CLUE15A,TX_NT_CLUE15B},{TX_NT_CLUE16A,TX_NT_CLUE16B},{TX_NT_CLUE17A,TX_NT_CLUE17B},{TX_NT_CLUE18A,TX_NT_CLUE18B},{TX_NT_CLUE19A,TX_NT_CLUE19B},{TX_NT_CLUE20A,TX_NT_CLUE20B},{TX_NT_CLUE21A,TX_NT_CLUE21B}};
static COLD void talk(unsigned q){if(ready(q)){claim(q);return;}if(offer(q))say(clues[q-11][0],clues[q-11][1]);else say(TX_NT_LOCKED_A,TX_NT_LOCKED_B);}
int north_game_is_room(unsigned a){return a>=22&&a<=29;}
static int swept_cart(unsigned which,unsigned from,unsigned to,int x,int y){int yy=which?96:64,xx1=which?160-(int)from*32:80+(int)from*32,xx2=which?160-(int)to*32:80+(int)to*32,tmp;
 if(xx1>xx2){tmp=xx1;xx1=xx2;xx2=tmp;}return ab(y-yy)<=12&&x>=xx1-12&&x<=xx2+12;
}
COLD int north_puzzle_step(NorthPuzzle*p,unsigned area,unsigned act,int x,int y){unsigned which;
 if(!p||area<26||area>28||p->rail>3||p->weight>1||p->cart[0]>2||p->cart[1]>2)return -1;
 if(act==NORTH_ACTION_RESET){p->rail=p->weight=p->cart[0]=p->cart[1]=0;return 1;}
 if(act==NORTH_ACTION_TURN){p->rail=(unsigned char)((p->rail+1)&3);return 1;}
 if(act==NORTH_ACTION_WEIGHT){p->weight^=1;return 1;}
 if(act!=NORTH_ACTION_REEL)return -1;
 if(area==26){if(p->rail!=1)return -1;which=0;}
 else if(area==27){if(p->rail!=1&&p->rail!=3)return -1;which=p->rail==3;}
 else{if(p->rail!=2&&p->rail!=0)return -1;which=p->rail==0;if(which&&p->cart[0]!=2)return -1;}
 if(which&&!p->weight)return -1;
 if(p->cart[which]==2)return 0;
 if(swept_cart(which,p->cart[which],p->cart[which]+1,x,y))return -1;
 p->cart[which]++;return 1;
}
COLD int north_puzzle_solved(const NorthPuzzle*p,unsigned area){return p&&area>=26&&area<=28&&p->weight==1&&p->cart[0]==2&&(area==26||p->cart[1]==2);}
COLD void north_game_reset(void){unsigned bit=room>=26&&room<=28?1u<<(room-26):0;
 north_game_puzzle.rail=north_game_puzzle.weight=north_game_puzzle.cart[0]=north_game_puzzle.cart[1]=0;
 if(bit&&(adventure_save.quests.objectives[21]&bit)){north_game_puzzle.weight=1;north_game_puzzle.cart[0]=2;north_game_puzzle.cart[1]=(unsigned char)(room==26?0:2);north_game_puzzle.rail=(unsigned char)(room==28?0:1);}
 forecast=tender_steps=heat_held=fragile_step=compass_step=machine_couplings=machine_hit=0;
 north_game_machine_stage=(unsigned char)((adventure_save.quests.objectives[21]&8)?5:0);north_game_machine_ticks=0;north_game_machine_hp=(unsigned char)(north_game_machine_stage==5?0:128);changed();
}
COLD int north_game_enter(unsigned area,unsigned spawn){int r;sync();if(!north_game_is_room(area)||spawn>=counts[area-22]||!northern_can_enter(&adventure_save,area))return 0;
 room=(int)area;checkpoint_spawn=(int)spawn;px=spawns[area-22][spawn][0];py=spawns[area-22][spawn][1];north_game_reset();door_notice=0;
 r=northern_visit(&adventure_save,area);if(r==NORTH_CHANGED)dirty=1;
 if(area>=26)offer(21);
 adventure_save.campaign.room=(Save4U8)area;adventure_save.campaign.spawn=(Save4U8)spawn;persist();return 1;
}
int north_game_solid(int x,int y){const NorthArtRoom*r;const unsigned short*band;unsigned count,area=(unsigned)room;
 if(area<22||area>29)return 0;
 if(game_road_collision){int road=game_road_collision(area,x,y);if(road>=0)return road;}
 r=&north_art_rooms[area-22];
 /* Casting before bounds checks covers negative/large signed coordinates
  * without overflow. Generated rows already include the exact foot radius. */
 if((unsigned)x>=r->width||(unsigned)y>=r->height)return 1;
 band=r->collision_bands+r->collision_rows[y];count=*band++;
 while(count--){if((unsigned)x<band[0])return 0;if((unsigned)x<band[1])return 1;band+=2;}
 return 0;
}
static COLD int door(unsigned dest,unsigned spawn){if(!northern_can_enter(&adventure_save,dest)){if(!door_notice){say(TX_NT_LOCKED_A,TX_NT_LOCKED_B);door_notice=45;}return 1;}persist();enter_room((int)dest,(int)spawn);return 1;}
static COLD void puzzle_action(unsigned act){int r=north_puzzle_step(&north_game_puzzle,(unsigned)room,act,px,py);static const int railtext[4]={TX_NT_RAIL0,TX_NT_RAIL1,TX_NT_RAIL2,TX_NT_RAIL3};
 if(r<0){toast(TX_NT_BLOCKED);return;}changed();toast(act==NORTH_ACTION_TURN?railtext[north_game_puzzle.rail]:act==NORTH_ACTION_WEIGHT?TX_NT_WEIGHT:TX_NT_REELED);
 if(north_puzzle_solved(&north_game_puzzle,(unsigned)room)){objective(21,1u<<(room-26));persist();toast(TX_NT_SOLVED);}
}
COLD int north_game_interact(void){unsigned i;dirty=0;sync();if(game_state!=PLAY)return 0;
 if(room==16){if(game_road_managed&&game_road_managed(16,22))return 0;if(!close(400,280)||!game_region_entry_safe())return 0;if(!northern_can_enter(&adventure_save,22)){say(TX_NT_ENTRY_A,TX_NT_ENTRY_B);return 1;}enter_room(22,0);return 1;}
 if(!north_game_is_room((unsigned)room))return 0;
 if(room==22){
  if(face==1&&near(px,py,88,138,18))return door(24,0);
  if(face==1&&near(px,py,384,138,18))return door(25,0);
  if((!game_road_managed||!game_road_managed(22,16))&&close(240,264)){persist();enter_room(16,0);return 1;}
  if(close(104,192)){northern_anchor(&adventure_save,22);game_health_fill();checkpoint_spawn=2;dirty=1;say(TX_NT_REST_A,TX_NT_REST_B);return 1;}
  if(close(168,192)){talk(done(11)?16:11);return 1;}
  if(close(312,192)){talk(!done(13)?13:ready(21)?21:20);return 1;}
  if(close(64,192)){talk(done(14)?18:14);return 1;}
  if(close(384,160)){talk(done(12)?17:12);return 1;}
  if(close(416,208)){talk(done(15)?19:15);return 1;}
  if(close(160,224)||close(304,224)){if(!state(11)){toast(TX_NT_FIRST);return 1;}objective(11,close(160,224)?1:2);persist();toast(TX_NT_LINE);return 1;}
  if(close(240,192)){say(TX_NT_WELCOME_A,TX_NT_WELCOME_B);return 1;}
 }else if(room==23){
  if(face==1&&near(px,py,400,65,18))return door(26,0);
  if(close(80,248)){northern_anchor(&adventure_save,23);game_health_fill();checkpoint_spawn=2;dirty=1;say(TX_NT_REST_A,TX_NT_REST_B);return 1;}
  if(close(240,192)){if(!offer(13)){toast(TX_NT_FIRST);return 1;}north_game_puzzle.rail=(unsigned char)((north_game_puzzle.rail+1)&3);changed();toast(north_game_puzzle.rail==1?TX_NT_RAIL1:TX_NT_NEED_PUZZLE);persist();return 1;}
  if(close(320,192)){if(north_game_puzzle.rail==1&&offer(13)){objective(13,1);persist();toast(TX_NT_BEARING);}else toast(TX_NT_NEED_PUZZLE);return 1;}
  if(close(352,160)){if(adventure_save.quests.objectives[13]&1){objective(13,2);claim(13);}else talk(13);return 1;}
  if(close(112,96)){if(offer(14)){objective(14,1);persist();toast(TX_NT_TENDER);}return 1;}
  if(close(176,144)){forecast=(unsigned char)((forecast+1)%3);changed();toast(forecast==2?TX_NT_FORECAST2:forecast==1?TX_NT_FORECAST1:TX_NT_FORECAST0);return 1;}
  if(close(144,112)){if(!offer(14))return 1;objective(14,2);if(forecast==2&&tender_steps<2)tender_steps++;if(tender_steps==2)objective(14,4);changed();persist();toast(TX_NT_TENDER);return 1;}
  {static const short xy[3][2]={{176,224},{288,112},{368,240}};for(i=0;i<3;i++)if(close(xy[i][0],xy[i][1])){if(offer(15)){objective(15,1u<<i);persist();toast(TX_NT_MARKER);}return 1;}}
 }else{
  if(close(32,132)){north_game_reset();toast(TX_NT_RESET);return 1;}
  if(room==24){
   if(close(208,112)){talk(done(16)?18:16);return 1;}
   if(close(120,80)){if(fragile_step==1){fragile_step=2;changed();toast(TX_NT_RAIL1);}else talk(18);return 1;}
  }else if(room==25){
   if(close(208,112)){talk(done(12)?17:12);return 1;}
   if(close(64,64)||close(120,64)){if(!done(12)){if(offer(12))objective(12,close(64,64)?1:2);persist();toast(TX_NT_HEAT);}else say(TX_NT_CLUE17A,TX_NT_CLUE17B);return 1;}
  }else if(room<=28){
   if(close(208,56)){unsigned bit=1u<<(room-26);if(adventure_save.quests.objectives[21]&bit)return door((unsigned)room+1,0);say(room==26?TX_NT_HALL_A:room==27?TX_NT_CROSS_A:TX_NT_RELAY_A,room==26?TX_NT_HALL_B:room==27?TX_NT_CROSS_B:TX_NT_RELAY_B);return 1;}
   if(close(176,96)){puzzle_action(NORTH_ACTION_WEIGHT);return 1;}
   if(room==27&&close(208,112)){if((adventure_save.quests.objectives[19]&1)&&offer(19)){objective(19,2);claim(19);}else talk(19);return 1;}
   if(room==28&&close(208,112)){talk(20);return 1;}
   if(close(120,96)||close(64,64)){say(room==26?TX_NT_HALL_A:room==27?TX_NT_CROSS_A:TX_NT_RELAY_A,room==26?TX_NT_HALL_B:room==27?TX_NT_CROSS_B:TX_NT_RELAY_B);return 1;}
  }else if(room==29&&close(120,108)){
   /* Once running, A belongs to the weapon even when its melee position
    * overlaps the start handle's interaction radius. Reset is independent. */
   if(north_game_machine_stage>=1&&north_game_machine_stage<=4)return 0;
   if(north_game_machine_stage==5){claim(21);return 1;}
   if(machine_couplings==3&&!north_game_machine_stage){north_game_machine_stage=1;north_game_machine_ticks=60;changed();toast(TX_NT_WARN);}else say(TX_NT_CROWN_A,TX_NT_CROWN_B);return 1;
  }
 }
 return 0;
}
static int wood(unsigned c){return c==13||c==14;}
static int metal(unsigned c){return c==21||c==22;}
static int heat(unsigned c){return c==15||c==16;}
static int water(unsigned c){return c==17||c==18;}
static int earth(unsigned c){return c==4||c==8||c==19||c==20;}
static COLD int wrong(void){toast(TX_NT_WRONG);return 1;}
COLD int north_game_power(unsigned cmd){CreatureInstance*c;unsigned i;dirty=0;sync();
 if(game_state!=PLAY||!summoned||!north_game_is_room((unsigned)room)||cmd!=progression_command())return 0;
 c=progression_selected();if(!c||!creatures_command_learned(c->form_id,c->level,cmd))return 0;
 if(room==24){
  if(close(64,80)||close(176,80)){if(!wood(cmd))return wrong();if(offer(16)){objective(16,close(64,80)?1:2);persist();toast(TX_NT_REELED);}return 1;}
  if(close(120,80)){if(!water(cmd))return wrong();if(!offer(18))return wrong();if(!fragile_step){fragile_step=1;objective(18,1);}else if(fragile_step==2){fragile_step=3;objective(18,2);objective(18,4);}changed();persist();toast(TX_NT_TENDER);return 1;}
 }else if(room==25){
  if(close(176,64)&&!done(12)){if(cmd!=1&&cmd!=5&& !heat(cmd))return wrong();if((adventure_save.quests.objectives[12]&3)!=3){toast(TX_NT_NEED_PUZZLE);return 1;}objective(12,4);persist();toast(TX_NT_HEAT);return 1;}
  if(close(64,64)&&done(12)){if(!heat(cmd))return wrong();if(offer(17)){heat_held=1;changed();persist();toast(TX_NT_HEAT);}return 1;}
  for(i=0;i<3;i++)if(close(64+(int)i*56,104)){if(!heat(cmd))return wrong();if(heat_held&&offer(17)){objective(17,1u<<i);persist();toast(TX_NT_DRY);}else toast(TX_NT_HEAT);return 1;}
 }else if(room>=26&&room<=28){
  if(room==27&&close(208,112)){if(cmd!=19&&cmd!=20)return wrong();if(offer(19)){if(north_puzzle_solved(&north_game_puzzle,27)){objective(19,1);persist();toast(TX_NT_WEIGHT);}else{persist();toast(TX_NT_NEED_PUZZLE);}}return 1;}
  if(room==28&&close(208,112)){if(!metal(cmd))return wrong();if(offer(20)){static const unsigned char bearings[3]={0,1,3};if(north_game_puzzle.rail==bearings[compass_step]){objective(20,1u<<compass_step);if(compass_step<2)compass_step++;persist();toast(TX_NT_RAIL1);}else{persist();toast(TX_NT_NEED_PUZZLE);}}return 1;}
  if(close(120,96)){if(!metal(cmd))return wrong();puzzle_action(NORTH_ACTION_TURN);return 1;}
  if(close(64,64)){if(!wood(cmd))return wrong();puzzle_action(NORTH_ACTION_REEL);return 1;}
  if(close(176,96)){if(!earth(cmd))return wrong();puzzle_action(NORTH_ACTION_WEIGHT);return 1;}
 }else if(room==29){
  if(close(64,108)){if(!wood(cmd))return wrong();machine_couplings|=1;changed();toast(TX_NT_COUPLED);return 1;}
  if(close(176,108)){if(!metal(cmd))return wrong();machine_couplings|=2;changed();toast(TX_NT_COUPLED);return 1;}
 }
 return 0;
}
COLD int north_game_target(int*x,int*y,int*r){if(room!=29||north_game_machine_stage!=3||!north_game_machine_hp)return 0;if(x)*x=120;if(y)*y=68;if(r)*r=12;return 1;}
COLD int north_game_weapon_hit(unsigned cls,int x,int y,unsigned damage){if(game_state!=PLAY||!north_game_target(0,0,0)||cls<1||cls>3||cls!=game_weapon_class()||!damage||!near(x,y,120,68,25))return 0;
 if(damage>north_game_machine_hp)damage=north_game_machine_hp;
 north_game_machine_hp=(unsigned char)(north_game_machine_hp-damage);changed();
 if(!north_game_machine_hp){north_game_machine_stage=5;north_game_machine_ticks=0;objective(21,8);persist();toast(TX_NT_MACHINE_DONE);}return 1;
}
COLD void north_game_tick(void){if(game_state!=PLAY)return;if(door_notice)door_notice--;if(!north_game_is_room((unsigned)room))return;
 if(room==29&&north_game_machine_stage>=1&&north_game_machine_stage<=4){
  if(north_game_machine_ticks)north_game_machine_ticks--;
  if(north_game_machine_stage==2&&!machine_hit&&py>=76&&py<=97&&px>=48&&px<=192){machine_hit=1;game_north_hurt(16);}
  if(!north_game_machine_ticks){if(north_game_machine_stage==1){north_game_machine_stage=2;north_game_machine_ticks=24;machine_hit=0;}else if(north_game_machine_stage==2){north_game_machine_stage=3;north_game_machine_ticks=90;toast(TX_NT_OPEN);}else if(north_game_machine_stage==3){north_game_machine_stage=4;north_game_machine_ticks=30;}else{north_game_machine_stage=1;north_game_machine_ticks=60;toast(TX_NT_WARN);}changed();}
 }
 if(transition_lock)return;
 if(room==22){if((!game_road_managed||!game_road_managed(22,23))&&(keys&UP)&&px>=224&&px<=255&&py<=18){door(23,0);return;}}
 else if(room==23){if((!game_road_managed||!game_road_managed(23,22))&&(keys&DOWN)&&px>=224&&px<=255&&py>=298){door(22,1);return;}}
 else if((keys&DOWN)&&px>=108&&px<=131&&py>=143){unsigned dest=room==24||room==25?22:room==26?23:(unsigned)room-1,spawn=room==24?3:room==25?4:room==26?1:0;door(dest,spawn);}
}
COLD int north_game_name(void){static const int n[8]={TX_NT_ROOM22,TX_NT_ROOM23,TX_NT_ROOM24,TX_NT_ROOM25,TX_NT_ROOM26,TX_NT_ROOM27,TX_NT_ROOM28,TX_NT_ROOM29};return north_game_is_room((unsigned)room)?n[room-22]:0;}
COLD int north_game_quest_text(void){unsigned q;for(q=11;q<=21;q++)if(state(q)==2)return quest_names[q-11];if(!done(11))return TX_NT_Q11;if(!done(13))return TX_NT_Q13;if(!done(21))return TX_NT_Q21;return TX_NT_JOURNAL;}
COLD void north_game_draw_journal(void){static const int s[4]={TX_NT_UNSEEN,TX_NT_ACTIVE,TX_NT_READY,TX_NT_CLAIMED};unsigned q=11+north_game_journal_selection%11,b,x=88;
 box(8,31,224,122);centered(TX_NT_JOURNAL,34,PAL_GOLD3);text(quest_names[q-11],18,54,PAL_GOLD4);text(s[state(q)],173,54,PAL_TEAL2);text(clues[q-11][0],14,76,PAL_GOLD4);text(clues[q-11][1],14,94,PAL_GOLD4);text(TX_NT_OBJECTIVES,18,115,PAL_TEAL2);
 for(b=1;b<=8;b<<=1)if(northern_quest_mask(q)&b){rect((int)x,118,8,8,(adventure_save.quests.objectives[q]&b)?PAL_GOLD3:PAL_STONE1);x+=13;}
 centered(TX_NT_KEYS,138,PAL_TEAL2);
}
COLD int north_game_menu_input(int k){if(journal_tab!=JOURNAL_TAB)return 0;if(k&UP){north_game_journal_selection=(north_game_journal_selection+10)%11;changed();return 1;}if(k&DOWN){north_game_journal_selection=(north_game_journal_selection+1)%11;changed();return 1;}return 0;}
COLD void north_game_draw_actors(void){unsigned i;if(room==16){return;}
 if(!north_game_is_room((unsigned)room))return;
 if(room==22){north_actor(NORTH_SPR_EDDA,168,192);north_actor(NORTH_SPR_NERI,312,192);north_actor(NORTH_SPR_PELL,64,192);north_actor(NORTH_SPR_TOVE,384,160);north_actor(NORTH_SPR_IVEN,416,208);north_actor(adventure_save.quests.anchors[1]&1?NORTH_SPR_REST_LIT:NORTH_SPR_REST,104,192);north_actor(NORTH_SPR_FORECAST,240,192);
  north_actor(adventure_save.quests.objectives[11]&1?NORTH_SPR_HANDLE_DONE:NORTH_SPR_HANDLE,160,224);north_actor(adventure_save.quests.objectives[11]&2?NORTH_SPR_HANDLE_DONE:NORTH_SPR_HANDLE,304,224);if(done(21))north_actor(NORTH_SPR_BEACON_LIT,240,216);
 }else if(room==23){north_actor(north_game_puzzle.rail&1?NORTH_SPR_JUNCTION_EW:NORTH_SPR_JUNCTION_NS,240,192);north_actor(NORTH_SPR_BEARING,320,192);north_actor(NORTH_SPR_NERI,352,160);north_actor(NORTH_SPR_FERRY_SIGN,112,96);north_actor(NORTH_SPR_TENDER,144+(int)tender_steps*8,112);north_actor(NORTH_SPR_FORECAST,176,144);north_actor(adventure_save.quests.anchors[1]&2?NORTH_SPR_REST_LIT:NORTH_SPR_REST,80,248);
  {static const short xy[3][2]={{176,224},{288,112},{368,240}};for(i=0;i<3;i++)north_actor(adventure_save.quests.objectives[15]&(1u<<i)?NORTH_SPR_SOCKET:NORTH_SPR_MARKER,xy[i][0],xy[i][1]);}
 }else{north_actor(NORTH_SPR_RESET,32,132);
  if(room==24){north_actor(adventure_save.quests.objectives[16]&1?NORTH_SPR_REEL_HELD:NORTH_SPR_REEL,64,80);north_actor(adventure_save.quests.objectives[16]&2?NORTH_SPR_REEL_HELD:NORTH_SPR_REEL,176,80);north_actor(fragile_step?NORTH_SPR_TENDER:NORTH_SPR_CART_LIGHT,120,80);north_actor(NORTH_SPR_EDDA,208,112);if(!ready(16))north_actor(NORTH_SPR_CART_LIGHT,120,48);}
  else if(room==25){for(i=0;i<3;i++){north_actor((adventure_save.quests.objectives[12]&(1u<<i))||heat_held?NORTH_SPR_HEAT_WARM:NORTH_SPR_HEAT_COLD,64+(int)i*56,64);north_actor(adventure_save.quests.objectives[17]&(1u<<i)?NORTH_SPR_CHART_DRY:NORTH_SPR_CHART_DAMP,64+(int)i*56,104);}north_actor(NORTH_SPR_TOVE,208,112);}
  else if(room<=28){north_actor(north_game_puzzle.rail&1?NORTH_SPR_JUNCTION_EW:NORTH_SPR_JUNCTION_NS,120,96);north_actor(NORTH_SPR_REEL,64,64);north_actor(north_game_puzzle.weight?NORTH_SPR_WEIGHT_DOWN:NORTH_SPR_WEIGHT_UP,176,96);north_actor(NORTH_SPR_CART_LIGHT,80+north_game_puzzle.cart[0]*32,64);if(room!=26)north_actor(NORTH_SPR_CART_HEAVY,160-north_game_puzzle.cart[1]*32,96);north_actor(adventure_save.quests.objectives[21]&(1u<<(room-26))?NORTH_SPR_HANDLE_DONE:NORTH_SPR_HANDLE,208,56);if(room>=27)north_actor(room==27?NORTH_SPR_WEIGHT_UP:NORTH_SPR_FORECAST,208,112);}
  else{north_actor(machine_couplings&1?NORTH_SPR_REEL_HELD:NORTH_SPR_REEL,64,108);north_actor(machine_couplings&2?NORTH_SPR_JUNCTION_EW:NORTH_SPR_JUNCTION_NS,176,108);north_actor(NORTH_SPR_HANDLE,120,108);north_actor(north_game_machine_stage==5?NORTH_SPR_BEACON_LIT:north_game_machine_stage==3?NORTH_SPR_MACHINE_OPEN:north_game_machine_stage==1?NORTH_SPR_MACHINE_WARN:NORTH_SPR_MACHINE_IDLE,120,68);}
 }
}
COLD void north_game_draw_overlay(void){
 if(room>=26&&room<=28){int x=80+north_game_puzzle.cart[0]*32;line(64,64,x,64,PAL_GOLD3);if(north_game_puzzle.weight)line(176,96,176,52,PAL_GOLD3);}
 if(room==29){if(north_game_machine_stage==1){line(48,85,192,85,PAL_GOLD3);line(48,88,192,88,PAL_GOLD3);}else if(north_game_machine_stage==2)rect(48,81,145,12,PAL_ROSE4);else if(north_game_machine_stage==3){line(106,54,133,54,PAL_WATER4);line(106,81,133,81,PAL_WATER4);}if(north_game_machine_stage&&north_game_machine_stage<5){rect(87,42,66,4,PAL_STONE1);rect(88,43,north_game_machine_hp/2,2,PAL_GOLD3);}}
}
