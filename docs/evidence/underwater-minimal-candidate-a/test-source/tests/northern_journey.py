#!/usr/bin/env python3
"""Controller-only Northern chapter acceptance on a hash-pinned native ROM.

Only controller input mutates gameplay. Symbols, VRAM, OAM and SRAM are read-only.
The old R5 fixture supplies six genuinely owned families and eleven histories;
Northern acquisition is earned in this run. Machine-state branches are accepted
only with their same-ROM, independently hash-checked SRAM pair. Developer-only
screenshots/report contain progression details and are not a player guide.
"""
from __future__ import annotations
import argparse, binascii, ctypes as C, hashlib, inspect, json, struct, sys
from collections import Counter
from pathlib import Path
from region_journey import RegionJourney, Emulator, ROOT, PLAY, PAUSE, DEAD, DIALOG, SAVING, CONFIRM, digest
from region_combat_tests import CombatReview

R5_SHA='74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106'
R5_ROM='0ba77d82ce15619784c35a67be83950f924265b604a47495a8987afb21963e90'
OLD_FORMS=[1,2,4,5,7,8,10,11,13,14,16]
NEW_FORMS=[19,20,22,23,73,74,75,76,77,78]
ALL_FORMS=sorted(OLD_FORMS+NEW_FORMS)
SHAPES=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))


def newest_bank(raw):
    good=[]
    for offset in (0x200,0x1a00):
        b=raw[offset:offset+6144]
        if len(b)!=6144 or b[:4]!=b'EB\x05\x20' or b[20]!=0xa5:continue
        expected=int.from_bytes(b[16:20],'little');test=bytearray(b);test[16:20]=bytes(4);test[20]=0
        if binascii.crc32(test)==expected:good.append((int.from_bytes(b[8:12],'little'),offset,b))
    assert good,'No CRC-valid committed format5 bank'
    return max(good)[2]


