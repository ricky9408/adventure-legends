#!/usr/bin/env python3
"""Current Sunlace fountain dialogue, approach and repeat interactions (host)."""
import ast
import ctypes as C
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='sunlace-welcome-') as tmp:
    out = Path(tmp)
    tree = ast.parse((ROOT / 'tests/test_south_game.py').read_text())
    harness = next(ast.literal_eval(n.value) for n in tree.body
                   if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'HARNESS' for t in n.targets))
    harness = harness.replace('void dialogue(int a,int b,int c){(void)a;(void)b;(void)c;game_state=2;}',
        'int lines[2]; void dialogue(int a,int b,int c){lines[0]=a;lines[1]=b;(void)c;game_state=2;}')
    harness += '\nint game_road_collision(unsigned r,int x,int y){(void)r;(void)x;(void)y;return -1;}\nint game_road_managed(unsigned a,unsigned b){(void)a;(void)b;return 0;}\n'
    ui = json.loads((ROOT / 'assets/southern_region/ui_additions.json').read_text())
    ui.update({'MG_RESERVED': '', 'MG_RESERVEDB': ''})
    (out / 'south_game_test_ui.h').write_text('enum{'+','.join('TX_'+k+'='+str(3000+i) for i,k in enumerate(ui))+'};\n')
    (out / 'h.c').write_text(harness)
    sources = ['south_game','south_art','southern_quests','northern_quests','save5','save4','equipment','equipment_data','creatures','creature_data']
    for sanitize in (False, True):
        libpath = out / ('san.so' if sanitize else 'test.so')
        subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC',
            '-DSOUTH_GAME_HOST_TEST','-DSAVE5_HOST_TEST','-DSAVE4_HOST_TEST','-Isrc','-I'+tmp,
            str(out/'h.c'), *['src/'+s+'.c' for s in sources],
            *(['-fsanitize=undefined','-fno-sanitize-recover=all'] if sanitize else []), '-o', str(libpath)], cwd=ROOT, check=True)
        lib = C.CDLL(str(libpath))
        sram = (C.c_ubyte*32768).in_dll(lib, 'save5_test_sram')
        sram[:] = (ROOT/'tests/fixtures/v5-revision3/northern-all21-town.sav').read_bytes()
        assert lib.fresh() == 1 and lib.entry(30,0) == 1
        value = lambda n: C.c_int.in_dll(lib,n).value
        # The historical fixture supplies access, not evidence of earned arrival.
        assert (value('px'),value('py')) == (240,284)
        for x,y in [(240,y) for y in range(284,239,-1)] + [(x,240) for x in range(240,223,-1)] + [(224,y) for y in range(240,159,-1)]:
            assert not lib.south_game_solid(x,y), (x,y)
        lib.snapshot_state()
        for _ in range(2):
            lib.at(224,160)
            assert lib.south_game_interact() == 1
            assert value('game_state') == 2 and value('room') == 30
            assert list((C.c_int*2).in_dll(lib,'lines')) == [3000+list(ui).index(k) for k in ('ST_WELCOME_A','ST_WELCOME_B')]
            assert lib.unchanged() == 1
        lib.at(224,160)
        C.c_int.in_dll(lib,'face').value = 0
        assert lib.south_game_interact() == 0
        lib.at(240,264)
        assert lib.south_game_interact() == 1 and value('room') == 22
print('Sunlace welcome: strict and UBSan passed')
