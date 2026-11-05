#!/usr/bin/env python3
"""Compile the actual ability_apply body with controlled module outcomes."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'src/game.c').read_text(encoding='utf-8')
match = re.search(r'COLD void ability_apply\(void\)\s*\{', source)
assert match, 'Missing production ability dispatcher'
start = match.start()
depth = 0
for end in range(source.index('{', start), len(source)):
    if source[end] == '{':
        depth += 1
    elif source[end] == '}':
        depth -= 1
        if depth == 0:
            break
else:
    raise AssertionError('Unterminated production ability dispatcher')

fixture = r'''
#include <assert.h>
#include <stdio.h>
#include "power_failure.h"
#define COLD
#define MAX_ENEMIES 6
#define PLAY 1
#define WORLD_BRIDGE_CENTER_X 120
#define WORLD_BRIDGE_Y 120
typedef struct {int hp,flash,x,y;} Enemy;
typedef struct {int max_hp_q4;} GearStats;
typedef struct {unsigned cooldown_updates;} Ability;
Enemy enemies[MAX_ENEMIES];GearStats gear_stats;
int summoned,ability_cd,ability_max,power_effect,covenants_cooldown_owned;
int legacy_ability_success,legacy_ability_shot,room,px,py,cx,cy,face;
int spirit,bridge_open,torches,heal_cd,hero_hp_q4,boss_x,boss_y,boss_armor,boss_flash;
static unsigned selected,reason;static int last_toast,casts_north,casts_south,succeed;
unsigned progression_command(void){return selected;}
void game_geometry_sync(void){}
void toast(int id){last_toast=id;}
int magma_powers_can_aim(void){return 0;}
int magma_powers_aim(void){return 0;}
int southern_powers_can_aim(void){return 0;}
int southern_powers_aim(void){return 0;}
int covenants_game_power(unsigned c){(void)c;return 0;}
int magma_game_power(unsigned c){(void)c;return 0;}
unsigned game_power_cooldown(unsigned n){return n;}
int magma_powers_feedback(unsigned c){(void)c;return 0;}
int southern_powers_feedback(unsigned c){(void)c;return 0;}
int northern_powers_feedback(unsigned c){(void)c;return 0;}
void sfx(int n){(void)n;}
int covenants_power(unsigned c){(void)c;return 0;}
int horizons_power(unsigned c){(void)c;return 0;}
int return_power(unsigned c){(void)c;return 0;}
int underwater_power(unsigned c){(void)c;return 0;}
int magma_power(unsigned c){(void)c;return 0;}
int south_game_power(unsigned c){(void)c;return 0;}
int southern_power(unsigned c){(void)c;casts_south++;return succeed;}
enum PowerFailure southern_power_failure(void){return (enum PowerFailure)reason;}
int north_game_power(unsigned c){(void)c;return 0;}
const Ability *creatures_ability(unsigned c){static const Ability a={90};(void)c;return &a;}
int northern_power(unsigned c){(void)c;casts_north++;return succeed;}
enum PowerFailure northern_power_failure(void){return (enum PowerFailure)reason;}
int region_game_power(unsigned c){(void)c;return 0;}
int trial_event(int e){(void)e;return 0;}
int trials_power(int r,int x,int y,int s){(void)r;(void)x;(void)y;(void)s;return 0;}
int campaign_power(void){return 0;}
int regional_power(unsigned c){(void)c;return 0;}
int advanced_power(unsigned c){(void)c;return 0;}
void game_health_heal(unsigned n){(void)n;}
int near(int x,int y,int tx,int ty,int r){(void)x;(void)y;(void)tx;(void)ty;(void)r;return 0;}
void save_game(void){}
void spawn_forest_rangers(void){}
void dialogue(int a,int b,int c){(void)a;(void)b;(void)c;}
int boss_active(void){return 0;}
int fire_shot(int x,int y,int dx,int dy,int owner){(void)x;(void)y;(void)dx;(void)dy;(void)owner;return -1;}
int sign(int x){return (x>0)-(x<0);}
'''
fixture += source[start:end + 1] + r'''
static void reset(unsigned command,enum PowerFailure why){
    selected=command;reason=(unsigned)why;summoned=1;ability_cd=0;
    last_toast=-1;casts_north=casts_south=succeed=0;
}
int main(void){
    reset(15,POWER_FAILURE_BLOCKED);ability_apply();
    assert(casts_north==1&&last_toast==TX_MG_BLOCKED&&!ability_cd);
    reset(15,POWER_FAILURE_MISMATCH);ability_apply();
    assert(casts_north==1&&last_toast==TX_C_POWER_MISMATCH&&!ability_cd);
    reset(24,POWER_FAILURE_BLOCKED);ability_apply();
    assert(casts_south==1&&last_toast==TX_MG_BLOCKED&&!ability_cd);
    reset(24,POWER_FAILURE_AIM);ability_apply();
    assert(casts_south==1&&last_toast==TX_SP_AIM_CLEAR&&!ability_cd);
    reset(15,POWER_FAILURE_WAIT);ability_cd=5;ability_apply();
    assert(!casts_north&&last_toast==TX_COOLDOWN&&ability_cd==5);
    reset(15,POWER_FAILURE_NONE);succeed=1;ability_apply();
    assert(casts_north==1&&last_toast==-1);
    puts("PASS production ability_apply feedback dispatch");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='power-feedback-dispatch-') as temporary:
    path = Path(temporary)
    (path / 'fixture.c').write_text(fixture, encoding='utf-8')
    subprocess.run(['cc', '-std=c99', '-O1', '-Wall', '-Wextra', '-Werror',
                    '-Wno-misleading-indentation', '-pedantic', '-Isrc',
                    str(path / 'fixture.c'), '-o', str(path / 'fixture')], cwd=ROOT, check=True)
    subprocess.run([str(path / 'fixture')], cwd=ROOT, check=True)
