#!/usr/bin/env python3
"""Actual engine preview-cancel helper with real power modules; host fixtures only.

Each chapter retains its existing catalog, damage and field fixture. This is
synthetic integration evidence, not controller acquisition or GBA timing.
"""
from pathlib import Path
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build' / 'field-preview-cancel-host'
CASES = (
    ('magma', 'test_magma_powers.py', 'magma_powers_native.c', 43, 66, 51),
    ('underwater', 'test_underwater_powers.py', 'underwater_powers_native.c', 67, 90, 68),
    ('return', 'test_return_powers.py', 'return_powers_host.c', 91, 105, 104),
    ('horizons', 'test_horizons_powers.py', 'horizons_powers_host.c', 106, 121, 106),
)

CONTRACT = r'''
static void preview_cancel_contract(void) {
 unsigned command, i, held_cases=0, progress;
 int cooldown, time, health;
 /* All commands start before a live effect is emitted. Some deliberately
  * lack held anticipation, but a same-frame interrupt still must cancel them. */
 for(command=FIRST_COMMAND;command<=LAST_COMMAND;command++) {
  setup(command);SEED_TARGETS;assert(POWER(command));
  if(HOLD(256)) {
   held_cases++;
   for(i=0;i<5;i++){updates(1);assert(AGE==0);assert(HOLD(256));}
  }
  assert(AGE==0&&TIME>0);
  cooldown=ability_cd;health=enemy_hp_q4[0];progress=FIELD_PROGRESS;
  game_power_preview_cancel();
  assert(TIME==0&&ability_cd==cooldown);
  assert(!HOLD(256));
  updates(400);
  assert(TIME==0&&enemy_hp_q4[0]==health&&(unsigned)FIELD_PROGRESS==progress);
  /* After the first real tick, opening/recalling must not erase an emitted
   * effect, roll its clock backward, or alter the engine-owned cooldown. */
  setup(command);SEED_TARGETS;assert(POWER(command));assert(!HOLD(0));updates(1);
  assert(AGE==1&&TIME>0);time=TIME;cooldown=ability_cd;
  game_power_preview_cancel();
  assert(TIME==time&&AGE==1&&ability_cd==cooldown);
  updates(400);assert(TIME==0);
 }
 assert(held_cases>0);
 /* Positive control: the same target fixture and a normally released
  * anticipation really damage an enemy and progress a field interaction. */
 setup(POSITIVE_COMMAND);SEED_TARGETS;assert(POWER(POSITIVE_COMMAND));
 health=enemy_hp_q4[0];assert(HOLD(256));updates(1);assert(AGE==0);
 assert(!HOLD(0));updates(400);
 assert(enemy_hp_q4[0]<health&&FIELD_PROGRESS>0&&FIELD_ACCEPTED>0);
 PRESERVE_PRIOR_STATUS;
 printf("PASS %s: %u commands; age0 cancellation, no delayed damage/field, cooldown retained; age1 lifetime preserved; live positive control\n",CHAPTER,LAST_COMMAND-FIRST_COMMAND+1);
}
int main(void){assert(creatures_catalog_validate());preview_cancel_contract();return 0;}
'''


def fixture_sources(script):
    tree = ast.parse((ROOT / 'tests' / script).read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == 'SOURCES'
                for target in node.targets):
            return ast.literal_eval(node.value)[1:]
    raise AssertionError('No explicit SOURCES in ' + script)


