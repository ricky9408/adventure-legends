#!/usr/bin/env python3
"""Archive exact native memory evidence with deterministic gzip/hash receipts."""
from pathlib import Path
import argparse,gzip,hashlib,io,json,shutil,tarfile
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def compress(raw,dest,source):
 out=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',compresslevel=9,mtime=0,fileobj=out) as gz:gz.write(raw)
 data=out.getvalue();dest.write_bytes(data);assert gzip.decompress(data)==raw
 receipt={'source':str(source),'compressed_path':dest.name,'compressed_bytes':len(data),'compressed_sha256':sha(data),'uncompressed_bytes':len(raw),'uncompressed_sha256':sha(raw),'gzip_mtime':0,'gzip_filename':'','compression_level':9,'exact_original_bytes':True}
 dest.with_suffix(dest.suffix+'.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

def archive(source,dest):
 source=source.resolve();dest.mkdir(parents=True,exist_ok=True)
 observation=json.loads((source/'stack-observations.json').read_text());journey=json.loads((source/'return-journey.json').read_text())
 assert not observation['game_ram_writes'] and not observation['machine_state_loads'] and not observation['timing_is_release_acceptance_evidence']
 assert not journey['machine_state_loads']
 for name in ('stack-observations.json','helper-source-hashes.json','candidate-source-hashes.json'):
  shutil.copyfile(source/name,dest/name)
 receipts=[compress((source/'return-journey.json').read_bytes(),dest/'return-journey.json.gz',source/'return-journey.json')]
 helpers=json.loads((source/'helper-source-hashes.json').read_text());buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w',format=tarfile.USTAR_FORMAT) as archive:
  for relative,expected in sorted(helpers.items()):
   raw=(source/'helper-source'/relative).read_bytes();assert sha(raw)==expected
   info=tarfile.TarInfo(relative);info.size=len(raw);info.mode=0o644;info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';archive.addfile(info,io.BytesIO(raw))
 receipts.append(compress(buf.getvalue(),dest/'helper-source.tar.gz','authenticated helper-source files, normalized tar headers'))
 source_input=Path(observation['source_sram']['fixture_path']);source_raw=source_input.read_bytes()
 assert sha(source_raw)==observation['source_sram']['sram_sha256']
 (dest/'source-input.sav').write_bytes(source_raw)
 source_receipt={'file':'source-input.sav','sha256':sha(source_raw),'bytes':len(source_raw),'original_path':str(source_input)}
 sram=[]
 for name,record in journey['snapshots'].items():
  original=Path(record['sram_path']);raw=original.read_bytes();assert sha(raw)==record['sram_sha256']
  (dest/(name+'.sav')).write_bytes(raw);sram.append({'snapshot':name,'file':name+'.sav','bytes':len(raw),'sha256':sha(raw)})
 summary={'raw_evidence_path':str(source),'source_input':source_receipt,'finished_scope':observation['finished_scope'],'functional_failures':journey['failures'],'timing_is_acceptance_evidence':False,'observations':len(observation['observations']),'last_hardware_frame':max(x['hardware_frame'] for x in observation['observations']),'maximum_observed_overwritten_extent_bytes':max(x['overwritten_extent_bytes'] for x in observation['observations']),'minimum_unmodified_prefix_bytes':min(x['unmodified_prefix_bytes'] for x in observation['observations']),'all_sampled_bottom_guards_intact':all(x['bottom_64_bytes_intact'] for x in observation['observations']),'functional_check_count':len(journey['checks']),'snapshot_sram_receipts':sram,'compression_receipts':receipts}
 (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(archive(a.source,a.output),indent=2))
if __name__=='__main__':main()
