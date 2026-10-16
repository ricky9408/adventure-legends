#!/usr/bin/env python3
"""Native audio/VBlank IRQ regression; controller-only, never host FPS gating."""
import argparse,array,ctypes as C,gzip,hashlib,json,sys,wave
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source-root',type=Path,default=Path(__file__).resolve().parents[1])
 for name in ('rom','symbols','bridge','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();root=a.source_root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 sys.path.insert(0,str(root/'tools'));from mgba_runner import keymask
 sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 sym={v[2]:int(v[0],16)for ln in a.symbols.read_text().splitlines()if len(v:=ln.split())==3}
 lib=C.CDLL(str(a.bridge.resolve()))
 for n,args,ret in [('eb_open',[C.c_char_p],C.c_void_p),('eb_close',[C.c_void_p],None),('eb_frames',[C.c_void_p,C.c_uint,C.c_uint],None),('eb_read',[C.c_void_p,C.c_uint32,C.c_uint],C.c_uint32),('eb_framecounter',[C.c_void_p],C.c_uint),('eb_reset',[C.c_void_p],None),('eb_load_save',[C.c_void_p,C.c_char_p],C.c_int),('eb_audio_start',[C.c_void_p,C.c_char_p],C.c_int),('eb_audio_stop',[C.c_void_p],C.c_uint)]:
  f=getattr(lib,n);f.argtypes=args;f.restype=ret
 if hasattr(lib,'eb_faults'):lib.eb_faults.argtypes=[C.c_void_p];lib.eb_faults.restype=C.c_uint
 report={'scope':__doc__,'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'bridge_sha256':sha(a.bridge),'harness_sha256':sha(__file__),'controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'physical_hardware_tested':False,'host_cpu_performance_gate':False,'cases':[],'checks':[],'inputs':[]}
 trace=gzip.open(out/'frames.jsonl.gz','wt');e=None;rows=[];session=''
 def check(label,ok):
  report['checks'].append({'session':session,'label':label,'passed':bool(ok)});assert ok,label
 def g(n):return lib.eb_read(e,sym[n],4)
 def read(addr,width=2):return lib.eb_read(e,addr,width)
 def step(n,keys=0,label='setup',strict=False):
  report['inputs'].append({'session':session,'label':label,'hw':lib.eb_framecounter(e),'frames':n,'keys':keymask(keys)})
  rr=[]
  for _ in range(n):
   old=g('frame');page=read(0x04000000)&16;lib.eb_frames(e,1,keymask(keys));serial=g('render_profile_serial')
   r={'session':session,'label':label,'hw':lib.eb_framecounter(e),'delta':(g('frame')-old)&0xffffffff,'flip':bool((read(0x04000000)&16)!=page),**{n:g(n)for n in('game_state','room','px','py','camera_x','camera_y','face','render_cycles','music_faults','music_recoveries','music_stopped','music_irq_count','music_irq_late_max','music_track')},'profile_serial':serial,'vblank_start':g('render_profile_vblank_start'),'vblank_end':g('render_profile_vblank_end'),'core_faults':int(lib.eb_faults(e))if hasattr(lib,'eb_faults')else None}
   rows.append(r);rr.append(r);trace.write(json.dumps(r,separators=(',',':'))+'\n')
   assert not any(r[n]for n in('music_faults','music_recoveries','music_stopped')) and not r['core_faults'],r
   if strict:assert r['delta']==1 and r['flip'] and r['render_cycles']<280896 and r['music_irq_late_max']<208 and not serial&1 and serial==g('render_profile_serial') and 160<=r['vblank_start']<=r['vblank_end']<228,r
  return rr
 def tap(k):step(2,k);step(5)
 def wait_play():
  for _ in range(1300):
   if g('game_state')==1 and not g('save_requested')and not g('save_feedback_background'):break
   step(1)
  check('controller reaches settled PLAY',g('game_state')==1 and not g('save_requested')and not g('save_feedback_background'))
 def irq_check():
  check('VBlank and Timer1 IRQ enabled together',read(0x04000200)==17 and read(0x04000004)&8 and read(0x04000208)==1)
 def window(name,n=1200,control=None,exact_audio=False):
  before=g('music_irq_count');path=out/(name+'.wav')
  if exact_audio:check('WAV capture opens',lib.eb_audio_start(e,str(path).encode())==1)
  rr=[]
  for i in range(n):rr+=step(1,control(i)if control else 0,name,True)
  captured_samples=lib.eb_audio_stop(e)if exact_audio else None
  result={'name':name,'frames':n,'updates':sum(r['delta']for r in rr),'flips':sum(r['flip']for r in rr),'maximum_cycles':max(r['render_cycles']for r in rr),'maximum_irq_lateness_samples':max(r['music_irq_late_max']for r in rr),'timer_irqs':g('music_irq_count')-before,'unique_positions':len({(r['px'],r['py'])for r in rr}),'unique_cameras':len({(r['camera_x'],r['camera_y'])for r in rr}),'faces':sorted({r['face']for r in rr})}
  check(name+' Timer1 advances while BIOS waits on VBlank',result['timer_irqs']>=n//40);irq_check()
  if exact_audio:
   cue=json.loads((root/'assets/music/selected/catalog.json').read_text())['cues'][0];src_path=root/cue['raw_path'];src=array.array('b',src_path.read_bytes());period=array.array('h',(v*96 for v in src for _ in range(2)))
   check('HOME PCM source matches approved catalog hash',sha(src_path)==cue['raw_sha256'])
   rom=a.rom.read_bytes();start=sym['music_home']-0x08000000;check('ROM contains exact approved HOME PCM',rom[start:start+len(src)]==src_path.read_bytes())
   with wave.open(str(path))as w:
    rate=w.getframerate();sample_count=w.getnframes();channels=w.getnchannels();sample_width=w.getsampwidth();pcm=array.array('h',w.readframes(sample_count))
   check(name+' nonempty stereo16-bit WAV covers the measured window',rate==32768 and channels==2 and sample_width==2 and sample_count>0 and captured_samples==sample_count and len(pcm)==sample_count*2 and abs(sample_count-n*280896*32768/16777216)<=2)
   actual=pcm[::2];found=(period+period[:8192]).tobytes().find(actual[:4096].tobytes());check(name+' exact approved PCM alignment',found>=0 and found%2==0)
   offset=found//2;expected=(period*((offset+len(actual))//len(period)+1))[offset:offset+len(actual)]
   check(name+' mixed output is exact approved PCM',actual==pcm[1::2]and actual==expected)
   result['audio']={'file':path.name,'sha256':sha(path),'samples':len(actual),'source_sha256':sha(src_path),'mismatched_samples':0,'observed_approved_loop_seam':offset+len(actual)>len(period)}
  report['cases'].append(result);return result
 def goto(x=None,y=None):
  for field,target,lo,hi in(('px',x,'LEFT','RIGHT'),('py',y,'UP','DOWN')):
   if target is None:continue
   for _ in range(350):
    if abs(g(field)-target)<=1:break
    step(1,lo if g(field)>target else hi)
   else:raise AssertionError('blocked controller route')
  step(8)
 try:
  session='blank-cartridge';e=lib.eb_open(str(a.rom.resolve()).encode());assert e
  step(160);check('cold title',g('game_state')==0);irq_check();tap('A');check('new opening',g('game_state')==14);tap('START');wait_play();step(120)
  window('village-idle',600,exact_audio=True)
  r=window('village-left-right',control=lambda i:'LEFT'if i%80<40 else'RIGHT',exact_audio=True);check('actual fixed-camera walking',r['unique_positions']>30 and r['unique_cameras']==1)
  r=window('village-facing-alternating',control=lambda i:'LEFT'if i%2==0 else'RIGHT',exact_audio=True);check('alternating direction really runs',r['unique_positions']==2 and r['unique_cameras']==1 and r['faces']==[2,3])
  check('at least one exact village capture crosses approved HOME loop seam',any(c.get('audio',{}).get('observed_approved_loop_seam')for c in report['cases']))
  goto(x=120,y=55)
  for _ in range(200):
   if g('room')==1:break
   step(1,'UP','edge-transition',True)
  check('controller enters scrolling river',g('room')==1);step(120)
  r=window('river-left-right-scroll',control=lambda i:'RIGHT'if i%80<40 else'LEFT');check('actual camera scrolling',r['unique_positions']>30 and r['unique_cameras']>20)
  lib.eb_reset(e);session='reset-first-checkpoint';step(500);check('reset retains first checkpoint',g('game_state')==0 and g('has_save')==1);tap('A');wait_play();window('reset-continue',600)
  lib.eb_close(e);e=None;session='historical-continue'
  e=lib.eb_open(str(a.rom.resolve()).encode());assert e;fixture=root/'tests/fixtures/v5-revision9/covenants-all128-72-cold.sav';check('historical SRAM opens',lib.eb_load_save(e,str(fixture).encode())==1);lib.eb_reset(e);step(500);check('historical title',g('game_state')==0);tap('A');wait_play();window('historical-continue-steady',600)
  report['fixture_sha256']=sha(fixture);report['result']='PASS'
 except Exception as ex:report['result']='FAIL';report['error']=repr(ex);raise
 finally:
  if e:lib.eb_close(e)
  trace.close();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'result':report['result'],'checks':len(report['checks']),'report':str(out/'report.json')}))

if __name__=='__main__':main()
