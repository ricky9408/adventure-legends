#!/usr/bin/env python3
"""Developer-only Southern native controller combat/control acceptance.

The acquisition source is authenticated separately. Only its paired SRAM is
cold-imported; all branches are newly produced same-candidate state+SRAM pairs.
No game-memory writes, function injection or fabricated enemies/ownership.
Synthetic host tests are complementary and never counted in this report.
"""
from __future__ import annotations
import argparse, hashlib, json, struct, traceback, subprocess, sys
from pathlib import Path
from southern_journey import SouthernJourney, ALL_FORMS, N5_SHA, N5_ROM
from northern_journey import newest_bank, NorthernJourney
from northern_combat_tests import NorthernCombat
from region_journey import ROOT, PLAY, PAUSE, DIALOG, SAVING, EVENT_PENDING, digest
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools

SNAPSHOT='08-complete41-independent-reboot'
ARCHIVE={
 'report':'1fac204c56125dde0f56a55929bc1c4a0a8863195e1217e9ace8cf8c2e63a6f8',
 'rom':'35d1def3959d88f071a79d7da2ed3219114415dbd4db09c151f1f2e72c3f47c1',
 'symbols':'50e6f963a035d4f0b0a30ed0e142af51e9df755270d5b246a64dae2bcc6e22ce',
 'sram':'0bd83c19eb0dee81b3cd9e2b48462f6362b559786e38fa119312fe05787b0bd3',
 'manifest':'bc39ad22c25dd42761e99291bf250a977582f62a3adf274dd7d1b6d9ef9f6390'}
OWNERS={c:f for c,f in zip(range(23,43),(26,26,29,29,80,80,82,82,84,84,86,86,88,88,90,90,92,92,94,94))}
PHASES={c:p for c,p in zip(range(23,43),(0,0,2,2,4,4,1,1,2,2,3,3,0,0,4,4,1,1,3,3))}
NAMES=dict(zip(range(23,43),('Leafbound','Canopy Arc','Dune fan','Dune diversion','Water split','Water intercept','Ranged windup delay','Fire annulus','Side guard','Switching side guard','Narrow frontal parry','Crossing line','One approach lure','Paired approach lure','Water fork','Water crescent','Single weapon echo','Paired weapon echo','Single ricochet','Returning fan')))


def artifact(report_path,record_path,fallback):
    p=Path(record_path);p=p if p.is_absolute() else report_path.parent/p
    return p if p.is_file() else report_path.parent/fallback


def validate_source_report(path,rom_sha,sym_sha):
    path=Path(path).resolve();r=json.loads(path.read_text());sha=digest(path)
    assert r['suite']=='southern-native-controller-journey'
    assert r.get('controller_only') is True and r.get('game_ram_writes')==0
    assert not r['failures'] and r['checks'] and all(c.get('passed') is True for c in r['checks'])
    archived=sha==ARCHIVE['report']
    assert archived or (r['rom_sha256'],r['symbols_sha256'])==(rom_sha,sym_sha),'Unpinned cross-ROM acquisition source'
    if archived:assert (r['rom_sha256'],r['symbols_sha256'],r['source_manifest_sha256'])==(ARCHIVE['rom'],ARCHIVE['symbols'],ARCHIVE['manifest'])
    assert r['enabled_rows_are_not_acquisition_evidence'] is True
    assert '10-southern-death-retry' in r['snapshots'],'Incomplete producer lifecycle route'
    assert r['provenance']['sram_sha256']==N5_SHA and r['provenance']['source_rom_sha256']==N5_ROM
    assert r['provenance']['source_machine_state_loaded'] is False
    assert all(r['frozen_source_checks'].values())
    for key,fallback in [('rom_path','tested.gba'),('symbols_path','tested.sym')]:
        p=artifact(path,r[key],fallback);assert digest(p)==r[key.replace('_path','_sha256')]
    manifest=path.parent/'candidate-source-hashes.json';assert digest(manifest)==r['source_manifest_sha256']
    for filename,expected in r['test_sources'].items():
        p=path.parent/'test-source'/Path(filename).name;assert digest(p)==expected,'Producer script changed: '+filename
        if not archived:assert digest(ROOT/filename)==expected,'Same-target producer uses stale test source'
    if not archived:
        assert r['content_contract_sha256']==digest(ROOT/'assets/southern_region/contract.json')
        assert r['scene_sha256']==digest(ROOT/'assets/southern_region/scene.json')
    rec=r['snapshots'][SNAPSHOT];save=artifact(path,rec['sram_path'],Path(rec['sram_path']).name)
    assert digest(save)==rec['sram_sha256'] and (not archived or rec['sram_sha256']==ARCHIVE['sram'])
    assert (rec['rom_sha256'],rec['symbols_sha256'])==(r['rom_sha256'],r['symbols_sha256'])
    bank=newest_bank(save.read_bytes());assert int.from_bytes(bank[12:14],'little')==(4 if archived else 6)
    live=[(bank[160+i*24],int.from_bytes(bank[168+i*24:172+i*24],'little')) for i in range(160) if bank[161+i*24]&1]
    obtained=[i+1 for i in range(128) if bank[112+(i>>3)]&(1<<(i&7))]
    quests=[(bank[4032+(i>>2)]>>((i&3)*2))&3 for i in range(30)]
    assert len(live)==21 and len({x[1] for x in live})==21 and all(x[1] for x in live)
    assert obtained==ALL_FORMS==rec['obtained_form_ids'] and quests==[3]*30==rec['quests']
    assert sorted(x[0] for x in live)==sorted(rec['owned_form_ids'])
    ancestor=ROOT/'tests/fixtures/v5-revision3/northern-all21-town.sav';assert digest(ancestor)==N5_SHA
    old=newest_bank(ancestor.read_bytes());oldids={int.from_bytes(old[168+i*24:172+i*24],'little') for i in range(160) if old[161+i*24]&1}
    assert oldids<={x[1] for x in live},'Earned ancestor identity lost'
    return dict(path=str(path),report_sha256=sha,rom_sha256=r['rom_sha256'],symbols_sha256=r['symbols_sha256'],sram_path=str(save),sram_sha256=digest(save),snapshot=SNAPSHOT,source_machine_state_loaded=False,trust='pinned-controller-acquisition-archive' if archived else 'same-target-current-controller-journey',source_manifest_sha256=r['source_manifest_sha256'],scope='41 controller-earned histories,21 retained instances,30 claimed quests; SRAM-only import; no prior combat acceptance implied')


