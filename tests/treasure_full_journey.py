#!/usr/bin/env python3
"""Same-candidate empty-SRAM adventure through homecoming and four treasures.

The unchanged G7 journey supplies route actions and native timing. This successor
entrypoint observes each real regional transaction and explicitly verifies its
saved receipt, original story continuation, passive ownership and preservation.
It forbids diagnostic/imported-progress CLI modes. StrictNative disables RAM
writes and machine-state imports. No game/runtime production code is changed.
"""
from __future__ import annotations
import argparse, ctypes as C, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
import journey_guidance_earned as journey
from treasure_player_flow import Save, QUEST, GOLD, sha, qstate

class TreasureOriginalJourney(journey.OriginalJourney):
    def __init__(self,*a,**kw):
        self.grove_entry_retry_done=False
        super().__init__(*a,**kw)
    def goto(self,*a,**kw):
        try:return super().goto(*a,**kw)
        except AssertionError:
            target_y=kw.get('y',a[1]if len(a)>1 else None)
            if not(self.get('game_state')==4 and self.get('room')==3 and self.get('boss_hp')==12 and target_y==100 and not self.grove_entry_retry_done):raise
            self.grove_entry_retry_done=True;before=self.status();deaths=self.get('deaths')
            self.check(self.get('hero_hp_q4')==0 and deaths>0,'first Grove approach ended in actual ordinary combat death')
            self.e.screenshot(self.out/'grove-approach-natural-death.png')
            self.tap('A',4,4);self.settle()
            self.check(self.get('room')==3 and self.get('game_state')==1 and self.get('hero_hp_q4')==self.e.read(self.sym['gear_stats'],2)and self.get('deaths')==deaths,'fresh A performs ordinary checkpoint retry with full health')
            self.cases.append({'case':'first-grove-approach-natural-death-and-retry','before':before,'after':self.status(),'controller_only':True,'game_ram_writes':0})
            self.coverage.append('first-grove-approach-ordinary-A-death-retry')
            self.select(0,summon=True)
            self.check(self.get('summoned')==1,'ordinary B resummons Fire after death cleared the companion')
            return super().goto(*a,**kw)

class TreasureRegionalJourney(journey.RegionalJourney):
    def __init__(self,*a,**kw):
        self.treasure_reports=[];self.treasure_pending=None;self.treasure_pending_stable=True
        super().__init__(*a,**kw)
    def state(self):return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
    save_state=state
    def raw_step(self,count,keys=0):
        for _ in range(count):
            was=self.get('game_state');before=self.state()if was==1 else None
            super().raw_step(1,keys)
            now=self.get('game_state')
            if was==1 and now==12:
                self.treasure_pending={'before':before,'frozen':{n:self.get(n)for n in ('room','px','py','hero_hp_q4','ability_cd','heal_cd','summoned')},'start':self.e.frame,'frames':0}
                self.treasure_pending_stable=True
            if self.treasure_pending and was==12:
                p=self.treasure_pending;p['frames']+=1
                if now==12:self.treasure_pending_stable &= bytes(self.state())==bytes(p['before'])
                self.treasure_pending_stable &= all(self.get(n)==v for n,v in p['frozen'].items())
    def settle_save(self,intrusive=False):
        for _ in range(1500):
            state=self.get('game_state')
            if state in (6,8,10,12):self.raw_step(1);continue
            if state==13:
                p=self.treasure_pending;after=self.state()
                self.check(p is not None,'treasure receipt follows an observed real report transaction')
                before=p['before'];bits=after.economy.later_claims^before.economy.later_claims
                self.check(bits in (1,2,4,8),'regional receipt commits exactly one new treasure')
                t=(1,2,4,8).index(bits)
                self.check(t==len(self.treasure_reports),'four treasures are acquired once in authored main-route order')
                self.check(qstate(before,QUEST[t])==2 and qstate(after,QUEST[t])==3,'real READY report reaches CLAIMED only on successful commit')
                self.check(self.treasure_pending_stable,'pending treasure leaves live save, HP, position and remaining cooldown unchanged')
                xp=sum(after.roster.instances[i].xp-before.roster.instances[i].xp for i in before.roster.party if i<160)
                gold=after.economy.gold-before.economy.gold
                self.check(gold==min(GOLD[t],9999-before.economy.gold),'first report pays exact actual clipped gold')
                self.check(self.get('game_shop_reward_gold')==gold and self.get('game_shop_reward_xp')==xp,'receipt shows actual earned gold and summed party EXP')
                self.check(bytes(before.equipment)==bytes(after.equipment) and bytes(before.roster.party)==bytes(after.roster.party) and before.roster.selected_party==after.roster.selected_party,'treasure acquisition preserves all gear and party selection')
                self.raw_step(3);shot=self.out/f'{self.chapter}-earned-treasure-receipt.png';self.e.screenshot(shot)
                self.treasure_reports.append({'treasure':t,'quest':QUEST[t],'source_room':self.get('room'),'session':self.session,'hardware_frame':self.e.frame,'pending_frames':p['frames'],'gold':gold,'xp':xp,'hero_hp_q4':self.get('hero_hp_q4'),'ability_cd':self.get('ability_cd'),'receipt_png_sha256':sha(shot)})
                self.receipts.append({'chapter':self.chapter,'frame':self.e.frame,'treasure':t});self.treasure_pending=None
                self.raw_step(2,'A');self.raw_step(3)
                self.check(self.get('game_state')==2,'fresh receipt A continues its original regional story')
                self.e.screenshot(self.out/f'{self.chapter}-earned-treasure-story.png')
                continue
            return
        raise AssertionError(('transaction failed to settle',self.status()))
    def run(self):
        super().run()
        if self.args.stop_after=='covenants':
            self.check(len(self.treasure_reports)==4 and self.state().economy.later_claims==15,'all four unique treasures remain owned at homecoming')
            self.coverage.append('four-treasures-earned-in-one-empty-SRAM-main-journey')
    def report(self):
        super().report()
        path=self.out/'report.json'
        if path.is_file():
            r=json.loads(path.read_text());r.update(suite='treasure-empty-SRAM-main-journey',treasure_reports=self.treasure_reports,later_claims=self.state().economy.later_claims)
            path.write_text(json.dumps(r,indent=2)+'\n')

def main():
    denied=('cross-rom-diagnostic','diagnostic-boundary-report','diagnostic-boundary-snapshot','diagnostic-start-chapter','diagnostic-original-report','baseline')
    assert not any(a.split('=')[0]=='--'+n for a in sys.argv[1:]for n in denied),'Fresh acceptance forbids imported or diagnostic progress modes'
    p=argparse.ArgumentParser(add_help=False);p.add_argument('--output',type=Path,required=True);a,_=p.parse_known_args()
    journey.OriginalJourney=TreasureOriginalJourney
    journey.RegionalJourney=TreasureRegionalJourney
    result=journey.main();path=a.output/'summary.json'
    if path.is_file():
        s=json.loads(path.read_text());region=a.output/'regions/report.json'
        r=json.loads(region.read_text())if region.is_file()else{}
        s.update(suite='treasure-empty-SRAM-opening-through-homecoming',treasure_reports=r.get('treasure_reports',[]),all_four_treasures_retained=r.get('later_claims')==15,successor_entrypoint_sha256=sha(__file__))
        if s['complete_fresh_main_journey']:
            s['accepted']=bool(s.get('accepted') and s['all_four_treasures_retained']and len(s['treasure_reports'])==4)
            result=result or int(not s['accepted'])
        path.write_text(json.dumps(s,indent=2)+'\n')
    return result
if __name__=='__main__':raise SystemExit(main())
