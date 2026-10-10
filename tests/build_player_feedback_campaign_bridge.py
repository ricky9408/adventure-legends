#!/usr/bin/env python3
"""Build the controller bridge from retained copies, with exact source receipts."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);sources={}
for name in ('tests/player_feedback_mgba_bridge.c','tools/mgba_bridge.c'):
 target=out/'bridge-source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target);sources[name]=sha(target)
usr=ROOT/'tools/sysroot/usr';binary=out/'bridge.so';cc=Path(shutil.which('cc')).resolve();command=[str(cc),'-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(out/'bridge-source/tests/player_feedback_mgba_bridge.c'),'-I'+str(usr/'include'),'-L'+str(usr/'lib/x86_64-linux-gnu'),'-Wl,-rpath,'+str((usr/'lib/x86_64-linux-gnu').resolve()),'-o',str(binary),'-lmgba'];subprocess.run(command,check=True)
receipt={'bridge_sha256':sha(binary),'sources':sources,'command':command,'compiler_sha256':sha(cc),'compiler_version':subprocess.check_output([str(cc),'--version'],text=True).splitlines()[0],'libmgba_sha256':sha(usr/'lib/x86_64-linux-gnu/libmgba.so'),'source_policy':'Compiled these exact retained source files, never mutable producer paths'}
(out/'bridge-build.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
