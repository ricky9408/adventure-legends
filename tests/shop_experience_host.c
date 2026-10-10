/* Focused player-facing shop behavior. Economy/save are explicit boundary doubles;
 * native controller tests and the economy suite establish real persistence. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "game_shop.h"
#include "economy.h"
#include "later_rewards.h"
#include "progression.h"
#include "gear_runtime.h"
#include "journal_nav.h"
#include "ui.h"
volatile int game_state,room,px,py,has_save,save_failed;
int face,pressed,keys,journal_tab,ability_cd,heal_cd,save_failure_notice,save_requested,save_ordinary_scope,quickparty_open,hero_hp_q4;
unsigned save_feedback_background,north_game_revision,south_game_revision,magma_game_revision,underwater_game_revision;
unsigned char north_game_machine_stage,south_game_machine_stage;
void progression_refresh(void){}
void dialogue(int a,int b,int state){(void)a;(void)b;game_state=state;}
void text_spans(const UiText*t,int x,int y,int c){(void)c;assert(x>=0&&y>=0&&x+t->width<=240&&y+t->height<=160);}
unsigned later_rewards_claimable(const Save5State*s){(void)s;return 0;}
unsigned later_rewards_check(const Save5State*s,unsigned t,unsigned source,const LaterRewardContext*c){(void)s;(void)t;(void)source;(void)c;return LATER_NOT_EARNED;}
int later_rewards_begin(Save5State*s,unsigned t,unsigned source,const LaterRewardContext*c){(void)s;(void)t;(void)source;(void)c;return 0;}
int later_rewards_pending(void){return 0;}
int later_rewards_cancel(void){return 1;}
unsigned later_rewards_step(const LaterRewardContext*c){(void)c;return SAVE5_FAILED;}
unsigned later_rewards_last_gold(void){return 0;}
unsigned later_rewards_last_xp(void){return 0;}
unsigned later_rewards_last_fresh(void){return 0;}
EquipmentStats gear_stats;
Save5State adventure_save;
static unsigned short framebuffer[19204];unsigned short *screen=framebuffer+2;
static unsigned calls,error_code,pending,status,claimed,last_gold=60,heals,refreshes,busy;
static int rendered[128],render_y[128],render_count;
int near(int x,int y,int a,int b,int r){return abs(x-a)+abs(y-b)<r;}
void box(int x,int y,int w,int h){assert(x>=0&&y>=0&&x+w<=240&&y+h<=160);}
void rect(int x,int y,int w,int h,unsigned char c){int i,j;assert(x>=0&&y>=0&&x+w<=240&&y+h<=160);for(j=y;j<y+h;j++)for(i=x;i<x+w;i++)((unsigned char*)screen)[j*240+i]=c;}
void text(int id,int x,int y,int c){(void)c;assert(id>=0&&id<TX_COUNT);assert(x>=0&&x+ui_texts[id].width<=240&&y>=0&&y+ui_texts[id].height<=160);assert(render_count<128);rendered[render_count]=id;render_y[render_count++]=y;}
void centered(int id,int y,int c){text(id,(240-ui_texts[id].width)/2,y,c);}
void toast(int id){(void)id;}void save_game(void){}void acknowledge_save_failure(void){save_failure_notice=0;}
void save_feedback_capture(const Save5State*s){(void)s;}void save_feedback_complete(int ok){(void)ok;}void save_feedback_invalidate(void){}
unsigned economy_gold(const Save5State*s){return s->economy.gold;}
unsigned economy_supply_count(const Save5State*s,unsigned i){return i<2?s->economy.supplies[i]:0;}
unsigned economy_price(unsigned i){static const unsigned p[3]={18,24,120};return i<3?p[i]:0;}
unsigned economy_claimable(const Save5State*s){(void)s;return claimed;}
unsigned economy_last_error(void){return error_code;}unsigned economy_last_gold(void){return last_gold;}
int economy_pending(void){return pending;}unsigned economy_step(void){if(status!=SAVE5_BUSY)pending=0;return status;}
int economy_begin_purchase(Save5State*s,unsigned i){(void)s;(void)i;calls++;if(error_code)return 0;pending=1;return 1;}
int economy_begin_use(Save5State*s,unsigned i){return economy_begin_purchase(s,i);}
int economy_begin_claim(Save5State*s,unsigned i){return economy_begin_purchase(s,i);}
unsigned game_gear_busy(void){return busy;}
void game_health_refresh(int fill){(void)fill;refreshes++;}
void game_health_heal(unsigned n){heals++;hero_hp_q4+=(int)n;if(hero_hp_q4>gear_stats.max_hp_q4)hero_hp_q4=gear_stats.max_hp_q4;}
static void reset(void){memset(&adventure_save,0,sizeof adventure_save);game_state=1;room=0;px=56;py=100;pressed=keys=journal_tab=quickparty_open=0;calls=error_code=pending=claimed=heals=refreshes=busy=0;status=SAVE5_BUSY;hero_hp_q4=gear_stats.max_hp_q4=144;save_failed=save_failure_notice=0;game_shop_reset();}
static void input(int held,int edge){int expected=game_state==11||game_state==12||game_state==13;keys=held;pressed=edge;game_shop_tick();assert(game_shop_update()==expected);}
static void tap(int key){input(key,key);input(0,0);}
static int saw(int id){int i;for(i=0;i<render_count;i++)if(rendered[i]==id)return 1;return 0;}
static void draw(void){render_count=0;memset(framebuffer,0,sizeof framebuffer);framebuffer[0]=framebuffer[1]=framebuffer[19202]=framebuffer[19203]=0xbeef;if(game_state==3)game_shop_draw_items();else game_shop_draw();assert(framebuffer[0]==0xbeef&&framebuffer[1]==0xbeef&&framebuffer[19202]==0xbeef&&framebuffer[19203]==0xbeef);}
static void context_and_errors(void){reset();assert(game_shop_in_range()&&game_shop_interact());error_code=ECONOMY_NO_GOLD;tap(1);tap(1);draw();assert(saw(TX_FB_NO_GOLD)&&saw(TX_FB_BUY_KEYS));assert(calls==1);tap(2);draw();assert(!saw(TX_FB_NO_GOLD)&&saw(TX_FB_SHOP_KEYS));tap(2);assert(game_state==1);game_state=3;journal_tab=JOURNAL_ITEMS;game_shop_tick();draw();assert(!saw(TX_FB_NO_GOLD)&&saw(TX_FB_TONIC_DESC)&&saw(TX_PF_ITEM_KEYS));
 adventure_save.economy.supplies[0]=1;adventure_save.economy.supplies[1]=1;game_shop_items_input(1);draw();assert(saw(TX_FB_HEALTH_FULL)&&saw(TX_PF_ITEM_KEYS));game_shop_items_input(128);draw();assert(!saw(TX_FB_HEALTH_FULL)&&saw(TX_FB_SPIRIT_DESC));game_shop_items_input(1);draw();assert(saw(TX_FB_POWER_READY)&&saw(TX_PF_ITEM_KEYS));journal_tab=JOURNAL_HUB;game_shop_tick();journal_tab=JOURNAL_ITEMS;draw();assert(!saw(TX_FB_POWER_READY));
 ability_cd=20;busy=1;game_shop_items_input(1);draw();assert(saw(TX_FB_ITEM_BUSY)&&saw(TX_PF_ITEM_KEYS));busy=0;game_shop_items_input(1);draw();assert(game_shop_confirm&&saw(TX_FB_SPIRIT_DESC)&&saw(TX_FB_USE_KEYS)&&!saw(TX_FB_ITEM_BUSY));game_shop_items_input(2);assert(!game_shop_confirm);adventure_save.economy.supplies[1]=0;game_shop_items_input(1);draw();assert(saw(TX_FB_NONE)&&saw(TX_PF_ITEM_KEYS));game_shop_cancel_items();draw();assert(!saw(TX_FB_NONE));
 reset();game_shop_interact();error_code=ECONOMY_FULL;tap(1);tap(1);draw();assert(saw(TX_FB_FULL)&&saw(TX_FB_BUY_KEYS));tap(2);tap(128);draw();assert(!saw(TX_FB_FULL)&&saw(TX_FB_SPIRIT_DESC));
 puts("PASS shop/item feedback follows its selection and context; errors retain A/B hints");}
static void repeat_and_commit(void){unsigned i;reset();game_shop_interact();input(128,128);assert(game_shop_selection==1);for(i=0;i<17;i++)input(128,0);assert(game_shop_selection==1);input(128,0);assert(game_shop_selection==2);for(i=0;i<6;i++)input(128,0);assert(game_shop_selection==0);input(0,0);input(192,192);for(i=0;i<60;i++)input(192,0);assert(game_shop_selection==0);input(0,0);
 input(1,1);for(i=0;i<90;i++)input(1,0);assert(game_shop_confirm&&calls==0);input(0,0);input(1,1);assert(game_state==12&&calls==1);for(i=0;i<90;i++)input(1,0);assert(calls==1&&game_state==12);status=SAVE5_DONE;input(1,0);assert(game_state==11&&!game_shop_confirm);for(i=0;i<90;i++)input(1,0);assert(calls==1&&!game_shop_confirm);draw();assert(saw(TX_FB_BOUGHT)&&saw(TX_FB_SHOP_KEYS));
 reset();game_state=3;journal_tab=JOURNAL_ITEMS;adventure_save.economy.supplies[0]=1;hero_hp_q4=96;game_shop_items_input(1);game_shop_items_input(1);assert(game_state==12&&calls==1&&!heals);for(i=0;i<30;i++)input(0,0);assert(!heals&&hero_hp_q4==96);status=SAVE5_DONE;input(0,0);assert(heals==1&&hero_hp_q4==128&&game_state==3);game_shop_tick();assert(heals==1);draw();assert(saw(TX_FB_USED)&&saw(TX_PF_ITEM_KEYS));
 reset();game_shop_interact();tap(1);tap(1);status=SAVE5_FAILED;input(0,0);assert(save_failed&&save_failure_notice);draw();assert(saw(TX_FB_SAVE_RETRY)&&saw(TX_FB_BUY_KEYS));
 puts("PASS held directions repeat at18/6; A remains edge-triggered; pending, done, and failed transactions stay singular");}
static void rewards(void){unsigned i,gold,xp;reset();game_shop_reward(180,6);gold=game_shop_reward_gold;xp=game_shop_reward_xp;for(i=0;i<40;i++)game_shop_tick();assert(game_shop_reward_visible());game_state=3;assert(!game_shop_reward_visible());for(i=0;i<300;i++)game_shop_tick();game_state=2;assert(!game_shop_reward_visible());for(i=0;i<300;i++)game_shop_tick();game_state=1;quickparty_open=1;assert(!game_shop_reward_visible());for(i=0;i<300;i++)game_shop_tick();render_count=0;game_shop_draw_reward();assert(!render_count&&!game_shop_reward_visible());quickparty_open=0;assert(game_shop_reward_visible());for(i=0;i<54;i++)game_shop_tick();assert(game_shop_reward_visible());game_shop_tick();assert(!game_shop_reward_visible());assert(game_shop_reward_gold==gold&&game_shop_reward_xp==xp&&!adventure_save.economy.gold);puts("PASS reward gets95 visible play updates across hub/dialogue/picker pauses without changing credits");}
static void layout(void){int selection;reset();adventure_save.economy.gold=9999;adventure_save.economy.supplies[0]=9;adventure_save.economy.supplies[1]=9;adventure_save.economy.relics=7;adventure_save.economy.upgrade=1;game_shop_interact();claimed=7;for(selection=0;selection<4;selection++){game_shop_selection=selection;draw();assert(saw(TX_PF_STOCK)&&saw(TX_EC_PRICE)&&saw(TX_FB_SHOP_KEYS));tap(1);draw();assert(saw(TX_FB_BUY_KEYS));tap(2);}game_state=3;journal_tab=JOURNAL_ITEMS;for(selection=0;selection<10;selection++){draw();assert(saw(TX_PF_STOCK));game_shop_items_input(128);}assert(!calls);puts("PASS all shop/claim/ten item rows render within240x160 with stock, prices, effects and separate controls");}
int main(void){context_and_errors();repeat_and_commit();rewards();layout();return 0;}
