#!/usr/bin/env python3
"""Independent header9/CRC/exact-payload check of an already observed native C import."""
from pathlib import Path
import argparse,binascii,hashlib,importlib.util,json
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--adapter',type=Path,required=True);p.add_argument('--native-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();src=a.adapter/'source';receipt=json.loads((a.adapter/'adapter-receipt.json').read_text());native=json.loads(a.native_report.read_text());snapshot=native['snapshots']['00-currentC-exact-import']
 for key,name in [('rom_sha256','emberbond.gba'),('elf_sha256','emberbond.elf'),('symbols_sha256','emberbond.sym'),('source_manifest_sha256','source-hashes.json')]:assert native[key]==receipt['candidate'][name]
 assert native['controller_only'] and not native['game_ram_writes'] and not native['machine_state_loads'];assert snapshot['sram_export']=='mCore.savedataClone'
 original=src/native['provenance']['fixture_path'];current=a.native_report.parent/Path(snapshot['sram_path']).name;assert sha(original)==native['provenance']['sram_sha256'];assert sha(current)==snapshot['sram_sha256']
 spec=importlib.util.spec_from_file_location('explicit_current9_checker',src/'tests/retained_migration_validator.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 def newest(raw,revision):
  best=None
  for offset in module.BANK_OFFSETS:
   b=raw[offset:offset+module.BANK_SIZE]
   try:module.validate_bank(b,revision)
   except AssertionError:continue
   if best is None or 0<(int.from_bytes(b[8:12],'little')-int.from_bytes(best[8:12],'little'))%2**32<2**31:best=b
  assert best is not None;return best
 before=original.read_bytes();after=current.read_bytes();old=newest(before,8);new=newest(after,9);assert module.validate_migration(old,new,before,after,8)
 negatives=[]
 for mode in ('wrong-current-header','crc-valid-changed-payload','lost-prior-bank'):
  bank=bytearray(new);image=bytearray(after)
  if mode=='wrong-current-header':bank[12:14]=(8).to_bytes(2,'little')
  elif mode=='crc-valid-changed-payload':
   bank[160]^=1;bank[16:20]=bytes(4);bank[20]=0;bank[16:20]=binascii.crc32(bank).to_bytes(4,'little');bank[20]=0xa5
  else:image[after.index(old)+100]^=1
  try:module.validate_migration(old,bank,before,image,8)
  except AssertionError:negatives.append(mode)
  else:raise AssertionError(('negative escaped',mode))
 report={'scope':__doc__,'current_header':9,'prior_header':8,'exact_payload_preserved':True,'prior_committed_bank_preserved':True,'independent_crc_validated':True,'no_runtime_or_save_mutation':True,'negative_controls_rejected':negatives,'native_report_sha256':sha(a.native_report),'source_sram_sha256':sha(original),'native_current_sram_sha256':sha(current),'candidate':receipt['candidate'],'validator_sha256':sha(src/'tests/retained_migration_validator.py')};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS: native-observed8→9 exact payload/CRC/prior-bank preservation; three malformed alternatives rejected')
if __name__=='__main__':main()
