import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from arm_toolchain import resolve_arm_tools
from trust.contracts import input_snapshot, require_unchanged, runtime_snapshot


class VerificationInterrupted(Exception):
    pass


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment():
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONHASHSEED': '0',
           'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1', 'UBSAN_OPTIONS': 'halt_on_error=1'}
    if 'ARM_PREFIX' not in env and not env.get('DEVKITARM') and not shutil.which('arm-none-eabi-gcc'):
        if Path('/opt/devkitpro/devkitARM/bin/arm-none-eabi-gcc').is_file():
            env['DEVKITARM'] = '/opt/devkitpro/devkitARM'
    return env


def run(command, output, name, env, timeout=600):
    print('Running', name, flush=True)
    def interrupted(_signal, _frame):
        raise VerificationInterrupted('Outer verification was interrupted')
    previous_handler = signal.signal(signal.SIGTERM, interrupted)
    try:
        with (output / (name + '.log')).open('w') as log:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt, VerificationInterrupted):
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=0.05)
                except subprocess.TimeoutExpired:
                    pass
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
    if code:
        print((output / (name + '.log')).read_text()[-8000:], file=sys.stderr)
        raise RuntimeError(f'{name} failed with exit status {code}')


def build(output, env):
    tools = resolve_arm_tools('gcc', 'objcopy', 'nm', environ=env)
    candidate = output / 'candidate'
    relative = str(candidate.relative_to(ROOT)) if candidate.is_relative_to(ROOT) else str(candidate)
    command = ['make', 'BUILD=' + relative, 'PYTHON=' + sys.executable]
    before = input_snapshot(ROOT)
    passes = []
    for attempt in (1, 2):
        run(command + ['clean'], output, f'clean-{attempt}', env)
        run(command + ['-j4', 'all'], output, f'build-{attempt}', env)
        names = ('emberbond.gba', 'emberbond.elf', 'emberbond.sym', 'emberbond.map', 'source-hashes.json')
        passes.append({name: sha(candidate / name) for name in names})
        require_unchanged(before, input_snapshot(ROOT))
        require_unchanged(json.loads((candidate / 'source-hashes.json').read_text()), runtime_snapshot(ROOT))
    if passes[0] != passes[1]:
        raise RuntimeError('Two clean builds produced different artifacts')
    symbols = {row[2]: int(row[0], 16) for line in (candidate / 'emberbond.sym').read_text().splitlines()
               if len(row := line.split()) == 3}
    if not (0x03000000 <= symbols['__iwram_start'] <= symbols['__iwram_end'] <= 0x03007000):
        raise RuntimeError('Linked IWRAM overlaps the reserved stacks')
    if not (0x02000000 <= symbols['__data_start'] <= symbols['__bss_end'] <= 0x02040000):
        raise RuntimeError('Linked state exceeds EWRAM')
    rom = (candidate / 'emberbond.gba').read_bytes()
    if not 0xc0 <= len(rom) <= 32 * 1024 * 1024 or (sum(rom[0xa0:0xbe]) + 0x19) & 255:
        raise RuntimeError('Invalid cartridge size or GBA header checksum')
    if b'SRAM_V113' not in rom:
        raise RuntimeError('Cartridge lacks its SRAM identifier')
    (output / 'build.json').write_text(json.dumps({
        'passed': True, 'clean_builds': passes, 'rom_bytes': len(rom),
        'iwram_end': symbols['__iwram_end'], 'ewram_end': symbols['__bss_end'],
        'tools': {name: {'path': executable, 'sha256': sha(Path(executable)),
                         'version': subprocess.check_output([executable, '--version'], text=True).splitlines()[0]}
                  for name, executable in tools.items()},
    }, indent=2) + '\n')


def platform_checks(output, env):
    os.environ.update(env)
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.discover(str(ROOT / 'tests/trust'), pattern=pattern)
        for pattern in ('test_platform.py', 'test_asset_geometry.py'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'passed': result.wasSuccessful() and result.testsRun > 0 and not result.skipped,
              'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': len(result.skipped)}
    (output / 'platform.json').write_text(json.dumps(report, indent=2) + '\n')
    if not report['passed']:
        raise RuntimeError('Platform properties failed')


def inventory(output, env):
    run([sys.executable, 'tools/trust/contracts.py', '--output', str(output / 'inventory.json')],
        output, 'inventory', env)
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/trust', '-p', 'test_contracts.py', '-v'],
        output, 'contract-negatives', env)
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/trust', '-p', 'test_adapters.py', '-v'],
        output, 'adapter-negatives', env)


