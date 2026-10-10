#ifndef EMBERBOND_COLLISION_RECTS_H
#define EMBERBOND_COLLISION_RECTS_H
/* Supported rooms:0..45,54..61 and70..77 (when that backend is linked). Every query endpoint must fit signed short;
 * capacity must be1..256 and output must be non-null.
 * Inclusive query and output endpoints. Nonnegative count describes the exact
 * occupied union inside the query. -1 (unsupported, invalid or overflow) grants
 * no shortcut; discard partial output. The caller owns storage and must bind
 * a cached result to room and the engine's dynamic collision generation. */
int game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap);
#endif
