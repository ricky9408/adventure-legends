#!/usr/bin/env python3
"""Host snapshot byte/ownership/dedup tests, including authenticated and maximum states."""
from pathlib import Path
import ctypes as C,hashlib,json,os,shlex,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_save5 import Save,compare_state
from test_return_history_differential import FIXTURES
OUT=ROOT/'build/snapshot-host';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'writer_probe.c').write_text('#include "save5.c"\nconst Save5State *test_writer_snapshot(void){return &scratch.state;}\n')
(OUT/'feedback_probe.c').write_text('#include "save_feedback.c"\nconst Save5State *test_feedback_snapshot(void){return &snapshot;}\n')
modules=['save4','creatures','creature_data','equipment','equipment_data']
so=OUT/'snapshot.so'
subprocess.run([*shlex.split(os.environ.get('HOST_CC','cc')),'-std=c99','-O3','-fstrict-aliasing','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-shared','-fPIC','-I'+str(ROOT/'src'),*[str(ROOT/'src'/f'{m}.c')for m in modules],str(OUT/'writer_probe.c'),str(OUT/'feedback_probe.c'),'-o',str(so)],check=True)
l=C.CDLL(str(so));ram=(C.c_ubyte*32768).in_dll(l,'save5_test_sram')
for n in ['save5_load','save5_begin','save5_validate','save5_preflight_begin','save_feedback_capture','save_feedback_same']:getattr(l,n).argtypes=[C.POINTER(Save)]
for n in ['test_writer_snapshot','test_feedback_snapshot']:getattr(l,n).restype=C.POINTER(Save)
inputs=[(ROOT/f'tests/fixtures/v5-revision{revision}'/n,h,'authenticated historical SRAM')for revision,n,h in FIXTURES]
for revision,name in [(7,'return-h-earned104-52.sav'),(8,'horizons-all120-64-cold.sav'),(9,'covenants-all128-72-cold.sav')]:
 provenance=json.loads((ROOT/f'tests/fixtures/v5-revision{revision}/provenance.json').read_text())
 row=next(r for r in provenance['fixtures']if (r.get('path')or r.get('file','')).endswith(name))
 inputs.append((ROOT/f'tests/fixtures/v5-revision{revision}'/name,row['sha256'],'authenticated historical SRAM'))
inputs.append((ROOT/'tests/fixtures/snapshot-copy/synthetic-full160-gear48-room43.sav','35390f2c949d75cd5dcaff6eb264bb493e869bfd7afb914c4caac124eb402494','synthetic valid full160/48 room43 state used by native controller diagnostic'))
assert C.sizeof(Save)==4976
results=[]
for index,(p,want,kind)in enumerate(inputs):
 assert sha(p)==want,('Snapshot fixture changed',str(p))
 l.save5_preflight_cancel();l.save5_test_reset_writer();ram[:]=p.read_bytes();s=Save()
 assert l.save5_load(C.byref(s))==1 and l.save5_validate(C.byref(s))==1
 expected=bytes(s);raw=(C.c_ubyte*C.sizeof(Save)).from_buffer(s)
 l.save_feedback_reset();l.save_feedback_capture(C.byref(s));assert bytes(l.test_feedback_snapshot().contents)==expected
 assert l.save_feedback_same(C.byref(s))==0;l.save_feedback_complete(1);assert l.save_feedback_same(C.byref(s))==1
 # Every byte participates in exact dedup, including runtime padding and tail.
 for offset in range(C.sizeof(Save)):
  raw[offset]^=0xff;assert l.save_feedback_same(C.byref(s))==0;raw[offset]^=0xff
 assert l.save_feedback_same(C.byref(s))==1 and bytes(l.test_feedback_snapshot().contents)==expected
 before_sram=bytes(ram);assert l.save5_begin(C.byref(s))==1
 assert bytes(l.test_writer_snapshot().contents)==expected and bytes(ram)==before_sram
 for offset in range(C.sizeof(Save)):raw[offset]^=0xff
 assert bytes(l.test_writer_snapshot().contents)==expected and bytes(l.test_feedback_snapshot().contents)==expected
 assert l.save5_begin(C.byref(s))==0 and bytes(l.test_writer_snapshot().contents)==expected
 for offset in range(C.sizeof(Save)):raw[offset]^=0xff
 l.save5_set_preemptible(1);assert l.save5_cancel_background()==1
 token=l.save5_preflight_begin(C.byref(s));assert token and bytes(l.test_writer_snapshot().contents)==expected
 assert l.save5_begin(C.byref(s))==0 and bytes(l.test_writer_snapshot().contents)==expected
 for _ in range(2000):
  status=l.save5_preflight_step(token,512)
  if status!=1:break
 assert status==2 and bytes(l.test_writer_snapshot().contents)==expected and bytes(ram)==before_sram
 l.save5_preflight_cancel();assert l.save5_begin(C.byref(s))==1
 for _ in range(2000):
  l.save5_step(192)
  if l.save5_status()!=1:break
 assert l.save5_status()==2
 out=Save();assert l.save5_load(C.byref(out))==1 and compare_state(out)==compare_state(s)
 state_path=OUT/f'state-{index:02d}.bin';state_path.write_bytes(expected)
 results.append({'input':str(p.relative_to(ROOT)),'input_sha256':want,'provenance_kind':kind,'state':str(state_path.relative_to(ROOT)),'state_sha256':sha(state_path),'roster_count':sum(bool(x.flags&1)for x in s.roster.instances),'gear_count':sum(bool(x.item_id)for x in s.equipment.bag),'byte_mutations_checked':C.sizeof(Save),'copy_feedback_and_preflight_exact':True,'mutable_source_isolated':True,'writer_and_preflight_ownership':True,'durable_roundtrip':True})
assert len(results)==13 and [results[-1]['roster_count'],results[-1]['gear_count']]==[160,48]
report={'passed':True,'state_bytes':C.sizeof(Save),'strict_aliasing':True,'fixtures':results,'source_hashes':{n:sha(ROOT/'src'/n)for n in ['save5.c','save_feedback.c','save_snapshot_copy.h']}}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'state_bytes':C.sizeof(Save),'fixtures':len(results),'dedup_byte_mutations':sum(r['byte_mutations_checked']for r in results),'max_state_counts':[results[-1]['roster_count'],results[-1]['gear_count']]}))
