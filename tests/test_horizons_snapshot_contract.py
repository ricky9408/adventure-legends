#!/usr/bin/env python3
"""Independent consumer review checks; synthetic component evidence only."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/collision-rects/consumer-review'
EXPECTED_POWER = '2c0e645a569e5c4f434edc4439763675b4305a9bb6db5082286aa86d81048485'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    digest = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    assert digest('src/horizons_powers.c') == EXPECTED_POWER, 'Reviewed consumer changed; inspect before repinning'
    sources = ('tests/horizons_snapshot_contract_host.c', 'src/horizons_powers.c',
               'src/collision_rects.inc', 'src/collision_rects.h', 'src/game.c',
               'src/progression.c', 'src/horizons_game.c', 'src/horizons_fields.inc')
    identities = {p: digest(p) for p in sources}
    results = []
    for mode, flags in [('strict', []), ('sanitized', ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-no-pie'])]:
        binary = OUT / mode
        subprocess.run(['cc', '-std=c99', '-O2', '-g', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-ffunction-sections', '-fdata-sections', '-Isrc', *flags,
                        'tests/horizons_snapshot_contract_host.c', 'src/north_art.c', 'src/south_art.c',
                        '-Wl,--gc-sections', '-o', str(binary)], cwd=ROOT, check=True)
        result = subprocess.run([str(binary)], cwd=ROOT, check=True, text=True, capture_output=True,
                                env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1'))
        results.append({'mode': mode, 'passed': True, 'output': result.stdout.strip()})
    assert identities == {p: digest(p) for p in sources}, 'Reviewed source changed during verification'
    report = {'scope': __doc__, 'source_sha256': identities, 'results': results,
              'no_native_acceptance_claim': True}
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
