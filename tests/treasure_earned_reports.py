#!/usr/bin/env python3
"""Actual-controller reports from authenticated, unmodified G7 checkpoints.

North/South defeat their bosses again after cold Continue from pre-boss saves.
Magma/Underwater walk home from authentically READY boss-cleared saves. This is
cross-ROM earned-save integration, not an empty-SRAM candidate campaign. Both
RAM mutation and machine-state import APIs are hard-disabled by StrictNative.
"""
from __future__ import annotations
import argparse, ctypes as C, gzip, json, shutil, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from journey_guidance_earned import RegionalJourney, NorthernJourney, SouthernJourney
from treasure_player_flow import Save, QUEST, GOLD, sha, qstate
FIXTURES={'north':'north-machine-1-telegraph','south':'south-36-solved','magma':'magma-regulator-cleared','underwater':'underwater-08-guardian-settled'}

class EarnedReports(RegionalJourney):
    def __init__(self,a,source,report,t):
        self.treasure=t;self.treasure_observations=[];self.treasure_pending=None;self.receipt_count=0;self.pending_stable=True
        super().__init__(a,source,report)
        self.chapter=a.region
        self.check(not self.state().economy.later_claims,'unmodified G7 Continue implicitly awards no treasure')
    def state(self):return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
    save_state=state
    def raw_step(self,count,keys=0):
        for _ in range(count):
            was=self.get('game_state');before=self.state() if was==1 else None
            super().raw_step(1,keys)
            now=self.get('game_state')
            if was==1 and now==12:
                self.treasure_pending={'before':before,'frozen':{n:self.get(n)for n in ('room','px','py','hero_hp_q4','ability_cd','heal_cd','summoned')},'start':self.e.frame,'frames':0}
                self.pending_stable=True
            if self.treasure_pending and was==12:
                p=self.treasure_pending;p['frames']+=1
                if now==12:self.pending_stable &= bytes(self.state())==bytes(p['before'])
                self.pending_stable &= all(self.get(n)==v for n,v in p['frozen'].items())
    def settle_save(self,intrusive=False):
        for _ in range(1500):
            state=self.get('game_state')
            if state in (6,8,10,12):self.raw_step(1);continue
            if state==13:
                after=self.state();t=self.treasure;p=self.treasure_pending
                self.check(p is not None,'earned receipt follows observed real report transaction')
                before=p['before'];xp=sum(after.roster.instances[i].xp-before.roster.instances[i].xp for i in before.roster.party if i<160)
                self.check(self.pending_stable,'earned pending write freezes state, HP and remaining cooldown')
                self.check(qstate(before,QUEST[t])==2 and qstate(after,QUEST[t])==3,'authentically READY report becomes CLAIMED only at commit')
                self.check(after.economy.later_claims==before.economy.later_claims|(1<<t),'exactly one new named treasure is owned')
                self.check(after.economy.gold-before.economy.gold==min(GOLD[t],9999-before.economy.gold),'earned report pays exact clipped gold')
                self.check(self.get('game_shop_reward_gold')==after.economy.gold-before.economy.gold and self.get('game_shop_reward_xp')==xp,'earned receipt displays actual committed gold and EXP')
                self.check(bytes(before.equipment)==bytes(after.equipment)and bytes(before.roster.party)==bytes(after.roster.party),'earned report preserves gear and selected party')
                self.raw_step(3);self.e.screenshot(self.out/f'{self.chapter}-earned-treasure-receipt.png')
                self.treasure_observations.append({'treasure':t,'source_room':self.get('room'),'receipt_frame':self.e.frame,'pending_frames':p['frames'],'hp_q4':self.get('hero_hp_q4'),'ability_cd':self.get('ability_cd'),'gold':after.economy.gold-before.economy.gold,'xp':xp,'before_quest':qstate(before,QUEST[t]),'after_quest':qstate(after,QUEST[t]),'controller_only':True})
                self.receipt_count+=1;self.treasure_pending=None
                self.raw_step(2,'A');self.raw_step(3)
                self.check(self.get('game_state')==2,'fresh receipt A continues original regional story dialogue')
                self.e.screenshot(self.out/f'{self.chapter}-earned-closing-story.png')
                continue
            return
        raise AssertionError(('earned report failed to settle',self.status()))
    def run_treasure(self):
        t=self.treasure
        if t==0:NorthernJourney.machine(self,1)
        elif t==1:self.entry(37);SouthernJourney.machine(self,1)
        elif t==2:self.entry(38);self.target(160,176)
        else:self.entry(46);self.target(120,72)
        self.check(self.receipt_count==1,'one earned fresh report presents one saved treasure receipt')
        s=self.state();self.check(s.economy.later_claims==1<<t,'only the current region treasure was newly collected')
        self.settle();before=self.state()
        if t==0:self.act(120,124)
        elif t==1:self.use('start')
        elif t==2:self.target(160,176)
        else:self.target(120,72)
        after=self.state()
        self.check(bytes(after.economy)==bytes(before.economy) and bytes(after.roster)==bytes(before.roster),'repeat report cannot duplicate treasure gold EXP bond or creatures')
        self.cold_reboot('treasure-earned')
        self.check(bytes(self.state().economy)==bytes(before.economy),'cold Continue preserves exact new treasure and money')
        self.check(self.receipt_count==1,'cold Continue does not reissue a treasure receipt')
        self.history=[self.chapter];self.route_complete=True;self.snapshot('treasure-final')
    def report(self):
        super().report()
        p=self.out/'report.json'
        if p.exists():
            d=json.loads(p.read_text());d.update(suite='treasure-earned-report-integration',treasure_observations=self.treasure_observations,scope='Actual controller boss/report integration from authenticated unmodified G7 SRAM; not same-ROM empty-SRAM acceptance',receipt_count=self.receipt_count)
            p.write_text(json.dumps(d,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','bridge','source-manifest','output','earned-root'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True)
    p.add_argument('--regions',default='north,south,magma,underwater')
    a=p.parse_args();assert sha(a.rom)==a.expected_rom_sha and sha(a.symbols)==a.expected_symbols_sha
    assert not a.output.exists()or not any(a.output.iterdir());a.output.mkdir(parents=True,exist_ok=True)
    a.source_root=ROOT;a.cross_rom_diagnostic=True;a.baseline=False;a.diagnostic_boundary_report=a.earned_root/'regions/report.json';a.diagnostic_start_chapter='north';a.stop_after='covenants'
    a.candidate={'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'elf_sha256':sha(a.rom.with_suffix('.elf')),'source_manifest_sha256':sha(a.source_manifest),'bridge_sha256':sha(a.bridge)}
    manifest=json.loads(a.source_manifest.read_text());assert all(sha(ROOT/n)==v for n,v in manifest.items())
    source_report=json.loads(a.diagnostic_boundary_report.read_text());out=a.output;results=[]
    for region in a.regions.split(','):
        a.output=out/region;a.output.mkdir();a.region=region;r=None
        source=Path(source_report['snapshots'][FIXTURES[region]]['sram_path'])
        assert sha(source)==source_report['snapshots'][FIXTURES[region]]['sram_sha256']
        helpers={}
        for directory,pattern in (('tests','*.py'),('tools','mgba_runner.py')):
            for f in (ROOT/directory).glob(pattern):
                target=a.output/'helper-source'/directory/f.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);helpers[str(f.relative_to(ROOT))]=sha(target)
        (a.output/'helper-source-hashes.json').write_text(json.dumps(helpers,indent=2)+'\n')
        try:
            r=EarnedReports(a,source,a.diagnostic_boundary_report,('north','south','magma','underwater').index(region));r.run_treasure()
        except Exception as exc:
            traceback.print_exc()
            if r:r.failures.append({'error':repr(exc),'status':r.status()});r.e.screenshot(r.out/'failure.png')
            results.append({'region':region,'complete':False,'error':repr(exc)})
        finally:
            if r:
                r.close();report=json.loads((r.out/'report.json').read_text());rows=[]
                with gzip.open(r.out/'native-frames.jsonl.gz','rt')as f:
                    for line in f:
                        row=json.loads(line)
                        if row['phase']=='journey':rows.append(row)
                timing={'frames':len(rows),'max_native_cycles':max((x['cycles']for x in rows),default=0),'update_misses':sum(x['delta']!=1 for x in rows),'flip_misses':sum(not x['flip']for x in rows),'cycle_overruns':sum(x['cycles']>=280896 for x in rows)}
                results.append({'region':region,'complete':report['route_complete'],'failures':report['failures'],'checks':len(report['checks']),'timing':timing,'report':str(r.out/'report.json')})
        (out/'summary.json').write_text(json.dumps({'suite':'treasure-earned-reports','candidate':a.candidate,'controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'historical_progress_imports':'one unmodified authenticated G7 SRAM per region','results':results},indent=2)+'\n')
    return int(any(not x['complete']or x.get('failures')or any(x.get('timing',{}).get(k,0)for k in ('update_misses','flip_misses','cycle_overruns'))for x in results))
if __name__=='__main__':raise SystemExit(main())
