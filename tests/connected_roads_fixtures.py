#!/usr/bin/env python3
"""Validated synthetic checkpoint fixtures for connected-road regression.

The starting ordinary SRAM was earned by the recorded Covenants E controller
run. Only checkpoint room/spawn are changed by this host fixture producer;
these outputs are explicitly synthetic and never count as player acquisition.
The unchanged game serializer/validator emits and reloads every result.
"""
from pathlib import Path
import ctypes as C,hashlib,json
from test_save5 import Save,Save5Tests
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tests/fixtures/v5-revision9/covenants-all128-72-cold.sav'
SOURCE_SHA='eec8efbfeaf83a51b66faa0c8e9d6a3061af36b88fb6d7b3aa77fbc47107122a'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class CheckpointFixtures:
 def __init__(self,out):
  self.out=Path(out);self.out.mkdir(parents=True,exist_ok=False);assert sha(SOURCE)==SOURCE_SHA
  Save5Tests.setUpClass();self.h=Save5Tests();self.h.reset();self.h.put(SOURCE.read_bytes());self.base=self.h.load();self.rows=[]
  self.original_noncheckpoint=(bytes(self.base.roster),bytes(self.base.quests),bytes(self.base.equipment),bytes(self.base.economy))
 def valid(self,room,spawn):
  s=Save.from_buffer_copy(bytes(self.base));s.campaign.room=room;s.campaign.spawn=spawn
  return s if self.h.lib.save5_validate(C.byref(s)) else None
 def create(self,room,spawn):
  s=self.valid(room,spawn)
  if s is None:return None
  before=bytes(s);self.h.reset();self.h.store(s);out=self.out/f'room-{room:02d}-spawn-{spawn}.sav';out.write_bytes(bytes(self.h.sram));loaded=self.h.load()
  assert (bytes(loaded.roster),bytes(loaded.quests),bytes(loaded.equipment),bytes(loaded.economy))==self.original_noncheckpoint
  assert loaded.campaign.room==room and loaded.campaign.spawn==spawn and bytes(s)==before
  row={'room':room,'spawn':spawn,'path':out.name,'sha256':sha(out),'bytes':out.stat().st_size,'synthetic_changes':['campaign.room','campaign.spawn'],'validated_and_roundtripped':True};self.rows.append(row);return out
 def close(self):
  report={'scope':__doc__,'source':str(SOURCE.relative_to(ROOT)),'source_sha256':SOURCE_SHA,'source_provenance_sha256':sha(SOURCE.parent/'provenance.json'),'source_bytes_unchanged':sha(SOURCE)==SOURCE_SHA,'helper_sha256':sha(__file__),'codec_sources':{n:sha(ROOT/'src'/n) for n in ('save4.c','save5.c','save4.h','save5.h')},'fixtures':self.rows}
  (self.out/'provenance.json').write_text(json.dumps(report,indent=2)+'\n');Save5Tests.doClassCleanups();return report

def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();f=CheckpointFixtures(a.output)
 try:
  for room in range(78):
   for spawn in range(6):f.create(room,spawn)
 finally:r=f.close()
 print(json.dumps({'passed':True,'fixtures':len(r['fixtures']),'source_sha256':r['source_sha256']}))
if __name__=='__main__':main()
