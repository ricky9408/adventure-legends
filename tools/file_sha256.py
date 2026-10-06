#!/usr/bin/env python3
"""Print one file's SHA256 without platform-specific shell digest tools."""
import hashlib
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: file_sha256.py FILE')
print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
