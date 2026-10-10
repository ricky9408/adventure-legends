#!/usr/bin/env python3
"""Explicit content9 retained-test adapter. Historical helpers/oracles remain intact.

Runtime/assets/docs and unchanged fixtures use verified immutable byte+mode CAS.
Editable helpers are independent copies. Only current header/link/cache contracts
change; gameplay, payload, cadence and historical fixture assertions remain.
Preparation is not test acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,sys
import prepare_retained_native_adapter as prior
from run_covenants_native import frozen_copy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from retained_horizons_cache import FIELDS as HORIZONS_FIELDS
from retained_boundary_core import include_closure
MODULES=['horizons_game','horizons_art','horizons_quests','horizons_creature_art','horizons_powers','horizons_power_art','horizons_audio','covenants_game','covenants_art','covenants_quests','covenants_creature_art','covenants_powers','covenants_power_art','story_rewards']
FILES=['tests/test_save_feedback.py']+['tests/underwater_engine_review/'+n for n in ('test_legacy_deferred_anchor_linked.py','test_legacy_deferred_anchor_current.py','test_engine_lifecycle.py','test_bounded_magma_return.py','test_bounded_southern_rest.py','test_bounded_magma_save_current.py')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare(frozen,out):
 manifest=frozen/'candidate/source-hashes.json';runtime=json.loads(manifest.read_text());runtime_root=frozen/'runtime-source';candidate=frozen/'candidate'
 assert 'SAVE5_CONTENT_REVISION = 9,'in(runtime_root/'src/save5.h').read_text()
 assert all(sha(runtime_root/n)==h for n,h in runtime.items())
 out.mkdir(parents=True,exist_ok=False);src=out/'source';src.mkdir();changes={};copied=[];linked=[]
 for name,digest in runtime.items():frozen_copy(runtime_root/name,src/name);assert sha(src/name)==digest;linked.append(name)
 for directory in ('tests','assets','tools','docs'):
  base=ROOT/directory
  for path in sorted(base.rglob('*')):
   relative=path.relative_to(ROOT)
   if '__pycache__'in path.parts or path.suffix=='.pyc':continue
   dest=src/relative
   if path.is_symlink():dest.parent.mkdir(parents=True,exist_ok=True);dest.symlink_to(path.readlink());continue
   if not path.is_file():continue
   editable=directory in ('tests','tools') and path.suffix in ('.py','.c','.h','.s','.inc','.json') and 'fixtures'not in path.parts and 'oracles'not in path.parts
   if editable:dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest);copied.append(str(relative))
   else:frozen_copy(path,dest);linked.append(str(relative))
 for name in ('Makefile','README.md','LICENSE'):
  shutil.copyfile(ROOT/name,src/name);copied.append(name)
 for name in ('emberbond.gba','emberbond.sym','emberbond.elf','source-hashes.json'):frozen_copy(candidate/name,src/'build'/name)
 def edit(name,pairs,why):
  path=src/name;assert path.stat().st_nlink==1,('Refusing to edit shared helper',name);text=path.read_text();before=sha(path)
  for old,new in pairs:
   assert text.count(old)==1,(name,old,text.count(old));text=text.replace(old,new,1)
  path.write_text(text);row=changes.setdefault(name,{'original_sha256':sha(ROOT/name),'edits':[]});row['adapted_sha256']=sha(path);row['edits'].append({'prior_sha256':before,'reason':why,'replacements':[{'before':x,'after':y}for x,y in pairs]})
 for name,pairs in prior.SUBSTITUTIONS.items():
  edit(name,[(old,new.replace('7','9'))for old,new in pairs],'Current writer header9 only; historical fixture/payload checks preserved')
 for name,(marker,revision,old,current,before,after)in prior.MIGRATIONS.items():
  addition="        from retained_migration_validator import validate_migration\n"+f"        self.check(validate_migration({old},{current},{before},{after},{revision}),'independent wire5 migration verifies prior header, current9 CRC, exact payload and preserved source bank')\n"
  edit(name,[(marker,addition+marker)],'Additional independent read-only migration assertion')
 edit('tests/retained_migration_validator.py',[("prior_revision in (3,4,5,6)","prior_revision in (3,4,5,6,7,8)"),("validate_bank(current_bank,7)","validate_bank(current_bank,9)")],'Explicit same-wire5 prior3..8 to current9; exact CRC/payload/prior-bank checks unchanged')
 edit('tests/return_journey.py',[("int.from_bytes(bank[12:14], 'little') == 7","int.from_bytes(bank[12:14], 'little') == 9"),('ordinary Continue commits content revision7','ordinary Continue commits content revision9'),('revision6 to7 preserves every durable payload byte','revision6 to9 preserves every durable payload byte'),("self.snapshot('00-revision7-exact-migration')","self.snapshot('00-revision9-exact-migration')")],'Explicit Return current-writer contract9; historical source and gameplay unchanged')
 edit('tests/return_companion_controls.py',[("int.from_bytes(b[12:14],'little')==7","int.from_bytes(b[12:14],'little')==9")],'Same-candidate follow-up controls consume exact current9 saves')
 edit('tests/playthrough.py',[("if self.get('game_state')!=6:break","if self.get('game_state') not in (6,10):break")],'Drain explicit bounded story EVENT_PENDING as well as SAVE_PENDING; original180-frame bound and every gameplay assertion retained')
 edit('tests/exploration_tests.py',[("if self.get('game_state')!=6 and not (self.get('game_state')==PLAY and self.get('frame')==0):break","if self.get('game_state') not in (6,10) and not (self.get('game_state')==PLAY and self.get('frame')==0):break"),("'reason':'SAVE_PENDING' if self.get('game_state')==6 else 'COLD_CONTINUE'","'reason':'EVENT_PENDING' if self.get('game_state')==10 else 'SAVE_PENDING' if self.get('game_state')==6 else 'COLD_CONTINUE'")],'Record/drain new explicit reward preparation; preserve all original gameplay/save/page-flip assertions and wait bound')
 paths=src/'tools/underwater_observer_paths.json';names=json.loads(paths.read_text());before=sha(paths);paths.write_text(json.dumps(sorted(set(names)|{'tests/retained_migration_validator.py'}),indent=2)+'\n');changes[str(paths.relative_to(src))]={'original_sha256':before,'adapted_sha256':sha(paths),'reason':'Include independent migration observer in copied closure'}
 for name in FILES:
  if name.endswith('test_save_feedback.py'):
   marker='    subprocess.run(shlex.split(';linkage='    modules += '+repr(MODULES)+'\n';source="*[str(ROOT/'src'/(n+'.c')) for n in modules]";replacement="str(ROOT/'tests/retained_host_audio.c'),'-I'+str(ROOT/'src'),"+source
  else:
   marker="RESULT={'scope':";linkage='MODULES += '+repr(MODULES)+'\n';base='ROOT'if name.endswith('test_legacy_deferred_anchor_linked.py')else'SOURCE_ROOT';source="*[str("+base+"/'src'/f'{n}.c') for n in MODULES]";replacement="str(ROOT/'tests/retained_host_audio.c'),"+source
  edit(name,[(marker,linkage+marker),("'-DGAME_HOST_TEST'","'-DGAME_HOST_TEST','-DHORIZONS_AUDIO_HOST'"),(source,replacement)],'Link complete real current engine and existing audio host mock; no audio/native timing claim')
  if not name.endswith('test_save_feedback.py'):
   edit(name,[("assert CACHE_FIELD_COUNT in (32,34),'Retained indices require an explicit adapter for any other layout'","from retained_covenants_cache import verify_cache_layout\nRESULT['cache_layout_contract']=verify_cache_layout("+base+",CACHE_FIELD_COUNT)")],'Exact pinned38-field layout, unchanged original36-field prefix and full two-page comparisons')
 edit('tests/retained_host_audio.c',[('int music_tick,music_step;','int music_tick,music_step;\nunsigned short horizons_audio_host_registers[128];')],'Inert guarded PSG2 registers only, no audio claim')
 fields=HORIZONS_FIELDS+['covenants_game_revision','game_state==PLAY?covenants_powers_hint():0'];game=(src/'src/game.c').read_text();assert re.search(r'u32 key\[CACHE_FIELDS\]=\{([^}]+)\}',game)[1].split(',')==fields
 cache='''"""Pinned content9 full-page cache observer; no production replacement."""\nimport hashlib,re\nGAME_SHA256='''+repr(runtime['src/game.c'])+'\nFIELDS='+repr(fields)+'''\ndef verify_cache_layout(root,count):
 p=root/'src/game.c';assert hashlib.sha256(p.read_bytes()).hexdigest()==GAME_SHA256
 assert 'SAVE5_CONTENT_REVISION = 9,'in(root/'src/save5.h').read_text()
 match=re.search(r'u32 key\\[CACHE_FIELDS\\]=\\{([^}]+)\\}',p.read_text());assert match and match[1].split(',')==FIELDS
 assert count==len(FIELDS)==38
 return {'content_revision':9,'fields_per_page':38,'ordered_fields':FIELDS,'game_source_sha256':GAME_SHA256,'unchanged_horizons_prefix_fields':36,'unchanged_return_prefix_fields':34,'view_scope':'All38 fields on both real production pages; gameplay and byte comparisons unchanged'}
''';(src/'tests/retained_covenants_cache.py').write_text(cache)
 old_contract=json.loads((ROOT/'tests/retained_boundary_content8_core.json').read_text());contract={'content_revision':9,'scope':'Frozen historical boundary algorithms and current bounded algorithms share this exact pinned content9 core. No historical/current core equivalence claim.','candidate_rom_sha256':sha(candidate/'emberbond.gba'),'candidate_source_manifest_sha256':sha(manifest),'contracts':{}}
 for name,old in old_contract['contracts'].items():
  current=include_closure(src,old['modules']);historical=json.loads((src/old['frozen_core_manifest']).read_text())
  if name!='magma':historical={p:historical[p]for p in current if p in historical}
  assert historical==old['frozen_core_hashes'];assert sha(src/old['frozen_core_manifest'])==old['frozen_core_manifest_sha256'];assert all(runtime[p]==h for p,h in current.items())
  contract['contracts'][name]={'modules':old['modules'],'frozen_core_manifest':old['frozen_core_manifest'],'frozen_core_manifest_sha256':old['frozen_core_manifest_sha256'],'frozen_core_hashes':historical,'current_core_hashes':current,'changed_or_added_core_files':{p:{'frozen_sha256':historical.get(p),'current_sha256':h}for p,h in current.items()if historical.get(p)!=h}}
 contract_path=src/'tests/retained_boundary_content9_core.json';contract_path.write_text(json.dumps(contract,indent=2)+'\n')
 verifier='''"""Explicit exact content9 boundary linkage contract; old oracles untouched."""\nimport hashlib,json\nfrom retained_boundary_core import include_closure\nCONTRACT_SHA256='''+repr(sha(contract_path))+'''\ndef sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_core(root,name,modules,frozen_hashes):
 p=root/'tests/retained_boundary_content9_core.json';assert sha(p)==CONTRACT_SHA256
 c=json.loads(p.read_text());item=c['contracts'][name];current=include_closure(root,modules)
 historical=dict(frozen_hashes)if name=='magma'else{p:frozen_hashes[p]for p in current if p in frozen_hashes}
 assert modules==item['modules']and historical==item['frozen_core_hashes']and current==item['current_core_hashes']
 assert sha(root/item['frozen_core_manifest'])==item['frozen_core_manifest_sha256']
 assert {p:{'frozen_sha256':historical.get(p),'current_sha256':h}for p,h in current.items()if historical.get(p)!=h}==item['changed_or_added_core_files']
 manifest=root/'build/source-hashes.json';assert sha(manifest)==c['candidate_source_manifest_sha256'];runtime=json.loads(manifest.read_text())
 assert all(runtime[p]==h for p,h in current.items())and all(sha(root/p)==h for p,h in runtime.items())
 assert sha(root/'build/emberbond.gba')==c['candidate_rom_sha256']and 'SAVE5_CONTENT_REVISION = 9,'in(root/'src/save5.h').read_text()
 return {'mode':'pinned-content9-shared-core','scope':c['scope'],'same_core_for_both_algorithms':True,'historical_core_equivalence_claimed':False,'contract_sha256':sha(p),'candidate_rom_sha256':c['candidate_rom_sha256'],'candidate_source_manifest_sha256':sha(manifest),**item}
''';(src/'tests/retained_covenants_boundary_core.py').write_text(verifier)
 for name in ['tests/test_southern_enter_job.py','tests/test_magma_boundaries.py']:edit(name,[('from retained_boundary_core import verify_core','from retained_covenants_boundary_core import verify_core')],'Use separate exact content9 shared-core contract; preserve frozen algorithm/oracles and byte comparisons')
 assert all(sha(src/n)==h for n,h in runtime.items());assert all(sha(ROOT/n)==r['original_sha256']for n,r in changes.items())
 inputs={str(p.relative_to(src)):sha(p)for directory in ('src','tests','assets','tools','docs')for p in(src/directory).rglob('*')if p.is_file()and'sysroot'not in p.parts and'__pycache__'not in p.parts and p.suffix!='.pyc'};inputs.update({n:sha(src/n)for n in ['Makefile','linker.ld']})
 (out/'adapter-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n');receipt={'scope':__doc__,'content_revision':9,'source_root':str(src),'frozen_root':str(frozen),'candidate':{n:sha(src/'build'/n)for n in ['emberbond.gba','emberbond.elf','emberbond.sym','source-hashes.json']},'changes':changes,'runtime_unchanged':True,'original_helpers_unchanged':True,'input_manifest_sha256':sha(out/'adapter-inputs.json'),'preparation_script_sha256':sha(Path(__file__)),'storage':{'verified_immutable_links':len(linked),'independently_copied_helpers':len(copied)},'new_modules':MODULES}
 (out/'adapter-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'prepared':str(src),'receipt_sha256':sha(out/'adapter-receipt.json'),'storage':receipt['storage']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--frozen-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.frozen_root.resolve(),a.output.resolve())
