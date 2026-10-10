#!/usr/bin/env python3
"""Compare completed native render outputs, not asynchronous LCD scanout.
Both ROMs replay identical authenticated SRAM/buttons; each observer run must
match a same-ROM normal runFrame control's full serialized end state.
"""
import argparse,ctypes as C,hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator,keymask
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(exist_ok=False,parents=True);d=json.loads(a.report.read_text());commands={}
for v in d['inputs']:
 for f in range(v['frame'],min(a.end,v['frame']+v['frames'])):commands[f]=v['keys']
 if v['frame']+v['frames']>=a.end:break
c=(ROOT/'tests/return_stall_observer.c').read_text();c=c.replace('struct SessionPrefix {', 'static void capture(struct mCore *);\nstruct SessionPrefix {').replace('if(p->address==render_address&&loop_active){','if(p->address==render_address)capture(core);\n    if(p->address==render_address&&loop_active){')
c+='''
static FILE *capture_file;static uint32_t capture_addresses[4];
void capture_open(const char*path,const uint32_t*a){capture_file=fopen(path,"wb");memcpy(capture_addresses,a,sizeof capture_addresses);}
void capture_close(void){if(capture_file)fclose(capture_file);capture_file=0;}
static void block(struct mCore*c,uint32_t address,unsigned n){for(unsigned i=0;i<n;i+=4){uint32_t v=c->busRead32(c,address+i);fwrite(&v,4,1,capture_file);}}
static void capture(struct mCore*c){if(!capture_file)return;uint32_t frame=c->busRead32(c,capture_addresses[0]),screen=c->busRead32(c,capture_addresses[1]),count=c->busRead32(c,capture_addresses[3]),hw=c->frameCounter(c);if(count>128)abort();fwrite(&frame,4,1,capture_file);fwrite(&count,4,1,capture_file);fwrite(&hw,4,1,capture_file);block(c,screen,38400);block(c,0x06014000,16384);block(c,0x05000000,1024);block(c,capture_addresses[2],count*8);}
'''
cf=out/'render-observer.c';cf.write_text(c);so=out/'observer.so';sysroot=ROOT/'tools/sysroot/usr';subprocess.run(['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(cf),'-I'+str(sysroot/'include'),'-L'+str(sysroot/'lib/x86_64-linux-gnu'),'-Wl,-rpath,'+str((sysroot/'lib/x86_64-linux-gnu').resolve()),'-lmgba','-o',str(so)],check=True)
l=C.CDLL(str(so));ptr=C.POINTER(C.c_uint32);l.return_profile_reset.argtypes=[ptr,C.c_uint,ptr,ptr,C.c_uint];l.return_profile_frames.argtypes=[C.c_void_p,C.c_uint,C.c_uint];l.return_loop_config.argtypes=[C.c_uint32,C.c_uint32];l.return_state_save.argtypes=[C.c_void_p,C.c_char_p];l.capture_open.argtypes=[C.c_char_p,ptr];arr=lambda v:(C.c_uint32*len(v))(*v)
results={}
for label,src in [('B',Path(d['source_root'])),('patched',a.candidate.resolve())]:
 folder=out/label;folder.mkdir();rom=src/'build/emberbond.gba';syms={s[2]:int(s[0],16)for line in rom.with_suffix('.sym').read_text().splitlines()if len(s:=line.split())==3};start=folder/'start.state';save=folder/'start.sav'
 with Emulator(rom)as e:
  e.load_save(d['provenance']['fixture_path']);e.reset()
  for v in d['inputs']:
   if v['frame']>=a.start:break
   assert e.frame==v['frame'];e.frames(min(v['frames'],a.start-e.frame),v['keys'])
  assert l.return_state_save(e.ptr,str(start).encode());save.write_bytes(e.bytes(0x0e000000,32768))
 for observer in (True,False):
  with Emulator(rom)as e:
   e.load_save(save);e.state(start,True)
   if observer:l.return_profile_reset(arr([syms['render']]),1,arr([]),arr([]),0);l.return_loop_config(0,syms['render']);l.capture_open(str(folder/'render.bin').encode(),arr([syms[n]for n in ['frame','screen','obj_entries','obj_count']]))
   for f in range(a.start,a.end):
    if observer:l.return_profile_frames(e.ptr,1,keymask(commands[f]))
    else:e.frames(1,commands[f])
   if observer:l.capture_close()
   assert l.return_state_save(e.ptr,str(folder/('observed.state'if observer else 'normal.state')).encode())
 assert (folder/'observed.state').read_bytes()==(folder/'normal.state').read_bytes(),'observer changed emulated execution'
 raw=(folder/'render.bin').read_bytes();off=0;rows={}
 while off<len(raw):
  frame,count,hw=struct.unpack_from('<III',raw,off);off+=12;size=38400+16384+1024+count*8;payload=raw[off:off+size];off+=size;assert len(payload)==size;rows[frame]={'hardware_frame':hw,'obj_count':count,'payload_sha256':hashlib.sha256(payload).hexdigest(),'bitmap_sha256':hashlib.sha256(payload[:38400]).hexdigest(),'tiles_sha256':hashlib.sha256(payload[38400:54784]).hexdigest(),'palette_sha256':hashlib.sha256(payload[54784:55808]).hexdigest(),'objects_sha256':hashlib.sha256(payload[55808:]).hexdigest()}
 results[label]={'rom_sha256':sha(rom),'serialized_control_equal':True,'state_sha256':sha(folder/'normal.state'),'rows':rows}
L=results['B']['rows'];R=results['patched']['rows'];frames=sorted(L.keys()&R.keys());diff=[dict(frame=f,baseline=L[f],patched=R[f])for f in frames if L[f]['payload_sha256']!=R[f]['payload_sha256']];report={'scope':'completed render bitmap, OBJ tile pixels, palette, ordered OBJ descriptors at matched logical update; exact same-ROM serialized observer/control equality','game_ram_writes':0,'cross_ROM_machine_state_loads':0,'source_report_sha256':sha(a.report),'script_sha256':sha(__file__),'observer_source_sha256':sha(cf),'matched_renders':len(frames),'differences':diff,'results':results};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'matched_renders':len(frames),'differences':diff},indent=2));assert not diff
