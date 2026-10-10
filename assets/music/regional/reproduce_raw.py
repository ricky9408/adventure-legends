#!/usr/bin/env python3
"""Portable exact PCM reproduction from bundled, audited performance manifests.
Usage: python reproduce_raw.py --output-dir /tmp/reproduced ROAD KELP
Omit cue names to reproduce all regional directories. HOME is a preserved
approved asset, not newly synthesized here. Requires only Python stdlib.
"""
import argparse,hashlib,json
from pathlib import Path
import approved_renderer as renderer
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output-dir',type=Path,required=True)
p.add_argument('cues',nargs='*')
a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
for directory in sorted(ROOT.iterdir()):
 if not directory.is_dir() or not (directory/'performance-manifest.json').exists():continue
 if a.cues and directory.name not in a.cues:continue
 report=json.loads((directory/'render-inputs.json').read_text())
 manifest=json.loads((directory/'performance-manifest.json').read_text())
 renderer.PALETTE=report['palette']
 samples,stems,events,info=renderer.render(manifest,16384)
 pcm,decoded=renderer.quantize_s8(samples)
 name=next(n for n in report['output_sha256'] if n.endswith('.raw'))
 digest=hashlib.sha256(pcm).hexdigest()
 assert digest==report['output_sha256'][name],(directory.name,'reproduction mismatch')
 (a.output_dir/name).write_bytes(pcm)
 print(directory.name,digest,flush=True)
