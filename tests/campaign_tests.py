#!/usr/bin/env python3
"""Controller-only QA of the complete fourteen-room Emberbond ROM.

The test never writes game RAM. Symbol reads observe the real ARM program, and
savestates only branch from positions reached with GBA buttons. Cartridge save
reloads use independent mGBA instances. Legacy/corruption fixtures are explicitly
separate from normal gameplay, and the report records their provenance.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
from itertools import permutations
import hashlib
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from mgba_runner import Emulator

PLAY, DIALOG, PAUSE, DEAD, WIN = 1, 2, 3, 4, 5
POWER = {'HOMURA': 0, 'MIDORI': 1, 'FUURI': 2, 'KOHAKU': 3}
CHAPTER = {'GROVE_CLEAR': 1, 'SKY_CLEAR': 2, 'CORE_CLEAR': 4, 'ENDING_SEEN': 8}
CYCLES_PER_FRAME = 280896
REFRESH_HZ = 16777216 / CYCLES_PER_FRAME


def read_symbols(path):
    return {w[2]: int(w[0], 16) for line in Path(path).read_text().splitlines()
            if len(w := line.split()) == 3}


class CampaignRun:
    def __init__(self, rom, symbols, output, optional=False, exhaustive=True):
        self.out = Path(output).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.source_rom = Path(rom).resolve()
        self.rom = self.out / 'tested.gba'
        self.rom.write_bytes(self.source_rom.read_bytes())
        self.symbol_path = self.out / 'tested.sym'
        self.symbol_path.write_bytes(Path(symbols).read_bytes())
        self.sym = read_symbols(self.symbol_path)
        self.e = Emulator(self.rom)
        candidate=self.e.read(self.sym['ui_texts']+8)
        self.ui_stride=16 if 0x08000000<=candidate<0x0a000000 else 8
        self.optional = optional
        self.exhaustive = exhaustive
        self.spec = json.loads((ROOT/'assets/campaign_layouts.json').read_text())
        self.rooms = {r['id']: r for r in self.spec['rooms']}
        self.flag_bits = {n: 1 << b for n,b in self.spec['flags'].items()}
        self.passes, self.failures, self.inputs, self.scenes = [], [], [], []
        self.visits, self.edges, self.snapshots, self.observations = [], [], {}, {}
        self.aliases = {'room_flags': ('room_flags', 'campaign_flags'),
                        'chapter_flags': ('chapter_flags',),
                        'unlock_mask': ('unlock_mask', 'companion_unlocks'),
                        'dialog_speaker': ('dialog_speaker', 'speaker_id'),
                        'story_seen': ('story_seen',),
                        'optional_flags': ('optional_flags',),
                        'boss_timer': ('boss_state_ticks', 'boss_timer'),
                        'guard_ticks': ('stone_guard', 'guard_ticks')}
        self.permutations_done = {'relay': [], 'sockets': []}
        self.ui_names = re.findall(r'\bTX_[A-Z0-9_]+\b', (ROOT/'src/ui.h').read_text())
        self.ui_names = list(dict.fromkeys(self.ui_names))
        self.ui_ids = {name:i for i,name in enumerate(self.ui_names) if name != 'TX_COUNT'}

    def get(self, name):
        if name == 'dialog_speaker' and 'dialog_speakers' in self.sym:
            return self.e.read(self.sym['dialog_speakers'] + self.get('dpage')*4) if self.get('game_state') == DIALOG else 0
        for candidate in self.aliases.get(name, (name,)):
            if candidate in self.sym:
                return self.e.read(self.sym[candidate])
        raise KeyError(f'Missing QA symbol {name}, tried {self.aliases.get(name, (name,))}')

    def has(self, name):
        if name == 'dialog_speaker' and 'dialog_speakers' in self.sym:
            return True
        return any(n in self.sym for n in self.aliases.get(name, (name,)))

    def status(self):
        fields = ('game_state', 'room', 'px', 'py', 'hp', 'max_hp', 'spirit',
                  'summoned', 'room_flags', 'chapter_flags', 'optional_flags',
                  'story_seen', 'unlock_mask', 'bridge_open', 'torches', 'boss_hp',
                  'boss_armor', 'boss_state', 'boss_phase', 'boss_timer',
                  'ability_cd', 'heal_cd', 'guard_ticks', 'camera_x', 'camera_y',
                  'roll_ticks', 'relic_found', 'camp_unlocked', 'dialog_speaker',
                  'dpage', 'dcount', 'frame')
        return {n: self.get(n) for n in fields if self.has(n)}

    def check(self, condition, label, fatal=True):
        if condition:
            self.passes.append(label)
            print('PASS', label, flush=True)
        else:
            self.failures.append({'check': label, 'status': self.status()})
            self.report()
            if fatal:
                raise AssertionError(f'{label}: {self.status()}')
            print('FAIL', label, flush=True)
        return bool(condition)

    def step(self, count, keys=0):
        if not count:
            return
        self.inputs.append({'emulator_frame': self.e.frame, 'frames': count, 'keys': keys})
        previous = self.get('room')
        self.e.frames(count, keys)
        # Saves intentionally keep the renderer alive while gameplay is paused.
        # Test callers wait for the committed state before advancing dialogue.
        if not getattr(self,'manual_save_control',False):
            for _ in range(180):
                if self.get('game_state')!=6 and not (self.get('game_state')==PLAY and self.get('frame')==0):break
                self.inputs.append({'emulator_frame':self.e.frame,'frames':1,'keys':0,'reason':'SAVE_PENDING' if self.get('game_state')==6 else 'COLD_CONTINUE'})
                self.e.frames(1,0)
            else:raise AssertionError('Transactional save did not finish')
        current = self.get('room')
        if self.has('save_failed') and self.get('save_failed'):
            raise AssertionError(f'Engine attempted an invalid/failed save: {self.status()}')
        if current != previous:
            self.edges.append([previous, current])
        if current not in self.visits:
            self.visits.append(current)
        if current != 1 and self.get('game_state') == PLAY:
            self.check_camera()

    def check_camera(self):
        if self.get('camera_x') or self.get('camera_y'):
            raise AssertionError(f'Fixed room retained scrolling camera: {self.status()}')

    def tap(self, keys, hold=2, release=2):
        self.step(hold, keys)
        self.step(release)

    def shot(self, name):
        self.e.screenshot(self.out / (name + '.png'))

    def snapshot(self, name):
        path = self.out / (name + '.state')
        self.e.state(path)
        sram=path.with_suffix('.state.sav')
        sram.write_bytes(self.e.bytes(0x0e000000,32768))
        self.snapshots[name] = {'path': str(path), 'sram_path':str(sram), 'status': self.status(),
                                'provenance': 'controller-reached; no game RAM writes'}
        return path

    def restore(self, path):
        path=Path(path)
        sram=path.with_suffix('.state.sav')
        if sram.exists():self.e.load_save(sram)
        self.e.state(path, load=True)

    def save(self, name):
        path = self.out / (name + '.sav')
        path.write_bytes(self.e.bytes(0x0e000000, 32768))
        return path

    def reopen(self, save):
        self.e.close()
        self.e = Emulator(self.rom)
        self.e.load_save(save)
        self.e.reset()
        self.step(90)
        self.check(self.get('has_save') == 1, 'independent emulator recognizes ' + Path(save).stem)
        self.tap('START', 4, 4)

    def dialogs(self, reward=None):
        pages = []
        for i in range(32):
            if self.get('game_state') != DIALOG:
                if reward:
                    self.observations[reward + '_pages'] = pages
                return
            pages.append(self.status())
            if self.exhaustive:
                self.dialog_case(reward or str(self.get('room')),i)
            self.shot(f'dialog-{reward or self.get("room")}-{i}')
            if reward and self.exhaustive:
                state = self.snapshot(f'{reward}-page-{i}')
                save = self.save(f'{reward}-page-{i}')
                chapter = self.get('chapter_flags')
                self.reopen(save)
                self.check(self.get('room') == 0 and self.get('chapter_flags') == chapter,
                           f'{reward} page {i}: power interruption preserves reward and safe village')
                self.restore(state)
            self.tap('A', 4, 4)
        raise AssertionError(f'Dialogue did not terminate: {self.status()}')

    def dialog_case(self,name,page):
        dpage=self.get('dpage')
        line_ids=[self.e.read(self.sym['dialog_lines']+(dpage*2+i)*4) for i in range(2)]
        self.check(all(0<=n<len(self.ui_names)-1 for n in line_ids),f'{name} page {page}: dialog text IDs stay in bounds')
        for n in line_ids:
            width=self.e.read(self.sym['ui_texts']+n*self.ui_stride,2)
            self.check(width<=214,f'{name} page {page}: Japanese line fits 214-pixel panel')
        line=self.ui_names[line_ids[0]]
        match=re.match(r'^(TX_C_.*)_\d+_0$',line)
        if match:
            expected=self.ui_ids[match.group(1)+'_SPEAKER']
            self.check(self.get('dialog_speaker')==expected,f'{name} page {page}: scene has its explicit correct speaker')
        frozen={n:self.get(n) for n in ('hp','ability_cd','heal_cd','boss_hp','boss_armor','boss_timer') if self.has(n)}
        self.step(self.get('transition')+5);first=self.e.screenshot().crop((5,99,235,155)).tobytes()
        self.step(13,'LEFT+R');second=self.e.screenshot().crop((5,99,235,155)).tobytes()
        self.check(all(self.get(n)==v for n,v in frozen.items()),f'{name} page {page}: dialog freezes health and combat timers')
        self.check(first==second,f'{name} page {page}: dialog panel stays stable across display pages')
        self.step(2)

    def goto(self, x=None, y=None):
        """Walk a known-clear orthogonal segment, preserving natural collision."""
        for name, target, lower, higher in [('px',x,'LEFT','RIGHT'), ('py',y,'UP','DOWN')]:
            if target is None:
                continue
            stagnant = 0
            for _ in range(700):
                old = self.get(name)
                if abs(old-target) <= 1:
                    break
                if self.get('game_state') != PLAY:
                    raise AssertionError(f'Movement interrupted toward {name}={target}: {self.status()}')
                self.step(1, lower if old > target else higher)
                stagnant = stagnant+1 if self.get(name) == old else 0
                if stagnant > 12:
                    raise AssertionError(f'Collision toward {name}={target}: {self.status()}')
            else:
                raise AssertionError(f'Movement exhausted toward {name}={target}: {self.status()}')
        self.step(2)

    def flags(self, names):
        return all((self.get('chapter_flags') & CHAPTER[n]) if n in CHAPTER
                   else (self.get('room_flags') & self.flag_bits[n]) for n in names)

    def valid_point(self, room, x, y, margin=5, exits=False):
        spec = self.rooms[room]
        bx,by,bw,bh = spec['play_bounds']
        if not (bx+margin <= x < bx+bw-margin and by+margin <= y < by+bh-margin):
            return False
        if not exits and not 47 <= y <= 136:
            return False
        solids = list(spec['static_solids']) + [s['rect'] for s in spec['dynamic_solids']
                   if not self.flags(s.get('blocking_unless_all', []))]
        return not any(rx-margin <= x < rx+rw+margin and ry-margin <= y < ry+rh+margin
                       for rx,ry,rw,rh in solids)

    def navigate(self, x, y, radius=2, exits=False):
        """Plan with published collision rectangles, execute solely with buttons."""
        room = self.get('room')
        if room < 4:
            return self.goto(x,y)
        start = (self.get('px'), self.get('py'))
        # A two-pixel grid keeps the BFS tiny and permits >=1px clearance slack.
        queue, prior = deque([start]), {start: None}
        found = None
        while queue:
            p = queue.popleft()
            if abs(p[0]-x)+abs(p[1]-y) <= radius:
                found = p
                break
            for dx,dy in ((0,-2),(-2,0),(2,0),(0,2)):
                q = p[0]+dx,p[1]+dy
                if q not in prior and self.valid_point(room,*q,exits=exits):
                    prior[q] = p
                    queue.append(q)
        if found is None:
            raise AssertionError(f'No design-valid route to {(x,y,radius)} from {start}: {self.status()}')
        path = []
        while found != start:
            path.append(found)
            found = prior[found]
        path.reverse()
        # Run only at turns. Position is read back after each controller segment.
        if not path:
            return
        last, direction = start, None
        for p in path:
            d = p[0]-last[0],p[1]-last[1]
            if direction is not None and d != direction:
                self.goto(*last)
            direction, last = d,p
        self.goto(*last)

    def select(self, spirit, summon=True):
        for _ in range(5):
            if self.get('spirit') == spirit:
                break
            self.tap('L')
        self.check(self.get('spirit') == spirit, f'L selects unlocked companion {spirit}')
        if bool(self.get('summoned')) != summon:
            self.tap('B')
        self.check(bool(self.get('summoned')) == summon, 'B sets expected summon state')

    def ready(self):
        self.step(self.get('ability_cd') + 2)

    def object(self, oid, *, negatives=False, persistence=False):
        obj = next(o for o in self.rooms[self.get('room')]['objects'] if o['id'] == oid)
        target = obj['at']
        power = POWER.get(obj.get('companion'))
        radius = max(2,obj.get('range_manhattan',24)-8)
        self.navigate(*target,radius=radius)
        before = self.get('room_flags')
        if negatives and power is not None:
            self.select(power,False)
            self.ready();self.tap('R')
            self.check(self.get('room_flags') == before, oid + ': unsummoned R changes no flags')
            unlocked = 4 if self.flags(['SKY_CLEAR']) else 3
            for wrong in range(unlocked):
                if wrong == power:
                    continue
                self.select(wrong)
                self.ready();self.tap('R')
                self.check(self.get('room_flags') == before, oid + f': wrong power {wrong} changes no flags')
        if power is not None:
            self.select(power)
            self.ready()
        self.tap(obj.get('input','R'))
        if obj.get('sets_flag'):
            bit = self.flag_bits[obj['sets_flag']]
            self.check(self.get('room_flags') == before | bit, oid + ': exactly its monotonic puzzle flag is set')
        elif obj.get('sets_optional'):
            self.check(self.get('optional_flags') & 1, 'optional flower chime is recorded')
        self.dialogs()
        self.shot('object-' + oid)
        if power is not None and self.exhaustive:
            committed = self.get('room_flags')
            self.ready();self.tap('R');self.dialogs()
            self.check(self.get('room_flags') == committed, oid + ': repeat cannot toggle or duplicate progress')
            self.tap('B');self.tap('L')
            self.check(self.get('room_flags') == committed, oid + ': dismissal and companion change retain progress')
        if persistence:
            self.reload_case('object-' + oid)

    def reload_case(self, name, expected_state=None):
        state = self.snapshot(name + '-before-reload')
        save = self.save(name)
        prior = self.status()
        self.reopen(save)
        if expected_state is not None:
            self.check((self.get('game_state'),self.get('room'))==expected_state,
                       name+': independent reboot opens expected safe game state and room')
        self.check(self.get('chapter_flags') == prior['chapter_flags'] and self.get('room_flags') == prior['room_flags'],
                   name + ': independent SRAM reload preserves chapter and puzzle flags')
        self.check(self.get('hp') == self.get('max_hp'), name + ': reload restores full health')
        for field in ('bridge_open','torches','max_hp','relic_found','camp_unlocked','optional_flags','story_seen'):
            self.check(self.get(field)==prior[field],name+': independent reload preserves '+field)
        self.restore(state)

    def nextroom(self, target, key='UP'):
        old = self.get('room')
        if old >= 4:
            self.navigate(120, 48 if key=='UP' else 134, radius=2)
        elif old == 1 and target == 2:
            self.goto(x=240);self.goto(y=92);self.goto(x=368)
        for _ in range(450):
            if self.get('room') == target:
                break
            self.step(1,key)
        self.check(self.get('room') == target, f'controller exit {old} -> {target}')
        self.step(24)
        self.check(self.get('room') == target, f'exit {old} -> {target}: arrival does not bounce')
        self.dialogs()
        if old >= 4 or target >= 4:
            self.check(not any(self.e.read(self.sym['shots']+i*24+16) for i in range(12)),
                       f'exit {old} -> {target}: old projectiles cleared')

    def roundtrip(self, previous):
        current = self.get('room')
        self.nextroom(previous,'DOWN')
        if previous == 0:
            self.hub(current)
        else:
            self.nextroom(current)

    def hub(self, target):
        self.check(self.get('room') == 0, 'hub travel begins in village')
        x = 196 if target == 4 else 80
        self.goto(y=128);self.goto(x=x)
        self.tap('A')
        self.check(self.get('room') == target, f'village marker enters chapter approach {target}')
        self.dialogs();self.step(24)
        self.check(self.get('room') == target, 'hub arrival remains stable')

    def defend(self, duration=800):
        for _ in range(duration//12):
            if self.get('game_state') == DIALOG:
                self.dialogs()
            if self.get('game_state') != PLAY:
                raise AssertionError(f'Combat interrupted: {self.status()}')
            live = []
            for i in range(6):
                a = self.sym['enemies']+i*20
                x,y,hp = (self.e.read(a+offset) for offset in (0,4,8))
                if hp:
                    live.append((abs(x-self.get('px'))+abs(y-self.get('py')),x,y))
            if not live:
                return
            distance,x,y = min(live)
            dx,dy = x-self.get('px'),y-self.get('py')
            key = ('LEFT' if dx<0 else 'RIGHT') if abs(dx)>abs(dy) else ('UP' if dy<0 else 'DOWN')
            if distance > 24:
                if self.get('room')>=4:
                    self.navigate(x,y,radius=22)
                else:
                    self.step(6,key)
            else:
                self.step(1,key)
            self.tap('A')
            self.step(12)
        self.check(not any(self.e.read(self.sym['enemies']+i*20+8) for i in range(6)), 'ordinary encounter cleared')

    def menu_case(self, name):
        state = self.snapshot(name+'-menu-start')
        self.tap('START')
        self.check(self.get('game_state') == PAUSE,name + ': Start opens journal')
        fixed = {n:self.get(n) for n in ('px','py','hp','ability_cd','heal_cd','boss_hp','boss_armor')}
        if self.has('boss_timer'):
            fixed['boss_timer'] = self.get('boss_timer')
        images=[]
        for _ in range(4):
            self.step(17,'LEFT' if self.flags(['ENDING_SEEN']) else 'LEFT+R')
            images.append(self.e.screenshot().tobytes())
        self.check(all(self.get(n)==v for n,v in fixed.items()),name+': menu freezes movement, health and combat timers')
        self.check(all(im==images[0] for im in images),name+': journal stable across both display pages')
        self.shot(name+'-journal')
        first_tab=self.get('journal_tab');tab_images={first_tab:self.e.screenshot().crop((8,31,232,153)).tobytes()}
        for i in range(7):
            self.tap('A');self.step(6);tab=self.get('journal_tab')
            if tab==first_tab:break
            tab_images[tab]=self.e.screenshot().crop((8,31,232,153)).tobytes()
            self.shot(name+f'-journal-tab-{tab}')
            self.snapshot(name+f'-journal-tab-{tab}')
        self.check(self.get('journal_tab')==first_tab and len(tab_images)>=2,name+': A cycles all journal tabs and returns')
        self.check(len(set(tab_images.values()))==len(tab_images),name+': every journal tab has distinct visible content')
        companion_tab=2 if 2 in tab_images else 1
        for _ in range(7):
            if self.get('journal_tab')==companion_tab:break
            self.tap('A');self.step(6)
        if len(tab_images)>=3:
            unlocked=4 if self.flags(['SKY_CLEAR']) else 3 if self.flags(['GROVE_CLEAR']) else 2
            original=self.get('spirit');visited=set()
            for _ in range(unlocked):
                self.tap('L');self.step(6);visited.add(self.get('spirit'))
                self.check(self.get('game_state')==PAUSE and all(self.get(n)==v for n,v in fixed.items()),
                           name+': companion selection leaves gameplay paused')
                self.shot(name+'-journal-companion-'+str(self.get('spirit')))
            self.check(visited==set(range(unlocked)) and self.get('spirit')==original,
                       name+': journal L cycles exactly the unlocked companions')
        self.tap('B')
        self.check(self.get('game_state')==PLAY,name+': B closes journal')
        self.restore(state)

    def cadence(self,name,frames=300,control=None):
        state = self.snapshot(name+'-cadence')
        self.step(8)
        start=self.status();last=self.get('frame');page=self.e.read(0x04000000,2)&16
        deltas=[];flips=[];cycles=[];states=Counter();peak_shots=peak_objects=0
        for offset in range(frames):
            self.step(1,control(offset) if control else 0)
            current=self.get('frame');deltas.append((current-last)&0xffffffff);last=current
            p=self.e.read(0x04000000,2)&16;flips.append(p!=page);page=p
            cycles.append(self.get('render_cycles'))
            states[f'{self.get("game_state")}:{self.get("room")}']+=1
            peak_shots=max(peak_shots,sum(bool(self.e.read(self.sym['shots']+i*24+16)) for i in range(12)))
            if self.has('obj_count'):peak_objects=max(peak_objects,self.get('obj_count'))
        result={'scene':name,'frames':frames,'initial':start,'final':self.status(),
                'simulation_updates':sum(deltas),'display_flips':sum(flips),
                'update_histogram':dict(Counter(deltas)),'states':dict(states),
                'cycles_max':max(cycles),'cycles_median':sorted(cycles)[len(cycles)//2],
                'cycles_max_frame_fraction':max(cycles)/CYCLES_PER_FRAME,
                'peak_projectiles':peak_shots,'peak_objects':peak_objects,
                'one_update_and_present_per_frame':all(d==1 for d in deltas) and all(flips)}
        self.scenes.append(result);self.shot(name+'-cadence');self.restore(state)
        self.check(result['one_update_and_present_per_frame'],name+': one update and presentation per emulated frame',fatal=False)
        return result

    def permutations_case(self,name,objects):
        state=self.snapshot(name+'-pristine')
        base=self.get('room_flags')
        mask=sum(self.flag_bits[next(o for o in self.rooms[self.get('room')]['objects'] if o['id']==oid)['sets_flag']] for oid in objects)
        for order in permutations(objects):
            self.restore(state)
            for oid in order:
                self.object(oid)
            self.check(self.get('room_flags') == base|mask,name+': order '+','.join(order))
            self.permutations_done[name].append(list(order))
            self.reload_case(name+'-'+'-'.join(order))
        self.restore(state)

    def first_chapter(self):
        self.step(90)
        self.check(self.get('game_state')==0,'complete campaign ROM boots to title')
        self.shot('01-title');self.snapshot('title');self.tap('SELECT',4,4);self.snapshot('intro');self.dialogs()
        self.check(self.get('game_state')==PLAY and self.get('room')==0,'fresh start enters village')
        self.check(self.get('chapter_flags')==self.get('room_flags')==0,'fresh start has no progression flags')
        self.menu_case('village')
        self.nextroom(1);self.snapshot('grove-south-entry')
        if self.exhaustive:self.death_case('grove')
        if self.optional:
            self.goto(y=248);self.goto(x=120);self.tap('A');self.dialogs()
            self.goto(x=240)
        self.goto(y=180)
        self.select(1);self.ready();self.tap('R');self.dialogs()
        self.check(self.get('bridge_open')==1,'Midori grows original grove bridge')
        self.goto(x=240);self.goto(y=92)
        if self.optional:
            self.goto(x=92);self.goto(y=72);self.tap('A');self.dialogs()
            self.check(self.get('max_hp')==8,'optional grove relic grants eight hearts')
            self.goto(y=92)
        self.goto(x=368);self.nextroom(2);self.dialogs()
        if self.exhaustive:
            self.death_case('original-shrine');rt=self.snapshot('original-shrine-roundtrip');self.nextroom(1,'DOWN');self.nextroom(2);self.restore(rt)
        self.select(0)
        self.goto(y=94);self.goto(x=64);self.goto(y=84)
        self.defend(240);self.goto(x=64,y=84);self.ready();self.tap('R')
        self.check(self.get('torches')&1,'first original shrine brazier lit')
        self.goto(y=94);self.goto(x=176);self.goto(y=84)
        self.defend(240);self.goto(x=176,y=84);self.ready();self.tap('R');self.dialogs()
        self.check(self.get('torches')==3,'original shrine gate opens')
        self.goto(y=94);self.goto(x=120);self.nextroom(3);self.dialogs()
        self.snapshot('grove-boss-entry');self.shot('02-grove-guardian')
        if self.exhaustive:
            self.death_case('original-guardian');rt=self.snapshot('original-guardian-roundtrip');self.nextroom(2,'DOWN');self.nextroom(3);self.restore(rt)
        self.goto(y=100);self.ready();self.tap('R');self.goto(y=96)
        for i in range(5000):
            if self.get('game_state')==DIALOG:break
            if self.get('boss_armor')==0 and self.get('ability_cd')==0:
                if self.get('roll_cd')==0:
                    self.step(1,'RIGHT+SELECT');self.step(12,'RIGHT')
                self.tap('R')
            if self.get('boss_armor')>12 and self.get('combo_timer')==0 and self.get('sword_cd')==0:
                self.goto(x=self.get('boss_x'),y=self.get('boss_y')+30)
                self.step(1,'UP');self.tap('A')
                self.check(self.get('combo_step')==1,'original guardian uses ordinary sword attacks')
            else:self.step(1)
        self.check(self.get('boss_hp')==0,'original guardian defeated by controller sword attacks')
        self.check(self.flags(['GROVE_CLEAR']),'grove reward committed before conversation')
        self.dialogs('grove-reward')
        self.check(self.get('room')==0 and self.get('game_state')==PLAY,'first guardian continues in village, not final ending')
        self.select(2)
        self.check(self.get('max_hp')==(8 if self.optional else 6),'optional relic status is preserved')
        self.reload_case('grove-complete')

    def death_case(self,name):
        snapshot=self.snapshot(name+'-before-natural-death')
        prior=self.status();room=self.get('room')
        if room==1:self.goto(x=180,y=240)
        elif room==2:self.goto(x=90,y=110)
        elif room==3:self.goto(x=120,y=100)
        elif room==13:self.navigate(120,100)
        for _ in range(2000):
            if self.get('game_state')==DEAD:break
            self.step(4)
        self.check(self.get('game_state')==DEAD and self.get('hp')==0,name+': natural threats can defeat an idle player')
        self.shot(name+'-natural-death');self.tap('A',4,4);self.dialogs()
        self.check(self.get('game_state')==PLAY and self.get('room')==room,name+': A retries current room')
        self.check(self.get('hp')==self.get('max_hp'),name+': retry restores full health')
        self.check(self.get('room_flags')==prior['room_flags'] and self.get('chapter_flags')==prior['chapter_flags'],
                   name+': death preserves monotonic progression')
        self.check(self.get('ability_cd')==self.get('heal_cd')==self.get('roll_ticks')==0,
                   name+': retry clears ability, heal and active dodge state')
        if room>=4:
            self.check(self.valid_point(room,self.get('px'),self.get('py')),name+': retry position clears every foot corner')
        self.restore(snapshot)

    def barrier_case(self,name,x,y,minimum_y):
        state=self.snapshot(name+'-collision-start')
        room=self.get('room');self.navigate(x,y)
        for key in ('UP','UP+LEFT','UP+RIGHT','UP+SELECT'):
            branch=self.snapshot(name+'-'+key.replace('+','-'))
            for _ in range(30):
                self.step(1,key)
                self.check(self.get('room')==room and self.get('py')>=minimum_y,
                           name+': '+key+' cannot tunnel through blocking row')
                self.check(self.valid_point(room,self.get('px'),self.get('py'),margin=4,exits=True),
                           name+': every foot corner stays outside solid geometry')
            self.restore(branch)
        self.restore(state)

    def closed_gate_case(self, y=52):
        room=self.get('room')
        self.navigate(120,y)
        before=self.get('room_flags')
        self.step(30,'UP');self.step(2,'UP+SELECT');self.step(18,'UP')
        self.check(self.get('room')==room and self.get('room_flags')==before,
                   f'room {room}: walking and dodging cannot cross the locked exit')
        self.check(self.get('py')>=48,f'room {room}: closed gate preserves full foot clearance')
        self.step(self.get('roll_cd')+2)

    def chapter_two(self):
        self.hub(4);self.snapshot('sky-path-entry');self.shot('03-sky-ridge')
        if self.exhaustive:self.death_case('sky-ridge')
        if self.exhaustive:
            self.roundtrip(0);self.menu_case('sky-ridge')
        if self.optional:
            self.object('flower_chime',negatives=True,persistence=True)
        self.object('trail_rest')
        self.nextroom(5);self.snapshot('sky-vanes-entry')
        if self.exhaustive:
            self.roundtrip(4)
            self.navigate(120,120);self.step(40,'UP');self.step(2,'UP+SELECT');self.step(18,'UP')
            self.check(self.get('py')>=108 and not self.flags(['SKY_BRIDGE']),
                       'folded sky bridge blocks walking and swept dodge')
        self.object('south_vane',negatives=self.exhaustive,persistence=self.exhaustive)
        if self.exhaustive:self.closed_gate_case()
        self.object('north_vane',negatives=self.exhaustive,persistence=self.exhaustive)
        self.nextroom(6);self.snapshot('sky-patrol-entry');self.shot('04-patrol')
        if self.exhaustive:
            self.death_case('sky-patrol');cs=self.snapshot('patrol-closed-gate');self.closed_gate_case();self.restore(cs)
        self.select(0)
        self.navigate(104,122)
        self.defend(3000);self.dialogs()
        self.check(self.flags(['SKY_PATROL_CLEAR']),'defeating all four patrol enemies latches gate')
        if self.exhaustive:
            self.reload_case('patrol-cleared');self.roundtrip(5)
            self.check(not any(self.e.read(self.sym['enemies']+i*20+8) for i in range(6)),
                       'completed patrol does not respawn on reentry')
        self.nextroom(7);self.snapshot('relay-entry')
        if self.exhaustive:
            self.roundtrip(6);self.closed_gate_case()
            self.permutations_case('relay',['left_vane','right_vane','source_brazier'])
        for oid in ['left_vane','right_vane','source_brazier']:
            self.object(oid,negatives=self.exhaustive,persistence=self.exhaustive)
        self.object('rest_lamp');self.shot('05-sky-relay')
        self.cadence('sky-relay-stable',180)
        self.nextroom(8);self.snapshot('kazane-entry');self.shot('06-kazane')
        self.menu_case('kazane')
        if self.exhaustive:self.death_case('kazane')
        self.boss_fight(8)
        self.check(self.flags(['SKY_CLEAR']),'sky reward committed before conversation')
        self.dialogs('sky-reward')
        self.check(self.get('room')==0 and self.get('game_state')==PLAY,'Kazane reward returns to village with continuing story')
        self.select(3);self.reload_case('sky-complete')

    def chapter_three(self):
        self.hub(9);self.snapshot('core-path-entry');self.shot('07-stone-slope')
        if self.exhaustive:
            self.roundtrip(0)
        self.object('slope_rest')
        if self.exhaustive:self.barrier_case('cracked-arch',120,120,100)
        self.object('cracked_arch',negatives=self.exhaustive,persistence=self.exhaustive)
        self.nextroom(10);self.snapshot('weights-entry')
        if self.exhaustive:
            self.roundtrip(9);self.closed_gate_case()
        for oid in ['west_weight','east_weight']:
            self.object(oid,negatives=self.exhaustive,persistence=self.exhaustive)
        self.nextroom(11);self.snapshot('roots-entry');self.shot('08-root-waterway')
        if self.exhaustive:
            self.roundtrip(10);self.barrier_case('root-channel-gap',120,120,108)
            self.navigate(76,120);self.select(1);self.ready();prior=self.get('room_flags');self.tap('R')
            self.check(self.get('room_flags')==prior,'Midori cannot grow bridge before well is uncapped')
        for oid in ['well_cap','dry_well','dry_thorns']:
            if oid=='dry_thorns' and self.exhaustive:self.barrier_case('thorn-screen',120,78,72)
            self.object(oid,negatives=self.exhaustive,persistence=self.exhaustive)
        self.nextroom(12);self.snapshot('sockets-entry')
        if self.exhaustive:
            self.roundtrip(11);self.closed_gate_case()
            self.permutations_case('sockets',['fire_lamp','nature_lamp','wind_lamp','stone_lamp'])
        for oid in ['fire_lamp','nature_lamp','wind_lamp','stone_lamp']:
            self.object(oid,negatives=self.exhaustive,persistence=self.exhaustive)
        self.object('last_rest');self.shot('09-four-companions')
        self.menu_case('four-lights');self.cadence('four-lights-stable',180)
        self.nextroom(13);self.snapshot('core-entry');self.shot('10-closed-core')
        self.menu_case('closed-core')
        if self.exhaustive:
            self.death_case('closed-core');self.stone_guard_case()
        self.boss_fight(13)
        self.check(self.flags(['CORE_CLEAR']) and not self.flags(['ENDING_SEEN']),
                   'core clear is committed independently before elder ending')
        self.dialogs('core-reward')
        self.check(self.get('room')==0 and self.get('game_state')==PLAY,'released core safely returns to village')
        self.reload_case('core-complete-ending-pending')

    def stone_guard_case(self):
        base=self.snapshot('core-stone-guard-start')
        self.select(3);self.goto(x=120,y=100)
        for _ in range(1800):
            if self.get('invuln')==0 and self.get('boss_state')==0 and self.get('boss_timer')<10:break
            self.step(1)
        while self.get('boss_timer')<10:self.step(1)
        self.ready();before_hp=self.get('hp')
        self.tap('R',1,0)
        self.check(self.get('guard_ticks')==36 and self.get('ability_cd')==75,
                   'Kohaku combat cast grants exactly 36-frame guard and 75-frame cooldown')
        cast=self.snapshot('stone-guard-cast')
        self.step(1);self.tap('B');self.tap('B');self.tap('L');self.select(3)
        cd=self.get('ability_cd');guard=self.get('guard_ticks');self.tap('R')
        self.check(self.get('ability_cd')<cd and self.get('guard_ticks')<=guard,
                   'dismissal, companion cycling and repeated R cannot refresh guard or cooldown')
        self.restore(cast)
        samples=[]
        for _ in range(100):
            self.step(1)
            samples.append({'timer':self.get('boss_timer'),'hazard':self.get('hazard_mode'),
                            'hp':self.get('hp'),'guard':self.get('guard_ticks'),
                            'guard_invuln':self.get('guard_invuln'),'invuln':self.get('invuln')})
            if self.get('guard_invuln'):
                break
        self.check(samples[-1]['guard_invuln']==24 and samples[-1]['guard']==0 and self.get('hp')==before_hp,
                   'one hazard consumes stone guard with no HP loss and exactly 24 guard-invulnerability frames')
        self.step(10)
        self.check(self.get('hp')==before_hp,'one full band activation cannot damage again after consuming guard')
        self.check(self.get('ability_cd')>0,'guard consumption leaves a real cooldown gap')
        self.observations['stone_guard']=samples
        self.restore(base)

    def boss_retreat_cases(self,room,phase):
        base=self.snapshot(f'boss-{room}-phase-{phase}-retreat-matrix')
        targets=[0,1,2,3,4,5] if room==8 else [0,4,5]+([6] if phase else [])
        records=[]
        for wanted in targets:
            self.restore(base)
            if wanted==5:
                self.select(2 if room==8 else (3,2,0)[phase])
                self.goto(x=120,y=120)
                self.ready()
                for _ in range(1600):
                    if self.get('boss_state')==4:break
                    self.step(1)
                self.tap('R')
                self.check(self.get('boss_state')==5,'retreat fixture reaches exposure through correct power')
            self.goto(x=120,y=138)
            for _ in range(1600):
                if self.get('boss_state')==wanted:break
                if self.get('game_state')!=PLAY:break
                self.step(1)
            self.check(self.get('game_state')==PLAY and self.get('boss_state')==wanted,
                       f'boss {room} phase {phase}: controller reaches retreat state {wanted}')
            before_flags=self.get('room_flags')
            actual=None
            for _ in range(12):
                prior=self.get('boss_state');self.step(1,'DOWN')
                if self.get('room')!=room:
                    actual=prior;break
            self.check(self.get('room')==room-1 and actual==wanted,
                       f'boss {room} phase {phase}: retreat exits while state {wanted} is active')
            self.step(24)
            self.check(self.get('room')==room-1,'boss retreat arrival never bounces')
            self.check(not any(self.e.read(self.sym['shots']+i*24+16) for i in range(12)),
                       'boss retreat removes stale projectiles')
            self.nextroom(room)
            self.check(self.get('boss_hp')==(20 if room==8 else 24) and self.get('boss_phase')==0,
                       'boss reentry restarts living encounter without duplicate rewards')
            self.check(self.get('room_flags')==before_flags,'retreat retains puzzle progress')
            records.append({'phase':phase,'requested_state':wanted,'actual_exit_state':actual})
        self.observations.setdefault(f'boss_{room}_retreats',[]).extend(records)
        self.restore(base)

    def walk_toward(self,x,y,dodge=False):
        dx,dy=x-self.get('px'),y-self.get('py')
        keys=[]
        if abs(dx)>1:keys.append('RIGHT' if dx>0 else 'LEFT')
        if abs(dy)>1:keys.append('DOWN' if dy>0 else 'UP')
        if dodge and self.get('roll_cd')==0 and keys:keys.append('SELECT')
        self.step(1,'+'.join(keys) if keys else 0)

    def boss_stand(self,distance):
        bx,by=self.get('boss_x'),self.get('boss_y')
        candidates=[(bx,by+distance),(bx-distance,by),(bx+distance,by),(bx,by-distance)]
        candidates=[p for p in candidates if self.valid_point(self.get('room'),*p)]
        self.check(bool(candidates),'boss has a reachable safe power/sword approach')
        target=min(candidates,key=lambda p:abs(p[0]-self.get('px'))+abs(p[1]-self.get('py')))
        self.navigate(*target,radius=2)

    def boss_fight(self,room):
        # State IDs are the explicit engine contract, kept separate from art IDs.
        recover, exposed = 4,5
        initial=self.snapshot(f'boss-{room}-fight-start')
        seen_states=set();seen_phases=set();captured=set();damage=[];last_hp=self.get('boss_hp')
        probes=set();retreat_phases=set();normal_swings=0;dodge_target=None;prior_state=None;enraged_captured=False
        for attempt in range(18000):
            if self.get('game_state')==DIALOG or self.get('room')!=room:
                break
            self.check(self.get('game_state')==PLAY,f'boss {room}: player remains alive') if self.get('game_state')!=PLAY else None
            state=self.get('boss_state');phase=self.get('boss_phase')
            if room==8 and self.get('boss_hp')<=10 and state==0 and not enraged_captured:
                self.snapshot('kazane-enraged-aim');enraged_captured=True
            seen_states.add(state);seen_phases.add(phase)
            if (phase,state) not in captured:
                self.snapshot(f'boss-{room}-phase-{phase}-state-{state}');captured.add((phase,state))
            if self.exhaustive and phase not in retreat_phases:
                self.boss_retreat_cases(room,phase);retreat_phases.add(phase)
            if self.get('boss_hp') != last_hp:
                damage.append({'before':last_hp,'after':self.get('boss_hp'),'phase':phase,'combo':self.get('combo_step')})
                last_hp=self.get('boss_hp')
            if state==recover:
                power=2 if room==8 else (3,2,0)[phase]
                self.boss_stand(42)
                if self.exhaustive and (room,phase) not in probes:
                    self.boss_power_cases(room,phase,power,recover,exposed)
                    probes.add((room,phase))
                self.select(power);self.ready()
                if self.get('boss_state')==recover:
                    self.tap('R')
            elif state==exposed:
                if self.get('combo_timer')==0 and self.get('sword_cd')==0:
                    self.boss_stand(30)
                    dx=self.get('boss_x')-self.get('px');dy=self.get('boss_y')-self.get('py')
                    key=('LEFT' if dx<0 else 'RIGHT') if abs(dx)>abs(dy) else ('UP' if dy<0 else 'DOWN')
                    self.step(1,key);self.tap('A')
                    self.check(self.get('combo_step')==1,f'boss {room}: ordinary sword swing {normal_swings+1}')
                    normal_swings+=1
                else:
                    self.step(2)
            else:
                if room==8:
                    if state in (0,2) and state!=prior_state:
                        bx,by=self.get('boss_x'),self.get('boss_y')
                        ax,ay=self.get('boss_aimx'),self.get('boss_aimy')
                        if state==0:
                            # Stand between the cardinal and diagonal fan rays.
                            candidates=[(bx+sx*25,by+sy*55) for sx in (-1,1) for sy in (-1,1)]
                            candidates += [(bx+sx*55,by+sy*25) for sx in (-1,1) for sy in (-1,1)]
                        elif abs(ax-bx)>abs(ay-by):
                            candidates=[(self.get('px'),self.get('py')+dy) for dy in (-45,45)]
                        else:
                            candidates=[(self.get('px')+dx,self.get('py')) for dx in (-45,45)]
                        candidates=[p for p in candidates if self.valid_point(room,*p)]
                        dodge_target=min(candidates,key=lambda p:abs(p[0]-self.get('px'))+abs(p[1]-self.get('py'))) if candidates else (120,132)
                    self.walk_toward(*(dodge_target or (120,132)), dodge=state in (1,3))
                elif room==13:
                    self.walk_toward(96 if phase==1 else 120,112,dodge=phase==1 and state==0 and self.get('boss_timer')>=34)
                else:self.step(2)
            prior_state=state
            if self.get('hp')<=0:
                raise AssertionError(f'Six-heart boss route died: {self.status()}')
        self.check(self.get('boss_hp')==0,f'boss {room}: defeated without relic requirement or combos')
        self.check(all(d['before']-d['after']==1 for d in damage),f'boss {room}: all observed sword damage is one HP')
        self.observations[f'boss_{room}']={'states':sorted(seen_states),'phases':sorted(seen_phases),
                                          'damage':damage,'ordinary_swings':normal_swings,
                                          'end_hp':self.get('hp')}
        if room==13:
            self.check({0,1,2}.issubset(seen_phases),'core fight traverses all three required phases')
            self.check({16,8}.issubset({d['after'] for d in damage}),'core stops exactly at both phase thresholds')

    def boss_power_cases(self,room,phase,power,recover,exposed):
        start=self.snapshot(f'boss-{room}-phase-{phase}-recovery')
        for wrong in range(4 if room==13 else 3):
            if wrong==power:continue
            self.restore(start);self.select(wrong);self.ready()
            self.check(self.get('boss_state')==recover,'wrong-power probe occurs inside recovery window')
            hp=self.get('boss_hp');self.tap('R')
            self.check(self.get('boss_state')!=exposed and self.get('boss_armor')==0 and self.get('boss_hp')==hp,
                       f'boss {room} phase {phase}: wrong power {wrong} cannot expose or damage')
        self.restore(start);self.select(power);self.ready();self.tap('R')
        self.check(self.get('boss_state')==exposed,f'boss {room} phase {phase}: required power exposes during recovery')
        self.shot(f'boss-{room}-phase-{phase}-exposed')
        before=self.get('boss_armor');self.step(80);self.tap('R')
        self.check(self.get('boss_armor')<before-60,f'boss {room} phase {phase}: repeat R cannot extend exposure')
        self.restore(start)

    def ending(self):
        self.goto(y=116);self.goto(x=120);self.tap('A')
        self.check(self.get('game_state')==DIALOG,'elder offers final celebration after core clear')
        self.dialogs('ending')
        self.check(self.get('game_state')==WIN and self.flags(['ENDING_SEEN']),
                   'all three lanterns and elder celebration reach persistent final card')
        self.shot('11-full-ending');self.reload_case('finished-ending',expected_state=(PLAY,0))
        self.tap('START')
        self.check(self.get('game_state')==PLAY and self.get('room')==0,'Start on final card returns to peaceful village')
        self.shot('12-peaceful-village');self.menu_case('peaceful-village')
        self.check(self.flags(['GROVE_CLEAR','SKY_CLEAR','CORE_CLEAR','ENDING_SEEN']),
                   'peaceful village retains all three rewards and ending')
        self.save('complete-campaign')

    def postgame_cases(self):
        base=self.snapshot('postgame-exploration-start')
        flags=self.get('room_flags');chapter=self.get('chapter_flags')
        self.tap('START');self.tap('R')
        self.check(self.get('game_state')==DIALOG,'journal R replays complete ending')
        self.dialogs('ending-replay')
        self.check(self.get('game_state')==WIN and self.get('chapter_flags')==chapter and self.get('room_flags')==flags,
                   'ending replay preserves every earned reward')
        self.tap('START');self.restore(base)
        self.hub(4)
        if self.optional:
            self.object('flower_chime',persistence=True)
            self.check(self.get('optional_flags')==1,'postgame chime remains one optional reward')
        for room in (5,6,7,8):self.nextroom(room)
        self.check(self.get('boss_hp')==0,'cleared Kazane does not respawn on postgame revisit')
        self.nextroom(0)
        self.hub(9)
        for room in (10,11,12,13):self.nextroom(room)
        self.check(self.get('boss_hp')==0,'cleared core does not respawn on postgame revisit')
        self.nextroom(0)
        self.check(self.get('chapter_flags')==chapter and self.get('room_flags')==flags,
                   'postgame paths remain traversable with all puzzle and story flags intact')
        self.restore(base)

    def run(self):
        self.first_chapter()
        self.chapter_two()
        self.chapter_three()
        self.ending()
        if self.exhaustive:
            self.postgame_cases();self.migration_cases()
        self.check(set(range(14)).issubset(self.visits),'fresh controller route visits all fourteen rooms')
        self.check(self.get('relic_found') == int(self.optional),'route optional relic condition maintained')
        if not self.optional:
            self.check(self.get('max_hp')==6 and self.get('optional_flags')==0,'six-heart route completes without either optional reward')
        self.report()

    def migration_cases(self):
        from test_save4 import AUTHENTIC_FIXTURES
        final=self.snapshot('postgame-before-migration-fixtures')
        base=ROOT/'tests/fixtures/legacy'
        evidence=[]
        for relative,header,digest,valid in AUTHENTIC_FIXTURES:
            source=base/relative
            if not source.exists():
                self.check(False,'authentic legacy fixture available: '+relative)
            data=source.read_bytes()
            self.check(hashlib.sha256(data).hexdigest()==digest,'authentic fixture hash: '+relative)
            self.e.close();self.e=Emulator(self.rom);self.e.load_save(source);self.e.reset();self.step(90)
            self.check(bool(self.get('has_save'))==valid,'legacy validity: '+relative)
            if valid:
                self.tap('START',4,4)
                complete=bool(data[6])
                self.check(self.get('chapter_flags')==int(complete),'legacy completion maps only to first lantern: '+relative)
                self.check(self.get('bridge_open')==data[4] and self.get('torches')==data[5],
                           'legacy bridge and torches preserved: '+relative)
                self.check(self.get('max_hp')==(data[10] if data[2]==3 else 6),
                           'legacy permanent heart capacity preserved: '+relative)
                if complete:
                    self.check(self.get('room')==0 and self.get('game_state')!=WIN,
                               'completed legacy save continues from village without replay: '+relative)
                    self.dialogs();self.select(2);self.hub(4)
                self.check(self.get('save_failed')==0,'legacy migration stores a valid v5 transaction: '+relative)
                self.check(self.e.bytes(0x0e000000,len(bytes.fromhex(header)))==data[:len(bytes.fromhex(header))],
                           'migration leaves original legacy bytes untouched: '+relative)
                upgraded=self.save('migrated-'+relative.replace('/','-'))
                self.reopen(upgraded)
                self.check(self.get('loaded_save_version')==5,'independent reopen uses v5: '+relative)
            evidence.append({'path':str(source),'sha256':digest,'valid':valid,
                             'provenance':'actual prior-ROM controller run or its explicitly labelled corruption fixture'})
        self.observations['legacy_fixtures']=evidence
        self.restore(final)
        complete=self.save('before-new-game-test')
        self.e.close();self.e=Emulator(self.rom);self.e.load_save(complete);self.e.reset();self.step(90)
        self.tap('SELECT',4,4);self.dialogs()
        self.check(self.get('chapter_flags')==0 and self.get('room_flags')==0 and self.get('max_hp')==6,
                   'Select intentionally resets completed game progression')
        new=self.save('new-game-after-complete')
        self.reopen(new);self.dialogs()
        self.check(self.get('chapter_flags')==0 and self.get('room_flags')==0,
                   'newer fresh-game sequence beats older completed bank')
        raw=bytearray(new.read_bytes())
        newest=max((0x200,0x1a00),key=lambda off:int.from_bytes(raw[off+8:off+12],'little'))
        raw[newest+16]^=1
        corrupted=self.out/'explicit-corrupted-newest-bank.sav';corrupted.write_bytes(raw)
        self.e.close();self.e=Emulator(self.rom);self.e.load_save(corrupted);self.e.reset();self.step(90)
        self.check(self.get('has_save')==1,'one corrupt v5 bank falls back to the other bank')
        raw[0x200+20]=raw[0x1a00+20]=0
        invalid=self.out/'explicit-no-valid-banks.sav';invalid.write_bytes(raw)
        self.e.close();self.e=Emulator(self.rom);self.e.load_save(invalid);self.e.reset();self.step(90)
        self.check(self.get('has_save')==0,'two uncommitted banks do not invent a save')
        self.restore(final)

    def report(self):
        result={'rom_sha256':hashlib.sha256(self.rom.read_bytes()).hexdigest(),
                'symbol_sha256':hashlib.sha256(self.symbol_path.read_bytes()).hexdigest(),
                'controller_only':True,'game_ram_writes':0,
                'route':'optional' if self.optional else 'six-heart-no-optional',
                'exhaustive':self.exhaustive,'passes':self.passes,'failures':self.failures,
                'visited_rooms':self.visits,'edges':self.edges,'permutations':self.permutations_done,
                'performance':self.scenes,'snapshots':self.snapshots,'observations':self.observations,
                'final':self.status(),'emulator_frame':self.e.frame}
        (self.out/'campaign-report.json').write_text(json.dumps(result,indent=2)+'\n')
        (self.out/'controller-inputs.json').write_text(json.dumps(self.inputs,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba')
    p.add_argument('--symbols',type=Path,default=ROOT/'build/emberbond.sym')
    p.add_argument('--output',type=Path,default=ROOT/'build/campaign-qa')
    p.add_argument('--optional',action='store_true',help='Collect optional relic and flower chime')
    p.add_argument('--quick',action='store_true',help='Only fresh route; skip permutation and interruption matrices')
    a=p.parse_args()
    run=CampaignRun(a.rom,a.symbols,a.output,a.optional,not a.quick)
    try:
        run.run()
    except Exception as exc:
        run.failures.append({'error':str(exc),'status':run.status()})
        run.shot('failure')
        raise
    finally:
        run.report();run.e.close()
    return int(bool(run.failures))


if __name__=='__main__':
    raise SystemExit(main())
