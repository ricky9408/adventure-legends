#!/usr/bin/env python3
"""Bounded local/Actions gameplay regression entrypoint; never installs tools.

Only fresh, repository-owned test output is collected. No personal saves,
credentials, environment dumps, external BIOS, or cross-ROM machine states.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BUILD_FILES = ('emberbond.gba', 'emberbond.elf', 'emberbond.sym', 'emberbond.map',
               'source-hashes.json')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def run_command(command, log, timeout, env):
    """Bound the whole process group, including compilers/emulators/encoders."""
    with log.open('w') as output:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            return process.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            # A child can ignore SIGTERM after its parent has already exited.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            output.write(f'\nCI timeout after {timeout} seconds\n')
            return 124, True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('all', 'host', 'native'), default='all')
    parser.add_argument('--output', type=Path, default=Path('build/ci-local'))
    parser.add_argument('--extended-audio', action='store_true')
    parser.add_argument('--seed', type=int, default=9408,
                        help='Deterministic companion/help menu stress sequence')
    args = parser.parse_args()
    if sys.flags.optimize or os.environ.get('PYTHONOPTIMIZE'):
        parser.error('Python assertions must be enabled; remove -O/PYTHONOPTIMIZE')
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'build') or out == ROOT / 'build':
        parser.error('--output must be a new directory under this repository build/')
    canonical_host = ROOT / 'build/equipment-rewards-host-current'
    if out == canonical_host or out.is_relative_to(canonical_host):
        parser.error('--output must not overlap the canonical host aggregate directory')
    if out.exists():
        parser.error('output already exists; choose a new directory to retain prior evidence')
    out.mkdir(parents=True)
    env = {**os.environ, 'PYTHONHASHSEED': '0', 'TZ': 'UTC', 'LC_ALL': 'C.UTF-8',
           'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
           'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
           'UBSAN_OPTIONS': 'halt_on_error=1'}
    report = {'schema': 1, 'result': 'RUNNING', 'suite': args.suite,
              'seed': args.seed, 'extended_audio': args.extended_audio,
              'platform': platform.platform(), 'stages': [],
              'limitations': [
                  'Native mGBA, not physical GBA hardware or a full campaign/collection run.',
                  'Bounded opening/early gameplay includes the first boss, shop, Fire trial/evolution and earned-save Continue; later bosses and complete collection are not covered.',
                  'Inherited cold-Continue stalls are reported separately, not a measured-play cadence pass.',
                  'Synthetic audio diagnostics do not prove controller-earned region access.']}
    report_file = out / 'summary.json'
    save = lambda: write_json(report_file, report)
    deadline = time.monotonic() + 35 * 60
    report['total_budget_seconds'] = 35 * 60
    save()

    def stage(name, command, timeout=300):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError('Total 35-minute regression budget exceeded')
        timeout = min(timeout, remaining)
        row = {'name': name, 'command': command, 'timeout_seconds': timeout,
               'status': 'RUNNING', 'log': name + '.log'}
        report['stages'].append(row)
        save()
        print(f'Running {name}: {row["log"]}', flush=True)
        started = time.monotonic()
        code, timed_out = run_command(command, out / row['log'], timeout, env)
        row.update(exit_code=code, timed_out=timed_out,
                   seconds=round(time.monotonic() - started, 3),
                   status='PASS' if code == 0 else 'FAIL')
        save()
        if code:
            print('\n'.join((out / row['log']).read_text(errors='replace').splitlines()[-60:]),
                  file=sys.stderr)
            raise RuntimeError(f'{name} failed ({code}); see {out / row["log"]}')

    python = sys.executable
    try:
        stage('tool-versions', [python, '-c',
              "import os,subprocess,sys; sys.path.insert(0,'tools'); "
              "from arm_toolchain import resolve_arm_tools; "
              "from PIL import __version__ as pil, ImageFont; import numpy,scipy; "
              "print('Pillow',pil,'NumPy',numpy.__version__,'SciPy',scipy.__version__); "
              "assert pil == '12.3.0', 'Pixel generation requires pinned Pillow 12.3.0; see docs/GAMEPLAY_CI.md'; "
              "[ImageFont.truetype(p,12,index=0) for p in "
              "['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',"
              "'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']]; "
              "print('Noto CJK and DejaVu font preflight PASS'); "
              "[subprocess.run(c,check=True) for c in "
              "[['git','-c','safe.directory='+os.getcwd(),'rev-parse','HEAD'],['cc','--version'],['ffmpeg','-version'],"
              "[resolve_arm_tools('gcc')['gcc'],'--version'],"
              "[resolve_arm_tools('objcopy')['objcopy'],'--version']]]"])
        # A full clean rebuild twice catches omitted generated dependencies and
        # nondeterministic ROM/symbol/ELF output on the actual selected compiler.
        snapshots = []
        for attempt in (1, 2):
            stage(f'clean-{attempt}', ['make', 'clean'])
            stage(f'build-{attempt}', ['make', '-j2', 'all'], timeout=600)
            snapshots.append({name: digest(ROOT / 'build' / name) for name in BUILD_FILES})
        report['reproducible_build'] = {'first': snapshots[0], 'second': snapshots[1],
                                        'passed': snapshots[0] == snapshots[1]}
        save()
        if snapshots[0] != snapshots[1]:
            raise RuntimeError('Clean build artifacts differ; inspect build logs and hashes')
        candidate = out / 'candidate'
        candidate.mkdir()
        for name in BUILD_FILES:
            shutil.copyfile(ROOT / 'build' / name, candidate / name)
        stage('native-bridge', ['sh', 'tools/build_mgba_bridge.sh'])
        stage('ci-runner-tests', [python, '-m', 'unittest', 'discover', '-s', 'tests',
                                  '-p', 'test_gameplay_ci.py'])
        if args.suite in ('all', 'host'):
            stage('archive-host-output', [python, 'tools/archive_test_output.py',
                  'build/equipment-rewards-host-current'])
            try:
                stage('host', ['make', 'test'], timeout=1800)
            finally:
                # Preserve the canonical Makefile byte-for-byte: historical
                # authoring contracts intentionally pin it. Copy only this
                # aggregate's known generated directory, including failures.
                host_output = ROOT / 'build/equipment-rewards-host-current'
                if host_output.is_dir():
                    shutil.copytree(host_output, out / 'host')
            host = json.loads((out / 'host/report.json').read_text())
            if host['result'] != 'PASS':
                raise RuntimeError('Current host aggregate did not report PASS')
            report['host_checks'] = len(host['runs'])
        if args.suite in ('all', 'native'):
            rom_sha = snapshots[-1]['emberbond.gba']
            common = [python, 'tests/regional_music_native.py', '--expected-rom-sha', rom_sha]
            stage('controller-route', common + ['--cases', 'controllers', '--output',
                                                str(out / 'controllers')], timeout=600)
            native = json.loads((out / 'controllers/report.json').read_text())
            if native['result'] != 'PASS' or not native['controller_only'] or native['game_ram_writes'] or native['machine_state_loads']:
                raise RuntimeError('Controller route did not establish clean controller-only acceptance')
            bridge = str(out / 'controllers/native-bridge.so')
            stage('fresh-early-gameplay', [python, 'tests/fresh_early_optional.py',
                  str(out / 'fresh-early'), '--bridge', bridge], timeout=600)
            early = json.loads((out / 'fresh-early/original/report.json').read_text())
            if not early['route_complete'] or early['failures'] or not early['controller_only'] or any(early[key] for key in ('game_ram_writes', 'machine_state_imports', 'historical_progress_imports')):
                raise RuntimeError('Fresh early controller route did not complete cleanly')
            stage('opening-save-load', [python, 'tests/opening_scene_native.py', '--bridge',
                                        bridge, '--output', str(out / 'opening')], timeout=600)
            opening = json.loads((out / 'opening/report.json').read_text())
            if opening['result'] != 'PASS_OPENING_AND_SAVE':
                raise RuntimeError('Opening/save gate did not report its expected pass')
            stage('companion-help-menus', [python, 'tests/opening_skip_guides_native.py',
                  '--bridge', bridge, '--save', str(out / 'opening/skip-0-village.sav'),
                  '--seed', str(args.seed), '--output', str(out / 'guides')])
            stage('synthetic-audio-diagnostics', common + ['--cases', 'synthetic',
                  '--output', str(out / 'synthetic-audio')], timeout=600)
            if args.extended_audio:
                stage('synthetic-exact-loops', common + ['--cases', 'regional_loops',
                      '--output', str(out / 'synthetic-loops')], timeout=1200)
            report['native'] = {'controller_metrics': native['metrics'],
                                'opening_checks': len(opening['checks']),
                                'fresh_early_checks': len(early['checks']),
                                'opening_cadence': opening['cadence_by_scope']}
        # Test-only additions must not accidentally mutate frozen runtime inputs.
        frozen = json.loads((ROOT / 'build/source-hashes.json').read_text())
        if any(digest(ROOT / name) != expected for name, expected in frozen.items()):
            raise RuntimeError('Runtime sources changed during regression checks')
        report['result'] = 'PASS'
    except Exception as error:
        report['result'] = 'FAIL'
        report['error'] = str(error)
        print(str(error), file=sys.stderr)
    finally:
        save()
        print(f'{report["result"]}: {report_file}', flush=True)
    return int(report['result'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
