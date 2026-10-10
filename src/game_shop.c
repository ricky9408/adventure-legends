#include "game_shop.h"
#include "economy.h"
#include "later_rewards.h"
#include "treasure_text_text.h"
#include "north_game.h"
#include "south_game.h"
#include "magma_game.h"
#include "underwater_game.h"
#include "save_feedback.h"
#include "progression.h"
#include "gear_runtime.h"
#include "gear_menu.h"
#include "journal_nav.h"
#include "quickparty.h"
#include "ui.h"
#include "assets.h"
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
#define PLAY 1
#define PAUSE 3
#define SHOP 11
#define SHOP_BUSY 12
#define SHOP_RECEIPT 13
#define A 1
#define B 2
#define START 8
#define UP 64
#define DOWN 128
extern volatile int game_state,room,px,py,has_save,save_failed;
extern int face,pressed,keys,journal_tab,ability_cd,heal_cd,save_failure_notice,save_requested,save_ordinary_scope;
extern void dialogue(int,int,int),text_spans(const UiText*,int,int,int);
extern void box(int,int,int,int),text(int,int,int,int),centered(int,int,int),rect(int,int,int,int,unsigned char),toast(int),save_game(void),acknowledge_save_failure(void);
extern int near(int,int,int,int,int),game_region_entry_safe(void);
unsigned game_shop_revision,game_shop_reward_xp,game_shop_reward_gold;
int game_shop_selection,game_shop_confirm;
static int item_selection,return_state,pending_kind,pending_item,feedback,feedback_ticks;
static unsigned reward_ticks,receipt_boss,receipt_gold,shop_repeat_direction,shop_repeat_delay;
static int feedback_context;
static unsigned later_scene=1,pending_source,receipt_later,receipt_fresh,receipt_xp;
static LaterRewardContext later_context(void){LaterRewardContext c;c.scene=later_scene;c.room=room;c.x=px;c.y=py;c.facing=face;c.source_state=pending_source==LATER_SOURCE_NORTH_MACHINE?north_game_machine_stage:pending_source==LATER_SOURCE_SOUTH_MACHINE?south_game_machine_stage:0;return c;}
int game_shop_scene_change(void){if(later_rewards_pending()&&!later_rewards_cancel())return 0;if(!++later_scene)later_scene=1;return 1;}
static void treasure_text(unsigned id,int x,int y,int color){text_spans(&treasure_text_texts[id],x,y,color);}
static void treasure_center(unsigned id,int y,int color){treasure_text(id,(240-treasure_text_texts[id].width)/2,y,color);}
static const unsigned char digits[10][5]={{7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},{5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},{7,5,7,5,7},{7,5,7,1,7}};
#if defined(__arm__)
#define SHOP_DIGITS __attribute__((section(".iwram.text.shop_digits"),long_call,noinline))
#else
#define SHOP_DIGITS
#endif
extern unsigned short *screen;
static SHOP_DIGITS void digit_blit(unsigned digit,int x,int y,unsigned color){unsigned row;unsigned short ink=(unsigned short)(color|(color<<8));
 for(row=0;row<5;row++){unsigned bits=digits[digit][row];unsigned short*p=screen+(y+(int)row)*120+(x>>1),mask;
  if(x&1){if(bits&4)*p=(unsigned short)((*p&255)|(color<<8));mask=(unsigned short)(((bits&2)?255:0)|((bits&1)?65280:0));if(mask)p[1]=(unsigned short)((p[1]&~mask)|(ink&mask));}
  else{mask=(unsigned short)(((bits&4)?255:0)|((bits&2)?65280:0));if(mask)*p=(unsigned short)((*p&~mask)|(ink&mask));if(bits&1)p[1]=(unsigned short)((p[1]&65280)|color);}
 }
}
static SHOP_DIGITS void number(unsigned n,int x,int y,int color){unsigned values[4]={0,0,0,0},i;int started=0;if(n>9999)n=9999;
 while(n>=1000){n-=1000;values[0]++;}while(n>=100){n-=100;values[1]++;}while(n>=10){n-=10;values[2]++;}values[3]=n;
 for(i=0;i<4;i++)if(values[i]||started||i==3){digit_blit(values[i],x,y,(unsigned)color);x+=4;started=1;}
}
static void gain(unsigned n,int x,int y,int color){rect(x,y+2,3,1,(unsigned char)color);rect(x+1,y+1,1,3,(unsigned char)color);number(n,x+5,y,color);}
/* The menus have room for readable 6x10 digits; the brief field reward keeps
   its compact font. Menu draws are cached, so this runs only after a change. */
