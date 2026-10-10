#!/usr/bin/env python3
"""Current engine story completion consumes exactly one valid defeated-boss authority."""
from pathlib import Path
import subprocess,tempfile,os
from test_covenants_engine import function
ROOT=Path(__file__).resolve().parents[1]
HEAD=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define COLD
#define PLAY 1
#define EVENT_PENDING 10
#define SAVE4_GROVE_CLEAR 1
#define SAVE4_SKY_CLEAR 2
#define SAVE4_CORE_CLEAR 4
#define SAVE4_SEEN_WIND_JOIN 2
#define SAVE4_SEEN_STONE_JOIN 8
#define SAVE4_SEEN_CORE_RELEASE 64
#define SAVE5_BUSY 1
#define SAVE5_DONE 2
#define SAVE5_FAILED 3
#define CD_GROVE_CLEAR 10
#define CD_WIND_JOIN 11
#define CD_SKY_BOSS_CLEAR 12
#define CD_STONE_JOIN 13
#define CD_CORE_RELEASE 14
#define TX_C_SAVE_FAILED 15
int room,boss_hp,boss_hp_q4,game_state,hazard_mode,save_failed,save_failure_notice;
unsigned chapter_flags,story_reward_chapters;int story_reward_room;unsigned char story_reward_ready;
unsigned char shots[288],impacts[72];int adventure_save;
unsigned pending,prepared,refreshes,saves,scenes,appends,last_scene,last_action,last_seen,last_append,treasure_requests;
int game_shop_begin_boss(unsigned boss){assert(boss==(room==3?0u:room==8?1u:2u));assert(chapter_flags&(1u<<boss));assert(saves==1&&scenes==1);treasure_requests++;return 1;}
void story_rewards_cancel(void){pending=0;}
int story_rewards_pending(void){return pending;}
int story_rewards_begin(void*s,unsigned chapters){assert(s==&adventure_save);assert(chapters==(chapter_flags|(room==3?1:room==8?2:4)));pending=1;return 1;}
unsigned story_rewards_step(void){if(prepared==SAVE5_DONE||prepared==SAVE5_FAILED)pending=0;return prepared;}
void progression_refresh(void){refreshes++;}
void save_at(int room,int spawn){assert(room==0&&spawn==3);saves++;}
void show_scene(int scene,int action,unsigned seen){scenes++;last_scene=scene;last_action=action;last_seen=seen;}
void append_scene(int scene){appends++;last_append=scene;}
void zero(void*p,int n){memset(p,0,n);}
void game_health_fill(void){}
void game_boss_health_set(unsigned hp){boss_hp=hp;boss_hp_q4=hp*16;}
int event_frame(void){game_state=EVENT_PENDING;return 1;}
void toast(int n){assert(n==TX_C_SAVE_FAILED);}
'''
CHECKS=r'''
static void reset(int area,unsigned chapters){game_story_reward_cancel();room=area;chapter_flags=chapters;boss_hp=boss_hp_q4=0;game_state=PLAY;prepared=SAVE5_BUSY;refreshes=saves=scenes=appends=treasure_requests=0;}
static void commit(void){prepared=SAVE5_DONE;assert(game_story_reward_step()==SAVE5_DONE);game_state=PLAY;game_story_reward_finish();}
int main(void){unsigned i;
 for(i=0;i<3;i++){
  int area=i==0?3:i==1?8:13;unsigned chapters=i==0?0:i==1?1:3;
  reset(area,chapters);game_story_reward_finish();assert(!saves&&!scenes&&!treasure_requests&&chapter_flags==chapters);
  boss_reward();assert(pending&&game_state==EVENT_PENDING);game_state=PLAY;game_story_reward_finish();assert(!saves&&!scenes&&!treasure_requests&&chapter_flags==chapters);
  game_state=EVENT_PENDING;assert(game_story_reward_step()==SAVE5_BUSY);assert(!saves&&!scenes);commit();
  assert(chapter_flags==(chapters|(1u<<i))&&saves==1&&refreshes==1&&scenes==1&&treasure_requests==1);
  assert(last_scene==(i==0?CD_GROVE_CLEAR:i==1?CD_SKY_BOSS_CLEAR:CD_CORE_RELEASE));
  assert(last_action==1);assert(last_seen==(i==0?2:i==1?10:64));
  if(i<2)assert(appends==1&&last_append==(i==0?CD_WIND_JOIN:CD_STONE_JOIN));else assert(!appends);
  game_story_reward_finish();boss_reward();assert(!pending&&saves==1&&scenes==1&&treasure_requests==1);
  reset(area,chapters);boss_reward();game_story_reward_cancel();game_state=PLAY;game_story_reward_finish();assert(!saves&&!scenes&&!treasure_requests&&chapter_flags==chapters);
  reset(area,chapters);boss_reward();prepared=SAVE5_DONE;assert(game_story_reward_step()==SAVE5_DONE);game_state=PLAY;room=0;game_story_reward_finish();room=area;game_story_reward_finish();assert(!saves&&!scenes&&!treasure_requests&&chapter_flags==chapters);
  reset(area,chapters);boss_reward();prepared=SAVE5_DONE;assert(game_story_reward_step()==SAVE5_DONE);game_state=PLAY;chapter_flags^=8;game_story_reward_finish();chapter_flags^=8;game_story_reward_finish();assert(!saves&&!scenes&&!treasure_requests&&chapter_flags==chapters);
  reset(area,chapters);boss_reward();prepared=SAVE5_DONE;assert(game_story_reward_step()==SAVE5_DONE);game_state=PLAY;boss_hp_q4=1;game_story_reward_finish();boss_hp_q4=0;game_story_reward_finish();assert(!saves&&!scenes&&!treasure_requests&&chapter_flags==chapters);
  reset(area,chapters);boss_reward();prepared=SAVE5_FAILED;assert(game_story_reward_step()==SAVE5_FAILED);game_state=PLAY;game_story_reward_finish();assert(!saves&&!scenes&&!treasure_requests&&chapter_flags==chapters);
 }
 reset(0,0);boss_reward();assert(!pending);assert(game_story_reward_step()==SAVE5_FAILED);game_story_reward_finish();assert(!saves&&!scenes&&!chapter_flags);
 puts("PASS: valid original scenes, one-shot finish authority; duplicate/cancel/wrong room/chapter/boss context fail closed");return 0;
}
'''
source=(ROOT/'src/game.c').read_text();code=HEAD+''.join(function(source,n)for n in ['game_story_reward_cancel','game_story_reward_step','game_story_reward_finish','boss_reward'])+CHECKS
with tempfile.TemporaryDirectory(prefix='story-finish-')as td:
 p=Path(td);c=p/'test.c';c.write_text(code)
 for name,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  exe=p/name;subprocess.run(['cc','-std=c99','-O1','-Wall','-Wextra','-Werror',*flags,str(c),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
