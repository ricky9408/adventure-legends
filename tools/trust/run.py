import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys


def main():
    sys.dont_write_bytecode = True
    vendor = Path(__file__).resolve().parent / 'vendor'
    manifest = vendor / 'ORIGIN.json'
    if vendor.is_symlink() or not vendor.is_dir():
        raise SystemExit('Harness vendor root must be a regular directory')
    if not stat.S_ISREG(manifest.lstat().st_mode):
        raise SystemExit('Harness origin must be a regular file')
    origin = json.loads(manifest.read_text())
    expected = origin['files']
    if not isinstance(expected, dict) or not expected:
        raise SystemExit('Harness origin must pin a nonempty package')
    directories = set()
    for name in expected:
        if not isinstance(name, str):
            raise SystemExit('Harness pin paths must be strings')
        relative = PurePosixPath(name)
        if (not name.startswith('trustkit/') or relative.is_absolute() or
                '..' in relative.parts or '\\' in name or name != relative.as_posix()):
            raise SystemExit('Harness pins must name normalized package files')
        directories.update(parent.as_posix() for parent in relative.parents if parent != PurePosixPath('.'))
    files = {}
    for path in vendor.rglob('*'):
        name = path.relative_to(vendor).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode) and name in directories:
            continue
        if not stat.S_ISREG(mode):
            raise SystemExit('Harness vendor contents must be pinned regular files or package directories')
        if name == 'ORIGIN.json':
            continue
        if name not in expected:
            raise SystemExit('Unpinned harness vendor file: ' + name)
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    if files != expected:
        raise SystemExit('Harness pin mismatch: review and import a tested upstream release')
    sys.path.insert(0, str(vendor))
    from trustkit.cli import main as trust_main
    return trust_main()


if __name__ == '__main__':
    raise SystemExit(main())
