#include <assert.h>
#include <stdio.h>
#include "world.h"

#define KEY_SELECT 4
#define KEY_RIGHT 16
#define KEY_LEFT 32
#define KEY_UP 64
#define KEY_DOWN 128
#define COLD

int px, py, px_q8, py_q8, face, step_cd, invuln, guard_invuln, roll_ticks, roll_cd;
static int solid_calls, mode;

int solid(int x, int y) {
 solid_calls++;
 if (mode == 1)
  return y >= WORLD_RIVER_Y && y < WORLD_RIVER_Y + WORLD_RIVER_H;
 if (mode == 2)
  return x == 56;
 if (mode == 3)
  return x >= 64 && x < 80;
 if (mode == 4)
  return x >= 120 && x < 136;
 return 0;
}

#include "field_step.inc"

static void place(int x, int y) {
 px = x;
 py = y;
 px_q8 = x * 256;
 py_q8 = y * 256;
 solid_calls = 0;
}

static void tick(int n) {
 while (n--) if (step_cd) step_cd--;
}

int main(void) {
 int inv, guard, rolls, cds;
 place(40, 90);
 inv = invuln = 4;
 guard = guard_invuln = 7;
 rolls = roll_ticks = 2;
 cds = roll_cd = 3;
 assert(field_step_try(KEY_SELECT) == 0 && px == 40 && step_cd == 0);
 assert(field_step_try(0) == 0 && px == 40);
 assert(field_step_try(KEY_RIGHT) == 1);
 assert(px == 52 && py == 90 && face == 3 && step_cd == 18);
 assert(solid_calls >= 12);
 assert(invuln == inv && guard_invuln == guard && roll_ticks == rolls && roll_cd == cds);
 assert(field_step_try(KEY_RIGHT) == 0 && px == 52 && step_cd == 18);
 tick(17);
 assert(field_step_try(KEY_RIGHT) == 0 && px == 52 && step_cd == 1);
 tick(1);
 assert(step_cd == 0);
 assert(field_step_try(KEY_UP) == 1 && py == 78 && px == 52 && face == 1);

 place(240, 188);
 mode = 1;
 step_cd = 0;
 assert(field_step_try(KEY_UP) == 1);
 assert(py == 176 && px == 240);
 assert(solid(240, 175) == 1 && solid(240, 176) == 0);

 place(50, 80);
 mode = 2;
 step_cd = 0;
 assert(field_step_try(KEY_RIGHT) == 1);
 assert(px == 55 && py == 80);

 place(52, 80);
 mode = 3;
 step_cd = 0;
 assert(field_step_try(KEY_RIGHT) == 1);
 assert(px == 63 && px < 64);

 place(108, 90);
 mode = 4;
 step_cd = 0;
 invuln = 4;
 guard_invuln = 7;
 roll_ticks = 0;
 roll_cd = 0;
 assert(field_step_try(KEY_RIGHT) == 1);
 assert(px == 119 && px < 120 && py == 90);
 assert(invuln == 4 && guard_invuln == 7 && roll_ticks == 0 && roll_cd == 0);
 assert(field_step_try(KEY_RIGHT) == 0 && px == 119);

 puts("PASS field step distance, per-pixel stop, cooldown, no invulnerability, closed river, thin wall, one-tile wall, locked route");
 return 0;
}
