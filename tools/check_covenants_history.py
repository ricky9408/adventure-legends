#!/usr/bin/env python3
"""Reproduce immutable8 policy exclusively from SHA-pinned accepted C source."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
from check_horizons_history import render
ROOT=Path(__file__).resolve().parents[1]
ORACLE=ROOT/'tests/fixtures/horizons-c-policy-oracle'
MANIFEST_SHA='de5129176b917cc7c3869089a7fd1b12bda6dce5fc2d1ab214867165b68bdeaf'
def render8(src):
 text=render(src.replace('quest_masks[60]','quest_masks[54]')).replace('history7_','history8_').replace('content7','content8').replace('before content8','before content9').replace('exact H','exact Horizons C').replace('return-h-policy-oracle','horizons-c-policy-oracle').replace('quest_masks[54]','quest_masks[60]')
 return re.sub(r'\bhorizons_', 'history8_horizons_', re.sub(r'creatures_form_allowed_revision\((\d+),7\)',r'creatures_form_allowed_revision(\1,8)',text))
def main():
 raw=(ORACLE/'manifest.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA:raise ValueError('Exact C manifest changed')
 extra=(ORACLE/'generator-inputs-manifest.json').read_bytes()
 if hashlib.sha256(extra).hexdigest()!='332bb762c54ab07e4fa2c422d14f5aa4f7204d0ae99d856a077a7ed9dd90edef':raise ValueError('Exact C generator-input manifest changed')
 for name,sha in dict(json.loads(raw)['files'],**json.loads(extra)['files']).items():
  if hashlib.sha256((ORACLE/name).read_bytes()).hexdigest()!=sha:raise ValueError('Exact C source changed: '+name)
 if (ROOT/'src/save5_revision8_policy.inc').read_text()!=render8((ORACLE/'src/save5.c').read_text()):raise ValueError('Immutable revision8 policy changed')
 expected_horizons='/* Frozen from accepted C before current9; no live Horizons quest rows. */\n'+re.sub(r'\bhorizons_','history8_horizons_',(ORACLE/'src/save5_horizons_policy.inc').read_text())
 if (ROOT/'src/save5_revision8_horizons.inc').read_text()!=expected_horizons:raise ValueError('Immutable revision8 Horizons rows changed')
 # Equipment rows are a fixed numeric extraction of all46 accepted source rows.
 equipment=(ORACLE/'src/equipment_data.c').read_text()
 quest_source=[int(x) for x in re.search(r'equipment_source_quest\[46\] = \{([^}]+)',(ORACLE/'src/save5.c').read_text())[1].split(',')]
 ids=[int(x) for x in re.search(r'equipment_authored_ids\[EQUIPMENT_AUTHORED_COUNT\] = \{([^}]+)',equipment)[1].split(',')]
 rows=[]
 for source,id_ in enumerate(ids):
  row=re.search(r'\['+str(id_)+r'\] = \{'+str(id_)+r', (\d+), \d+, (\d+),',equipment)
  rows.append((id_,int(row[1]),int(row[2]),0 if source==0 else 1 if quest_source[source]<0 else 2,quest_source[source]))
 actual=(ROOT/'src/save5_revision8_equipment.inc').read_text().split('save5_policy8_items[46] = {')[1]
 actual=[tuple(map(int,row.split(','))) for row in re.findall(r'\{([^{}]+)\}',actual)]
 if actual!=rows:raise ValueError('Immutable revision8 equipment/source rows changed')
 subprocess.run([sys.executable,str(ROOT/'tools/generate_creature_history.py'),'--check'],check=True)
 subprocess.run([sys.executable,str(ROOT/'tools/check_horizons_history.py')],check=True)
 subprocess.run([sys.executable,str(ORACLE/'assets/creatures/generate_data.py'),'--check'],check=True)
 subprocess.run([sys.executable,str(ORACLE/'assets/equipment/generate_data.py'),'--check'],check=True)
 print('Exact C source oracle and immutable revision8 verified; old1–7 retained')
if __name__=='__main__':main()
