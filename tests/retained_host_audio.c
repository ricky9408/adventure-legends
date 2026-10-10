/* Explicit host-only audio boundary for game-state integration tests.
 * This file does not emulate audio, timers, DMA, IRQs or their cycle cost.
 * Native ROM tests use the real frozen music implementation and never link it.
 * Legacy music_tick/music_step are inert fixture controls only; they are not
 * claimed to exist in the new cartridge or to describe its audio state. */
#if defined(__arm__) || defined(__thumb__)
#error "retained_host_audio.c must never be linked into an ARM cartridge"
#endif
#include "music.h"
int music_tick,music_step;
const char retained_host_audio_scope[]="host audio disabled; no audio/IRQ/timing claim";
void music_init(void){}
void music_update(unsigned room,unsigned state){(void)room;(void)state;}
void music_service(void){}
