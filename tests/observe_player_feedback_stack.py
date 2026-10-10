#!/usr/bin/env python3
"""Qualified startup-only stack canary replay of a passing feedback campaign.

No host game-RAM writes or machine-state imports. A copied-object control link
must reproduce the frozen production ROM, ELF and symbols byte for byte. Only
separate diagnostic startup fills reserved stacks before main. Canary extent
is an observation, not minimum SP, an exhaustive bound or production timing.
"""
from __future__ import annotations
import argparse,ctypes as C,gzip,hashlib,json,os,re,shutil,struct,subprocess,sys,traceback
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
CANARY=0xA55AC33C
RANGES={'system':(0x03007000,0x03007F00,64),'irq':(0x03007F00,0x03007FA0,16),'svc':(0x03007FA0,0x03007FE0,16)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def write(p,value):Path(p).write_text(json.dumps(value,indent=2)+'\n')
def copy(source,destination):
 destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination);assert sha(source)==sha(destination)
def symbols(path):
 rows=[v for line in Path(path).read_text().splitlines() if len(v:=line.split())==3];counts=Counter(v[2] for v in rows)
 return {v[2]:int(v[0],16) for v in rows if counts[v[2]]==1}
def build(a):
 build_root=a.build_root.resolve();out=a.diagnostic.resolve();out.mkdir(parents=True,exist_ok=False)
 pins=json.loads(a.candidate_receipt.read_text());files=('emberbond.gba','emberbond.elf','emberbond.sym','source-hashes.json')
 assert all(sha(build_root/name)==pins[name] for name in files),'Frozen production receipt mismatch'
 manifest=json.loads((build_root/'source-hashes.json').read_text());assert all(sha(ROOT/name)==value for name,value in manifest.items()),'Runtime source differs from frozen build'
 for name in files:copy(build_root/name,out/'production'/name)
 copy(a.candidate_receipt,out/'production/candidate-receipt.json')
 for name in manifest:copy(ROOT/name,out/'source'/name)
 line=re.search(r'^OBJECTS := (.+)$',(ROOT/'Makefile').read_text(),re.M).group(1)
 originals=[build_root/Path(word.replace('$(BUILD)','build')).name for word in line.split()];before={str(p):sha(p) for p in originals};objects=[]
 for source in originals:
  target=out/'objects'/source.name;copy(source,target);objects.append(target)
 original=(out/'source/src/startup.s').read_text();anchor='    ldr sp, =0x03007F00\n';assert original.count(anchor)==1
 fill=('    @ Diagnostic startup only: reserved stacks; BIOS vectors untouched.\n'
       '    ldr r1, =0x03007000\n    ldr r2, =0x03007FE0\n    ldr r3, =0xA55AC33C\n'
       '5:  cmp r1, r2\n    strlo r3, [r1], #4\n    blo 5b\n')
 startup=out/'diagnostic-input/startup.s';startup.parent.mkdir();startup.write_text(original.replace(anchor,anchor+fill))
 diagnostic_manifest=dict(manifest);diagnostic_manifest['src/startup.s']=sha(startup);assert [n for n in manifest if manifest[n]!=diagnostic_manifest[n]]==['src/startup.s'];write(out/'diagnostic-source-hashes.json',diagnostic_manifest)
 for name in ('Makefile','tools/fix_header.py'):copy(ROOT/name,out/'build-inputs'/name)
 prefix=os.environ.get('ARM_PREFIX',str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-'));cc=prefix+'gcc';cpu=['-mcpu=arm7tdmi','-mthumb-interwork'];commands=[];logs=[]
 def call(args,stdout=None):
  commands.append(list(map(str,args)));r=subprocess.run(commands[-1],cwd=ROOT,text=True,capture_output=True,check=True);logs.append(r.stdout+r.stderr)
  if stdout:Path(stdout).write_text(r.stdout)
 (out/'roms').mkdir();call([cc,*cpu,'-marm','-g','-x','assembler-with-cpp','-c',startup,'-o',out/'objects/diagnostic-startup.o'])
 for label in ('control','diagnostic'):
  target=out/'roms'/label;linked=[out/'objects/diagnostic-startup.o' if label=='diagnostic' and p.name=='startup.o' else p for p in objects]
  call([cc,*cpu,'-mthumb','-nostdlib','-Wl,-T,'+str(out/'source/linker.ld')+',-Map,'+str(target.with_suffix('.map')),*linked,'-lgcc','-o',target.with_suffix('.elf')])
  call([prefix+'objcopy','-O','binary',target.with_suffix('.elf'),target.with_suffix('.gba')]);call([sys.executable,out/'build-inputs/tools/fix_header.py',target.with_suffix('.gba')]);call([prefix+'nm','-n',target.with_suffix('.elf')],target.with_suffix('.sym'))
 for suffix in ('gba','elf','sym'):assert sha(out/'roms'/('control.'+suffix))==pins['emberbond.'+suffix],('Control relink differs',suffix)
 assert all(sha(p)==value for p,value in before.items()),'Production objects changed while linking'
 assert all(sha(ROOT/name)==value for name,value in manifest.items()),'Production sources changed while linking'
 libgcc=Path(subprocess.check_output([cc,*cpu,'-mthumb','-print-libgcc-file-name'],text=True).strip())
 receipt={'suite':'player-feedback-startup-stack-build','production':pins,'control_relink_byte_identical':True,'runtime_source_changes':['src/startup.s'],'source_manifest_sha256':sha(out/'production/source-hashes.json'),'diagnostic_manifest_sha256':sha(out/'diagnostic-source-hashes.json'),'production_object_sha256':before,'frozen_object_sha256':{str(p.relative_to(out)):sha(p) for p in objects},'roms':{label:{s:sha(out/'roms'/(label+'.'+s)) for s in ('gba','elf','sym','map')} for label in ('control','diagnostic')},'compiler':subprocess.check_output([cc,'--version'],text=True).splitlines()[0],'compiler_sha256':sha(cc),'libgcc_sha256':sha(libgcc),'commands':commands,'canary_word':hex(CANARY),'filled_range':['0x03007000','0x03007fe0'],'bios_vectors_untouched':['0x03007fe0','0x03008000'],'observer_sha256':sha(__file__)}
 write(out/'build-receipt.json',receipt);(out/'build.log').write_text('\n'.join(logs));copy(__file__,out/'build-inputs/observe_player_feedback_stack.py');print('PASS byte-identical production control; separate startup-only diagnostic built',flush=True)
def run(a):
 from player_feedback_native import Native
 from test_save5 import Save
 class ReadOnly(Native):
  def write(self,*args,**kwargs):raise AssertionError('Host game-RAM writes forbidden')
  def state(self,*args,**kwargs):raise AssertionError('Machine-state APIs forbidden')
 diag=a.diagnostic.resolve();receipt=json.loads((diag/'build-receipt.json').read_text());pins=receipt['production']
 assert receipt['control_relink_byte_identical'] and receipt['runtime_source_changes']==['src/startup.s']
 assert all(sha(diag/'roms'/(label+'.'+s))==value for label,parts in receipt['roms'].items() for s,value in parts.items())
 producer=a.producer_report.resolve();assert sha(producer)==a.expected_producer_sha;p=json.loads(producer.read_text());root=producer.parent
 assert p['suite']=='player-feedback-fresh-campaign-and-earned-evolution' and p['controller_only'] and p['route_complete'] and p['native_cadence_passed'] and not p['failures']
 assert p['game_ram_writes']==p['machine_state_imports']==0 and not p['synthetic_progression']
 assert all(p['native_observation'][k]==0 for k in ('update_misses','flip_misses','cycle_overruns','faults'))
 assert p['native_observation'].get('publication_spills',0)==0
 for key,name in [('rom_sha256','emberbond.gba'),('elf_sha256','emberbond.elf'),('symbols_sha256','emberbond.sym'),('source_manifest_sha256','source-hashes.json')]:assert p['candidate'][key]==pins[name],key
 inputs_path=root/'controller-inputs.json.gz';assert sha(inputs_path)==p['input_trace_sha256'];inputs=json.load(gzip.open(inputs_path,'rt'));bridge=root/'bridge.so';assert sha(bridge)==p['candidate']['bridge_sha256']
 producer_sources=json.loads((root/'producer-source-receipt.json').read_text());assert producer_sources['candidate']==p['candidate'];assert all(sha(root/'test-source'/name)==value for name,value in producer_sources['sources'].items())
 assert sha(root/'test-source/tests/player_feedback_campaign.py')==p['candidate']['helper_sha256']
 bridge_receipt=json.loads((root/'bridge-build-context.json').read_text());assert bridge_receipt['bridge_sha256']==sha(bridge);assert all(sha(root/'bridge-source'/name)==value for name,value in bridge_receipt['sources'].items())
 assert sha(root/'candidate-source-hashes.json')==pins['source-hashes.json']
 expected_handoff=p['checkpoints']['controller-complete']['sram_sha256'];assert sha(root/'controller-complete.sav')==expected_handoff
 expected_final=p['checkpoints']['controller-complete-cold']['sram_sha256'];assert sha(root/'controller-complete-cold.sav')==expected_final
 sessions=[]
 for row in inputs:
  assert isinstance(row['frames'],int) and row['frames']>0 and 0<=row['keys']<=1023 and not(row['keys']&4)
  if not sessions or sessions[-1]!=row['session']:sessions.append(row['session'])
 assert sessions==[0,1],'Only authenticated new-game then own-SRAM Continue sessions are supported'
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);(out/'sram').mkdir()
 for source,name in [(producer,'producer-report.json'),(inputs_path,'controller-inputs.json.gz'),(bridge,'bridge.so'),(root/'producer-source-receipt.json','producer-source-receipt.json'),(root/'bridge-build-context.json','bridge-build-context.json')]:copy(source,out/name)
 for folder in ('test-source','bridge-source'):
  for source in (root/folder).rglob('*'):
   if source.is_file():copy(source,out/'producer-source'/source.relative_to(root))
 helper_hashes={}
 for module in tuple(sys.modules.values()):
  name=getattr(module,'__file__',None)
  if name and Path(name).is_file() and Path(name).resolve().is_relative_to(ROOT):
   source=Path(name).resolve();relative=source.relative_to(ROOT);target=out/'observer-source'/relative;copy(source,target);helper_hashes[str(relative)]=sha(target)
 # Resolve the library actually selected by this exact bridge, not a guessed version.
 dependencies=subprocess.check_output(['ldd',str(bridge)],text=True);(out/'bridge-dependencies.txt').write_text(dependencies)
 match=re.search(r'libmgba[^ ]*\s+=>\s+(\S+)',dependencies);assert match,'Bridge did not resolve libmgba';library=Path(match.group(1)).resolve();copy(library,out/'observer-source/libmgba.so');helper_hashes['libmgba.so']=sha(library);write(out/'observer-source-hashes.json',helper_hashes)
 syms={label:symbols(diag/'roms'/(label+'.sym')) for label in ('control','diagnostic')};save_size=C.sizeof(Save)
 # STT_OBJECT size proves that current host structure spans the complete target Save.
 def object_size(path,name):
  raw=path.read_bytes();h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw);sections=[struct.unpack_from('<IIIIIIIIII',raw,h[6]+i*h[11]) for i in range(h[12])];found=[]
  for section in sections:
   if section[1]!=2:continue
   strings=sections[section[6]];strings=raw[strings[4]:strings[4]+strings[5]]
   for pos in range(section[4],section[4]+section[5],section[9]):
    ni,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,pos)
    if strings[ni:].split(b'\0',1)[0].decode()==name and info&15==1:found.append(size)
  assert len(found)==1;return found[0]
 assert all(object_size(diag/'roms'/(tag+'.elf'),'adventure_save')==save_size for tag in syms)
 emus={};observations=[];resets=[];failures=[];total=0;session=0;last_sample=-999
 result={'suite':'player-feedback-qualified-startup-stack-replay','finished':False,'controller_only':True,'host_game_ram_writes':0,'machine_state_imports':0,'diagnostic_startup_canary_writes':True,'diagnostic_timing_is_release_evidence':False,'physical_hardware_tested':False,'build_receipt_sha256':sha(diag/'build-receipt.json'),'producer_report_sha256':sha(producer),'producer_input_sha256':sha(inputs_path),'producer_bridge_sha256':sha(bridge),'producer_source_receipt_sha256':sha(root/'producer-source-receipt.json'),'production':pins,'current_save5_bytes':save_size,'observations':observations,'session_resets':resets,'failures':failures,'limitations':['Overwritten canary extent is not true minimum SP; unwritten allocated bytes or writes equal to the canary are invisible.','Finite route coverage is not an exhaustive stack bound or physical-hardware proof.','Only reserved SYSTEM/IRQ/SVC stacks are filled before main; BIOS vector bytes remain untouched.','Pairing compares pointer-free gameplay fields, complete current Save5 and ordinary SRAM, not the whole machine state.','Startup instrumentation and code relocation cannot establish production timing acceptance.']}
 fields=('frame','game_state','room','px','py','hp','max_hp','chapter_flags','room_flags','checkpoint_spawn','journal_tab','save_failed','summoned','ability_cd','spirit','save_requested','save_feedback_background','progression_revision','gear_menu_revision','scene_present_phase','presented_transition','scene_actor_pending')
 fields=tuple(n for n in fields if all(n in syms[tag] for tag in syms))
 def record():write(out/'stack-observations.json',result)
 def words(e,address,n):assert n%4==0;return b''.join(struct.pack('<I',e.read(address+i,4)) for i in range(0,n,4))
 def values(label):return {n:emus[label].read(syms[label][n]) for n in fields}
 def open_pair(paths=None):
  for tag in syms:
   e=ReadOnly(diag/'roms'/(tag+'.gba'),out/'bridge.so')
   if paths:e.load_save(paths[tag]);e.reset()
   emus[tag]=e
 def observe(label):
  nonlocal last_sample
  e=emus['diagnostic'];ranges={}
  for name,(bottom,top,guard) in RANGES.items():
   vals=struct.unpack('<'+'I'*((top-bottom)//4),words(e,bottom,top-bottom));changed=[i for i,v in enumerate(vals) if v!=CANARY];lowest=bottom+4*min(changed) if changed else top
   ranges[name]={'range':[hex(bottom),hex(top)],'reserved_bytes':top-bottom,'lowest_overwritten_word':hex(lowest),'overwritten_extent_bytes':top-lowest,'changed_word_bytes':4*len(changed),'unmodified_prefix_bytes':lowest-bottom,'bottom_guard_bytes':guard,'bottom_guard_intact':all(v==CANARY for v in vals[:guard//4]),'true_minimum_sp':'not measured'}
  state={tag:words(e,syms[tag]['adventure_save'],save_size) for tag,e in emus.items()};blobs={};paths={}
  for tag,e in emus.items():
   path=out/'sram'/('%04d-%s.sav'%(len(observations),tag));e.save(path);paths[tag]=str(path);blobs[tag]=path.read_bytes();assert len(blobs[tag])==32768
  paired={'fields':values('control'),'diagnostic_fields':values('diagnostic'),'adventure_save_sha256':{k:digest(v) for k,v in state.items()},'sram_sha256':{k:digest(v) for k,v in blobs.items()},'sram_paths':paths};paired.update(fields_equal=paired['fields']==paired['diagnostic_fields'],adventure_save_equal=state['control']==state['diagnostic'],sram_equal=blobs['control']==blobs['diagnostic'])
  observations.append({'label':label,'session':session,'total_hardware_frames':total,'hardware_frame':e.frame,'stacks':ranges,'paired':paired});last_sample=total;record()
  assert all(r['bottom_guard_intact'] for r in ranges.values()),'A sampled stack bottom guard was overwritten'
  assert paired['fields_equal'] and paired['adventure_save_equal'] and paired['sram_equal'],'Paired gameplay or SRAM diverged';return paths
 try:
  open_pair()
  for index,row in enumerate(inputs):
   if row['session']!=session:
    assert session==0 and row['session']==1 and row['emulator_frame']==0
    paths=observe('before-own-SRAM-Continue');assert all(sha(path)==expected_handoff for path in paths.values()),'Session0 SRAM differs from producer handoff'
    resets.append({'input_index':index,'from_session':session,'source_sram':paths,'source_sha256':expected_handoff})
    for e in emus.values():e.close()
    session=1;open_pair(paths)
   assert all(e.frame==row['emulator_frame'] for e in emus.values()),('Input frame discontinuity',index,row)
   for e in emus.values():e.frames(row['frames'],row['keys'])
   total+=row['frames'];control,diagnostic=values('control'),values('diagnostic')
   assert all(e.lib.eb_faults(e.ptr)==0 for e in emus.values()),'mGBA core/log fault'
   active=control['frame'] and diagnostic['frame'] and control['game_state']!=0 and diagnostic['game_state']!=0
   if active:
    assert control==diagnostic,('Paired fields differ after input batch',index,control,diagnostic)
    if total-last_sample>=a.sample_frames:observe('input-'+str(index))
  paths=observe('finished-own-SRAM-Continue');assert all(sha(path)==expected_final for path in paths.values()),'Final SRAM differs from producer'
  result.update(finished=True,all_sampled_bottom_guards_intact=True,paired_samples_equal=True,final_sram_matches_producer=True,input_batches=len(inputs),hardware_frames_per_rom=total,cold_sessions=2,maximum_overwritten_extent={name:max(row['stacks'][name]['overwritten_extent_bytes'] for row in observations) for name in RANGES})
  assert all(sha(out/'observer-source'/name)==value for name,value in helper_hashes.items());assert sha(producer)==a.expected_producer_sha and sha(inputs_path)==p['input_trace_sha256'] and sha(bridge)==p['candidate']['bridge_sha256']
 except Exception as exc:failures.append({'error':str(exc),'traceback':traceback.format_exc(),'hardware_frames':total,'session':session});raise
 finally:
  record()
  for e in emus.values():e.close()
 print(json.dumps({'extent':result['maximum_overwritten_extent'],'paired_samples':len(observations),'sessions':2,'hardware_frames_per_rom':total}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
 b=sub.add_parser('build');b.add_argument('--candidate-receipt',type=Path,required=True);b.add_argument('--build-root',type=Path,default=ROOT/'build');b.add_argument('--diagnostic',type=Path,required=True)
 r=sub.add_parser('run');r.add_argument('--diagnostic',type=Path,required=True);r.add_argument('--producer-report',type=Path,required=True);r.add_argument('--expected-producer-sha',required=True);r.add_argument('--output',type=Path,required=True);r.add_argument('--sample-frames',type=int,default=120)
 args=p.parse_args();build(args) if args.action=='build' else run(args)
