#!/usr/bin/env python3
"""Host/synthetic actual C adapter regression; rendering is stubbed, not native gameplay."""
from pathlib import Path
import re, subprocess, shutil, os
ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'build'/'regional-adapter-host'
TMP.mkdir(parents=True,exist_ok=True)
shutil.copyfile(ROOT/'tests/regional_adapters_native.c',TMP/'harness.c')
for name in ('progression.c','progression.h','quickparty.c','quickparty.h'):
    shutil.copyfile(ROOT/'src'/name,TMP/name)
header=(ROOT/'src/ui.h').read_text()
known=set(re.findall(r'\bTX_\w+\b',header))
needed=set(re.findall(r'\bTX_\w+\b',(TMP/'progression.c').read_text()+(TMP/'quickparty.c').read_text()))
missing=sorted(needed-known)
(TMP/'ui.h').write_text(header+'\n'+('\nenum { '+', '.join(f'{n}={1000+i}' for i,n in enumerate(missing))+' };\n' if missing else ''))
modules=['creatures','creature_data','equipment','equipment_data','save4','save5','regional_quests','campaign_rules','evolution_art','regional_creature_art','northern_creature_art','southern_creature_art','progression_events','southern_quests']
args=['cc','-std=c99','-g','-O1','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(TMP),'-I'+str(ROOT/'src'),str(TMP/'harness.c'),str(TMP/'progression.c'),str(TMP/'quickparty.c'),*[str(ROOT/'src'/(n+'.c')) for n in modules],'-o',str(TMP/'harness')]
print('UI shim IDs:',missing,flush=True)
subprocess.run(args,check=True)
subprocess.run([str(TMP/'harness')],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
