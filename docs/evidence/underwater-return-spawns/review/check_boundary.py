#!/usr/bin/env python3
"""Independent before/after source-locked return-spawn acceptance delta."""
import ctypes as C,hashlib,json,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tests'))
from test_underwater_save import build,prepare,runtime_hashes,FIXTURE,FIXTURE_SHA
from test_underwater_transactions import configure
from test_save5 import Save,Roster,A,B,SIZE,repair_crc,compare_state
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def custom_build(folder,sources):
 out=folder/'before.so';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wstrict-aliasing=2','-fstrict-aliasing','-ffreestanding','-fno-builtin','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-shared','-fPIC','-I'+str(ROOT/'src'),'-I'+str(folder),*[str(p) for p in sources.values()],str(ROOT/'tests/underwater_save_setup.c'),'-o',str(out)],check=True)
 lib=C.CDLL(str(out));lib.save5_validate.argtypes=[C.POINTER(Save)];lib.save5_validate_revision.argtypes=[C.POINTER(Save),C.c_uint];return lib
before_hashes=runtime_hashes();prior=json.loads((ROOT/'docs/evidence/underwater-transaction-review/manifest.json').read_text())['runtime_source_hashes']
changed=[p for p in before_hashes if before_hashes[p]!=prior[p]];assert changed==['src/save5.c','src/save5_underwater_policy.h'],changed
assert sha(FIXTURE)==FIXTURE_SHA
counts={'all_room_spawn_pairs':0,'anchor_variants':0,'preflight_checks':0,'raw_bank_checks':0,'newly_accepted':0,'gate_denials':0};start=time.monotonic()
with tempfile.TemporaryDirectory(prefix='independent-return-boundary-') as td:
 td=Path(td);oldsrc=td/'oldsrc';(oldsrc/'src').mkdir(parents=True)
 for p in changed:(oldsrc/p).write_bytes((ROOT/p).read_bytes())
 patch=(ROOT/'docs/evidence/underwater-return-spawns/codec.diff').read_bytes()
 subprocess.run(['patch','--batch','-R','-p1','-d',str(oldsrc)],input=patch,check=True,stdout=subprocess.PIPE)
 for p in changed:assert sha(oldsrc/p)==prior[p],p
 sources=prepare(td/'old');sources['save5']=oldsrc/'src/save5.c';old=custom_build(td/'old',sources)
 new=configure(build(td/'new'));base=Save();assert not new.underwater_test_completed(C.byref(base),0)
 base.quests.anchors[3]=3;base.quests.anchors[4]=3;assert new.save5_validate(C.byref(base))==1
 assert new.save5_store(C.byref(base))==1
 offset=max((A,B),key=lambda p:int.from_bytes(bytes(new.sram[p+8:p+12]),'little'));template=bytes(new.sram[offset:offset+SIZE])
 expected_new={(38,4),(46,3),(48,2),(51,2),(52,2)};actual_new=set()
 def preflight(s,wanted):
  token=new.save5_preflight_begin(C.byref(s));assert token
  for _ in range(300):
   status=new.save5_preflight_step(token,640)
   if status!=1:break
  assert status==(2 if wanted else 3);new.save5_preflight_cancel();counts['preflight_checks']+=1
 def raw(s,wanted):
  # Direct wire mutation of known complete template; no candidate encoder dependency.
  wire=bytearray(template);wire[32]=s.campaign.room;wire[33]=s.campaign.spawn
  wire[4032:4048]=bytes(s.quests.states);wire[4048:4176]=b''.join(v.to_bytes(2,'little') for v in s.quests.objectives)
  wire[4176:4184]=bytes(s.quests.rewards);wire[4248:4280]=bytes(s.quests.region_flags);wire[4280:4296]=bytes(s.quests.anchors)
  wire=bytes(repair_crc(wire))
  for dst in (A,B):
   new.save5_test_reset_writer();new.sram[:]=bytes([255])*32768;new.sram[dst:dst+SIZE]=wire
   sram=bytes(new.sram);out=Save.from_buffer_copy(bytes([0x91])*C.sizeof(Save));untouched=bytes(out)
   assert new.save5_load(C.byref(out))==wanted,(s.campaign.room,s.campaign.spawn,dst)
   if wanted:assert compare_state(out)==compare_state(s)
   else:assert bytes(out)==untouched
   assert bytes(new.sram)==sram;counts['raw_bank_checks']+=1
 for room in range(256):
  for spawn in range(256):
   s=Save.from_buffer_copy(bytes(base));s.campaign.room=room;s.campaign.spawn=spawn
   before=old.save5_validate(C.byref(s));after=new.save5_validate(C.byref(s));assert old.save5_validate_revision(C.byref(s),6)==before
   assert new.save5_validate_revision(C.byref(s),6)==after,(room,spawn)
   assert after==before or (not before and after and (room,spawn) in expected_new),(room,spawn,before,after)
   if after!=before:actual_new.add((room,spawn));counts['newly_accepted']+=1
   if room>=38:preflight(s,after)
   counts['all_room_spawn_pairs']+=1
 assert actual_new==expected_new
 for anchor3 in range(4):
  for anchor4 in range(4):
   for room in range(38,54):
    for spawn in range(6):
     s=Save.from_buffer_copy(bytes(base));s.quests.anchors[3]=anchor3;s.quests.anchors[4]=anchor4;s.campaign.room=room;s.campaign.spawn=spawn
     after=new.save5_validate(C.byref(s));before=old.save5_validate(C.byref(s));want=(room,spawn) in expected_new or bool(before)
     assert after==int(want),(room,spawn,anchor3,anchor4,before,after)
     assert new.save5_validate_revision(C.byref(s),6)==after;preflight(s,after);raw(s,after);counts['anchor_variants']+=1
 # Every new landing still needs its actual visit, and room38:4 cannot use Magma anchors as a substitute.
 for room,spawn in sorted(expected_new):
  s=Save.from_buffer_copy(bytes(base));s.campaign.room=room;s.campaign.spawn=spawn
  s.quests.region_flags[4]&=~(1 if room==38 else 1<<(room-46))
  assert not new.save5_validate(C.byref(s));assert not new.save5_validate_revision(C.byref(s),6);preflight(s,0);raw(s,0);counts['gate_denials']+=1
 # Isolate the new 38:4 town gate on minimal native34, without later quest dependencies.
 complete_template=template
 minimal=Save();assert not new.underwater_test_earned34(C.byref(minimal));minimal.quests.anchors[3]=0;minimal.campaign.room=38;minimal.campaign.spawn=0
 assert new.save5_store(C.byref(minimal))==1
 offset=max((A,B),key=lambda p:int.from_bytes(bytes(new.sram[p+8:p+12]),'little'));template=bytes(new.sram[offset:offset+SIZE])
 minimal.campaign.room=38;minimal.campaign.spawn=4
 assert not new.save5_validate(C.byref(minimal));preflight(minimal,0);raw(minimal,0);counts['gate_denials']+=1
 minimal.campaign.spawn=0;assert new.underwater_visit(C.byref(minimal),46)==1;minimal.campaign.spawn=4
 assert new.save5_validate(C.byref(minimal))==1;assert new.save5_validate_revision(C.byref(minimal),6)==1
 assert old.save5_validate(C.byref(minimal))==0;preflight(minimal,1);raw(minimal,1)
 template=complete_template
 # Exhaustively preserve old r5 Magma mask semantics on authenticated old state.
 historical=Save();assert not new.underwater_test_earned34(C.byref(historical));historical.quests.anchors[3]=3
 for room in range(38,46):
  for spawn in range(256):
   historical.campaign.room=room;historical.campaign.spawn=spawn
   for revision in range(1,6):
    assert old.save5_validate_revision(C.byref(historical),revision)==new.save5_validate_revision(C.byref(historical),revision)
 assert before_hashes==runtime_hashes()
 report={'status':'pass','scope':'independent host current-r6 return-spawn boundary; no native geometry or pacing claim','only_runtime_files_changed_since_prior_review':changed,'prior_runtime_source_hashes':{p:prior[p] for p in changed},'source_hashes':before_hashes,'counts':counts,'old_r1_to_r5_typed_magma_matrix':10240,'new_landings':sorted(actual_new),'fixture_sha256':FIXTURE_SHA,'test_sha256':sha(__file__),'seconds':time.monotonic()-start}
 (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(counts,sort_keys=True));print('PASS: exact five new current-r6 returns; all other room/spawn acceptance unchanged')
