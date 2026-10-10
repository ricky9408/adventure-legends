#ifndef EMBERBOND_HORIZONS_AUDIO_H
#define EMBERBOND_HORIZONS_AUDIO_H
/* Original 180-active-update stage phrase. PSG2 only; PCM and PSG1 keep owners. */
void game_horizons_performance_start(void);
void game_horizons_performance_stop(void);
/* Advance only from the real world tick; poll never advances musical time. */
void horizons_audio_tick(void);
void horizons_audio_poll(void);
extern unsigned char horizons_music_active,horizons_music_note,horizons_music_left,horizons_music_paused;
#endif
