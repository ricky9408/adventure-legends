#!/usr/bin/env python3
"""Verify exact H policy inputs and reproduce the immutable revision7 include.

This never reads a live catalog or regenerates policy from current definitions.
An older revision is checked against the independently frozen H source closure.
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ORACLE=ROOT/'tests/fixtures/return-h-policy-oracle'
MANIFEST_SHA='1a5a74ad82a2856224118b0aaebe1e63bed9ec0e9c83f9b90772fa0cad80a3d9'
NAMES=('save5_campaign_validate','quest_objective_mask','quest_objective_validate','quest_fields_validate','quest_campaign_validate','quest_creatures_validate')
def render(src):
 def extract(name):
  match=re.search(r'^(?:static )?(?:int|unsigned) '+name+r'\([^;]+?\) \{',src,re.M)
  start=match.start();end=match.end();depth=1
  while depth:
   if src[end]=='{':depth+=1
   if src[end]=='}':depth-=1
   end+=1
  return src[start:end]
 out='/* Immutable exact H content7 validator. Frozen before content8 expansion.\n * Preserve these numeric checks and their fixed historical dependencies.\n * Source: tests/fixtures/return-h-policy-oracle/manifest.json. */\n'
 out+=re.search(r'static const Save4U8 quest_masks\[54\] = [^;]+;',src)[0].replace('quest_masks','history7_quest_masks')+'\n'
 for name in NAMES:
  f=extract(name)
  for old in NAMES:f=re.sub(r'\b'+old+r'\b','history7_'+old,f)
  f=f.replace('quest_masks','history7_quest_masks')
  f=re.sub(r'creatures_form\((\d+)\)',r'creatures_form_allowed_revision(\1,7)',f)
  if not f.startswith('static'):f='static '+f
  out+=f+'\n'
 return out

def main():
 raw=(ORACLE/'manifest.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA:raise ValueError('Exact H manifest changed')
 manifest=json.loads(raw)
 for file,sha in manifest['files'].items():
  if hashlib.sha256((ORACLE/file).read_bytes()).hexdigest()!=sha:raise ValueError('Exact H source changed: '+file)
 expected=render((ORACLE/'src/save5.c').read_text())
 if (ROOT/'src/save5_revision7_policy.inc').read_text()!=expected:raise ValueError('Immutable revision7 include changed')
 subprocess.run([sys.executable,str(ROOT/'tools/generate_creature_history.py'),'--check'],check=True)
 print('Exact H source oracle and immutable revision7 policy verified')
if __name__=='__main__':main()
