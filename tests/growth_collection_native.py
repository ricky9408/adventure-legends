#!/usr/bin/env python3
"""Controller-only fresh journal inspection plus separately labeled old collection.
No game-RAM writes,machine states,personal saves or acquisition claims for fixtures.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from journey_guidance_earned import StrictNative
from test_save5 import Save
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(a,fixture=None):
 label='historical-full-collection'if fixture else'fresh-opening';out=a.output/label;out.mkdir(parents=True,exist_ok=False)
 sym={v[2]:int(v[0],16)for line in a.symbols.read_text().splitlines()if len(v:=line.split())==3}
 inputs=[];shots=[];profiles=[];checks=[];fixture_sha=sha(fixture)if fixture else None
 with StrictNative(a.rom,a.bridge)as e:
  def g(n):return e.read(sym[n])
  def step(n=1,buttons=0,measure=True):
   inputs.append({'frame':e.frame,'frames':n,'buttons':buttons});previous=g('frame');page=e.read(0x04000000,2)&16
   for _ in range(n):
    e.frames(1,buttons);now=g('frame');next_page=e.read(0x04000000,2)&16
    if measure and g('game_state')in(3,7):profiles.append({'hw':e.frame,'state':g('game_state'),'journal':g('journal_tab'),'delta':(now-previous)&0xffffffff,'flip':int(page!=next_page),'cycles':g('render_cycles'),'card':g('render_profile_card'),'update':g('render_profile_update')})
    previous=now;page=next_page
  def tap(k):step(2,k);step(5)
  def snapshot():return e.bytes(sym['adventure_save'],C.sizeof(Save))
  def shot(name):
   step(8);p=out/(name+'.png');e.screenshot(p);shots.append({'file':p.name,'sha256':sha(p),'frame':e.frame,'state':g('game_state'),'journal':g('journal_tab')})
  def check(value,name):checks.append({'check':name,'passed':bool(value)});assert value,name
  if fixture:e.load_save(fixture);e.reset()
  step(180,measure=False);tap('A')
  for _ in range(2400):
   state=g('game_state')
   if state==1 and not g('scene_present_phase')and not g('save_requested')and not g('save_feedback_background'):break
   if state in(2,14):tap('A')
   else:step(1,measure=False)
  check(g('game_state')==1,'reached playable state without RAM or machine-state writes')
  step(60,measure=False);tap('START');baseline=snapshot();cooldown=g('ability_cd');heal=g('heal_cd');sram=e.bytes(0x0e000000,32768)
  shot('01-hub')
  if not fixture:
   tap('DOWN');tap('RIGHT');tap('A');check(g('journal_tab')==3,'A opens Growth');shot('02-growth-xp-next')
   tap('DOWN');tap('A');check(g('game_state')==7,'unready evolution opens all goals');shot('03-all-unmet-goals')
   tap('DOWN');shot('04-personal-wish-below-level-bond');tap('DOWN');shot('05-new-technique-preview');tap('B');tap('B')
   check(snapshot()==baseline and g('ability_cd')==cooldown and g('heal_cd')==heal,'goal and clue browsing preserves wholeSave5 and recovery')
  # Appended cell8 keeps every established0..7 category stable.
  if not fixture:
   tap('LEFT');tap('DOWN');tap('DOWN');tap('DOWN')
  else:
   for _ in range(4):tap('DOWN')
  check(g('journal_nav_category')==8,'collection cell reachable with four-way controller navigation');tap('A');check(g('journal_tab')==17,'A opens collection')
  shot('06-cumulative-history-family-list');tap('A');shot('07-family-form-owned')
  if fixture:
   tap('B')
   for target,name in((13,'magma'),(17,'underwater')):
    for _ in range(60):
     if g('collection_journal_family')==target:break
     tap('DOWN')
    check(g('collection_journal_family')==target,'historical '+name+' family reached');tap('A');shot('08-'+name+'-form-history');tap('RIGHT');shot('09-'+name+'-owned-branch');tap('B')
   tap('RIGHT');shot('10-owned-family-filter');tap('RIGHT');shot('11-missing-family-filter')
  else:
   tap('A');check(g('journal_tab')==2 and g('quickparty_menu_candidate')==0,'owned form opens exact Party candidate without assigning');shot('08-owned-party-handoff')
  check(snapshot()==baseline,'collection inspection preserves entireSave5 including cumulative history and individual identity')
  check(e.bytes(0x0e000000,32768)==sram,'inspection requests no save and leaves cartridgeSRAM unchanged')
  check(not int(e.lib.eb_faults(e.ptr)),'native core fault count remainszero')
  if fixture:check(sha(fixture)==fixture_sha,'input developer fixture file untouched')
 result={'result':'PASS','scope':'historical developer full collection inspection;not acquisition'if fixture else'fresh-controller-earned opening and journal inspection','rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'bridge_sha256':sha(a.bridge),'harness_sha256':sha(__file__),'source_manifest_sha256':sha(a.rom.parent/'source-hashes.json'),'fixture_sha256':fixture_sha,'game_ram_writes':0,'machine_state_imports':0,'checks':checks,'captures':shots,'inputs':inputs,'profiles':profiles,'max_menu_cycles':max((x['cycles']for x in profiles),default=0),'menu_update_misses':sum(x['delta']!=1 for x in profiles),'menu_cycle_overruns':sum(x['cycles']>280896 for x in profiles)}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(label,{k:result[k]for k in('result','max_menu_cycles','menu_update_misses','menu_cycle_overruns')},flush=True)
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--fixture',type=Path);a=p.parse_args()
 a.rom=a.rom.resolve();a.symbols=a.symbols.resolve();a.bridge=a.bridge.resolve()
 manifest=json.loads((a.rom.parent/'source-hashes.json').read_text());assert all(sha(ROOT/k)==v for k,v in manifest.items()),'Current runtime source must match frozen ROM build'
 a.output.mkdir(parents=True,exist_ok=False)
 runs=[run(a)];
 if a.fixture:runs.append(run(a,a.fixture))
 (a.output/'summary.json').write_text(json.dumps({'result':'PASS','runs':[r['scope']for r in runs],'native_screenshots':sum(len(r['captures'])for r in runs)},indent=2)+'\n')
if __name__=='__main__':main()
