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
typedef uint32_t u32;

Save5State adventure_save;
volatile unsigned int chapter_flags;
volatile int room;
int game_state,quickparty_open,quickparty_visible,toast_id,toast_ticks,field_goal_detail;
int px,py,invuln,save_calls;

unsigned save5_quest_state(const Save5Quests*q,unsigned n){
 return n<64?(q->states[n>>2]>>((n&3)*2))&3:0;
}
void save_game(void){save_calls++;}

#include "field_goal_select.inc"

static void reset(void){
 memset(&adventure_save,0,sizeof adventure_save);
 game_state=PLAY;room=0;chapter_flags=0;quickparty_open=quickparty_visible=0;
 toast_id=toast_ticks=field_goal_detail=0;px=120;py=126;invuln=save_calls=0;
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
 puts("PASS field Select opening and grove goals, modal guards, unchanged player/save, journal parity, card cache key");
 return 0;
}
