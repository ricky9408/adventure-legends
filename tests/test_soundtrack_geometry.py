#!/usr/bin/env python3
"""Unchanged current geometry checks behind the full soundtrack successor proof.

The older font-specific pixel method stays explicitly excluded in the original
wrapper; historical G5 negatives and current GBJ pixels run separately.
"""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'tests/test_gbj_return_geometry.py';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='62f894fb24830b77ecc01e9f5420b0818afdba54cf72b198e47e9c41f9281613'
s=raw.decode();before='from verify_gbj_font_successor import verify';after='from verify_soundtrack_successor import verify'
assert s.count(before)==1;s=s.replace(before,after)
exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
