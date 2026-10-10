#!/usr/bin/env python3
"""Exact production fixed-slot Party raster versus pinned original rectangles."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
fixture=ROOT/'tests/fixtures/player-feedback-proposed/party_original_card.inc'
assert hashlib.sha256(fixture.read_bytes()).hexdigest()==json.loads(fixture.with_suffix('.json').read_text())['fixture_sha256']
with tempfile.TemporaryDirectory(prefix='feedback-party-pixels-') as tmp:
 for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  exe=Path(tmp)/label
  subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc',*flags,'tests/player_feedback_party_pixels_host.c','src/progression.c','src/creatures.c','src/creature_data.c','-o',str(exe)],cwd=ROOT,check=True)
  subprocess.run([str(exe)],cwd=ROOT,check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0',UBSAN_OPTIONS='halt_on_error=1'))
