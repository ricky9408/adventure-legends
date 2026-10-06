/* Generated original Magma art: same palette, shared streamed OBJ slots. */
#ifndef EMBERBOND_MAGMA_ART_H
#define EMBERBOND_MAGMA_ART_H
#define MAGMA_ART_FIRST_ROOM 38
#define MAGMA_ART_ROOM_COUNT 8
#define MAGMA_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } MagmaArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const MagmaArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } MagmaArtRoom;
extern const MagmaArtRoom magma_art_rooms[8];
enum {
 MAGMA_SPR_RESSA=0,
 MAGMA_SPR_NEMI=1,
 MAGMA_SPR_OMI=2,
 MAGMA_SPR_TAVI=3,
 MAGMA_SPR_SEN=4,
 MAGMA_SPR_PELL=5,
 MAGMA_SPR_REST=6,
 MAGMA_SPR_REST_LIT=7,
 MAGMA_SPR_LIFT=8,
 MAGMA_SPR_BRICK=9,
 MAGMA_SPR_BRICK_HOT=10,
 MAGMA_SPR_BAFFLE=11,
 MAGMA_SPR_SHOE=12,
 MAGMA_SPR_HOOD=13,
 MAGMA_SPR_HOOD_OPEN=14,
 MAGMA_SPR_WHEEL=15,
 MAGMA_SPR_SHELF=16,
 MAGMA_SPR_BOWL=17,
 MAGMA_SPR_TRAY=18,
 MAGMA_SPR_HOOK=19,
 MAGMA_SPR_PIN=20,
 MAGMA_SPR_CATCH=21,
 MAGMA_SPR_SPRING=22,
 MAGMA_SPR_RIBBON=23,
 MAGMA_SPR_GRILLE=24,
 MAGMA_SPR_RESET=25,
 MAGMA_SPR_TRIAL=26,
 MAGMA_SPR_NOTICE=27,
 MAGMA_SPR_GATE=28,
 MAGMA_SPR_DONE=29,
 MAGMA_SPR_REGULATOR=30,
 MAGMA_SPR_REG_WARN=31,
 MAGMA_SPR_REG_OPEN=32,
 MAGMA_SPR_REG_DONE=33,
 MAGMA_SPR_GRAB=34,
 MAGMA_SPR_RESSA_WORK=35,
 MAGMA_SPR_NEMI_WORK=36,
 MAGMA_SPR_OMI_WORK=37,
 MAGMA_SPR_TAVI_WORK=38,
 MAGMA_SPR_SEN_STEP=39,
 MAGMA_SPR_PELL_WORK=40,
 MAGMA_SPR_COUNT=41
};
extern const unsigned char magma_sprites[MAGMA_SPR_COUNT][256];
extern const unsigned char magma_background_kilnstep_commons[153600];
extern const unsigned char magma_background_kilnstep_commons_odd[153600];
extern const unsigned char magma_background_pumice_terraces[153600];
extern const unsigned char magma_background_pumice_terraces_odd[153600];
extern const unsigned char magma_background_potters_walk[38400];
extern const unsigned char magma_background_cloudwell_grotto[38400];
extern const unsigned char magma_background_intake_ledger[38400];
extern const unsigned char magma_background_breathing_vault[38400];
extern const unsigned char magma_background_return_flue_gallery[38400];
extern const unsigned char magma_background_caldera_bell[38400];
#endif