def elf_locals(path,filename):
    """Read ELF32 STT_FILE-scoped locals; nm name collisions are not authority."""
    raw=Path(path).read_bytes();assert raw[:6]==b'\x7fELF\x01\x01'
    header=struct.unpack_from('<16sHHIIIIIHHHHHH',raw);off,entsize,count=header[6],header[11],header[12]
    sections=[struct.unpack_from('<IIIIIIIIII',raw,off+i*entsize) for i in range(count)]
    answer={}
    for section in sections:
        if section[1]!=2:continue
        strings=sections[section[6]];strings=raw[strings[4]:strings[4]+strings[5]];current=None
        for p in range(section[4],section[4]+section[5],section[9]):
            name,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,p);name=strings[name:].split(b'\0',1)[0].decode()
            if info&15==4:current=name
            if current==filename and info>>4==0 and info&15==1:answer[name]={'address':value,'size':size}
    assert 'missiles' in answer and 'caster_id' in answer,'Southern local symbols missing from exact ELF'
    return answer


class SouthernCombat(SouthernJourney):
    gear_candidate=NorthernCombat.gear_candidate
    arrows=NorthernCombat.arrows
    stats=NorthernCombat.stats
    def __init__(self,rom,symbols,output,rom_sha,sym_sha,source_report,source_manifest,elf):
        self.ready_report=False;self.source_evidence=validate_source_report(source_report,rom_sha,sym_sha)
        super().__init__(rom,symbols,output,rom_sha,sym_sha,source_manifest=source_manifest,elf=elf)
        self.locals=elf_locals(elf,'southern_powers.c');self.elf_sha=digest(elf)
        extracted=self.out/'verified-elf-binary.gba';subprocess.run([resolve_arm_tools('objcopy',root=ROOT)['objcopy'],'-O','binary',str(elf),str(extracted)],check=True)
        eraw=extracted.read_bytes();rraw=self.rom.read_bytes();assert len(eraw)==len(rraw) and eraw[0xc0:]==rraw[0xc0:],'ELF load image does not match frozen ROM beyond repaired cartridge header'
        self.elf_pairing={'elf_sha256':self.elf_sha,'extracted_binary_sha256':digest(extracted),'rom_sha256':self.target_sha,'matched_bytes':len(eraw)-0xc0,'header_note':'Only first192bytes containing fix_header.py cartridge metadata are excluded'}
        for filename in ('tests/southern_combat_tests.py','tests/northern_combat_tests.py','tests/southern_controls.py','tools/arm_toolchain.py'):
            self.test_sources[filename]=digest(ROOT/filename);(self.out/'test-source'/Path(filename).name).write_bytes((ROOT/filename).read_bytes())
        self.provenance=self.source_evidence;self.notes=[];self.accepted_commands=[];self.native_write_attempts=[]
        def forbidden_write(*args,**kwargs):
            self.native_write_attempts.append({'args':repr(args)});raise AssertionError('Gameplay memory writes are forbidden')
        self.e.write=forbidden_write;self.e.lib.eb_write=forbidden_write
        self.e.load_save(self.provenance['sram_path']);self.e.reset();self.ready_report=True;self.report()
    def report(self):
        if not getattr(self,'ready_report',False):return
        data={'suite':'southern-native-combat-controls','controller_only':True,'game_ram_writes':0,'game_ram_write_attempts':self.native_write_attempts,'player_facing':False,'synthetic_gameplay':False,
          'provenance':self.provenance,**self.candidate,'elf_sha256':self.elf_sha,'elf_rom_pairing':self.elf_pairing,'test_sources':self.test_sources,'source_manifest_sha256':self.source_manifest_sha,'frozen_source_checks':self.source_checks,'content_contract_sha256':self.contract_sha,'scene_sha256':self.scene_sha,
          'branch_policy':'Only this exact candidate creates and restores hash-checked machine-state+SRAM pairs; source machine states are never imported',
          'timing_caveat':'Render cycles exclude final VBlank/OAM commit; strict acceptance also requires one update and displayed-page flip per hardware frame',
          'native_commands_accepted':sorted(set(self.accepted_commands)),'checks':self.checks,'failures':self.failures,'cases':self.cases,'coverage':self.coverage,'frame_windows':self.frame_windows,'pixel_cases':self.pixel_cases,'snapshots':self.snapshots,'notes':self.notes,'inputs':self.inputs}
        (self.out/'southern-combat.json').write_text(json.dumps(data,indent=2)+'\n')
    def local(self,name,signed=False):
        r=self.locals[name];assert r['size'] in (1,2,4),name
        n=self.e.read(r['address'],r['size']);return n-(1<<(r['size']*8)) if signed and n>>(r['size']*8-1) else n
    def power(self):
        fields=('kind','time','form','direction','origin_x','origin_y','age','cooldown','cast_time','phase')
        p={k:self.get('southern_power_'+k) for k in fields}
        p.update({k:self.local(k,k=='guard_side') for k in ('caster_id','lease_generation','hit_mask','spent','mark_a','mark_b','delayed','redirected','redirect_left','slow_mask','side_changed','startup_until','guard_grace','guard_enemy','guard_side','ax','ay','bx','by','ex','ey')})
        p.update(global_cooldown=self.get('ability_cd'),tile_owner=self.get('tile_owner'))
        p['missiles']=[dict(zip(('x','y','dx','dy','error','life','stage','harmless','pad'),struct.unpack('<5h4B',self.e.bytes(self.locals['missiles']['address']+i*14,14)))) for i in range(3)]
        return p
    def enemies(self):
        rows=super().enemies()
        for i,r in enumerate(rows):r.update(index=i,windup=self.e.read(self.sym['enemy_windups']+i*4),clock=self.e.read(self.sym['enemy_clocks']+i*4),serial=self.e.read(self.locals['enemy_serial']['address']+i*2,2),slow=self.e.read(self.sym['slowed_enemies']+i,1))
        return rows
    def row(self):return dict(frame=self.e.frame,game_frame=self.get('frame'),hero=[self.get('px'),self.get('py')],companion=[self.get('cx'),self.get('cy')],selected_id=self.selected().instance_id,selected_form=self.selected().form_id,command=self.command(),action=self.action(),power=self.power(),enemies=self.enemies(),shots=self.shots(),arrows=self.arrows(),hp_q4=self.hp_q4(),hitstop=self.get('hitstop'),state=self.get('game_state'),render_cycles=self.get('render_cycles'),obj_count=self.get('obj_count'),displayed_page=self.e.read(0x04000000,2)&16)
    def boot(self):
        self.step(150);self.tap('START',2,35);self.settle()
        self.check(self.get('room')==30 and self.collection()==ALL_FORMS and len(self.live())==21,'authenticated completed Southern collection cold-boots on candidate')
        self.check(all(self.quest(q)==3 for q in range(30)),'all30 controller-earned claims survive')
        self.check(sum(bool(r.item_id) for r in self.state().equipment.bag)==25,'all25 controller-earned gear items survive')
        for slot,item in ((0,1),(1,34),(3,65)):self.equip_item(slot,item)
        self.use('rest');self.ready();self.snapshot('candidate-town-source')
    def entry(self,target):
        if self.get('room')<30 and target<30:return NorthernJourney.entry(self,target)
        return super().entry(target)
    def prepare(self,cmd,goal=(320,123),direction=1,field=True):
        self.restore('candidate-town-source');self.owned_select(OWNERS[cmd]);self.set_command(cmd);self.ready()
        if field:self.entry(22);self.entry(23)
        self.goto(*goal);self.face(direction);self.ready()
        self.check(self.command()==cmd and self.selected().form_id==OWNERS[cmd],f'command{cmd} selected through actual party/Growth controls')
    def trace(self,count,keys=None):
        rows=[]
        for i in range(count):self.step(1,keys(i) if keys else 0);rows.append(self.row())
        return rows
    def cast(self,cmd,count=65,keys=None):
        before=self.row();self.step(1,'R');trace=[self.row()]+self.trace(count,keys)
        self.check(trace[0]['power']['kind']==cmd and trace[0]['power']['time']>0,f'command{cmd} starts native bounded effect')
        self.check(trace[0]['power']['caster_id']==before['selected_id'],'cast snapshots actual selected identity')
        self.check(trace[0]['power']['phase']==PHASES[cmd],'command uses authored five-phase index')
        self.check(all(r['power']['time']<=60 and len(r['power']['missiles'])==3 for r in trace),'effect lifetime and missile pool remain bounded')
        return before,trace
    def run_case(self,name,fn):
        print('BEGIN',name,flush=True)
        try:fn()
        except Exception as exc:
            traceback.print_exc();self.failures.append({'case':name,'error':str(exc),'status':self.status()});self.cases.append({'case':name,'passed':False,'error':str(exc)})
            self.snapshot(name+'-failure',settle=False)
        self.report()
    def record(self,cmd,before,trace,extra=None):
        row=dict(case='command-'+str(cmd),name=NAMES[cmd],command=cmd,owner=OWNERS[cmd],before=before,trace=trace,passed=True)
        row.update(extra or {});self.cases.append(row);self.accepted_commands.append(cmd);self.report()
    def direct(self,cmd):
        goal={23:(320,109),24:(336,112),25:(320,123),26:(320,123),27:(320,123),30:(320,123),37:(308,123),38:(296,108),41:(320,123),42:(320,123)}[cmd]
        self.prepare(cmd,goal);before,trace=self.cast(cmd);damage=before['enemies'][4]['hp_q4']-trace[-1]['enemies'][4]['hp_q4']
        base={23:16,24:24,25:20,26:20,27:16,30:24,37:12,38:24,41:20,42:24}[cmd]
        expected=base*5//4 if PHASES[cmd]==2 else base*7//8 if PHASES[cmd]==1 else base
        self.cases.append({'case':'direct-probe-'+str(cmd),'before':before,'trace':trace,'damage_q4':damage,'expected_q4':expected})
        self.check(damage==expected,f'{NAMES[cmd]} lands expected{expected}Q4 once on genuine Water ranger')
        hp=[before['enemies'][4]['hp_q4']]+[r['enemies'][4]['hp_q4'] for r in trace];self.check(sum(a!=b for a,b in zip(hp,hp[1:]))==1,'single-cast target ledger allows exactly one damage transition')
        if cmd==26:self.check(next(r['power']['age'] for r in trace if r['enemies'][4]['hp_q4']<hp[0])==30,'diversion crosscut waits30 active updates')
        if cmd==25:self.check(before['enemies'][4]['y']-trace[-1]['enemies'][4]['y']==6,'ordinary ranged enemy push is exactly6 swept pixels')
        if cmd==27:self.check(any(sum(m['life']>0 for m in r['power']['missiles'])==2 and all(m['stage']==1 for m in r['power']['missiles'][1:]) for r in trace),'one actual hit creates exactly two split children')
        if cmd==37:self.check(any(r['power']['missiles'][1]['life'] and r['power']['missiles'][2]['life'] for r in trace),'fork creates two swept branches after12pixels')
        if cmd==42:self.check(any(m['stage']==1 and m['life'] for r in trace for m in r['power']['missiles']),'fan visibly changes from outbound to bounded return')
        self.record(cmd,before,trace,{'damage_q4':damage,'expected_q4':expected})
    def guards(self,cmd):
        self.prepare(cmd,(232,256),3 if cmd==33 else 0)
        for _ in range(120):
            e=self.enemies()[0];dx=e['x']-self.get('px');dy=e['y']-self.get('py')
            if dx==12 and abs(dy)<=4 and not self.get('invuln'):break
            self.step(1)
        self.check(dx==12 and abs(dy)<=4,'ordinary Wood walker naturally approaches directional guard')
        before,trace=self.cast(cmd,48);guards=[r for r in trace if r['power']['guard_grace']]
        self.cases.append(dict(case='guard-probe-'+str(cmd),before=before,trace=trace))
        self.check(bool(guards) and guards[0]['power']['guard_enemy']==0,'eligible ordinary melee consumes directional guard')
        self.check(guards[0]['hp_q4']==before['hp_q4'],'guard stops its actual eligible contact attack')
        expected=24 if cmd in (31,32) else 30
        # Wood controls Earth, so Earth retaliation is reduced to75percent.
        expected=14 if cmd==31 else 21 if cmd==32 else 30
        self.check(before['enemies'][0]['hp_q4']-trace[-1]['enemies'][0]['hp_q4']==expected,'guard retaliation uses authored phase and once-only ledger')
        self.check(all(r['power']['guard_enemy']==0 for r in guards),'grace remains bound to one actual enemy identity')
        self.record(cmd,before,trace)
    def approach_command(self,cmd):
        self.prepare(cmd,(238,256),3);before,trace=self.cast(cmd,58)
        redirects=[r for r in trace if r['power']['redirect_left']]
        self.cases.append(dict(case='approach-probe-'+str(cmd),before=before,trace=trace))
        self.check(bool(redirects) and all(r['power']['redirected']==0 for r in redirects),'ordinary walker follows one bounded temporary approach target')
        self.check(max(r['power']['redirect_left'] for r in trace)<=12,'diverted approach has at most12 active updates')
        e=[before['enemies'][0]]+[r['enemies'][0] for r in trace]
        self.check(all(abs(a['x']-b['x'])+abs(a['y']-b['y'])<=1 for a,b in zip(e,e[1:])),'approach is ordinary movement with no teleport or push')
        expected=16 if cmd==36 else 0
        self.check(before['enemies'][0]['hp_q4']-trace[-1]['enemies'][0]['hp_q4']==expected,'lure damage matches distinct authored mechanic')
        self.record(cmd,before,trace)
    def crossing_line(self):
        self.prepare(34,(228,256),3);before,trace=self.cast(34,50)
        self.cases.append(dict(case='crossing-probe',before=before,trace=trace))
        changes=[r for r in trace if r['enemies'][0]['hp_q4']<before['enemies'][0]['hp_q4']]
        self.check(bool(changes),'walker physically crosses the placed line')
        self.check(before['enemies'][0]['hp_q4']-trace[-1]['enemies'][0]['hp_q4']==30,'crossing Metal line deals once-only125percent damage to Wood')
        self.record(34,before,trace)
    def interception(self):
        self.prepare(28,(320,146),1);incoming=None
        for _ in range(220):
            incoming=[s for s in self.shots() if s['life'] and s['owner'] and abs(s['x']-self.get('px'))<=6 and 40<=self.get('py')-s['y']<=48]
            if incoming:break
            self.step(1)
        self.check(bool(incoming),'real ranger shot approaches authored Water intercept plane')
        before,trace=self.cast(28,52);split=[r for r in trace if r['power']['spent']]
        self.cases.append(dict(case='intercept-probe',before=before,trace=trace,incoming=incoming))
        self.check(bool(split),'real ordinary hostile shot is intercepted once')
        self.check(any(all(m['life'] and m['harmless'] for m in r['power']['missiles'][:2]) for r in trace),'interception emits two bounded harmless spray pieces')
        self.check(all(not r['power']['missiles'][2]['life'] for r in trace),'interception never creates an unbounded third spray')
        self.record(28,before,trace)
    def weapon_echo(self,cmd,weapon,lethal=False):
        self.prepare(cmd,(312,84) if cmd==40 else (320,113),0 if cmd==40 else 1);self.equip_item(0,weapon);self.ready()
        if lethal:
            self.goto(272,66)
            for _ in range(20):
                if self.get('px')==272:break
                self.step(1,'LEFT+DOWN' if self.get('px')>272 else 'RIGHT+DOWN')
            self.check(self.get('px')==272,'lethal-source setup aligns real player with ranger without lateral knockback')
            self.face(1);damage=None
            for _ in range(6):
                hp=self.enemies()[2]['hp_q4']
                if damage is not None and hp<=damage:break
                for _ in range(16):
                    if self.get('py')-self.enemies()[2]['y']<=16:break
                    self.step(1,'UP')
                self.step(2,'A');self.step(38);after=self.enemies()[2]['hp_q4'];damage=hp-after
                self.check(damage>0 and after>0,'ordinary weapon prepares a living low-health echo source')
            self.goto(312,84);self.face(0)
        before=self.row();self.step(1,'R');trace=[self.row()]
        self.check(trace[0]['power']['mark_a']==4,'mark selects actual nearby ranger')
        if cmd==40:
            # Separate second R targets the nearby Earth ranger via real movement.
            self.step(32,'LEFT+UP');self.step(1,'UP');self.step(1);self.step(1,'R');trace.append(self.row())
            self.check(self.power()['mark_b']<6,'second aimed R selects another real target')
            self.check(self.power()['global_cooldown']<trace[0]['power']['global_cooldown'],'second target cannot refresh cooldown')
            self.step(5,'LEFT');self.step(1,'UP');self.step(1)
        for _ in range(2):
            trace+=self.trace(2,lambda _: 'A');trace+=self.trace(24)
        self.cases.append(dict(case=f'echo-probe-{cmd}-{weapon}',before=before,trace=trace))
        triggers=[r for r in trace if r['power']['spent'] and r['power']['delayed']]
        self.check(bool(triggers),'actual ordinary weapon hit triggers bounded delayed echo')
        self.check(any(r['hitstop'] or any(a['active'] for a in r['arrows']) or (weapon==17 and r['action']['class']==3 and r['action']['phase'] and r['enemies'][2 if cmd==40 else 4]['hp_q4']<before['enemies'][2 if cmd==40 else 4]['hp_q4']) for r in trace),'echo evidence contains actual melee hitstop or real bow action and confirmed target damage')
        if cmd==40:
            self.check(before['enemies'][4]['hp_q4']-trace[-1]['enemies'][4]['hp_q4']==21,'paired echo deals exactly one Fire21Q4 hit to surviving Water partner')
            if lethal:self.check(trace[-1]['enemies'][2]['hp_q4']==0,'lethal ordinary weapon source still triggers surviving partner echo')
        self.record(cmd,before,trace,{'weapon_item':weapon,'lethal_source':lethal})
    def rejected_marks(self):
        for cmd in (29,39,40):
            self.prepare(cmd,(240,224),1,False);before=self.row();tiles=self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64);self.step(1,'R');after=self.row()
            self.check(not after['power']['time'] and not after['power']['global_cooldown'],'no eligible target rejects mark before cooldown')
            self.check(tiles==self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64),'rejected target cannot acquire/upload shared effect tiles')
            self.cases.append(dict(case='no-target-'+str(cmd),before=before,after=after,passed=True))
    def ranged_delay(self):
        self.prepare(29);self.ready()
        for _ in range(240):
            e=self.enemies()[4]
            if 12<=e['windup']<=26:break
            self.step(1)
        self.check(12<=e['windup']<=26,'real kind2 ranger enters ordinary windup')
        before,trace=self.cast(29,32);first=trace[0]
        self.check(first['enemies'][4]['windup']==before['enemies'][4]['windup']+11,'R adds12 windup updates before one ordinary AI decrement')
        self.check(first['power']['spent']==1 and first['power']['delayed']==12,'one-shot windup extension schedules exactly12-update delayed strike')
        self.check(before['enemies'][4]['hp_q4']-trace[-1]['enemies'][4]['hp_q4']==14,'delayed Fire strike uses actual phase damage')
        self.record(29,before,trace)
    def gear_freeze(self):
        for cmd in (23,24,25,26,27,28,30,31,32,33,34,35,36,37,38,41,42):
            self.prepare(cmd,(240,224),1,False);self.step(1,'R');self.check(self.power()['time']>0,'effect starts for modal/gear test')
            self.gear_candidate(0,4);before=self.power();equipment=bytes(self.state().equipment);hp=self.hp_q4();self.tap('R',2,3);self.step(30)
            self.check(self.power()==before,'pause and refused gear equip freeze entire effect state')
            self.check(bytes(self.state().equipment)==equipment and self.hp_q4()==hp,'busy gear cannot mutate equipment or heal')
            self.close_menu();self.step(130);self.equip_item(0,4)
            self.check(not self.power()['time'] and not self.power()['tile_owner'],'expired effect releases transient shared lease')
            self.cases.append(dict(case='gear-freeze-'+str(cmd),paused=before,passed=True))
        self.coverage.append('native-gear-lock-release-and-pause')
    def side_reaim(self):
        self.prepare(32,(240,224),1,False);self.step(1,'R');self.step(8);before=self.row();self.step(1,'R');after=self.row()
        self.check(after['power']['guard_side']==1 and after['power']['side_changed']==1,'second R chooses opposite side')
        self.check(after['power']['startup_until']==after['power']['age']+6,'side change starts fresh6-update guard startup')
        self.check(after['power']['time']==before['power']['time']-1 and after['power']['global_cooldown']==before['power']['global_cooldown']-1,'side reaim refreshes neither lifetime nor cooldown')
        self.step(1);self.step(1,'R');last=self.row();self.check(last['power']['guard_side']==1 and last['power']['side_changed']==1,'third R cannot chain additional side swaps')
        self.cases.append(dict(case='command32-one-shot-R-reaim',before=before,after=after,last=last,passed=True))
    def selector_identity(self):
        self.prepare(23,(240,224),1,False);self.step(1,'R');self.step(1,'L');before=self.row();self.step(35,'L');frozen=self.row()
        self.check(before['power']==frozen['power'] and before['hp_q4']==frozen['hp_q4'],'held selector freezes effect/cooldown and health')
        target=next(i for i,j in enumerate(self.roster().party) if j<160 and self.roster().instances[j].instance_id!=before['selected_id'])
        self.step(1,'L+'+('UP','RIGHT','DOWN','LEFT')[target]);self.step(1);after=self.row()
        self.check(after['selected_id']!=before['selected_id'] and after['power']['caster_id']==before['selected_id'],'committed swap preserves cast identity')
        self.check(after['power']['global_cooldown']>0 and after['hp_q4']<=before['hp_q4'],'selector cannot heal or reset cooldown')
        self.step(1,'R');self.check(self.power()['caster_id']==before['selected_id'],'wrong selected instance cannot recast/steal live effect')
        self.cases.append(dict(case='selector-freeze-swapped-instance',before=before,frozen=frozen,after=after,passed=True))
    def phase_matchups(self):
        records=[]
        for cmd,target,goal,direction,expected in ((24,2,(288,64),1,30),(30,3,(388,176),3,30),(25,4,(320,123),1,25),(41,0,(250,256),3,25),(27,1,(172,176),2,20)):
            self.prepare(cmd,goal,direction);before,trace=self.cast(cmd);actual=before['enemies'][target]['hp_q4']-trace[-1]['enemies'][target]['hp_q4'];records.append(dict(command=cmd,target=target,before=before,trace=trace,actual_q4=actual,expected_q4=expected))
            self.cases.append(dict(case='phase-probe-'+str(cmd),record=records[-1]))
            self.check(actual==expected,'actual Southern command gains125percent in controlling phase matchup')
        self.cases.append(dict(case='five-native-controlling-phase-advantages',records=records,passed=True));self.coverage.append('all-five-native-phase-advantages')
    def blocked_geometry(self):
        def clear(mask,w,x,y,tx,ty):
            dx=abs(tx-x);dy=-abs(ty-y);sx=1 if x<tx else -1;sy=1 if y<ty else -1;err=dx+dy
            while True:
                if mask[y*w+x]:return False
                if (x,y)==(tx,ty):return True
                twice=err*2;nx,ny=x,y
                if twice>=dy:err+=dy;nx+=sx
                if twice<=dx:err+=dx;ny+=sy
                if nx!=x and ny!=y and (mask[y*w+nx] or mask[ny*w+x]):return False
                x,y=nx,ny
        for cmd in (24,26,28,31,32,34,35,36):
            self.prepare(cmd,(240,224),1,False);mask,w,h=self.mask();choices=[]
            for y in range(60,290,4):
                for x in range(20,460,4):
                    if not mask[y*w+x] and not mask[(y-3)*w+x] and (mask[y*w+x-12] if cmd in (31,32) else mask[(y-24)*w+x]):choices.append((abs(x-240)+abs(y-224),x,y))
            self.check(bool(choices),'compiled map provides an accessible wall-facing rejection probe')
            found=False
            for _,x,y in sorted(choices)[:30]:
                self.goto(x,y,radius=4);self.face(1);self.ready();px,py=self.get('px'),self.get('py');a,b=(px-12,py-24),(px+12,py-24)
                if cmd==24:a,b=(px-16,py-16),(px,py-40)
                if cmd==26:a,b=(px-12,py-16),(px+12,py-28)
                if cmd in (31,32):a=b=(px-12,py)
                if cmd in (35,36):a,b=(px-16,py-20),(px+16,py-20)
                if all(clear(mask,w,*s,*t) for s,t in (((px,py),a),(a,b),((px,py),b))):continue
                before=self.row();tiles=self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64);self.step(1,'R');after=self.row()
                self.check(not after['power']['time'] and not after['power']['global_cooldown'],'actual blocked geometry rejects cast before cooldown')
                self.check(tiles==self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64),'wall-rejected cast does not acquire shared OBJ tiles')
                self.cases.append(dict(case='blocked-native-'+str(cmd),before=before,after=after,endpoint_a=a,endpoint_b=b,passed=True));found=True;break
            self.check(found,'native wall rejection reached for command'+str(cmd))
        self.coverage.append('native-wall-LOS-corner-safe-cast-rejection')
    def shared_lease(self):
        self.prepare(24,(240,224),1,False);self.assign(0,26);self.assign(1,20);self.assign(2,14);self.assign(3,16);self.select_form(26);self.set_command(24);self.ready();self.snapshot('southern-lease-ready')
        for target,cmd,key in ((20,14,'northern'),(14,9,'regional'),(16,11,'regional')):
            self.restore('southern-lease-ready');self.step(1,'R');before=self.power();tiles=self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64);self.select_form(target);self.step(1,'R');after=self.power()
            self.check(after['caster_id']==before['caster_id'] and after['time']>0 and after['global_cooldown']>0,'old-companion swap cannot steal cast or refund cooldown')
            self.check(tiles==self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64),'old command cannot overwrite live Southern lease')
            self.ready();self.set_command(cmd);self.ready();self.step(1,'R')
            self.check(self.get(key+'_power_time')>0 and self.get(key+'_power_kind')==cmd,'legacy command runs after Southern lease is released')
            self.cases.append(dict(case='Southern-lease-to-'+str(cmd),before=before,after=after,passed=True))
        self.coverage.append('legacy-powers-after-Southern-shared-lease')
    def safe_bow(self):
        self.restore('candidate-town-source');self.equip_item(0,19);self.goto(240,224);self.face(3);self.step(50)
        self.check(self.action()['phase']==0 and not any(a['active'] for a in self.arrows()),'native bow cancellation starts cleanly')
    def bow_controls(self):
        from region_combat_tests import CombatReview
        self.results=self.cases;CombatReview.bow_cancel_case(self)
    def hitstop_freeze(self):
        self.prepare(30,(320,113),1);self.step(1,'R');self.step(2);self.step(1,'A');trace=self.trace(65)
        frozen=[(a,b) for a,b in zip(trace,trace[1:]) if a['hitstop']>0]
        self.cases.append(dict(case='native-Southern-hitstop-freeze',trace=trace,frozen_samples=len(frozen)))
        self.check(bool(frozen),'real sword impact creates hitstop during live Southern effect')
        self.check(all(a['power']==b['power'] for a,b in frozen),'actual hitstop freezes lifetime,age,cooldown and target ledger')
        self.cases[-1]['passed']=True
    def dialogue_freeze(self):
        self.prepare(24,(112,225),1,False);self.approach('rest');self.step(1,'R');self.step(1);self.step(1,'A')
        # Rest now validates through the bounded event/save scheduler. Observe
        # its actual terminal dialogue rather than assuming a fixed40 frames.
        pending=self.row();previous=pending;preparation=[]
        for _ in range(250):
            if self.get('game_state')==DIALOG:break
            self.check(self.get('game_state') in (EVENT_PENDING,SAVING),'rest preparation remains in an explicit bounded modal state')
            self.step(1);row=self.row()
            row['update_delta']=(row['game_frame']-previous['game_frame'])&0xffffffff
            row['page_flip']=row['displayed_page']!=previous['displayed_page'];preparation.append(row);previous=row
            self.check(row['power']==pending['power'] and row['enemies']==pending['enemies'],'rest preparation freezes the live effect and enemies')
            self.check(row['update_delta']==1 and row['page_flip'] and row['render_cycles']<280896,'rest preparation updates and presents every native hardware frame')
        self.check(self.get('game_state')==DIALOG,'real rest interaction opens dialogue during active effect')
        before=self.row();self.step(45,'R');after=self.row()
        self.check(before['power']==after['power'] and before['enemies']==after['enemies'],'dialogue freezes effect and enemy state despite held R')
        self.cases.append(dict(case='real-dialogue-effect-freeze',preparation=preparation,before=before,after=after,passed=True))
    def enemy_generation(self):
        self.prepare(24,(240,286),1);self.step(1,'R');before=self.row();self.step(24,'DOWN');self.settle();after=self.row()
        self.check(self.get('room')==22 and not after['power']['time'] and not after['power']['tile_owner'],'real room exit clears effect and shared lease')
        self.check(after['power']['global_cooldown']>0,'room exit retains live cooldown')
        self.entry(23);spawn=self.row()
        self.check(all(a['serial']!=b['serial'] for a,b in zip(before['enemies'],spawn['enemies'])),'actual pool slots receive fresh generation when room enemies respawn')
        self.check(spawn['power']['mark_a']==6 and spawn['power']['mark_b']==6 and not spawn['power']['time'],'old target cannot bind to newly spawned slot identity')
        self.cases.append(dict(case='native-new-enemy-slot-generation',before=before,after=after,respawn=spawn,passed=True))
    def field_feedback(self):
        self.restore('candidate-town-source');self.owned_select(80);self.set_command(27);self.ready();self.entry(31);self.entry(34);self.approach('receiver');self.ready();before=self.row();self.step(2,'R');after=self.row()
        self.check(after['power']['cast_time']>0 and after['power']['caster_id']==after['selected_id'],'field success renders feedback for actual selected instance')
        self.check(not after['power']['time'] and not after['power']['tile_owner'] and not any(m['life'] for m in after['power']['missiles']),'successful field feedback creates no combat lifetime, lease or missile')
        self.check(before['enemies']==after['enemies'],'field visual feedback cannot fabricate combat damage')
        self.cases.append(dict(case='field-feedback-is-render-only',before=before,after=after,passed=True))
    def friendly_projectile_rejection(self):
        self.prepare(28,(240,224),1,False);self.equip_item(0,19);self.ready();self.step(1,'R');self.step(24,'A');self.step(1);trace=self.trace(32)
        self.check(any(any(a['active'] for a in r['arrows']) for r in trace),'eligibility probe contains genuine player arrows')
        self.check(not any(r['power']['spent'] for r in trace),'ordinary player arrow cannot trigger hostile-projectile interception')
        self.cases.append(dict(case='Water-intercept-rejects-real-player-arrow',trace=trace,passed=True))
    def guard_wrong_facing(self):
        for cmd in (31,32,33):
            self.prepare(cmd,(232,256),2 if cmd==33 else 1)
            for _ in range(160):
                e=self.enemies()[0];dx=e['x']-self.get('px');dy=e['y']-self.get('py')
                if dx==12 and abs(dy)<=4 and not self.get('invuln'):break
                self.step(1)
            self.check(dx==12 and abs(dy)<=4,'wrong-facing guard has real approaching ordinary melee target')
            before,trace=self.cast(cmd,36)
            self.check(not any(r['power']['guard_grace'] for r in trace),'wrong-facing guard never blocks a real attack from the wrong side')
            self.check(trace[-1]['hp_q4']<before['hp_q4'],'wrong-side enemy contact damages player normally')
            self.cases.append(dict(case='wrong-facing-native-guard-'+str(cmd),before=before,trace=trace,passed=True))
    def aim_cadence(self):
        self.prepare(40,(312,84),0);previous=(self.get('frame'),self.e.read(0x04000000,2)&16);trace=[]
        for n in range(80):
            key='R' if n in (0,35) else 'LEFT+UP' if 1<=n<=32 else 'UP' if n==33 else 'A' if n==36 else 0
            self.step(1,key);row=self.row();row.update(keys=key,update_delta=(row['game_frame']-previous[0])&0xffffffff,page_flip=row['displayed_page']!=previous[1],action=self.action());trace.append(row);previous=(row['game_frame'],row['displayed_page'])
        r=dict(case='paired40-second-aim-single-frame-input-cadence',hardware_frames=len(trace),game_updates=sum(x['update_delta'] for x in trace),page_flips=sum(x['page_flip'] for x in trace),maximum_cycles=max(x['render_cycles'] for x in trace),trace=trace);self.frame_windows.append(r);self.report()
        self.check(trace[35]['power']['mark_a']==4 and trace[35]['power']['mark_b']==2,'cadence follows real long-link second-target selection')
        self.check(all(x['update_delta']==1 and x['page_flip'] for x in trace) and r['maximum_cycles']<280896,'paired40 including second-aim startup presents every hardware frame')
        self.check(trace[36]['action']['phase']!=0,'one-hardware-frame A immediately after second aim is sampled')
        self.cases.append(dict(case=r['case'],passed=True))
    def ricochet_wall(self):
        self.prepare(41,(240,224),1,False);mask,w,h=self.mask();choices=[]
        for y in range(60,290,4):
            for x in range(20,460,4):
                if mask[y*w+x]:continue
                distance=next((d for d in range(1,41) if mask[(y-d)*w+x]),41)
                if 14<=distance<=30:choices.append((abs(x-240)+abs(y-224),x,y))
        self.check(bool(choices),'compiled collision supplies a reachable real wall ricochet')
        for _,x,y in sorted(choices)[:30]:
            self.goto(x,y);self.face(1);self.ready();px,py=self.get('px'),self.get('py')
            distance=next((d for d in range(1,41) if mask[(py-d)*w+px]),41)
            if 10<=distance<=36:break
        before,trace=self.cast(41,50);missiles=[r['power']['missiles'][0] for r in trace]
        self.check(any(m['life'] and m['stage']==1 and m['dy']==1 for m in missiles),'real collision reverses outbound missile once')
        self.check(all(m['stage']<=1 for m in missiles),'native projectile never gains a second ricochet stage')
        active=[m for m in missiles if m['life']]
        self.check(all(not mask[m['y']*w+m['x']] for m in active),'all observed outbound and reflected missile pixels stay outside solid cells')
        self.check(not trace[-1]['power']['time'] and not trace[-1]['power']['missiles'][0]['life'],'real ricochet expires within the cast bound')
        self.cases.append(dict(case='real-wall-single-ricochet41',before=before,trace=trace,wall_distance=distance,passed=True))
    def same_enemy_grace(self):
        self.prepare(31,(272,190),0);route=[]
        for _ in range(400):
            if self.enemies()[0]['y']<=208:break
            self.step(1)
        route.append(self.row());self.goto(200,176)
        for _ in range(350):
            if self.enemies()[1]['x']>=180:break
            self.step(1)
        self.goto(220,176)
        for _ in range(200):
            if self.enemies()[1]['x']>=198:break
            self.step(1)
        route.append(self.row());self.goto(237,188);self.face(0)
        for _ in range(320):
            p=[self.get('px'),self.get('py')];a,b=self.enemies()[:2]
            if all(abs(e['x']-p[0])+abs(e['y']-p[1])<=1 for e in (a,b)):break
            self.step(1)
        self.check(all(abs(e['x']-p[0])+abs(e['y']-p[1])<=1 for e in (a,b)),'two ordinary enemies naturally converge without pool injection')
        for _ in range(100):
            if 4<=self.get('invuln')<=12:break
            self.step(1)
        self.step(18,'LEFT');self.step(2,'RIGHT');self.step(2)
        for _ in range(40):
            a,b=self.enemies()[:2];p=[self.get('px'),self.get('py')]
            if 11<=a['x']-p[0]<=12 and 11<=b['x']-p[0]<=13 and not self.get('invuln'):break
            self.step(1)
        self.step(1,'DOWN');route.append(self.row());before,trace=self.cast(31,42)
        self.cases.append(dict(case='two-natural-enemies-same-enemy-only-grace',route=route,before=before,trace=trace))
        blocked=[r for r in trace if r['power']['guard_grace']]
        self.check(bool(blocked),'directional guard consumes a real contact in the two-enemy crowd')
        guard=blocked[0]['power']['guard_enemy'];other=1-guard
        self.check(guard in (0,1) and blocked[0]['hp_q4']==before['hp_q4'],'first actual contact is blocked without health loss')
        self.check(any(r['hp_q4']<before['hp_q4'] and abs(r['enemies'][other]['x']-r['hero'][0])<11 and abs(r['enemies'][other]['y']-r['hero'][1])<11 for r in blocked),'different enemy damages player while first enemy grace remains active')
        self.check(all(r['power']['guard_enemy']==guard for r in blocked),'grace never changes enemy identity')
        self.cases[-1]['passed']=True
    def boss_no_retiming(self):
        report=Path(self.provenance['path']);self.check(digest(report)==self.provenance['report_sha256'],'pre-boss producer report remains authenticated')
        producer=json.loads(report.read_text());record=producer['snapshots']['03-machine-ready'];save=artifact(report,record['sram_path'],Path(record['sram_path']).name)
        self.check(digest(save)==record['sram_sha256'] and record['rom_sha256']==producer['rom_sha256'] and record['symbols_sha256']==producer['symbols_sha256'],'exact pre-boss SRAM is paired with authenticated producer ROM/symbols')
        bank=newest_bank(save.read_bytes());self.check(int.from_bytes(bank[12:14],'little')==6,'pre-boss source has CRC-valid current revision6 bank')
        self.notes.append(dict(case='boss-no-retiming',source_snapshot='03-machine-ready',source_sram=str(save),source_sram_sha256=digest(save),producer_report_sha256=digest(report),source_machine_state_loaded=False,scope='Cold import controller-earned pre-boss progress; base81 is acquired normally on this target'))
        self.e.load_save(save);self.e.reset();self.step(150);self.tap('START',2,35);self.settle();self.to_town();self.entry(31);self.entry(33);self.use('sun_shutter');self.recruit_field('encounter2',81);self.leave_interior(31);self.owned_select(81);self.set_command(29);self.ready();self.entry(34)
        for target in (35,36,37):self.entry(target)
        self.use('start');self.goto(88,112);self.face(1);self.snapshot('candidate-boss-retiming-ready',False);runs=[]
        for cast in (False,True):
            self.restore('candidate-boss-retiming-ready');trace=[]
            for n in range(260):
                self.step(1,'R' if cast and n%4==0 else 0);trace.append(dict(frame=self.e.frame,stage=self.get('south_game_machine_stage',1),ticks=self.get('south_game_machine_ticks',1),hp=self.get('south_game_machine_hp',1),power=self.power(),hero_hp=self.hp_q4()))
            runs.append(trace)
        self.cases.append(dict(case='native-boss-warning-not-retimed',baseline=runs[0],repeated_command29=runs[1]))
        self.check({r['stage'] for r in runs[0]}=={1,2,3,4},'real boss trace covers warning,attack,open and recovery stages')
        self.check([(r['stage'],r['ticks'],r['hp']) for r in runs[0]]==[(r['stage'],r['ticks'],r['hp']) for r in runs[1]],'repeated command29 cannot target or retime the actual boss')
        self.check(all(not r['power']['time'] and not r['power']['global_cooldown'] for r in runs[1]),'boss-only invalid target consumes no cooldown or combat lease')
        self.cases[-1]['passed']=True;self.restore('candidate-town-source')
    def run(self,only=None):
        self.boot();cases=[('command-'+str(c),lambda c=c:self.direct(c)) for c in (23,24,25,26,27,30,37,38,41,42)]
        cases += [('command-'+str(c),lambda c=c:self.guards(c)) for c in (31,32,33)]
        cases += [('command-'+str(c),lambda c=c:self.approach_command(c)) for c in (35,36)]
        cases += [('command-28',self.interception),('command-34',self.crossing_line)]
        cases += [('echo-'+str(c)+'-'+str(w),lambda c=c,w=w:self.weapon_echo(c,w)) for c in (39,40) for w in (1,9,17)]
        cases += [('lethal-echo-40-'+str(w),lambda w=w:self.weapon_echo(40,w,True)) for w in (1,9,17)]
        cases += [('command-29',self.ranged_delay),('rejected-marks',self.rejected_marks),('side-reaim',self.side_reaim),('selector-identity',self.selector_identity),('gear-freeze',self.gear_freeze),('phase-matchups',self.phase_matchups),('blocked-geometry',self.blocked_geometry),('shared-lease',self.shared_lease),('bow-controls',self.bow_controls),('hitstop-freeze',self.hitstop_freeze),('dialogue-freeze',self.dialogue_freeze),('enemy-generation',self.enemy_generation),('field-feedback',self.field_feedback),('friendly-projectile',self.friendly_projectile_rejection),('wrong-facing-guards',self.guard_wrong_facing),('aim-cadence',self.aim_cadence),('ricochet-wall',self.ricochet_wall),('same-enemy-grace',self.same_enemy_grace),('boss-no-retiming',self.boss_no_retiming)]
        selected=set(only.split(',')) if only else {n for n,_ in cases};assert selected<={n for n,_ in cases}
        for name,fn in cases:
            if name in selected:self.run_case(name,fn)
        self.check(self.collection()==ALL_FORMS and len(self.live())==21 and len({c.instance_id for c in self.live()})==21,'native combat/control suite preserves41 histories and21 unique retained instances')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','elf','output','source-report','source-manifest'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+key,required=True)
    p.add_argument('--case');a=p.parse_args();run=SouthernCombat(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_manifest,a.elf)
    try:run.run(a.case)
    finally:run.report();run.e.close()
    return bool(run.failures)
if __name__=='__main__':raise SystemExit(main())
