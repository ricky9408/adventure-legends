"""Non-destructive GBA-address reservations for the synthetic engine process.

Only the repository's already-tested EEXIST + proved Python-heap overlap class
may start a fresh process, before any game assertion. Unknown errors, crashes,
permission denials and game failures are retained and never retried.
"""
import ctypes as C
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('protected_deferred_launcher', ROOT / 'tools/run_deferred_anchor_probe.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)
ADDRESSES = tuple(sorted(policy.ADDRESSES))
LENGTH = 0x20000
MAP_FLAGS = 0x100022  # MAP_FIXED_NOREPLACE | MAP_PRIVATE | MAP_ANONYMOUS


def overlaps(address):
    rows = []
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split()
        start, end = (int(value, 16) for value in fields[0].split('-'))
        if start < address + LENGTH and end > address:
            rows.append({'start': start, 'end': end, 'tag': fields[5] if len(fields) > 5 else ''})
    return rows


def reserve_gba_pages():
    libc = C.CDLL(None, use_errno=True)
    libc.mmap.argtypes = [C.c_void_p, C.c_size_t, C.c_int, C.c_int, C.c_int, C.c_long]
    libc.mmap.restype = C.c_void_p
    libc.munmap.argtypes = [C.c_void_p, C.c_size_t]
    libc.munmap.restype = C.c_int
    owned, reservations = [], []
    for address in ADDRESSES:
        before = overlaps(address)
        C.set_errno(0)
        result = libc.mmap(address, LENGTH, 3, MAP_FLAGS, -1, 0)
        error = C.get_errno()
        if result != address:
            # Old kernels may ignore an unknown flag and choose another hint.
            # Reject that outcome and release only memory this call obtained.
            if result not in (None, C.c_void_p(-1).value):
                libc.munmap(result, LENGTH)
            detail = {'kind': 'synthetic-address-reservation', 'probe': 'player-feedback-engine',
                      'errno': error, 'address': address, 'length': LENGTH,
                      'mapped_before_failure': len(owned), 'overlaps': overlaps(address),
                      'pre_map_overlaps': before, 'returned_address': result,
                      'game_assertions_started': False, 'overwritten_mappings': False,
                      'mapping_flags': MAP_FLAGS}
            for prior in reversed(owned):
                assert libc.munmap(prior, LENGTH) == 0
            print(policy.PREFIX + json.dumps(detail), file=sys.stderr, flush=True)
            raise SystemExit(78)
        owned.append(address)
        reservations.append({'address': address, 'length': LENGTH, 'pre_map_overlaps': before})
    path = os.environ.get('PLAYER_FEEDBACK_MAPPING_REPORT')
    if path:
        Path(path).write_text(json.dumps({'mapping_flags': MAP_FLAGS, 'overwritten_mappings': False,
                                         'reservations': reservations}, indent=2) + '\n')
    return libc


def run_protected_probe(script):
    (ROOT / 'build').mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix='player-feedback-engine-probe-', dir=ROOT / 'build'))
    attempts = []

    def run(number):
        environment = dict(os.environ, PLAYER_FEEDBACK_PROBE_CHILD='1',
                           PLAYER_FEEDBACK_MAPPING_REPORT=str(output / f'attempt-{number:02}-mappings.json'),
                           PLAYER_FEEDBACK_RESULT=str(output / f'attempt-{number:02}-result.json'))
        return subprocess.run([sys.executable, str(script)], cwd=ROOT, env=environment,
                              text=True, capture_output=True)

    def record(number, result, collision):
        for name, data in (('stdout', result.stdout), ('stderr', result.stderr)):
            (output / f'attempt-{number:02}-{name}.txt').write_text(data)
        row = {'attempt': number, 'returncode': result.returncode, 'classified_heap_collision': collision,
               'stdout_sha256': hashlib.sha256(result.stdout.encode()).hexdigest(),
               'stderr_sha256': hashlib.sha256(result.stderr.encode()).hexdigest()}
        if result.returncode == 0:
            report_path = output / f'attempt-{number:02}-result.json'
            report = json.loads(report_path.read_text())
            expected_entries = len(json.loads((ROOT/'assets/feedback_travel_entries.json').read_text())['entries'])
            assert report['passed'] is True and report['walking_entries'] == expected_entries
            row['result_sha256'] = hashlib.sha256(report_path.read_bytes()).hexdigest()
        attempts.append(row)
        print(f'Feedback engine attempt {number}: exit {result.returncode}' +
              (' (proved pre-game Python heap overlap)' if collision else ''), flush=True)
        if result.returncode == 0:
            print(result.stdout, end='')
        elif collision is None:
            print(result.stdout, end='')
            print(result.stderr, file=sys.stderr, end='')

    status = policy.run_attempts(run, record)
    (output / 'launcher-result.json').write_text(json.dumps({
        'scope': 'Protected synthetic engine process; no native GBA timing claim',
        'returncode': status, 'attempts': attempts, 'maximum_attempts': 3,
        'game_failure_retries': 0, 'forced_mappings': False}, indent=2) + '\n')
    print('Evidence:', output / 'launcher-result.json')
    return status
