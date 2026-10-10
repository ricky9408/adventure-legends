#!/usr/bin/env python3
"""Losslessly archive completed matching traces; keep original hash claims.
Only remove a raw file after checking its report hash and round-tripping gzip.
"""
import gzip,hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for rel in sys.argv[1:]:
 folder=(ROOT/rel).resolve();report=folder/'report.json';d=json.loads(report.read_text());assert d['byte_exact'];receipts=[]
 for kind,expected in d['results'].items():
  raw=folder/kind/'trace.bin';archive=raw.with_suffix('.bin.gz');assert raw.is_file() and not archive.exists();assert sha(raw)==expected['sha256'] and raw.stat().st_size==expected['bytes'];temp=archive.with_suffix('.gz.pending')
  with raw.open('rb')as src,temp.open('wb')as dst:
   with gzip.GzipFile(filename='',mode='wb',compresslevel=9,mtime=0,fileobj=dst)as gz:
    while chunk:=src.read(1024*1024):gz.write(chunk)
   dst.flush();os.fsync(dst.fileno())
  digest=hashlib.sha256();count=0
  with gzip.open(temp,'rb')as gz:
   while chunk:=gz.read(1024*1024):digest.update(chunk);count+=len(chunk)
  assert digest.hexdigest()==expected['sha256'] and count==expected['bytes'];temp.rename(archive)
  receipt={'raw_path':str(raw.relative_to(ROOT)),'raw_sha256':expected['sha256'],'raw_bytes':expected['bytes'],'archive_path':str(archive.relative_to(ROOT)),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'round_trip_verified':True,'compression':'gzip level9, empty filename, mtime0','source_report_sha256':sha(report)}
  raw.unlink();receipt['raw_removed_after_verified_reversible_archive']=True;receipts.append(receipt)
  (folder/'storage-receipts.json').write_text(json.dumps({'report_unmodified':True,'receipts':receipts},indent=2)+'\n')
  print(json.dumps(receipt),flush=True)
 print('Recovered bytes',sum(x['raw_bytes']-x['archive_bytes']for x in receipts),flush=True)
