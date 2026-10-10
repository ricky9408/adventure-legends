#!/usr/bin/env python3
"""Exact-candidate mGBA treasure integration matrix.

Prepared regional cases import authenticated G7 SRAM, then explicitly log RAM
preparation. They prove controller integration, not controller acquisition.
The earned village recovery case imports unmodified G7 SRAM and forbids writes.
All timing is native hardware-frame/cycle observation, never host throughput.
"""
from __future__ import annotations
import argparse, ctypes as C, gzip, hashlib, json, shutil, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Run, Native, sha, LIMIT
from test_save5 import CampaignSave, Roster, Quests, Equipment, Instance

class Economy(C.Structure):
    _fields_=[('earned',C.c_uint),('spent',C.c_uint),('gold',C.c_ushort),('bought',C.c_ushort*2),('used',C.c_ushort*2),('supplies',C.c_ubyte*2),('relics',C.c_ubyte),('upgrade',C.c_ubyte),('boss_claims',C.c_ubyte),('later_claims',C.c_ubyte),('reserved',C.c_ubyte*8)]
class Save(C.Structure):
    _fields_=[('campaign',CampaignSave),('roster',Roster),('quests',Quests),('equipment',Equipment),('economy',Economy)]
QUEST=(21,24,32,40);GOLD=(80,100,120,160)
SOURCE=((0,29,120,122,1,5),(0,22,312,206,1,0),(1,37,120,126,1,5),(1,30,400,206,1,0),(2,38,160,190,1,0),(3,46,120,86,1,0))
FIXTURE=('north-machine-1-cleared','south-boss-1-cleared','magma-regulator-cleared','underwater-08-guardian-settled')
CLAIMED=('north-north-main-before-continue','south-south-main-before-continue','magma-magma-main-before-continue','underwater-underwater-main-before-continue')

def qstate(s,q):return (s.quests.states[q>>2]>>((q&3)*2))&3

def changeq(s,q,state):
    s.quests.states[q>>2]=(s.quests.states[q>>2]&~(3<<((q&3)*2)))|(state<<((q&3)*2))
    if state==2:s.quests.rewards[q>>3]&=~(1<<(q&7))

