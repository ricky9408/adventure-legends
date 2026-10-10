"""CI infrastructure checks: nonzero failures and bounded process cleanup."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gameplay_ci', ROOT / 'tools/run_gameplay_ci.py')
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class GameplayCITests(unittest.TestCase):
    def test_nonzero_exit_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'failure.log'
            code, timed_out = ci.run_command(
                [sys.executable, '-c', 'print("expected failure"); raise SystemExit(7)'],
                log, 5, os.environ.copy())
            self.assertEqual(code, 7)
            self.assertFalse(timed_out)
            self.assertIn('expected failure', log.read_text())

    def test_timeout_terminates_child_group(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'should-not-exist'
            child = f'import time,signal; signal.signal(signal.SIGTERM, signal.SIG_IGN); from pathlib import Path; time.sleep(2); Path({str(marker)!r}).touch()'
            parent = ('import subprocess,sys,time; '
                      f'subprocess.Popen([sys.executable,"-c",{child!r}]); time.sleep(20)')
            code, timed_out = ci.run_command([sys.executable, '-c', parent],
                                             Path(directory) / 'timeout.log', 0.2,
                                             os.environ.copy())
            self.assertEqual(code, 124)
            self.assertTrue(timed_out)
            # The original child would create the marker if only its parent died.
            import time
            time.sleep(2.1)
            self.assertFalse(marker.exists())

    def test_atomic_report_replaces_complete_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            ci.write_json(path, {'result': 'RUNNING'})
            ci.write_json(path, {'result': 'FAIL'})
            self.assertIn('FAIL', path.read_text())
            self.assertFalse(path.with_suffix('.json.tmp').exists())


if __name__ == '__main__':
    unittest.main()
