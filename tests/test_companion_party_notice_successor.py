#!/usr/bin/env python3
"""Retain every legendary-party notice assertion and link the real UI table.

Companion identity titles now read ui_texts widths. The historical synthetic
notice harness omitted that link dependency; no assertion or mock changes.
"""
from pathlib import Path
import hashlib
from verify_companion_browsing_successor import verify
ROOT=Path(__file__).resolve().parents[1]
verify();p=ROOT/'tests/test_covenants_party_notice.py';raw=p.read_bytes()
EXPECTED='1151c6a8dfcb312a5518cd2fc5cad92e5e44151cab6972a371357ac527f20ce3'
assert hashlib.sha256(raw).hexdigest()==EXPECTED
s=raw.decode();before="'src/companion_guide_text.c','-o',str(exe)";after="'src/companion_guide_text.c','src/ui.c','-o',str(exe)"
assert s.count(before)==1;s=s.replace(before,after)
exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
