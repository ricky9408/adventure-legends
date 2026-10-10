#!/usr/bin/env python3
"""Actual current C transport sanitizer and deterministic importer rejection gate."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='current-soundtrack-runtime-')as d:
 t=Path(d);exe=t/'actual-c'
 subprocess.run(['cc','-std=c99','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Itests','-Isrc','tests/regional_actual_c.c','src/music_data.c','-o',str(exe)],cwd=ROOT,check=True)
 subprocess.run([str(exe)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
 work=t/'import';(work/'tools').mkdir(parents=True);(work/'src').mkdir();(work/'docs').mkdir();(work/'assets/music/regional').mkdir(parents=True)
 shutil.copyfile(ROOT/'tools/generate_music.py',work/'tools/generate_music.py');shutil.copyfile(ROOT/'assets/music/regional/room-plan.json',work/'assets/music/regional/room-plan.json')
 original=json.loads((ROOT/'assets/music/regional/catalog.json').read_text())
 for cue in original['cues']:
  target=work/cue['raw_path'];target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(ROOT/cue['raw_path'])
 catalog=work/'assets/music/regional/catalog.json';catalog.write_text(json.dumps(original))
 subprocess.run([sys.executable,str(work/'tools/generate_music.py')],check=True)
 generated=[p for p in(work/'src').rglob('*')if p.is_file()]+[work/'docs/music-conversion.json']
 assert all(p.read_bytes()==(ROOT/p.relative_to(work)).read_bytes()for p in generated)
 snapshot=lambda:{str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest()for p in generated}
 before=snapshot()
 for kind in ('hash','length','rate','duplicate'):
  candidate=json.loads(json.dumps(original));cue=candidate['cues'][-1]
  if kind=='hash':cue['raw_sha256']='0'*64
  elif kind=='length':cue['sample_count']+=1
  elif kind=='rate':cue['sample_rate']=32000
  else:cue['id']=candidate['cues'][0]['id']
  catalog.write_text(json.dumps(candidate));run=subprocess.run([sys.executable,str(work/'tools/generate_music.py')],capture_output=True)
  assert run.returncode!=0 and snapshot()==before,kind
 print('PASS current importer',len(generated),'exact generated files; four invalid inputs rejected before mutation')
