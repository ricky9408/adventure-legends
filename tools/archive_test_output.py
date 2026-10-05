#!/usr/bin/env python3
"""Preserve earlier ignored test evidence before a fresh exact-ROM run.

Only direct directories beneath this checkout's build/ are accepted. Renaming,
not deletion, retains earlier reports and prevents stale snapshot collisions.
"""
from pathlib import Path
import sys, time
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build'
for arg in sys.argv[1:]:
    source=Path(arg)
    if not source.is_absolute():source=ROOT/source
    if source.parent.resolve()!=BUILD.resolve() or source.is_symlink():
        raise SystemExit('Only direct, non-symlink build output directories may be archived')
    if not source.exists():continue
    if not source.is_dir():raise SystemExit('Test output must be a directory')
    archive=BUILD/'previous-test-runs'
    if archive.is_symlink():raise SystemExit('Archive directory must not be a symlink')
    archive.mkdir(exist_ok=True)
    target=archive/(source.name+'-'+str(time.time_ns()))
    source.rename(target)
    print('Preserved previous evidence:',target.relative_to(ROOT))
