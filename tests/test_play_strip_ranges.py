#!/usr/bin/env python3
"""Actual current strip functions versus the immutable 4005 full-strip oracle.

This is synthetic host pixel/provenance evidence. Drawing, bitmap DMA, and save
delivery use explicit stubs; no earned play, text rasterization, or timing claim.
The historical functions below were checked byte-for-byte against commit
4005fa2c9e7cf7bcc92576b16753dc4022b8a5a8 and the measured baseline before
embedding. CI needs neither Git history nor external evidence files.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/play-strip-ranges'
PARENT_COMMIT = '4005fa2c9e7cf7bcc92576b16753dc4022b8a5a8'
SIGNATURES = (
    'COLD void capture_play_strip(void)',
    'COLD int reuse_play_strip(const u32*key)',
    'COLD void finish_scene_presentation(void)',
)
REFERENCE_HASHES = (
    'bf8a28b4c7ef68655efbd68d7f0d52a00ffab623052fb8dbf9781363dad3b07c',
    'e87809af3f40488b1c484b4815790b7e7f68db177dc06a2ca9ee8c7e13fa357c',
    '1986561ce5d18464dcfe53740eb76fd36eb636ed1482e1dfd0c11114179a8360',
)
REFERENCE_FUNCTIONS = (
    r'''COLD void capture_play_strip(void){
 if(game_state!=PLAY||quickparty_open){play_strip_valid[page]=play_strip_clean[page]=0;return;}
 if(!boss_active()&&!toast_ticks&&!game_shop_reward_visible()&&!southern_powers_hint()&&!magma_powers_hint()&&!underwater_powers_hint()&&!return_powers_hint()&&!horizons_powers_hint()&&!covenants_powers_hint()){play_strip_valid[page]=0;play_strip_clean[page]=1;return;}
#ifndef GAME_HOST_TEST
 REG32(0x040000D4)=(u32)(screen+122*120);REG32(0x040000D8)=(u32)play_world_strip[page];REG32(0x040000DC)=0x84000000|2280;
#else
 {unsigned i;for(i=0;i<120u*38u;i++)play_world_strip[page][i]=screen[122*120+i];}
#endif
 play_strip_valid[page]=1;play_strip_clean[page]=0;
}
''',
    r'''COLD int reuse_play_strip(const u32*key){unsigned i;int raw;
#ifndef GAME_HOST_TEST
 unsigned started;
#endif
 if(play_strip_disabled||game_state!=PLAY||quickparty_open||!cache_valid[page]||(!play_strip_valid[page]&&!play_strip_clean[page])||cache_fields[page][1]!=PLAY)return 0;
 /* Campaign4..13 backgrounds use the explicit room/chapter flags below.
  * EXP/level bookkeeping changes progression_revision but only the HUD/actors
  * and earned notice; both are still drawn this update. Other chapters keep
  * their full progression key because it can change authored scenery. */
 for(i=0;i<CACHE_FIELDS;i++)if(i!=7&&i!=8&&i!=27&&i!=29&&i!=31&&i!=33&&i!=35&&i!=37&&i!=40&&i!=42&&!(i==19&&room>=4&&room<14)&&cache_fields[page][i]!=key[i])return 0;
 raw=play_strip_valid[page];
 if(!raw&&(!play_strip_clean[page]||boss_active()||cache_fields[page][7]||cache_fields[page][27]||cache_fields[page][29]||cache_fields[page][31]||cache_fields[page][33]||cache_fields[page][35]||cache_fields[page][37]||cache_fields[page][42]))return 0;
#ifndef GAME_HOST_TEST
 started=cycle_now();
#endif
 /* A clean page is already the exact underlay. Capture before its first
  * overlay; never restore an uninitialized raw buffer or invent new keys. */
 if(!raw)capture_play_strip();
 if(raw){
#ifndef GAME_HOST_TEST
  REG32(0x040000D4)=(u32)play_world_strip[page];REG32(0x040000D8)=(u32)(screen+122*120);REG32(0x040000DC)=0x84000000|2280;
#else
  unsigned n;for(n=0;n<120u*38u;n++)screen[122*120+n]=play_world_strip[page][n];
#endif
 }
 draw_play_notices(1);game_shop_draw_reward();
#ifndef GAME_HOST_TEST
 render_card_cycles=cycle_now()-started;
#endif
 play_strip_reuses++;return 1;
}
''',
    r'''COLD void finish_scene_presentation(void){int i,other=page^1;
 copy_previous_bitmap();
 for(i=0;i<CACHE_FIELDS;i++)cache_fields[page][i]=cache_fields[other][i];
 for(i=0;i<112;i++)modal_world_row[page][i]=modal_world_row[other][i];
 cache_valid[page]=cache_valid[other];cached_armor[page]=cached_armor[other];play_strip_valid[page]=play_strip_valid[other];play_strip_clean[page]=play_strip_clean[other];
 if(play_strip_valid[other]){
#ifndef GAME_HOST_TEST
  REG32(0x040000D4)=(u32)play_world_strip[other];REG32(0x040000D8)=(u32)play_world_strip[page];REG32(0x040000DC)=0x84000000|2280;
#else
  for(i=0;i<120*38;i++)play_world_strip[page][i]=play_world_strip[other][i];
#endif
 }
 scene_present_phase=0;
 /* Both pages now contain the completed scene. Only ordinary work can use
  * this frozen warm-copy update; critical/typed owners keep their path. */
 if(game_state==PLAY&&(!save_requested||save_feedback_ordinary)&&(save_feedback_background||(save_requested&&save_feedback_ordinary))){save_ordinary_defer=0;save_frame();}
}
''',
)
FIELDS = (
    'game_state', 'quickparty_open', 'quickparty_visible', 'page', 'screen', 'play_strip_valid',
    'play_strip_clean', 'play_strip_top', 'play_world_strip', 'play_strip_disabled',
    'cache_valid', 'cache_fields', 'room', 'play_strip_reuses', 'modal_world_row',
    'cached_armor', 'scene_present_phase', 'save_requested',
    'save_feedback_ordinary', 'save_feedback_background', 'save_ordinary_defer',
    'toast_ticks',
)


def extract(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def translation_unit(name, functions):
    # Macro bindings supply two independent host states. Extracted function
    # bodies remain unchanged, including their real GAME_HOST_TEST branches.
    bindings = ['#include "play_strip_ranges_host.h"', '#define GAME_HOST_TEST 1',
                '#define COLD', f'#define capture_play_strip {name}_capture',
                f'#define reuse_play_strip {name}_reuse',
                f'#define finish_scene_presentation {name}_finish']
    # The exact historical reference used open for visible panel ownership.
    # Bind that old name to visibility; current open also includes hidden arming.
    bindings += [f'#define {field} ({name}.{"quickparty_visible" if name == "reference" and field == "quickparty_open" else field})'
                 for field in FIELDS
                 if not (name == "reference" and field == "quickparty_visible")]
    bindings += [
        f'#define boss_active() ({name}.boss)',
        f'#define game_shop_reward_visible() ({name}.reward)',
        f'#define draw_play_notices(mode) oracle_draw_notices(&{name},mode)',
        f'#define game_shop_draw_reward() oracle_draw_reward(&{name})',
        f'#define copy_previous_bitmap() oracle_copy_previous_bitmap(&{name})',
        f'#define save_frame() oracle_save_frame(&{name})',
    ]
    for index, chapter in enumerate(('southern', 'magma', 'underwater', 'return',
                                     'horizons', 'covenants')):
        bindings += [f'#define {chapter}_powers_hint() ({name}.hints[{index}])']
    return '\n'.join(bindings) + '\n' + '\n'.join(functions)


def checked_run(command, log):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            timeout=120, env={**os.environ,
                                'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
                                'UBSAN_OPTIONS': 'halt_on_error=1'})
    log.write_text(result.stdout + result.stderr)
    if result.returncode:
        print(result.stdout + result.stderr, end='')
        result.check_returncode()
    return result.stdout.strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report_path = OUT / 'report.json'
    report_path.unlink(missing_ok=True)
    reference_hashes = tuple(map(sha256, REFERENCE_FUNCTIONS))
    if reference_hashes != REFERENCE_HASHES:
        raise AssertionError('Embedded historical full-strip reference changed')
    source = (ROOT / 'src/game.c').read_text()
    candidate_functions = tuple(extract(source, sig) for sig in SIGNATURES)
    # The optimization retains the original world/viewport admission guard.
    guards = [functions[1].split('raw=play_strip_valid[page];')[0]
              for functions in (candidate_functions, REFERENCE_FUNCTIONS)]
    if guards[0].count('quickparty_visible') != 1:
        raise AssertionError('Expected one explicit current display-visibility guard')
    if guards[0].replace('quickparty_visible', 'quickparty_open') != guards[1]:
        raise AssertionError('Current strip cache changed the world/viewport guard beyond display ownership')
    if 'u16 play_world_strip[2][120*38]' not in source:
        raise AssertionError('The complete 38-row backing buffer must remain')
    runs = []
    with tempfile.TemporaryDirectory(prefix='play-strip-ranges-') as temporary:
        temporary = Path(temporary)
        units = []
        for name, functions in (('candidate', candidate_functions),
                                ('reference', REFERENCE_FUNCTIONS)):
            unit = temporary / f'{name}.c'
            unit.write_text(translation_unit(name, functions))
            units.append(str(unit))
        for label, flags in [('strict', []), ('sanitized', [
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
            target = temporary / label
            command = [os.environ.get('HOST_CC', 'cc'), '-std=c99', '-O2',
                       '-Wall', '-Wextra', '-Werror', '-pedantic', *flags,
                       '-I' + str(ROOT / 'tests'),
                       str(ROOT / 'tests/play_strip_ranges_host.c'), *units,
                       '-o', str(target)]
            checked_run(command, OUT / f'{label}-compile.log')
            output = checked_run([str(target)], OUT / f'{label}.log')
            print(label + ': ' + output)
            runs.append({'mode': label, 'result': output})
    report = {
        'evidence': 'synthetic host pixel/provenance differential; no play or timing claim',
        'historical_reference_commit': PARENT_COMMIT,
        'world_guard_identical_after_display_binding': True,
        'historical_open_bound_to_current_visible': True,
        'hidden_selector_arming_exercises_normal_field_ranges': True,
        'full_38_row_buffer_retained': True,
        'candidate_source': {'path': 'src/game.c', 'sha256': sha256(source)},
        'functions': [
            {'signature': sig, 'candidate_sha256': sha256(candidate),
             'reference_sha256': reference}
            for sig, candidate, reference in zip(SIGNATURES, candidate_functions,
                                                  REFERENCE_HASHES)],
        'harness_sha256': {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in ('tests/test_play_strip_ranges.py',
                         'tests/play_strip_ranges_host.c',
                         'tests/play_strip_ranges_host.h')},
        'runs': runs,
        'stubs': ['overlay drawing within documented row bounds',
                  'bitmap scene copy into host arrays', 'save_frame call counter',
                  'boss/reward/hint state queries'],
        'limitations': ['DMA hardware branch not executed',
                        'actual Japanese text/sprite rasterization not exercised',
                        'gameplay, native timing, and personal saves not exercised'],
    }
    report_path.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
