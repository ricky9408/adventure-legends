#!/usr/bin/env python3
"""Exact-ROM controller-only combat, equipment and frame-cadence regressions.

Imports hash-pinned controller-earned SRAM into the selected target ROM.
Never imports a source journey's machine state. Any branches restore only this
run's exact target-ROM machine-state/SRAM pair; all game symbols are read-only
observations. --expected-rom-sha can additionally pin a release candidate.
"""
from __future__ import annotations
import argparse, ctypes as C, hashlib, json, struct
from pathlib import Path
from region_journey import RegionJourney, Emulator, ROOT, PLAY, PAUSE, DEAD, CONFIRM, digest

SOURCE_SNAPSHOT='11-idempotent-revisit'
SOURCE_SRAM_SHA='af04d795c9a4781f35cdc187559fd4929320ddb34f9f4a5e04dc4ed4e748302b'
PHASES=['Wood','Fire','Earth','Metal','Water']

class CombatReview(RegionJourney):
    def __init__(self,rom,symbols,output,source_report,expected_rom_sha=None):
        self.target_sha=digest(rom);self.expected_rom_sha=expected_rom_sha.lower() if expected_rom_sha else None
        if self.expected_rom_sha:
            assert self.target_sha==self.expected_rom_sha,'Target ROM differs from --expected-rom-sha'
        self.results=[];self.coverage=[];self.provenance={};self.frame_windows=[]
        super().__init__(rom,symbols,output,ROOT/'tests/fixtures/v4/finished-ending.sav')
        source_report=Path(source_report).resolve()
        report=json.loads(source_report.read_text());source=report['snapshots'][SOURCE_SNAPSHOT]
        source_sram=Path(source['sram_path'])
        if not source_sram.is_absolute():source_sram=source_report.parent/source_sram
        # Packaged reports may retain the producer's old absolute path. A
        # sibling with the same exact filename is accepted only after SHA check.
        if not source_sram.is_file():source_sram=source_report.parent/Path(source['sram_path']).name
        assert report['controller_only'] and not report['failures'] and all(c['passed'] for c in report['checks'])
        assert source['sram_sha256']==SOURCE_SRAM_SHA and digest(source_sram)==SOURCE_SRAM_SHA
        assert source['quests']==[3]*11
        self.provenance={'source_report':str(source_report),'source_report_sha256':digest(source_report),
            'source_rom_sha256':report['rom_sha256'],'source_snapshot':SOURCE_SNAPSHOT,
            'sram_path':str(source_sram),'sram_sha256':SOURCE_SRAM_SHA,
            'source_machine_state_loaded':False,'scope':'Controller-earned collection/quests/gear imported forward as SRAM only'}
        self.e.load_save(source_sram);self.e.reset()
    def report(self):
        if not hasattr(self,'out'):return
        (self.out/'region-combat.json').write_text(json.dumps({'suite':'region-native-combat',
            'controller_only':True,'game_ram_writes':0,'provenance':self.provenance,
            'test_source_sha256':digest(__file__),'expected_rom_sha256':self.expected_rom_sha,'branch_policy':'Only same-candidate machine states paired with their own hash-checked SRAM are restored',
            **self.candidate,'checks':self.checks,'cases':self.results,'coverage':self.coverage,
            'failures':self.failures,'snapshots':self.snapshots,'frame_windows':self.frame_windows,
            'inputs':self.inputs,'timing_caveat':'Timer observes update/render before VBlank wait and OAM commit; strict cadence also verifies one update and page flip per hardware frame.'},indent=2)+'\n')
    def snapshot(self,name):
        result=super().snapshot(name);self.snapshots[name]['rom_sha256']=self.target_sha;self.report();return result
    def restore(self,name):
        record=self.snapshots[name]
        assert record['rom_sha256']==self.target_sha and digest(self.rom)==self.target_sha
        assert digest(record['state_path'])==record['state_sha256']
        assert digest(record['sram_path'])==record['sram_sha256']
        super().restore(name)
    def enemies(self):
        return [dict(zip(('x','y','hp','flash','kind'),struct.unpack('<5i',self.e.bytes(self.sym['enemies']+i*20,20))),
                     hp_q4=self.e.read(self.sym['enemy_hp_q4']+i*4),phase=self.e.read(self.sym['enemy_phases']+i,1)) for i in range(6)]
    def arrows(self):
        return [{'x':self.e.read(self.sym['player_arrows']+i*20)//256,'y':self.e.read(self.sym['player_arrows']+i*20+4)//256,
                 'active':self.e.read(self.sym['player_arrows']+i*20+12,1)} for i in range(2)]
    def action(self):
        b=self.e.bytes(self.sym['weapon_action'],20)
        return {'class':b[2],'phase':b[3],'direction':b[4],'age':b[6],'charge':b[7],'suppress':b[11]}
    def hp_q4(self):return self.get('hero_hp_q4')
    def stats(self):
        b=self.e.bytes(self.sym['gear_stats'],14)
        return {'max_hp':int.from_bytes(b[:2],'little'),'attack':b[6],'defense':b[7],'weapon':b[12]}
    def command(self):c=self.selected();return c.equipped[c.selected_command]
    def owned_select(self,form):
        if not any(i<160 and self.roster().instances[i].form_id==form for i in self.roster().party):self.assign(3,form)
        self.select_form(form)
    def equip_item(self,slot,item):
        self.open_tab(4)
        for _ in range(5):
            if self.get('gear_menu_slot')==slot:break
            self.tap('DOWN',2,3)
        for _ in range(50):
            ref=self.get('gear_menu_candidate');chosen=self.state().equipment.bag[ref].item_id if ref<48 else (1 if slot==0 else 0)
            if chosen==item:break
            self.tap('RIGHT',2,3)
        self.check(chosen==item,f'owned gear item{item} is selectable in slot{slot}')
        before=self.hp_q4();self.tap('R',2,25);self.settle();self.close_menu()
        ref=self.state().equipment.equipped[slot];actual=self.state().equipment.bag[ref].item_id if ref<48 else 0
        self.check(actual==item,f'real equipment menu equips item{item}')
        self.check(self.hp_q4()<=before,'equipping never increases current q4 health')
    def set_command(self,command):
        if self.command()==command:return
        self.open_tab(3)
        for _ in range(3):
            if self.command()==command:break
            self.tap('R',2,25);self.settle()
        self.check(self.command()==command,f'real growth menu selects learned command{command}');self.close_menu()
    def boot(self):
        self.step(150);self.tap('START',2,35);self.settle()
        self.check(self.get('room')==16,'forward-imported SRAM resumes in town on the selected target ROM')
        self.check(all(self.quest(q)==3 for q in range(11)),'eleven earned quests survive forward SRAM load')
        self.check({c.form_id for c in self.roster().instances if c.flags&1}=={1,4,7,10,14,16},'actual six owned companions retain identity')
        self.check(sum(bool(r.item_id) for r in self.state().equipment.bag)==13,'all thirteen earned gear items survive forward SRAM load')
        self.snapshot('candidate-town-source')
    def prepare_basin(self,form,command=None,armor=33):
        self.restore('candidate-town-source');self.owned_select(form)
        if command:self.set_command(command)
        self.equip_item(1,armor);self.enter_basin();self.ready()
        self.check([e['phase'] for e in self.enemies()[:5]]==[0,1,3,4,2],'basin enemy phases are Wood Fire Metal Water Earth')
    def phase_case(self,label,form,command,target,goal,direction,base,expected):
        self.prepare_basin(form,command);self.goto(*goal);self.face(direction);self.ready()
        self.snapshot('phase-'+label+'-before')
        before=self.enemies();start=self.e.frame;self.step(1,'R');trace=[]
        for i in range(100):
            now=self.enemies();trace.append({'frame':self.e.frame,'hero':[self.get('px'),self.get('py')],
                                          'target':now[target],'ability_cd':self.get('ability_cd'),'command':self.command()})
            if now[target]['hp_q4']<before[target]['hp_q4']:break
            self.step(1)
        after=self.enemies();damage=before[target]['hp_q4']-after[target]['hp_q4']
        result={'case':label,'form':form,'command':command,'defender_index':target,'defender_phase':PHASES[before[target]['phase']],
                'base_q4':base,'expected_q4':expected,'actual_q4':damage,'start_frame':start,'before':before[target],'after':after[target],
                'trace':trace,'passed':damage==expected}
        self.results.append(result);self.report()
        self.check(damage==expected,f'{label}: actual native q4 damage equals{expected}')
        self.coverage.append(label);self.snapshot('phase-'+label+'-after')
    def run_phases(self):
        self.phase_case('Fire-controls-Metal',1,1,2,(400,279),1,32,40)
        self.phase_case('Water-controls-Fire',14,9,1,(337,263),2,24,30)
        self.phase_case('Metal-controls-Wood',16,11,0,(213,264),2,32,40)
        self.phase_case('Earth-controls-Water',10,4,3,(177,123),2,16,20)
    def shots(self):
        return [dict(zip(('x','y','dx','dy','life','owner'),struct.unpack('<6i',self.e.bytes(self.sym['shots']+i*24,24))),
                     phase=self.e.read(self.sym['shot_phases']+i,1)) for i in range(12)]
    def wood_reflection(self):
        self.restore('candidate-town-source');self.owned_select(7);self.open_tab(3)
        self.tap('SELECT',2,3);self.check(self.get('game_state')==CONFIRM,'earned Fuuri trial permits explicit evolution confirmation')
        self.tap('A',2,3);self.settle();self.check(self.selected().form_id==8,'Fuuri evolves through real menu confirmation')
        self.close_menu();self.set_command(7);self.equip_item(1,33);self.enter_basin();self.ready();self.goto(269,128);self.face(1)
        self.snapshot('phase-Wood-controls-Earth-before');before=self.enemies()[4]['hp_q4'];incoming=[]
        for _ in range(250):
            x,y=self.get('px'),self.get('py')
            incoming=[dict(index=i,**s) for i,s in enumerate(self.shots()) if s['life'] and s['owner'] and s['phase']==2
                      and -8<=y-s['y']<=75 and abs(x-s['x'])<=30]
            if incoming and not self.get('ability_cd'):break
            self.step(1)
        self.check(bool(incoming),'actual Earth ranger projectile enters Fuuri reflection cone')
        self.step(1,'R');reflected=[dict(index=i,**s) for i,s in enumerate(self.shots())
            if i in {shot['index'] for shot in incoming} and not s['owner'] and s['phase']==0]
        # A reflected shot beside its shooter can hit and expire in this very
        # update. Its original live hostile identity and new phase are evidence
        # even when life is now zero; target q4 loss is checked independently.
        self.check(bool(reflected),'actual reflected projectile changes owner and becomes Wood phase')
        trace=[]
        for _ in range(100):
            target=self.enemies()[4];trace.append({'frame':self.e.frame,'target':target,'shots':self.shots()})
            if target['hp_q4']<before:break
            self.step(1)
        damage=before-self.enemies()[4]['hp_q4']
        self.results.append({'case':'Wood-controls-Earth','form':8,'command':7,'base_q4':32,'expected_q4':40,
                             'actual_q4':damage,'incoming':incoming,'reflected':reflected,'trace':trace,'passed':damage==40})
        self.check(damage==40,'Wood reflected shot deals40Q4 to Earth ranger');self.coverage.append('Wood-controls-Earth')
        self.snapshot('phase-Wood-controls-Earth-after')
    def health_menu_case(self):
        self.restore('candidate-town-source');self.equip_item(1,33)
        self.check(self.stats()['max_hp']==104 and self.hp_q4()==96,'half-heart armor adds capacity without healing on real menu')
        self.enter_basin();self.goto(184,264)
        before=self.hp_q4();start=self.e.frame
        for _ in range(150):
            self.step(1)
            if self.hp_q4()<before:break
        damaged=self.hp_q4();self.check(before-damaged==14,'ordinary enemy hit subtracts14Q4 with defense2')
        self.check(damaged%16!=0,'health remains fractional rather than rounded to hearts')
        # Pause halts the enemy and keeps the exact fractional value while all
        # candidate previews and commits happen through the same native menu.
        self.open_tab(4)
        for _ in range(5):
            if self.get('gear_menu_slot')==1:break
            self.tap('DOWN',2,3)
        for _ in range(20):
            self.tap('RIGHT',2,3)
            self.check(self.hp_q4()==damaged,'hovering equipment preserves exact fractional HP')
        self.close_menu();self.snapshot('fractional-armor-hit')
        # A same-ROM branch isolates menu no-heal from additional world damage.
        self.restore('candidate-town-source');self.equip_item(1,33);self.act(104,232)
        self.check(self.hp_q4()==104,'legitimate sanctuary rest fills half-heart capacity')
        self.equip_item(1,0);self.check(self.hp_q4()==96,'unequipping clamps fractional max health downward')
        for _ in range(3):
            self.equip_item(1,33);self.check(self.hp_q4()==96,'reequipping armor cannot farm its half heart')
            self.equip_item(1,0);self.check(self.hp_q4()==96,'repeated unequip remains96Q4')
        self.results.append({'case':'fractional-health-and-equipment-no-heal','hit_before_q4':before,'hit_after_q4':damaged,
                             'hit_delta_q4':before-damaged,'menu_hover_samples':20,'equip_cycles':3,'start_frame':start,'passed':True})
        self.coverage.append('fractional-health-and-equipment-no-heal');self.snapshot('equipment-no-free-heal')
    def safe_bow(self):
        self.restore('candidate-town-source');self.equip_item(0,17);self.goto(240,280);self.face(1);self.step(50)
        self.check(self.action()['phase']==0 and not any(a['active'] for a in self.arrows()),'clean idle bow setup is controller reached')
    def bow_cancel_case(self):
        self.safe_bow();self.snapshot('bow-controller-setup')
        def short(modal):
            self.restore('bow-controller-setup');self.step(1,'A');self.step(1)
            self.check(self.action()['phase']==1,f'short bow tap is latched before {modal}')
            if modal=='picker':self.step(3,'L');self.step(4)
            elif modal=='pause':self.tap('START',1,3);self.check(self.get('game_state')==PAUSE,'pause opens before short draw fires');self.close_menu()
            else:
                self.step(1,'SELECT')
                self.check(self.get('roll_ticks')>0,'roll starts and cancels the un-fired short bow draw')
            observed=[]
            for _ in range(70):
                self.step(1);observed.append(sum(a['active'] for a in self.arrows()))
            self.check(not any(observed),f'{modal} emits no arrow during the entire post-cancel window')
            self.check(self.action()['phase']==0,f'{modal} leaves the short draw idle')
            self.results.append({'case':'short-bow-'+modal,'post_cancel_live_arrow_samples':observed,'passed':True})
            self.coverage.append('short-bow-'+modal)
        def held(modal):
            self.restore('bow-controller-setup');self.step(16,'A');self.check(self.action()['phase']==4,'real held bow reaches charging')
            if modal=='picker':self.step(3,'L+A');self.step(4,'A')
            elif modal=='pause':self.step(1,'START+A');self.step(3,'A');self.step(1,'B+A');self.step(4,'A')
            else:
                self.step(1,'SELECT+A');self.check(self.get('roll_ticks')>0,'roll starts during held bow charge');self.step(20,'A')
            observed=[]
            for _ in range(20):
                self.step(1,'A');observed.append(sum(a['active'] for a in self.arrows()))
            self.check(not any(observed),f'{modal} emits no arrow while A remains held after cancellation')
            self.check(self.action()['phase']==0,f'{modal} cancels held charge until physical A release')
            self.step(3);self.step(1,'A');self.step(4)
            self.check(sum(a['active'] for a in self.arrows())==1,'fresh press after cancellation emits exactly one arrow')
            self.results.append({'case':'held-bow-'+modal,'post_cancel_live_arrow_samples':observed,'passed':True})
            self.coverage.append('held-bow-'+modal)
        for modal in ('picker','pause','roll'):self.run_case('short-bow-'+modal,lambda m=modal:short(m))
        for modal in ('picker','pause','roll'):self.run_case('held-bow-'+modal,lambda m=modal:held(m))
        self.snapshot('bow-cancel-and-fresh-release')
    def projectile_lock_case(self):
        self.safe_bow();self.step(24,'A');self.step(1);self.step(23)
        self.check(self.action()['phase']==0,'bow recovery finishes while charged arrow is still flying')
        self.check(any(a['active'] for a in self.arrows()),'actual player arrow remains in flight')
        self.open_tab(4)
        for _ in range(5):
            if self.get('gear_menu_slot')==0:break
            self.tap('UP',2,3)
        for _ in range(50):
            r=self.get('gear_menu_candidate');item=self.state().equipment.bag[r].item_id if r<48 else 1
            if item==1:break
            self.tap('RIGHT',2,3)
        before=bytes(self.state().equipment);self.tap('R',2,3)
        self.check(bytes(self.state().equipment)==before,'idle action with live player arrow refuses real-menu weapon change')
        self.e.screenshot(self.out/'projectile-only-equipment-lock.png');self.close_menu();self.step(60)
        self.check(not any(a['active'] for a in self.arrows()),'arrow expires normally after leaving menu')
        self.equip_item(0,1);self.results.append({'case':'projectile-only-equipment-lock','passed':True})
        self.coverage.append('projectile-only-equipment-lock')
    def companion_projectile_lock_case(self):
        for label,form in (('friendly-Fire-shot',1),('returning-Metal-pin',16)):
            self.restore('candidate-town-source');self.owned_select(form);self.equip_item(0,1)
            self.goto(240,280);self.face(1);self.ready();self.step(1,'R')
            if form==1:self.check(any(s['life'] and not s['owner'] for s in self.shots()),'controller Fire command launches a live friendly shot')
            else:
                self.check(self.get('regional_power_kind')==11 and self.get('regional_power_time')>0,'controller Metal command launches a live pin')
                self.step(17)
                self.check(self.get('regional_power_time')>0 and self.get('pin_return')==1,'Metal pin remains active on its return leg')
            self.check(self.action()['phase']==0,'companion projectile lock starts with idle mundane weapon')
            self.open_tab(4)
            for _ in range(5):
                if self.get('gear_menu_slot')==0:break
                self.tap('UP',2,3)
            for _ in range(50):
                ref=self.get('gear_menu_candidate');item=self.state().equipment.bag[ref].item_id if ref<48 else 1
                if item==17:break
                self.tap('RIGHT',2,3)
            self.check(item==17,'a different bow is selected for the lock attempt')
            before=bytes(self.state().equipment);cooldown=self.get('ability_cd');self.tap('R',2,3)
            self.check(bytes(self.state().equipment)==before,f'{label} blocks real-menu gear changes')
            self.check(self.get('ability_cd')==cooldown,'blocked gear attempt does not reset existing power cooldown')
            self.e.screenshot(self.out/(label+'-gear-lock.png'));self.close_menu();self.step(100)
            self.equip_item(0,17)
            self.results.append({'case':label+'-gear-lock','passed':True});self.coverage.append(label+'-gear-lock')
    def weapon_damage_case(self):
        for item,expected in ((1,32),(2,36)):
            self.restore('candidate-town-source');self.equip_item(0,item);self.equip_item(1,33);self.enter_basin();self.goto(213,264);self.face(2)
            before=self.enemies()[0]['hp_q4'];trace=[];self.step(1,'A')
            for _ in range(12):
                trace.append({'frame':self.e.frame,'target_hp_q4':self.enemies()[0]['hp_q4'],
                              'action':self.action(),'hit_mask':self.e.read(self.sym['weapon_action'],2)})
                self.step(1)
            damage=before-self.enemies()[0]['hp_q4']
            self.check(damage==expected,f'item{item} first sword swing deals exactly{expected}Q4 once through hit-stop')
            self.results.append({'case':'weapon-item'+str(item)+'-q4-hit','before':before,'after':self.enemies()[0]['hp_q4'],
                                 'damage_q4':damage,'expected_q4':expected,'trace':trace,'passed':True})
            self.coverage.append('weapon-item'+str(item)+'-q4-hit')
    def crowded_timing_case(self):
        self.prepare_basin(14,9);self.goto(184,264)
        before=self.hp_q4()
        for _ in range(150):
            self.step(1)
            if self.hp_q4()<before:break
        self.check(self.hp_q4()%16!=0,'stress setup has real fractional damage')
        self.goto(240,265);self.equip_item(0,17);self.face(1);self.ready();self.snapshot('crowded-bow-before')
        rows=[];last=self.get('frame');page=self.e.read(0x04000000,2)&16
        two_arrow_image=False;two_arrow_effect_image=False
        for n in range(200):
            keys='A' if n in range(0,24) or n in range(90,114) or n in (48,138) else ('R' if n in (53,153) else 0)
            self.step(1,keys);now=self.get('frame');newpage=self.e.read(0x04000000,2)&16
            rows.append({'frame':n,'update_delta':(now-last)&0xffffffff,'page_flip':newpage!=page,'cycles':self.get('render_cycles'),
                         'live_arrows':sum(a['active'] for a in self.arrows()),'live_enemies':sum(e['hp']>0 for e in self.enemies()),
                         'visible_enemies':sum(e['hp']>0 and self.get('camera_x')-8<e['x']<self.get('camera_x')+248
                             and self.get('camera_y')-8<e['y']<self.get('camera_y')+168 for e in self.enemies()),
                         'live_hostile_shots':sum(bool(s['life'] and s['owner']) for s in self.shots()),'hp_q4':self.hp_q4(),
                         'fractional_hp':bool(self.hp_q4()%16),'max_hp_q4':self.stats()['max_hp'],'obj_count':self.get('obj_count'),
                         'regional_effect':self.get('regional_power_time')})
            if rows[-1]['live_arrows']==2 and not two_arrow_image:
                self.e.screenshot(self.out/'crowded-two-arrows.png');two_arrow_image=True
            if rows[-1]['live_arrows']==2 and rows[-1]['regional_effect'] and not two_arrow_effect_image:
                self.e.screenshot(self.out/'crowded-two-arrows-water.png');two_arrow_effect_image=True
            last,page=now,newpage
            self.check(self.get('game_state')==PLAY and self.get('room')==17,'stress window remains active basin gameplay')
        path=self.out/'crowded-combat-frames.json';path.write_text(json.dumps(rows,indent=2)+'\n')
        result={'case':'crowded-fractional-two-arrow-cadence','frames':len(rows),'updates':sum(r['update_delta'] for r in rows),
                'page_flips':sum(r['page_flip'] for r in rows),'peak_cycles':max(r['cycles'] for r in rows),
                'peak_objects':max(r['obj_count'] for r in rows),'two_arrow_frames':sum(r['live_arrows']==2 for r in rows),
                'fractional_frames':sum(r['fractional_hp'] for r in rows),'max_live_enemies':max(r['live_enemies'] for r in rows),
                'max_hostile_shots':max(r['live_hostile_shots'] for r in rows),
                'max_visible_enemies':max(r['visible_enemies'] for r in rows),'trace':str(path)}
        result['strict_60hz']=all(r['update_delta']==1 and r['page_flip'] for r in rows) and result['peak_cycles']<280896
        self.frame_windows.append(result);self.report()
        self.check(result['two_arrow_frames']>0,'stress window includes simultaneous real arrows')
        self.check(result['fractional_frames']>0 and result['max_live_enemies']>=4,'stress window includes fractional health and at least four typed enemies')
        self.check(result['strict_60hz'],'crowded combat sustains one update and page flip per hardware frame')
        self.coverage.append('crowded-fractional-two-arrow-cadence');self.snapshot('crowded-bow-after')
    def complete_collection_case(self):
        self.restore('candidate-town-source')
        initial_ids={c.instance_id for c in self.roster().instances if c.flags&1}
        expected_forms=[1,2,4,5,7,8,10,11,13,14,16]
        changes=[]
        for base in (1,4,7,10):
            row=next(c for c in self.roster().instances if c.flags&1 and c.form_id in (base,base+1))
            if row.form_id==base+1:continue
            self.owned_select(base);self.open_tab(3);before=bytes(self.selected())
            self.tap('SELECT',2,3)
            self.check(self.get('game_state')==CONFIRM,f'form{base} opens explicit sanctuary evolution confirmation')
            self.tap('A',2,3);self.settle()
            self.check(self.selected().form_id==base+1,f'controller confirmation evolves form{base} to{base+1}')
            expected=bytearray(before);expected[0]=base+1
            self.check(bytes(self.selected())==bytes(expected),'evolution retains identity XP bond flags and equipped command bytes')
            changes.append({'from':base,'to':base+1,'instance_id':self.selected().instance_id})
            self.close_menu()
        def collection():
            r=self.roster()
            return [i+1 for i in range(128) if r.obtained[i>>3]&(1<<(i&7))]
        live=[c for c in self.roster().instances if c.flags&1]
        self.check(collection()==expected_forms,'one controller-earned collection contains exactly all eleven enabled forms')
        self.check(len(live)==6 and {c.instance_id for c in live}==initial_ids,'eleven historical forms retain only six original family instances')
        self.check(sorted(c.form_id for c in live)==[2,5,8,11,14,16],'live collection has six evolved-or-final enabled companions and no placeholder')
        self.check(all(self.quest(q)==3 for q in range(11)),'all eleven earned quests remain claimed after original evolutions')
        self.act(104,232);before_roster=bytes(self.roster())
        self.snapshot('collection-all-eleven-saved');saved=self.snapshots['collection-all-eleven-saved']
        self.e.close();self.e=Emulator(self.rom);self.e.load_save(saved['sram_path']);self.e.reset()
        self.step(150);self.tap('START',2,35);self.settle()
        self.check(bytes(self.roster())==before_roster,'independent SRAM reboot preserves exact eleven-form collection roster and commands')
        self.check(collection()==expected_forms,'all eleven obtained forms survive ordinary save and reboot')
        self.results.append({'case':'complete-eleven-form-collection','evolutions':changes,'obtained_form_ids':collection(),
            'live_form_ids':sorted(c.form_id for c in self.roster().instances if c.flags&1),'live_instance_count':6,
            'source_instance_ids':sorted(initial_ids),'saved_sram_path':saved['sram_path'],
            'saved_sram_sha256':saved['sram_sha256'],'independent_reboot':True,'passed':True})
        self.coverage.append('complete-eleven-form-collection');self.snapshot('collection-all-eleven-reloaded')
    def run_case(self,name,fn):
        try:fn()
        except Exception as exc:
            state=self.out/(name+'-failure.state');save=self.out/(name+'-failure.sav')
            self.e.state(state);save.write_bytes(self.e.bytes(0x0e000000,32768))
            failure={'case':name,'error':str(exc),'status':self.status(),'action':self.action(),'arrows':self.arrows(),
                     'rom_sha256':self.target_sha,'state_path':str(state),'state_sha256':digest(state),'sram_path':str(save),'sram_sha256':digest(save)}
            self.failures.append(failure);self.results.append({'case':name,'passed':False,'error':str(exc)})
            self.e.screenshot(self.out/(name+'-failure.png'));self.report();print('FAILED',name,repr(exc),flush=True)
    def run(self,scope,only=None):
        self.boot()
        cases=[]
        if scope in ('all','phases'):cases += [('phases',self.run_phases),('wood-reflection',self.wood_reflection)]
        if scope in ('all','controls'):cases += [('health-menu',self.health_menu_case),('bow-cancel',self.bow_cancel_case),
            ('projectile-lock',self.projectile_lock_case),('companion-locks',self.companion_projectile_lock_case),
            ('weapon-damage',self.weapon_damage_case),('crowded-timing',self.crowded_timing_case)]
        if scope in ('all','collection'):cases.append(('collection',self.complete_collection_case))
        for name,fn in cases:
            if only is None or name==only:self.run_case(name,fn)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba')
    p.add_argument('--symbols',type=Path,default=ROOT/'build/emberbond.sym');p.add_argument('--output',required=True,type=Path)
    p.add_argument('--expected-rom-sha',help='Optional exact SHA256 for an immutable release acceptance run')
    p.add_argument('--case',choices=('phases','wood-reflection','health-menu','bow-cancel','projectile-lock','companion-locks','weapon-damage','crowded-timing','collection'));p.add_argument('--scope',choices=('all','phases','controls','collection'),default='all');p.add_argument('--source-report',type=Path,required=True,help='Controller-earned source journey report; its hash-pinned SRAM is resolved beside the report when packaged')
    a=p.parse_args();run=CombatReview(a.rom,a.symbols,a.output,a.source_report,a.expected_rom_sha)
    try:run.run(a.scope,a.case)
    finally:run.report();run.e.close()
    return bool(run.failures)
if __name__=='__main__':raise SystemExit(main())