static void menu_number(unsigned n,int x,int y,int color){unsigned values[4]={0,0,0,0},i,row,bit;unsigned short ink=(unsigned short)(color|(color<<8));int started=0;if(n>9999)n=9999;
 while(n>=1000){n-=1000;values[0]++;}while(n>=100){n-=100;values[1]++;}while(n>=10){n-=10;values[2]++;}values[3]=n;
 for(i=0;i<4;i++)if(values[i]||started||i==3){for(row=0;row<5;row++){unsigned short*p=screen+(y+(int)row*2)*120+(x>>1);for(bit=0;bit<3;bit++)if(digits[values[i]][row]&(4u>>bit))p[bit]=p[bit+120]=ink;}x+=8;started=1;}
}
static void changed(void){game_shop_revision++;}
static int menu_context(void){int state=game_shop_display_state();return state==SHOP?SHOP:state==PAUSE&&journal_tab==JOURNAL_ITEMS?PAUSE:state==SHOP_RECEIPT?SHOP_RECEIPT:0;}
static void clear_feedback(void){if(feedback||feedback_ticks){feedback=feedback_ticks=feedback_context=0;changed();}}
static int shop_input(void){unsigned direction=(unsigned)keys&240u;int input=pressed&~240;
 if(direction!=UP&&direction!=DOWN){shop_repeat_direction=shop_repeat_delay=0;return input;}
 if(pressed&(B|START)){shop_repeat_direction=shop_repeat_delay=0;return input;}
 if(direction!=shop_repeat_direction){shop_repeat_direction=direction;shop_repeat_delay=18;return input|(int)direction;}
 if(shop_repeat_delay&&!--shop_repeat_delay){shop_repeat_delay=6;return input|(int)direction;}return input;
}
static void notify(int id){feedback=id;feedback_ticks=140;feedback_context=menu_context();changed();}
static unsigned next_claim(void){unsigned mask=economy_claimable(&adventure_save),i;for(i=0;i<3;i++)if(mask&(1u<<i))return i;mask=later_rewards_claimable(&adventure_save);for(i=0;i<4;i++)if(mask&(1u<<i))return i+3;return 7;}
static int error_text(void){unsigned e=economy_last_error();return e==ECONOMY_NO_GOLD?TX_FB_NO_GOLD:e==ECONOMY_EMPTY?TX_FB_NONE:e==ECONOMY_FULL||e==ECONOMY_ALREADY_OWNED?TX_FB_FULL:TX_FB_SAVE_RETRY;}
void game_shop_reset(void){game_shop_scene_change();receipt_later=receipt_fresh=receipt_xp=0;game_shop_selection=game_shop_confirm=item_selection=pending_kind=pending_item=feedback=feedback_ticks=0;reward_ticks=game_shop_reward_xp=game_shop_reward_gold=shop_repeat_direction=shop_repeat_delay=0;feedback_context=0;changed();}
void game_shop_cancel_items(void){game_shop_confirm=0;clear_feedback();changed();}
void game_shop_tick(void){
 if(game_state==PAUSE&&journal_tab!=JOURNAL_ITEMS&&game_shop_confirm){game_shop_confirm=0;changed();}
 if(feedback&&menu_context()!=feedback_context)clear_feedback();
 if(feedback_ticks&&!--feedback_ticks){feedback=feedback_context=0;changed();}
 /* Menus, dialogue, and the held-L picker hide the reward and pause its life. */
 if(game_state==PLAY&&!quickparty_open&&reward_ticks&&!--reward_ticks)changed();
}
static COLD int begin(unsigned kind,unsigned item,int resume){int ok;if(kind!=3){save_ordinary_scope=1;save_game();save_ordinary_scope=0;}
 ok=kind==1?economy_begin_purchase(&adventure_save,item):kind==2?economy_begin_use(&adventure_save,item):economy_begin_claim(&adventure_save,item);
 if(!ok){notify(error_text());return 0;}
 save_requested=0;return_state=resume;pending_kind=(int)kind;pending_item=(int)item;feedback=feedback_ticks=0;game_state=SHOP_BUSY;changed();return 1;
}
static COLD int begin_later(unsigned treasure,unsigned source,int resume){LaterRewardContext c;pending_source=source;c=later_context();
 if(!later_rewards_begin(&adventure_save,treasure,source,&c)){notify(TX_FB_SAVE_RETRY);if(resume==PLAY)toast(TX_FB_SAVE_RETRY);return 0;}
 save_requested=0;return_state=resume;pending_kind=4;pending_item=(int)treasure;feedback=feedback_ticks=0;game_state=SHOP_BUSY;changed();return 1;
}
/* Only exact, eligible authored report geometry consumes A. An unrelated NPC,
 * locked report or already-owned treasure follows the original interaction. */
