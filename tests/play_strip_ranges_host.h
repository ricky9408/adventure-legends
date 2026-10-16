#ifndef PLAY_STRIP_RANGES_HOST_H
#define PLAY_STRIP_RANGES_HOST_H
#include <stdint.h>

typedef uint16_t u16;
typedef uint32_t u32;
enum { CACHE_FIELDS=45, PLAY=1, FRAME_WORDS=120*160, STRIP_WORDS=120*38 };
typedef struct {
 u32 guard_pre[8];
 u16 bitmap[2][FRAME_WORDS];
 u16 play_world_strip[2][STRIP_WORDS];
 u32 guard_post[8];
 u16 *screen;
 int page,room,game_state,quickparty_open,quickparty_visible;
 int play_strip_valid[2],play_strip_clean[2],play_strip_top[2],play_strip_disabled;
 unsigned play_strip_reuses;
 int cache_valid[2];u32 cache_fields[2][CACHE_FIELDS];
 u16 modal_world_row[2][112];int cached_armor[2];
 int scene_present_phase,save_requested,save_feedback_ordinary;
 int save_feedback_background,save_ordinary_defer,toast_ticks;
 unsigned boss,reward,hints[6],overlay_serial,save_calls;
} StripState;

extern StripState candidate,reference;
void candidate_capture(void);
void reference_capture(void);
int candidate_reuse(const u32 *key);
int reference_reuse(const u32 *key);
void candidate_finish(void);
void reference_finish(void);
void oracle_draw_notices(StripState *state,int cached);
void oracle_draw_reward(StripState *state);
void oracle_copy_previous_bitmap(StripState *state);
void oracle_save_frame(StripState *state);
#endif
