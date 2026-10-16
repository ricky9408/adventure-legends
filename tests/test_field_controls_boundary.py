#!/usr/bin/env python3
"""Current controls bytes fail closed; historical 4005 bytes/modes stay exact."""
import base64,copy,gzip,json,stat,unittest
from pathlib import Path
from unittest.mock import patch
import field_controls_boundary as boundary


class BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=boundary.load();cls.s=boundary.state(cls.c)
        boundary.authenticate(cls.c,cls.s)
        cls.packed=(boundary.ROOT/boundary.INVERSE_PATH).read_bytes()
        cls.entries=json.loads(gzip.decompress(cls.packed))

    def test_current_and_all_negative_categories(self):
        boundary.authenticate(self.c,self.s)
        rejected=boundary.negatives(self.c,self.s)
        for label in ('production: src/game.c','helpers: tests/current_field_controls.py',
                      'proofs: tests/selected_music_boundary.py',
                      'protected: assets/music/selected/catalog.json',
                      'unexpected src/unreviewed.c','deleted tests/current_field_controls.py',
                      'inverse tampering','contract tampering'):
            self.assertIn(label,rejected)
        self.assertGreater(len(rejected),len(self.c['current_helpers']))

    def test_exact_tree_modes_and_independent_housekeeping(self):
        original=Path.read_bytes;live_ignore=boundary.ROOT/'.gitignore';reads=[]
        def read_bytes(path):
            if path==live_ignore:reads.append(path);return b'later-housekeeping/\n'
            return original(path)
        with patch.object(Path,'read_bytes',read_bytes):
            with boundary.parent_view(self.c) as view:
                files={p.relative_to(view).as_posix():p.read_bytes() for p in view.rglob('*') if p.is_file()}
                modes={p.relative_to(view).as_posix():f'100{stat.S_IMODE(p.stat().st_mode):03o}' for p in view.rglob('*') if p.is_file()}
                self.assertEqual({p:boundary.sha(data) for p,data in files.items()},self.c['parent_files'])
                self.assertEqual(modes,self.c['parent_modes'])
                self.assertEqual(boundary.git_tree(files,modes),boundary.PARENT_TREE)
                self.assertEqual(boundary.sha(files['docs/selected-music/contract.json']),boundary.SELECTED_CONTRACT_SHA)
        self.assertEqual(reads,[])

    def assert_rejected(self,packed,c,message):
        original=Path.read_bytes;archive=boundary.ROOT/boundary.INVERSE_PATH
        with patch.object(Path,'read_bytes',lambda path:packed if path==archive else original(path)):
            with self.assertRaisesRegex(AssertionError,message):
                with boundary.parent_view(c):self.fail('accepted corrupted history')

    def corrupt(self):
        entries=dict(self.entries);data=base64.b64decode(entries['.gitignore'])+b'corrupted-history/\n'
        entries['.gitignore']=base64.b64encode(data).decode()
        packed=gzip.compress(json.dumps(entries,sort_keys=True,separators=(',',':')).encode(),mtime=0)
        c=copy.deepcopy(self.c);c['inverse_sha256']=boundary.sha(packed)
        return packed,c,data

    def test_archive_tamper(self):self.assert_rejected(self.packed+b'bad',self.c,'field controls inverse changed')
    def test_entry_tamper_after_archive_repin(self):
        packed,c,_=self.corrupt();self.assert_rejected(packed,c,'inverse byte set changed')
    def test_parent_tamper_after_entry_repin(self):
        packed,c,data=self.corrupt();c['inverse_files_sha256']['.gitignore']=boundary.sha(data)
        self.assert_rejected(packed,c,'parent bytes changed')
    def test_tree_tamper_after_parent_repin(self):
        packed,c,data=self.corrupt();c['inverse_files_sha256']['.gitignore']=boundary.sha(data);c['parent_files']['.gitignore']=boundary.sha(data)
        self.assert_rejected(packed,c,'not the exact 4005 tree')
    def test_mode_tamper(self):
        c=copy.deepcopy(self.c);c['parent_modes']['.gitignore']='100755'
        self.assert_rejected(self.packed,c,'not the exact 4005 tree')


if __name__=='__main__':unittest.main()
