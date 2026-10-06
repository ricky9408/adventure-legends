#!/usr/bin/env python3
"""Native GBA advanced-command behavior and timing checks.

Consumes a matching immutable ROM/symbol pair and the controller-produced
evolution-report.json. All normal setup is GBA input or restoration of a paired
controller-reached machine-state/SRAM snapshot. This module never writes game
RAM. A source-derived test is not counted as ROM behavior, and synthetic saves,
if supplied for impossible negative combinations, are reported separately.
"""
from __future__ import annotations
import argparse
from collections import Counter
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from evolution_tests import EvolutionRun, PLAY, DIALOG, PAUSE, SAVE_PENDING, ROOT

EVOLVED = (2, 5, 8, 11)
GBA_CYCLES = 280896
GBA_CLOCK = 16777216
EFFECT_LENGTH = {5: 60, 6: 90, 7: 25, 8: 72}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_contract_tests(output):
    """Supplemental C tests, never counted as controller/ROM progression proof.

The real advanced_powers.c is linked unchanged. The selected exact game.c
function bodies are compiled with a small host environment for combinations
which the authored story cannot normally reach (evolved wind and a live first
guardian, or six simultaneous incoming shots). These are host fixtures only.
    """
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    source = (ROOT/'src/game.c').read_text()
    def body(name):
        match = re.search(r'(?:void|int) '+name+r'\([^;{}]*\)\s*\{',source)
        if match is None: raise ValueError('Missing source function '+name)
        start = match.start()
        opening = source.index('{',start); depth = 1; end = opening+1
        while depth:
            if source[end]=='{': depth+=1
            elif source[end]=='}': depth-=1
            end+=1
        return source[start:end]
    shim = r'''
#include <assert.h>
#include <string.h>
#include "advanced_powers.h"
#include "gear_runtime.h"
#include "combat_rules.h"
#include "regional_powers.h"
#include "northern_powers.h"
#include "southern_powers.h"
#include "south_game.h"
#include "magma_powers.h"
#include "magma_game.h"
#include "underwater_powers.h"
#include "underwater_game.h"
#include "progression.h"
#include "ui.h"
#define MAX_ENEMIES 6
#define PLAY 1
#define DEAD 4
#define WORLD_W 480
#define WORLD_H 320
typedef struct{int x,y,hp,flash,kind;} Enemy;
typedef struct{int x,y,dx,dy,life,owner;} Shot;
Enemy enemies[6]; Shot shots[12];
unsigned char ordinary_hostile_shots[12];
static unsigned char vram[16384];
int cx,cy,south_reset_calls,magma_reset_calls,underwater_reset_calls,evolution_cancel_calls;
volatile int px,py,spirit,stone_guard,guard_invuln;
int face,frame,ability_cd,ability_max,power_effect,enemy_windups[6];
int invuln,roll_ticks,game_state,hp,max_hp,deaths,summoned,room;
int boss_armor,boss_flash,boss_x,boss_y,torches,save_calls,dialogue_calls;
int swing,combo_step,swing_damage,hitstop,enemy_clocks[6],enemy_aimx[6],enemy_aimy[6];
int kills,wall_x,wall_y,wall_w,wall_h,sword_connect;
EquipmentStats gear_stats;WeaponAttack weapon_action;
unsigned char enemy_phases[6],enemy_stagger_ticks[6];
int hero_hp_q4;
/* This fixture isolates advanced commands and exact game dispatch. Fractional
 * health, weapon geometry and gear mutation have dedicated actual-C suites. */
void game_enemy_hurt(unsigned i,unsigned base,unsigned bonus,unsigned phase){(void)bonus;(void)phase;enemies[i].hp-=(int)(base/16);}
void game_enemy_stagger(unsigned i,unsigned bonus){(void)i;(void)bonus;}
void game_health_heal(unsigned amount){hp+=(int)(amount/16);hero_hp_q4=hp*16;}
void game_health_hurt(unsigned amount,unsigned phase){(void)phase;hp-=(int)(amount/16);hero_hp_q4=hp*16;}
void game_attacks_reset(void){}
/* Power handlers, shot generations and the shared OBJ lease are real modules.
 * This bounded world has no selected regional caster or Southern/Magma machine. */
CreatureInstance *progression_selected(void){return 0;}
void south_game_reset(void){south_reset_calls++;}
void magma_game_reset(void){magma_reset_calls++;}
void underwater_game_reset(void){underwater_reset_calls++;}
void progression_evolution_cancel(void){evolution_cancel_calls++;}
/* Chapter geometry/tokens are outside this old-command dispatch fixture.
 * Real Magma power handlers must see no target and cannot claim a chapter hit. */
int magma_game_target(int*x,int*y,int*radius){(void)x;(void)y;(void)radius;return 0;}
unsigned magma_game_action_begin(unsigned channel){assert(channel<4);return 0;}
int magma_game_command_hit(int x,int y,unsigned damage,unsigned token){
 (void)x;(void)y;(void)damage;(void)token;return 0;
}
/* New chapter event targets are absent in this old-command source fixture;
 * production Underwater power/reset and shared tile modules still run. */
/* Outside Underwater, its rectangle fast proof declines; point LOS remains authoritative. */
int underwater_game_clear_box(int x0,int y0,int x1,int y1){(void)x0;(void)y0;(void)x1;(void)y1;return 0;}
/* No Underwater room is present; retain the production generic point-LOS path. */
int underwater_game_supercover(int x,int y,int tx,int ty){(void)x;(void)y;(void)tx;(void)ty;return -1;}
int underwater_game_target(int*x,int*y,int*radius){(void)x;(void)y;(void)radius;return 0;}
int underwater_game_field_target(unsigned i,int*x,int*y,int*radius){(void)i;(void)x;(void)y;(void)radius;return 0;}
int underwater_game_field_hit(unsigned i,unsigned command,unsigned caster,unsigned form,unsigned token){(void)i;(void)command;(void)caster;(void)form;(void)token;return 0;}
unsigned underwater_game_action_begin(unsigned channel){assert(channel<4);return 0;}
int underwater_game_command_hit(int x,int y,unsigned damage,unsigned token){(void)x;(void)y;(void)damage;(void)token;return 0;}
unsigned game_companion_phase(void){return CREATURE_FIRE;}
unsigned game_power_cooldown(unsigned base){return base;}
int game_melee_hit(unsigned id,int x,int y,int boss){(void)id;(void)x;(void)y;(void)boss;return sword_connect&&swing==11;}
int scrolling_room(void){return room==1;}
int world_width(void){return room==1?480:240;}
int world_height(void){return room==1?320:160;}
int ab(int x){return x<0?-x:x;}
int sign(int x){return x<0?-1:x>0;}
int near(int a,int b,int c,int d,int r){return ab(a-c)+ab(b-d)<r;}
int solid(int x,int y){return x<0||y<0||x>=world_width()||y>=world_height()||(wall_w&&x>=wall_x&&x<wall_x+wall_w&&y>=wall_y&&y<wall_y+wall_h);}
int boss_active(void){return 1;}
void zero(void*p,unsigned n){memset(p,0,n);}
void impact(int x,int y){(void)x;(void)y;}
void sfx(int x){(void)x;}
void toast(int x){(void)x;}
void save_game(void){save_calls++;}
void dialogue(int a,int b,int c){(void)a;(void)b;(void)c;dialogue_calls++;}
int sword_hits(int x,int y,int r){(void)x;(void)y;(void)r;return sword_connect;}
void progression_encounter(unsigned a,unsigned b){(void)a;(void)b;}
void obj_upload(const unsigned char *pixels,int w,int h,int off){
 assert(pixels&&w>0&&h>0&&w<=32&&h<=32&&off>=0&&off+w*h<=16384);
 memcpy(vram+off,pixels,(size_t)w*h);
}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip){
 (void)x;(void)y;(void)priority;(void)depth;(void)flip;
 assert(w>0&&h>0&&w<=32&&h<=32&&off>=0&&off+w*h<=16384);
}
'''
    shim += '\n'.join(body(n) for n in ('kill_enemy','damage_amount','damage_phase','damage','fire_shot','shot_segment_clear','update_shots','update_enemies'))
    shim += r'''
void source_reset(void){
 memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);
 memset(shot_effects,0,sizeof shot_effects);memset(shot_phases,255,sizeof shot_phases);
 memset(ordinary_hostile_shots,0,sizeof ordinary_hostile_shots);
 memset(enemy_phases,255,sizeof enemy_phases);memset(enemy_stagger_ticks,0,sizeof enemy_stagger_ticks);
 memset(enemy_windups,0,sizeof enemy_windups);
 memset(enemy_clocks,0,sizeof enemy_clocks);
 px=py=100;face=3;frame=0;spirit=0;stone_guard=guard_invuln=0;
 invuln=roll_ticks=deaths=summoned=room=0;game_state=1;hp=max_hp=8;hero_hp_q4=128;gear_stats.max_hp_q4=128;weapon_action.damage_q4=32;weapon_action.attack_q4=0;weapon_action.stagger=0;weapon_action.element=255;
 boss_armor=boss_flash=torches=save_calls=dialogue_calls=0;
 boss_x=boss_y=0;swing=combo_step=swing_damage=hitstop=0;
 kills=wall_x=wall_y=wall_w=wall_h=sword_connect=south_reset_calls=magma_reset_calls=underwater_reset_calls=evolution_cancel_calls=0;
 cx=px;cy=py;ability_cd=ability_max=power_effect=0;
 advanced_reset();regional_powers_reset();northern_powers_reset();southern_powers_reset();magma_powers_reset();underwater_powers_reset();
}
'''
    class Enemy(C.Structure):
        _fields_=[(n,C.c_int) for n in ('x','y','hp','flash','kind')]
    class Shot(C.Structure):
        _fields_=[(n,C.c_int) for n in ('x','y','dx','dy','life','owner')]
    results=[]
    with tempfile.TemporaryDirectory(prefix='advanced-source-contract-') as tmp:
        fixture=Path(tmp)/'fixture.c';fixture.write_text(shim)
        libfile=Path(tmp)/'contract.so'
        subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O2','-Wall','-Wextra',
                        '-Werror','-fPIC','-shared','-I'+str(ROOT/'src'),str(fixture),
                        str(ROOT/'src/advanced_powers.c'),str(ROOT/'src/regional_powers.c'),
                        str(ROOT/'src/northern_powers.c'),str(ROOT/'src/northern_power_art.c'),
                        str(ROOT/'src/southern_powers.c'),str(ROOT/'src/southern_power_art.c'),
                        str(ROOT/'src/magma_powers.c'),str(ROOT/'src/magma_power_art.c'),
                        str(ROOT/'src/underwater_powers.c'),str(ROOT/'src/underwater_power_art.c'),str(ROOT/'src/combat_rules.c'),
                        str(ROOT/'src/creatures.c'),
                        str(ROOT/'src/creature_data.c'),'-o',str(libfile)],check=True)
        lib=C.CDLL(str(libfile));enemies=(Enemy*6).in_dll(lib,'enemies')
        shots=(Shot*12).in_dll(lib,'shots');effects=(C.c_ubyte*12).in_dll(lib,'shot_effects')
        ordinary=(C.c_ubyte*12).in_dll(lib,'ordinary_hostile_shots')
        roots=(C.c_int*6).in_dll(lib,'rooted_enemies')
        def get(n): return C.c_int.in_dll(lib,n).value
        def setv(n,v): C.c_int.in_dll(lib,n).value=v
        def check(label,condition):
            results.append({'check':label,'passed':bool(condition)})
            print(('PASS' if condition else 'FAIL')+' source-contract '+label,flush=True)
        def ticks(n):
            for _ in range(n): lib.advanced_tick()
        for command,cd in ((5,105),(6,120),(7,105),(8,120)):
            lib.source_reset();lib.advanced_power(command)
            check(f'command{command} authored cooldown',get('ability_cd')==cd)
        lib.source_reset()
        for i,x in enumerate((116,130,144)):enemies[i]=Enemy(x,100,6,0,0)
        lib.advanced_power(5);ticks(7)
        check('fire line has seven full delay updates',all(enemies[i].hp==6 for i in range(3)))
        ticks(1);check('first fire cell opens on update8',enemies[0].hp==4 and enemies[1].hp==6)
        ticks(6);check('second fire cell opens on update14',enemies[1].hp==4 and enemies[2].hp==6)
        ticks(6);check('third fire cell opens on update20',enemies[2].hp==4)
        ticks(40);check('each target is hit only once per cast',all(enemies[i].hp==4 for i in range(3)))
        check('per-cast hit mask covers distinct targets',get('advanced_hit_mask')==7)
        lib.advanced_power(5);ticks(60)
        check('next cast can hit the same surviving targets',all(enemies[i].hp==2 for i in range(3)))
        lib.source_reset();setv('wall_x',128);setv('wall_y',90);setv('wall_w',2);setv('wall_h',20)
        enemies[0]=Enemy(144,100,6,0,0);lib.advanced_power(5);ticks(60)
        check('fire cells cannot jump an intervening thin wall',enemies[0].hp==6)
        lib.source_reset();setv('wall_x',128);setv('wall_y',90);setv('wall_w',1);setv('wall_h',20)
        enemies[0]=Enemy(129,100,6,0,0);lib.advanced_power(5);ticks(60)
        check('fire cell hit radius cannot damage through a wall',enemies[0].hp==6)
        lib.source_reset();enemies[0]=Enemy(120,100,6,0,2);enemies[1]=Enemy(147,100,6,0,2)
        lib.advanced_power(6)
        check('roots bind in-range but exclude out-of-range enemies',roots[0]==90 and roots[1]==0)
        pos=enemies[0].x,enemies[0].y
        for _ in range(20):lib.advanced_tick();lib.update_enemies()
        check('rooted enemy neither moves nor begins ranged windup',(enemies[0].x,enemies[0].y)==pos and get('enemy_windups')==0)
        setv('sword_connect',1);setv('swing',11);setv('swing_damage',2);lib.update_enemies()
        check('roots do not make an enemy immune to sword damage',enemies[0].hp==4 and roots[0]>0)
        ticks(70);check('roots expire after90 effect updates',roots[0]==0)
        lib.source_reset();setv('wall_x',110);setv('wall_y',80);setv('wall_w',1);setv('wall_h',40)
        enemies[0]=Enemy(120,100,6,0,2);lib.advanced_power(6)
        check('roots cannot bind a nearby enemy through a wall',roots[0]==0)
        lib.source_reset();shots[0]=Shot(110,100,-2,0,50,1);shots[1]=Shot(112,100,-2,0,50,1)
        lib.advanced_power(6);ticks(1)
        check('canopy shelter consumes exactly one hostile projectile',sum(s.life>0 for s in shots)==1 and get('advanced_shield_left')==0)
        ticks(20);check('spent shelter cannot erase a second projectile',shots[1].life==50)
        lib.source_reset();setv('wall_x',110);setv('wall_y',80);setv('wall_w',1);setv('wall_h',40)
        shots[0]=Shot(120,100,-2,0,50,1);lib.advanced_power(6);ticks(1)
        check('shelter cannot erase a projectile through a wall',shots[0].life==50 and get('advanced_shield_left')==1)
        lib.source_reset()
        for i in range(6):shots[i]=Shot(120+i*3,100,-2,1,50,1)
        shots[6]=Shot(90,100,2,0,50,1);shots[7]=Shot(120,135,-2,0,50,1)
        lib.advanced_power(7)
        check('wind reflects at most three of six eligible shots',sum(s.life>0 and s.owner==0 for s in shots)==3)
        check('reflection reverses velocity and sets non-fire identity',all(shots[i].dx==2 and shots[i].dy==-1 and effects[i]==2 and shots[i].life==70 for i in range(3)))
        check('rear and outside-lane shots stay hostile',shots[6].owner==1 and shots[7].owner==1)
        lib.source_reset();setv('wall_x',110);setv('wall_y',80);setv('wall_w',1);setv('wall_h',40)
        shots[0]=Shot(120,100,-2,0,50,1);lib.advanced_power(7)
        check('wind cannot reflect a projectile through a wall',shots[0].owner==1 and effects[0]==0)
        lib.source_reset();shots[0]=Shot(116,100,2,0,50,0);effects[0]=2
        enemies[0]=Enemy(120,100,6,0,2);enemies[1]=Enemy(120,100,6,0,2);lib.update_enemies()
        check('one reflected shot cannot damage overlapping enemies twice',enemies[0].hp==4 and enemies[1].hp==6 and not shots[0].life)
        ordinary[0]=1;lib.fire_shot(120,100,-2,0,1)
        check('hostile shot slot reuse clears prior wind identity',shots[0].owner==1 and effects[0]==0)
        check('generic hostile shot reuse clears ordinary-enemy eligibility',ordinary[0]==0)
        shots[0].life=0;lib.fire_shot(120,100,2,0,0)
        check('fire shot slot reuse restores explicit fire identity',shots[0].owner==0 and effects[0]==1)
        lib.source_reset();setv('room',2);setv('px',42);setv('py',64)
        shots[0]=Shot(60,64,-2,0,50,1);lib.advanced_power(7);lib.update_shots()
        check('reflected wind crossing temple torch never ignites it',shots[0].owner==0 and effects[0]==2 and get('torches')==0 and get('save_calls')==0)
        lib.source_reset();setv('room',3);setv('px',70);setv('py',65);setv('boss_x',120);setv('boss_y',65)
        shots[0]=Shot(100,65,-2,0,50,1);lib.advanced_power(7);lib.update_shots()
        check('reflected wind reaching live Grove armor never exposes fire armor',shots[0].owner==0 and effects[0]==2 and get('boss_armor')==0)
        # Positive controls prove the negative checks execute the fire branches.
        effects[0]=1;lib.update_shots();check('fire positive control exposes Grove armor',get('boss_armor')==210)
        lib.source_reset();setv('room',2);shots[0]=Shot(60,64,2,0,50,0);effects[0]=1;lib.update_shots()
        check('fire positive control ignites temple torch',get('torches')==1 and get('save_calls')==1)
        lib.source_reset();enemies[0]=Enemy(120,100,6,0,2);lib.update_enemies()
        check('inactive Southern hooks preserve ordinary ranged windup',get('enemy_windups')==30)
        for _ in range(30):lib.update_enemies()
        check('ordinary ranged emission marks only the spawned hostile shot',
              shots[0].owner==1 and shots[0].life==90 and ordinary[0]==1 and sum(ordinary)==1)
        lib.source_reset();lib.regional_power(11)
        check('source fixture links a live regional lease',get('regional_power_time')==36 and lib.northern_powers_tiles_owner()!=0)
        check('absent Magma caster cannot steal live regional lease',not lib.magma_power(43) and
              get('magma_power_time')==0 and get('regional_power_time')==36 and lib.northern_powers_tiles_owner()!=0)
        setv('hp',1);setv('hero_hp_q4',16);lib.damage()
        check('exact death dispatch resets live power lease and Southern chapter bridge',
              get('game_state')==4 and get('deaths')==1 and get('south_reset_calls')==1 and
              get('regional_power_time')==get('northern_power_time')==get('southern_power_time')==0 and
              lib.northern_powers_tiles_owner()==0)
        check('exact death dispatch also resets Magma chapter bridge and power',
              get('magma_reset_calls')==1 and get('magma_power_time')==0)
        check('exact death dispatch resets Underwater and cancels pending evolution',
              get('underwater_reset_calls')==1 and get('underwater_power_time')==0 and get('evolution_cancel_calls')==1)
        lib.source_reset();lib.advanced_power(8);setv('invuln',10);lib.damage()
        check('ordinary invulnerability does not consume guard charges',get('advanced_guard_charges')==2 and get('hp')==8)
        setv('invuln',0);lib.damage()
        check('first guard hit consumes one charge without HP damage',get('advanced_guard_charges')==1 and get('hp')==8 and get('guard_invuln')==24)
        lib.damage();check('guard invulnerability prevents duplicate charge consumption',get('advanced_guard_charges')==1)
        setv('guard_invuln',0);lib.damage()
        check('second guard hit consumes guard without HP damage',not get('advanced_guard_charges') and not get('stone_guard') and get('hp')==8)
        setv('guard_invuln',0);lib.damage();check('third hit after guard and grace deals normal damage',get('hp')==7)
        lib.source_reset();lib.advanced_power(8);setv('stone_guard',0);lib.advanced_tick()
        check('expired guard cannot retain movement penalty charges',not get('advanced_guard_charges'))
        check('Shot ABI stays exactly24bytes with separate12byte metadata',C.sizeof(Shot)==24 and len(effects)==12)
    report={'kind':'supplemental host source-contract tests; synthetic host states',
            'normal_progression_proof':False,'actual_rom_execution':False,
            'source_sha256':{n:sha(ROOT/'src'/n) for n in ('advanced_powers.c','regional_powers.c','northern_powers.c','northern_power_art.c','southern_powers.c','southern_power_art.c','magma_powers.c','magma_power_art.c','magma_powers.h','magma_game.h','underwater_powers.c','underwater_powers.h','underwater_power_art.c','underwater_game.h','combat_rules.c','game.c','creatures.c','creature_data.c')},
            'checks':results,'passed':all(r['passed'] for r in results)}
    (output/'source-contract-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


class AdvancedRun(EvolutionRun):
    def __init__(self, journey, output, snapshot='all-evolved-village', families=(0,1,2,3)):
        self.journey_path = Path(journey).resolve()
        manifest = json.loads(self.journey_path.read_text())
        if not manifest.get('controller_only') or manifest.get('game_ram_writes') != 0:
            raise ValueError('Ordinary ability proof requires a controller-only journey')
        rom, symbols = self.journey_path.parent/'tested.gba', self.journey_path.parent/'tested.sym'
        if sha(rom) != manifest['rom_sha256']:
            raise ValueError('Journey ROM digest mismatch')
        if sha(symbols) != manifest.get('symbol_sha256', manifest.get('symbols_sha256')):
            raise ValueError('Journey symbols digest mismatch')
        self.journey = manifest
        self.fixture = manifest['snapshots'][snapshot]
        self.fixture_name = snapshot
        self.families = tuple(families)
        self.cases, self.timing, self.unavailable = [], [], []
        self.extra_fixtures = {}
        self.current_case = 'initialization'
        self.negative_cases = []
        super().__init__(rom, symbols, output)
        self.aliases.update({
            'advanced_kind': ('advanced_kind', 'kind'),
            'advanced_time_left': ('advanced_time_left', 'time_left'),
            'advanced_origin_x': ('advanced_origin_x', 'origin_x'),
            'advanced_origin_y': ('advanced_origin_y', 'origin_y'),
            'advanced_direction': ('advanced_direction', 'direction'),
            'advanced_hit_mask': ('advanced_hit_mask', 'hit_mask'),
            'advanced_shield_left': ('advanced_shield_left', 'shield_left')})
        for name in ('advanced_kind', 'advanced_time_left', 'advanced_shield_left',
                     'advanced_hit_mask', 'advanced_guard_charges', 'rooted_enemies',
                     'shot_effects', 'render_cycles'):
            if not self.has(name):
                raise ValueError('Missing read-only observation symbol '+name)
        state = Path(self.fixture['path'])
        if not state.is_absolute():
            state = self.journey_path.parent/state
        sram = Path(self.fixture.get('sram_path', str(state)+'.sav'))
        if not sram.is_absolute():
            sram = self.journey_path.parent/sram
        for file, field in ((state, 'state_sha256'), (sram, 'sram_sha256')):
            if field in self.fixture and sha(file) != self.fixture[field]:
                raise ValueError('Journey snapshot digest mismatch: '+str(file))
        self.base = self.out/'authentic-all-evolved.state'
        self.base.write_bytes(state.read_bytes())
        self.base.with_suffix('.state.sav').write_bytes(sram.read_bytes())
        self.expected_rom, self.expected_symbols = sha(self.rom), sha(self.symbol_path)

    def report(self):
        # The inherited constructor does not issue checks before initialization.
        if not hasattr(self, 'expected_rom'):
            return
        if sha(self.rom) != self.expected_rom or sha(self.symbol_path) != self.expected_symbols:
            raise AssertionError('Immutable tested ROM or symbols changed')
        report = {'rom_sha256': self.expected_rom, 'symbol_sha256': self.expected_symbols,
                  'controller_only': True, 'game_ram_writes': 0, 'host_fps_used': False,
                  'gba_clock_hz': GBA_CLOCK, 'hardware_cycles_per_frame': GBA_CYCLES,
                  'native_refresh_hz': GBA_CLOCK/GBA_CYCLES,
                  'source_journey': str(self.journey_path), 'source_snapshot': self.fixture_name,
                  'source_snapshot_sha256': sha(self.base),
                  'source_sram_sha256': sha(self.base.with_suffix('.state.sav')),
                  'extra_controller_fixtures': self.extra_fixtures,
                  'passes': self.passes, 'failures': self.failures, 'cases': self.cases,
                  'timing': self.timing, 'synthetic_negative_cases': self.negative_cases,
                  'unavailable_checks': self.unavailable, 'inputs_file': 'controller-inputs.json',
                  'requested_families': self.families,
                  'complete': set(self.families)=={0,1,2,3} and bool(self.cases) and not self.failures and not self.unavailable,
                  'scope': 'Controller-reached advanced-command samples; timing is actual GBA updates, display-page flips and hardware timer cycles, not host FPS',
                  'cycle_caveat': 'Input/update/render timer excludes VBlank wait and OAM commit; once-per-hardware-frame reads can repeat the last completed timing sample',
                  'current_case': self.current_case, 'final': self.status()}
        (self.out/'advanced-power-report.json').write_text(json.dumps(report, indent=2)+'\n')
        (self.out/'controller-inputs.json').write_text(json.dumps(self.inputs, indent=2)+'\n')

    def attempt(self, name, fn):
        self.current_case = name
        start = len(self.passes)
        try:
            fn()
            self.cases.append({'name': name, 'passed': True, 'checks': len(self.passes)-start})
        except Exception as exc:
            self.failures.append({'case': name, 'error': str(exc), 'status': self.status()})
            self.cases.append({'name': name, 'passed': False})
            self.shot('failure-'+name)
            print('FAIL', name, str(exc), flush=True)
        self.report()

    def reset_case(self, family=0, advanced=True):
        self.restore(self.base)
        self.auto_save = True
        self.settle_save()
        self.check(self.get('room') == 0 and self.get('max_hp') == 8,
                   'authentic controller fixture is the eight-heart village')
        self.check(all(self.instance(i).form_id==EVOLVED[i] for i in self.families),
                   'requested evolved identities come from controller journey')
        if self.get('game_state') == PAUSE:
            self.tap('B')
        self.check(self.get('game_state') == PLAY, 'fixture resumes active gameplay')
        self.goto(144, 126)
        self.select(family)
        self.set_command(advanced)
        self.ready()
        self.step(2)

    def command(self):
        c = self.instance(self.get('spirit'))
        return c.equipped[c.selected_command]

    def journal(self):
        if self.get('game_state') != PAUSE:
            self.tap('START')
        for _ in range(4):
            if self.get('journal_tab') == 3:
                break
            self.tap('A')
        self.check(self.get('game_state') == PAUSE and self.get('journal_tab') == 3,
                   'growth journal reached with controller buttons')

    def set_command(self, advanced):
        expected = self.get('spirit') + (5 if advanced else 1)
        if self.command() != expected:
            self.journal()
            self.tap('R')
            self.check(self.command() == expected, 'growth R selects command '+str(expected))
            self.tap('B')
        return expected

    def enemies(self):
        return [dict(zip(('x','y','hp','flash','kind'),
                        (self.e.read(self.sym['enemies']+i*20+j*4) for j in range(5))))
                for i in range(6)]

    def shots(self):
        rows = []
        for i in range(12):
            row = dict(zip(('x','y','dx','dy','life','owner'),
                           (self.e.read(self.sym['shots']+i*24+j*4) for j in range(6))))
            for n in ('dx','dy'):
                if row[n] & 0x80000000:
                    row[n] -= 0x100000000
            row['effect'] = self.e.read(self.sym['shot_effects']+i, 1)
            row['index'] = i
            rows.append(row)
        return rows

    def roots(self):
        return [self.e.read(self.sym['rooted_enemies']+i*4) for i in range(6)]

    def frozen(self):
        result = {n: self.get(n) for n in ('ability_cd', 'heal_cd', 'stone_guard',
                   'guard_invuln', 'advanced_kind', 'advanced_time_left',
                   'advanced_guard_charges', 'advanced_shield_left', 'advanced_hit_mask')}
        result['roots'] = self.roots()
        result['shots'] = self.shots()
        result['enemies'] = self.enemies()
        return result

    def update_once(self, keys=0):
        before = self.get('frame')
        for _ in range(4):
            self.raw_step(1, keys)
            delta = (self.get('frame')-before)&0xffffffff
            if delta:
                self.check(delta == 1, 'single observed GBA update') if delta != 1 else None
                return
        raise AssertionError('No GBA update in four hardware frames')

    def cast(self):
        self.update_once(0)
        self.update_once('R')
        self.check(self.get('ability_cd') > 0, 'R casts ready summoned command')

    def command_case(self, family):
        self.reset_case(family)
        command = family+5
        # Ability catalog is a ROM-resident 8-byte record, cooldown at +2.
        expected_cd = self.e.read(self.sym['creature_abilities']+(command-1)*8+2,2)
        self.cast()
        self.check(self.get('advanced_kind') == command, 'advanced effect kind is selected command')
        self.check(self.get('ability_cd') == expected_cd == self.get('ability_max'),
                   f'command {command} cooldown agrees with ROM ability catalog')
        self.check(self.get('advanced_time_left') == EFFECT_LENGTH[command],
                   f'command {command} begins with authored effect duration')
        origin = (self.get('advanced_origin_x'), self.get('advanced_origin_y'))
        trace = []
        for age in range(1, expected_cd+1):
            self.update_once('R' if age%10 == 0 and age < expected_cd else 0)
            trace.append((age, self.get('ability_cd'), self.get('advanced_time_left')))
            if self.get('ability_cd') != expected_cd-age:
                raise AssertionError('Repeated R changed shared cooldown: '+str(trace[-5:]))
            if self.get('advanced_time_left') != max(0,EFFECT_LENGTH[command]-age):
                raise AssertionError('Wrong effect duration: '+str(trace[-5:]))
        self.check(True, f'command {command} duration and repeat lockout are exact update counts')
        self.check(origin == (self.get('advanced_origin_x'), self.get('advanced_origin_y')),
                   'stationary cast origin remains stable')
        self.set_command(False)
        self.ready(); self.cast()
        self.check(self.get('ability_cd') == 75, 'retained base command keeps its 75-update cooldown')
        if family == 0:
            self.check(any(s['life'] and s['effect']==1 and not s['owner'] for s in self.shots()),
                       'retained fire command still produces a fire dart')
        if family == 3:
            self.check(self.get('stone_guard') == 36 and not self.get('advanced_guard_charges'),
                       'retained stone command keeps its one-hit 36-update guard')
        if family == 2:
            self.check(self.get('power_effect') == 14, 'retained wind command still has original 14-update effect')

    def freeze_case(self, family):
        self.reset_case(family)
        self.cast(); self.update_once(0)
        self.update_once('START')
        self.check(self.get('game_state') == PAUSE, 'pause interrupts active advanced effect')
        before = self.frozen()
        self.step(90)
        self.check(self.frozen() == before, 'pause freezes effects, roots, shots and combat timers')
        self.journal()
        before = self.frozen()
        self.auto_save = False
        self.update_once(0); self.update_once('R')
        self.check(self.get('game_state') == SAVE_PENDING, 'command switch enters transactional save')
        save_frames = 0
        while self.get('game_state') == SAVE_PENDING and save_frames < 180:
            self.raw_step(1,'A+LEFT+R+SELECT')
            self.check(self.frozen() == before, 'save frame freezes advanced combat state')
            save_frames += 1
        self.check(save_frames > 0 and self.get('game_state') == PAUSE,
                   'save finishes and returns to growth journal')
        self.auto_save = True
        self.step(2); self.tap('B')
        # A fresh branch puts an active effect beside the elder's real dialogue.
        self.reset_case(family)
        self.goto(120,119)
        self.cast(); self.update_once(0); self.update_once('A')
        self.settle_save()
        self.check(self.get('game_state') == DIALOG, 'elder interaction opens real save/dialogue')
        before = self.frozen()
        self.step(90,'LEFT+R')
        self.check(self.frozen() == before, 'dialogue freezes advanced combat state')

    def recall_switch_case(self, family):
        self.reset_case(family)
        self.cast(); self.update_once(0)
        cd = self.get('ability_cd')
        self.update_once('B')
        self.check(not self.get('summoned') and self.get('ability_cd') == cd-1,
                   'recall retains the shared cooldown')
        before = self.get('ability_cd')
        self.update_once('R')
        self.check(self.get('ability_cd') == before-1, 'unsummoned R cannot recast')
        before = self.get('ability_cd'); effect = self.frozen()
        self.update_once('L')
        self.check(self.get('quickparty_open') and self.get('spirit') == family
                   and self.frozen() == effect,
                   'held L previews without selecting and freezes cooldown and active effects')
        self.update_once(0)
        self.check(self.get('spirit') == (family+1)%4 and self.get('ability_cd') == before
                   and self.frozen() == effect,
                   'release commits one short-tap switch without resetting or advancing cooldown/effects')
        self.update_once('B'); self.update_once(0)
        before = self.get('ability_cd')
        self.update_once('R')
        self.check(self.get('ability_cd') == before-1, 'new companion cannot bypass shared cooldown')
        self.check(self.get('advanced_kind') == family+5,
                   'cast effect retains original identity after recall/switch')
        self.check(self.get('advanced_time_left') == EFFECT_LENGTH[family+5]-6,
                   'cast effect continues its original duration across recall and switch, excluding two frozen picker updates')

    def guard_speed_case(self):
        self.reset_case(3)
        self.goto(144,125)
        baseline = self.snapshot('guard-speed-baseline')
        start = self.get('px_q8')
        for _ in range(20): self.update_once('RIGHT')
        ordinary = self.get('px_q8')-start
        self.restore(baseline)
        self.cast(); start = self.get('px_q8')
        for _ in range(20): self.update_once('RIGHT')
        guarded = self.get('px_q8')-start
        self.check(ordinary == 20*320 and guarded == 20*224,
                   'advanced guard moves at 224/256 pixels per update versus normal 320/256')
        self.check(self.get('advanced_guard_charges') == 2, 'untouched guard retains two charges')
        self.update_once('SELECT')
        self.check(self.get('roll_ticks') > 0 and not self.get('stone_guard')
                   and not self.get('advanced_guard_charges'), 'dodge cancels advanced guard and both charges')

    def enter_grove(self):
        self.goto(120,48)
        for _ in range(60):
            if self.get('room') == 1: break
            self.step(1,'UP')
        self.settle_save()
        self.check(self.get('room') == 1, 'controller walks from village into grove')
        self.step(2)

    def room_reset_case(self, family):
        self.reset_case(family)
        self.goto(120,33)
        self.ready(); self.cast()
        for _ in range(20):
            if self.get('room') == 1: break
            self.step(1,'UP')
        self.settle_save()
        self.check(self.get('room') == 1, 'active effect crosses real room transition')
        self.check(not self.get('advanced_time_left') and not self.get('advanced_guard_charges')
                   and not self.get('stone_guard') and not any(self.roots()),
                   'room transition clears roots and all transient advanced effects')
        self.check(not any(s['life'] for s in self.shots()), 'room transition clears projectiles')

    def grove_combat_setup(self, family, x, y, facing='RIGHT'):
        self.reset_case(family)
        self.enter_grove()
        self.navigate(x,y,radius=3)
        self.ready()
        self.update_once(facing);self.update_once(0)

    def fire_enemy_case(self):
        self.grove_combat_setup(0,282,238)
        target=1
        enemy=self.enemies()[target]
        self.check(enemy['hp']==4 and enemy['kind']==2,'fire test uses living authentic grove ranger')
        self.cast()
        before=enemy['hp'];first_hit=None;trace=[]
        for age in range(1,61):
            self.update_once(0)
            health=self.enemies()[target]['hp']
            trace.append({'age':age,'hp':health,'hit_mask':self.get('advanced_hit_mask')})
            if health<before and first_hit is None:first_hit=age
        self.check(first_hit is not None and first_hit>=8,'real fire-line enemy damage begins only after delayed cells open')
        self.check(self.enemies()[target]['hp']==before-2 and self.get('advanced_hit_mask')&(1<<target),
                   'real ranger receives exactly one two-damage hit across entire fire cast')
        (self.out/'fire-enemy-frames.json').write_text(json.dumps(trace,indent=2)+'\n')
        self.ready();self.cast()
        for _ in range(60):self.update_once(0)
        self.check(self.enemies()[target]['hp']==0,'second real fire cast may hit and defeat same ranger')

    def nature_enemy_case(self):
        self.grove_combat_setup(1,303,238)
        target=1;enemy=self.enemies()[target]
        self.check(enemy['hp']==4,'root test uses living authentic grove ranger')
        self.cast()
        self.check(self.roots()[target]==90,'real nature cast binds nearby ranger for90 updates')
        position=self.enemies()[target]['x'],self.enemies()[target]['y']
        shots_before=sum(s['life']>0 and s['owner'] for s in self.shots())
        for _ in range(20):self.update_once(0)
        self.check((self.enemies()[target]['x'],self.enemies()[target]['y'])==position,
                   'rooted real ranger stays in place')
        self.check(self.e.read(self.sym['enemy_windups']+target*4)==0,
                   'rooted real ranger cannot start another ranged windup')
        before=self.enemies()[target]['hp'];self.update_once('A')
        hitstop_seen=False;frozen_checks=0
        for _ in range(12):
            old_hitstop=self.get('hitstop');old_roots=self.roots();old_time=self.get('advanced_time_left')
            self.update_once(0)
            if old_hitstop:
                hitstop_seen=True;frozen_checks+=1
                self.check(self.roots()==old_roots and self.get('advanced_time_left')==old_time,
                           'real sword hit-stop freezes root and effect timers')
        self.check(self.enemies()[target]['hp']<before and self.roots()[target]>0,
                   'real rooted ranger remains damageable by sword')
        self.check(hitstop_seen and frozen_checks>=1,'real rooted sword hit exercises hit-stop freezing')

    def reflection_enemy_case(self):
        self.grove_combat_setup(2,274,238)
        candidate=None
        for _ in range(180):
            enemyshots=[s for s in self.shots() if s['life'] and s['owner']
                        and 18<=s['x']-self.get('px')<=70 and abs(s['y']-self.get('py'))<=20]
            if enemyshots:
                candidate=enemyshots[0];break
            self.update_once(0)
        self.check(candidate is not None,'real ranger launches an incoming projectile in wind lane')
        incoming=self.snapshot('authentic-incoming-wind-shot')
        before=self.enemies()[1]['hp']
        self.cast()
        reflected=self.shots()[candidate['index']]
        self.check(not reflected['owner'] and reflected['effect']==2
                   and reflected['dx']==-candidate['dx'] and reflected['dy']==-candidate['dy'],
                   'real wind cast reverses hostile shot as explicitly non-fire friendly projectile')
        playerhp=self.get('hp')
        for _ in range(60):self.update_once(0)
        self.check(self.enemies()[1]['hp']==before-2,
                   'actual reflected shot damages its ranger once for two HP')
        self.restore(incoming)
        self.set_command(False)
        self.cast()
        self.check(not self.shots()[candidate['index']]['life'],
                   'retained base wind still clears incoming hostile projectile')
        self.check(not any(s['life'] and not s['owner'] and s['effect']==2 for s in self.shots()),
                   'retained base wind does not acquire evolved reflection behavior')

    def canopy_projectile_case(self):
        self.grove_combat_setup(1,266,238)
        candidate=None
        for _ in range(180):
            candidates=[s for s in self.shots() if s['life'] and s['owner']
                        and 20<=abs(s['x']-self.get('px'))+abs(s['y']-self.get('py'))<28]
            if candidates:candidate=candidates[0];break
            self.update_once(0)
        self.check(candidate is not None,'real ranger shot approaches nature shelter location')
        self.cast();hp=self.get('hp')
        self.update_once(0)
        self.check(not self.shots()[candidate['index']]['life'] and not self.get('advanced_shield_left'),
                   'real canopy shelter consumes the approaching hostile projectile')
        self.check(self.get('hp')==hp,'canopy intercept prevents projectile damage')

    def guard_enemy_case(self):
        self.grove_combat_setup(3,310,238)
        # Enter contact while invulnerability from arrival has fully expired.
        for _ in range(95):self.update_once(0)
        for _ in range(120):
            if not self.get('invuln'):break
            self.update_once(0)
        self.check(not self.get('invuln'),'guard contact setup reaches a non-invulnerable moment outside contact')
        self.cast();hp=self.get('hp')
        states=[]
        for _ in range(68):
            states.append((self.get('hp'),self.get('stone_guard'),self.get('advanced_guard_charges'),self.get('guard_invuln')))
            self.update_once('RIGHT' if self.get('px')<321 else 0)
        self.check(any(s[2]==1 and s[3]>0 and s[0]==hp for s in states),
                   'actual contact consumes first guard charge with grace and no HP damage')
        self.check(any(s[2]==0 and s[3]>0 and s[0]==hp for s in states),
                   'actual second contact consumes remaining charge with grace and no HP damage')
        self.check(any(s[0]<hp for s in states),'actual contact after both guard charges and grace damages player')
        (self.out/'guard-contact-updates.json').write_text(json.dumps(states,indent=2)+'\n')

    def stress_case(self, family):
        self.reset_case(family)
        self.enter_grove()
        self.navigate(240,238)
        self.ready()
        expected_room, expected_hp = self.get('room'), self.get('max_hp')
        last, page = self.get('frame'), self.e.read(0x04000000,2)&16
        rows, effects = [], 0
        for n in range(240):
            keys = 'R' if n%125==0 else 0
            self.raw_step(1,keys)
            now, newpage = self.get('frame'), self.e.read(0x04000000,2)&16
            active = bool(self.get('advanced_time_left'))
            effects += active
            rows.append({'frame':n,'update_delta':(now-last)&0xffffffff,
                         'page_flip':newpage!=page,'cycles':self.get('render_cycles'),
                         'effect_active':active,'hp':self.get('hp'),
                         'shots':sum(bool(s['life']) for s in self.shots())})
            last,page=now,newpage
            if self.get('room')!=expected_room or self.get('game_state')!=PLAY or self.get('hp')<=0:
                raise AssertionError('Stress window left expected active room or player died')
        peak=max(r['cycles'] for r in rows)
        result={'family':family,'hardware_frames':len(rows),'max_hp':expected_hp,
                'effect_active_frames':effects,'updates':sum(r['update_delta'] for r in rows),
                'page_flips':sum(r['page_flip'] for r in rows),'peak_cycles':peak,
                'peak_frame_budget_fraction':peak/GBA_CYCLES,
                'strict_60hz':all(r['update_delta']==1 and r['page_flip'] for r in rows) and peak<=GBA_CYCLES,
                'trace':f'stress-{family}-frames.json'}
        (self.out/result['trace']).write_text(json.dumps(rows,indent=2)+'\n')
        self.timing.append(result)
        self.check(expected_hp == 8 and effects > 20, 'stress window includes eight-heart HUD and active evolved effects')
        self.check(result['strict_60hz'], 'actual GBA window sustains one update/page flip per frame within 280896 cycles')

    def boss_stress_case(self, family, phase):
        name=f'boss-13-phase-{phase}-state-0'
        fixture=self.journey['snapshots'][name]
        source=Path(fixture['path'])
        if not source.is_absolute():source=self.journey_path.parent/source
        sram=Path(fixture.get('sram_path',str(source)+'.sav'))
        if not sram.is_absolute():sram=self.journey_path.parent/sram
        for path,field in ((source,'state_sha256'),(sram,'sram_sha256')):
            if field in fixture and sha(path)!=fixture[field]:raise AssertionError('Extra controller fixture hash mismatch')
        local=self.out/(name+'.state');local.write_bytes(source.read_bytes())
        local.with_suffix('.state.sav').write_bytes(sram.read_bytes())
        self.extra_fixtures[name]={'state_sha256':sha(local),'sram_sha256':sha(local.with_suffix('.state.sav')),
                                   'source_manifest':str(self.journey_path),'provenance':'authentic controller-reached final-boss phase'}
        self.restore(local);self.auto_save=True;self.settle_save()
        self.check(self.get('room')==13 and self.get('boss_phase')==phase and self.get('max_hp')==8,
                   'heavy scene uses authentic eight-heart final-boss phase')
        self.select(family);self.set_command(True);self.ready()
        self.check(self.instance(family).form_id==EVOLVED[family],
                   'heavy scene evolved form was already earned before final boss')
        last,page=self.get('frame'),self.e.read(0x04000000,2)&16
        rows=[]
        for n in range(240):
            keys=('LEFT' if (n//24)%2==0 else 'RIGHT')+('+R' if n%125==0 else '')
            self.raw_step(1,keys)
            now,newpage=self.get('frame'),self.e.read(0x04000000,2)&16
            rows.append({'frame':n,'update_delta':(now-last)&0xffffffff,'page_flip':newpage!=page,
                         'cycles':self.get('render_cycles'),'effect_active':bool(self.get('advanced_time_left')),
                         'hp':self.get('hp'),'shots':sum(bool(s['life']) for s in self.shots()),
                         'hazard':self.get('hazard_mode'),'boss_state':self.get('boss_state')})
            last,page=now,newpage
            if self.get('room')!=13 or self.get('boss_phase')!=phase or self.get('game_state')!=PLAY or self.get('hp')<=0:
                raise AssertionError('Heavy stress scene changed phase/room or player died')
        peak=max(r['cycles'] for r in rows)
        result={'family':family,'room':13,'boss_phase':phase,'hardware_frames':len(rows),'max_hp':8,
                'effect_active_frames':sum(r['effect_active'] for r in rows),
                'peak_live_projectiles':max(r['shots'] for r in rows),
                'observed_hazards':sorted(set(r['hazard'] for r in rows)),
                'updates':sum(r['update_delta'] for r in rows),'page_flips':sum(r['page_flip'] for r in rows),
                'peak_cycles':peak,'peak_frame_budget_fraction':peak/GBA_CYCLES,
                'strict_60hz':all(r['update_delta']==1 and r['page_flip'] for r in rows) and peak<=GBA_CYCLES,
                'trace':f'boss-phase{phase}-power{family}-frames.json'}
        (self.out/result['trace']).write_text(json.dumps(rows,indent=2)+'\n');self.timing.append(result)
        self.check(result['effect_active_frames']>10,'heavy final-boss stress includes active evolved effect')
        self.check(result['strict_60hz'],'heavy actual GBA window sustains240updates/flips within frame-cycle budget')

    def run(self):
        for family in self.families:
            for label,fn in [('command',self.command_case),('freeze',self.freeze_case),
                             ('recall-switch',self.recall_switch_case),('room-reset',self.room_reset_case),
                             ('stress',self.stress_case)]:
                self.attempt(f'{label}-{family}', lambda f=family,fn=fn:fn(f))
        if 3 in self.families:self.attempt('guard-speed-dodge',self.guard_speed_case)
        for family,label,fn in [(0,'fire-real-enemy',self.fire_enemy_case),
                                (1,'nature-real-enemy',self.nature_enemy_case),
                                (2,'wind-real-projectile',self.reflection_enemy_case),
                                (1,'canopy-real-projectile',self.canopy_projectile_case),
                                (3,'guard-real-contact',self.guard_enemy_case)]:
            if family in self.families:self.attempt(label,fn)
        if set(self.families)=={0,1,2,3}:
            for phase in (1,2):
                for family in (0,1,2):
                    self.attempt(f'boss-phase{phase}-stress-{family}',lambda f=family,p=phase:self.boss_stress_case(f,p))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journey',type=Path)
    parser.add_argument('--snapshot',default='all-evolved-village')
    parser.add_argument('--families',default='0,1,2,3',help='Comma-separated families for explicitly partial development smoke checks')
    parser.add_argument('--output',type=Path,default=ROOT/'build/advanced-power-qa')
    parser.add_argument('--source-contracts',action='store_true',help='Run supplemental unchanged-C host fixtures, not ROM/progression proof')
    args=parser.parse_args()
    source_result=source_contract_tests(args.output) if args.source_contracts else None
    if not args.journey:
        if source_result is None:parser.error('--journey or --source-contracts is required')
        return int(not source_result['passed'])
    families=tuple(int(f) for f in args.families.split(','))
    if not families or any(f not in range(4) for f in families):parser.error('families must be0..3')
    run=AdvancedRun(args.journey,args.output,args.snapshot,families)
    try:
        run.run()
    finally:
        run.report();run.e.close()
    return int(bool(run.failures) or bool(run.unavailable) or (source_result is not None and not source_result['passed']))


if __name__=='__main__':
    raise SystemExit(main())
