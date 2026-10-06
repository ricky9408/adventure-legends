#!/usr/bin/env python3
"""Verify both repository and shipped memory evidence, including lossless gzip.
The three publication-omitted raw trace files are not required to be present.
"""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 count=0
 for relative,expected in json.loads((ROOT/'CHECKSUMS.json').read_text()).items():
  p=ROOT/relative;assert p.is_file(),str(p);assert sha(p.read_bytes())==expected,relative;count+=1
 for receipt_path in sorted(ROOT.glob('candidate-*/native50-all16-cadence-traces.compression.json')):
  receipt=json.loads(receipt_path.read_text());folder=receipt_path.parent;compressed=(folder/receipt['compressed_file']).read_bytes();raw=gzip.decompress(compressed)
  assert len(compressed)==receipt['compressed_bytes'] and sha(compressed)==receipt['compressed_sha256']
  assert len(raw)==receipt['uncompressed_bytes'] and sha(raw)==receipt['uncompressed_sha256']
  assert compressed[4:8]==bytes(4),'gzip mtime must be zero'
  assert not (compressed[3]&8),'gzip original filename must be absent'
  assert isinstance(json.loads(raw),list),'Expected original cadence window list'
  original=folder/receipt['uncompressed_original_filename']
  if original.exists():assert original.read_bytes()==raw
  print(f'{folder.name}: exact {len(raw)} raw bytes verified from {len(compressed)} compressed bytes')
 policy=json.loads((ROOT/'packaging-notes.json').read_text())
 for path in policy['required_tsv_paths']:
  relative=path.removeprefix('docs/underwater-memory/');assert (ROOT/relative).is_file();assert relative in json.loads((ROOT/'CHECKSUMS.json').read_text())
 print(f'{count} shipped evidence file hashes and all four stack-usage TSV files verified')
if __name__=='__main__':main()
