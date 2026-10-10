#!/usr/bin/env python3
"""Host register/sequence contract, not native audio or listening acceptance."""
from pathlib import Path
import hashlib,json,subprocess,os
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/horizons-audio-host';OUT.mkdir(parents=True,exist_ok=True)
sources=['tests/horizons_audio_host.c','src/horizons_audio.c']
rows=[]
for mode,extra in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie'])]:
    exe=OUT/mode
    subprocess.run(['cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-DHORIZONS_AUDIO_HOST','-Isrc',*extra,*sources,'-o',str(exe)],cwd=ROOT,check=True)
    env=dict(os.environ)
    # The module has no heap allocations. LSan cannot inspect this executor
    # under ptrace; AddressSanitizer and UndefinedBehaviorSanitizer stay active.
    if mode=='sanitized':env['ASAN_OPTIONS']='detect_leaks=0'
    result=subprocess.run([str(exe)],cwd=ROOT,text=True,capture_output=True,env=env)
    (OUT/(mode+'.log')).write_text(result.stdout+result.stderr)
    result.check_returncode()
    rows.append({'mode':mode,'passed':True,'output':result.stdout.strip()})
report={'scope':'Host synthetic PSG2 register and sequence contract only; ASan/UBSan active, leak detection omitted for no-heap module under ptrace','checks':rows,'source_sha256':{x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest()for x in [*sources,'src/horizons_audio.h']},'native_audio_tested':False,'listening_review':False}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
