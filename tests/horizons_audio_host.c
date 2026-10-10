#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "progression.h"
#include "horizons_audio.h"
volatile int room,game_state;
int quickparty_open;
Save5State adventure_save;
unsigned short horizons_audio_host_registers[128];
#define R(a) horizons_audio_host_registers[(a)/2]
static unsigned short before[128];
static void setup(void){unsigned i;
 game_horizons_performance_stop();memset(&adventure_save,0,sizeof adventure_save);
 for(i=0;i<128;i++)horizons_audio_host_registers[i]=(unsigned short)(0x4100+i);
 R(0x80)=0x1177;R(0x84)=0x80;room=68;game_state=1;quickparty_open=0;
 memcpy(before,horizons_audio_host_registers,sizeof before);
}
static void ownership(void){unsigned i;
 for(i=0;i<128;i++)if(i!=0x68/2&&i!=0x6c/2&&i!=0x80/2)
  assert(horizons_audio_host_registers[i]==before[i]);
 assert((R(0x80)&(unsigned short)~0x2200u)==before[0x80/2]);
}
int main(void){unsigned i,ticks,changes;unsigned char note,left;
 setup();game_horizons_performance_start();assert(!horizons_music_active);
 adventure_save.quests.objectives[57]=4;room=67;game_horizons_performance_start();assert(!horizons_music_active);
 room=68;R(0x84)=0;game_horizons_performance_start();assert(!horizons_music_active);R(0x84)=0x80;
 game_state=10;game_horizons_performance_start();assert(horizons_music_active&&horizons_music_paused);
 assert(horizons_music_left==20);for(i=0;i<40;i++){horizons_audio_poll();horizons_audio_tick();}
 assert(horizons_music_left==20&&horizons_music_note==0);ownership();
 game_state=1;horizons_audio_tick();assert(horizons_music_left==19&&!horizons_music_paused&&(R(0x80)&0x2200)==0x2200);
 assert((R(0x6c)&0x8000)&&((R(0x68)>>12)&15)==2);ownership();
 note=horizons_music_note;left=horizons_music_left;game_horizons_performance_start();assert(note==horizons_music_note&&left==horizons_music_left);
 /* All modal states and the quick picker preserve the sequence, including
  * accidental calls to tick while the world is stopped. */
 {unsigned modes[]={2,3,6,7,8,10};for(i=0;i<sizeof modes/sizeof modes[0];i++){
   game_state=(int)modes[i];horizons_audio_poll();horizons_audio_tick();
   assert(horizons_music_note==note&&horizons_music_left==left&&horizons_music_paused&&R(0x68)==0);
 }}
 game_state=1;quickparty_open=1;for(i=0;i<90;i++){horizons_audio_poll();horizons_audio_tick();}
 assert(horizons_music_note==note&&horizons_music_left==left);quickparty_open=0;
 /* No world tick (for example hitstop) means no sequence time elapses. */
 for(i=0;i<60;i++)horizons_audio_poll();assert(horizons_music_left==left);
 game_horizons_performance_stop();assert(!horizons_music_active&&R(0x80)==0x1177);ownership();
 setup();adventure_save.quests.objectives[57]=4;game_horizons_performance_start();changes=1;note=0;
 for(ticks=0;horizons_music_active&&ticks<181;ticks++){
  horizons_audio_tick();if(horizons_music_active&&horizons_music_note!=note){changes++;note=horizons_music_note;}
  ownership();
 }
 assert(ticks==180&&changes==12&&!horizons_music_active&&R(0x68)==0&&R(0x80)==0x1177);
 {int modes[]={0,4,5,9};for(i=0;i<4;i++){
   game_state=1;game_horizons_performance_start();horizons_audio_tick();game_state=modes[i];horizons_audio_poll();assert(!horizons_music_active);
   game_horizons_performance_start();assert(!horizons_music_active);
 }}
 game_state=1;game_horizons_performance_start();horizons_audio_tick();room=62;horizons_audio_poll();assert(!horizons_music_active);ownership();
 puts("PASS: PSG2 ownership, committed trigger, 180 actual world ticks, 12 notes, modal/picker/hitstop timing, no active restart, exit/death reset");
 return 0;
}
