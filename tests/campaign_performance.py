#!/usr/bin/env python3
"""Independent real-ROM campaign cadence and hardware-cycle stress measurements.

Consumes campaign_tests.py's controller-only snapshot manifest. It copies the ROM,
matching symbols and used snapshots, checks their hashes, then uses GBA buttons
and read-only memory observations exclusively. No game-RAM writes, save fixtures,
host FPS, patched ROMs, or fabricated progress are used. All measurements reject
unexpected state/room/phase changes and death, including a death on the last frame.

Example: python3 tests/campaign_performance.py --campaign build/campaign-qa/campaign-report.json
Incomplete manifests are useful for development, but cannot earn a full-coverage
pass. Use --allow-partial only to suppress a missing-coverage exit status.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from mgba_runner import Emulator

CLOCK = 16777216
CYCLES = 280896
HZ = CLOCK / CYCLES
PLAY, DIALOG, PAUSE, DEAD, WIN = 1, 2, 3, 4, 5
POWERS = ('homura', 'midori', 'fuuri', 'kohaku')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def distribution(values):
    if not values:
        return None
    s = sorted(values)
    return {'samples': len(s), 'min': s[0], 'median': s[len(s)//2],
            'p95': s[int((len(s)-1)*.95)], 'max': s[-1],
            'max_fraction_of_frame': s[-1]/CYCLES}


class CampaignPerformance:
    fields = ('game_state', 'room', 'px', 'py', 'hp', 'max_hp', 'spirit',
              'summoned', 'room_flags', 'chapter_flags', 'optional_flags',
              'story_seen', 'bridge_open', 'torches', 'boss_hp', 'boss_armor',
              'boss_state', 'boss_phase', 'boss_state_ticks', 'boss_pattern',
              'hazard_mode', 'power_effect', 'ability_cd', 'heal_cd', 'stone_guard',
              'camera_x', 'camera_y', 'roll_ticks', 'roll_cd', 'swing', 'toast_ticks',
              'dpage', 'dcount', 'journal_tab', 'frame', 'render_cycles',
              'worst_render_cycles', 'obj_count', 'deaths')
    aliases = {'boss_timer': 'boss_state_ticks', 'guard_ticks': 'stone_guard'}

    def __init__(self, campaigns, output, frames=360):
        self.out = Path(output).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.frames = frames
        self.sources, self.snapshots, self.scene_results = [], {}, []
        self.transitions = []
        self.failures, self.missing, self.inputs = [], [], []
        self.covered = Counter()
        self.feature_cycles = defaultdict(list)
        self.current_snapshot = None
        self.e = None
        self.expected_hash = self.expected_symbols = None
        for index, file in enumerate(campaigns):
            file = Path(file).resolve()
            manifest = json.loads(file.read_text())
            if manifest.get('controller_only') is not True or manifest.get('game_ram_writes') != 0:
                raise AssertionError(f'Manifest is not controller-only: {file}')
            rom, symbols = file.parent/'tested.gba', file.parent/'tested.sym'
            digest, symbol_digest = sha(rom), sha(symbols)
            if digest != manifest['rom_sha256'] or symbol_digest != manifest['symbol_sha256']:
                raise AssertionError(f'Manifest ROM/symbol digest mismatch: {file}')
            if self.expected_hash and (digest != self.expected_hash or symbol_digest != self.expected_symbols):
                raise AssertionError('Cannot mix snapshots from different ROM/symbol builds')
            self.expected_hash, self.expected_symbols = digest, symbol_digest
            if index == 0:
                self.rom, self.symbols = self.out/'tested.gba', self.out/'tested.sym'
                for source, target in ((rom,self.rom),(symbols,self.symbols)):
                    if target.exists() and sha(target) != sha(source):
                        raise AssertionError(f'Refusing to replace another tested build: {target}')
                    if source != target:
                        target.write_bytes(source.read_bytes())
            copy = self.out/f'controller-manifest-{index}.json'
            copy.write_bytes(file.read_bytes())
            self.sources.append({'manifest': str(file), 'sha256': sha(file),
                                 'copy': copy.name, 'campaign_failures': manifest.get('failures', [])})
            for name, snap in manifest['snapshots'].items():
                if snap.get('provenance') != 'controller-reached; no game RAM writes':
                    raise AssertionError(f'Untrusted snapshot provenance: {name}')
                snap = dict(snap, manifest_index=index)
                self.snapshots[name] = snap
        self.sym = {words[2]:int(words[0],16) for line in self.symbols.read_text().splitlines()
                    if len(words := line.split()) == 3}
        required = ('game_state','room','hp','frame','render_cycles','worst_render_cycles','shots')
        if any(n not in self.sym for n in required):
            raise AssertionError('Missing instrumentation symbols')
        self.used = {}

    def get(self, name):
        return self.e.read(self.sym[self.aliases.get(name,name)])

    def status(self):
        return {n:self.get(n) for n in self.fields if n in self.sym}

    def check_context(self, expected):
        s = self.status()
        errors = [f'{k}: expected {v}, observed {s.get(k)}' for k,v in expected.items() if s.get(k) != v]
        if expected.get('game_state') == PLAY and s.get('hp',0) <= 0:
            errors.append('player died')
        if s.get('game_state') == DEAD:
            errors.append('death screen cannot stand in for gameplay')
        if 'save_failed' in self.sym and self.get('save_failed'):
            errors.append('engine save_failed flag')
        if errors:
            raise AssertionError('; '.join(errors))
        return s

    def load(self, name):
        snap = self.snapshots[name]
        source = Path(snap['path'])
        target = self.out/'snapshots'/source.name
        target.parent.mkdir(exist_ok=True)
        digest = sha(source)
        if target.exists() and sha(target) != digest:
            raise AssertionError(f'Conflicting snapshot contents: {name}')
        target.write_bytes(source.read_bytes())
        sram_info=None
        if snap.get('sram_path'):
            sram_source=Path(snap['sram_path'])
            sram_target=target.with_suffix(target.suffix+'.sav')
            sram_target.write_bytes(sram_source.read_bytes())
            self.e.load_save(sram_target)
            sram_info={'sha256':sha(sram_target),'file':str(sram_target.relative_to(self.out)),
                       'source':str(sram_source)}
        self.e.state(target, load=True)
        # Compare every directly observable field in the controller manifest.
        for key,value in snap['status'].items():
            symbol = self.aliases.get(key,key)
            if symbol in self.sym and self.get(symbol) != value:
                raise AssertionError(f'Snapshot {name} failed readback for {key}')
        self.used[name] = {'sha256':digest, 'file':str(target.relative_to(self.out)),
                           'source':str(source), 'manifest_index':snap['manifest_index'],
                           'status':snap['status'],'paired_sram':sram_info}
        self.current_snapshot = name
        return self.status()

    def step(self, frames, keys=0):
        if frames < 1:
            return
        self.inputs.append({'snapshot':self.current_snapshot,'emulator_frame':self.e.frame,
                            'frames':frames,'keys':keys})
        self.e.frames(frames, keys)

    def tap(self, keys, hold=2, release=2):
        self.step(hold,keys)
        self.step(release)

    def goto(self, x=None, y=None):
        expected = {'game_state':PLAY,'room':self.get('room')}
        for field,target,low,high in (('px',x,'LEFT','RIGHT'),('py',y,'UP','DOWN')):
            if target is None:
                continue
            stuck = 0
            for _ in range(700):
                current = self.get(field)
                if abs(current-target) <= 1:
                    break
                self.check_context(expected)
                self.step(1,low if current>target else high)
                stuck = stuck+1 if self.get(field)==current else 0
                if stuck>12:
                    raise AssertionError(f'Controller setup blocked at {field}={current}, target={target}')
            else:
                raise AssertionError('Controller setup exhausted')
        self.check_context(expected)

    def select(self, power):
        for _ in range(5):
            if self.get('spirit') == power:
                break
            self.tap('L')
        if self.get('spirit') != power:
            raise AssertionError(f'Companion {power} not unlocked in fixture')
        if not self.get('summoned'):
            self.tap('B')
        self.step(self.get('ability_cd')+2)

    def features(self, s, shots, enemy_shots, player_shots):
        labels = [f'room-{s["room"]}',f'game-state-{s["game_state"]}']
        for field in ('summoned','roll_ticks','swing','toast_ticks','power_effect','stone_guard'):
            if s.get(field):
                labels.append(field)
        if shots:
            labels.append('projectiles')
        if enemy_shots:
            labels.append('enemy-projectiles')
        if player_shots:
            labels.append('player-projectiles')
        if s['game_state']==PAUSE:
            labels.append(f'journal-tab-{s["journal_tab"]}')
            if s['journal_tab']==2:
                labels.append('journal-selected-'+POWERS[s['spirit']])
        if s['game_state']==PLAY and s.get('summoned'):
            labels.append('companion-'+POWERS[s['spirit']])
            if s.get('ability_cd'):
                labels.append('ability-'+POWERS[s['spirit']])
        if s['room'] in (8,13) and s['game_state']==PLAY:
            prefix = f'boss-{s["room"]}-phase-{s["boss_phase"]}'
            labels.append(prefix+f'-state-{s["boss_state"]}')
            if s.get('hazard_mode'):
                labels.append(prefix+f'-hazard-{s["hazard_mode"]}')
            if enemy_shots:
                labels.append(prefix+'-projectiles')
            if s['room']==8 and 0<s['boss_hp']<=10:
                labels.append('kazane-enraged')
                if enemy_shots>=6:
                    labels.append('kazane-six-projectiles')
        return labels

    def measure(self, name, *, frames=None, control=None, interval=1, expected=None, requirements=()):
        frames = frames or self.frames
        initial = self.status()
        expected = expected or {'game_state':initial['game_state'],'room':initial['room']}
        if initial['room'] in (8,13) and initial['game_state']==PLAY:
            expected.setdefault('boss_phase', initial['boss_phase'])
        self.check_context(expected)
        self.e.screenshot(self.out/f'{name}-start.png')
        last = self.get('frame')
        page = self.e.read(0x04000000,2)&16
        first_frame = self.e.frame
        rows, events, flips = [], [], []
        activity, states = Counter(), Counter()
        cycles, scene_features = [], set()
        feature_screenshots = {}
        max_cycle = -1
        longest_stall = stall = 0
        invalid = None
        prior_camera = initial.get('camera_x',0),initial.get('camera_y',0)
        camera_changes = 0
        for n in range(frames):
            self.step(1,control(n) if control else 0)
            s = self.status()
            current = s['frame']
            delta = (current-last)&0xffffffff
            last = current
            current_page = self.e.read(0x04000000,2)&16
            flip = current_page!=page
            page=current_page
            if delta:
                events.append(n+1)
                stall=0
            else:
                stall+=1
                longest_stall=max(longest_stall,stall)
            if flip:
                flips.append(n+1)
            shots = [i for i in range(12) if self.e.read(self.sym['shots']+i*24+16)]
            enemy_shots = sum(bool(self.e.read(self.sym['shots']+i*24+20)) for i in shots)
            labels = self.features(s,len(shots),enemy_shots,len(shots)-enemy_shots)
            cx,cy = s.get('camera_x',0),s.get('camera_y',0)
            if (cx,cy)!=prior_camera:
                labels.append('camera-moving')
                camera_changes+=1
            prior_camera=(cx,cy)
            cycle=s['render_cycles']
            cycles.append(cycle)
            states[f'{s["game_state"]}:{s["room"]}:{s.get("boss_phase",0)}']+=1
            try:
                self.check_context(expected)
                if delta>16:
                    raise AssertionError('frame counter reset or unexpected update burst')
            except AssertionError as exc:
                invalid=str(exc)
            for label in labels:
                activity[label]+=1
                if activity[label] in (1,3) and ('boss-' in label or 'ability-' in label or label=='kazane-six-projectiles'):
                    file=f'{name}-{label}.png'
                    self.e.screenshot(self.out/file)
                    feature_screenshots[label]={'file':file,'hardware_frame_offset':n+1,'status':s}
                scene_features.add(label)
            if cycle>max_cycle:
                max_cycle=cycle
                self.e.screenshot(self.out/f'{name}-peak-cycles.png')
            rows.append({'offset':n+1,'update_delta':delta,'page_flip':flip,
                         'cycles':cycle,'state':s['game_state'],'room':s['room'],
                         'boss_phase':s.get('boss_phase'),'boss_state':s.get('boss_state'),
                         'hazard':s.get('hazard_mode'),'hp':s['hp'],'shots':len(shots),
                         'enemy_shots':enemy_shots,'objects':s.get('obj_count'),
                         'camera':[cx,cy],'features':labels})
            if invalid:
                break
        count=len(rows)
        intervals=[b-a for a,b in zip(events,events[1:])]
        present_intervals=[b-a for a,b in zip(flips,flips[1:])]
        deltas=[r['update_delta'] for r in rows]
        update_met=(sum(deltas)>=count//interval and max(intervals,default=count)<=interval and longest_stall<interval)
        flip_met=(len(flips)>=count//interval and max(present_intervals,default=count)<=interval)
        missing=[r for r in requirements if not activity[r]]
        elapsed=self.e.frame-first_frame
        met=(invalid is None and count==frames and elapsed==count and update_met and flip_met and max_cycle<=CYCLES and not missing)
        result={'scene':name,'snapshot':self.current_snapshot,'initial':initial,'final':self.status(),
                'expected_context':expected,'requested_frames':frames,'measured_frames':count,
                'emulated_frames_elapsed':elapsed,'updates':sum(deltas),
                'updates_per_emulated_second':sum(deltas)/count*HZ,
                'presentations':len(flips),'presentations_per_emulated_second':len(flips)/count*HZ,
                'update_delta_histogram':dict(Counter(deltas)),
                'update_interval_hardware_frames':dict(Counter(intervals)),
                'page_flip_interval_hardware_frames':dict(Counter(present_intervals)),
                'longest_stall_hardware_frames':longest_stall,'render_cycles':distribution(cycles),
                'engine_worst_before':initial['worst_render_cycles'],
                'engine_worst_after':self.get('worst_render_cycles'),
                'peak_projectiles':max(r['shots'] for r in rows),
                'peak_objects':max((r['objects'] or 0) for r in rows),
                'camera_changes':camera_changes,
                'camera_x_range':[min(r['camera'][0] for r in rows),max(r['camera'][0] for r in rows)],
                'camera_y_range':[min(r['camera'][1] for r in rows),max(r['camera'][1] for r in rows)],
                'activity_hardware_frames':dict(activity),'observed_contexts':dict(states),
                'scene_stayed_valid':invalid is None,'invalid_reason':invalid,
                'missing_scene_requirements':missing,
                'target':{'max_interval_hardware_frames':interval,'cycle_budget':CYCLES,'met':met},
                'trace':f'{name}-frames.json','feature_screenshots':feature_screenshots}
        (self.out/result['trace']).write_text(json.dumps(rows,indent=2)+'\n')
        self.e.screenshot(self.out/f'{name}-end.png')
        self.scene_results.append(result)
        if met:
            self.covered.update(activity)
            for row in rows:
                for label in row['features']:
                    self.feature_cycles[label].append(row['cycles'])
        else:
            self.failures.append({'scene':name,'invalid':invalid,'missing_features':missing,
                                  'update_met':update_met,'page_flip_met':flip_met,
                                  'cycle_budget_met':max_cycle<=CYCLES,'emulated_frame_count_matches':elapsed==count})
        print(f'{"PASS" if met else "FAIL"} {name}: updates {sum(deltas)}/{count}, '
              f'flips {len(flips)}/{count}, peak {max_cycle} cycles ({max_cycle/CYCLES:.1%}), '
              f'valid={invalid is None}'+(f'; {invalid}' if invalid else ''),flush=True)
        self.write_report()
        return result

    def attempt(self, name, callback):
        try:
            callback()
        except Exception as exc:
            self.failures.append({'setup':name,'error':str(exc),'status':self.status()})
            self.e.screenshot(self.out/f'{name}-setup-failure.png')
            print(f'FAIL setup {name}: {exc}',flush=True)
            self.write_report()

    def fixture(self, name, callback):
        if name not in self.snapshots:
            self.missing.append(name)
            return
        self.attempt(name,lambda:(self.load(name),callback()))

    def room_case(self, snapshot, room):
        def capture():
            # A at the patrol entrance reads its sign instead of swinging.
            if room==6:
                self.goto(x=180)
            self.measure(f'room-{room}-active',
                control=(lambda n: 'A' if n%30<2 else 0) if room==6 else None,
                expected={'game_state':PLAY,'room':room})
        self.fixture(snapshot,capture)

    def grove_case(self, direction):
        self.load('grove-south-entry')
        # Keep sword presses outside the newly authored hearth interaction radius.
        # The same diagonal scrolling/combat workload is retained.
        self.goto(y=228 if direction=='diagonal' else 248)
        self.select(0)
        self.step(2,'UP')
        def control(n):
            key={'horizontal':('RIGHT','LEFT'),'vertical':('UP','DOWN'),
                 'diagonal':('UP+RIGHT','DOWN+LEFT'),'roll':('RIGHT','LEFT')}[direction][(n//48)%2]
            if n%30<2:
                key+='+A'
            if n%96==4:
                key+='+R'
            if direction=='roll' and n%48==0:
                key+='+SELECT'
            return key
        requirements=['camera-moving','summoned','swing','player-projectiles']
        if direction=='roll':
            requirements.append('roll_ticks')
        self.measure('grove-'+direction,control=control,
                     expected={'game_state':PLAY,'room':1},requirements=requirements)

    def transition(self, name, target_state, key=0, duration=60):
        """Expose cold-cache cost separately from sustained scene throughput."""
        initial=self.status()
        previous=initial['frame']
        page=self.e.read(0x04000000,2)&16
        rows=[]
        reached=None
        invalid=None
        events=[]
        flips=[]
        worst=0
        for n in range(duration):
            self.step(1,key if n<2 else 0)
            s=self.status()
            delta=(s['frame']-previous)&0xffffffff
            previous=s['frame']
            now=self.e.read(0x04000000,2)&16
            flip=now!=page
            page=now
            if delta:events.append(n+1)
            if flip:flips.append(n+1)
            if s['game_state']==target_state and reached is None:reached=n+1
            if s['game_state']==DEAD or s['room']!=initial['room']:
                invalid='death or unexpected room transition'
            if reached is not None and s['game_state']!=target_state:
                invalid='left expected UI state after reaching it'
            if s['render_cycles']>worst:
                worst=s['render_cycles']
                self.e.screenshot(self.out/f'{name}-peak-cycles.png')
            rows.append({'offset':n+1,'update_delta':delta,'page_flip':flip,
                         'cycles':s['render_cycles'],'game_state':s['game_state']})
            if invalid:break
        gaps=[b-a for a,b in zip(events,events[1:])]
        pgaps=[b-a for a,b in zip(flips,flips[1:])]
        # UI input/first-paint has an explicit two-frame budget. The report also
        # exposes every single-frame overrun rather than calling it steady 60 Hz.
        met=(invalid is None and reached is not None and reached<=2
             and max(gaps,default=duration)<=2 and max(pgaps,default=duration)<=2
             and worst<=CYCLES*2)
        result={'transition':name,'snapshot':self.current_snapshot,'initial':initial,
                'final':self.status(),'controller_key':key,'hardware_frames':len(rows),
                'first_target_state_frame':reached,'updates':sum(r['update_delta'] for r in rows),
                'page_flips':len(flips),'update_intervals':dict(Counter(gaps)),
                'page_flip_intervals':dict(Counter(pgaps)),
                'render_cycles':distribution([r['cycles'] for r in rows]),
                'exceeds_single_frame_cycle_budget':worst>CYCLES,
                'strict_one_update_and_present_per_frame':invalid is None and all(r['update_delta']==1 and r['page_flip'] for r in rows),
                'strict_one_frame_cycle_budget':worst<=CYCLES,
                'invalid_reason':invalid,
                'target':{'input_latency_frames':2,'max_interval_frames':2,
                          'cycle_budget':CYCLES*2,'met':met},'trace':f'{name}-frames.json'}
        (self.out/result['trace']).write_text(json.dumps(rows,indent=2)+'\n')
        self.transitions.append(result)
        if not met:self.failures.append({'transition':name,'invalid':invalid,'peak_cycles':worst})
        print(f'{"PASS" if met else "FAIL"} transition {name}: latency={reached}, '
              f'peak={worst} cycles ({worst/CYCLES:.1%} of one frame), '
              f'updates={result["updates"]}/{len(rows)}, flips={len(flips)}/{len(rows)}, '
              f'strict60={result["strict_one_update_and_present_per_frame"] and result["strict_one_frame_cycle_budget"]}',flush=True)
        self.write_report()
        if invalid or reached is None:
            raise AssertionError(invalid or 'UI transition did not reach target')

    def menu_case(self, snapshot, name, map_view=False):
        self.load(snapshot)
        self.transition(name+'-open',PAUSE,'START')
        if map_view and self.get('journal_tab')!=1:
            self.transition(name+'-switch-tab',PAUSE,'A')
        if not map_view and self.get('journal_tab')!=0:
            self.transition(name+'-switch-tab',PAUSE,'A')
        self.measure(name,expected={'game_state':PAUSE,'room':self.get('room')})
        if snapshot=='four-lights-menu-start':
            self.transition(name+'-route-map-open',PAUSE,'A')
            self.measure(name+'-route-map',expected={'game_state':PAUSE,'room':self.get('room'),'journal_tab':1})
            self.transition(name+'-companion-panel-open',PAUSE,'A')
            self.measure(name+'-companion-panel',expected={'game_state':PAUSE,'room':self.get('room'),'journal_tab':2})
            for i in range(4):
                self.transition(name+f'-cycle-companion-{i}',PAUSE,'L')
                self.measure(name+f'-companion-{self.get("spirit")}',
                    expected={'game_state':PAUSE,'room':self.get('room'),'journal_tab':2,'spirit':self.get('spirit')})
        self.transition(name+'-close',PLAY,'B')

    def dialog_case(self,label):
        self.transition('dialog-'+label+'-cold',DIALOG)
        self.measure('dialog-'+label,expected={'game_state':DIALOG,'room':self.get('room'),'dpage':self.get('dpage')})

    def power_case(self,power,snapshot):
        self.load(snapshot)
        if self.get('room')==12:
            self.goto(x=80,y=112)
        self.select(power)
        def control(n):
            keys=[]
            if n%90<2:keys.append('R')
            if n%30==5:keys.append('A')
            return '+'.join(keys) if keys else 0
        required=['ability-'+POWERS[power],'summoned','swing']
        if power==0:required.append('player-projectiles')
        if power==2:required.append('power_effect')
        if power==3:required.append('stone_guard')
        self.measure('power-'+POWERS[power],control=control,
                     expected={'game_state':PLAY,'room':self.get('room'),'spirit':power},requirements=required)

    def boss_case(self,room,phase,state):
        snapshot=f'boss-{room}-phase-{phase}-state-{state}'
        self.load(snapshot)
        # No sword input: the initial boss phase must remain the measured phase.
        # Exposure windows are measured before their natural timeout.
        length=min(120,max(16,174-self.get('boss_state_ticks'))) if state==5 else self.frames
        self.measure(f'boss-{room}-phase-{phase}-from-{state}',frames=length,
                     expected={'game_state':PLAY,'room':room,'boss_phase':phase},
                     requirements=[f'boss-{room}-phase-{phase}-state-{state}'])

    def run(self):
        self.e=Emulator(self.rom)
        for snapshot,label in [('title','title'),('intro','intro-dialog'),
                               ('final-card','final-card')]:
            if snapshot in self.snapshots:
                self.fixture(snapshot,lambda label=label:self.measure(label,interval=2))
        self.fixture('village-menu-start',lambda:self.measure('village-active'))
        for snapshot,label,map_view in [('village-menu-start','village-journal',False),
                ('grove-south-entry','grove-map',True),('kazane-menu-start','kazane-journal',False),
                ('four-lights-menu-start','four-lights-journal',False),
                ('closed-core-menu-start','core-journal',False),
                ('peaceful-village-menu-start','postgame-journal',False)]:
            if snapshot in self.snapshots:
                self.attempt(label,lambda s=snapshot,l=label,m=map_view:self.menu_case(s,l,m))
            else:self.missing.append(snapshot)
        if 'grove-south-entry' in self.snapshots:
            for direction in ('horizontal','vertical','diagonal','roll'):
                self.attempt('grove-'+direction,lambda d=direction:self.grove_case(d))
        for name in ('original-shrine-before-natural-death','original-shrine-roundtrip'):
            if name in self.snapshots:
                self.room_case(name,2)
                break
        self.fixture('grove-boss-entry',lambda:self.measure('original-guardian-active',
            frames=180,control=lambda n: ('LEFT' if (n//48)%2 else 'RIGHT'),
            expected={'game_state':PLAY,'room':3}))
        for snapshot,room in [('sky-path-entry',4),('sky-vanes-entry',5),
                             ('sky-patrol-entry',6),('relay-entry',7),
                             ('core-path-entry',9),('weights-entry',10),
                             ('roots-entry',11),('sockets-entry',12)]:
            self.room_case(snapshot,room)
        for room in (8,13):
            for phase in ((0,) if room==8 else (0,1,2)):
                for state in ((0,1,2,3,4,5) if room==8 else (0,4,5)):
                    name=f'boss-{room}-phase-{phase}-state-{state}'
                    if name in self.snapshots:
                        self.attempt(name,lambda r=room,p=phase,s=state:self.boss_case(r,p,s))
                    else:self.missing.append(name)
        self.fixture('kazane-enraged-aim',lambda:self.measure('kazane-enraged-cycle',
            control=lambda n: ('RIGHT' if (n//48)%2==0 else 'LEFT')+('+SELECT' if n%48==0 else ''),
            expected={'game_state':PLAY,'room':8,'boss_phase':0},
            requirements=['kazane-enraged','kazane-six-projectiles']))
        power_snapshot=next((n for n in ('four-lights-stable-cadence','four-lights-menu-start',
                            'peaceful-village-menu-start') if n in self.snapshots),None)
        if power_snapshot:
            for power in range(4):
                self.attempt('power-'+POWERS[power],lambda p=power:self.power_case(p,power_snapshot))
        else:self.missing.append('all-four-powers-fixture')
        dialogs=[name for name,s in self.snapshots.items() if s['status']['game_state']==DIALOG]
        # Each distinct requested chapter/reward dialog family, including all ending pages.
        selected={}
        for name in dialogs:
            family=re.sub(r'-page-\d+$','',name)
            if family=='ending' or family not in selected:
                selected[name if family=='ending' else family]=name
        for label,snapshot in selected.items():
            self.fixture(snapshot,lambda l=label:self.dialog_case(l))
        if 'finished-ending-before-reload' in self.snapshots:
            self.fixture('finished-ending-before-reload',lambda:self.measure('ending-final-card',interval=2,
                         expected={'game_state':WIN,'room':0}))
        self.write_report()

    def coverage(self):
        needed=[f'room-{room}' for room in range(14)]
        needed+=['game-state-0','game-state-2','game-state-3','game-state-5','camera-moving']
        needed+=['ability-'+p for p in POWERS]
        needed+=[f'journal-tab-{tab}' for tab in range(3)]
        needed+=['journal-selected-'+p for p in POWERS]
        needed+=[f'boss-8-phase-0-state-{s}' for s in range(6)]+['boss-8-phase-0-projectiles']
        for phase,modes in [(0,(1,2,3,4)),(1,(5,)),(2,(1,2,3,4,6,7))]:
            needed += [f'boss-13-phase-{phase}-state-{s}' for s in (0,4,5)]
            needed += [f'boss-13-phase-{phase}-hazard-{mode}' for mode in modes]
        needed+=['boss-13-phase-1-projectiles','kazane-enraged','kazane-six-projectiles']
        return {'required':needed,'observed_hardware_frames':dict(self.covered),
                'missing':[name for name in needed if not self.covered[name]]}

    def write_report(self):
        if sha(self.rom)!=self.expected_hash or sha(self.symbols)!=self.expected_symbols:
            raise AssertionError('Immutable tested ROM or symbols changed during measurement')
        coverage=self.coverage()
        report={'rom_sha256':self.expected_hash,'symbols_sha256':self.expected_symbols,
                'rom_file':'tested.gba','symbols_file':'tested.sym','rom_bytes':self.rom.stat().st_size,
                'emulator':'mGBA 0.10.5 via tools/mgba_runner.py','gba_clock_hz':CLOCK,
                'hardware_cycles_per_frame':CYCLES,'hardware_refresh_hz':HZ,
                'controller_only':True,'game_ram_writes':0,'host_fps_used':False,
                'method':'Sample frame counter, DISPCNT bitmap-page bit, and hardware Timer 2/3 instrumentation after each emulated GBA frame.',
                'cycle_scope':'Input, update, and render. Excludes VBlank wait and OAM commit; page-flip cadence independently checks presentation.',
                'cycle_sampling_caveat':'Last completed timing value is read once per hardware frame; long work may repeat the previous sample. Feature classification is read-after-frame and can be offset from the timing sample at transitions.',
                'scope':'Representative controller-reached stress windows, not an exhaustive all-frame maximum or physical-hardware verification.',
                'manifests':self.sources,'used_snapshots':self.used,
                'failures':self.failures,'unavailable_fixtures':sorted(set(self.missing)),
                'strict_cold_failures':[t['transition'] for t in self.transitions if not t['strict_one_update_and_present_per_frame'] or not t['strict_one_frame_cycle_budget']],
                'coverage':coverage,'all_measured_targets_met':bool(self.scene_results) and not self.failures,
                'complete_coverage_pass':bool(self.scene_results) and not self.failures and not coverage['missing'],
                'all_cold_transitions_strict_one_frame':bool(self.transitions) and all(t['strict_one_update_and_present_per_frame'] and t['strict_one_frame_cycle_budget'] for t in self.transitions),
                'full_strict_60hz_pass':bool(self.scene_results) and not self.failures and not coverage['missing'] and bool(self.transitions) and all(t['strict_one_update_and_present_per_frame'] and t['strict_one_frame_cycle_budget'] for t in self.transitions),
                'feature_cycles':{k:distribution(v) for k,v in self.feature_cycles.items()},
                'transitions':self.transitions,'scenes':self.scene_results}
        (self.out/'campaign-performance.json').write_text(json.dumps(report,indent=2)+'\n')
        (self.out/'performance-controller-inputs.json').write_text(json.dumps(self.inputs,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',type=Path,action='append',required=True,help='Controller QA manifest; repeat to merge same-build sources')
    parser.add_argument('--output',type=Path,default=ROOT/'build/campaign-performance')
    parser.add_argument('--frames',type=int,default=360)
    parser.add_argument('--allow-partial',action='store_true')
    parser.add_argument('--strict-cold',action='store_true',help='Also fail any cold UI update/page-flip skip or one-frame cycle-budget overrun')
    args=parser.parse_args()
    if args.frames<180:
        parser.error('--frames must be at least 180')
    run=CampaignPerformance(args.campaign,args.output,args.frames)
    try:
        run.run()
    finally:
        run.write_report()
        if run.e:run.e.close()
    print(json.dumps({'failures':len(run.failures),'strict_cold_failures':[t['transition'] for t in run.transitions if not t['strict_one_update_and_present_per_frame'] or not t['strict_one_frame_cycle_budget']],'missing_coverage':run.coverage()['missing']},indent=2),flush=True)
    return int(bool(run.failures) or (bool(run.coverage()['missing']) and not args.allow_partial)
               or (args.strict_cold and any(not t['strict_one_update_and_present_per_frame'] or not t['strict_one_frame_cycle_budget'] for t in run.transitions)))


if __name__=='__main__':
    raise SystemExit(main())
