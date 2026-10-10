#!/usr/bin/env python3
"""Native fixed-state notice raster proof, with complete stabilized scanout.

Calls production ARM/Thumb functions in a same-ROM active-power snapshot while
explicitly suspending gameplay/IRQs, then lets two full display scans finish.
Compares cold/warm cache with the original separate toast and hint functions on
both bitmap pages over different random world pixels and UI width/expiry keys.
This is a frozen rendering oracle; it makes no gameplay or timing claim.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Native,sha
p=argparse.ArgumentParser(description=__doc__)
for name in('candidate-root','state-evidence','output'):p.add_argument('--'+name,type=Path,required=True)
for name in('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+name,required=True)
a=p.parse_args();root=a.candidate_root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
rom=root/'build/emberbond.gba';symbols=root/'build/emberbond.sym'
assert sha(rom)==a.expected_rom_sha and sha(symbols)==a.expected_symbols_sha
assert sha(a.state_evidence/'tested.gba')==a.expected_rom_sha and sha(a.state_evidence/'tested.sym')==a.expected_symbols_sha
for source,name in((rom,'tested.gba'),(symbols,'tested.sym'),(Path(__file__),'helper.py'),(ROOT/'tests/notice_cache_callable_bridge.c','bridge-source.c')):shutil.copyfile(source,out/name)
bridge=out/'bridge.so';subprocess.run(['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(ROOT/'tests/notice_cache_callable_bridge.c'),'-I'+str(ROOT/'tools/sysroot/usr/include'),'-L'+str(ROOT/'tools/sysroot/usr/lib/x86_64-linux-gnu'),'-Wl,-rpath,'+str((ROOT/'tools/sysroot/usr/lib/x86_64-linux-gnu').resolve()),'-o',str(bridge),'-lmgba'],check=True)
sym={v[2]:int(v[0],16)for line in symbols.read_text().splitlines()if len(v:=line.split())==3}
ids=list(dict.fromkeys(re.findall(r'\bTX_[A-Z0-9_]+\b',(root/'src/ui.h').read_text())))
e=Native(rom,bridge);e.lib.eb_notice_call.argtypes=[C.c_void_p,C.c_uint32];e.lib.eb_notice_call.restype=C.c_uint
e.lib.eb_notice_fill.argtypes=[C.c_void_p,C.c_uint32,C.c_uint];e.lib.eb_notice_fill.restype=None
writes=[];results=[];calls=[]
def put(n,v):writes.append({'symbol':n,'value':v});e.write(sym[n],v&0xffffffff)
def invoke(name):
 count=e.lib.eb_notice_call(e.ptr,sym[name]);calls.append({'function':name,'instructions_bound':count});assert count,(name,'did not return')
states=sorted(a.state_evidence.glob('*-active.state'));assert states,'No same-ROM active-power snapshots supplied'
for state in states:
 for page in(0,1):
  for key in('original','wide','expire'):
   branches=[]
   for cached in(False,True):
    e.state(state,load=True);screen=0x0600a000 if page else 0x06000000
    put('screen',screen);put('play_notice_cache_disabled',0);put('play_notice_valid',0)
    # Select exactly the target page for the fixed-state scanout.
    e.write(0x04000000,0x1444|(page<<4),2)
    if key=='wide':put('toast_id',ids.index('TX_PF_ROUTE_LATER'));put('toast_ticks',20)
    if key=='expire':put('toast_ticks',0)
    samples=[]
    for warm in(0,1):
     e.lib.eb_notice_fill(e.ptr,screen,76413+warm*6371)
     before_oam=e.bytes(0x07000000,1024);before_obj=e.bytes(0x06014000,16384)
     if cached:invoke('draw_play_notices')
     else:invoke('draw_play_toast');invoke('draw_play_hint')
     raw=e.bytes(screen,38400);assert before_oam==e.bytes(0x07000000,1024)and before_obj==e.bytes(0x06014000,16384)
     e.frames(2);image=e.screenshot();pixels=image.tobytes()
     samples.append({'bitmap':hashlib.sha256(raw).hexdigest(),'rgb':hashlib.sha256(pixels).hexdigest(),'oam':hashlib.sha256(before_oam).hexdigest(),'obj':hashlib.sha256(before_obj).hexdigest()})
     if key=='original'and warm:image.save(out/('%s-page%d-%s.png'%(state.stem,page,'cached'if cached else'original')))
    branches.append(samples)
   for warm in(0,1):results.append({'state':state.name,'page':page,'key':key,'warm':bool(warm),'passed':branches[0][warm]==branches[1][warm],'original':branches[0][warm],'cached':branches[1][warm]})
assert len(results)==len(states)*12
report={'scope':__doc__,'passed':all(r['passed']for r in results)and not e.lib.eb_faults(e.ptr),'candidate':{'rom_sha256':sha(rom),'symbols_sha256':sha(symbols),'bridge_sha256':sha(bridge),'helper_sha256':sha(__file__)},'comparisons':results,'preparation_writes':writes,'native_calls':calls,'faults':e.lib.eb_faults(e.ptr)}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'comparisons':len(results),'failures':[r for r in results if not r['passed']],'faults':report['faults']},indent=2));e.close();sys.exit(not report['passed'])
