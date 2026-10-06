#!/usr/bin/env python3
"""Same-ROM, paired-state native Magma controller and pixel acceptance.

No game RAM mutations or fabricated progression. Imported snapshots must be
paired state/SRAM from an exact-hash, successful controller journey. Bitmap
oracles are pure expected pixels, not synthetic gameplay evidence. This suite
never treats enabled catalog rows as acquisitions. Outputs contain spoilers.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, struct
from pathlib import Path
from magma_journey import MagmaJourney, ROOT, Emulator, PLAY, PAUSE, DIALOG, DEAD, SAVING, digest

def tiled(raw):
    return b''.join(raw[(ty+y)*16+tx:(ty+y)*16+tx+8] for ty in (0,8) for tx in (0,8) for y in range(8))

class NoRamWriteEmulator(Emulator):
    def write(self, *args, **kwargs):
        raise AssertionError('Game RAM writes are forbidden in native acceptance')

class MagmaControls(MagmaJourney):
    def __init__(self, *args, source_report, **kwargs):
        self.completed = False
        self.branch_loads = []
        self.case_results = []
        self.oracle_results = []
        report_path = Path(source_report).resolve()
        report = json.loads(report_path.read_text())
        fixture = ROOT/'tests/fixtures/v5-revision4'/Path(report['provenance']['fixture']).name
        assert digest(fixture) == report['provenance']['sram_sha256']
        kwargs['fixture'] = fixture
        super().__init__(*args, **kwargs)
        assert report['controller_only'] and report['game_ram_writes'] == 0
        assert report['rom_sha256'] == self.target_sha and report['symbols_sha256'] == self.symbol_sha
        assert not report['failures'] and all(c['passed'] for c in report['checks'])
        self.provenance['same_rom_source_report'] = str(report_path)
        self.provenance['same_rom_source_report_sha256'] = digest(report_path)
        self.provenance['source_machine_state_policy'] = 'Exact same ROM and symbols, authenticated paired SRAM plus machine state only'
        for name, row in report['snapshots'].items():
            assert row['rom_sha256'] == self.target_sha and row['symbols_sha256'] == self.symbol_sha
            saved = dict(row)
            for kind, suffix in (('state', '.state'), ('sram', '.sav')):
                path = Path(row[kind+'_path'])
                assert digest(path) == row[kind+'_sha256']
                destination = self.out/('source-'+name+suffix)
                shutil.copyfile(path, destination)
                saved[kind+'_path'] = str(destination)
            self.snapshots['source-'+name] = saved
        self.e.close()
        self.e = NoRamWriteEmulator(self.rom)
        self.test_sources['tests/magma_controls.py'] = digest(Path(__file__))
        for path, sha in self.test_sources.items():
            source = ROOT/path
            assert digest(source) == sha
            target = self.out/'test-source'/path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        self.palette = {k:int(v) for k,v in re.findall(r'#define (PAL_\w+) (\d+)', (ROOT/'src/assets.h').read_text())}
        self.report()

    def report(self):
        super().report()
        data = json.loads((self.out/'magma-journey.json').read_text())
        data.update(suite='magma-native-controller-boundaries', completed=self.completed,
                    case_results=self.case_results, branch_loads=self.branch_loads,
                    pixel_oracles=self.oracle_results, synthetic_gameplay=False,
                    enabled_rows_are_not_acquisition_evidence=True,
                    timing_scope='Real mGBA GBA hardware-frame counter, update counter, displayed Mode4 page bit, and ARM timer cycles; never host FPS')
        (self.out/'magma-controls.json').write_text(json.dumps(data, indent=2)+'\n')

    def restore(self, name):
        row = self.snapshots[name]
        super().restore(name)
        self.branch_loads.append({'name':name, 'rom_sha256':self.target_sha,
                                  'state_sha256':row['state_sha256'], 'sram_sha256':row['sram_sha256'],
                                  'matching_sram_imported_before_state':True})

    def raw(self, label, count, keys=None):
        old = self.get('frame')
        page = self.e.read(0x04000000,2)&16
        trace = []
        for i in range(count):
            self.step(1, keys(i) if keys else 0)
            now = self.get('frame')
            newpage = self.e.read(0x04000000,2)&16
            trace.append({'hardware_frame':self.e.frame, 'update_delta':(now-old)&0xffffffff,
                          'page_flip':newpage!=page, 'cycles':self.get('render_cycles'),
                          'state':self.get('game_state'), 'obj_count':self.get('obj_count'), 'journal_tab':self.get('journal_tab')})
            old, page = now, newpage
        row = {'name':label, 'hardware_frames':count, 'updates':sum(r['update_delta'] for r in trace),
               'flips':sum(r['page_flip'] for r in trace), 'max_cycles':max(r['cycles'] for r in trace), 'trace':trace}
        self.frame_windows.append(row)
        self.report()
        self.check(all(r['update_delta']==1 and r['page_flip'] and r['cycles']<280896 and r['obj_count']<=128 for r in trace), label+' updates and flips every hardware frame inside native cycle and OBJ budgets')
        return row

    def file_bytes(self, file, name):
        address, size = self.locals[file+':'+name]
        return self.e.bytes(address, size)

    def fingerprint(self):
        return list(struct.unpack('<4I', self.file_bytes('game.c', 'collision_fingerprint')))

    def camera(self):
        stride = int(re.search(r'#define CACHE_FIELDS (\d+)', (ROOT/'src/game.c').read_text())[1])
        page = int(bool(self.e.read(0x04000000,2)&16))
        address = self.sym['cache_fields']+page*stride*4
        return self.e.read(address+17*4), self.e.read(address+18*4)

    def clean_bitmap(self, label, settle=True):
        if settle: self.step(140)
        self.check(self.get('game_state')==PLAY and not self.get('toast_ticks') and not self.get('area_ticks'), 'bitmap oracle observes a clean active viewport')
        room = self.get('room')
        descriptor = self.descriptors[room]
        width = descriptor['width']
        cx, cy = self.camera()
        raw = self.e.bytes(descriptor['bitmap'], width*descriptor['height'])
        expected = bytearray(b''.join(raw[(cy+y)*width+cx:(cy+y)*width+cx+240] for y in range(160)))
        def pixel(x,y,c):
            x-=cx; y-=cy
            if 0<=x<240 and 0<=y<160: expected[y*240+x]=c
        def rect(x,y,w,h,c):
            for yy in range(y,y+h):
                for xx in range(x,x+w): pixel(xx,yy,c)
        def line(x,y,xx,yy,c):
            assert x==xx or y==yy
            rect(min(x,xx),min(y,yy),abs(xx-x)+1,abs(yy-y)+1,c)
        p = self.palette
        if room==38:
            assert not self.quest(33) and not self.quest(36)
            line(184,240,200,240,p['PAL_WATER3'])
        elif room==39:
            assert not self.quest(35) and not self.quest(37) and not self.local('seed') and not self.local('branch_visible')
            line(168,272,184,272,p['PAL_WATER3'])
        elif room==40:
            assert not self.state().quests.objectives[35]&2 and not self.local('branch_visible') and not self.local('pots') and not self.local('clapper')
            for i in range(3): rect(80+i*6,72,4,3,p['PAL_WATER3'] if i==self.local('shelf') else p['PAL_STONE2'])
        elif room==41:
            assert not self.local('branch_visible') and not self.local('bypass') and not self.local('basin') and not self.local('sound') and not self.state().quests.region_flags[19]
        elif 42<=room<=44:
            rect(43,76,10,2,p['PAL_GOLD3']); rect(187,76,10,2,p['PAL_WATER3'])
            if room!=42:
                rect(139,40,10,2,p['PAL_WATER3'])
                if room==43: rect(139,76,10,2,p['PAL_GOLD3'])
            if self.puzzle()[3]: rect(165,109,7,3,p['PAL_WATER4'])
            if room==44 and self.puzzle()[3]:
                line(184,104,200,104,p['PAL_GOLD3']); line(192,97,192,111,p['PAL_GOLD3'])
        else:
            raise AssertionError('No authored bitmap oracle for this room')
        page = 0x0600a000 if self.e.read(0x04000000,2)&16 else 0x06000000
        actual = self.e.bytes(page,38400)
        bad = [i for i,(a,b) in enumerate(zip(expected,actual)) if a!=b]
        self.oracle_results.append({'name':label, 'room':room, 'displayed_camera':[cx,cy], 'pixels_compared':38400,
                                    'mismatches':len(bad), 'first_mismatches':bad[:20],
                                    'actual_sha256':hashlib.sha256(actual).hexdigest(),
                                    'expected_sha256':hashlib.sha256(expected).hexdigest(),
                                    'oracle_kind':'Exact ROM backdrop plus explicit authored overlay; expected bitmap only is synthetic'})
        self.e.screenshot(self.out/(label+'.png'))
        self.check(not bad, label+' all240x160 native displayed BG pixels match exact ROM artwork and overlays')

    def tile_check(self, label):
        form = self.selected().form_id
        ids = list(self.e.bytes(self.sym['magma_creature_form_ids'],24))
        self.check(form in ids, 'native tile test observes an actually owned new companion')
        code = self.get('gfx_companion_frame')
        direction = code%16//4
        casting = code>=131072
        index = ids.index(form)
        pointer = self.sym['magma_creature_ability_frames']+((index*4+direction)*2+((code//262144)&1))*256 if casting else self.sym['magma_creature_direction_frames']+((index*4+direction)*4+code%4)*256
        expected = tiled(self.e.bytes(pointer,256))
        actual = self.e.bytes(0x06014000+6400,256)
        self.check(actual==expected, label+' companion OBJ tiles match exact selected form and authored pose')
        actors = []
        for slot in range(self.get('region_actor_cursor')):
            key = self.e.read(self.sym['region_actor_keys']+slot*4)
            if not 6144<=key<6208: continue
            offset = 8448+slot*256 if slot<8 else 10816+(slot-8)*256
            self.check(self.e.bytes(0x06014000+offset,256)==tiled(self.e.bytes(self.sym['magma_sprites']+(key-6144)*256,256)), label+' dynamic actor cache matches actual keyed ROM pixels')
            actors.append({'slot':slot, 'key':key})
        self.check(bool(actors), 'visible dynamic Magma actors were inspected')
        self.oracle_results.append({'name':label, 'selected_form':form, 'selected_instance_id':self.selected().instance_id,
                                    'companion_sha256':hashlib.sha256(actual).hexdigest(), 'casting':casting, 'actors':actors})

    def grabbing(self):
        self.restore('source-01-lift-entry')
        self.goto(144,258); self.step(24,'UP')
        self.check(self.get('py')>=242, 'ungrabbed physical town jar blocks ordinary walking')
        self.target(144,232)
        self.check(self.local('grab')==2, 'A grabs actual town jar')
        y = self.get('py')
        self.step(24,'RIGHT')
        self.check(self.local('lesson_x')==168 and self.get('py')==y, 'held direction performs only one discrete physical slide')
        self.step(4); self.tap('RIGHT'); self.settle()
        self.check(self.local('lesson_x')==192, 'fresh repeated direction edge performs second slide')
        self.tap('RIGHT'); self.settle()
        self.check(self.local('lesson_x')==192, 'boundary blocks further slide without moving object')
        self.tap('LEFT+RIGHT'); self.settle()
        self.check(self.local('lesson_x')==168, 'conflicting horizontal edges have deterministic single-direction priority')
        self.tap('UP+DOWN+RIGHT'); self.settle()
        self.check(self.local('lesson_x')==168, 'conflicting vertical edge is rejected without an accidental horizontal slide')
        self.check(self.fingerprint()==[38,168,0,0], 'real collision fingerprint tracks relocated physical object')
        x = self.get('px')
        self.step(1,'A+RIGHT')
        self.check(self.local('grab')==255 and self.local('lesson_x')==168 and self.get('px')==x, 'A cancel owns simultaneous direction without slipping or attacking')
        self.step(4); self.settle()
        self.goto(144,248); self.step(13,'UP')
        self.check(self.get('py')<242, 'vacated object location becomes genuinely traversable after cache synchronization')
        self.target(168,232); summoned = self.get('summoned')
        self.tap('B'); self.settle()
        self.check(self.local('grab')==255 and self.get('summoned')==summoned, 'B release does not also toggle the companion')
        self.target(168,232); self.tap('START',2,4)
        self.check(self.get('game_state')==PAUSE and self.local('grab')==2, 'journal safely pauses an active grab')
        self.tap('RIGHT'); self.tap('B'); self.settle()
        self.check(self.local('grab')==2 and self.local('lesson_x')==168, 'journal navigation and close do not leak into held object')
        self.tap('A'); self.settle()
        self.check(self.local('grab')==255, 'grab resumes and releases after journal close')
        self.snapshot('town-grab-boundaries')
        self.restore('source-03-intake-unsolved')
        self.target(48,68)
        self.check(self.local('grab')==0, 'A grabs actual room puzzle brick')
        before = self.puzzle()
        self.tap('LEFT'); self.settle()
        self.check(self.puzzle()==before, 'grid boundary rejects physical puzzle slide')
        self.step(24,'DOWN')
        self.check(self.puzzle()[0]==before[0]+7, 'held puzzle direction produces one real discrete grid movement')
        self.check(self.fingerprint()==[42,self.puzzle()[0],0,0], 'puzzle collision cache fingerprint follows actual shifted cell')
        position = (self.get('px'),self.get('py'))
        self.step(20,'L+RIGHT')
        self.check(self.local('grab')==0 and (self.get('px'),self.get('py'))==position, 'selector safely pauses movement while an actual puzzle object is grabbed')
        self.step(3); self.tap('B'); self.settle()
        self.check(self.local('grab')==255, 'puzzle B release recovers ordinary walking after selector')
        self.target(24,136,0)
        self.check(self.puzzle()==before, 'ordinary reset sign restores the unsolved physical puzzle configuration')
        self.leave_interior(39)
        self.snapshot('puzzle-grab-reset-escape')

    def modal_selector(self):
        self.restore('source-02-teaching-companions')
        self.entry(38); self.goto(240,232); self.select_form(31); self.ready(); self.step(3)
        self.tap('R',1,1)
        self.check(self.get('magma_power_time')>0, 'real owned teaching companion starts a native cast')
        before = (self.get('px'),self.get('py'),self.get('hp'),self.get('magma_power_time'),self.get('magma_power_age'),self.local('world_clock'))
        self.raw('new-companion-L-hold-pause',45,lambda i:'L+RIGHT')
        during = (self.get('px'),self.get('py'),self.get('hp'),self.get('magma_power_time'),self.get('magma_power_age'),self.local('world_clock'))
        self.check(during==before, 'L selector freezes hero health active cast age and region clock')
        self.raw('new-companion-L-release-resume',1)
        self.check(self.selected().form_id==34 and not self.get('quickparty_open'), 'L release selects second actual new companion')
        self.step(4); self.tile_check('new-companion-post-selector')
        self.check(self.get('magma_power_age')>before[4], 'original cast resumes after selector release')
        selected = self.selected().instance_id
        self.tap('L+UP+RIGHT',15,3)
        self.check(self.selected().instance_id==selected, 'conflicting L directions do not choose a phantom party slot')
        self.step(3,'L+UP'); self.tap('L+B',2,4)
        self.check(self.selected().instance_id==selected and not self.get('quickparty_open'), 'B cancels selector without committing tentative selection')
        self.step(3,'L+UP'); self.step(2,'L+START'); self.step(3)
        self.check(self.get('game_state')==PAUSE and not self.get('quickparty_open'), 'START transfers held selector safely into journal')
        self.close_menu(); self.step(120); self.ready()
        self.raw('all-nine-journal-first-open-change-close',120,
                 lambda i:'START' if i==0 else 'A' if i in (12,24,36,48,60,72,84,96) else 'B' if i==108 else 0)
        self.check(self.get('game_state')==PLAY and self.get('journal_tab')==8, 'every cold journal transition presents correctly and returns to field')
        for tab in range(9):
            self.open_tab(tab)
            frozen = (self.get('px'),self.get('py'),self.get('hp'),self.local('world_clock'))
            self.raw('native-journal-'+str(tab),16)
            self.check((self.get('px'),self.get('py'),self.get('hp'),self.local('world_clock'))==frozen, 'journal modal keeps simulation frozen')
            self.e.screenshot(self.out/f'journal-{tab}.png')
            self.close_menu(); self.step(3); self.tile_check('post-journal-'+str(tab))
        self.clean_bitmap('town-resume-clean-art')
        self.goto(260,248); self.step(140)
        for frame in range(5):
            self.step(1,'RIGHT+UP')
            self.clean_bitmap('native-scrolling-diagonal-'+str(frame),settle=False)
        self.goto(160,190); self.face(1); self.step(1,'A+R+L')
        self.check(self.get('quickparty_open') and self.get('game_state')==PLAY, 'selector owns simultaneous interaction and cast input')
        self.tap('L+B',2,4); self.step(3); self.tap('A',1,1)
        self.check(self.get('game_state')==DIALOG, 'ordinary town dialogue opens')
        frozen = (self.get('px'),self.get('py'),self.selected().instance_id,self.get('magma_power_time'),self.local('world_clock'))
        self.raw('dialogue-input-boundary',20,lambda i:'L+R+RIGHT+B+START')
        self.check(self.get('game_state')==DIALOG and (self.get('px'),self.get('py'),self.selected().instance_id,self.get('magma_power_time'),self.local('world_clock'))==frozen, 'dialogue consumes non-A gameplay and selector input')
        self.step(3); self.settle(); self.goto(112,264); self.face(1); self.step(1,'A')
        self.check(self.get('game_state')==SAVING, 'actual anchor interaction starts native incremental save')
        position = (self.get('px'),self.get('py'))
        selected = self.selected().instance_id
        row = self.raw('save-input-boundary',16,lambda i:'L+R+RIGHT+START+B')
        self.check(all(r['state']==SAVING for r in row['trace']), 'input boundary sample stays entirely inside actual save')
        self.check((self.get('px'),self.get('py'))==position and self.selected().instance_id==selected, 'save blocks hero and selection changes')
        self.step(3); self.settle(); self.check(self.get('game_state')==PLAY and not self.get('quickparty_open'), 'save completion resumes controllable field without stuck selector')
        self.snapshot('modal-selector-save-boundaries')

    def death_restart(self):
        self.restore('source-regulator-telegraph')
        self.goto(100,85)
        quests = bytes(self.state().quests)
        roster = bytes(self.roster())
        trace = []
        for _ in range(100):
            self.step(24)
            trace.append({'frame':self.e.frame,'hp':self.get('hp'),'state':self.get('game_state'),'stage':self.get('magma_game_machine_stage',1)})
            if self.get('game_state')==DEAD: break
        self.check(self.get('game_state')==DEAD and self.get('hp')==0, 'actual regulator hazard kills hero without injecting health')
        self.check(not self.get('magma_power_time') and self.local('grab')==255, 'death clears native cast and grab transient state')
        self.snapshot('actual-controller-death',settle=False)
        self.tap('A+R',1,1); self.settle()
        self.check(self.get('game_state')==PLAY and self.get('room')==45 and self.get('hp')>0, 'ordinary retry returns to same room with restored health')
        self.check(self.get('magma_game_machine_stage',1)==0 and not self.get('magma_power_time'), 'retry resets unsolved machine and consumes simultaneous cast')
        self.check(bytes(self.state().quests)==quests and bytes(self.roster())==roster, 'death and retry preserve earned quests and exact actual roster')
        self.leave_interior(44); self.entry(45)
        self.check(self.get('game_state')==PLAY, 'post-retry exit and reentry remain usable')
        self.case_results.append({'name':'actual-death-hazard-trace','trace':trace})
        self.snapshot('death-retry-exit-reentry')

    def room_exits_art(self):
        for name, destination in [('03-intake-unsolved',39),('05-vault-solved',42),('06-gallery-solved',43),('regulator-telegraph',44)]:
            self.restore('source-'+name)
            if self.get('room')!=45:
                self.clean_bitmap('native-room-'+str(self.get('room')))
                self.raw('room-'+str(self.get('room'))+'-idle',60)
            self.leave_interior(destination)
        self.restore('source-01-lift-entry'); self.entry(40)
        self.clean_bitmap('native-room-40'); self.raw('room-40-idle',60); self.leave_interior(38)
        self.restore('source-02-teaching-companions')
        self.clean_bitmap('native-room-39'); self.raw('room-39-active-enemies',60)
        self.entry(41); self.clean_bitmap('native-room-41'); self.raw('room-41-active-enemies',60); self.leave_interior(39)
        self.entry(38); self.entry(30)
        self.check(self.get('room')==30, 'all six interiors and old-region return have ordinary controller escapes')

    def sweep_pixels(self):
        self.restore('source-regulator-telegraph')
        self.goto(32,108)
        descriptor = self.descriptors[45]
        backdrop = self.e.bytes(descriptor['bitmap'],38400)
        def state():
            return {'stage':self.get('magma_game_machine_stage',1),'ticks':self.get('magma_game_machine_ticks',1),'lane':self.local('reg_lane')}
        def expected(row):
            image = bytearray(backdrop)
            y = 94 if row['lane'] else 76
            x = 48+(36-row['ticks'])*4
            for yy in range(y,y+18): image[yy*240+x:yy*240+x+12]=bytes([self.palette['PAL_ROSE4']])*12
            # Exact integer Bresenham used by native line(x,y,x+12,y+18).
            xx, yy, dx, dy, err = x, y, 12, -18, -6
            while True:
                image[yy*240+xx]=self.palette['PAL_GOLD4']
                if xx==x+12 and yy==y+18: break
                twice=2*err
                if twice>=dy: err+=dy;xx+=1
                if twice<=dx: err+=dx;yy+=1
            return bytes(image)
        for _ in range(500):
            row=state()
            if row['stage']==2 and 5<row['ticks']<32: break
            self.step(1)
        else: raise AssertionError('Native regulator never enters moving sweep')
        trace=[]
        last=self.get('frame');page=self.e.read(0x04000000,2)&16
        for _ in range(20):
            before=state();self.step(1);after=state()
            self.check(before['stage']==after['stage']==2, 'sweep pixel sample remains in moving stage')
            actual=self.e.bytes(0x0600a000 if self.e.read(0x04000000,2)&16 else 0x06000000,38400)
            indices=[y*240+x for y in range(76,113) for x in range(48,205)]
            mismatch=[sum(actual[i]!=oracle[i] for i in indices) for oracle in (expected(before),expected(after))]
            now=self.get('frame');np=self.e.read(0x04000000,2)&16
            trace.append({'before':before,'after':after,'mismatches_before_after':mismatch,'native_frame':self.e.frame,
                          'update_delta':(now-last)&0xffffffff,'flip':np!=page,'cycles':self.get('render_cycles')})
            last,page=now,np
        self.oracle_results.append({'name':'regulator-moving-sweep-pixels','trace':trace,'pixels_each_frame':5809,
                                    'boundary_policy':'Displayed pixels must equal exact current or one in-flight previous hardware-update position'})
        self.e.screenshot(self.out/'regulator-moving-sweep.png')
        self.report()
        self.check(all(min(r['mismatches_before_after'])==0 for r in trace), 'displayed sweep bitmap follows every physical hazard position without stale cached trail')
        self.check(all(r['update_delta']==1 and r['flip'] and r['cycles']<280896 for r in trace), 'moving sweep cold redraw updates and flips each hardware frame within cycle budget')

    def run(self, only=None):
        for name, method in [('grabbing',self.grabbing),('modal-selector',self.modal_selector),('death-restart',self.death_restart),('room-exits-art',self.room_exits_art),('sweep-pixels',self.sweep_pixels)]:
            if only and name!=only: continue
            try:
                method()
                self.case_results.append({'name':name,'passed':True})
            except Exception as exc:
                self.failures.append({'case':name,'error':str(exc),'status':self.status()})
                self.case_results.append({'name':name,'passed':False})
                self.snapshot('failure-'+name,settle=False)
            self.report()
        self.completed=not self.failures
        self.report()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','symbols','output','source-report'):
        parser.add_argument('--'+key,type=Path,required=True)
    for key in ('expected-rom-sha','expected-symbols-sha'):
        parser.add_argument('--'+key,required=True)
    parser.add_argument('--source-manifest',type=Path)
    parser.add_argument('--only')
    a=parser.parse_args()
    run=MagmaControls(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,source_report=a.source_report,source_manifest=a.source_manifest)
    try: run.run(a.only)
    finally: run.report();run.e.close()
    print(json.dumps({'completed':run.completed,'checks':len(run.checks),'failures':run.failures,'report_sha256':digest(run.out/'magma-controls.json')}))
    return bool(run.failures)

if __name__=='__main__':
    raise SystemExit(main())
