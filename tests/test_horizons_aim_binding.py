#!/usr/bin/env python3
"""Real power pixels plus world gates; host regression, not a native route."""
from pathlib import Path
import ctypes as C
import os
import subprocess
import tempfile
import unittest

import test_horizons_world as world

ROOT = Path(__file__).resolve().parents[1]
SHIM = r'''
#include "gear_runtime.h"
#include "northern_powers.h"
#include "return_powers.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
Enemy enemies[6]; Shot shots[12]; EquipmentStats gear_stats;
int ability_cd,ability_max,hitstop;
int enemy_hp_q4[6],enemy_windups[6],enemy_clocks[6],enemy_aimx[6],enemy_aimy[6];
unsigned char slowed_enemies[6],enemy_phases[6],enemy_stagger_ticks[6];
static unsigned review_owner,review_generation,review_overlap;
int northern_powers_tiles_claim(unsigned o){if(review_owner)return 0;review_owner=o;++review_generation;return 1;}
int northern_powers_tiles_release(unsigned o){if(review_owner!=o)return 0;review_owner=0;++review_generation;return 1;}
unsigned northern_powers_tiles_owner(void){return review_owner;}
unsigned northern_powers_tiles_generation(void){return review_generation;}
int solid(int x,int y){return horizons_game_solid(x,y);}
/* Real new-world geometry is exercised; unrelated legacy certificates are unsupported. */
int game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap){(void)x0;(void)y0;(void)x1;(void)y1;(void)out;(void)cap;return -1;}
int underwater_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
int game_clear_box(int x0,int y0,int x1,int y1){return horizons_game_clear_box(x0,y0,x1,y1);}
void game_enemy_hurt(unsigned i,unsigned d,unsigned a,unsigned p){(void)i;(void)d;(void)a;(void)p;}
unsigned game_power_cooldown(unsigned n){return n;}
void kill_enemy(Enemy*e){e->hp=0;}
void impact(int x,int y){(void)x;(void)y;}
void sfx(int x){(void)x;}
void obj_upload(const unsigned char*p,int w,int h,int o){(void)p;(void)w;(void)h;(void)o;}
void obj_add(int o,int x,int y,int w,int h,int p,int d,int f){(void)o;(void)x;(void)y;(void)w;(void)h;(void)p;(void)d;(void)f;}
int return_game_clear_box(int x0,int y0,int x1,int y1){(void)x0;(void)y0;(void)x1;(void)y1;return 0;}
int return_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return 0;}
unsigned return_game_action_begin(unsigned c){(void)c;return 0;}
int return_game_field_target(unsigned i,int*x,int*y,int*r){(void)i;(void)x;(void)y;(void)r;return 0;}
int return_game_field_hit(unsigned i,unsigned c,unsigned id,unsigned f,unsigned t){(void)i;(void)c;(void)id;(void)f;(void)t;return 0;}
void review_reset_power(void){horizons_powers_reset();return_powers_reset();ability_cd=hitstop=0;review_overlap=0;}
int review_begin(unsigned command,unsigned direction,unsigned aim){int result;face=(int)direction;review_overlap=0;
 result=command>=106?horizons_power(command):return_power(command);if(!result)return 0;
 if(aim&&!(command>=106?horizons_powers_input(aim):return_powers_input(aim)))return -1;
 return 1;
}
void review_ticks(unsigned n,unsigned target){while(n--){int x,y,r;
 if(horizons_power_time)horizons_powers_tick();if(return_power_time)return_powers_tick();
 if(horizons_game_field_target(target,&x,&y,&r)&&
  (horizons_powers_overlap(x,y,r)||return_powers_overlap(x,y,r)))review_overlap=1;
}}
unsigned review_seen_overlap(void){return review_overlap;}
unsigned review_effect_direction(void){return horizons_power_time?(unsigned)horizons_power_direction:(unsigned)return_power_direction;}
'''


class AimBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='horizons-aim-binding-')
        cls.addClassCleanup(cls.tmp.cleanup)
        folder = Path(cls.tmp.name)
        source = (ROOT / 'tests/horizons_world_host.c').read_text()
        # Keep real world, quests, collision, and persistence. Replace only the
        # old tagged-callback power mocks with the two actual power modules.
        prefixes = (
            'int horizons_power_kind,',
            'int return_power_kind,',
            'void return_powers_geometry_changed(',
            'void horizons_powers_geometry_changed(',
            'unsigned horizons_powers_beat(',
            'unsigned horizons_powers_release_phase(',
            'int horizons_powers_busy(',
            'unsigned horizons_powers_cast_token(',
            'unsigned horizons_powers_caster_id(',
            'int return_powers_busy(',
            'unsigned return_powers_cast_token(',
            'unsigned return_powers_caster_id(',
        )
        source = '\n'.join(line for line in source.splitlines()
                           if not line.startswith(prefixes))
        selected_root = Path(os.environ.get('HORIZONS_AIM_WORLD_ROOT', ROOT / 'src'))
        source = source.replace('#include "../src/horizons_game.c"',
                                '#include "' + str(selected_root / 'horizons_game.c') + '"')
        harness = folder / 'host.c'
        harness.write_text(source + '\n' + SHIM)
        sources = ['horizons_art', 'horizons_creature_art', 'horizons_quests',
                   'save4', 'save5', 'creatures', 'creature_data', 'equipment',
                   'equipment_data', 'progression_events', 'horizons_powers',
                   'horizons_power_art', 'return_powers', 'return_power_art',
                   'north_art', 'south_art']
        output = folder / 'host.so'
        subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-Wno-misleading-indentation', '-fPIC', '-shared',
                        '-DSAVE4_HOST_TEST', '-DSAVE5_HOST_TEST', '-Isrc',
                        str(harness), *['src/' + s + '.c' for s in sources],
                        '-o', str(output)], cwd=ROOT, check=True)
        cls.lib = C.CDLL(str(output))

    def setUp(self):
        self.h = world.World()
        self.h.l = self.lib
        self.h.sram = (C.c_ubyte * 32768).in_dll(self.lib, 'save5_test_sram')
        self.h.s = world.Save.in_dll(self.lib, 'adventure_save')
        self.lib.review_reset_power()
        self.h.setUp()
        self.h.intro()

    def yard(self):
        self.h.entry(63)
        self.h.act(136, 80)
        self.h.act(80, 96)
        self.h.select(105, 106)
        self.h.at(224, 90, 1)

    def test_early_facing_change_authorizes_visible_horizontal_pull(self):
        self.yard()
        self.assertEqual(self.lib.review_begin(106, 1, 32), 1)
        self.assertEqual(self.lib.review_effect_direction(), 2)
        self.lib.review_ticks(24, 0)
        self.assertEqual(self.lib.get_setting(3), 1,
                         'A real left-facing hem must start the cleared cargo step')

    def test_player_facing_after_startup_cannot_redirect_cast_gate(self):
        self.yard()
        self.assertEqual(self.lib.review_begin(106, 2, 0), 1)
        C.c_int.in_dll(self.lib, 'face').value = 1
        self.lib.review_ticks(24, 0)
        self.assertEqual(self.lib.get_setting(3), 1)

    def test_real_pin_keeps_return_side_aim_semantics(self):
        self.h.entry(63)
        self.h.entry(64)
        self.h.select(101, 102)
        self.h.at(208, 120, 1)
        self.assertEqual(self.lib.review_begin(102, 1, 16), 1)
        self.assertEqual(self.lib.review_effect_direction(), 1)
        C.c_int.in_dll(self.lib, 'face').value = 3
        self.lib.review_ticks(24, 3)
        self.assertEqual(self.lib.get_setting(1), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
