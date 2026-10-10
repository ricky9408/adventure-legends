"""Include-aware source view for retained synthetic/parser tests.

Only local quoted .inc fragments are expanded. Runtime statements are preserved
verbatim; headers stay normal includes so fixture headers remain authoritative.
This is a host adapter, not a replacement implementation or historical oracle.
"""
from pathlib import Path
import re


def expand_local_includes(path, stack=()):
    path = Path(path).resolve()
    if path in stack:
        raise AssertionError(f'recursive source include: {path}')
    def replace(match):
        child = path.parent / match.group(1)
        if not child.is_file():
            raise AssertionError(f'missing source include: {child}')
        return expand_local_includes(child, (*stack, path))
    return re.sub(r'^\s*#include\s+"([^"\n]+\.inc)"\s*$', replace,
                  path.read_text(), flags=re.M)
