#!/usr/bin/env python3
"""Developer-only native Northern combat and gear acceptance.

Controller input is the only game mutation. A producer-authenticated complete
collection SRAM is cold-booted in the hash-pinned candidate; machine-state
branches are created locally and verified with matching SRAM and target hashes.
Read-only game symbols are observations, never fabricated ownership or setup.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct, traceback
from collections import Counter
from pathlib import Path
from northern_journey import NorthernJourney, ALL_FORMS, PLAY, PAUSE, digest, ROOT, R5_SHA, R5_ROM, newest_bank

SOURCE_SNAPSHOT='09-complete21-independent-reboot'
OWNERS={13:20,14:20,15:23,16:23,17:74,18:74,19:76,20:76,21:78,22:78}
NAMES={13:'Wood narrow pull',14:'Wood persistent span',15:'Fire delayed pocket',16:'Fire moving drawer',17:'Water straight push',18:'Water turning wake',19:'Earth delayed impact',20:'Earth intercept pulse',21:'Metal single turn',22:'Metal two-shot gate'}

# Cross-cartridge inputs require exact archived producer pins. Fresh reports are
# accepted only for the same ROM/symbols and current controller journey sources.
ARCHIVED_REPORTS={
    '6fc22f863fdad4843a66230788a08532163c758dc121b2e5b924ff01add0e490':('ebfbef970190904125f85eec194fed7dc6c145aea6e2934ba4133ee4df00ba95','76bd0fa03749108bdb69549f91717c966f70c654e7dee3f563508c9138fb5ee7'),
    '6a3f10034028ce06f190cab331896bad76388766a6f58424deb9bf8b62928bd3':('807d8b3e53f8709de05b2320e734b507b6705ca1e61deae4bde30825b5c056ac','bcd704d93725021e8f7e7f3b0d0c230c8e39679152339997a168b257137a44a7'),
}
ARCHIVED_SRAM={
    '09-complete21-independent-reboot':'f4e853c85445b8567263a1a875eba967e552e0dcae30958ca42f39bfec4e4479',
    '04-machine-ready':'6661d02624864cb7258abdfe435a16d16b588ae5feb482e7f6402876657b7694',
}

def validate_source_report(path,target_rom_sha,target_symbols_sha):
    """Authenticate lineage and actual SRAM bytes before starting an emulator.

    No foreign machine state is loaded. Hashes in an arbitrary foreign report
    do not confer trust: cross-ROM reports must match the explicit archive pins.
    Same-ROM reports must pass the current source/contract and R5 lineage gate.
    """
    path=Path(path).resolve();report_hash=digest(path);report=json.loads(path.read_text())
    assert report.get('suite')=='northern-native-controller-journey','Not a controller journey report'
    assert report.get('controller_only') is True and report.get('game_ram_writes')==0,'Source is not controller-only'
    assert report.get('failures')==[] and report.get('checks') and all(c.get('passed') is True for c in report['checks']),'Source journey did not pass'
    archived=report_hash in ARCHIVED_REPORTS
    if archived:
        assert (report['rom_sha256'],report['symbols_sha256'])==ARCHIVED_REPORTS[report_hash]
    else:
        assert (report['rom_sha256'],report['symbols_sha256'])==(target_rom_sha,target_symbols_sha),'Unpinned cross-ROM report'
        for filename in ('tests/northern_journey.py','tests/region_journey.py','tests/region_combat_tests.py','tools/mgba_runner.py'):
            assert report.get('test_sources',{}).get(filename)==digest(ROOT/filename),'Source journey script hash differs: '+filename
        assert report.get('content_contract_sha256')==digest(ROOT/'assets/northern_region/contract.json'),'Source contract differs'
        assert report.get('enabled_rows_are_not_acquisition_evidence') is True
        assert '11-north-death-retry' in report.get('snapshots',{}),'Source journey has not finished its lifecycle checks'
        for key,fallback,expected in (('rom_path','tested.gba',target_rom_sha),('symbols_path','tested.sym',target_symbols_sha)):
            artifact=Path(report[key]);artifact=artifact if artifact.is_absolute() else path.parent/artifact
            if not artifact.is_file():artifact=path.parent/fallback
            assert digest(artifact)==expected,'Source tested artifact bytes differ: '+key
        assert {19,22,73,75,77}<={a.get('form_id') for a in report.get('acquisitions',[])},'Missing native recruitment evidence'
    provenance=report.get('provenance',{})
    assert provenance.get('sram_sha256')==R5_SHA and provenance.get('source_rom_sha256')==R5_ROM and provenance.get('source_machine_state_loaded') is False,'Unverified R5 ancestor'
    fixture=Path(provenance['fixture_path'])
    if not fixture.is_file():fixture=ROOT/'tests/fixtures/v5-revision2/all-eleven-town.sav'
    assert digest(fixture)==R5_SHA,'Ancestor fixture bytes differ'
    ancestor=newest_bank(fixture.read_bytes());assert int.from_bytes(ancestor[12:14],'little')==2
    old_ids={int.from_bytes(ancestor[160+i*24+8:160+i*24+12],'little') for i in range(160) if ancestor[160+i*24+1]&1}
    # Archived evidence remains tied to the original revision3 cartridge. Only
    # a fresh, source-authenticated same-target journey follows today's header.
    content_revision=3
    if not archived:
        revision_match=re.search(r'\bSAVE5_CONTENT_REVISION\s*=\s*(\d+)\b',(ROOT/'src/save5.h').read_text())
        assert revision_match,'Missing current SAVE5 content revision'
        content_revision=int(revision_match.group(1))
    snapshots={}
    for name in (SOURCE_SNAPSHOT,'04-machine-ready'):
        record=report.get('snapshots',{}).get(name);assert record,'Missing authenticated source snapshot: '+name
        assert (record['rom_sha256'],record['symbols_sha256'])==(report['rom_sha256'],report['symbols_sha256']),'Snapshot target differs from journey'
        source=Path(record['sram_path']);source=source if source.is_absolute() else path.parent/source
        if not source.is_file():source=path.parent/Path(record['sram_path']).name
        assert digest(source)==record['sram_sha256'],'Snapshot SRAM bytes differ: '+name
        if archived:assert record['sram_sha256']==ARCHIVED_SRAM[name],'Archived snapshot is not pinned'
        bank=newest_bank(source.read_bytes());assert int.from_bytes(bank[12:14],'little')==content_revision,f'Expected CRC-valid Northern content revision{content_revision}'
        live=[(bank[160+i*24],int.from_bytes(bank[160+i*24+8:160+i*24+12],'little')) for i in range(160) if bank[160+i*24+1]&1]
        ids={identity for _,identity in live};assert 0 not in ids and len(ids)==len(live) and old_ids<=ids,'Source lost or duplicated real instance identities'
        obtained=[i+1 for i in range(128) if bank[112+(i>>3)]&(1<<(i&7))]
        quests=[(bank[4032+(i>>2)]>>((i&3)*2))&3 for i in range(22)]
        assert sorted(record['owned_form_ids'])==sorted(form for form,_ in live) and record['obtained_form_ids']==obtained and record['quests']==quests,'Snapshot metadata disagrees with CRC-valid SRAM'
        if name==SOURCE_SNAPSHOT:
            assert obtained==ALL_FORMS and len(live)==11 and quests==[3]*22,'Source is not the genuinely completed collection'
            assert sorted(form for form,_ in live)==[2,5,8,11,14,16,20,23,74,76,78]
        else:
            assert len(live)==8 and {19,77}<={form for form,_ in live} and quests[11]==quests[13]==3 and quests[21]==1,'Pre-machine source lacks its earned guaranteed recruits/route'
            assert int.from_bytes(bank[4032+16+21*2:4032+16+21*2+2],'little')==7,'Pre-machine route is not exactly ready'
        snapshots[name]={'path':source,'record':record,'bank_sha256':hashlib.sha256(bank).hexdigest()}
    return {'path':path,'report':report,'sha256':report_hash,'snapshots':snapshots,'trust':'pinned-archived-controller-report' if archived else 'same-target-current-controller-journey','ancestor_fixture':str(fixture),'ancestor_sha256':R5_SHA}

def northern_local_symbols(symbols,rom,elf=None):
    """Disambiguate file-static geometry using an independently ROM-paired ELF.

    Old Northern-only symbol files remain sufficient when names are unique.
    Later chapters may reuse private names; picking the last nm row silently
    observes another power system. Require STT_FILE scope in that case.
    """
    sizes={name:4 for name in ('ax','ay','bx','by','effect_x','effect_y','travel','pulse_age','tile_owner')}
    sizes.update(enemy_hits=1,redirect_count=1,turned_slots=2,friendly_slots=2,shot_serial=24)
    rows=[p for line in Path(symbols).read_text().splitlines() if len(p:=line.split())==3]
    counts=Counter(p[2] for p in rows)
    assert all(counts[name] for name in sizes),'Missing Northern observation symbol'
    if elf is None and not any(counts[name]>1 for name in sizes):return {},None
    elf=Path(elf) if elf is not None else Path(symbols).with_suffix('.elf')
    raw=elf.read_bytes();target=Path(rom).read_bytes()
    assert raw[:6]==b'\x7fELF\x01\x01','Expected little-endian ELF32 for scoped Northern symbols'
    header=struct.unpack_from('<16sHHIIIIIHHHHHH',raw)
    assert header[2]==40,'Scoped Northern symbols require ARM ELF'
    image=bytearray();covered=bytearray()
    for i in range(header[10]):
        kind,offset,virtual,physical,size,memsize,flags,align=struct.unpack_from('<IIIIIIII',raw,header[5]+i*header[9])
        if kind!=1 or not size:continue
        start=physical-0x08000000;end=start+size
        assert 0<=start<end<=len(target),'ELF load segment lies outside frozen ROM'
        if end>len(image):image.extend(bytes(end-len(image)));covered.extend(bytes(end-len(covered)))
        assert len(raw[offset:offset+size])==size,'Truncated ELF load segment'
        image[start:end]=raw[offset:offset+size];covered[start:end]=b'\1'*size
    assert len(image)==len(target) and all(covered) and image[0xc0:]==target[0xc0:],'Scoped-symbol ELF load image differs from frozen ROM beyond repaired192-byte header'
    sections=[struct.unpack_from('<IIIIIIIIII',raw,header[6]+i*header[11]) for i in range(header[12])]
    scoped={}
    for section in sections:
        if section[1]!=2:continue
        strings=sections[section[6]];strings=raw[strings[4]:strings[4]+strings[5]];current=None
        for pos in range(section[4],section[4]+section[5],section[9]):
            name,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,pos)
            name=strings[name:].split(b'\0',1)[0].decode()
            if info&15==4:current=name
            if current=='northern_powers.c' and info>>4==0 and info&15==1 and name in sizes:
                assert size==sizes[name] and name not in scoped,'Ambiguous Northern power local'
                assert any(p[2]==name and int(p[0],16)==value for p in rows),'Scoped Northern local missing from pinned symbols'
                scoped[name]=value
    assert set(scoped)==set(sizes),'Exact ELF lacks Northern power locals'
    pairing={'elf_path':str(elf.resolve()),'elf_sha256':digest(elf),'rom_sha256':digest(rom),
        'matched_bytes':len(target)-0xc0,'header_note':'Only first192bytes repaired by fix_header.py are excluded',
        'file_scope':'northern_powers.c','addresses':scoped,'sizes':sizes,
        'resolver_source':'tests/northern_combat_tests.py','resolver_source_sha256':digest(__file__)}
    return scoped,pairing

class NorthernCombat(NorthernJourney):
    def __init__(self,rom,symbols,output,rom_sha,symbols_sha,source_report,elf=None):
        self.ready_report=False
        self.harness_bytes=Path(__file__).read_bytes();self.harness_sha=hashlib.sha256(self.harness_bytes).hexdigest()
        self.source_evidence=validate_source_report(source_report,rom_sha,symbols_sha)
        super().__init__(rom,symbols,output,rom_sha,symbols_sha)
        self.northern_symbols,self.northern_symbol_pairing=northern_local_symbols(self.source_symbols,self.rom,elf)
        self.sym.update(self.northern_symbols)
        evidence=self.source_evidence;report=evidence['report'];source=evidence['snapshots'][SOURCE_SNAPSHOT]['path']
        self.provenance={'source_report':str(evidence['path']),'source_report_sha256':evidence['sha256'],
            'source_rom_sha256':report['rom_sha256'],'source_snapshot':SOURCE_SNAPSHOT,'sram_path':str(source),
            'sram_sha256':digest(source),'source_machine_state_loaded':False,'source_trust':evidence['trust'],
            'ancestor_fixture':evidence['ancestor_fixture'],'ancestor_sram_sha256':evidence['ancestor_sha256'],
            'scope':'Verified controller-earned21historical forms/11live instances,22claimed quests,19owned gear; SRAM-only cold import'}
        (self.out/'tested-harness.py').write_bytes(self.harness_bytes)
        self.e.load_save(source);self.e.reset();self.notes=[];self.ready_report=True;self.report()
    def report(self):
        if not getattr(self,'ready_report',False):return
        data={'suite':'northern-native-combat-controls','controller_only':True,'game_ram_writes':0,'player_facing':False,
            'provenance':self.provenance,**self.candidate,'test_source_sha256':self.harness_sha,'test_source_copy':str(self.out/'tested-harness.py'),
            'branch_policy':'This run creates and hash-checks only same-candidate state+SRAM pairs','phase_order':['Wood','Fire','Earth','Metal','Water'],'development_status':'Northern forms remain development content pending final acceptance','timing_caveat':'render_cycles excludes the final VBlank wait and OAM commit; acceptance also requires every hardware frame to update and flip',
            'northern_symbol_pairing':self.northern_symbol_pairing,
            'checks':self.checks,'failures':self.failures,'cases':self.cases,'coverage':self.coverage,
            'frame_windows':self.frame_windows,'snapshots':self.snapshots,'notes':self.notes,'inputs':self.inputs}
        (self.out/'northern-combat.json').write_text(json.dumps(data,indent=2)+'\n')
    def boot(self):
        self.step(150);self.tap('START',2,35);self.settle()
        self.check(self.get('room')==22 and self.collection()==ALL_FORMS and len(self.live())==11,'authenticated collection cold-boots on selected candidate')
        self.check(all(self.quest(q)==3 for q in range(22)),'22controller-earned quest claims survive SRAM import')
        self.check(sum(bool(r.item_id) for r in self.state().equipment.bag)==19,'all19genuinely earned gear items remain owned')
        self.snapshot('candidate-town-source')
    def power(self):
        names=['northern_power_kind','northern_power_time','northern_power_form','northern_power_age','northern_power_direction','northern_power_origin_x','northern_power_origin_y','northern_power_cooldown','northern_power_cast_time','ax','ay','bx','by','effect_x','effect_y','travel','pulse_age','tile_owner']
        p={n:self.get(n) for n in names};p.update(enemy_hits=self.get('enemy_hits',1),redirect_count=self.get('redirect_count',1),turned_slots=self.get('turned_slots',2),friendly_slots=self.get('friendly_slots',2),cooldown=self.get('ability_cd'))
        return p
    def shots(self):
        rows=super().shots()
        for i,r in enumerate(rows):r.update(index=i,effect=self.e.read(self.sym['shot_effects']+i,1),serial=self.e.read(self.sym['shot_serial']+i*2,2))
        return rows
    def arrows(self):
        rows=[]
        for i in range(2):
            b=self.e.bytes(self.sym['player_arrows']+i*20,20);x,y,remaining,speed,*v=struct.unpack('<iiHH8B',b)
            rows.append(dict(index=i,x=x/256,y=y/256,remaining_q8=remaining,speed_q8=speed,active=v[0],direction=v[1],damage_q4=v[2],attack_q4=v[3],stagger=v[4],element=v[5]))
        return rows
    def stats(self):
        hp,speed,diagonal,*v=struct.unpack('<HHH8B',self.e.bytes(self.sym['gear_stats'],14))
        return dict(max_hp=hp,speed_q8=speed,diagonal_q8=diagonal,**dict(zip(['attack','defense','roll_cooldown','power_cooldown','reach','stagger','weapon','phase'],v)))
    def row(self):
        return {'frame':self.e.frame,'game_frame':self.get('frame'),'hero':[self.get('px'),self.get('py')],'power':self.power(),'enemies':self.enemies(),'shots':self.shots(),'arrows':self.arrows(),'hp_q4':self.hp_q4(),'hitstop':self.get('hitstop'),'state':self.get('game_state')}
    def prepare(self,cmd,field=True,goal=None,direction=1):
        self.restore('candidate-town-source');self.owned_select(OWNERS[cmd]);self.set_command(cmd)
        self.ready()
        if field:self.entry(23)
        if goal:self.goto(*goal)
        self.face(direction);self.ready()
        self.check(self.command()==cmd and self.selected().form_id==OWNERS[cmd],f'actual command{cmd} selected via party and Growth menu')
        if field:self.check([e['phase'] for e in self.enemies()[:5]]==list(range(5)),'Northern five-phase field enemies have authoritative phase indices0..4')
    def run_case(self,name,fn):
        print('BEGIN',name,flush=True)
        try:fn()
        except Exception as exc:
            traceback.print_exc();self.failures.append({'case':name,'error':str(exc),'status':self.status()});self.cases.append({'case':name,'passed':False,'error':str(exc)})
            self.e.screenshot(self.out/(name+'-failure.png'));self.e.state(self.out/(name+'-failure.state'));(self.out/(name+'-failure.sav')).write_bytes(self.e.bytes(0x0e000000,32768))
        self.report()
    def damage_case(self,cmd):
        goal={13:(320,132),14:(320,123),15:(320,123),16:(320,138),17:(320,123),18:(296,123),19:(320,123)}[cmd]
        self.prepare(cmd,goal=goal);before=self.row();self.step(1,'R');trace=[self.row()]
        self.check(self.get('northern_power_kind')==cmd and self.get('northern_power_time')>0,NAMES[cmd]+': native combat cast starts')
        self.e.screenshot(self.out/f'command-{cmd}-cast.png')
        for _ in range(68):self.step(1);trace.append(self.row())
        after=self.enemies();damage=before['enemies'][4]['hp_q4']-after[4]['hp_q4'];expected={13:16,14:24,15:21,16:21,17:24,18:24,19:30}[cmd]
        result={'case':'command-'+str(cmd),'name':NAMES[cmd],'command':cmd,'owner':OWNERS[cmd],'before':before,'trace':trace,'damage_q4':damage,'expected_q4':expected}
        self.cases.append(result);self.report()
        self.check(damage==expected,f'{NAMES[cmd]} actual Water-ranger damage{damage}Q4 equals{expected}Q4')
        changes=[r for r in trace if r['enemies'][4]['hp_q4']<before['enemies'][4]['hp_q4']]
        first=changes[0]['power']['northern_power_age'];result['first_damage_age']=first
        if cmd in (15,19):self.check(first==18,'stationary marked impact waits exactly18active updates')
        if cmd==16:self.check(first==30 and any(r['power']['effect_y']!=trace[0]['power']['effect_y'] for r in trace),'moving heat travels before its update30burst')
        if cmd==18:self.check(first>24 and any(r['power']['travel']>24 and r['power']['effect_x']>r['power']['ax'] for r in trace),'wake reaches target only on visible second orthogonal segment')
        if cmd in (13,17):
            displacement=abs(before['enemies'][4]['x']-after[4]['x'])+abs(before['enemies'][4]['y']-after[4]['y']);result['displacement_px']=displacement
            self.check(displacement==(8 if cmd==13 else 10),'ordinary ranger displacement obeys exact swept-pixel budget')
        self.check(len(set(r['enemies'][4]['hp_q4'] for r in trace if r['enemies'][4]['hp_q4']<before['enemies'][4]['hp_q4']))==1,'one-hit ledger prevents repeated effect damage')
        result['passed']=True;self.coverage.append(result['case'])
    def blocked_geometry(self):
        for cmd in range(13,23):
            self.prepare(cmd,False,(247,270),3);before=self.power();tiles=self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64);self.step(1,'R');after=self.power()
            if cmd not in (13,17):
                self.check(after['northern_power_time']==0 and after['cooldown']==0,'blocked endpoint rejects command'+str(cmd)+' before cooldown/effect')
                self.check(tiles==self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64),'failed geometry never uploads shared OBJ lease')
            else:self.check(after['ax']<=252 and after['ax']>=after['northern_power_origin_x'],'straight cast clips at collision-safe endpoint')
            self.cases.append({'case':'blocked-endpoint-'+str(cmd),'before':before,'after':after,'passed':True})
        self.coverage.append('blocked-endpoints-all10')
    def interception(self):
        self.prepare(20,goal=(320,137));trace=[]
        # Actual Water ranger shoots toward us. Place its intercept20px ahead,
        # close enough to the ranger for the reaction pulse to reach it.
        for _ in range(260):
            if any(s['life'] and s['owner'] and abs(s['x']-self.get('px'))<=6 and 14<=self.get('py')-s['y']<=30 for s in self.shots()):break
            self.step(1)
        incoming=self.shots();before=self.enemies();self.step(1,'R');trace.append(self.row())
        for _ in range(55):self.step(1);trace.append(self.row())
        pulsed=[r for r in trace if r['power']['pulse_age']]
        damage=before[4]['hp_q4']-self.enemies()[4]['hp_q4']
        self.cases.append({'case':'command-20','incoming':incoming,'trace':trace,'damage_q4':damage})
        self.check(bool(pulsed),'Earth weight intercepts a genuine hostile projectile and starts pulse')
        self.check(damage==40,'interception emits exactly one40Q4Earth pulse into nearby Water ranger')
        self.check(len({r['power']['pulse_age'] for r in pulsed})==1,'one-shot interception records one pulse time')
        self.cases[-1]['passed']=True;self.coverage.append('command-20')
    def metal_case(self,cmd):
        self.prepare(cmd,goal=(320,146));attempts=[];success=None
        for attempt in range(7):
            self.ready()
            for _ in range(230):
                p=self.get('py');near=[s for s in self.shots() if s['life'] and s['owner'] and 18<=p-s['y']<=35 and abs(s['x']-self.get('px'))<=12]
                if near:break
                self.step(1)
            before=self.row();self.step(1,'R');trace=[self.row()]
            for _ in range(55):self.step(1);trace.append(self.row())
            count=max(r['power']['redirect_count'] for r in trace);attempts.append({'attempt':attempt,'before':before,'trace':trace,'redirect_count':count})
            if count==(1 if cmd==21 else 2):success=attempts[-1];break
            if self.get('game_state')!=PLAY:break
        self.cases.append({'case':'command-'+str(cmd),'attempts':attempts})
        self.check(success is not None,NAMES[cmd]+' redirects exact capacity from real hostile shots')
        turned=[]
        prev=success['before']['shots']
        for r in success['trace']:
            for s in r['shots']:
                p=prev[s['index']]
                if s['serial']==p['serial'] and p['owner'] and not s['owner']:
                    turned.append({'before':p,'after':s,'frame':r['frame']})
                    self.check((s['dx'],s['dy'])==(-p['dy'],p['dx']),'Metal reflection turns real velocity90degrees clockwise')
                    self.check(s['phase']==3 and s['effect']==0 and s['life']<=48,'reflected projectile is Metal phase, field-neutral, bounded lifetime')
            prev=r['shots']
        self.check(len(turned)==(1 if cmd==21 else 2),'each reflected projectile changes ownership once')
        for turn in turned:
            identity=turn['after'];later=[r['shots'][identity['index']] for r in success['trace'] if r['frame']>=turn['frame'] and r['shots'][identity['index']]['serial']==identity['serial'] and r['shots'][identity['index']]['life']>0]
            self.check(all((s['dx'],s['dy'],s['owner'],s['phase'],s['effect'])==(identity['dx'],identity['dy'],0,3,0) for s in later),'same live projectile preserves one turned velocity and never reacquires a field tag')
        self.cases[-1].update(passed=True,turns=turned);self.coverage.append('command-'+str(cmd))
    def gear_candidate(self,slot,item):
        self.open_tab(4)
        for _ in range(6):
            if self.get('gear_menu_slot')==slot:break
            self.tap('DOWN',2,3)
        for _ in range(52):
            r=self.get('gear_menu_candidate');candidate=self.state().equipment.bag[r].item_id if r<48 else (1 if slot==0 else 0)
            if candidate==item:break
            self.tap('RIGHT',2,3)
        self.check(candidate==item,f'gear-lock probe selects actual owned item{item}')
    def gear_locks_and_freeze(self):
        for cmd in range(13,23):
            self.prepare(cmd,False,(240,180),1);self.step(1,'R');self.gear_candidate(0,3)
            before=self.power();equipment=bytes(self.state().equipment);self.tap('R',2,3);self.step(30)
            after=self.power();self.check(bytes(self.state().equipment)==equipment,f'active command{cmd} refuses real-menu gear mutation')
            self.check(after==before,f'pause and denied equip freeze command{cmd} effect, ledger and cooldown')
            self.close_menu();self.step(130);self.equip_item(0,3)
            self.cases.append({'case':'active-effect-gear-lock-'+str(cmd),'before':before,'after':after,'passed':True})
        # After the first hit, neither pause nor picker can re-arm the ledger.
        self.prepare(14,goal=(320,123));self.step(1,'R');self.step(2);hp=self.enemies()[4]['hp_q4'];self.tap('START',1,3);pause=self.power();self.step(45)
        self.check(self.power()==pause,'pause preserves exact post-hit effect ledger')
        self.close_menu();self.step(1,'L');picker=self.power();self.step(45,'L')
        self.check(self.power()==picker,'held picker freezes active effect and cooldown')
        target_slot=next(i for i,index in enumerate(self.roster().party) if index<160 and self.roster().instances[index].form_id!=20)
        self.step(1,'L+'+('UP','RIGHT','DOWN','LEFT')[target_slot]);self.step(1);switched=self.selected().form_id;after_switch=self.power();self.step(1,'B');after_recall=self.power()
        self.check(switched!=20,'picker commits a genuinely different owned companion')
        self.check(after_switch['northern_power_form']==20 and after_recall['northern_power_form']==20,'party switch and recall never retarget the captured cast owner')
        self.check(0<after_recall['cooldown']<=pause['cooldown'],'switch/recall cannot erase or refund cooldown')
        self.step(80);self.check(self.enemies()[4]['hp_q4']==hp,'unfreezing and switching never deals second span hit')
        self.cases.append({'case':'pause-picker-switch-recall-ledger','paused':pause,'picker':picker,'after_switch':after_switch,'selected_form':switched,'after_recall':after_recall,'final_target_hp_q4':hp,'passed':True})
        # A real room crossing resets transient effects while keeping cooldown.
        self.prepare(14,goal=(240,286),direction=1);self.step(1,'R');before=self.power();self.check(before['northern_power_time']>0,'room-reset setup has actual live effect');self.step(24,'DOWN');self.settle();after=self.power()
        self.check(self.get('room')==22 and after['northern_power_time']==0 and after['tile_owner']==0,'room transition clears transient Northern effect and shared lease')
        self.check(after['cooldown']>0,'room transition cannot evade power cooldown')
        self.cases.append({'case':'room-reset','before':before,'after':after,'passed':True});self.coverage.extend(['all10-active-effect-gear-lock','modal-ledger-freeze','room-reset'])
    def shared_lease(self):
        self.restore('candidate-town-source');self.assign(0,20);self.assign(1,14);self.assign(2,16);self.select_form(20);self.set_command(14);self.goto(240,180);self.face(1);self.ready();self.snapshot('shared-lease-ready')
        for origin,target,cmd in ((20,14,14),(20,16,14),(14,20,9),(16,20,11)):
            self.restore('shared-lease-ready');self.select_form(origin);self.set_command(cmd);self.ready();self.step(1,'R')
            native=origin==20;key='northern_power_time' if native else 'regional_power_time';owner_key='northern_power_form' if native else 'regional_power_form'
            before={'kind':self.get('northern_power_kind' if native else 'regional_power_kind'),'owner':self.get(owner_key),'time':self.get(key),'cooldown':self.get('ability_cd'),'tile_owner':self.get('tile_owner')}
            tiles=self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64)
            self.select_form(target);self.step(1,'R');after={'owner':self.get(owner_key),'time':self.get(key),'cooldown':self.get('ability_cd'),'tile_owner':self.get('tile_owner')}
            self.check(after['owner']==origin and 0<after['time']<before['time'] and 0<after['cooldown']<=before['cooldown'],'switch and recast preserve original live effect and cooldown')
            self.check(after['tile_owner']==before['tile_owner'] and tiles==self.e.bytes(0x06014000+15616,256)+self.e.bytes(0x06014000+16192,64),'Water/drop and returning-pin tile lease cannot clobber live Northern effect or vice versa')
            self.cases.append({'case':f'shared-lease-{origin}-to-{target}','before':before,'after':after,'obj_bytes':320,'passed':True})
        self.coverage.append('native-shared-OBJ-lease-both-directions')
    def sidegrades(self):
        expected={3:(0,{'attack':2,'reach':3,'weapon':1}),11:(0,{'attack':2,'defense':1,'weapon':2}),19:(0,{'attack':1,'reach':12,'weapon':3}),35:(1,{'defense':1,'max_hp':100}),51:(2,{'speed_q8':324,'roll_cooldown':41}),83:(4,{'defense':1,'power_cooldown':73})}
        for item,(slot,fields) in expected.items():
            self.restore('candidate-town-source');before=self.stats();hp=self.hp_q4();self.equip_item(slot,item);after=self.stats()
            self.check(all(after[k]==v for k,v in fields.items()),f'sidegrade{item} real equip has exact authored bounded stats')
            self.check(self.hp_q4()==hp,f'sidegrade{item} grants no equip healing')
            self.cases.append({'case':'sidegrade-'+str(item),'slot':slot,'before':before,'after':after,'before_hp_q4':hp,'after_hp_q4':self.hp_q4(),'passed':True})
        self.restore('candidate-town-source');self.equip_item(1,35);self.act(104,208)
        self.check(self.hp_q4()==100,'legitimate rest fills new quarter-heart capacity')
        for _ in range(3):
            self.equip_item(1,0);self.check(self.hp_q4()==96,'unequip clamps quarter-heart to old maximum')
            self.equip_item(1,35);self.check(self.hp_q4()==96,'re-equip cannot heal the quarter-heart')
        self.cases.append({'case':'quarter-heart-no-heal-cycles','cycles':3,'final_hp_q4':self.hp_q4(),'passed':True});self.coverage.extend(['six-authored-sidegrade-stats','quarter-heart-no-equip-heal'])
    def bow_ranges(self):
        for item in (18,19):
            for charged in (False,True):
                self.restore('candidate-town-source');self.equip_item(0,item);self.goto(225,181);self.face(3);self.step(30);origin=[self.get('px'),self.get('py')]
                self.step(24 if charged else 1,'A');trace=[]
                for _ in range(65):self.step(1);trace.append({'frame':self.e.frame,'arrows':self.arrows(),'action':self.action()})
                live=[r for r in trace if r['arrows'][0]['active']];last=trace[-1]['arrows'][0];expected=(144 if charged else 112)+(12 if item==19 else 0)
                self.check(bool(live),'real bow button release spawns arrow')
                self.check(last['x']-origin[0]==expected and not last['remaining_q8'],f'Bow{item} '+('charged' if charged else 'quick')+f' travels exactly{expected}px')
                self.check(all(r['arrows'][0]['attack_q4']==(1 if item==19 else 4) and r['arrows'][0]['element']==255 and r['arrows'][0]['damage_q4']==(48 if charged else 32) for r in live),'arrow retains captured sidegrade attack, damage and neutral phase')
                self.cases.append({'case':f'bow-{item}-'+('charged' if charged else 'quick'),'origin':origin,'range_px':expected,'trace':trace,'passed':True})
        self.coverage.append('Bow19-156charged-124quick-versus-Bow18-144-112')
    def weapon_hits(self):
        for item,expected in ((3,34),(11,50),(19,49)):
            self.restore('candidate-town-source');self.equip_item(0,item);self.entry(23);self.goto(320,123 if item==3 else 135);self.face(1);self.step(3)
            before=self.enemies()[4]['hp_q4'];self.step(24 if item==19 else 1,'A');trace=[]
            for _ in range(65):self.step(1);trace.append({'frame':self.e.frame,'target':self.enemies()[4],'action':self.action(),'arrows':self.arrows()})
            damage=before-self.enemies()[4]['hp_q4'];self.check(damage==expected,f'sidegrade weapon{item} actual hit deals{expected}Q4')
            self.cases.append({'case':'weapon-native-hit-'+str(item),'damage_q4':damage,'trace':trace,'passed':True})
        self.coverage.append('three-weapon-sidegrades-native-q4-hits')
    def wrong_positions(self):
        for cmd in (13,14,15,16,17,18,19):
            self.prepare(cmd,goal=(285,138),direction=1);before=self.enemies();self.step(1,'R');p=self.power();self.step(68);after=self.enemies()
            self.check(p['northern_power_time']>0,'wrong-position test still creates actual command'+str(cmd))
            self.check([e['hp_q4'] for e in before]==[e['hp_q4'] for e in after],f'command{cmd} cannot damage targets outside its actual geometry')
            self.cases.append({'case':'wrong-position-'+str(cmd),'power':p,'before':before,'after':after,'passed':True})
        self.coverage.append('seven-damage-commands-wrong-position')
    def metal_late_lock_and_reuse(self):
        self.prepare(21,goal=(320,146));before=None;turned=None
        for _ in range(250):
            if any(s['life'] and s['owner'] and 18<=self.get('py')-s['y']<=35 and abs(s['x']-self.get('px'))<=12 for s in self.shots()):break
            self.step(1)
        before=self.row();self.step(1,'R');trace=[]
        for _ in range(55):
            row=self.row();trace.append(row)
            live=[s for s in row['shots'] if s['life'] and not s['owner'] and s['phase']==3 and s['effect']==0]
            if not row['power']['northern_power_time'] and live:turned=live[0];break
            self.step(1)
        self.check(turned is not None,'actual reflected projectile outlives single-turn effect')
        self.gear_candidate(0,3);equipment=bytes(self.state().equipment);cd=self.get('ability_cd');self.tap('R',2,3)
        self.check(bytes(self.state().equipment)==equipment and self.get('ability_cd')==cd,'reflected-shot-only window refuses equipment without cooldown reset')
        self.e.screenshot(self.out/'reflected-shot-only-equipment-lock.png');self.close_menu()
        reused=None
        for _ in range(250):
            self.step(1);s=self.shots()[turned['index']]
            if s['serial']!=turned['serial'] and s['life']:
                reused={'shot':s,'turned_slots':self.get('turned_slots',2),'friendly_slots':self.get('friendly_slots',2)};break
        self.check(reused is not None,'same projectile pool slot is naturally reused by a later hostile shot')
        self.check(reused['shot']['owner']==1 and not reused['turned_slots']&(1<<turned['index']) and not reused['friendly_slots']&(1<<turned['index']),'reused slot clears cast/reflection ledger and stays hostile')
        self.cases.append({'case':'reflected-shot-lock-and-natural-slot-reuse','before':before,'trace':trace,'reflected':turned,'reused':reused,'passed':True});self.coverage.append('reflected-shot-only-gear-lock-natural-slot-reuse')
    def hitstop_and_cooldown(self):
        self.prepare(14,goal=(320,123));before=self.enemies()[4]['hp_q4'];self.step(1,'R');self.step(18);self.step(1,'A');trace=[]
        for _ in range(70):self.step(1);trace.append(self.row())
        frozen=[(a,b) for a,b in zip(trace,trace[1:]) if a['hitstop']>0]
        self.check(bool(frozen),'real weapon hit causes native hit-stop during active span')
        self.check(all(a['power']==b['power'] for a,b in frozen),'hit-stop freezes effect age, lifetime, cooldown and one-hit ledger')
        damage=before-self.enemies()[4]['hp_q4'];self.check(damage==56,'single span24Q4 plus one mundane sword32Q4 remains56through hit-stop')
        self.cases.append({'case':'one-hit-ledger-through-weapon-hitstop','damage_q4':damage,'frozen_samples':len(frozen),'trace':trace,'passed':True})
        self.prepare(14,False,(240,180),1);self.step(1,'R');self.step(61);self.check(not self.get('northern_power_time') and self.get('ability_cd')>0,'cooldown remains after live effect expires')
        self.gear_candidate(4,83);before=self.get('ability_cd');captured=self.get('northern_power_cooldown');self.tap('R',2,2)
        self.check(self.get('ability_cd')==before and self.get('northern_power_cooldown')==captured==120,'equipping cooldown ring cannot rewrite or refund current cast cooldown')
        self.settle();self.close_menu();self.ready();self.step(1,'R');self.check(self.get('northern_power_cooldown')==118,'new cast legitimately captures Bearing Ring two-update cooldown sidegrade')
        self.cases.append({'case':'captured-cooldown-ring-no-evasion','old_cast':captured,'remaining_at_equip':before,'new_cast':118,'passed':True});self.coverage.extend(['native-hitstop-one-hit-ledger','captured-cooldown-no-gear-evasion'])
    def capture_raw(self,name):
        state=self.out/(name+'.state');save=self.out/(name+'.sav');shot=self.out/(name+'.png')
        self.e.state(state);save.write_bytes(self.e.bytes(0x0e000000,32768));self.e.screenshot(shot)
        self.snapshots[name]={'rom_sha256':self.target_sha,'symbols_sha256':self.symbol_sha,'state_path':str(state),'state_sha256':digest(state),'sram_path':str(save),'sram_sha256':digest(save),'screenshot':str(shot),'status':self.status(),'note':'Exact native instant; no settling or machine advancement for capture'}
        self.report()
    def cadence_sample(self,previous):
        frame=self.get('frame');page=self.e.read(0x04000000,2)&16;cx,cy=self.get('camera_x'),self.get('camera_y');enemies=self.enemies();shots=self.shots()
        visible=lambda x,y:cx-8<x<cx+248 and cy-8<y<cy+168
        state=self.get('game_state');picker=self.get('quickparty_open')
        def world_visible(x,y):
            if not visible(x,y) or state in (3,4,7,8):return False
            sx,sy=x-8-cx,y-8-cy
            if picker and sx+16>26 and sx<214 and sy+16>29 and sy<160:return False
            if state==2 and sy+16>99:return False
            if state==6 and sx+16>37 and sx<203 and sy+16>77 and sy<111:return False
            return True
        row={'hardware_frame':self.e.frame,'game_frame':frame,'update_delta':(frame-previous[0])&0xffffffff,'page_flip':page!=previous[1],
            'cycles':self.get('render_cycles'),'camera':[cx,cy],'obj_count':self.get('obj_count'),'game_state':self.get('game_state'),'journal_tab':self.get('journal_tab'),
            'live_enemies':sum(e['hp']>0 for e in enemies),'enemy_sprites_in_viewport':sum(e['hp']>0 and visible(e['x'],e['y']) for e in enemies),
            'visible_enemy_bodies':sum(e['hp']>0 and world_visible(e['x'],e['y']) and (not e['flash'] or bool(frame&2)) for e in enemies),
            'live_hostile_shots':sum(bool(s['life'] and s['owner']) for s in shots),
            'visible_hostile_shots':sum(bool(s['life'] and s['owner'] and world_visible(s['x'],s['y'])) for s in shots),
            'player_arrows':sum(a['active'] for a in self.arrows()),'northern_effect':self.get('northern_power_time'),
            'hp_q4':self.hp_q4(),'summoned':self.get('summoned')}
        return row,(frame,page)
    def performance(self,gather=False):
        self.restore('candidate-town-source');self.equip_item(0,19);self.equip_item(1,34 if gather else 35)
        if gather:self.equip_item(3,65)
        self.owned_select(20 if gather else 74);self.set_command(14 if gather else 18);self.act(104,208);self.entry(23)
        gather_route=[]
        if gather:
            self.goto(272,190);gather_route.append(self.row())
            for _ in range(360):
                if self.enemies()[0]['y']<=205:break
                self.step(1)
            gather_route.append(self.row());self.goto(200,176)
            for _ in range(300):
                if self.enemies()[1]['x']>=178:break
                self.step(1)
            gather_route.append(self.row());self.goto(312,124);gather_route.append(self.row())
            self.check(self.get('game_state')==PLAY,'native pursuit gathers crowd without death or enemy injection')
        else:self.goto(304,176)
        self.ready();self.face(2)
        self.capture_raw('gathered-native-ready' if gather else 'combined-native-ready')
        previous=(self.get('frame'),self.e.read(0x04000000,2)&16);trace=[];captures=[]
        for n in range(420):
            phase=n%90;key='A' if phase<24 or phase==48 else 'R' if phase==53 else 'LEFT' if 57<=phase<62 else 'RIGHT' if 67<=phase<72 else 0
            self.step(1,key);row,previous=self.cadence_sample(previous);row['keys']=key;trace.append(row)
            if row['player_arrows']==2 and row['northern_effect']>0 and row['visible_hostile_shots']>0 and row['visible_enemy_bodies']>=(4 if gather else 2) and len(captures)<3:
                path=self.out/(('combat-gathered-' if gather else 'combat-combined-')+str(len(captures))+'.png');self.e.screenshot(path);captures.append({'path':str(path),**row})
            if self.get('game_state')!=PLAY:break
        result={'case':'native-gathered-combat-cadence' if gather else 'native-combined-combat-cadence','ability':14 if gather else 18,'gather_route':gather_route,'hardware_frames':len(trace),'updates':sum(r['update_delta'] for r in trace),'page_flips':sum(r['page_flip'] for r in trace),
            'maximum_cycles':max(r['cycles'] for r in trace),'maximum_oam':max(r['obj_count'] for r in trace),'maximum_live_enemies':max(r['live_enemies'] for r in trace),
            'maximum_visible_enemy_bodies':max(r['visible_enemy_bodies'] for r in trace),'maximum_live_hostile_shots':max(r['live_hostile_shots'] for r in trace),'maximum_visible_hostile_shots':max(r['visible_hostile_shots'] for r in trace),
            'two_arrow_new_effect_visible_hostile_multiple_enemy_frames':sum(r['player_arrows']==2 and r['northern_effect']>0 and r['visible_hostile_shots']>0 and r['visible_enemy_bodies']>=(4 if gather else 2) for r in trace),
            'camera_parities':sorted({(r['camera'][0]%4,r['camera'][1]%2) for r in trace}),'captures':captures,'trace':trace,'frame_budget_cycles':280896,'timing_source':'actual emulated GBA hardware frames, global update counter and displayed Mode4 page flip; never hostFPS'}
        self.frame_windows.append(result);self.report()
        self.check(bool(captures),'one native representative window has two arrows, new effect, visible hostile shot and multiple visible enemy bodies')
        self.check(all(r['update_delta']==1 and r['page_flip'] for r in trace) and result['maximum_cycles']<280896,'combined native combat presents once per hardware frame within cycle budget')
        self.check(result['maximum_oam']<=128,'combined native OAM remains within128slots');self.coverage.append('representative-visible-native-combat-cadence')
    def cold_menu_save(self):
        for name,schedule,count in [('cold-journal-seven-tabs',{0:'START',5:'A',10:'A',15:'A',20:'A',25:'A',30:'A',55:'B'},80),('cold-rest-save',{0:'A',40:'A',80:'A',120:'A'},150),('cold-field-journal',{0:'START',5:'A',10:'A',15:'A',20:'A',25:'A',30:'A',55:'B'},80)]:
            self.restore('candidate-town-source')
            if name=='cold-field-journal':self.entry(23);self.goto(304,176);self.ready()
            previous=(self.get('frame'),self.e.read(0x04000000,2)&16);trace=[]
            for n in range(count):self.step(1,schedule.get(n,0));row,previous=self.cadence_sample(previous);trace.append(row)
            result={'case':name,'hardware_frames':count,'updates':sum(r['update_delta'] for r in trace),'page_flips':sum(r['page_flip'] for r in trace),'maximum_cycles':max(r['cycles'] for r in trace),'trace':trace,'frame_budget_cycles':280896}
            self.frame_windows.append(result);self.report()
            self.check(all(r['update_delta']==1 and r['page_flip'] for r in trace) and result['maximum_cycles']<280896,name+' presents once per hardware frame within cycle budget')
        self.coverage.append('cold-journal-save-native-cadence')
    def interception_capacity_and_wrong_facing(self):
        self.prepare(20,goal=(320,146));self.ready()
        for _ in range(250):
            if any(s['life'] and s['owner'] and 18<=self.get('py')-s['y']<=35 and abs(s['x']-self.get('px'))<=12 for s in self.shots()):break
            self.step(1)
        self.step(1,'R');trace=[self.row()]
        for _ in range(52):self.step(1);trace.append(self.row())
        pulse_ages={r['power']['pulse_age'] for r in trace if r['power']['pulse_age']};second=[]
        for a,b in zip(trace,trace[1:]):
            p=a['power']
            if not p['pulse_age'] or not p['northern_power_time']:continue
            for s in a['shots']:
                if s['life'] and s['owner'] and abs(s['x']-p['ax'])+abs(s['y']-p['ay'])<=10:
                    following=b['shots'][s['index']]
                    if following['life'] and following['owner'] and following['serial']==s['serial']:second.append({'before':s,'after':following,'frame':a['frame']})
        self.cases.append({'case':'Earth-one-shot-intercept-capacity','trace':trace,'second_shot_crossings':second})
        self.check(len(pulse_ages)==1,'Earth weight fires only one pulse across two naturally incoming projectile trajectories')
        self.check(bool(second),'a second hostile projectile crosses spent weight without interception')
        self.check(min(r['hp_q4'] for r in trace)<trace[0]['hp_q4'],'spent Earth weight grants no player invulnerability against that follow-on shot')
        self.cases[-1]['passed']=True
        for cmd in (21,22):
            self.prepare(cmd,goal=(320,146),direction=0);before=self.row();self.step(1,'R');trace=[]
            for _ in range(52):self.step(1);trace.append(self.row())
            self.check(any(s['life'] and s['owner'] for r in trace for s in r['shots']),'wrong-facing Metal case contains real incoming hostile projectiles')
            self.check(max(r['power']['redirect_count'] for r in trace)==0,'wrong-facing Metal gate never rotates a projectile from behind')
            self.cases.append({'case':'wrong-facing-'+str(cmd),'before':before,'trace':trace,'passed':True})
        self.coverage.append('Earth-one-projectile-capacity-Metal-wrong-facing')
    def fractional_native_hit(self):
        self.restore('candidate-town-source');self.equip_item(1,35);self.act(104,208);self.entry(23);self.goto(272,260)
        before=self.hp_q4()
        for _ in range(180):
            if self.hp_q4()<before:break
            self.step(1)
        damaged=self.hp_q4();self.check(before-damaged==15,'Sailcloth defense1 reduces real enemy contact16Q4 to15Q4')
        self.check(damaged%16!=0,'native quarter-heart capacity and damage retain fractional q4 health')
        self.open_tab(4);trace=[]
        for _ in range(20):self.tap('RIGHT',2,3);trace.append(self.hp_q4())
        self.check(all(hp==damaged for hp in trace),'gear previews preserve exact damaged fractional health')
        self.cases.append({'case':'fractional-real-enemy-hit-and-preview','before_q4':before,'after_q4':damaged,'delta_q4':15,'preview_samples':trace,'passed':True});self.coverage.append('fractional-q4-hit-preview')
    def moving_away(self):
        for cmd,goal,damage in ((14,(320,123),24),(16,(320,138),21),(19,(320,123),30)):
            self.prepare(cmd,goal=goal);hp=self.enemies()[4]['hp_q4'];self.step(1,'R');before=self.power();trace=[]
            for i in range(68):self.step(1,'DOWN' if i<18 else 0);trace.append(self.row())
            self.check(all(r['power']['northern_power_origin_x']==before['northern_power_origin_x'] and r['power']['northern_power_origin_y']==before['northern_power_origin_y'] for r in trace),'moving caster does not drag captured effect origin')
            self.check(hp-self.enemies()[4]['hp_q4']==damage,'moving away preserves authored placement and one-hit damage')
            self.cases.append({'case':'moving-away-'+str(cmd),'before':before,'trace':trace,'damage_q4':damage,'passed':True})
        self.coverage.append('cast-origin-immutable-while-moving')
    def safe_bow(self):
        self.restore('candidate-town-source');self.equip_item(0,19);self.goto(225,181);self.face(3);self.step(50)
        self.check(self.action()['phase']==0 and not any(a['active'] for a in self.arrows()),'clean new-bow controller setup avoids interaction handles')
    def bow_controls(self):
        from region_combat_tests import CombatReview
        self.results=self.cases
        CombatReview.bow_cancel_case(self)
    def span_late_entry(self):
        self.prepare(14,goal=(230,256),direction=3)
        # Move away from the naturally approaching Wood slime until it starts
        # just outside the span's collision band. No enemy location is edited.
        for _ in range(45):
            e=self.enemies()[0];distance=e['x']-self.get('px')
            if 33<=distance<=39:break
            self.step(1,'LEFT' if distance<33 else 'RIGHT')
        self.face(3);before=self.row();self.step(1,'R');trace=[self.row()]
        for _ in range(66):self.step(1);trace.append(self.row())
        hits=[r for r in trace if r['enemies'][0]['hp_q4']<before['enemies'][0]['hp_q4']]
        self.cases.append({'case':'Wood-span-late-enemy-crossing','before':before,'trace':trace})
        self.check(bool(hits) and hits[0]['power']['northern_power_age']>1,'persistent Wood span damages a real enemy entering after placement')
        self.check(before['enemies'][0]['hp_q4']-self.enemies()[0]['hp_q4']==24,'late crossing receives only one24Q4span hit')
        self.cases[-1].update(passed=True,first_damage_age=hits[0]['power']['northern_power_age']);self.coverage.append('Wood-span-persistent-late-crossing')
    def sidegrade_behavior(self):
        motion=[]
        for boots in (0,51):
            self.restore('candidate-town-source')
            if boots:self.equip_item(2,boots)
            self.goto(225,181);self.face(3);before=self.get('px_q8');self.step(12,'RIGHT');delta=self.get('px_q8')-before;self.step(1,'SELECT');cooldown=self.get('roll_cd')
            self.check(delta==12*(324 if boots else 320),'Deck Boots changes actual twelve-update walking distance by authored4Q8')
            self.check(cooldown==(41 if boots else 42),'Deck Boots changes actual dodge cooldown by exactly one update')
            motion.append({'boots':boots,'updates':12,'walking_delta_q8':delta,'actual_roll_cooldown':cooldown})
        reaches=[]
        for item in (2,3):
            self.restore('candidate-town-source');self.equip_item(0,item);self.entry(23);self.goto(320,132);self.face(1);hp=self.enemies()[4]['hp_q4'];self.step(1,'A');start={'hero':[self.get('px'),self.get('py')],'target':self.enemies()[4],'captured_reach':self.e.read(self.sym['weapon_action']+14,1)};self.step(24)
            damage=hp-self.enemies()[4]['hp_q4'];self.check(damage==(34 if item==3 else 0),'Ropeguard reach lands genuine longer-distance hit where shorter Reedguard misses')
            reaches.append({'item':item,'start':start,'damage_q4':damage})
        self.cases.append({'case':'native-sidegrade-movement-roll-reach','motion':motion,'reaches':reaches,'passed':True});self.coverage.append('native-DeckBoots-movement-roll-Ropeguard-reach')
    def control_phase_matchups(self):
        records=[]
        for cmd,target,goal,direction,expected in ((13,2,(272,78),1,20),(15,3,(388,176),3,30),(17,1,(172,176),2,30),(19,4,(320,123),1,30)):
            self.prepare(cmd,goal=goal,direction=direction);before=self.row();self.step(1,'R');trace=[]
            for _ in range(65):self.step(1);trace.append(self.row())
            damage=before['enemies'][target]['hp_q4']-self.enemies()[target]['hp_q4'];records.append({'command':cmd,'target_index':target,'phase':before['enemies'][target]['phase'],'damage_q4':damage,'expected_q4':expected,'before':before,'trace':trace})
            self.check(damage==expected,'actual Northern controlling matchup deals authored125percent q4 damage')
        self.cases.append({'case':'four-direct-controlling-phase-matchups','matchups':records,'passed':True})
        # Herd the Wood foe along a real pursuit route so the 90-degree Metal
        # redirect has a genuine sideways target, rather than injecting one.
        self.restore('candidate-town-source');self.equip_item(1,34);self.equip_item(3,65);self.owned_select(78);self.set_command(21);self.act(104,208);self.ready();self.entry(23);self.goto(272,190)
        for _ in range(360):
            if self.enemies()[0]['y']<=198:break
            self.step(1)
        self.goto(320,191);self.goto(320,224);self.face(1);self.ready();self.capture_raw('metal-sideways-target-ready');before=self.row();incoming=None
        for _ in range(260):
            target=self.enemies()[0]
            candidates=[s for s in self.shots() if s['life'] and s['owner'] and abs(s['x']-self.get('px'))<=8 and abs(s['y']-target['y'])<=12 and 10<=self.get('py')-s['y']<=37]
            if candidates:incoming=candidates;break
            self.step(1)
        self.check(incoming is not None,'real ranger projectile aligns with normally herded sideways Wood target')
        hp=self.enemies()[0]['hp_q4'];self.step(1,'R');trace=[]
        for _ in range(60):self.step(1);trace.append(self.row())
        damage=hp-self.enemies()[0]['hp_q4'];self.cases.append({'case':'Metal-reflected-controls-Wood','before':before,'incoming':incoming,'trace':trace,'damage_q4':damage})
        self.check(damage==40,'new Metal90-degree reflected projectile actually hits Wood for40Q4')
        self.cases[-1]['passed']=True;self.coverage.append('all-five-control-matchups-native-Northern-targets')
    def boss_weapon_inputs(self):
        evidence=self.source_evidence;report=evidence['report'];source=evidence['snapshots']['04-machine-ready']['path']
        # Recheck the immutable producer bytes immediately before the second
        # cold SRAM import; never consume a source machine state.
        assert digest(evidence['path'])==evidence['sha256']
        assert digest(source)==evidence['snapshots']['04-machine-ready']['record']['sram_sha256']
        self.notes.append({'case':'boss-weapon-inputs','source_report':str(evidence['path']),'source_report_sha256':evidence['sha256'],'source_rom_sha256':report['rom_sha256'],'source_snapshot':'04-machine-ready','source_sram':str(source),'source_sram_sha256':digest(source),'source_machine_state_loaded':False,'scope':'Controller-earned base recruits and three linked solved rooms, before machine encounter; SRAM-only cold load'})
        self.e.load_save(source);self.e.reset();self.step(150);self.tap('START',2,35);self.settle()
        self.check(self.get('room')==29 and self.get('north_game_machine_stage',1)==0,'genuinely earned pre-machine SRAM cold-boots in unstarted encounter')
        self.capture_raw('candidate-machine-ready')
        for cls in (1,2,3):
            self.restore('candidate-machine-ready');self.equip_item(0,{1:1,2:9,3:17}[cls]);self.cast_owned(19,64,124);self.cast_owned(77,176,124);self.act(120,124)
            for _ in range(140):
                if self.get('north_game_machine_stage',1)==3:break
                self.step(1)
            self.goto(120,100);self.face(1);before=self.get('north_game_machine_hp',1);position=[self.get('px'),self.get('py')]
            self.check(abs(position[0]-120)+abs(position[1]-108)<24,'weapon probe stands inside actual start-handle interaction radius')
            self.step(1,'A');self.step(14);damage=before-self.get('north_game_machine_hp',1)
            self.check(damage>0,'exposed machine weapon A takes priority over overlapping start handle')
            self.cases.append({'case':'boss-handle-A-priority-'+str(cls),'weapon_class':cls,'hero':position,'damage_q4':damage,'passed':True})
            self.restore('candidate-machine-ready');NorthernJourney.machine(self,cls)
        self.coverage.append('all-three-weapon-classes-near-exposed-machine')
    def wake_around_corner(self):
        self.prepare(18,goal=(152,48),direction=1);self.step(1,'R');p=self.power();self.check(p['northern_power_time']>0,'native Water wake starts around actual tree corner')
        # Compare the hypothetical shortcut against the independently decoded
        # ROM collision mask. Actual gameplay validates only both orthogonal
        # legs, which is why this cast can go around the obstructing corner.
        mask,w,h=self.mask();x,y=p['northern_power_origin_x'],p['northern_power_origin_y'];tx,ty=p['bx'],p['by'];dx=abs(tx-x);dy=-abs(ty-y);sx=1 if x<tx else -1;sy=1 if y<ty else -1;error=dx+dy;blocked=[]
        while True:
            if mask[y*w+x]:blocked.append([x,y])
            if (x,y)==(tx,ty):break
            twice=error*2
            if twice>=dy:error+=dy;x+=sx
            if twice<=dx:error+=dx;y+=sy
        self.check(bool(blocked),'direct shortcut really crosses an actual collision wall')
        trace=[]
        for _ in range(42):self.step(1);trace.append(self.row())
        self.check(max(r['power']['travel'] for r in trace)==48,'native bent wake completes both swept24px segments around corner')
        self.cases.append({'case':'Water-L-path-around-real-corner','power':p,'blocked_shortcut_pixels':blocked,'trace':trace,'passed':True});self.coverage.append('native-Water-two-leg-corner-LOS')
    def modal_cache_resume(self):
        def tiled(raw):
            return b''.join(raw[(ty+y)*16+tx:(ty+y)*16+tx+8] for ty in (0,8) for tx in (0,8) for y in range(8))
        self.restore('candidate-town-source');self.entry(23);self.goto(304,176);self.ready();records=[]
        for tab in (0,2,3,4,6):
            self.open_tab(tab);self.step(25);paused=self.oam()
            self.check(all(o['priority']==0 for o in paused),'fully opaque journal shows HUD and suppresses all world OBJ')
            self.close_menu();self.step(4,'RIGHT');self.step(4,'LEFT');self.step(2)
            hero_code=self.get('gfx_hero_frame');hero=tiled(self.e.bytes(self.sym['hero_frames']+hero_code*256,256))
            self.check(self.e.bytes(0x06014000+6144,256)==hero,'post-pause hero OBJ exactly matches current ROM animation frame')
            form=self.selected().form_id;code=self.get('gfx_companion_frame');index=[19,20,22,23,73,74,75,76,77,78].index(form);direction=(code%16)//4;pose=code%4
            companion=tiled(self.e.bytes(self.sym['northern_creature_direction_frames']+((index*4+direction)*4+pose)*256,256))
            self.check(self.e.bytes(0x06014000+6400,256)==companion,'post-pause selected companion OBJ exactly matches current ROM pose')
            actor_checks=[]
            for slot in range(self.get('region_actor_cursor')):
                key=self.e.read(self.sym['region_actor_keys']+slot*4)
                if 512<=key<1024:ptr=self.sym['north_sprites']+(key-512)*256
                elif 200<=key<256:ptr=self.sym['world_sprites']+(key-200)*256
                else:continue
                offset=8448+slot*256 if slot<8 else 10816+(slot-8)*256
                self.check(self.e.bytes(0x06014000+offset,256)==tiled(self.e.bytes(ptr,256)),'post-pause regional actor lease contains exact keyed ROM pixels')
                actor_checks.append({'slot':slot,'key':key,'offset':offset})
            self.check(bool(actor_checks),'resumed world renders actual cached Northern actors')
            oam=self.oam();self.check(any(o['priority']==1 for o in oam),'world actors are actually submitted after closing journal')
            screenshot=self.out/f'journal-{tab}-resumed.png';self.e.screenshot(screenshot)
            records.append({'tab':tab,'paused_oam_count':len(paused),'resumed_oam_count':len(oam),'hero_frame':hero_code,'form':form,'companion_code':code,'actor_tile_checks':actor_checks,'screenshot':str(screenshot)})
        self.cases.append({'case':'modal-hidden-world-cache-resume','records':records,'passed':True});self.coverage.append('post-journal-hero-companion-regional-cache-pixel-resume')
    def run(self,only=None):
        self.boot();cases=[('command-'+str(c),lambda c=c:self.damage_case(c)) for c in (13,14,15,16,17,18,19)]
        cases += [('command-20',self.interception),('command-21',lambda:self.metal_case(21)),('command-22',lambda:self.metal_case(22)),('blocked-geometry',self.blocked_geometry),('wake-corner',self.wake_around_corner),('gear-locks-freeze',self.gear_locks_and_freeze),('shared-lease',self.shared_lease),('sidegrades',self.sidegrades),('sidegrade-behavior',self.sidegrade_behavior),('bow-ranges',self.bow_ranges),('weapon-hits',self.weapon_hits),('boss-weapons',self.boss_weapon_inputs),('wrong-positions',self.wrong_positions),('phase-matchups',self.control_phase_matchups),('metal-late-lock',self.metal_late_lock_and_reuse),('hitstop-cooldown',self.hitstop_and_cooldown),('fractional-health',self.fractional_native_hit),('moving-away',self.moving_away),('late-span',self.span_late_entry),('bow-controls',self.bow_controls),('capacity-wrong-facing',self.interception_capacity_and_wrong_facing),('performance',self.performance),('gathered-performance',lambda:self.performance(True)),('modal-cache-resume',self.modal_cache_resume),('cold-menu-save',self.cold_menu_save)]
        selected=set(only.split(',')) if only else {name for name,_ in cases}
        assert selected<={name for name,_ in cases},'Unknown requested test case'
        for name,fn in cases:
            if name in selected:self.run_case(name,fn)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);p.add_argument('--source-report',type=Path,default=ROOT/'build/northern-journey/northern-journey.json');p.add_argument('--case');p.add_argument('--elf',type=Path,help='Exact ROM-paired ELF for file-scoped locals; defaults to symbols sibling when names collide');a=p.parse_args()
    run=NorthernCombat(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.elf)
    try:run.run(a.case)
    finally:run.report();run.e.close()
    return bool(run.failures)
if __name__=='__main__':raise SystemExit(main())
