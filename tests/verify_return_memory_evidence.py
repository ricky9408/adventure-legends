#!/usr/bin/env python3
"""Verify shipped Return memory evidence, exact gzip bytes, helper and SRAM hashes."""
from pathlib import Path
import argparse,gzip,hashlib,io,json,tarfile
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=ROOT/'docs/return-memory');p.add_argument('--write-checksums',action='store_true');a=p.parse_args();root=a.directory.resolve()
 if a.write_checksums:
  records={str(f.relative_to(root)):{'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())} for f in sorted(root.rglob('*')) if f.is_file() and f.name!='CHECKSUMS.json'}
  (root/'CHECKSUMS.json').write_text(json.dumps(records,indent=2)+'\n')
 records=json.loads((root/'CHECKSUMS.json').read_text());assert records
 assert set(records)=={str(f.relative_to(root)) for f in root.rglob('*') if f.is_file() and f.name!='CHECKSUMS.json'},'Untracked/missing evidence files'
 for name,r in records.items():
  raw=(root/name).read_bytes();assert len(raw)==r['bytes'] and sha(raw)==r['sha256'],name
 for receipt in root.rglob('*.gz.receipt.json'):
  r=json.loads(receipt.read_text());packed=(receipt.parent/r['compressed_path']).read_bytes();raw=gzip.decompress(packed)
  assert len(packed)==r['compressed_bytes'] and sha(packed)==r['compressed_sha256']
  assert len(raw)==r['uncompressed_bytes'] and sha(raw)==r['uncompressed_sha256']
  assert packed[3]&8==0 and packed[4:8]==b'\0'*4 and r['exact_original_bytes']
 for summary in root.rglob('summary.json'):
  d=summary.parent;r=json.loads(summary.read_text());o=json.loads((d/'stack-observations.json').read_text());j=json.loads(gzip.decompress((d/'return-journey.json.gz').read_bytes()))
  assert not o['game_ram_writes'] and not o['machine_state_loads'] and not o['timing_is_release_acceptance_evidence']
  assert not j['machine_state_loads'] and j['rom_sha256']==o['diagnostic']['rom_sha256']
  assert len(o['observations'])==r['observations']
  for row in [r['source_input'],*r['snapshot_sram_receipts']]:
   raw=(d/row['file']).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
  helpers=json.loads((d/'helper-source-hashes.json').read_text())
  with tarfile.open(fileobj=io.BytesIO(gzip.decompress((d/'helper-source.tar.gz').read_bytes())),mode='r:') as archive:
   assert set(archive.getnames())==set(helpers)
   for name,h in helpers.items():assert sha(archive.extractfile(name).read())==h
  if r['finished_scope']:
   assert not r['functional_failures'] and r['all_sampled_bottom_guards_intact']
 print(json.dumps({'files_verified':len(records),'gzip_receipts_verified':len(list(root.rglob('*.gz.receipt.json'))),'native_evidence_sets_verified':len(list(root.rglob('summary.json'))),'passed':True},indent=2))
if __name__=='__main__':main()
