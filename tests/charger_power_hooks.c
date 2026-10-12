/* Explicit inactive successor backends for this isolated real-cast matrix.
 * The selected chapter's callbacks come from its owning harness. None of these
 * adapters authorizes a world hit or a clearance certificate. Keep production
 * missing-symbol checks strict, including on Mach-O where weak undefined
 * symbols are not ELF-style optional imports. */
#if defined(TEST_POWER_NORTHERN) || defined(TEST_POWER_SOUTHERN)
int magma_power_time;
#endif
#if defined(TEST_POWER_NORTHERN) || defined(TEST_POWER_SOUTHERN) || defined(TEST_POWER_MAGMA)
int underwater_power_time;
#endif
#if defined(TEST_POWER_NORTHERN) || defined(TEST_POWER_SOUTHERN) || defined(TEST_POWER_MAGMA) || defined(TEST_POWER_UNDERWATER)
int return_power_time,horizons_power_time,covenants_power_time;
int return_legacy_box_certificate(int x,int y,int tx,int ty) {
    (void)x;(void)y;(void)tx;(void)ty;return 0;
}
#endif
#define INACTIVE_ACTION(name) \
unsigned name##_game_action_begin(unsigned channel) { (void)channel;return 0; } \
int name##_game_field_target(unsigned i,int *x,int *y,int *r) { \
    (void)i;(void)x;(void)y;(void)r;return 0; } \
int name##_game_field_hit(unsigned i,unsigned command,unsigned caster,unsigned form,unsigned token) { \
    (void)i;(void)command;(void)caster;(void)form;(void)token;return 0; }
#define INACTIVE_SCOPE(name) \
int name##_game_is_room(unsigned area) { (void)area;return 0; } \
void name##_game_revoke_cast(unsigned token) { (void)token; } \
int name##_game_supercover(int x,int y,int tx,int ty) { \
    (void)x;(void)y;(void)tx;(void)ty;return 0; }
#if defined(TEST_POWER_RETURN)
INACTIVE_ACTION(horizons)
INACTIVE_SCOPE(horizons)
INACTIVE_ACTION(covenants)
INACTIVE_SCOPE(covenants)
#endif
#if defined(TEST_POWER_HORIZONS)
INACTIVE_ACTION(return)
INACTIVE_ACTION(covenants)
void covenants_game_revoke_cast(unsigned token) { (void)token; }
int covenants_game_supercover(int x,int y,int tx,int ty) {
    (void)x;(void)y;(void)tx;(void)ty;return 0;
}
#endif
#if defined(TEST_POWER_RETURN) || defined(TEST_POWER_HORIZONS) || defined(TEST_POWER_COVENANTS)
int game_road_box_touched(unsigned area,int x0,int y0,int x1,int y1) {
    (void)area;(void)x0;(void)y0;(void)x1;(void)y1;return 0;
}
#endif
