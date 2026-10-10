"""Resolve and freeze the bridge's real mGBA library; OS libraries stay host-provided."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

_handles = {}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def output(command):
    return subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout


def identity(path):
    """Read the actual library loader identity, not a guessed distro filename."""
    if sys.platform == 'darwin':
        rows = output(['otool', '-D', str(path)]).splitlines()[1:]
        assert len(rows) == 1, 'Expected one mGBA install identity'
        return rows[0].strip()
    text = output(['readelf', '-d', str(path)])
    match = re.search(r'\(SONAME\).*?\[([^]]+)\]', text)
    assert match, 'mGBA library has no verified ELF SONAME'
    return match.group(1)


def resolve_mgba(bridge, specified=None):
    bridge = Path(bridge).resolve()
    if sys.platform == 'darwin':
        discovery = output(['otool', '-L', str(bridge)])
        names = [line.strip().split(' (', 1)[0] for line in discovery.splitlines()[1:] if 'libmgba' in line]
    else:
        dynamic = output(['readelf', '-d', str(bridge)])
        names = [name for name in re.findall(r'\(NEEDED\).*?\[([^]]+)\]', dynamic) if 'libmgba' in name]
        discovery = output(['ldd', str(bridge)])
    assert len(names) == 1, 'Expected exactly one mGBA dynamic dependency'
    needed = names[0]
    if specified:
        library = Path(specified).resolve()
    elif sys.platform == 'darwin':
        assert Path(needed).is_absolute(), 'Pass --mgba-library for an unresolved @rpath mGBA installation'
        library = Path(needed).resolve()
    else:
        match = re.search(r'^\s*' + re.escape(needed) + r'\s+=>\s+(.+?)\s+\(0x[0-9a-fA-F]+\)', discovery, re.M)
        assert match, 'mGBA dependency is unresolved; install libmgba-dev or pass --mgba-library'
        library = Path(match.group(1)).resolve()
    assert library.is_file(), 'Resolved mGBA library does not exist'
    soname = identity(library)
    assert soname == needed, ('Specified mGBA loader identity does not match bridge', soname, needed)
    return library, soname, discovery


def preload_frozen(root):
    root = Path(root)
    receipt = root / 'emulator-library.json'
    if not receipt.is_file():
        return
    data = json.loads(receipt.read_text())
    bridge = root / 'tools/mgba_bridge.so'
    library = root / data['library']['relative_path']
    assert digest(bridge) == data['bridge_sha256']
    assert digest(library) == data['library']['sha256']
    key = str(library.resolve())
    if key not in _handles:
        _handles[key] = ctypes.CDLL(key, mode=ctypes.RTLD_GLOBAL)


def frozen_environment(root):
    directory = str((Path(root) / 'tools/emulator-libs').resolve())
    key = 'DYLD_LIBRARY_PATH' if sys.platform == 'darwin' else 'LD_LIBRARY_PATH'
    return {key: directory + (os.pathsep + os.environ[key] if os.environ.get(key) else '')}


def freeze_emulator_library(source_root, destination_root, specified=None):
    source_root, destination_root = Path(source_root), Path(destination_root)
    bridge = source_root / 'tools/mgba_bridge.so'
    prior = source_root / 'emulator-library.json'
    if prior.is_file() and not specified:
        receipt = json.loads(prior.read_text())
        library = source_root / receipt['library']['relative_path']
        assert digest(bridge) == receipt['bridge_sha256'] and digest(library) == receipt['library']['sha256']
        soname = identity(library)
        assert soname == receipt['library']['loader_identity']
        discovery = (source_root / 'emulator-dependencies.txt').read_text()
    else:
        library, soname, discovery = resolve_mgba(bridge, specified)
    name = Path(soname).name
    assert name and name not in ('.', '..')
    relative = 'tools/emulator-libs/' + name
    target = destination_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(library, target)
    data = {'bridge_sha256': digest(bridge), 'platform': sys.platform,
            'library': {'source_path': str(library.resolve()), 'loader_identity': soname,
                        'relative_path': relative, 'sha256': digest(target)},
            'scope': 'Bridge and libmgba are frozen; other OS/shared-library dependencies remain host-provided',
            'discovery_report_sha256': hashlib.sha256(discovery.encode()).hexdigest()}
    (destination_root / 'emulator-library.json').write_text(json.dumps(data, indent=2) + '\n')
    (destination_root / 'emulator-dependencies.txt').write_text(discovery)
    return {relative: digest(target), 'emulator-library.json': digest(destination_root / 'emulator-library.json'),
            'emulator-dependencies.txt': digest(destination_root / 'emulator-dependencies.txt')}