COLD int game_shop_later_interact(void){unsigned source,treasure,error;LaterRewardContext c;
 if(game_state!=PLAY)return 0;
 switch(room){case 29:source=0;treasure=0;break;case 22:source=1;treasure=0;break;case 37:source=2;treasure=1;break;case 30:source=3;treasure=1;break;case 38:source=4;treasure=2;break;case 46:source=5;treasure=3;break;default:return 0;}
 pending_source=source;c=later_context();error=later_rewards_check(&adventure_save,treasure,source,&c);if(error!=LATER_OK)return 0;
 begin_later(treasure,source,PLAY);return 1;
}
static COLD void begin_shop_claim(void){unsigned claim=next_claim();if(claim<3)begin(3,claim,SHOP);else if(claim<7)begin_later(claim-3,LATER_SOURCE_VILLAGE_SHOP,SHOP);}
static COLD void finish_later_story(void){static const int lines[4][2]={{TX_NT_RETURN_A,TX_NT_RETURN_B},{TX_ST_RETURN_A,TX_ST_RETURN_B},{TX_MG_END,TX_MG_ENDB},{TX_UW_END,TX_UW_HOME}};if(receipt_later&&receipt_fresh&&return_state==PLAY)dialogue(lines[receipt_boss][0],lines[receipt_boss][1],PLAY);receipt_fresh=0;}
int game_shop_in_range(void){return game_state==PLAY&&room==0&&near(px,py,56,100,22);}
int game_shop_interact(void){if(!game_shop_in_range())return 0;game_shop_confirm=0;clear_feedback();shop_repeat_direction=shop_repeat_delay=0;if(next_claim()>=3&&next_claim()<7)game_shop_selection=3;game_state=SHOP;changed();return 1;}
int game_shop_display_state(void){return game_state==SHOP_BUSY?return_state:game_state;}
int game_shop_begin_boss(unsigned boss){if(boss>=3)return 0;return begin(3,boss,game_state);}
COLD int game_shop_update(void){unsigned status;int input;
 if(game_state==SHOP_RECEIPT){if(pressed&(A|B|START)){game_state=return_state;if((pressed&A)&&!(pressed&(B|START)))finish_later_story();else receipt_fresh=0;changed();}return 1;}
 if(game_state==SHOP_BUSY){
  if(pending_kind==4?!later_rewards_pending():!economy_pending()){game_state=return_state;notify(TX_FB_SAVE_RETRY);return 1;}
  if(pending_kind==4){LaterRewardContext c=later_context();status=later_rewards_step(&c);}else status=economy_step();if(status==SAVE5_BUSY)return 1;game_state=return_state;
  if(status==SAVE5_DONE){
   if(pending_kind==4){receipt_later=1;receipt_boss=(unsigned)pending_item;receipt_gold=later_rewards_last_gold();receipt_xp=later_rewards_last_xp();receipt_fresh=later_rewards_last_fresh();progression_refresh();game_health_refresh(0);north_game_revision++;south_game_revision++;magma_game_revision++;underwater_game_revision++;game_shop_reward(receipt_xp,receipt_gold);game_state=SHOP_RECEIPT;if(next_claim()>=7&&game_shop_selection>=3)game_shop_selection=0;}
   else if(pending_kind==2){if(!pending_item)game_health_heal(32);else ability_cd=0;notify(TX_FB_USED);}
   else if(pending_kind==3){receipt_later=receipt_fresh=receipt_xp=0;game_health_refresh(0);receipt_boss=(unsigned)pending_item;receipt_gold=economy_last_gold();game_shop_reward(0,receipt_gold);game_state=SHOP_RECEIPT;notify(TX_FB_RELIC_SAVED);if(next_claim()>=7&&game_shop_selection>=3)game_shop_selection=0;}
   else{if(pending_item==2)game_health_refresh(0);notify(TX_FB_BOUGHT);}
   save_requested=0;save_feedback_background=0;save_feedback_capture(&adventure_save);save_feedback_complete(1);has_save=1;save_failed=0;acknowledge_save_failure();game_shop_confirm=0;
  }else{save_feedback_background=0;save_feedback_invalidate();save_failed=save_failure_notice=1;notify(TX_FB_SAVE_RETRY);toast(TX_C_SAVE_FAILED);}
  pending_kind=0;changed();return 1;
 }
 if(game_state!=SHOP)return 0;
 input=shop_input();
 if(input&(B|START)){clear_feedback();if(game_shop_confirm&&!(input&START)){game_shop_confirm=0;changed();}else{game_state=PLAY;acknowledge_save_failure();}return 1;}
 if(input&4)return 1;
 if(game_shop_confirm){if(input&A){if(game_shop_selection<3)begin(1,(unsigned)game_shop_selection,SHOP);else begin_shop_claim();}return 1;}
 if(input&(UP|DOWN)){int count=next_claim()<7?4:3;game_shop_selection=(game_shop_selection+(input&UP?count-1:1))%count;clear_feedback();changed();return 1;}
 if(input&A){clear_feedback();game_shop_confirm=1;changed();}return 1;
}
COLD int game_shop_items_input(int input){if(game_state!=PAUSE||journal_tab!=JOURNAL_ITEMS)return 0;
 if(input&B){game_shop_confirm=0;clear_feedback();changed();return 1;}
 if(input&(UP|DOWN)){item_selection=(item_selection+(input&UP?9:1))%10;game_shop_confirm=0;clear_feedback();changed();return 1;}
 if(input&A){if(item_selection>=2)return 1;if(!economy_supply_count(&adventure_save,(unsigned)item_selection)){notify(TX_FB_NONE);return 1;}if(!item_selection&&hero_hp_q4>=gear_stats.max_hp_q4){notify(TX_FB_HEALTH_FULL);return 1;}if(item_selection&&!ability_cd){notify(TX_FB_POWER_READY);return 1;}if(item_selection&&game_gear_busy()){notify(TX_FB_ITEM_BUSY);return 1;}if(!game_shop_confirm){clear_feedback();game_shop_confirm=1;changed();}else begin(2,(unsigned)item_selection,PAUSE);return 1;}
 return 0;
}
static void heading(int title){box(8,31,224,123);centered(title,35,PAL_GOLD3);text(TX_FB_GOLD,20,53,PAL_GOLD3);menu_number(economy_gold(&adventure_save),34,57,PAL_GOLD4);}
static void scroll_marks(int first,int more){if(first){rect(225,67,1,1,PAL_GOLD3);rect(224,68,3,1,PAL_GOLD3);rect(223,69,5,1,PAL_GOLD3);}if(more){rect(223,115,5,1,PAL_GOLD3);rect(224,116,3,1,PAL_GOLD3);rect(225,117,1,1,PAL_GOLD3);}}
static void shop_amounts(unsigned item,int y){unsigned owned=item<2?economy_supply_count(&adventure_save,item):adventure_save.economy.upgrade;menu_number(owned,164,y+3,PAL_GOLD3);menu_number(economy_price(item),196,y+3,PAL_GOLD3);}
static void claim_name(unsigned claim,int y,int color){if(claim<3)centered(claim==0?TX_FB_GROVE_RELIC:claim==1?TX_FB_SKY_RELIC:TX_FB_CORE_RELIC,y,color);else if(claim<7)treasure_center(TT_COMPASS+claim-3,y,color);}
COLD int game_shop_draw(void){unsigned i,count,first;static const int names[3]={TX_FB_TONIC,TX_FB_SPIRIT,TX_FB_EDGE};static const int desc[3]={TX_FB_TONIC_DESC,TX_FB_SPIRIT_DESC,TX_FB_EDGE_DESC};
 if(game_state==SHOP_RECEIPT){
  if(receipt_later){box(8,31,224,123);treasure_center(TT_TITLE,35,PAL_GOLD3);treasure_center(TT_COMPASS+receipt_boss,59,PAL_GOLD4);treasure_center(TT_COMPASS_EFFECT+receipt_boss,79,PAL_TEAL2);treasure_center(TT_PERMANENT,97,PAL_TEAL2);text(TX_FB_GOLD,44,115,PAL_GOLD3);menu_number(receipt_gold,64,118,PAL_GOLD4);if(receipt_xp){text(TX_FB_XP,128,115,PAL_TEAL2);menu_number(receipt_xp,166,118,PAL_GOLD4);}treasure_center(TT_RECEIPT_KEYS,138,PAL_TEAL2);}
  else{heading(TX_FB_RELIC_SAVED);claim_name(receipt_boss,75,PAL_GOLD4);text(TX_FB_GOLD,90,102,PAL_GOLD3);menu_number(receipt_gold,118,106,PAL_GOLD4);treasure_center(TT_RECEIPT_KEYS,138,PAL_TEAL2);}return 1;
 }
 if(game_shop_display_state()!=SHOP)return 0;
 heading(TX_FB_SHOP);count=next_claim()<7?4:3;if(game_shop_selection>=(int)count)game_shop_selection=0;
 text(TX_PF_STOCK,150,53,PAL_TEAL2);text(TX_EC_PRICE,196,53,PAL_TEAL2);
 if(game_shop_confirm){unsigned claim=next_claim();centered(game_shop_selection<3?TX_FB_BUY_ASK:TX_FB_CLAIM,73,PAL_GOLD4);
  if(game_shop_selection<3){text(names[game_shop_selection],20,95,PAL_TEAL2);shop_amounts((unsigned)game_shop_selection,95);}else claim_name(claim,95,PAL_TEAL2);
  if(feedback||game_shop_selection<3)centered(feedback?feedback:desc[game_shop_selection],119,PAL_TEAL2);else if(claim>=3)treasure_center(TT_CLAIM_HINT,119,PAL_TEAL2);else centered(TX_EC_CLAIM_HINT,119,PAL_TEAL2);
  centered(TX_FB_BUY_KEYS,138,PAL_TEAL2);return 1;}
 first=game_shop_selection>2?(unsigned)game_shop_selection-2:0;
 for(i=first;i<count&&i<first+3;i++){int y=69+(int)(i-first)*15;if((int)i==game_shop_selection)rect(15,y,210,15,PAL_STONE1);if(i<3){text(names[i],20,y,PAL_GOLD4);shop_amounts(i,y);}else if(next_claim()>=3)treasure_text(TT_CLAIM,20,y,PAL_GOLD4);else text(TX_FB_CLAIM,20,y,PAL_GOLD4);}
 scroll_marks((int)first,first+3<count);if(feedback||game_shop_selection<3)centered(feedback?feedback:desc[game_shop_selection],119,PAL_TEAL2);else if(next_claim()>=3)treasure_center(TT_CLAIM_HINT,119,PAL_TEAL2);else centered(TX_EC_CLAIM_HINT,119,PAL_TEAL2);
 centered(TX_FB_SHOP_KEYS,138,PAL_TEAL2);return 1;
}
static unsigned item_owned(unsigned i){return i<2?economy_supply_count(&adventure_save,i):i<5?!!(adventure_save.economy.relics&(1u<<(i-2))):i==5?adventure_save.economy.upgrade:!!(adventure_save.economy.later_claims&(1u<<(i-6)));}
COLD void game_shop_draw_items(void){int i,first=item_selection>2?item_selection-2:0;static const int names[6]={TX_FB_TONIC,TX_FB_SPIRIT,TX_EC_GROVE_SEED,TX_EC_SKY_FEATHER,TX_EC_CORE_PRISM,TX_FB_EDGE};static const int descriptions[6]={TX_FB_TONIC_DESC,TX_FB_SPIRIT_DESC,TX_EC_GROVE_DESC,TX_EC_SKY_DESC,TX_EC_CORE_DESC,TX_FB_EDGE_DESC};int description=item_selection<6?descriptions[item_selection]:0;unsigned selected_owned=item_owned((unsigned)item_selection);heading(TX_PF_ITEMS);
 if(item_selection>=2&&item_selection!=5&&!selected_owned)description=TX_PF_TREASURE_UNKNOWN;
 text(TX_PF_STOCK,198,53,PAL_TEAL2);
 if(game_shop_confirm&&item_selection<2){centered(TX_FB_USE_ASK,73,PAL_GOLD4);text(names[item_selection],20,95,PAL_TEAL2);menu_number(economy_supply_count(&adventure_save,(unsigned)item_selection),210,98,PAL_GOLD3);centered(feedback?feedback:description,119,PAL_TEAL2);centered(TX_FB_USE_KEYS,138,PAL_TEAL2);return;}
 for(i=first;i<first+3&&i<10;i++){int y=69+(i-first)*15;unsigned owned=item_owned((unsigned)i);if(i==item_selection)rect(15,y,210,15,PAL_STONE1);if(i>=2&&i!=5&&!owned)text(TX_PF_TREASURE_UNKNOWN,20,y,PAL_STONE3);else if(i<6)text(names[i],20,y,owned?PAL_GOLD4:PAL_STONE3);else treasure_text(TT_COMPASS+i-6,20,y,PAL_GOLD4);if(i<2)menu_number(owned,210,y+3,PAL_GOLD3);else if(owned)rect(213,y+5,4,4,PAL_TEAL2);}
 scroll_marks(first,first+3<10);if(feedback||description)centered(feedback?feedback:description,119,PAL_TEAL2);else treasure_center(TT_COMPASS_EFFECT+item_selection-6,119,PAL_TEAL2);centered(item_selection<2?TX_PF_ITEM_KEYS:TX_FB_OWNED_KEYS,138,PAL_TEAL2);
}
/* EXP is the sum of actual before/after gains across occupied party slots. */
void game_shop_reward(unsigned xp,unsigned gold){if(!xp&&!gold)return;game_shop_reward_xp=xp;game_shop_reward_gold=gold;reward_ticks=95;changed();}
unsigned game_shop_reward_visible(void){return game_state==PLAY&&!quickparty_open&&reward_ticks!=0;}
COLD void game_shop_draw_reward(void){int x=8;if(game_state!=PLAY||quickparty_open||!reward_ticks)return;box(5,122,116,17);if(game_shop_reward_xp){text(TX_FB_XP,x,122,PAL_TEAL2);gain(game_shop_reward_xp,x+30,127,PAL_GOLD4);x+=66;}if(game_shop_reward_gold){text(TX_FB_GOLD,x,122,PAL_GOLD3);gain(game_shop_reward_gold,x+13,127,PAL_GOLD4);}}