class TreasureRun(Run):
    def __init__(self,a):
        super().__init__(a)
        self.events=[];self.native_windows=[];self.authenticated_inputs=[];self.strict_controller=False
        source=Path(__file__);target=self.out/'test-source/tests/treasure_player_flow.py';shutil.copyfile(source,target)
        self.hashes['test_sources']['tests/treasure_player_flow.py']=sha(target)
        self.earned_root=a.earned_root.resolve();self.earned_report=self.earned_root/'regions/report.json'
        self.earned=json.loads(self.earned_report.read_text())
        assert self.earned['route_complete'] and not self.earned['failures']
        self.hashes['earned_G7_report_sha256']=sha(self.earned_report)
        self.hashes['earned_G7_candidate']=self.earned['candidate']
    def put(self,*a,**kw):
        assert not self.strict_controller,'earned controller case forbids RAM writes'
        return super().put(*a,**kw)
    def save_state(self):return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
    def patch_save(self,s,reason):
        assert not self.strict_controller
        before=self.e.bytes(self.sym['adventure_save'],C.sizeof(Save));after=bytes(s)
        changed=[]
        for i,(x,y) in enumerate(zip(before,after)):
            if x!=y:self.e.write(self.sym['adventure_save']+i,y,1);changed.append([i,x,y])
        self.writes.append({'case':self.case,'emulator_id':self.emulator_id,'frame':self.e.frame,'symbol':'adventure_save','reason':reason,'byte_changes':changed,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest()})
    def fixture_path(self,name):
        row=self.earned['snapshots'][name];p=self.earned_root/'regions'/(name+'.sav');assert sha(p)==row['sram_sha256']
        self.authenticated_inputs.append({'case':self.case,'name':name,'path':str(p),'sha256':sha(p),'source_candidate':self.earned['candidate'],'source_quests':{str(q):row['quests'][q] for q in QUEST}})
        return p
    def mark(self,label):
        s=self.save_state();row={'label':label,'case':self.case,'frame':self.e.frame,'gold':s.economy.gold,'later_claims':s.economy.later_claims,'quests':{str(q):qstate(s,q)for q in QUEST},'party_xp':[s.roster.instances[i].xp for i in s.roster.party if i<160],**self.state(),**{n:self.g(n)for n in ('hero_hp_q4','ability_cd','heal_cd','game_shop_selection','game_shop_confirm','summoned','quickparty_open','save_requested')}}
        self.events.append(row);return row
    def settle_dialog(self):
        for _ in range(12):
            if self.g('game_state')!=2:return
            self.tap('A')
        self.check('dialogue has a bounded completion',self.g('game_state')!=2)
    def prepared(self,source,fresh=True,full=False,gold=None):
        t,room,x,y,face,stage=SOURCE[source]
        self.play(self.fixture_path(FIXTURE[t]if fresh else CLAIMED[t]))
        s=self.save_state();s.campaign.room=room;s.campaign.spawn=0
        if fresh:changeq(s,QUEST[t],2)
        s.economy.later_claims&=~(1<<t)
        if gold is not None:s.economy.gold=gold;s.economy.earned=s.economy.spent+gold
        self.patch_save(s,'synthetic regional report context and optional READY rewind / wallet boundary')
        self.location(room,x,y);self.put('face',face)
        if source in (0,2):self.put('north_game_machine_stage'if source==0 else'south_game_machine_stage',stage,w=1)
        self.put('transition_lock',1000)
        for en in range(6):self.put('enemies',0,offset=en*20+8,reason='synthetic cleared safe report scene')
        self.step(5,phase='prepared')
        self.put('hero_hp_q4',48);self.put('hp',3);self.put('ability_cd',77);self.put('heal_cd',43)
        self.mark('prepared-source')
    def claim(self,t,*,fresh,exit_key='A',busy_key='A',resume=1):
        before=self.save_state();before_hp=self.g('hero_hp_q4');before_cd=self.g('ability_cd');before_heal=self.g('heal_cd');start=len(self.frames)
        self.step(1,'A')
        self.check('actual A enters treasure transaction',self.g('game_state')==12,self.state())
        if self.g('game_state')!=12:return False
        frozen={n:self.g(n)for n in ('room','px','py','face','hero_hp_q4','ability_cd','heal_cd','summoned')}
        pending_save=bytes(self.save_state());pending=0;stable=True
        # Hold one chord continuously through the last busy frame: it must not
        # leak into the next receipt or field scene without a fresh press.
        while self.g('game_state')==12 and pending<600:
            self.step(1,busy_key);pending+=1
            if self.g('game_state')==12:stable &= bytes(self.save_state())==pending_save
            stable &= all(self.g(n)==v for n,v in frozen.items())
        self.check('busy transaction preserves live state and player timers until commit',stable,{'pending_frames':pending,'frozen':frozen})
        self.check('transaction reaches explicit receipt',self.g('game_state')==13,self.state())
        if self.g('game_state')!=13:return False
        after=self.save_state();gain=min(GOLD[t],9999-before.economy.gold)
        xp=sum(after.roster.instances[i].xp-before.roster.instances[i].xp for i in before.roster.party if i<160)
        self.check('one treasure and exact clipped gold committed',after.economy.later_claims==before.economy.later_claims|(1<<t) and after.economy.gold-before.economy.gold==gain,{'gain':gain,'before':before.economy.gold,'after':after.economy.gold,'bits':after.economy.later_claims})
        self.check('treasure does not consume gear capacity or change party selection',bytes(after.equipment)==bytes(before.equipment) and bytes(after.roster.party)==bytes(before.roster.party) and after.roster.selected_party==before.roster.selected_party)
        self.check('fresh report is claimed exactly once',qstate(after,QUEST[t])==3)
        self.check('treasure commit preserves current HP and cooldown',self.g('hero_hp_q4')==before_hp and self.g('ability_cd')==before_cd-(resume==1) and self.g('heal_cd')==before_heal-(resume==1),{'before':[before_hp,before_cd,before_heal],'after':[self.g('hero_hp_q4'),self.g('ability_cd'),self.g('heal_cd')]})
        self.check('receipt uses actual gold and EXP',self.g('game_shop_reward_gold')==gain and self.g('game_shop_reward_xp')==xp,{'gold':gain,'xp':xp})
        if not fresh:self.check('recovery does not replay any companion EXP, bond or event',bytes(after.roster)==bytes(before.roster) and bytes(after.quests)==bytes(before.quests))
        self.step(20,busy_key);self.check('held busy input does not dismiss or duplicate receipt',self.g('game_state')==13 and bytes(self.save_state())==bytes(after))
        self.step(3);self.tap('SELECT');self.check('Select is inert on saved receipt',self.g('game_state')==13 and bytes(self.save_state())==bytes(after))
        self.shot(self.case+'-receipt');self.mark('saved-receipt')
        self.tap(exit_key)
        self.check(exit_key+' leaves receipt with expected story behavior',self.g('game_state')==(2 if fresh and exit_key=='A' and resume==1 else resume),self.state())
        if fresh and exit_key=='A' and resume==1:self.shot(self.case+'-story');self.settle_dialog()
        self.check('receipt dismissal cannot duplicate reward',self.save_state().economy.gold==after.economy.gold and self.save_state().economy.later_claims==after.economy.later_claims)
        window=self.frames[start:]
        self.native_windows.append({'case':self.case,'kind':'actual-controller-report-transaction-receipt-dismissal','frames':len(window),'pending_frames':pending,'max_native_cycles':max(f['cycles']for f in window),'update_misses':sum(f['delta']!=1 for f in window),'flip_misses':sum(not f['flip']for f in window),'cycle_overruns':sum(f['cycles']>=LIMIT for f in window)})
        return True
    def repeat_reload(self,t):
        self.step(3);before=self.save_state();self.tap('A');self.settle_dialog();self.step(20)
        self.check('repeated report cannot duplicate treasure gold EXP or bond',bytes(self.save_state().economy)==bytes(before.economy) and bytes(self.save_state().roster)==bytes(before.roster))
        self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1000)
        self.shot(self.case+'-field-restored')
        saved=self.out/(self.case+'-committed.sav');self.e.save(saved);expected=self.save_state();self.play(saved);after=self.save_state()
        self.check('independent cold Continue preserves treasure economy and companion data',bytes(after.economy)==bytes(expected.economy) and bytes(after.roster)==bytes(expected.roster) and bytes(after.quests)==bytes(expected.quests))
        self.check('cold Continue does not invent a claim receipt',self.g('game_state')==1)
    def sources(self):
        for source in range(6):
            for fresh in (True,False):
                self.case=f'prepared-source-{source}-'+('fresh'if fresh else'recovery')
                self.prepared(source,fresh)
                if self.claim(SOURCE[source][0],fresh=fresh,exit_key=('A','B','START','A+B','A+START','B+START')[source],busy_key=('A','B+START+SELECT+RIGHT','A+B+START+SELECT+LEFT')[source%3]):self.repeat_reload(SOURCE[source][0])
                self.report()
    def wallet(self):
        for gold in (9990,9999):
            self.case='prepared-wallet-'+str(gold);self.prepared(5,True,gold=gold)
            self.claim(3,fresh=True,exit_key='START');self.repeat_reload(3)
    def fault(self):
        self.case='prepared-native-save-fault';self.prepared(5,True);before=self.save_state();self.step(1,'A')
        self.check('fault probe begins a real later transaction',self.g('game_state')==12)
        reached=self.wait(lambda:self.g('writer_phase')==13 and self.g('game_state')==12,600)
        self.check('transaction reaches native inactive-bank verification',reached)
        if not reached:return
        destination=self.g('writer_destination');position=self.g('writer_position');address=0x0e000000+destination+min(position+600,6000);value=self.e.read(address,1)^1
        self.writes.append({'case':self.case,'frame':self.e.frame,'address':hex(address),'width':1,'value':value,'reason':'deliberately corrupt inactive SRAM before native readback; failure-path integration only'})
        self.e.write(address,value,1);self.wait(lambda:self.g('game_state')!=12,600)
        self.check('failed commit never grants treasure gold EXP bond or receipt',self.g('game_state')==1 and bytes(self.save_state())==bytes(before))
        self.check('native save failure is visible',self.g('save_failed')==1 and self.g('save_failure_notice')==1)
        self.shot(self.case+'-visible');failed=self.out/'prepared-failed-treasure.sav';self.e.save(failed)
        self.step(3)
        # A is an ordinary retry at the same report source. No RAM repair or
        # writer-reset function is invoked; the next transaction owns recovery.
        if self.claim(3,fresh=True,exit_key='A'):
            self.check('successful ordinary retry clears save failure',not self.g('save_failed'));self.repeat_reload(3)
        self.play(failed);self.check('failed write cold-loads the prior claim-free wallet',bytes(self.save_state().economy)==bytes(before.economy))
    def items(self):
        self.case='prepared-items-unknown';self.play(self.fixture_path(CLAIMED[3]));self.tap('START');self.tap('A');self.check('controller opens Items',self.g('journal_tab')==15)
        for _ in range(6):self.tap('DOWN')
        self.shot(self.case)
        before=bytes(self.save_state());self.tap('A');self.tap('SELECT');self.check('unknown treasure A and Select cannot claim or consume',bytes(self.save_state())==before and self.g('game_state')==3)
        self.tap('START')
    def earned_shop(self):
        self.case='earned-G7-village-recovery';self.strict_controller=True
        try:
            self.play(self.fixture_path('covenants-homecoming-after-continue'));self.check('earned G7 homecoming resumes at village',self.g('room')==0,self.state())
            self.check('unmodified revision10 load grants no later rewards',self.save_state().economy.later_claims==0)
            self.check('actual walking reaches village merchant',self.navigate(120,100)and self.navigate(56,100))
            self.tap('A');self.check('actual A opens recovery shop',self.g('game_state')==11)
            self.check('later recovery is initially selected when original claims are owned',self.g('game_shop_selection')==3)
            self.tap('A');self.shot('earned-shop-confirm');before=bytes(self.save_state());self.tap('B')
            self.check('B cancels recovery confirmation without mutation',self.g('game_state')==11 and not self.g('game_shop_confirm')and bytes(self.save_state())==before)
            self.tap('SELECT');self.check('Select does not alter recovery selection',self.g('game_shop_selection')==3)
            for t in range(4):
                self.case=f'earned-G7-village-treasure-{t}';self.tap('A')
                if not self.claim(t,fresh=False,exit_key=('A','B','START','A')[t],resume=11):break
            s=self.save_state();self.check('all four earned recoveries are unique and row disappears',s.economy.later_claims==15 and self.g('game_shop_selection')==0)
            self.tap('START');self.tap('START');self.tap('A')
            for _ in range(6):self.tap('DOWN')
            for t in range(4):
                self.shot('earned-items-'+str(t));before=bytes(self.save_state());self.tap('A');self.tap('SELECT');self.check('owned permanent treasure is inspection only '+str(t),bytes(self.save_state())==before and self.g('game_state')==3)
                if t<3:self.tap('DOWN')
            self.tap('B');self.check('B returns Items to hub',self.g('game_state')==3 and self.g('journal_tab')==13);self.tap('START')
            self.step(20,'L');self.check('held L picker remains available',self.g('quickparty_open')==1);self.step(3);self.check('release L restores field',not self.g('quickparty_open'))
            self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1000)
            saved=self.out/'earned-G7-recovery-complete.sav';self.e.save(saved);expected=self.save_state();(self.out/'earned-before-reload.bin').write_bytes(bytes(expected));self.play(saved);(self.out/'earned-after-reload.bin').write_bytes(bytes(self.save_state()))
            self.check('earned recovery cold reload preserves economy roster and gear',bytes(self.save_state().economy)==bytes(expected.economy)and bytes(self.save_state().roster)==bytes(expected.roster)and bytes(self.save_state().equipment)==bytes(expected.equipment),{'differences':{n:[i for i,(x,y)in enumerate(zip(bytes(getattr(expected,n)),bytes(getattr(self.save_state(),n))))if x!=y]for n in ('economy','roster','equipment')}})
        finally:self.strict_controller=False
    def full(self):
        self.case='prepared-full160-gear48';self.play(True);s=self.save_state();template=Instance.from_buffer_copy(bytes(s.roster.instances[0]));template.flags=1
        for i in range(160):
            if not s.roster.instances[i].form_id:s.roster.instances[i]=template;s.roster.instances[i].instance_id=s.roster.next_instance_id;s.roster.next_instance_id+=1
        s.campaign.room=0;s.campaign.spawn=0;s.economy.boss_claims=s.economy.relics=7;s.economy.gold=s.economy.earned=320
        self.patch_save(s,'synthetic full160 roster built from authenticated full48-equipment G7 predecessor; old relics preclaimed to isolate later recovery')
        self.location(0,56,114);self.put('face',1);self.step(5,phase='prepared');self.put('hero_hp_q4',48);self.put('hp',3);self.put('ability_cd',77);self.put('heal_cd',43)
        before=self.save_state();self.check('prepared fixture actually fills all160 companions and48 gear slots',sum(bool(c.flags&1)for c in before.roster.instances)==160 and sum(bool(g.item_id)for g in before.equipment.bag)==48)
        self.tap('A')
        for t in range(4):
            self.case=f'prepared-full160-gear48-treasure-{t}';self.tap('A')
            if not self.claim(t,fresh=False,resume=11):break
        after=self.save_state();self.check('all four full-capacity recoveries preserve every roster gear and quest byte',after.economy.later_claims==15 and bytes(before.roster)==bytes(after.roster) and bytes(before.equipment)==bytes(after.equipment) and bytes(before.quests)==bytes(after.quests))
        self.tap('START');saved=self.out/'prepared-full-capacity-complete.sav';self.e.save(saved);self.play(saved);self.check('full-capacity claimed state cold reloads exactly',bytes(self.save_state().roster)==bytes(after.roster) and bytes(self.save_state().equipment)==bytes(after.equipment)and bytes(self.save_state().economy)==bytes(after.economy))
    def report(self):
        d=super().report();d.update(suite='treasure-player-flow',scope='Synthetic regional report routing and boundary probes separately labeled from unmodified G7 controller-only village recovery',events=getattr(self,'events',[]),native_windows=getattr(self,'native_windows',[]),authenticated_inputs=getattr(self,'authenticated_inputs',[]),pending_return_WAV='untouched; no audio approval claimed')
        (self.out/'report.json').write_text(json.dumps(d,indent=2)+'\n');return d

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','output','earned-root'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True)
    p.add_argument('--cases',default='sources,wallet,items,earned_shop,full,fault')
    a=p.parse_args();r=TreasureRun(a)
    try:
        for name in a.cases.split(','):r.section(name,getattr(r,name))
    finally:d=r.finish()
    return int(bool(d['failures'])or not d['exact_files_unchanged']or not d['performance']['strict_measured_pacing_pass'])
if __name__=='__main__':raise SystemExit(main())
