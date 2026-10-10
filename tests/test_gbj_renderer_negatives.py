#!/usr/bin/env python3
"""Preserve I4 renderer negative probes on the exact authenticated title inverse.

This is NOT a claim that historical I4 pins accept the current title source.
Current-title and font tampering is covered by verify_gbj_font_successor. The
old tests remain unchanged and every old mutation/CLI test runs on exact I4
renderer context, with only the proven credit draw removed from the input view.
"""
from pathlib import Path
import hashlib,json,tempfile,unittest
from verify_gbj_font_successor import verify,ROOT
assert hashlib.sha256((ROOT/'tests/test_renderer_equipment_successor.py').read_bytes()).hexdigest()=='c64c1b00333d24b6f47432ed4b23aa49cce5801b5ccbe2520611a54cb7a8583f'
import test_renderer_equipment_successor as original
c,normalized=verify()
with tempfile.TemporaryDirectory(prefix='gbj-renderer-negative-context-')as d:
 root=Path(d);(root/'src').mkdir();(root/'src/game.c').write_bytes(normalized)
 pins=json.loads((ROOT/'tests/fixtures/render-equipment-i4/reference.json').read_text())['context_source_pins']
 for path in pins:(root/path).write_bytes((ROOT/path).read_bytes())
 # Read-only original scripts/fixtures, never modified or repinned.
 (root/'tests').symlink_to(ROOT/'tests',target_is_directory=True)
 original.ROOT=root
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(original))
 raise SystemExit(not result.wasSuccessful())
