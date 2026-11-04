#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "journey_goal.h"
#include "save4.h"
#include "ui.h"

#define COLD
#define KEY_SELECT 4
#define PLAY 1
#define DIALOG 2
#define PAUSE 3
#define DEAD 4
#define EVOLVE_CONFIRM 5
#define EVOLVE_ANIM 6
#define SAVE_NOTICE_Y 8
#define SAVE_NOTICE_H 19
typedef uint32_t u32;
typedef uint16_t u16;
typedef struct {u16 a0,a1,a2,pad;} ObjEntry;

Save5State adventure_save;
volatile unsigned int chapter_flags;
volatile int room;
int game_state,quickparty_open,quickparty_visible,toast_id,toast_ticks,field_goal_detail;
int px,py,invuln,save_calls;
int camera_x,camera_y,obj_count,fixture_hint,fixture_reward;
ObjEntry obj_entries[128];int obj_depth[128];
const UiText ui_texts[TX_COUNT]={
 [TX_JG_BEGIN]={.width=100},[TX_JG_BEGIN_DETAIL]={.width=120}
};

int scrolling_room(void){return 0;}
int save_notice_visible(void){return 0;}
int save_notice_left(void){return 0;}
int game_save_badge_left(void){return 240;}
int game_shop_reward_visible(void){return fixture_reward;}
int game_display_state(void){return game_state;}
int play_hint_text(void){return fixture_hint;}

unsigned save5_quest_state(const Save5Quests*q,unsigned n){
 return n<64?(q->states[n>>2]>>((n&3)*2))&3:0;
}
void save_game(void){save_calls++;}

#include "field_goal_select.inc"

static void reset(void){
 memset(&adventure_save,0,sizeof adventure_save);
 game_state=PLAY;room=0;chapter_flags=0;quickparty_open=quickparty_visible=0;
 toast_id=toast_ticks=field_goal_detail=0;px=120;py=126;invuln=save_calls=0;
 obj_count=fixture_hint=fixture_reward=0;
}
int main(void){
 static Save5State before;
 JourneyGoal journal;
 reset();memcpy(&before,&adventure_save,sizeof before);
 journal=journey_goal_read(&adventure_save,chapter_flags,(unsigned)room);
 field_goal_input(KEY_SELECT);
 assert(toast_id==TX_JG_BEGIN&&field_goal_detail==TX_JG_BEGIN_DETAIL&&toast_ticks==110);
 assert(journal.title==toast_id&&journal.detail==field_goal_detail);
 assert(!memcmp(&before,&adventure_save,sizeof before));
 assert(px==120&&py==126&&invuln==0&&save_calls==0&&game_state==PLAY);
 field_goal_input(0);assert(toast_ticks==110);
 toast(TX_SUMMONED);assert(field_goal_detail==0&&toast_id==TX_SUMMONED);

 reset();chapter_flags=SAVE4_GROVE_CLEAR;
 journal=journey_goal_read(&adventure_save,chapter_flags,(unsigned)room);
 field_goal_input(KEY_SELECT);
 assert(toast_id==TX_C_QUEST_ACT2&&field_goal_detail==TX_JG_SKY_DETAIL);
 assert(journal.title==toast_id&&journal.detail==field_goal_detail);
 assert(px==120&&py==126&&invuln==0&&save_calls==0);

 reset();game_state=PAUSE;field_goal_input(KEY_SELECT);assert(!toast_ticks);
 game_state=DIALOG;field_goal_input(KEY_SELECT);assert(!toast_ticks);
 game_state=PLAY;quickparty_open=1;field_goal_input(KEY_SELECT);assert(!toast_ticks);
 quickparty_open=0;quickparty_visible=1;field_goal_input(KEY_SELECT);assert(!toast_ticks);

 reset();toast_id=TX_JG_ELDER;toast_ticks=110;field_goal_detail=TX_JG_ELDER_LIGHTS;
 {unsigned first=play_toast_cache_key();field_goal_detail=TX_JG_ELDER_NEW;
  assert(first!=play_toast_cache_key()&&first>=TX_COUNT);}
 field_goal_detail=0;assert(play_toast_cache_key()==TX_JG_ELDER);
 game_state=PAUSE;assert(play_toast_cache_key()==0);

 reset();field_goal_input(KEY_SELECT);
 obj_add(0,112,115,16,16,1,126,0);assert(obj_count==0);
 obj_add(0,0,123,16,16,1,126,0);assert(obj_count==1);
 obj_add(0,112,154,16,16,1,170,0);assert(obj_count==2);
 obj_count=0;fixture_hint=1;
 obj_add(0,112,115,16,16,1,126,0);assert(obj_count==1);
 obj_count=0;fixture_hint=0;fixture_reward=1;
 obj_add(0,122,115,16,16,1,126,0);assert(obj_count==1);
 obj_count=0;fixture_reward=0;toast(TX_SUMMONED);
 obj_add(0,112,115,16,16,1,126,0);assert(obj_count==1);
 puts("PASS field Select goals, modal guards, unchanged player/save, journal parity, cache key, sprite legibility");
 return 0;
}