def cross_chapter_hooks(chapter, sources):
    extra = ''
    linked = {prefix for prefix in ('magma', 'underwater', 'return', 'horizons')
              if 'src/' + prefix + '_powers.c' in sources}
    for prefix in ('magma', 'underwater', 'return', 'horizons'):
        if prefix not in linked:
            extra += f'''int {prefix}_power_time,{prefix}_power_age;
void {prefix}_powers_reset(void){{assert(0&&"absent chapter must not reset");}}
'''
            if prefix == 'magma':
                extra += 'void magma_powers_cancel_preview(void){assert(0&&"absent chapter must not cancel");}\n'
    # Explicit fail-closed hooks match the existing isolated hold-input suite.
    # They are not production replacements or a synthetic world-progress oracle.
    for prefix in ('return', 'horizons', 'covenants'):
        if prefix == chapter:
            continue
        if prefix == 'covenants':
            extra += 'int covenants_power_time;\n'
        extra += f'''int {prefix}_game_is_room(unsigned a){{(void)a;return 0;}}
int {prefix}_game_clear_box(int a,int b,int c,int d){{(void)a;(void)b;(void)c;(void)d;return 0;}}
int {prefix}_game_supercover(int a,int b,int c,int d){{(void)a;(void)b;(void)c;(void)d;return -1;}}
unsigned {prefix}_game_action_begin(unsigned a){{(void)a;return 0;}}
int {prefix}_game_field_target(unsigned a,int*b,int*c,int*d){{(void)a;(void)b;(void)c;(void)d;return 0;}}
int {prefix}_game_field_hit(unsigned a,unsigned b,unsigned c,unsigned d,unsigned e){{(void)a;(void)b;(void)c;(void)d;(void)e;return 0;}}
void {prefix}_game_revoke_cast(unsigned a){{(void)a;}}
'''
    if chapter == 'horizons':
        extra += '''int game_collision_rects(int a,int b,int c,int d,short e[][4],unsigned f){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;return -1;}
int underwater_game_supercover(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;return -1;}
int game_road_box_touched(unsigned a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;return 0;}
'''
    if chapter in ('magma', 'underwater'):
        extra += 'int return_legacy_box_certificate(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;return 0;}\n'
    return extra


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    game_source = (ROOT / 'src/game.c').read_text()
    match = re.search(r'COLD void game_power_preview_cancel\(void\)\{.*?\n\}',
                      game_source, re.S)
    assert match, 'Actual engine helper is missing'
    helper = match.group().replace('COLD ', '', 1)
    results = []
    hashes = {'src/game.c': hashlib.sha256(game_source.encode()).hexdigest(),
              'engine_helper_sha256': hashlib.sha256(helper.encode()).hexdigest()}
    with tempfile.TemporaryDirectory(prefix='field-preview-cancel-') as directory:
        directory = Path(directory)
        for chapter, script, fixture, first, last, positive in CASES:
            sources = fixture_sources(script)
            seed = ('enemy(0,140,100,10);chapter_enabled=1;chapter_x=140;chapter_y=100'
                    if chapter == 'magma' else
                    'enemy(0,120,100,10);field_enabled=1;field_x=120;field_y=100'
                    if chapter == 'underwater' else
                    'enemy(0,20,0,0);field_count=1;field_x=120;field_y=100')
            progress = 'chapter_used' if chapter == 'magma' else 'field_calls'
            macros = {'FIRST_COMMAND': str(first), 'LAST_COMMAND': str(last),
                      'POSITIVE_COMMAND': str(positive), 'CHAPTER': json.dumps(chapter),
                      'POWER': chapter + '_power', 'HOLD': chapter + '_powers_hold_input',
                      'AGE': chapter + '_power_age', 'TIME': chapter + '_power_time',
                      'FIELD_PROGRESS': progress, 'SEED_TARGETS': seed,
                      'FIELD_ACCEPTED': 'chapter_used' if chapter == 'magma' else 'field_accepted' if chapter == 'underwater' else 'field_accepts',
                      'PRESERVE_PRIOR_STATUS': 'preserve_prior_status()' if chapter == 'magma' else '((void)0)'}
            preserve = r'''
static void preserve_prior_status(void){
 int cooldown, status;
 /* An actual old cast sets Magma's ownership bit, then naturally expires.
  * A real gear-runtime stagger refreshes the same enemy after cooldown.
  * Cancelling the next anticipation must not erase the weapon's status. */
 setup(46);enemy(0,118,100,10);assert(magma_power(46));updates(6);
 assert(enemy_stagger_ticks[0]>0);updates(180);
 assert(!magma_power_time&&!ability_cd&&!enemy_stagger_ticks[0]);
 game_enemy_stagger(0,1);assert(enemy_stagger_ticks[0]==24);updates(10);
 assert(enemy_stagger_ticks[0]>0&&enemy_stagger_ticks[0]<=16);
 status=enemy_stagger_ticks[0];select_command(51);assert(magma_power(51));
 assert(magma_powers_hold_input(256));cooldown=ability_cd;
 game_power_preview_cancel();
 assert(!magma_power_time&&!magma_power_cast_time&&ability_cd==cooldown);
 assert(enemy_stagger_ticks[0]==status);
 updates(1);assert(enemy_stagger_ticks[0]==status-1);
 /* The narrow cancel also retains ownership for a later full room reset. */
 magma_powers_reset();assert(!enemy_stagger_ticks[0]);
 puts("prior emitted weapon stagger survives new preview cancellation");
}
''' if chapter == 'magma' else ''
            headers = ''.join('#include "' + prefix + '_powers.h"\n'
                              for prefix in ('magma', 'underwater', 'return', 'horizons'))
            source = ('#define main inherited_main\n#include "' + fixture +
                      '"\n#undef main\n' + headers +
                      cross_chapter_hooks(chapter, sources) + helper + '\n' + preserve +
                      '\n'.join('#define ' + key + ' ' + value
                                for key, value in macros.items()) + '\n' + CONTRACT)
            path = directory / (chapter + '.c')
            path.write_text(source)
            for relative in sources + ['tests/' + script, 'tests/' + fixture,
                                       'src/' + chapter + '_powers.h']:
                hashes[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            for sanitized in (False, True):
                name = chapter + ('-sanitized' if sanitized else '-strict')
                target = OUT / name
                flags = ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if sanitized else []
                link = '-Wl,-dead_strip' if sys.platform == 'darwin' else '-Wl,--gc-sections'
                subprocess.run([os.environ.get('HOST_CC', 'cc'), '-std=c99', '-O1', '-g',
                                '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation',
                                '-pedantic', '-ffunction-sections', '-fdata-sections', link,
                                '-Isrc', '-Itests', *flags, str(path), *sources,
                                '-o', str(target)], cwd=ROOT, check=True)
                result = subprocess.run([str(target)], cwd=ROOT, check=True, text=True,
                                        capture_output=True, env={**os.environ,
                                            'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
                                            'UBSAN_OPTIONS': 'halt_on_error=1'})
                print(name + ': ' + result.stdout.strip(), flush=True)
                results.append({'case': name, 'commands': last - first + 1, 'passed': True})
    (OUT / 'report.json').write_text(json.dumps(
        {'scope': __doc__, 'source_hashes': hashes, 'results': results}, indent=2) + '\n')


if __name__ == '__main__':
    main()