def native(output, env, candidate=None):
    candidate = candidate or output.parent / 'build' / 'candidate'
    require_unchanged(json.loads((candidate / 'source-hashes.json').read_text()), runtime_snapshot(ROOT))
    compiler = shutil.which(env.get('HOST_CC', 'cc'))
    if not compiler:
        raise RuntimeError('A native C compiler is required')
    bridge = output / 'observer.so'
    command = [compiler, '-std=c11', '-D_GNU_SOURCE', '-Wall', '-Wextra', '-Werror', '-O2', '-fPIC',
               '-dynamiclib' if sys.platform == 'darwin' else '-shared', str(ROOT / 'tools/trust/native_bridge.c')]
    if sys.platform == 'darwin':
        prefix = Path(subprocess.check_output(['brew', '--prefix', 'mgba'], text=True).strip())
        command += ['-I' + str(prefix / 'include'), '-L' + str(prefix / 'lib')]
        libraries = sorted((prefix / 'lib').glob('libmgba.0.10*.dylib'))
    else:
        prefix = ROOT / 'tools/sysroot/usr'
        if (prefix / 'include/mgba/core/core.h').is_file():
            command += ['-I' + str(prefix / 'include'), '-L' + str(prefix / 'lib/x86_64-linux-gnu'),
                        '-Wl,-rpath,' + str(prefix / 'lib/x86_64-linux-gnu')]
            libraries = sorted((prefix / 'lib/x86_64-linux-gnu').glob('libmgba.so*'))
        else:
            libraries = sorted(Path('/usr/lib/x86_64-linux-gnu').glob('libmgba.so*'))
    run(command + ['-lmgba', '-o', str(bridge)], output, 'observer-build', env)
    run([sys.executable, 'tools/trust/native_probe.py', '--rom', str(candidate / 'emberbond.gba'),
         '--symbols', str(candidate / 'emberbond.sym'), '--bridge', str(bridge), '--output', str(output)],
        output, 'native', env)
    report = json.loads((output / 'native.json').read_text())
    report['compiler'] = subprocess.check_output([compiler, '--version'], text=True).splitlines()[0]
    report['library_files'] = {str(path): sha(path) for path in libraries if path.is_file()}
    (output / 'native.json').write_text(json.dumps(report, indent=2) + '\n')
    if not report['passed']:
        raise RuntimeError('Native scenarios failed')


def assets(output, env):
    pinned = False
    if importlib.util.find_spec('PIL'):
        from PIL import __version__, features
        fonts = ('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        pinned = (__version__ == '13.0.0' and features.version_codec('zlib') == '1.3.1'
                  and all(Path(path).is_file() for path in fonts))
    if pinned:
        command = [sys.executable, 'tools/trust/assets.py', '--full', '--output', str(output / 'assets.json')]
        runtime = {'python': sys.version, 'platform': platform.platform()}
    else:
        image = env.get('TRUST_LINUX_IMAGE', 'codex-pillow-compat:20261027')
        image_id = subprocess.check_output(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], text=True).strip()
        command = ['docker', 'run', '--rm', '--pull=never', '--platform', 'linux/amd64',
                   '--mount', f'type=bind,source={ROOT},target=/source,readonly',
                   '--mount', f'type=bind,source={output},target=/evidence',
                   image_id, '/opt/pillow13/bin/python', '/source/tools/trust/assets.py',
                   '--root', '/source', '--full', '--output', '/evidence/assets.json']
        runtime = {'container_image': image_id}
    run(command, output, 'asset-generation', env, timeout=1200)
    (output / 'asset-runtime.json').write_text(json.dumps(runtime, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('check', choices=('inventory', 'build', 'platform', 'native', 'assets'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    destination = args.output or (Path(os.environ['TRUST_EVIDENCE_DIR']) if os.environ.get('TRUST_EVIDENCE_DIR') else None)
    if destination is None:
        parser.error('Supply --output or run through the trust harness')
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    env = environment()
    if args.check == 'native':
        native(destination, env, args.candidate.resolve() if args.candidate else None)
    else:
        {'inventory': inventory, 'build': build, 'platform': platform_checks, 'assets': assets}[args.check](destination, env)


if __name__ == '__main__':
    main()
