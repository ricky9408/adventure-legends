#!/usr/bin/env python3
"""Reproduce fresh strict Return controller acquisition and dependent checks.

Requires a caller-pinned ROM/symbol/ELF/source closure. Freezes the helper closure
once, runs an uninterrupted producer, independent minimal arms/lifecycle, then
same-candidate repeat/control branches only if that producer passes. All stage
exits and skipped dependencies are recorded. No publication or game RAM writes.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import return_journey
import return_followup_diagnostics
from return_native_dependencies import freeze_emulator_library, frozen_environment, preload_frozen


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze_helpers(destination, mgba_library=None):
    files = {Path(__file__).resolve(), ROOT / 'tests/test_return_journey_harness.py'}
    files.update(ROOT / p for p in (
        'tools/mgba_bridge.c', 'tools/mgba_bridge.so', 'assets/region/layout.json',
        'assets/world_manifest.json', 'assets/campaign_layouts.json', 'assets/return_region/geometry.json',
        'tests/fixtures/v5-revision6/underwater-all89-town.sav',
        'tests/fixtures/v5-revision6/underwater-minimal12-town.sav',
        'tests/fixtures/v5-revision6/provenance.json'))
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).is_file() and Path(filename).resolve().is_relative_to(ROOT):
            files.add(Path(filename).resolve())
    hashes = {}
    for source in sorted(files):
        relative = source.relative_to(ROOT)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[str(relative)] = sha(target)
    hashes.update(freeze_emulator_library(ROOT, destination, mgba_library))
    (destination / 'helper-hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    return hashes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('rom', 'symbols', 'elf', 'source-manifest', 'source-root', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('expected-rom-sha', 'expected-symbols-sha', 'expected-elf-sha', 'expected-manifest-sha'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--mgba-library', type=Path, help='Optional explicit installed mGBA library; loader identity must match the bridge')
    a = p.parse_args()
    out = a.output.resolve()
    assert not out.exists() or not any(out.iterdir()), 'Use an empty new run directory; failure evidence must not be overwritten'
    out.mkdir(parents=True, exist_ok=True)
    source_root = a.source_root.resolve()
    assert sha(a.source_manifest) == a.expected_manifest_sha
    runtime = json.loads(a.source_manifest.read_text())
    assert all((source_root / path).is_file() and sha(source_root / path) == digest for path, digest in runtime.items()), 'Runtime closure differs from supplied manifest'
    candidate = out / 'candidate'
    candidate.mkdir()
    for source, name, expected in ((a.rom, 'emberbond.gba', a.expected_rom_sha),
                                   (a.symbols, 'emberbond.sym', a.expected_symbols_sha),
                                   (a.elf, 'emberbond.elf', a.expected_elf_sha),
                                   (a.source_manifest, 'source-hashes.json', a.expected_manifest_sha)):
        assert sha(source) == expected, ('wrong supplied candidate', str(source))
        # One independent immutable copy protects against a caller rebuilding
        # its usual build output. Per-stage harnesses hardlink this sealed copy.
        shutil.copyfile(source, candidate / name)
        assert sha(candidate / name) == expected
    return_journey.elf_locals(candidate / 'emberbond.elf', candidate / 'emberbond.gba')
    helpers = out / 'helpers'
    helper_hashes = freeze_helpers(helpers, a.mgba_library)
    preload_frozen(helpers)
    ctypes.CDLL(str(helpers / 'tools/mgba_bridge.so'))
    status = {'suite': 'return-native-reproduction', 'release_acceptance': False,
              'controller_only': True, 'game_ram_writes': 0,
              'recipe_sha256': sha(__file__), 'helper_manifest_sha256': sha(helpers / 'helper-hashes.json'),
              'runtime_manifest_sha256': a.expected_manifest_sha, 'runtime_source_root': str(source_root),
              'candidate': {'rom_sha256': a.expected_rom_sha, 'symbols_sha256': a.expected_symbols_sha,
                            'elf_sha256': a.expected_elf_sha}, 'stages': [], 'finished': False}
    status_path = out / 'run-status.json'

    def record():
        status_path.write_text(json.dumps(status, indent=2) + '\n')

    common = ['--rom', str(candidate / 'emberbond.gba'), '--symbols', str(candidate / 'emberbond.sym'),
              '--source-manifest', str(candidate / 'source-hashes.json'), '--expected-rom-sha', a.expected_rom_sha,
              '--expected-symbols-sha', a.expected_symbols_sha, '--expected-elf-sha', a.expected_elf_sha,
              '--expected-manifest-sha', a.expected_manifest_sha, '--timing-mode', 'strict']

    def run(name, script, extra, source_root_arg=True):
        destination = out / name
        command = [sys.executable, str(helpers / 'tests' / script), *common,
                   '--output', str(destination), *extra]
        if source_root_arg:
            command.extend(['--source-root', str(source_root)])
        log = out / (name + '.log')
        row = {'name': name, 'argv': command, 'log': str(log), 'state': 'running', 'exit_code': None}
        status['stages'].append(row)
        record()
        started = time.monotonic()
        try:
            with log.open('w') as stream:
                result = subprocess.run(command, cwd=helpers, stdout=stream, stderr=subprocess.STDOUT,
                                        env={**os.environ, **frozen_environment(helpers), 'PYTHONDONTWRITEBYTECODE': '1'}, check=False)
            row.update(exit_code=result.returncode, state='passed' if result.returncode == 0 else 'failed')
        except Exception as exc:
            row.update(state='launch-failed', error=str(exc))
        row['elapsed_seconds'] = round(time.monotonic() - started, 3)
        report = destination / 'return-journey.json'
        if report.is_file():
            row.update(report=str(report), report_sha256=sha(report))
        record()
        print(name + ': ' + row['state'], flush=True)
        return row

    record()
    producer = run('full', 'return_journey.py', ['--scope', 'full'])
    minimal = str(helpers / 'tests/fixtures/v5-revision6/underwater-minimal12-town.sav')
    run('minimal-north-lifecycle', 'return_journey.py', ['--source-sram', minimal, '--scope', 'lifecycle', '--arm-order', 'north-first'])
    run('minimal-south', 'return_journey.py', ['--source-sram', minimal, '--scope', 'main', '--arm-order', 'south-first'])
    report_path = out / 'full/return-journey.json'
    ready = False
    if producer['exit_code'] == 0 and report_path.is_file():
        evidence = json.loads(report_path.read_text())
        ready = (evidence['finished_scope'] == 'full' and not evidence['failures'] and
                 not evidence['machine_state_loads'] and all(c['passed'] for c in evidence['checks']) and
                 evidence['global_native']['enabled'] and evidence['global_native']['closed'] and
                 not evidence['global_native']['exceptions'])
    for work in ('new-repeats', 'trial-controls', 'legacy-repeats'):
        if ready:
            run(work, 'return_followup_diagnostics.py',
                ['--producer-report', str(report_path), '--expected-producer-sha', sha(report_path), '--work', work])
        else:
            status['stages'].append({'name': work, 'state': 'skipped-dependency', 'exit_code': None,
                                     'reason': 'No passing fresh uninterrupted producer on this exact candidate'})
            record()
    status['runtime_closure_still_exact'] = all(sha(source_root / path) == digest for path, digest in runtime.items())
    status['helper_closure_still_exact'] = all(sha(helpers / path) == digest for path, digest in helper_hashes.items())
    status['finished'] = True
    status['all_requested_stages_passed'] = (all(s['state'] == 'passed' for s in status['stages']) and
                                           status['runtime_closure_still_exact'] and status['helper_closure_still_exact'])
    record()
    return not status['all_requested_stages_passed']


if __name__ == '__main__':
    raise SystemExit(main())
