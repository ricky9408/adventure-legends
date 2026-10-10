"""Fail-closed contract probes; does not compile the expensive raster matrices."""
from pathlib import Path
import copy,json,os,shutil,subprocess,sys,tempfile,unittest
sys.dont_write_bytecode=True
from renderer_equipment_successor import FLAG,PARENT_SHA256,PREVIOUS_SUCCESSOR_SHA256,I3_SUCCESSOR_SHA256,SUCCESSOR_SHA256,digest,select_manifest,query_function
from verify_late_renderer import authenticate,function
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/render-g5'
PREVIOUS=ROOT/'tests/fixtures/render-equipment-i1/reference.json'
I3=ROOT/'tests/fixtures/render-equipment-i3/reference.json'
SUCCESSOR=ROOT/'tests/fixtures/render-equipment-i4/reference.json'

class EquipmentRendererContract(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='renderer-successor-probes-')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)/'source';self.fixture=Path(self.temp.name)/'render-g5'
        self.manifest,_=select_manifest(FIXTURE,True)
        for path in {'src/game.c',*self.manifest['context_source_pins']}:
            p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,p)
        shutil.copytree(FIXTURE,self.fixture)
        shutil.copytree(PREVIOUS.parent,self.fixture.parent/'render-equipment-i1')
        shutil.copytree(I3.parent,self.fixture.parent/'render-equipment-i3')
        shutil.copytree(SUCCESSOR.parent,self.fixture.parent/'render-equipment-i4')
    def reject_file(self,path,mutation,manifest=None,match=None):
        old=path.read_bytes();path.write_bytes(mutation(old))
        try:
            with self.assertRaisesRegex(AssertionError,match or '.*'):
                authenticate(self.root,self.fixture,manifest or self.manifest)
        finally:path.write_bytes(old)
    def test_exact_successor_authenticates(self):
        authenticate(self.root,self.fixture,self.manifest)
        self.assertEqual(digest(SUCCESSOR.read_bytes()),SUCCESSOR_SHA256)
        self.assertEqual(len(self.manifest['candidate_function_sha256']),9)
        self.assertEqual(sum(map(len,self.manifest['unchanged_query_function_sha256'].values())),8)
    def test_all_original_pins_retained(self):
        parent,path=select_manifest(self.fixture)
        self.assertEqual(digest(path.read_bytes()),PARENT_SHA256)
        for key in ('fixture_files','reference_function_sha256','candidate_function_sha256','suites','baseline'):
            self.assertEqual(parent[key],self.manifest[key])
        for name,old in parent['context_source_pins'].items():
            self.assertEqual(old,self.manifest['context_changes'][name]['before_sha256'] if name in self.manifest['context_changes'] else self.manifest['context_source_pins'][name])
    def test_default_rejects_successor_source(self):
        parent,_=select_manifest(self.fixture)
        with self.assertRaisesRegex(AssertionError,'game source differs'):authenticate(self.root,self.fixture,parent)
    def test_unrelated_source_byte_rejected(self):
        self.reject_file(self.root/'src/game.c',lambda b:b+b'\n',match='game source differs')
    def test_line_endings_are_full_byte_pinned(self):
        self.reject_file(self.root/'src/game.c',lambda b:b.replace(b'\n',b'\r\n'),match='game source differs')
    def test_each_candidate_function_rejected_even_if_whole_source_repin_attempted(self):
        path=self.root/'src/game.c'
        for name in self.manifest['candidate_function_sha256']:
            with self.subTest(function=name):
                old=path.read_text();body=function(old,name);changed=old.replace(body,body[:-1]+' /* mutation */}',1).encode()
                manifest=copy.deepcopy(self.manifest);manifest['reviewed_candidate']['game_source_sha256']=digest(changed)
                self.reject_file(path,lambda b:changed,manifest,'Candidate differs')
    def test_each_context_full_file_rejected(self):
        for relative in self.manifest['context_source_pins']:
            with self.subTest(path=relative):self.reject_file(self.root/relative,lambda b:b+b'\n',match='query/palette context changed')
    def test_each_unchanged_query_rejected_even_if_file_repin_attempted(self):
        for relative,names in self.manifest['unchanged_query_function_sha256'].items():
            for name in names:
                with self.subTest(path=relative,function=name):
                    path=self.root/relative;old=path.read_text();body=query_function(old,name);changed=old.replace(body,body[:-1]+' /* mutation */}',1).encode()
                    manifest=copy.deepcopy(self.manifest)
                    if relative=='src/game.c':manifest['reviewed_candidate']['game_source_sha256']=digest(changed)
                    else:manifest['context_source_pins'][relative]=digest(changed)
                    self.reject_file(path,lambda b:changed,manifest,'Pinned renderer query changed')
    def test_each_original_fixture_rejected(self):
        for name in self.manifest['fixture_files']:
            with self.subTest(fixture=name):self.reject_file(self.fixture/name,lambda b:b+b'\n',match='Reference fixture changed')
    def test_each_reference_function_rejected_even_if_fixture_repin_attempted(self):
        path=self.fixture/'reference-game.c'
        for name in self.manifest['reference_function_sha256']:
            with self.subTest(function=name):
                old=path.read_text();body=function(old,name);changed=old.replace(body,body[:-1]+' /* mutation */}',1).encode()
                manifest=copy.deepcopy(self.manifest);manifest['fixture_files']['reference-game.c']=digest(changed)
                self.reject_file(path,lambda b:changed,manifest,'G5 reference function changed')
    def test_changed_parent_manifest_rejected_in_both_modes(self):
        p=self.fixture/'reference.json';p.write_bytes(p.read_bytes()+b' ')
        for successor in (False,True):
            with self.subTest(successor=successor):
                with self.assertRaisesRegex(AssertionError,'Original renderer manifest changed'):select_manifest(self.fixture,successor,SUCCESSOR if successor else None)
    def test_changed_successor_manifest_rejected(self):
        p=Path(self.temp.name)/'successor.json';p.write_bytes(SUCCESSOR.read_bytes()+b' ')
        with self.assertRaisesRegex(AssertionError,'successor manifest changed'):select_manifest(self.fixture,True,p)
    def test_each_manifest_pin_or_matrix_mutation_rejected(self):
        changes=[('reviewed_candidate','game_source_sha256'),('candidate_function_sha256','rect'),('reference_function_sha256','rect'),('fixture_files','raster_differential.c')]
        changes += [('context_source_pins',name)for name in self.manifest['context_source_pins']]
        for group,key in changes:
            with self.subTest(group=group,key=key):
                m=copy.deepcopy(self.manifest);m[group][key]='0'*64;p=Path(self.temp.name)/'successor.json';p.write_text(json.dumps(m))
                with self.assertRaisesRegex(AssertionError,'successor manifest changed'):select_manifest(self.fixture,True,p)
        for transform in (lambda m:m['suites'][0]['expected_counts'].__setitem__('lines',1),lambda m:m['suites'][0].__setitem__('candidate_marker','wrong'),lambda m:m['context_source_pins'].pop('src/assets.h')):
            m=copy.deepcopy(self.manifest);transform(m);p.write_text(json.dumps(m))
            with self.assertRaisesRegex(AssertionError,'successor manifest changed'):select_manifest(self.fixture,True,p)
    def test_successor_path_without_opt_in_rejected(self):
        with self.assertRaisesRegex(AssertionError,'explicit opt-in'):select_manifest(self.fixture,False,SUCCESSOR)
    def test_default_cli_rejects_and_creates_no_pass_report(self):
        out=Path(self.temp.name)/'should-not-exist.json'
        run=subprocess.run([sys.executable,str(ROOT/'tests/verify_late_renderer.py'),'--source-root',str(self.root),'--output',str(out)],capture_output=True,text=True,env={**os.environ,'EQUIPMENT_REWARDS_SUCCESSOR':'1'})
        self.assertNotEqual(run.returncode,0);self.assertIn('game source differs',run.stderr);self.assertFalse(out.exists())
    def test_duplicate_or_abbreviated_flags_rejected(self):
        for flags in ([FLAG,FLAG],['--equipment-rewards']):
            run=subprocess.run([sys.executable,str(ROOT/'tests/verify_late_renderer.py'),*flags],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
    def test_previous_successor_manifest_stays_frozen(self):
        self.assertEqual(digest(PREVIOUS.read_bytes()),PREVIOUS_SUCCESSOR_SHA256)
        previous=json.loads(PREVIOUS.read_text())
        for key in previous:
            if key not in ('reviewed_candidate','context_source_pins','context_changes'):self.assertEqual(previous[key],self.manifest[key])
        for path,pin in previous['context_source_pins'].items():
            self.assertEqual(pin,self.manifest['context_changes'][path]['before_sha256'] if path=='src/save_feedback.c' else self.manifest['context_source_pins'][path])
        for path,change in previous['context_changes'].items():self.assertEqual(change,self.manifest['context_changes'][path])
    def test_previous_successor_tampering_rejected(self):
        p=self.fixture.parent/'render-equipment-i1/reference.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(AssertionError,'Previous equipment renderer manifest changed'):select_manifest(self.fixture,True,SUCCESSOR)
    def test_old_successor_cannot_be_selected_as_current(self):
        for predecessor in (PREVIOUS,I3):
            with self.subTest(path=predecessor):
                with self.assertRaisesRegex(AssertionError,'successor manifest changed'):select_manifest(self.fixture,True,predecessor)
    def test_only_ordinary_slice_reversal_recovers_previous_source(self):
        raw=(self.root/'src/game.c').read_bytes();change=self.manifest['source_change']
        self.assertEqual(raw.count(change['after_statement'].encode()),1)
        self.assertEqual(digest(raw.replace(change['after_statement'].encode(),change['before_statement'].encode(),1)),change['before_sha256'])
    def test_other_source_change_rejected_despite_outer_source_repin(self):
        path=self.root/'src/game.c';raw=path.read_bytes()+b'\n';manifest=copy.deepcopy(self.manifest);manifest['reviewed_candidate']['game_source_sha256']=digest(raw)
        self.reject_file(path,lambda b:raw,manifest,'Changes beyond the reviewed ordinary save slice')
    def test_wrong_slice_rejected_despite_outer_source_repin(self):
        path=self.root/'src/game.c';raw=path.read_bytes().replace(b'status=save5_step(192);',b'status=save5_step(191);');manifest=copy.deepcopy(self.manifest);manifest['reviewed_candidate']['game_source_sha256']=digest(raw)
        self.reject_file(path,lambda b:raw,manifest,'Exact ordinary save slice change')
    def test_i3_manifest_stays_frozen(self):
        self.assertEqual(digest(I3.read_bytes()),I3_SUCCESSOR_SHA256)
        i3=json.loads(I3.read_text())
        for key in i3:
            if key not in ('reviewed_candidate','context_source_pins','context_changes'):self.assertEqual(i3[key],self.manifest[key])
        self.assertEqual(i3['reviewed_candidate']['game_source_sha256'],self.manifest['reviewed_candidate']['game_source_sha256'])
    def test_i3_manifest_tampering_rejected(self):
        p=self.fixture.parent/'render-equipment-i3/reference.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(AssertionError,'I3 equipment renderer manifest changed'):select_manifest(self.fixture,True,SUCCESSOR)
    def test_i3_contract_rejects_current_source(self):
        with self.assertRaisesRegex(AssertionError,'query/palette context changed'):authenticate(self.root,self.fixture,json.loads(I3.read_text()))
    def test_i4_new_header_is_required_and_pinned(self):
        path='src/save_snapshot_copy.h'
        self.assertIsNone(self.manifest['context_changes'][path]['before_sha256'])
        self.assertEqual(self.manifest['context_changes'][path]['after_sha256'],self.manifest['context_source_pins'][path])
        self.reject_file(self.root/path,lambda b:b.replace(b'words -= 8',b'words -= 7'),match='query/palette context changed')
    def test_i4_changed_feedback_copy_rejected(self):
        self.reject_file(self.root/'src/save_feedback.c',lambda b:b.replace(b'save_snapshot_copy(&snapshot,s);',b'save_snapshot_copy(&snapshot,&snapshot);'),match='query/palette context changed')
    def test_authentication_is_read_only(self):
        paths=list(self.root.rglob('*'))+list(self.fixture.rglob('*'));before={str(p):digest(p.read_bytes())for p in paths if p.is_file()};manifest=copy.deepcopy(self.manifest)
        authenticate(self.root,self.fixture,self.manifest)
        self.assertEqual(self.manifest,manifest);self.assertEqual(before,{p:digest(Path(p).read_bytes())for p in before})

if __name__=='__main__':unittest.main(verbosity=2)
