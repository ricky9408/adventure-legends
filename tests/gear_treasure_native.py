#!/usr/bin/env python3
"""Integrated passive Gear checks on the exact native candidate.

All passive combinations here are explicitly prepared developer fixtures based
on authenticated bundled SRAM with already-CLAIMED source quests. They do not
claim acquisition. Production save validation and economy/gear conversion are
used before native controller previews, commits, SRAM reloads, and walking.
"""
from __future__ import annotations
import argparse, ctypes as C, gzip, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from gear_preview_native import GearNative, Stats, Comparison, Save, Economy, State, TEAL, BACKGROUND, sha

class TreasureGear(GearNative):
    def __init__(self,args):
        super().__init__(args)
        self.passive_rows=[];self.movement_rows=[];self.context_rows=[]
        self.hashes['integrated_suite_sha256']=sha(__file__)
        self.frozen_runtime=json.loads((self.rom.parent/'source-hashes.json').read_text())
        assert all(sha(ROOT/name)==value for name,value in self.frozen_runtime.items()),'Oracle source must match the frozen candidate'
        self.hashes['candidate_source_manifest_sha256']=sha(self.rom.parent/'source-hashes.json')
        sources=['tests/gear_treasure_oracle.c','src/gear_runtime.c','src/economy.c','src/save4.c','src/save5.c','src/creatures.c','src/creature_data.c','src/equipment.c','src/equipment_data.c','src/southern_quests.c','src/magma_quests.c']
        so=self.out/'production-passive-oracle.so'
        subprocess.run(['cc','-std=c99','-O2','-fPIC','-shared','-fvisibility=hidden','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Isrc',*sources,'-o',str(so)],cwd=ROOT,check=True)
        self.production=C.CDLL(str(so));self.production.gear_treasure_valid.argtypes=[C.POINTER(Save)];self.production.gear_treasure_valid.restype=C.c_int
        self.production.gear_treasure_expected.argtypes=[C.POINTER(Save),C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.POINTER(Comparison)];self.production.gear_treasure_expected.restype=C.c_uint
        for relative in sources+[str(Path(__file__).relative_to(ROOT))]:
            dest=self.out/'test-source'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,dest);self.hashes['test_sources'][relative]=sha(dest)
        self.hashes['production_passive_oracle_sha256']=sha(so)
        self.gp_names=re.findall(r' GP_([A-Z_]+),', (ROOT/'src/gear_preview_text.h').read_text())
    def expected(self,slot=None,candidate=None):
        s=self.save_state();out=Comparison()
        result=self.production.gear_treasure_expected(C.byref(s),self.g('max_hp'),self.g('hero_hp_q4'),self.g('gear_menu_slot')if slot is None else slot,self.g('gear_menu_candidate')if candidate is None else candidate,C.byref(out))
        assert result==0,result
        return out
    def validate(self,label):
        s=self.save_state();valid=self.production.gear_treasure_valid(C.byref(s))
        self.check(label+': actual full Save5 validation',valid==1,{'later':s.economy.later_claims,'old':s.economy.relics,'earned':s.economy.earned,'source_quests':{str(q):(s.quests.states[q>>2]>>((q&3)*2))&3 for q in (21,24,32,40)}})
        assert valid==1
    def prepared(self,later,old,loadout=(1,0,0,0,0),base=8):
        self.play(True);self.open_gear();self.phase_override='fixture_preparation'
        s=self.save_state()
        for bit,q in enumerate((21,24,32,40)):
            if later&(1<<bit):assert (s.quests.states[q>>2]>>((q&3)*2))&3==3,('Claimed provenance missing',q)
        s.economy=Economy();s.economy.earned=2000;s.economy.spent=120;s.economy.gold=1880;s.economy.upgrade=1;s.economy.relics=s.economy.boss_claims=old;s.economy.later_claims=later
        s.campaign.relic=1 if base==8 else 0
        for slot,item in enumerate(loadout):s.equipment.equipped[slot]=next(i for i,r in enumerate(s.equipment.bag)if r.item_id==item)if item else 255
        self.write_blob('adventure_save',bytes(s),reason='Prepared valid passive/loadout fixture, source CLAIMED quests retained')
        self.put('max_hp',base);self.put('relic_found',int(base==8));self.put('hero_hp_q4',83);self.put('hp',6)
        self.put('ability_cd',137);self.put('ability_max',180);self.put('heal_cd',213)
        self.validate('Prepared passive combination')
        self.choose(loadout[0]);self.commit('Apply prepared passive '+str(later)+'/'+str(old))
        self.passive_rows.append({'later':later,'old':old,'loadout':loadout,'base':base,'stats':dict((n,int(getattr(self.expected().after,n)))for n,_ in Stats._fields_)})
    def context(self,name):
        idx=self.gp_names.index(name);address=self.sym['gear_preview_texts']+idx*16
        width=self.e.read(address,2);height=self.e.read(address+2,1);x=(240-width)//2;y=110
        runs=self.e.read(address+4+(x&1)*4);count=self.e.read(address+12+(x&1)*2,2)
        expected=bytearray([BACKGROUND]*(240*14))
        for i in range(count):
            offset=self.e.read(runs+i*4,2);length=self.e.read(runs+i*4+2,1);mask=self.e.read(runs+i*4+3,1)
            for step in range(length):
                p=((x&~1)+2*(offset+step))
                for bit in range(2):
                    if mask&(1<<bit):expected[p+bit]=TEAL
        page=0x0600a000 if self.e.read(0x04000000,2)&16 else 0x06000000
        actual=self.e.bytes(page+y*240,240*14)
        diffs=[i for i,(a,b)in enumerate(zip(expected,actual))if 12<=i%240<228 and a!=b]
        self.context_rows.append({'label':name,'frame':self.e.frame,'mismatches':len(diffs)})
        self.check('Actual context pixels '+name,not diffs,{'first':diffs[:8]})
    def combinations(self):
        for later,old in ((0,0),(1,0),(2,0),(4,0),(8,0),(5,2),(10,1),(15,7)):
            self.prepared(later,old)
            before=self.snapshot();self.choose(89);self.shot(f'passives-{later:02d}-{old}-preview89');self.preserved('Passive preview preserves full state',before)
            self.commit('Passive combination gear commit')
            self.choose(0,4);self.shot(f'passives-{later:02d}-{old}-remove89');self.commit('Passive combination gear removal')
            self.validate('Committed passive combination')
            path=self.out/f'PREPARED-passives-{later:02d}-{old}.sav';self.e.save(path);saved=bytes(self.save_state().economy);self.play(path)
            self.check('Cold SRAM keeps all passive receipt bytes',bytes(self.save_state().economy)==saved)
    def boundary_cases(self):
        self.prepared(15,7,(14,34,56,65,82));self.check('Pearl makes actual maximum12 hearts reachable',self.expected().after.max_hp_q4==192)
        self.phase_override='fixture_preparation';self.put('hero_hp_q4',192);self.put('hp',12)
        self.choose(14);self.phase_override='boundary';before=self.snapshot();self.shot('pearl-full12-noop-preview');self.preserved('Full Pearl preview preserves192HP and timers',before)
        self.commit('Full Pearl no-op equip');self.check('Full Pearl no-op preserves192 HP',self.g('hero_hp_q4')==192)
        self.choose(0,1);self.shot('pearl-full12-armor-removal');self.commit('Full Pearl remove armor');self.check('Pearl removal clamps only to effective capacity',self.g('hero_hp_q4')==self.expected().after.max_hp_q4)
        self.prepared(2,0,(2,34,49,67,82));self.check('Actual defense raw7 plus Aegis2 caps at8',self.expected().after.defense_q4==8)
        self.choose(0,3);cmp=self.expected();self.check('Aegis cap preserves8 DEF when one raw point removed',cmp.before.defense_q4==cmp.after.defense_q4==8)
        self.shot('aegis-defense-cap-belt-removal');self.commit('Aegis capped belt removal')
        self.prepared(4,2,(1,0,50,69,88));self.check('Bell plus Feather plus gear gives20 reduction',self.expected().after.power_cooldown==55)
        self.choose(52);cmp=self.expected();self.check('Bell does not hide capped recovery or speed cost',cmp.before.power_cooldown==cmp.after.power_cooldown==55 and cmp.after.speed_q8<cmp.before.speed_q8)
        self.shot('bell-feather-gear-cap-speed-loss');self.context('RECOVERY_CAP')
        before=self.snapshot();self.commit('Bell capped swap');self.check('Bell equip does not reset current cooldown',self.g('ability_cd')==int.from_bytes(bytes.fromhex(before['ability_cd']),'little'))
    def cache(self):
        self.prepared(0,0,(1,0,50,69,88));self.choose(52);self.shot('cache-original')
        original=self.e.bytes(self.sym['preview_cache'],self.sizes['preview_cache'])
        for later in (1,3,7,15):
            s=self.save_state();s.economy.later_claims=later;self.phase_override='fixture_preparation';self.write_blob('adventure_save',bytes(s),reason='Prepared passive cache-key mutation with valid claimed quest provenance');self.validate('Cache mutation')
            self.put('gear_menu_revision',self.g('gear_menu_revision')+1,reason='Prepared renderer invalidation; keep production raw equipment preview cache intact')
            self.phase_override='boundary';before=self.snapshot();self.shot('cache-later-'+str(later));self.preserved('Fresh passive projection preserves state',before)
            current=self.e.bytes(self.sym['preview_cache'],self.sizes['preview_cache'])
            self.check('Raw cache reused for non-HP passive flags'if later!=15 else'Pearl base HP invalidates raw cache',current==original if later!=15 else current!=original)
        self.commit('Commit after prepared raw-cache mutations');self.validate('Cache mutation commit')
    def compass(self):
        for later in (0,1):
            self.prepared(later,0,(21,0,49,0,85));stats=self.expected().after
            self.check('Fastest authored Compass speed stays below synthetic352 cap',stats.speed_q8==(350 if later else 334))
            self.shot('compass-fastest-'+str(later));self.phase_override='return';self.step(1,'START');self.step(3)
            for key,dx,dy in [('RIGHT',1,0),('LEFT',-1,0),('DOWN',0,1),('UP',0,-1),('RIGHT+DOWN',1,1),('LEFT+DOWN',-1,1),('RIGHT+UP',1,-1),('LEFT+UP',-1,-1)]:
                self.phase_override='fixture_preparation';self.location(0,120,112);self.put('advanced_guard_charges',0);self.put('transition_lock',99)
                self.step(3);before=(self.g('px_q8'),self.g('py_q8'));self.phase_override='boundary';self.step(1,key);after=(self.g('px_q8'),self.g('py_q8'));speed=stats.diagonal_q8 if dx and dy else stats.speed_q8
                actual=(after[0]-before[0],after[1]-before[1]);expected=(dx*speed,dy*speed)
                self.movement_rows.append({'compass':later,'keys':key,'expected_q8':expected,'actual_q8':actual,'stats_speed':stats.speed_q8,'stats_diagonal':stats.diagonal_q8})
                self.check('Compass actual controller movement '+str(later)+' '+key,actual==expected,{'actual':actual,'expected':expected})
    def ring_choice(self):
        # All choices use controller selection and the actual live A commit.
        # Prior full snapshots also retain HP, attack and current power timers.
        for label, boots, belt, capped in [('uncapped',0,0,False),('near-cap',55,0,False),('capped',50,69,True)]:
            self.prepared(15,7,(1,0,boots,belt,88))
            for candidate in (89,88):
                before=self.snapshot();self.choose(candidate);cmp=self.expected()
                delta=int(cmp.after.power_cooldown)-int(cmp.before.power_cooldown)
                self.check('Porchlight '+label+' exact future recovery tradeoff '+str(candidate),delta==(0 if capped else -1 if candidate==89 else 1),{'before':cmp.before.power_cooldown,'after':cmp.after.power_cooldown})
                speed_delta=int(cmp.after.speed_q8)-int(cmp.before.speed_q8)
                self.check('Porchlight '+label+' retains two Q8 walking cost '+str(candidate),speed_delta==(-2 if candidate==89 else 2))
                self.check('Porchlight choice leaves attack and HP capacity equal',cmp.before.attack_q4==cmp.after.attack_q4 and cmp.before.max_hp_q4==cmp.after.max_hp_q4)
                self.shot('porchlight-'+label+'-to-'+str(candidate))
                if capped:self.context('RECOVERY_CAP')
                self.preserved('Porchlight '+label+' preview preserves complete state',before)
                self.commit('Porchlight '+label+' equip '+str(candidate))
    def finish(self):
        self.check('Candidate runtime source still matches the frozen candidate manifest',all(sha(ROOT/name)==value for name,value in self.frozen_runtime.items()))
        return super().finish()
    def report(self):
        result=super().report()
        if result and hasattr(self,'passive_rows'):
            result.update(suite='gear-treasure-native',scope=__doc__,passive_combinations=self.passive_rows,movement=self.movement_rows,context_pixels=self.context_rows)
            (self.out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
        return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);p.add_argument('--cases',default='combinations,boundary_cases,cache,compass,ring_choice');a=p.parse_args()
    run=TreasureGear(a)
    for name in a.cases.split(','):run.section(name,getattr(run,name))
    result=run.finish();return int(bool(result['failures'])or bool(result['performance']['pacing_exceptions'])or not result['exact_files_unchanged'])
if __name__=='__main__':raise SystemExit(main())
