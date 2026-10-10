#include "horizons_audio.h"
#include "progression.h"
extern volatile int room,game_state;
extern int quickparty_open;
#ifdef HORIZONS_AUDIO_HOST
#if defined(__arm__) || defined(__thumb__)
#error Host register mock must never enter the cartridge
#endif
extern unsigned short horizons_audio_host_registers[128];
#define SREG(offset) horizons_audio_host_registers[(offset)/2]
#else
#define SREG(offset) (*(volatile unsigned short*)(0x04000000u+(offset)))
#endif
/* Composed for the makers' assembly: a rising invitation, an answering turn,
 * then a quiet return. Rates use 2048-131072/f; no borrowed melody/sample.
 * D5,A5,F#5,E5,G5,B5,A5,F#5,E5,A4,E5,D5; total180 active updates. */
static const unsigned short notes[12]={1825,1899,1871,1849,1881,1915,1899,1871,1849,1750,1849,1825};
static const unsigned char lengths[12]={20,10,10,20,20,10,10,20,20,10,10,20};
unsigned char horizons_music_active,horizons_music_note,horizons_music_left,horizons_music_paused;
static void silence(void){SREG(0x68)=0;SREG(0x80)&=(unsigned short)~0x2200u;}
static void play(void){
 SREG(0x80)|=0x2200; /* PSG2 on both speakers, preserve all other routing/gain. */
 SREG(0x68)=0x2340; /* low volume2, decaying envelope3, quarter duty. */
 SREG(0x6c)=(unsigned short)(0x8000u|notes[horizons_music_note]);
}
void game_horizons_performance_stop(void){
 if(horizons_music_active||horizons_music_paused)silence();
 horizons_music_active=horizons_music_note=horizons_music_left=horizons_music_paused=0;
}
void game_horizons_performance_start(void){
 if(horizons_music_active||room!=68||!(adventure_save.quests.objectives[57]&4u)||
    game_state==0||game_state==4||game_state==5||game_state==9||!(SREG(0x84)&0x80))return;
 /* The committed job may call from EVENT_PENDING. Begin audibly only when
  * the engine resumes PLAY, keeping the world-owned visual timer aligned. */
 horizons_music_active=horizons_music_paused=1;horizons_music_note=0;horizons_music_left=lengths[0];
}
void horizons_audio_poll(void){
 if(!horizons_music_active)return;
 if(room!=68||game_state==0||game_state==4||game_state==5||game_state==9||horizons_music_note>=12){game_horizons_performance_stop();return;}
 if(game_state!=1||quickparty_open){if(!horizons_music_paused)silence();horizons_music_paused=1;}
}
void horizons_audio_tick(void){
 horizons_audio_poll();
 if(!horizons_music_active||game_state!=1||quickparty_open)return;
 if(horizons_music_paused){horizons_music_paused=0;play();}
 if(horizons_music_left)--horizons_music_left;
 if(horizons_music_left)return;
 if(++horizons_music_note>=12){game_horizons_performance_stop();return;}
 horizons_music_left=lengths[horizons_music_note];play();
}
