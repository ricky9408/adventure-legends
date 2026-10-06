#!/usr/bin/env python3
"""Independent controller-only Magma combat acceptance on an immutable candidate.

Acquisition is authenticated by a successful producer report. Only exact-ROM
hash-paired state + SRAM may be restored. No game-memory writes, arbitrary
calls, fabricated enemies, form grants, level grants, HP grants, or old states.
The observer uses the exact paired ELF's STT_FILE-scoped local variables.
An explicitly pinned predecessor may supply SRAM-only cold import; its machine
state is never loaded or copied. An untested requirement is not accepted.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, struct, traceback
from pathlib import Path
from magma_journey import MagmaJourney, elf_locals, ROOT, PLAY, PAUSE, DIALOG, SAVING, digest
from northern_journey import newest_bank
from northern_combat_tests import NorthernCombat

COMMANDS = dict(zip(range(43,67), ('Warm Thread','Coil Clamp','Crown Interval','Heel Knock','Brace Reply','Archfall','Burr Skip','Root Hem','Cone Drop','Mist Stop','Cup Shower','Ribbon Sweep','Pick Tap','Spiral Notch','Tail Pendulum','Cinder Tilt','Plume Cut','Ash Screen','Gravel Sift','Terrace Lift','Sprig March','Trellis Bend','Bead Step','Dewfold')))
OWNERS = {43:33,44:33,45:33,46:36,47:36,48:36,49:38,50:38,51:39,52:41,53:41,54:42,55:44,56:44,57:45,58:47,59:47,60:48,61:96,62:96,63:98,64:98,65:100,66:100}
# Independent transcription of the authored combat card budgets (not live state).
SPECS = dict(zip(range(43,67), ((8,36,12,90,16,1),(12,16,16,120,24,1),(18,30,20,150,32,1),(6,8,16,90,20,2),(12,24,18,120,24,2),(20,10,22,150,32,2),(8,18,12,90,16,0),(14,36,14,120,20,0),(16,6,18,120,24,0),(8,12,14,90,16,4),(12,30,18,120,24,4),(10,20,20,120,24,4),(6,12,16,90,20,3),(14,8,22,120,28,3),(16,20,16,120,24,3),(8,10,12,90,16,1),(12,18,18,120,24,1),(14,40,18,120,16,1),(10,12,12,90,20,2),(16,20,20,120,24,2),(10,24,12,90,16,0),(14,30,16,120,24,0),(10,14,12,90,16,4),(18,24,18,120,24,4))))
# A point on each genuinely distinct role. Values are forward/lateral from hero.
TARGETS={43:(8,0),44:(24,-10),45:(30,0),46:(18,0),48:(30,0),49:(24,0),50:(22,12),51:(32,0),52:(28,0),53:(32,0),54:(18,0),55:(18,-5),56:(20,0),57:(18,2),58:(16,-13),59:(20,-8),60:(26,0),61:(20,0),62:(20,-14),63:(24,0),64:(24,-16),65:(22,0),66:(20,0)}
REQUIREMENTS=['all24_native_damage_roles','all24_five_phase_modifiers','zero_control_boss_exceptions','cooldown_and_one_hit','recycled_slot_and_serial_wrap','wall_corner_and_connected_turn_clipping','ConeDrop_startup_only_retarget','exact_selected_instance_and_retained_family','shared_tile_lease_and_older_power_reset','L_menu_hitstop_pause_and_gear_lock','native240x160_field_cast_and_cold_overlay_cadence']

def phase_damage(command, defender):
    base, phase=SPECS[command][4:];controls=(2,3,4,0,1)
    multiplier=320 if controls[phase]==defender else 224 if controls[defender]==phase else 256
    return (base*multiplier+128)//256

class MagmaCombat(MagmaJourney):
    arrows=NorthernCombat.arrows
    stats=NorthernCombat.stats
    gear_candidate=NorthernCombat.gear_candidate
    def __init__(self,rom,symbols,output,rom_sha,symbols_sha,source_report,source_snapshot,source_manifest=None,approved_source_report_sha=None):
        self.report_ready=False
        report_path=Path(source_report).resolve();source=json.loads(report_path.read_text())
        assert source['suite'] in ('magma-native-controller-journey','magma-minimal-native-controller-route')
        assert source['controller_only'] is True and source['game_ram_writes']==0 and not source['failures']
        assert source['checks'] and all(c['passed'] is True for c in source['checks'])
        cross_rom=source['rom_sha256']!=rom_sha
        if cross_rom:
            assert approved_source_report_sha and digest(report_path)==approved_source_report_sha,'Cross-ROM SRAM requires the explicitly approved exact acquisition report hash'
            assert len(source['snapshots'][source_snapshot]['obtained_form_ids'])==65,'Only the authenticated completed roster can use predecessor SRAM'
        else:assert source['symbols_sha256']==symbols_sha
        if approved_source_report_sha:assert digest(report_path)==approved_source_report_sha
        assert source['provenance']['cross_rom_machine_state_loaded'] is False
        producer_sources={}
        for name,sha in source['test_sources'].items():
            candidates=(report_path.parent/'test-source'/name,report_path.parent/'test-source'/Path(name).name,ROOT/name)
            matched=next((p for p in candidates if p.is_file() and digest(p)==sha),None)
            assert matched is not None,('No exact pinned producer source',name)
            producer_sources[name]=matched
        fixture=ROOT/'tests/fixtures/v5-revision4'/Path(source['provenance']['fixture']).name
        super().__init__(rom,symbols,output,rom_sha,symbols_sha,fixture=fixture,source_manifest=source_manifest)
        if not cross_rom:assert source['source_manifest_sha256']==self.source_manifest_sha
        assert digest(report_path.parent/'candidate-source-hashes.json')==source['source_manifest_sha256']
        producer_elf=report_path.parent/'tested.elf';producer_rom=report_path.parent/'tested.gba'
        assert digest(producer_elf)==source['elf_sha256'] and digest(producer_rom)==source['rom_sha256']
        elf_locals(producer_elf,producer_rom) # Separate debug-path ELF is allowed only after exact ROM load-image pairing.
        self.source_evidence=dict(report_path=str(report_path),report_sha256=digest(report_path),snapshot=source_snapshot,source_sram_ancestor=self.provenance.copy(),source_rom_sha256=source['rom_sha256'],source_symbols_sha256=source['symbols_sha256'],source_elf_sha256=source['elf_sha256'],source_manifest_sha256=source['source_manifest_sha256'],cross_rom_sram_import=cross_rom,approved_acquisition_report_sha256=approved_source_report_sha,source_machine_state_policy='Exact-ROM, hash-checked matched state+SRAM only')
        shutil.copyfile(report_path,self.out/'acquisition-source-report.json')
        self.source_evidence['producer_test_sources']=source['test_sources']
        for name,path in producer_sources.items():
            dest=self.out/'acquisition-test-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
        capture=report_path.parent/'test-source-capture.json'
        if capture.is_file():
            self.source_evidence['producer_source_capture_sha256']=digest(capture);shutil.copyfile(capture,self.out/'acquisition-test-source-capture.json')
            for name,sha in json.loads(capture.read_text()).get('additional_imported_observer_sources',{}).items():
                path=report_path.parent/'test-source'/Path(name).name;assert digest(path)==sha
                dest=self.out/'acquisition-test-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
        self.source_snapshot='source-'+source_snapshot
        rec=dict(source['snapshots'][source_snapshot]);assert (rec['rom_sha256'],rec['symbols_sha256'])==(source['rom_sha256'],source['symbols_sha256'])
        for kind,suffix in (('state','.state'),('sram','.sav')):
            p=Path(rec[kind+'_path']);assert digest(p)==rec[kind+'_sha256']
            if cross_rom and kind=='state':rec[kind+'_path']=None;continue
            dest=self.out/(self.source_snapshot+suffix);shutil.copyfile(p,dest);rec[kind+'_path']=str(dest)
        bank=newest_bank(Path(rec['sram_path']).read_bytes());assert int.from_bytes(bank[12:14],'little')==(5 if cross_rom else 6)
        retained=[(bank[160+i*24],int.from_bytes(bank[168+i*24:172+i*24],'little')) for i in range(160) if bank[161+i*24]&1]
        histories=[i+1 for i in range(128) if bank[112+(i>>3)]&(1<<(i&7))]
        assert [f for f,i in retained]==rec['owned_form_ids'] and histories==rec['obtained_form_ids']
        assert len({i for f,i in retained})==len(retained) and all(i for f,i in retained)
        if len(histories)==65:assert len(retained)==34 and set(range(31,49))|set(range(95,101))<=set(histories)
        self.snapshots[self.source_snapshot]=rec
        self.source_evidence.update(state_sha256=rec['state_sha256'],sram_sha256=rec['sram_sha256'],owned_forms=rec['owned_form_ids'],historical_forms=rec['obtained_form_ids'])
        self.branch_loads=[];self.screenshots=[];self.accepted_commands=[];self.covered=[];self.native_write_attempts=[];self.source_checks={p:digest(self.source_root/p)==v for p,v in self.source_hashes.items()}
        self.elf_pairing={'sha256':digest(self.elf),'matched_load_image_beyond192byte_header':True,'locals_file':'magma_powers.c','locals':{k:v for k,v in self.locals.items() if k.startswith(('magma_powers.c:','game.c:','northern_powers.c:'))}}
        for name in ('tests/magma_combat_tests.py','tests/region_combat_tests.py','tests/northern_combat_tests.py','tests/test_save5.py','tests/test_save4.py'):
            self.test_sources[name]=digest(ROOT/name)
        for name,sha in self.test_sources.items():
            p=self.out/'test-source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p);assert digest(p)==sha
        def deny(*args,**kwargs):
            self.native_write_attempts.append(repr(args));raise AssertionError('Game RAM writes are forbidden')
        self.e.write=deny;self.e.lib.eb_write=deny
        self.report_ready=True;self.report()
    def report(self):
        if not self.report_ready:return
        r={'suite':'magma-native-combat-controls','controller_only':True,'synthetic_gameplay':False,'game_ram_writes':0,'game_ram_write_attempts':self.native_write_attempts,'player_facing':False,'enabled_rows_are_not_acquisition_evidence':True,**self.candidate,'source_manifest_sha256':self.source_manifest_sha,'frozen_source_checks':self.source_checks,'provenance':self.source_evidence,'elf_pairing':self.elf_pairing,'test_sources':self.test_sources,'native_damage_commands_accepted':sorted(set(self.accepted_commands)),'requirements_covered':self.covered,'requirements_not_accepted':[x for x in REQUIREMENTS if x not in self.covered],'screenshots':self.screenshots,'branch_loads':self.branch_loads,'checks':self.checks,'failures':self.failures,'cases':self.cases,'frame_windows':self.frame_windows,'snapshots':self.snapshots,'inputs':self.inputs,'timing_source':'Actual GBA hardware frames, game update counter, displayed Mode4 page flips and GBA ARM timer cycles; never host FPS','timing_caveat':'render_cycles excludes final VBlank/OAM commit; strict cadence therefore separately requires one update and page flip every hardware frame','native_limits':['alternate-side API is not a controller affordance','serial-wrap and forged projectile provenance require synthetic host tests and are not claimed native','No full-engine stack high-water measurement is performed here']}
        (self.out/'magma-combat.json').write_text(json.dumps(r,indent=2)+'\n')
    def restore(self,name):
        row=self.snapshots[name];super().restore(name)
        self.branch_loads.append({'snapshot':name,'rom_sha256':self.target_sha,'state_sha256':row['state_sha256'],'sram_sha256':row['sram_sha256'],'matched_sram_loaded_before_state':True})
    def power(self):
        p={n:self.get('magma_power_'+n) for n in ('kind','time','form','direction','origin_x','origin_y','age','cooldown','cast_time','phase')}
        for name in ('caster_id','lease_generation','chapter_token','chapter_hit','hit_mask','spent','aimed','ended_mask','guard_enemy','guard_grace','cast_side','own_slow','own_root','own_stagger','aim_x','aim_y','path_count','draw_count'):
            v=self.local(name,file='magma_powers.c');size=self.locals['magma_powers.c:'+name][1]
            if name in ('cast_side','aim_x','aim_y') and v>>(size*8-1):v-=1<<(size*8)
            p[name]=v
        p['global_cooldown']=self.get('ability_cd');p['tile_owner']=self.local('tile_owner',file='northern_powers.c')
        a,size=self.locals['magma_powers.c:paths'];assert size==240
        p['paths']=[dict(zip(('x','y','tx','ty','ex','ey','valid','open','whole','radius','parent','group','from','to'),struct.unpack('<6h8B',self.e.bytes(a+i*20,20)))) for i in range(p['path_count'])]
        return p
    def enemies(self):
        rows=super().enemies()
        for i,e in enumerate(rows):
            e.update(index=i,windup=self.e.read(self.sym['enemy_windups']+i*4),clock=self.e.read(self.sym['enemy_clocks']+i*4),slow=self.e.read(self.sym['slowed_enemies']+i,1),root=self.e.read(self.sym['rooted_enemies']+i*4,4),stagger=self.e.read(self.sym['enemy_stagger_ticks']+i,1),serial=self.e.read(self.locals['magma_powers.c:enemy_serial'][0]+i*2,2))
        return rows
    def shots(self):
        rows=super().shots()
        for i,r in enumerate(rows):r.update(index=i,ordinary_provenance=self.e.read(self.sym['ordinary_hostile_shots']+i,1))
        return rows
    def row(self):
        return dict(hardware_frame=self.e.frame,game_frame=self.get('frame'),hero=[self.get('px'),self.get('py')],selected_form=self.selected().form_id,selected_id=self.selected().instance_id,command=self.command(),power=self.power(),enemies=self.enemies(),shots=self.shots(),arrows=self.arrows(),hp_q4=self.hp_q4(),hitstop=self.get('hitstop'),invuln=self.get('invuln'),guard_invuln=self.get('guard_invuln'),state=self.get('game_state'),machine_stage=self.get('magma_game_machine_stage',1),machine_ticks=self.get('magma_game_machine_ticks',1),machine_hp_q4=self.get('magma_game_machine_hp',1),cycles=self.get('render_cycles'),obj_count=self.get('obj_count'),displayed_page=self.e.read(0x04000000,2)&16)
    def boot(self):
        if len(self.source_evidence['historical_forms'])==65:
            self.e.load_save(self.snapshots[self.source_snapshot]['sram_path']);self.e.reset();self.step(150);self.tap('START',2,35);self.settle()
            self.source_evidence.update(source_machine_state_loaded=False,source_sram_cold_boot=True,source_machine_state_policy='Authenticated SRAM-only cold import; only newly generated same-candidate state+SRAM branches follow')
        else:
            self.restore(self.source_snapshot);self.source_evidence.update(source_machine_state_loaded=True,source_sram_cold_boot=False)
        self.check([c.form_id for c in self.live()]==self.source_evidence['owned_forms'],'authenticated snapshot retains exact genuinely earned individual forms')
        self.check(self.collection()==self.source_evidence['historical_forms'],'authenticated snapshot retains exact earned history')
        self.to_town();self.target(112,248);self.ready();self.snapshot('combat-town-source')
        self.forms={c.form_id for c in self.live()}
    def owner(self,cmd):
        candidates=[OWNERS[cmd]]+([31,32] if cmd==43 else [32] if cmd==44 else [34,35] if cmd==46 else [35] if cmd==47 else [])
        return next((f for f in candidates if f in self.forms),None)
    def prepare(self,cmd,field=True):
        self.restore('combat-town-source');form=self.owner(cmd);self.check(form is not None,'command'+str(cmd)+' has a genuinely earned owner')
        self.owned_select(form);self.set_command(cmd);self.ready()
        if field:self.entry(39)
        self.check(self.command()==cmd,'actual Growth R cycling selects command'+str(cmd))
    def align(self,x,y,direction):
        # Facing is also ordinary movement; offset that one update before the cast.
        dx,dy=((0,1),(0,-1),(-1,0),(1,0))[direction]
        tx,ty=x-dx*2,y-dy*2
        self.goto(tx,ty,radius=4)
        for _ in range(16):
            ex,ey=tx-self.get('px'),ty-self.get('py')
            if abs(ex)+abs(ey)<=2:break
            self.step(1,('RIGHT' if ex>0 else 'LEFT') if abs(ex)>=abs(ey) else ('DOWN' if ey>0 else 'UP'))
        self.step(1,('DOWN','UP','LEFT','RIGHT')[direction]);self.step(1)
        self.check(self.get('face')==direction,'D-pad establishes real cast facing')
    def trace(self,count,keys=None,label=None):
        previous=(self.get('frame'),self.e.read(0x04000000,2)&16);rows=[]
        for n in range(count):
            self.step(1,keys(n) if keys else 0);r=self.row();r['update_delta']=(r['game_frame']-previous[0])&0xffffffff;r['page_flip']=r['displayed_page']!=previous[1];previous=(r['game_frame'],r['displayed_page']);rows.append(r)
            if label and label.startswith('cast-') and n in (2,12,24):
                path=self.out/(getattr(self,'current_case','probe')+'-'+label+'-native-'+str(n)+'.png');self.e.screenshot(path);self.screenshots.append(dict(path=str(path),sha256=digest(path),dimensions=[240,160],case=label,frame=self.e.frame,power_age=r['power']['age']))
        if label:
            window=dict(name=label,hardware_frames=count,updates=sum(r['update_delta'] for r in rows),page_flips=sum(r['page_flip'] for r in rows),max_cycles=max(r['cycles'] for r in rows),max_oam=max(r['obj_count'] for r in rows),trace=rows)
            self.frame_windows.append(window)
            self.check(all(r['update_delta']==1 and r['page_flip'] and r['cycles']<280896 and r['obj_count']<=128 for r in rows),label+' obeys native hardware cadence and OAM budgets')
        return rows
    def cast_pixels(self,cmd):
        def tiled(raw):return b''.join(raw[(ty+y)*16+tx:(ty+y)*16+tx+8] for ty in (0,8) for tx in (0,8) for y in range(8))
        checks=[]
        for label,symbol,stride,offset in (('mark','magma_power_marks',256,15616),('particle','magma_power_particles',64,16192)):
            expected=self.e.bytes(self.sym[symbol]+(cmd-43)*stride,stride)
            if stride==256:expected=tiled(expected)
            actual=self.e.bytes(0x06014000+offset,stride);self.check(actual==expected,'command'+str(cmd)+' '+label+' shared OBJ tiles match its exact ROM motif')
            checks.append(dict(kind=label,expected_sha256=hashlib.sha256(expected).hexdigest(),actual_sha256=hashlib.sha256(actual).hexdigest()))
        form=self.selected().form_id;ids=list(self.e.bytes(self.sym['magma_creature_form_ids'],24));code=self.get('gfx_companion_frame');direction=code%16//4;index=ids.index(form)
        self.check(code>=131072,'actual selected new companion displays its startup casting pose')
        pointer=self.sym['magma_creature_ability_frames']+((index*4+direction)*2+((code//262144)&1))*256
        expected=tiled(self.e.bytes(pointer,256));actual=self.e.bytes(0x06014000+6400,256)
        self.check(actual==expected,'selected individual companion tiles match the exact authored form and cast direction')
        checks.append(dict(kind='companion',form=form,instance_id=self.selected().instance_id,expected_sha256=hashlib.sha256(expected).hexdigest(),actual_sha256=hashlib.sha256(actual).hexdigest()))
        return checks
    def cast(self,cmd,count=None,keys=None):
        before=self.row();self.step(1,'R');start=self.row();startup,active,recovery,cd,damage,phase=SPECS[cmd]
        start['update_delta']=(start['game_frame']-before['game_frame'])&0xffffffff;start['page_flip']=start['displayed_page']!=before['displayed_page']
        self.check(start['update_delta']==1 and start['page_flip'] and start['cycles']<280896,'cold R cast frame updates and flips inside the actual native hardware budget')
        self.check(start['power']['kind']==cmd and start['power']['time']==startup+active+recovery,'actual R starts exact authored lifetime for command'+str(cmd))
        self.check(start['power']['caster_id']==before['selected_id'] and start['power']['form']==before['selected_form'],'cast snapshots exact actual selected individual')
        self.check(start['power']['phase']==phase and cd-8<=start['power']['global_cooldown']<=cd,'cast applies authored phase and bounded equipment cooldown')
        self.check(start['power']['tile_owner']==4 and start['power']['cast_side']==-1,'game R takes Magma lease and actual default side minus one')
        start['native_tile_checks']=self.cast_pixels(cmd)
        rows=[start]+self.trace(count or startup+active+recovery+3,keys,'cast-'+str(cmd))
        window=self.frame_windows[-1];window['trace'].insert(0,start);window['hardware_frames']+=1;window['updates']+=start['update_delta'];window['page_flips']+=int(start['page_flip']);window['max_cycles']=max(window['max_cycles'],start['cycles']);window['max_oam']=max(window['max_oam'],start['obj_count'])
        self.check(all(r['power']['draw_count']<=24 and r['power']['path_count']<=12 and r['power']['hit_mask']<64 and r['power']['ended_mask']<8 for r in rows),'real command uses bounded24OBJ12path6target3projectile bookkeeping')
        return before,rows
    def direct(self,cmd):
        self.prepare(cmd);f,s=TARGETS[cmd];self.align(424-s,120+f,1);self.ready()
        before,rows=self.cast(cmd);hp=before['enemies'][2]['hp_q4'];after=rows[-1]['enemies'][2]['hp_q4'];expected=phase_damage(cmd,3)
        result={'case':'direct-'+str(cmd),'name':COMMANDS[cmd],'command':cmd,'before':before,'trace':rows,'damage_q4':hp-after,'expected_q4':expected};self.cases.append(result)
        self.check(hp-after==expected,COMMANDS[cmd]+' lands exactly one authored phase-resolved budget on genuine Metal ranger')
        changes=[r for a,r in zip([before]+rows,rows) if a['enemies'][2]['hp_q4']!=r['enemies'][2]['hp_q4']]
        self.check(len(changes)==1,'one-hit ledger prevents repeated target damage across full lifetime')
        hit=changes[0];self.check(hit['power']['age']>=SPECS[cmd][0],'startup warning causes no damage')
        if cmd==45:self.check(hit['power']['age']==28,'Crown Interval middle spoke waits for its distinct second interval')
        if cmd==53:self.check(hit['power']['age']==28,'Cup Shower middle point lands at its distinct active-update16')
        if cmd==55:
            self.check(hit['power']['age']==6 and hit['power']['spent']==1,'Pick Tap first nail consumes the shared effect on first actual hit')
            self.check(all(r['power']['draw_count']==0 for r in rows if 12<=r['power']['age']<18),'first Pick Tap hit suppresses the later second nail rendering')
        if cmd==49:self.check(hit['enemies'][2]['slow']>0,'Burr Skip applies short ordinary slow')
        if cmd==50:self.check(hit['enemies'][2]['root']>0,'Root Hem applies brief ordinary root')
        if cmd in (46,48,52):self.check(hit['enemies'][2]['stagger']>0 and not hit['enemies'][2]['windup'],'ordinary windup is interrupted and briefly staggered')
        if cmd==56:self.check(hit['enemies'][2]['stagger']==0,'Spiral Notch does not invent prior stagger')
        if cmd==60:self.check(hit['power']['age']==54,'Ash Screen damage is its one expiry puff')
        self.check(not rows[-1]['power']['time'] and rows[-1]['power']['tile_owner']==0,'expired cast releases its tile lease')
        self.check(rows[-1]['power']['global_cooldown']>0,'effect expiry cannot reset remaining cooldown')
        result['passed']=True;self.accepted_commands.append(cmd)
        # Restore the paired pre-cast branch is unnecessary; screenshot captures full native viewport.
        self.e.screenshot(self.out/('command-'+str(cmd)+'-recovered.png'));self.report()
    def phase_case(self,cmd,enemy_index):
        self.prepare(cmd);f,s=TARGETS[cmd];f=12 if cmd==43 and enemy_index!=2 else f;s=-8 if cmd==55 and enemy_index!=2 else s;self.ready();chosen=None
        for attempt in range(3):
            enemy=self.enemies()[enemy_index];mask,w,h=self.mask();options=[]
            for direction,(dx,dy) in enumerate(((0,1),(0,-1),(-1,0),(1,0))):
                x=enemy['x']-f*dx+s*dy;y=enemy['y']-f*dy-s*dx
                if 8<=x<w-8 and 8<=y<min(h-8,286) and not mask[y*w+x] and not mask[(y-dy*2)*w+x-dx*2]:options.append((abs(x-self.get('px'))+abs(y-self.get('py')),direction,x,y))
            self.check(bool(options),'real phase target has a collision-valid authored attack approach')
            _,direction,x,y=min(options);self.align(x,y,direction);chosen=(direction,x,y)
            self.check(self.get('room')==39,'phase approach stays in the actual intended enemy field')
        before,rows=self.cast(cmd);enemy=before['enemies'][enemy_index];expected=phase_damage(cmd,enemy['phase']);actual=enemy['hp_q4']-rows[-1]['enemies'][enemy_index]['hp_q4']
        self.cases.append(dict(case='phase-'+str(cmd)+'-'+str(enemy['phase']),command=cmd,defender_phase=enemy['phase'],enemy_index=enemy_index,approach=chosen,before=before,trace=rows,expected_q4=expected,damage_q4=actual))
        self.check(actual==expected,'real command'+str(cmd)+' resolves phase'+str(enemy['phase'])+' to exact authored '+str(expected)+'Q4')
    def safe_gap(self,cmd):
        self.prepare(cmd);f,s={50:(22,0),58:(16,13),62:(20,0),64:(24,16),65:(20,7),66:(0,0)}[cmd];self.align(424-s,120+f,1);self.ready();before,rows=self.cast(cmd)
        self.check(before['enemies'][2]['hp_q4']==rows[-1]['enemies'][2]['hp_q4'],COMMANDS[cmd]+' preserves its real authored center/angular/unchosen-side gap')
        self.cases.append(dict(case='safe-gap-'+str(cmd),before=before,trace=rows,passed=True))
    def spiral_extend(self):
        self.prepare(56);self.align(424,135,1);self.ready();self.check(self.stats()['stagger']>0,'actual earned equipment supplies a real weapon stagger')
        self.step(1,'A');weapon=[]
        for _ in range(70):
            self.step(1);weapon.append(self.row());e=self.enemies()[2]
            if e['stagger']>=24 and not self.get('hitstop'):break
        # The real sword knocks the ranger away diagonally; walk back into the narrow lane before its stagger expires.
        for _ in range(12):
            e=self.enemies()[2];dx=e['x']-self.get('px')
            if abs(dx)<=2:break
            self.step(1,'RIGHT' if dx>0 else 'LEFT')
        self.step(1,'UP');self.step(1)
        for _ in range(35):
            e=self.enemies()[2]
            if e['stagger']<=16:break
            self.step(1)
        self.check(e['hp_q4']>28 and e['stagger']==16,'real ordinary sword contact creates a living already-staggered target')
        before,rows=self.cast(56);raises=[(a,b) for a,b in zip([before]+rows,rows) if b['enemies'][2]['stagger']>a['enemies'][2]['stagger']]
        self.check(len(raises)==1 and 0<raises[0][0]['enemies'][2]['stagger']<16 and raises[0][1]['enemies'][2]['stagger']==15,'Spiral Notch extends only existing short stagger to its bounded16updates before ordinary engine decrement')
        self.check(before['enemies'][2]['hp_q4']-rows[-1]['enemies'][2]['hp_q4']==phase_damage(56,3),'stagger extension adds no second or weapon-triggered damage budget')
        self.cases.append(dict(case='Spiral-Notch-real-stagger-extension',weapon_trace=weapon,before=before,trace=rows,passed=True))
    def screen_intercept(self):
        self.prepare(60);self.align(424,180,1);self.ready();incoming=[]
        for _ in range(260):
            incoming=[s for s in self.shots() if s['life'] and s['owner']==1 and s['ordinary_provenance']==1 and abs(s['x']-424)<=2 and 120<=s['y']<=128 and s['dy']>0]
            if incoming:break
            self.step(1)
        self.check(bool(incoming),'actual ordinary Metal ranger creates a correctly provenanced incoming shot')
        before,rows=self.cast(60);spent=[r for r in rows if r['power']['spent']]
        self.cases.append(dict(case='Ash-Screen-real-shot-interception',before=before,trace=rows,incoming=incoming))
        self.check(spent and spent[0]['power']['age']>=14,'stationary Ash Screen consumes a real ordinary hostile shot during its active window')
        i=incoming[0]['index'];self.check(spent[0]['shots'][i]['life']==0 and spent[0]['hp_q4']==before['hp_q4'],'intercept consumes the actual shot before it reaches or damages the player')
        self.check(before['enemies'][2]['hp_q4']==rows[-1]['enemies'][2]['hp_q4'],'interception does not invent damage outside the expiry-puff geometry')
    def pick_second(self):
        self.prepare(55);self.align(419,138,1);self.ready();before,rows=self.cast(55)
        changes=[r for a,r in zip([before]+rows,rows) if a['enemies'][2]['hp_q4']!=r['enemies'][2]['hp_q4']]
        self.check(len(changes)==1 and changes[0]['power']['age']==12,'Pick Tap second nail starts six updates after first only when first misses')
        self.check(before['enemies'][2]['hp_q4']-rows[-1]['enemies'][2]['hp_q4']==phase_damage(55,3),'second jab shares the same one-hit Q4 budget')
        self.cases.append(dict(case='Pick-Tap-second-jab',before=before,trace=rows,passed=True))
    def import_authenticated_branch(self,name):
        source=json.loads((self.out/'acquisition-source-report.json').read_text());rec=dict(source['snapshots'][name]);key='source-'+name
        assert (rec['rom_sha256'],rec['symbols_sha256'])==(self.target_sha,self.symbol_sha)
        for kind,suffix in (('state','.state'),('sram','.sav')):
            p=Path(rec[kind+'_path']);assert digest(p)==rec[kind+'_sha256'];dest=self.out/(key+suffix);shutil.copyfile(p,dest);rec[kind+'_path']=str(dest)
        self.snapshots[key]=rec;return key
    def teaching_boss(self):
        key=self.import_authenticated_branch('regulator-telegraph')
        for cmd,form,f in ((43,31,8),(46,34,18)):
            self.restore(key);self.owned_select(form);self.set_command(cmd);self.ready();self.target(32,80);self.align(120,64-f,0)
            for _ in range(260):
                if self.get('magma_game_machine_stage',1)==3:break
                self.step(1)
            before,rows=self.cast(cmd);damage=before['machine_hp_q4']-rows[-1]['machine_hp_q4'];self.cases.append(dict(case='regulator-damage-exception-'+str(cmd),before=before,trace=rows,damage_q4=damage))
            self.check(damage==SPECS[cmd][4],'exposed neutral regulator accepts one genuine command'+str(cmd)+' budget')
            self.check(sum(a['machine_hp_q4']!=b['machine_hp_q4'] for a,b in zip([before]+rows,rows))==1,'regulator local one-hit ledger survives full command lifetime')
            self.check(all(not r['power']['own_slow'] and not r['power']['own_root'] and not r['power']['own_stagger'] for r in rows),'regulator damage exception creates no ordinary slow root or stagger')
            self.check(all(a['machine_ticks']-b['machine_ticks']==1 for a,b in zip(rows,rows[1:]) if a['machine_stage']==b['machine_stage']),'companion hit does not retime regulator stages')
            self.ready()
            for _ in range(260):
                if self.get('magma_game_machine_stage',1)==4:break
                self.step(1)
            before,rows=self.cast(cmd);self.check(all(r['machine_stage']!=3 for r in rows),'closed-regulator probe stays entirely outside exposure')
            self.check(rows[-1]['machine_hp_q4']==before['machine_hp_q4'],'same real geometry cannot hurt closed regulator')
        self.cases.append(dict(case='teaching-regulator-closed-exposed-and-control-exclusion',passed=True))
    def wall(self,cmd):
        self.prepare(cmd,False);x=self.local('lesson_x');self.align(x-26,232,3);self.ready();before,rows=self.cast(cmd)
        visible=[p for r in rows for p in r['power']['paths'] if p['valid']]
        self.check(any(p['open'] and not p['whole'] for p in visible),'actual movable town jar clips native checked geometry')
        if cmd==64:
            pairs=[r['power']['paths'] for r in rows if len(r['power']['paths'])==2]
            self.check(pairs and all(not p[0]['whole'] and not p[1]['open'] for p in pairs),'blocked Trellis first segment prevents its connected turn restarting beyond real wall')
        self.cases.append(dict(case='real-jar-wall-'+str(cmd),before=before,trace=rows,passed=True))
    def selection_identity(self,cmd=43,other=None):
        self.prepare(cmd,False);owner=self.owner(cmd);other=other or self.owner(46)
        self.assign(0,owner);self.assign(1,other);self.select_slot(0);self.set_command(cmd);self.align(240,220,1);self.ready();self.step(1,'R');original=self.row()
        self.step(1,'L+RIGHT');self.step(1);different=self.row()
        self.check(different['selected_id']!=original['selected_id'] and different['power']['caster_id']==original['selected_id'],'party switch retains the original immutable individual caster')
        self.check(self.get('gfx_companion_frame')<131072,'another selected companion does not borrow the old individual casting pose')
        self.step(1,'R');refused=self.row()
        self.check(refused['power']['caster_id']==original['selected_id'] and refused['power']['kind']==cmd,'different selected companion cannot replace the live cast during cooldown')
        if cmd==51:self.check(not refused['power']['aimed'],'same-family retained branch cannot retarget the other individual Cone Drop')
        self.step(1,'L+UP');self.step(1);same=self.row()
        self.check(same['selected_id']==original['selected_id'] and self.get('gfx_companion_frame')>=131072,'return to exact casting individual restores its remaining startup pose')
        self.check(same['power']['global_cooldown']<=original['power']['global_cooldown'] and same['power']['time']<=original['power']['time'],'selection never refreshes cooldown or lifetime')
        self.cases.append(dict(case='selected-individual-'+str(cmd),original=original,different=different,refused=refused,same=same,passed=True,native_limit='Same-family branches have distinct real forms; identical-form different-ID rejection is covered by the host matrix, not fabricated here'))
    def dynamic_wall(self):
        self.prepare(46,False);x=self.local('lesson_x');self.align(x-16,232,3);self.ready();self.step(1,'R');before=self.row()
        self.check(any(p['open'] and not p['whole'] for p in before['power']['paths']),'cast geometry is actually clipped by the real jar before movement')
        self.step(1);self.step(1,'A');grabbed=self.row();self.check(self.local('grab')==2,'actual A grabs blocking jar during live cast')
        self.step(1);self.step(1,'RIGHT');moved=self.row()
        self.check(self.local('lesson_x')==x+24,'actual D-pad slide moves jar out of snapshotted geometry')
        self.check(moved['power']['caster_id']==before['power']['caster_id'] and moved['power']['origin_x']==before['power']['origin_x'] and moved['power']['age']==4 and moved['power']['time']==before['power']['time']-4,'moving solid invalidates only geometry and preserves immutable cast identity and clock')
        self.check(all(p['whole'] for p in moved['power']['paths']),'render cache re-proves the vacated wall during that same real update')
        self.e.screenshot(self.out/'dynamic-jar-reclipped-native.png');self.step(1);self.step(1,'A');self.step(50)
        self.cases.append(dict(case='actual-dynamic-wall-invalidation',before=before,grabbed=grabbed,moved=moved,passed=True))
    def guards(self):
        self.prepare(47);self.goto(216,264);self.face(3);self.ready()
        for _ in range(260):
            e=self.enemies()[1];dx=e['x']-self.get('px');dy=e['y']-self.get('py')
            if 13<=dx<=14 and abs(dy)<=2 and not self.get('invuln'):break
            self.step(1)
        self.check(13<=dx<=14 and abs(dy)<=2 and not self.get('invuln'),'real ordinary Fire walker reaches active-window guard spacing with no invulnerability')
        before,rows=self.cast(47);guards=[r for r in rows if r['power']['guard_grace']]
        self.cases.append(dict(case='Brace-Reply-real-contact',before=before,trace=rows))
        self.check(bool(guards),'Brace Reply is consumed by real ordinary melee contact')
        first=guards[0];i=first['power']['guard_enemy']
        self.check(first['hp_q4']==before['hp_q4'],'actual eligible melee contact is prevented')
        self.check(before['enemies'][i]['hp_q4']-rows[-1]['enemies'][i]['hp_q4']==phase_damage(47,before['enemies'][i]['phase']),'real guard retaliation lands one phase-resolved budget')
        self.check(all(r['power']['guard_enemy']==i for r in guards),'grace remains attached to that one enemy identity')
        self.accepted_commands.append(47)
    def shared_leases(self):
        self.restore('combat-town-source');self.align(240,220,1);self.ready();rows=[]
        # Each transition is controller selection, Growth R cycling, then real R.
        north=next((f for f in (19,20) if f in self.forms),None);south=next((f for f in (79,80) if f in self.forms),None)
        choices=[(16,11,1),(north,13,2),(south,27,3),(self.owner(43),43,4)]
        for form,cmd,owner in choices:
            if form not in self.forms:continue
            self.owned_select(form);self.set_command(cmd);self.ready();self.step(1,'R')
            actual=self.local('tile_owner',file='northern_powers.c');self.check(actual==owner,'actual command'+str(cmd)+' claims its own shared tile lease')
            rows.append(dict(form=form,command=cmd,owner=actual,power=self.power()))
            self.step(170);self.check(self.local('tile_owner',file='northern_powers.c')==0,'expired legacy/Magma effect releases only its lease')
        self.owned_select(self.owner(43));self.set_command(43);self.ready();self.goto(304,18);self.step(1,'R');self.check(self.power()['time']>0,'room-reset probe begins with a live Magma cast')
        self.step(12,'UP');self.settle();self.check(self.get('room')==39 and not self.power()['time'] and not self.power()['caster_id'] and not self.power()['tile_owner'],'actual room transition clears bounded Magma cast and shared lease')
        self.cases.append(dict(case='shared-tile-leases-and-room-reset',transitions=rows,passed=True))
        if len(rows)==4:self.covered.append('shared_tile_lease_and_older_power_reset')
    def hitstop_pause(self):
        self.prepare(43);self.align(424,135,1);self.ready();self.step(1,'R');self.step(1);self.step(1,'A');rows=self.trace(35,label='actual-weapon-hitstop')
        pairs=[(a,b) for a,b in zip(rows,rows[1:]) if a['hitstop']>0]
        self.check(bool(pairs),'real ordinary weapon collision creates observed hitstop')
        self.check(all(a['power']['age']==b['power']['age'] and a['power']['time']==b['power']['time'] and a['power']['global_cooldown']==b['power']['global_cooldown'] for a,b in pairs),'hitstop freezes Magma age lifetime and cooldown')
        self.cases.append(dict(case='hitstop-freeze',trace=rows,passed=True))
    def lifetime(self,cmd):
        self.prepare(cmd,False);self.align(240,220,1);self.ready();before,rows=self.cast(cmd)
        self.check(rows[-1]['power']['time']==0 and rows[-1]['power']['tile_owner']==0,'bounded empty cast expires with no orphan lease')
        self.cases.append(dict(case='lifetime-'+str(cmd),before=before,trace=rows,passed=True))
    def gear_recovery(self):
        self.prepare(43,False);self.align(240,220,1);self.ready();self.step(1,'R');self.step(45);p=self.power()
        self.check(p['age']==45 and 0<p['time']<12,'gear probe reaches actual Magma recovery after all active geometry')
        before=bytes(self.state().equipment);self.open_tab(4);frozen=self.power()
        self.check(frozen['age']>=44 and frozen['time']>0,'journal opens before real recovery has expired')
        current=self.state().equipment.equipped[self.get('gear_menu_slot')]
        for _ in range(12):
            self.tap('RIGHT',1,2)
            if self.get('gear_menu_candidate')!=current:break
        self.check(self.get('gear_menu_candidate')!=current,'recovery gear probe selects a genuinely different owned candidate')
        self.tap('R',1,2);self.check(bytes(self.state().equipment)==before and self.power()['time']==frozen['time'],'actual Gear R stays locked throughout frozen recovery')
        self.close_menu();self.step(20);self.check(not self.power()['time'],'recovery eventually ends normally')
        self.equip_item(0,4);self.cases.append(dict(case='actual-gear-recovery-lock-and-unlock',recovery=p,passed=True))
    def cooldown_edges(self):
        self.prepare(43,False);self.align(240,220,1);self.ready();self.step(1,'R');first=self.power();self.step(8);before=self.power();self.step(1,'R');again=self.power()
        self.check(again['age']==before['age']+1 and again['time']==before['time']-1 and again['global_cooldown']==before['global_cooldown']-1 and again['chapter_token']==first['chapter_token'],'fresh R edge during live cooldown cannot refresh or replace a cast')
        self.step(50);expired=self.power();self.check(not expired['time'] and expired['global_cooldown']>0,'effect is genuinely expired while cooldown still remains')
        self.step(1,'R');self.check(not self.power()['time'] and self.power()['chapter_token']==first['chapter_token'],'fresh R edge after expiry still respects remaining cooldown')
        self.step(100);self.step(1,'R');self.check(self.power()['time']==56 and self.power()['chapter_token']!=first['chapter_token'],'first allowed fresh R after real cooldown starts a new bounded cast identity')
        self.cases.append(dict(case='real-cooldown-boundaries',first=first,again=again,expired=expired,recast=self.power(),passed=True))
    def pauses(self):
        self.prepare(43,False);self.align(240,220,1);self.ready();self.step(1,'R');before=self.power();equipment=bytes(self.state().equipment)
        rows=self.trace(40,lambda n:'L+RIGHT','held-L-freezes-cast')
        self.check(all(r['power']['age']==before['age'] and r['power']['time']==before['time'] and r['power']['global_cooldown']==before['global_cooldown'] for r in rows),'L selector freezes lifetime and cooldown while native rendering continues')
        self.step(1);self.step(1,'START');self.check(self.get('game_state')==PAUSE,'journal opens during live cast')
        frozen=self.power();self.trace(20,label='live-cast-journal')
        self.check(self.power()==frozen,'journal draw cannot mutate cast state')
        while self.get('journal_tab')!=4:self.tap('A',1,2)
        self.tap('RIGHT',1,2);self.tap('R',1,2)
        self.check(bytes(self.state().equipment)==equipment,'actual Gear R refuses changes during Magma lifetime')
        self.close_menu();self.step(90)
        self.check(not self.power()['time'] and not self.power()['tile_owner'],'resumed cast expires and releases lease')
        self.cases.append(dict(case='L-menu-gear-lock',passed=True,trace=rows))
    def retarget(self):
        self.prepare(51,False);self.align(240,220,1);self.ready();self.step(1,'R');initial=self.power();self.step(1);self.step(1,'RIGHT');self.step(1);self.step(1,'R');once=self.power()
        self.check(once['aimed']==1 and [once['aim_x'],once['aim_y']]!=[initial['aim_x'],initial['aim_y']],'Cone Drop permits one actual startup R retarget')
        self.check(once['age']==4 and once['global_cooldown']==initial['global_cooldown']-4 and once['caster_id']==initial['caster_id'],'retarget preserves original expiry cooldown and caster')
        self.step(1);self.step(1,'LEFT');self.step(1);self.step(1,'R');twice=self.power()
        self.check([twice['aim_x'],twice['aim_y']]==[once['aim_x'],once['aim_y']],'second startup retarget cannot change landing again')
        self.prepare(51,False);self.align(240,220,1);self.ready();self.step(1,'R');initial=self.power();self.step(12);self.step(1,'RIGHT');self.step(1);self.step(1,'R')
        late=self.power();self.check(late['aimed']==0 and [late['aim_x'],late['aim_y']]==[initial['aim_x'],initial['aim_y']],'R after12 startup updates cannot retarget')
        self.covered.append('ConeDrop_startup_only_retarget');self.cases.append(dict(case='ConeDrop-retarget',initial=initial,once=once,twice=twice,late=late,passed=True))
    def run_case(self,name,fn):
        print('BEGIN',name,flush=True);self.current_case=name
        try:fn()
        except Exception as exc:
            traceback.print_exc();self.failures.append({'case':name,'error':str(exc),'status':self.status()});self.snapshot(name+'-failure',settle=False)
        self.report()
    def run(self,only=None):
        self.boot();available=[c for c in COMMANDS if self.owner(c)]
        cases=[('direct-'+str(c),lambda c=c:self.direct(c)) for c in available if c!=47]
        cases += [('lifetime-'+str(c),lambda c=c:self.lifetime(c)) for c in available]+[('pauses',self.pauses),('gear-recovery',self.gear_recovery),('cooldown',self.cooldown_edges),('shared-leases',self.shared_leases),('hitstop',self.hitstop_pause),('dynamic-wall',self.dynamic_wall),('selection',self.selection_identity),('wall',lambda:self.wall(46))]
        if 51 in available:cases.extend([('retarget',self.retarget),('retained-family',lambda:self.selection_identity(51,38))])
        if 47 in available:cases.append(('guard',self.guards))
        if 55 in available:cases.append(('pick-second',self.pick_second))
        if 56 in available:cases.append(('spiral-extend',self.spiral_extend))
        if 60 in available:cases.append(('screen-intercept',self.screen_intercept))
        if 64 in available:cases.append(('wall-turn',lambda:self.wall(64)))
        cases += [('phase-'+str(c)+'-'+str(i),lambda c=c,i=i:self.phase_case(c,i)) for c,indices in ((43,(1,2,3)),(46,(4,3,0)),(49,(0,4,2)),(52,(3,1,4)),(55,(2,0,1))) if c in available for i in indices]
        cases += [('gap-'+str(c),lambda c=c:self.safe_gap(c)) for c in (50,58,62,64,65,66) if c in available]
        if len(self.source_evidence['historical_forms'])<65 and 'regulator-telegraph' in json.loads((self.out/'acquisition-source-report.json').read_text())['snapshots']:cases.append(('teaching-boss',self.teaching_boss))
        names={n for n,_ in cases};chosen=set(only.split(',')) if only else names;assert chosen<=names,(chosen-names)
        for name,fn in cases:
            if name in chosen:self.run_case(name,fn)
        if set(self.accepted_commands)==set(COMMANDS):self.covered.append('all24_native_damage_roles')
        self.report()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('rom','symbols','output','source-report','source-manifest'):p.add_argument('--'+k,type=Path,required=True)
    for k in ('expected-rom-sha','expected-symbols-sha','source-snapshot'):p.add_argument('--'+k,required=True)
    p.add_argument('--case');p.add_argument('--approved-source-report-sha');a=p.parse_args();r=MagmaCombat(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_snapshot,a.source_manifest,a.approved_source_report_sha)
    try:r.run(a.case)
    finally:r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
