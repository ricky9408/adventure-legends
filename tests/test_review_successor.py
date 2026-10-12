#!/usr/bin/env python3
"""Current review authentication, complete inverse and non-vacuous tamper checks."""
import hashlib
import unittest
import verify_review_successor as boundary


class ReviewBoundary(unittest.TestCase):
    def test_current_positive_and_all_mutation_negatives(self):
        c, _ = boundary.verify(chain=False)
        rejected = boundary.negatives(c, boundary.state(c))
        self.assertIn('inverse payload tampering', rejected)
        self.assertIn('review contract tampering', rejected)
        self.assertIn('changed src/game.c', rejected)
        self.assertIn('changed src/save5.c', rejected)
        self.assertIn('changed LICENSE', rejected)
        self.assertIn('unexpected src/unreviewed.c', rejected)
        self.assertIn('unexpected assets/unreviewed.json', rejected)
        self.assertGreaterEqual(len(rejected), len(c['changed']) + len(c['added']))

    def test_exact_prior_main_tree_and_soundtrack_runtime(self):
        c, _ = boundary.verify(chain=False)
        with boundary.parent_view(c) as view:
            import verify_soundtrack_successor as original
            saved = original.ROOT
            original.ROOT = view
            try:
                soundtrack = original.load()
                original.authenticate(soundtrack, original.state(soundtrack))
            finally:
                original.ROOT = saved
            for path, want in c['music_license'].items():
                self.assertEqual(hashlib.sha256((view / path).read_bytes()).hexdigest(), want)

    def test_git_tree_detects_bytes_modes_and_paths(self):
        files = {'a': b'one', 'dir/b': b'two'}
        modes = {'a': '100644', 'dir/b': '100755'}
        before = boundary.git_tree(files, modes)
        self.assertNotEqual(before, boundary.git_tree(files | {'a': b'three'}, modes))
        self.assertNotEqual(before, boundary.git_tree(files, modes | {'a': '100755'}))
        self.assertNotEqual(before, boundary.git_tree({'other': b'one', 'dir/b': b'two'},
                                                   {'other': '100644', 'dir/b': '100755'}))


if __name__ == '__main__':
    unittest.main(verbosity=2)
