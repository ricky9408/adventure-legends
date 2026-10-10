#!/usr/bin/env python3
"""Create an explicit Return7 adapter copy; historical helpers stay untouched.

Enumerated changes only: current-header assertions, an additional independent
wire5 migration proof, and the adapter dependency in observer manifests. All
prior fixture-version, payload, gameplay, cadence and pixel assertions remain.
Audio candidates also receive explicitly host-only no-audio link boundaries
in copied engine probes, plus their original ARM music build wiring.
This preparation does not run a test and grants no acceptance result.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
SUBSTITUTIONS={
 'tests/southern_minimal_route.py':[("int.from_bytes(migrated[12:14],'little')==6", "int.from_bytes(migrated[12:14],'little')==7"),("current revision6", "current revision7")],
 'tests/southern_journey.py':[("int.from_bytes(migrated[12:14],'little')==6", "int.from_bytes(migrated[12:14],'little')==7"),("current revision6", "current revision7"),("revision3 to current6", "revision3 to current7")],
 'tests/magma_journey.py':[("int.from_bytes(migrated[12:14],'little')==6", "int.from_bytes(migrated[12:14],'little')==7"),("content revision6", "content revision7"),("revision4 to6", "revision4 to7")],
 'tests/underwater_journey.py':[("int.from_bytes(bank[12:14],'little')==6", "int.from_bytes(bank[12:14],'little')==7"),("content revision6", "content revision7"),("revision5-to6", "revision5-to7")],
 'tests/underwater_combat_native.py':[("int.from_bytes(bank[12:14],'little')==6", "int.from_bytes(bank[12:14],'little')==7")],
 'tests/underwater_minimal_review.py':[("int.from_bytes(bank[12:14], 'little') == 6", "int.from_bytes(bank[12:14], 'little') == 7")],
 'tests/magma_retained_controls.py':[("(6 if same_rom else 5)","(7 if same_rom else 5)")],
 'tests/magma_combat_tests.py':[("(5 if cross_rom else 6)","(5 if cross_rom else 7)")],
 'tests/southern_combat_tests.py':[("(4 if archived else 6)","(4 if archived else 7)"),("int.from_bytes(bank[12:14],'little')==6", "int.from_bytes(bank[12:14],'little')==7"),("current revision6", "current revision7")],
}
MIGRATIONS={
 'tests/southern_journey.py':("        self.snapshot('00-n5-forward-migration')",3,'b','migrated','self.source_bytes','saved'),
 'tests/southern_minimal_route.py':("        self.absent_optional();self.record_state('before-southern-entry')",3,'b','migrated','self.source_bytes','saved'),
 'tests/magma_journey.py':("        self.old_ids={c.instance_id for c in self.live()};self.snapshot('00-s3-forward-migration')",4,'b','migrated','self.source_bytes','saved'),
 'tests/underwater_journey.py':("        self.snapshot('00-magma-forward-migration')",5,'self.source_bank','bank','self.source_bytes',"self.e.bytes(0x0e000000,32768)"),
}
def audio_adapter(candidate,src,receipts):
    if not (candidate/'src/music.h').is_file():return
    header=(candidate/'src/music.h').read_text()
    for declaration in ('void music_init(void);','void music_update(unsigned room, unsigned state);','void music_service(void);'):
        assert declaration in header,('Unreviewed audio host interface',declaration)
    scope='Audio hooks are explicit host-only no-ops; no audio, DMA, IRQ, native timing or native music claim.'
    files=['tests/test_save_feedback.py']+['tests/underwater_engine_review/'+name for name in (
        'test_legacy_deferred_anchor_linked.py','test_legacy_deferred_anchor_current.py',
        'test_engine_lifecycle.py','test_bounded_magma_return.py','test_bounded_southern_rest.py',
        'test_bounded_magma_save_current.py')]
    for name in files:
        path=src/name;before=path.read_text();text=before
        if name=='tests/test_save_feedback.py':
            marker="*[str(ROOT/'src'/(n+'.c')) for n in modules]"
            replacement="str(ROOT/'tests/retained_host_audio.c'),'-I'+str(ROOT/'src'),"+marker
            assert text.count('Audio is held below its hardware-write interval.')==1
            text=text.replace('Audio is held below its hardware-write interval.',scope)
        else:
            marker="*[str(SOURCE_ROOT/'src'/f'{n}.c') for n in MODULES]"
            if name.endswith('test_legacy_deferred_anchor_linked.py'):
                marker="*[str(ROOT/'src'/f'{n}.c') for n in MODULES]"
            replacement="str(ROOT/'tests/retained_host_audio.c'),"+marker
            assert text.count('TMP=tempfile.TemporaryDirectory(')==1
            text=text.replace('TMP=tempfile.TemporaryDirectory(',"RESULT['audio_scope']="+repr(scope)+"\nTMP=tempfile.TemporaryDirectory(",1)
        assert text.count(marker)==1,(name,'audio source marker')
        text=text.replace(marker,replacement,1);path.write_text(text)
        receipts[name]={'original_sha256':sha(ROOT/name),'adapted_sha256':sha(path),
            'change':scope,'compile_argument_before':marker,'compile_argument_after':replacement,
            'stub_sha256':sha(src/'tests/retained_host_audio.c'),'gameplay_assertions_unchanged':True}
    recipe=src/'Makefile';before=sha(recipe);text=recipe.read_text()
    old='OBJECTS := $(BUILD)/startup.o $(BUILD)/game.o'
    new='OBJECTS := $(BUILD)/startup.o $(BUILD)/music.o $(BUILD)/music_data.o $(BUILD)/game.o'
    rule='$(BUILD)/music.o: src/music.c | $(BUILD)\n\t$(CC) $(filter-out -mthumb,$(CFLAGS)) -marm -c $< -o $@\n\n'
    candidate_recipe=(candidate/'Makefile').read_text()
    assert new in candidate_recipe and rule in candidate_recipe
    if old in text:
        assert text.count(old)==1 and text.count('$(BUILD)/startup.o:')==1 and rule not in text
        text=text.replace(old,new,1).replace('$(BUILD)/startup.o:',rule+'$(BUILD)/startup.o:',1)
    else:
        # A source export can already carry the reviewed audio build wiring.
        # Preserve it exactly while keeping the current test recipe intact.
        assert text.count(new)==1 and text.count(rule)==1,'Unreviewed existing audio build wiring'
    recipe.write_text(text)
    receipts['Makefile']={'source_recipe_sha256':before,'adapted_sha256':sha(recipe),
        'candidate_recipe_sha256':sha(candidate/'Makefile'),
        'change':'Preserve latest test recipes; copy exact frozen audio object order and ARM music compilation rule only'}
def prepare(candidate,out):
    manifest=candidate/'build/source-hashes.json';runtime=json.loads(manifest.read_text())
    assert all(sha(candidate/k)==v for k,v in runtime.items()),'Frozen runtime changed'
    out.mkdir(parents=True,exist_ok=False);src=out/'source';src.mkdir()
    receipts={};originals={}
    # Keep every authored asset: current host art checks read the Return PNGs
    # and pinned Magma/Underwater scene and lineage images as well as old art.
    # This copy supports both retained native recipes and current host gates.
    def ignore(path,names):
        return [n for n in names if n=='__pycache__' or n.endswith('.pyc')]
    shutil.copytree(candidate/'src',src/'src')
    for name in ('tests','assets','tools','docs'):
        shutil.copytree(ROOT/name,src/name,symlinks=True,ignore=ignore)
    for name in ('Makefile','linker.ld','README.md','LICENSE'):
        shutil.copyfile(ROOT/name,src/name)
    (src/'build').mkdir()
    for name in ('emberbond.gba','emberbond.sym','emberbond.elf','source-hashes.json'):
        shutil.copyfile(candidate/'build'/name,src/'build'/name)
    for name,changes in SUBSTITUTIONS.items():
        path=src/name;old=path.read_text();text=old;rows=[];originals[name]=sha(ROOT/name)
        for before,after in changes:
            assert text.count(before)==1,(name,before,text.count(before))
            text=text.replace(before,after,1);rows.append({'before':before,'after':after})
        if name in MIGRATIONS:
            marker,revision,prior,current,prior_image,current_image=MIGRATIONS[name]
            assert text.count(marker)==1,(name,marker)
            addition=("        from retained_migration_validator import validate_migration\n"
                      f"        self.check(validate_migration({prior},{current},{prior_image},{current_image},{revision}),"
                      "'independent wire5 migration verifies prior header, current7 CRC, exact payload and preserved source bank')\n")
            text=text.replace(marker,addition+marker,1)
            rows.append({'additional_check':addition,'before_marker':marker})
        path.write_text(text)
        receipts[name]={'original_sha256':originals[name],'adapted_sha256':sha(path),'enumerated_changes':rows}
    paths=src/'tools/underwater_observer_paths.json';before=sha(paths);names=json.loads(paths.read_text())
    names=sorted(set(names)|{'tests/retained_migration_validator.py'})
    paths.write_text(json.dumps(names,indent=2)+'\n')
    receipts['tools/underwater_observer_paths.json']={'original_sha256':before,'adapted_sha256':sha(paths),'change':'add independent migration validator to copied observer closure'}
    audio_adapter(candidate,src,receipts)
    assert all(sha(ROOT/k)==v for k,v in originals.items()),'Original helper changed during preparation'
    assert all(sha(ROOT/k)==v['original_sha256'] for k,v in receipts.items() if 'original_sha256' in v),'Original adapter input changed during preparation'
    assert all(sha(src/k)==v for k,v in runtime.items()),'Adapter must not alter runtime inputs'
    inputs={str(p.relative_to(src)):sha(p) for root in ('src','tests','assets','tools') for p in (src/root).rglob('*') if p.is_file() and 'sysroot' not in p.parts and '__pycache__' not in p.parts and p.suffix in ('.c','.h','.s','.inc','.py','.json','.txt','.sav')}
    inputs.update({name:sha(src/name) for name in ('Makefile','linker.ld')})
    (out/'adapter-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    receipt={'scope':'explicit frozen-copy Return7 retained native adapter; not a test result','source_root':str(src),'candidate_source':str(candidate),'candidate':{name:sha(src/'build'/name) for name in ('emberbond.gba','emberbond.sym','emberbond.elf','source-hashes.json')},'changes':receipts,'original_helpers_unchanged':True,'runtime_unchanged':True,'input_manifest_sha256':sha(out/'adapter-inputs.json'),'build_disabled_invocation':['make','-o','build/emberbond.gba','MAKE=make -o build/emberbond.gba','test-tools','test']}
    (out/'adapter-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
    return src
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.candidate_source.resolve(),a.output.resolve())