class NorthernJourney(RegionJourney):
    # Reuse controller menu operations, never CombatReview's old-state branches.
    command=CombatReview.command
    set_command=CombatReview.set_command
    equip_item=CombatReview.equip_item
    enemies=CombatReview.enemies
    arrows=CombatReview.arrows
    shots=CombatReview.shots
    action=CombatReview.action
    stats=CombatReview.stats
    hp_q4=CombatReview.hp_q4

    def __init__(self,rom,symbols,output,expected_rom_sha,expected_symbols_sha,fixture=None):
        assert digest(rom)==expected_rom_sha,'Candidate ROM differs from explicit frozen SHA'
        assert digest(symbols)==expected_symbols_sha,'Candidate symbols differ from explicit frozen SHA'
        assert expected_rom_sha!=R5_ROM,'Northern native acceptance cannot use the old R5 ROM'
        self.target_sha=expected_rom_sha;self.symbol_sha=expected_symbols_sha
        self.coverage=[];self.cases=[];self.frame_windows=[];self.pixel_cases=[];self.acquisitions=[];self.transitions=[];self.main_selections=[]
        super().__init__(rom,symbols,output,ROOT/'tests/fixtures/v4/finished-ending.sav')
        self.north=json.loads((ROOT/'assets/northern_region/layout.json').read_text())
        strides=[]
        for stride in (20,28,32):
            if all(self.e.read(self.sym['north_art_rooms']+i*stride,2)==r['size'][0] and self.e.read(self.sym['north_art_rooms']+i*stride+2,2)==r['size'][1] and self.e.read(self.sym['north_art_rooms']+i*stride+4)==self.sym['north_background_'+r['key']] for i,r in enumerate(self.north['rooms'])):strides.append(stride)
        assert len(strides)==1,'Cannot uniquely authenticate compiled Northern room descriptor layout'
        self.north_descriptor_stride=strides[0]
        self.contract=json.loads((ROOT/'assets/northern_region/contract.json').read_text())
        self.contract_sha=digest(ROOT/'assets/northern_region/contract.json')
        sources=tuple(dict.fromkeys([Path(__file__).resolve(),ROOT/'tests/region_journey.py',ROOT/'tests/region_combat_tests.py',ROOT/'tests/test_save5.py',ROOT/'tests/test_save4.py',ROOT/'tools/mgba_runner.py']+[Path(inspect.getfile(cls)).resolve() for cls in type(self).__mro__ if cls.__module__!='builtins']))
        self.test_sources={str(p.relative_to(ROOT)):digest(p) for p in sources}
        (self.out/'test-source').mkdir(exist_ok=True)
        for p in sources:(self.out/'test-source'/p.name).write_bytes(p.read_bytes())
        self.fixture=Path(fixture or ROOT/'tests/fixtures/v5-revision2/all-eleven-town.sav').resolve()
        assert digest(self.fixture)==R5_SHA,'Use only the authenticated unchanged R5 SRAM fixture'
        self.source_bytes=self.fixture.read_bytes();self.source_bank=newest_bank(self.source_bytes)
        assert int.from_bytes(self.source_bank[12:14],'little')==2,'Source is exact content revision2'
        self.e.load_save(self.fixture);self.e.reset();self.main_only=False
        self.provenance={'fixture_path':str(self.fixture),'sram_sha256':R5_SHA,'source_rom_sha256':R5_ROM,
            'source_machine_state_loaded':False,'scope':'Prior six owned families/eleven histories only. No Northern progress exists in fixture.'}
        self.report()

    def report(self):
        if not hasattr(self,'provenance'):return
        data={'suite':'northern-native-controller-journey','controller_only':True,'game_ram_writes':0,
            'player_facing':False,'provenance':self.provenance,**self.candidate,
            'test_sources':self.test_sources,
            'content_contract_sha256':self.contract_sha,'compiled_room_descriptor_stride':self.north_descriptor_stride,
            'branch_policy':'Same tested ROM and symbols, hash-checked state/SRAM pairs only; no machine states imported from prior ROMs',
            'enabled_rows_are_not_acquisition_evidence':True,'acquisition_event_policy':'Events include explicit same-ROM alternate branches; count distinct retained instances only in the final collection snapshot','checks':self.checks,'failures':self.failures,
            'cases':self.cases,'coverage':self.coverage,'acquisitions':self.acquisitions,'snapshots':self.snapshots,
            'transitions':self.transitions,'main_route_selected_form_ids':sorted(set(self.main_selections)),
            'frame_windows':self.frame_windows,'pixel_cases':self.pixel_cases,'inputs':self.inputs}
        (self.out/'northern-journey.json').write_text(json.dumps(data,indent=2)+'\n')

    def step(self,n,keys=0):
        before=self.get('room')
        if self.main_only and self.get('game_state')==PLAY:
            form=self.selected().form_id;self.main_selections.append(form)
            self.check(form not in (10,11,75,76),'mandatory route never selects an Earth companion')
        super().step(n,keys)
        after=self.get('room')
        if before!=after:self.transitions.append({'frame':self.e.frame,'from':before,'to':after,'keys':keys})

    def snapshot(self,name,settle=True):
        if settle:self.settle()
        state=self.out/(name+'.state');save=self.out/(name+'.sav');shot=self.out/(name+'.png')
        self.e.screenshot(shot);self.e.state(state);save.write_bytes(self.e.bytes(0x0e000000,32768))
        self.snapshots[name]={'rom_sha256':self.target_sha,'symbols_sha256':self.symbol_sha,
            'state_path':str(state),'state_sha256':digest(state),'sram_path':str(save),'sram_sha256':digest(save),
            'screenshot':str(shot),'status':self.status(),'quests':[self.quest(q) for q in range(22)],
            'obtained_form_ids':self.collection(),'owned_form_ids':[c.form_id for c in self.roster().instances if c.flags&1]}
        self.report();print(name,self.status(),'Northern quests',[self.quest(q) for q in range(11,22)],flush=True);return name

    def restore(self,name):
        r=self.snapshots[name]
        assert digest(self.rom)==r['rom_sha256']==self.target_sha
        assert digest(self.symbol_path)==r['symbols_sha256']==self.symbol_sha
        assert digest(r['state_path'])==r['state_sha256'] and digest(r['sram_path'])==r['sram_sha256']
        self.e.load_save(r['sram_path']);self.e.state(r['state_path'],True);self.step(4)

    def mask(self):
        room=self.get('room')
        if room<22:return super().mask()
        d=self.north['rooms'][room-22];base=self.sym['north_art_rooms']+(room-22)*self.north_descriptor_stride
        w,h=self.e.read(base,2),self.e.read(base+2,2);ptr=self.e.read(base+12);count=self.e.read(base+16,2);b=bytearray(w*h)
        for y in range(h):
            for x in range(w):
                if x<5 or y<5 or x>w-6 or y>h-6:b[y*w+x]=1
        # Mirrors inclusive foot overlap from north_game_solid, not pathfinding
        # through an actor or direct player-position manipulation.
        for i in range(count):
            x,y,rw,rh=struct.unpack('<4h',self.e.bytes(ptr+i*8,8));left,right=max(0,x-5),min(w,x+rw+5)
            for yy in range(max(0,y-5),min(h,y+rh+5)):b[yy*w+left:yy*w+right]=b'\1'*(right-left)
        return b,w,h

    def collection(self):
        return [i+1 for i in range(128) if self.roster().obtained[i>>3]&(1<<(i&7))]
    def live(self):return [c for c in self.roster().instances if c.flags&1]
    def puzzle(self):return list(self.e.bytes(self.sym['north_game_puzzle'],4))
    def owned_select(self,form):
        if not any(i<160 and self.roster().instances[i].form_id==form for i in self.roster().party):self.assign(3,form)
        self.select_form(form)
    def cast_owned(self,form,x,y,cmd=None):
        self.owned_select(form)
        if cmd is not None:self.set_command(cmd)
        self.goto(x,y);self.ready();before=self.selected().instance_id;self.tap('R');self.settle()
        self.check(self.selected().instance_id==before,'field command keeps selected instance identity')
    def reward(self,q,form=None):
        self.check(self.quest(q)==3,f'quest{q} reward really claimed by controller')
        if form:
            rows=[c for c in self.live() if c.form_id==form];self.check(len(rows)==1,f'form{form} has exactly one real owned instance')
            c=rows[0];self.acquisitions.append({'quest':q,'form_id':form,'instance_id':c.instance_id,'level':c.level,'bond':c.bond,'frame':self.e.frame})
            self.check(not c.flags&2,f'new form{form} is not a legacy story-locked fixture instance')
    def entry(self,room):
        here=self.get('room')
        if room==22 and here==16:self.act(400,280)
        elif room==23 and here==22:self.goto(240,16);self.step(8,'UP');self.settle()
        elif room==22 and here==23:self.goto(240,300);self.step(8,'DOWN');self.settle()
        elif room in (24,25) and here==22:self.act(88 if room==24 else 384,144,1)
        elif room==26 and here==23:self.act(400,72,1)
        elif room in (27,28,29) and here==room-1:self.act(208,72)
        else:raise AssertionError(('unsupported controller transition',here,room))
        self.check(self.get('room')==room,f'ordinary transition {here} to{room}')
    def exit_north(self,target):
        if self.get('room')==22 and target==16:self.act(240,280)
        else:self.leave_interior(target)
        self.check(self.get('room')==target,'ordinary return transition is usable')
    def to_town(self):
        while self.get('room')>=24:self.exit_north(22 if self.get('room') in (24,25) else 23 if self.get('room')==26 else self.get('room')-1)
        if self.get('room')==23:self.entry(22)
        self.check(self.get('room')==22,'Northern town return')

    def boot(self):
        self.step(150);self.tap('START',2,35);self.settle();s=self.state();b=self.source_bank
        self.check(self.get('room')==16,'authentic R5 save resumes in Reedhaven')
        self.check(bytes(s.roster.instances)==b[160:4000],'R5 forward migration preserves all160 exact instance records')
        self.check(bytes(s.roster.party)==b[4000:4004] and s.roster.selected_party==b[4004],'R5 forward migration retains party and selected identity')
        self.check(bytes(s.roster.seen)+bytes(s.roster.obtained)+bytes(s.roster.rewards)==b[96:144],'R5 exact collection/reward ledger preservation')
        self.check(bytes(s.quests)==b[4032:4296] and bytes(s.equipment)==b[4544:5056],'R5 exact prior quests and equipment preserved')
        self.check(bytes(s.roster.expedition_bond)+bytes(s.roster.expedition_events)+bytes(s.roster.lifetime_field_aid)==b[4296:4536],'R5 expedition credits and bond ledger preserved')
        self.check(self.collection()==OLD_FORMS and len(self.live())==6,'source genuinely owns six instances with eleven historical forms')
        self.check(all(self.quest(q)==0 and not s.quests.objectives[q] for q in range(11,22)) and not s.quests.region_flags[1],'migration invents no Northern content')
        self.old_ids={c.instance_id for c in self.live()};self.old_quests=bytes(s.quests);self.snapshot('00-r5-forward-migration')
        self.entry(22);self.snapshot('01-quay-entry');self.pixel_case('quay-native-source')

    def recruits_main(self):
        self.act(168,208);self.snapshot('02-lines-active')
        # Both orderings earn the same real objectives/reward, with no cloning.
        for order in ((304,160),(160,304)):
            self.restore('02-lines-active')
            for x in order:self.act(x,224)
            self.check(self.quest(11)==2,'either cargo-line order reaches ready')
            self.act(168,208);self.reward(11,19)
            if order==(304,160):self.snapshot('lines-reversed-order')
        self.assign(0,19);self.select_form(19);self.main_only=True
        self.entry(23);self.act(320,208)
        self.check(not self.state().quests.objectives[13],'wrong manual rail cannot grant bearing')
        self.act(240,208);self.act(320,208);self.act(352,176);self.reward(13,77)
        self.assign(1,77);self.select_form(19);self.snapshot('03-guaranteed-base-recruits')
        self.check(self.old_ids<={c.instance_id for c in self.live()},'every original story/river companion remains owned')
        self.entry(26)

    def puzzle_room(self,room):
        self.check(self.get('room')==room,'expected linked dungeon chamber')
        bit=1<<(room-26);self.snapshot(f'{room}-unsolved-entry')
        before=self.puzzle();self.cast_owned(77,64,80);self.cast_owned(19,120,112)
        self.check(self.puzzle()==before,'wrong powers do not mutate cart/junction state')
        self.cast_owned(77,120,112);self.act(32,132)
        self.check(self.puzzle()==[0,0,0,0],'reachable manual reset restores unsolved mechanism')
        self.cast_owned(77,120,112);self.exit_north(23 if room==26 else room-1)
        self.entry(room);self.check(self.puzzle()==[0,0,0,0],'unsolved transient rail resets on ordinary reentry')
        for _ in range(2 if room==28 else 1):self.cast_owned(77,120,112)
        self.cast_owned(19,64,80);self.cast_owned(19,64,80);self.act(176,112)
        if room!=26:
            self.cast_owned(77,120,112);self.cast_owned(77,120,112)
            self.cast_owned(19,64,80);self.cast_owned(19,64,80)
        self.check(self.state().quests.objectives[21]&bit,'real cart arrangement earns permanent linked objective')
        solved=self.puzzle();self.act(32,132)
        self.check(self.state().quests.objectives[21]&bit and self.puzzle()[1]==2,'reset preserves completed room stage')
        self.snapshot(f'{room}-solved-manual-weight');self.entry(room+1)

    def machine(self,cls=1):
        self.equip_item(0,{1:1,2:9,3:17}[cls]);self.cast_owned(19,64,124);self.cast_owned(77,176,124)
        self.act(120,124);self.check(self.get('north_game_machine_stage',1)==1,'handle starts visible machine telegraph')
        self.snapshot(f'machine-{cls}-telegraph');trace=[]
        # Safe lower floor during telegraph/sweep, actual weapon during exposure.
        for cycle in range(12):
            if self.get('north_game_machine_stage',1)==5:break
            self.goto(120,116)
            for _ in range(300):
                stage=self.get('north_game_machine_stage',1)
                trace.append({'frame':self.e.frame,'stage':stage,'ticks':self.get('north_game_machine_ticks',1),'hp_q4':self.get('north_game_machine_hp',1)})
                if stage in (3,5):break
                self.step(1)
            if self.get('north_game_machine_stage',1)==5:break
            self.goto(120,80);self.face(1)
            for _ in range(3):
                before=self.get('north_game_machine_hp',1)
                self.tap('A',2,22);self.settle();after=self.get('north_game_machine_hp',1)
                trace.append({'frame':self.e.frame,'stage':self.get('north_game_machine_stage',1),'hp_q4':after,'damage_q4':before-after,'weapon_class':cls})
                if self.get('north_game_machine_stage',1)!=3:break
        self.check(self.get('north_game_machine_stage',1)==5 and self.get('north_game_machine_hp',1)==0,f'ordinary weapon class{cls} defeats exposed machine through collision')
        self.check(any(r.get('damage_q4',0)>0 for r in trace),'machine damage is observed after actual A attacks')
        self.act(120,124);self.reward(21);self.cases.append({'case':'machine-weapon-'+str(cls),'trace':trace,'passed':True})
        self.snapshot(f'machine-{cls}-cleared')

    def main_route(self):
        self.recruits_main()
        for room in (26,27,28):self.puzzle_room(room)
        self.snapshot('04-machine-ready')
        for cls in (2,3,1):
            self.restore('04-machine-ready');self.machine(cls)
        self.check(not set(self.main_selections)&{10,11,75,76},'entire mandatory route succeeds without selecting Earth')
        self.main_only=False;self.coverage.append('mandatory-base-Wood-Metal-manual-weights-no-Earth')
        self.to_town();self.act(104,208);self.snapshot('05-main-complete-town')

    def optional_recruits(self):
        self.entry(25);self.cast_owned(2,176,80,1)
        self.check(not self.state().quests.objectives[12],'heat cannot skip two manual kiln prerequisites')
        self.act(120,80);self.act(64,80);self.cast_owned(19,176,80)
        self.check(self.state().quests.objectives[12]==3,'wrong Wood cannot ignite the opened kiln')
        self.cast_owned(2,176,80,1);self.act(208,128);self.reward(12,22);self.exit_north(22)
        self.entry(23);self.act(144,128)
        self.check(not self.state().quests.objectives[14]&4,'unsafe forecast never completes tender movement')
        self.act(176,160);self.act(176,160);self.act(144,128);self.act(144,128);self.act(112,112)
        self.check(self.quest(14)==2,'safe manual tender path and both discovery cues reach ready')
        for x,y in ((368,256),(176,240),(288,128)):self.act(x,y)
        self.entry(22);self.act(64,208);self.reward(14,73);self.act(416,224);self.reward(15,75)
        self.snapshot('06-all-five-new-recruits')

    def trials(self):
        # Optional exploration can leave the real hero at one heart. Rest by
        # ordinary interaction before this long non-combat puzzle itinerary;
        # do not depend on a particular global-frame phase to dodge every hit.
        # Deliberate death/retry remains independently covered in lifecycle().
        retained=bytes(self.roster());quests=bytes(self.state().quests)
        self.act(104,208)
        self.check(self.hp_q4()>0 and bytes(self.roster())==retained and bytes(self.state().quests)==quests,
                   'ordinary town rest prepares trials without changing retained companions or quest rewards')
        self.entry(24);self.cast_owned(19,176,96);self.exit_north(22);self.entry(24)
        self.check(self.state().quests.objectives[16]==2,'partial roof objective survives leaving/reentry')
        self.cast_owned(19,64,96);self.act(208,128);self.reward(16)
        self.cast_owned(73,120,96);self.act(32,132);self.cast_owned(73,120,96);self.act(120,96);self.cast_owned(73,120,96)
        self.act(208,128);self.reward(18);self.exit_north(22)
        self.entry(25);self.cast_owned(22,64,80)
        for x in (176,64,120):self.cast_owned(22,x,120)
        self.act(208,128);self.reward(17);self.exit_north(22)
        self.entry(23);self.entry(26);self.entry(27);self.cast_owned(75,208,128);self.act(208,128);self.reward(19)
        self.entry(28)
        # Completed relay enters at rail0. Retrace after leaving retains bits.
        self.cast_owned(77,208,128);self.exit_north(27);self.entry(28)
        self.check(self.state().quests.objectives[20]&1,'partial compass objective persists on leave')
        self.cast_owned(77,208,128);self.cast_owned(77,120,112);self.cast_owned(77,208,128)
        self.cast_owned(77,120,112);self.cast_owned(77,120,112);self.cast_owned(77,208,128)
        self.act(208,128);self.reward(20);self.to_town();self.act(104,208)
        self.check(all(self.quest(q)==3 for q in range(11,22)),'all eleven Northern quests earned')
        self.check({3,11,19,35,51,83}<={r.item_id for r in self.state().equipment.bag},'all six sidegrade items genuinely awarded')
        self.check(self.state().quests.region_flags[1]==255,'all eight Northern rooms actually visited')
        self.snapshot('07-all-northern-quests')

    def evolutions(self):
        expected_trials={19:32,22:64,73:128,75:256,77:512}
        changes=[]
        for base,trial in expected_trials.items():
            self.owned_select(base);self.act(104,208);self.open_tab(3)
            before=bytes(self.selected());roster=bytes(self.roster());quests=bytes(self.state().quests)
            self.check(self.selected().trial_flags&trial,f'form{base} earned its actual personal trial')
            self.tap('SELECT',2,4);self.check(self.get('game_state')==CONFIRM,'Northern evolution asks for explicit confirmation')
            self.e.screenshot(self.out/f'evolution-{base}-confirmation.png');self.tap('B',2,4)
            self.check(bytes(self.roster())==roster and bytes(self.state().quests)==quests,'decline keeps instance/history/quest bytes identical')
            self.tap('SELECT',2,4);self.wait_evolution();self.tap('A',2,3);self.wait_evolution(8);self.settle()
            self.check(self.selected().form_id==base+1,f'confirmed actual evolution {base} to{base+1}')
            expected=bytearray(before);expected[0]=base+1
            self.check(bytes(self.selected())==bytes(expected),'evolution changes form only and retains identity/selected command')
            old_cmd=self.command();self.tap('R',2,25);self.settle()
            self.check(self.command()==old_cmd+1,'new learned evolved command explicitly selected in journal')
            self.close_menu();self.ready();self.tap('R');self.step(10);self.settle()
            self.snapshot(f'evolved-{base+1}-actual-command')
            changes.append({'base':base,'evolved':base+1,'instance_id':self.selected().instance_id,'command':self.command()})
        self.check(self.collection()==ALL_FORMS,'one actual save earns all21 historical form bits')
        self.check(len(self.live())==11 and len({c.instance_id for c in self.live()})==11,'complete21-history collection has11 real owned instances')
        self.check(self.old_ids<={c.instance_id for c in self.live()},'collection preserves every original instance rather than cloning historical forms')
        self.cases.append({'case':'five-confirmed-evolutions','changes':changes,'passed':True})

    def lifecycle(self):
        self.act(104,208);before=(bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))
        for x,y in ((168,208),(312,208),(64,208),(384,176),(416,224)):self.act(x,y)
        self.check((bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))==before,'repeated Northern turn-ins are byte-identical no-ops')
        self.snapshot('08-complete21-saved');saved=self.snapshots['08-complete21-saved']
        self.e.close();self.e=Emulator(self.rom);self.e.load_save(saved['sram_path']);self.e.reset();self.step(150);self.tap('START',2,35);self.settle()
        self.check((bytes(self.roster()),bytes(self.state().quests),bytes(self.state().equipment))==before,'independent emulator SRAM reboot preserves complete roster/quests/gear byte-for-byte')
        self.check(self.collection()==ALL_FORMS and len(self.live())==11,'independent reboot retains21 earned forms in11 instances')
        self.snapshot('09-complete21-independent-reboot');self.exit_north(16)
        self.check(all(self.quest(q)==3 for q in range(11)),'old eleven quests survive complete Northern round trip')
        self.check(self.old_ids<={c.instance_id for c in self.live()},'old-region return keeps original family identities')
        self.snapshot('10-old-region-return');self.entry(22);self.entry(23);self.act(80,264);self.goto(240,208)
        for _ in range(600):
            if self.get('game_state')==DEAD:break
            self.step(10)
        self.check(self.get('game_state')==DEAD,'actual ordinary Northern enemy damage reaches death without health injection')
        self.e.screenshot(self.out/'north-ordinary-death.png');self.tap('A',2,30);self.settle()
        self.check(self.get('room')==23 and self.hp_q4()>0,'ordinary Northern death/retry returns to valid rest checkpoint')
        self.check(self.collection()==ALL_FORMS and len(self.live())==11 and all(self.quest(q)==3 for q in range(22)),'death retry does not lose or duplicate earned content')
        self.snapshot('11-north-death-retry')

    def oam(self):
        raw=self.e.bytes(0x07000000,1024);out=[]
        for i in range(128):
            a0,a1,a2,_=struct.unpack_from('<HHHH',raw,i*8)
            if a0&0x300==0x200:continue
            shape=a0>>14;size=a1>>14;assert shape<3 and not a0&0x100
            w,h=SHAPES[shape][size];x=a1&511;y=a0&255
            if x>=256:x-=512
            if y>=160:y-=256
            out.append(dict(slot=i,x=x,y=y,w=w,h=h,tile=a2&1023,priority=(a2>>10)&3,flipx=bool(a1&0x1000),flipy=bool(a1&0x2000),eightbit=bool(a0&0x2000)))
        return out

    def pixel_case(self,name):
        self.step(150);self.check(self.get('game_state')==PLAY and not self.get('toast_ticks') and not self.get('area_ticks'),'native pixel scene has no transient text')
        room=self.get('room');d=self.north['rooms'][room-22];w,h=d['size'];cx,cy=self.get('camera_x'),self.get('camera_y')
        atlas=self.e.bytes(self.sym['north_background_'+d['key']],w*h)
        expected=b''.join(atlas[(cy+y)*w+cx:(cy+y)*w+cx+240] for y in range(160))
        page=0x0600a000 if self.e.read(0x04000000,2)&16 else 0x06000000;actual=self.e.bytes(page,38400)
        bad=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
        # Source comparison is intended for exterior bitmap-only scenes. Puzzle
        # overlays are tested separately, never silently masked as source art.
        self.check(room in (22,23),'full-source comparison uses documented exterior scene')
        result={'name':name,'room':room,'camera':[cx,cy],'source_pixels':38400,'rows_compared':160,'mismatches':len(bad),'examples':bad[:20]}
        self.pixel_cases.append(result);self.check(not bad,'all240x160 displayed bitmap pixels match exact ROM source')
        oam=self.oam();positions={(o['x'],o['y'],o['w'],o['h']) for o in oam if o['priority']==0}
        self.check((3,3,16,16) in positions and (216,3,16,16) in positions and (204,8,8,8) in positions,'HUD floats in actual viewport corners')
        self.check(len(oam)<=128 and self.get('obj_count')<=128,'OAM insertion budget stays bounded')
        self.e.screenshot(self.out/(name+'.png'));result['oam']=oam;self.report()

    def cadence(self,name,count=180,keys=None):
        self.settle();self.step(10);last=self.get('frame');page=self.e.read(0x04000000,2)&16;rows=[]
        for i in range(count):
            self.step(1,keys(i) if keys else 0);now=self.get('frame');newpage=self.e.read(0x04000000,2)&16
            rows.append({'hardware_frame':self.e.frame,'update_delta':(now-last)&0xffffffff,'page_flip':newpage!=page,
                'render_cycles':self.get('render_cycles'),'game_state':self.get('game_state'),'journal_tab':self.get('journal_tab'),'camera':[self.get('camera_x'),self.get('camera_y')],
                'obj_count':self.get('obj_count'),'arrows':sum(a['active'] for a in self.arrows()),'hostile_shots':sum(bool(s['life'] and s['owner']) for s in self.shots()),
                'enemies':sum(e['hp']>0 for e in self.enemies()),'effect':self.get('northern_power_time'), 'cast':self.get('northern_power_cast_time')})
            last,page=now,newpage
        result={'name':name,'hardware_frames':count,'game_updates':sum(r['update_delta'] for r in rows),'page_flips':sum(r['page_flip'] for r in rows),
            'update_histogram':dict(Counter(r['update_delta'] for r in rows)),'max_cycles':max(r['render_cycles'] for r in rows),'frame_budget':280896,
            'source':'emulated hardware frames, active game updates and displayed page flips; never host FPS','trace':rows}
        self.frame_windows.append(result);self.report()
        self.check(all(r['update_delta']==1 and r['page_flip'] for r in rows),name+': every actual hardware frame updates and presents')
        self.check(result['max_cycles']<280896 and max(r['obj_count'] for r in rows)<=128,name+': native cycles and OAM stay within bounds')
        return result

    def run(self,scope='full'):
        self.boot()
        if scope=='migration':return
        self.main_route()
        if scope=='main':return
        self.optional_recruits();self.trials();self.evolutions();self.lifecycle()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',required=True,type=Path);p.add_argument('--symbols',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True)
    p.add_argument('--source-sram',type=Path);p.add_argument('--scope',choices=('migration','main','full'),default='full')
    a=p.parse_args();run=NorthernJourney(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_sram)
    try:run.run(a.scope)
    except Exception as exc:
        run.failures.append({'error':str(exc),'status':run.status()});run.snapshot('failure',settle=False);raise
    finally:run.report();run.e.close()
    return 0
if __name__=='__main__':raise SystemExit(main())
