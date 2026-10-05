#ifndef EMBERBOND_TRIAL_ART_H
#define EMBERBOND_TRIAL_ART_H
/* Original deterministic art, existing indexed palette. Row-major backgrounds
 * are opaque240x160; sprite data16x16 with zero transparency; center anchors. */
extern const unsigned char trial_background_wind[38400];
extern const unsigned char trial_background_stone[38400];
extern const unsigned char trial_aid_sprites[6][2][256];
extern const unsigned char trial_vane_sprites[4][256];
enum { TRIAL_SPR_WIND_SIGN,TRIAL_SPR_STONE_SIGN,TRIAL_SPR_RESET,TRIAL_SPR_PARCEL,
 TRIAL_SPR_LOOM,TRIAL_SPR_LOOM_LIT,TRIAL_SPR_ARCH,TRIAL_SPR_ARCH_LIT,TRIAL_SPR_COUNT };
extern const unsigned char trial_misc_sprites[TRIAL_SPR_COUNT][256];
#endif
