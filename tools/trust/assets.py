#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
INPUTS = ('assets/generate_assets.py', 'assets/connected_road_art.py',
          'assets/redesign_characters.py', 'assets/generate_enemy_tactics.py',
          'assets/connected_roads.json')
OUTPUTS = ('src/assets.c', 'src/assets.h', 'src/asset_collisions.h',
           'src/enemy_tactics_art.inc')


class GenerationInterrupted(Exception):
    pass


def run_generator(command, *, cwd, env, timeout):
    managed = os.name == 'posix' and os.environ.get('TRUST_PROCESS_GROUP_MANAGED') == '1'
    owns_group = os.name == 'posix' and not managed
    child_env = {**env, 'TRUST_PROCESS_GROUP_MANAGED': '1'} if os.name == 'posix' else env
    cancelled = False
    interruptible = False

    def interrupted(_signal, _frame):
        nonlocal cancelled
        cancelled = True
        # Spawn and cleanup must retain control until the child can be reaped.
        if interruptible:
            raise GenerationInterrupted('Asset generation was interrupted')

    previous_handlers = {number: signal.getsignal(number)
                         for number in (signal.SIGTERM, signal.SIGINT)}
    process = None
    try:
        for number in previous_handlers:
            signal.signal(number, interrupted)
        process = subprocess.Popen(command, cwd=cwd, env=child_env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=owns_group)
        interruptible = True
        if cancelled:
            raise GenerationInterrupted('Asset generation was interrupted')
        stdout, stderr = process.communicate(timeout=timeout)
        if process.returncode:
            raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)
    finally:
        interruptible = False
        try:
            if process is not None:
                try:
                    if owns_group:
                        os.killpg(process.pid, signal.SIGKILL)
                    elif process.poll() is None:
                        process.kill()
                except ProcessLookupError:
                    pass
                process.wait()
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()
        finally:
            for number, handler in previous_handlers.items():
                signal.signal(number, handler)
    if cancelled:
        raise GenerationInterrupted('Asset generation was interrupted')
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_paths(root):
    return set(OUTPUTS) | {p.relative_to(root).as_posix()
                          for p in (root / 'src/asset_data').glob('*.inc')}


def compare_generated(root, generated):
    expected = output_paths(root)
    actual = output_paths(generated)
    if expected != actual:
        raise ValueError('Generated file set differs: ' + json.dumps({
            'missing': sorted(expected - actual), 'extra': sorted(actual - expected)}))
    mismatches = [name for name in sorted(expected)
                  if not (root / name).is_file() or not (generated / name).is_file()
                  or (root / name).read_bytes() != (generated / name).read_bytes()]
    if mismatches:
        raise ValueError('Generated source differs: ' + ', '.join(mismatches))
    return {name: digest(root / name) for name in sorted(expected)}


def verify(root):
    with tempfile.TemporaryDirectory(prefix='trust-assets-') as directory:
        generated = Path(directory)
        (generated / 'src').mkdir()
        for name in INPUTS:
            destination = generated / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / name, destination)
        runs = []
        for name in ('assets/generate_assets.py', 'assets/generate_enemy_tactics.py'):
            completed = run_generator(
                [sys.executable, name], cwd=generated,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONHASHSEED': '0'},
                timeout=90,
            )
            runs.append({'command': [sys.executable, name], 'stdout': completed.stdout})
        outputs = compare_generated(root, generated)
        import PIL
        return {'schema': 1, 'result': 'PASS', 'pillow': PIL.__version__,
                'inputs': {name: digest(root / name) for name in INPUTS},
                'generated_sources': outputs, 'runs': runs,
                'limitations': ['Only core palette, scenery, actors, collision geometry and enemy-tactics pixels are regenerated here.',
                                'Other regional art, text, music and preview compression require their separate checks.']}


def full_regeneration(root):
    from PIL import Image, ImageSequence, __version__ as pillow_version
    from contracts import visible_paths
    paths = [name for name in visible_paths(root)
             if not name.startswith(('build/', 'dist/', '.trust/runs/'))]
    with tempfile.TemporaryDirectory(prefix='trust-full-assets-') as directory:
        generated = Path(directory)
        for name in paths:
            source = root / name
            if source.is_symlink():
                raise ValueError('Asset regeneration cannot copy symlink inputs: ' + name)
            target = generated / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        before = {name: digest(generated / name) for name in paths
                  if name.startswith(('src/', 'assets/'))}
        completed = run_generator(
            ['make', 'assets', 'PYTHON=' + sys.executable], cwd=generated,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONHASHSEED': '0'},
            timeout=900,
        )
        after = {path.relative_to(generated).as_posix(): digest(path)
                 for folder in ('src', 'assets') for path in (generated / folder).rglob('*')
                 if path.is_file() and '__pycache__' not in path.parts}
        added = sorted(after.keys() - before.keys())
        removed = sorted(before.keys() - after.keys())
        changed = sorted(name for name in before.keys() & after.keys() if before[name] != after[name])
        semantic_changes = []
        metadata_only = []
        for name in changed:
            if Path(name).suffix.lower() in {'.png', '.gif'}:
                def frames(path):
                    with Image.open(path) as picture:
                        return [(frame.size, frame.convert('RGBA').tobytes(), frame.info.get('duration'))
                                for frame in ImageSequence.Iterator(picture)]
                if frames(root / name) == frames(generated / name):
                    metadata_only.append(name)
                    continue
            semantic_changes.append(name)
        extra_previews = [name for name in added if name.startswith('assets/')
                          and Path(name).suffix.lower() in {'.png', '.gif'}]
        problems = removed + semantic_changes + sorted(set(added) - set(extra_previews))
        return {'schema': 1, 'result': 'FAIL' if problems else 'PASS',
                'scope': 'Every generator in current make assets; all src bytes and existing asset semantics',
                'pillow': pillow_version, 'command': completed.args,
                'input_makefile_sha256': digest(root / 'Makefile'),
                'input_hashes': before, 'output_hashes': after,
                'source_or_asset_changes': semantic_changes, 'removed': removed,
                'added_outputs': added, 'additional_previews': extra_previews,
                'unexpected_added_inputs': sorted(set(added) - set(extra_previews)),
                'image_encoding_only_changes': metadata_only,
                'stdout': completed.stdout, 'stderr': completed.stderr,
                'limitations': ['Additional PNG/GIF previews are reported, not runtime inputs; other added paths fail.',
                                'Matching decoded image frames does not require identical PNG/GIF compression.',
                                'Selected PCM tables are regenerated from the retained audio sources; composition quality is not measured.',
                                'Byte equality proves generator consistency, not artistic quality or gameplay correctness.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    try:
        report = full_regeneration(args.root.resolve()) if args.full else verify(args.root.resolve())
    except (OSError, ValueError, subprocess.SubprocessError, GenerationInterrupted) as error:
        report = {'schema': 1, 'result': 'FAIL', 'error': str(error)}
        if isinstance(error, subprocess.CalledProcessError):
            report['stderr'] = error.stderr
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{report["result"]}: {args.output}')
    return int(report['result'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
