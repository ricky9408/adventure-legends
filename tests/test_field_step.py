#!/usr/bin/env python3
"""Wall-checked field step: distance, cooldown, collision, and the garden contract."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'src/game.c').read_text(encoding='utf-8')
QUICK = (ROOT / 'src/quickparty.c').read_text(encoding='utf-8')
JOURNAL = (ROOT / 'src/journal_nav.c').read_text(encoding='utf-8')
GUIDE = (ROOT / 'docs/PLAY_JA.md').read_text(encoding='utf-8')


def function(name):
    match = re.search(r'^(?:COLD )?(?:int|void) ' + name + r'\([^;{}]*\)\s*\{', SOURCE, re.MULTILINE)
    assert match, name
    start = match.start()
    depth = 0
    for end in range(SOURCE.index('{', start), len(SOURCE)):
        depth += (SOURCE[end] == '{') - (SOURCE[end] == '}')
        if depth == 0:
            return SOURCE[start:end + 1]
    raise AssertionError(name)


update = SOURCE[SOURCE.index('void update(void)'):SOURCE.index('COLD void draw_sword(void)')]
assert 'roll_ticks=roll_cd=roll_dx=roll_dy=0;' in update
assert 'if(step_cd)step_cd--;' in update
assert 'field_step_try(axis)' in update
assert update.index('field_goal_input((unsigned)pressed)') < update.index('field_controls_read(')
step = function('field_step_try')
for forbidden in ('invuln', 'guard_invuln', 'roll_ticks', 'roll_cd'):
    assert forbidden not in step
assert 'move_player(dx*12*256,dy*12*256)' in step and 'step_cd=18' in step
assert 'SELECT 目的  L＋方向で一歩' in JOURNAL
assert 'field_step_control_line(18,112,CREAM)' in JOURNAL
assert '方向を押したままLを短く押す：向いているほうへ短い一歩' in GUIDE
assert 'quickparty_directional_tap=axis' in QUICK

with tempfile.TemporaryDirectory(prefix='field-step-') as temporary:
    out = Path(temporary)
    (out / 'field_step.inc').write_text(
        function('move_player') + '\n' + step + '\n', encoding='utf-8')
    common = ['cc', '-std=c99', '-O1', '-Wall', '-Wextra', '-Werror', '-pedantic',
              '-Isrc', '-I' + str(out), 'tests/field_step_host.c']
    for mode, flags in (('strict', []),
                        ('sanitized', ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])):
        target = out / mode
        subprocess.run([*common, *flags, '-o', str(target)], cwd=ROOT, check=True)
        subprocess.run([str(target)], cwd=ROOT, check=True)

    region = (ROOT / 'tests/test_region_game.py').read_text(encoding='utf-8')
    harness = region.split("HARNESS=r'''", 1)[1].split("'''", 1)[0]
    harness = harness.replace(
        'summoned,roll_ticks,transition_lock',
        'summoned,roll_ticks,roll_cd,transition_lock', 1)
    garden = r'''
int main(void){
 static const int xy[3][2]={{72,72},{120,72},{168,104}};
 unsigned i;
 test_fresh(15);
 assert(test_enter(16,0));
 assert(test_enter(21,0));
 test_at(64,136,0);
 assert(region_game_interact());
 for(i=0;i<3;i++){
  test_at(xy[i][0],xy[i][1],0);
  test_keys(0,0);
  region_game_tick();
  assert(region_game_garden_step==i+1);
  assert(roll_ticks==0&&roll_cd==0);
  region_game_tick();
  assert(region_game_garden_step==i+1&&roll_ticks==0&&roll_cd==0);
 }
 assert(test_state(9)==2);
 puts("PASS Reedhaven garden on foot with roll_ticks and roll_cd at 0");
 return 0;
}
'''
    (out / 'bridges.c').write_text('#include <assert.h>\n#include <stdio.h>\n' + harness + garden, encoding='utf-8')
    sources = ['src/region_game.c', 'src/region_art.c', 'src/regional_quests.c', 'src/save5.c',
               'src/save4.c', 'src/equipment.c', 'src/equipment_data.c', 'src/creatures.c', 'src/creature_data.c']
    flags = ['cc', '-std=c99', '-O1', '-Wall', '-Wextra', '-Werror', '-pedantic',
             '-DREGION_GAME_HOST_TEST', '-DSAVE5_HOST_TEST', '-DSAVE4_HOST_TEST',
             '-I' + str(out), '-Isrc', str(out / 'bridges.c'), *sources,
             '-Wl,--wrap=equipment_claim_many', '-o', str(out / 'garden')]
    (out / 'region_game_test_ui.h').write_text(
        'enum {\n' + ''.join(
            f'TX_{key}={1000 + index},\n'
            for index, key in enumerate(__import__('json').loads(
                (ROOT / 'assets/region/ui_additions.json').read_text()) | {'MG_RESERVED': '', 'MG_RESERVEDB': ''}))
        + '};\n', encoding='utf-8')
    subprocess.run(flags, cwd=ROOT, check=True)
    subprocess.run([str(out / 'garden')], cwd=ROOT, check=True)
