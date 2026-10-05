#!/usr/bin/env python3
"""Controller-only Reedhaven journey against an immutable native GBA candidate.

The pinned old finished-ending SRAM supplies earlier story progress only. Every
regional item, puzzle and companion in this report is earned by actual buttons.
The emulator is observed through symbols; this file never calls emu.write().
Machine-state branches always travel with matching SRAM and recorded hashes.
"""
from __future__ import annotations
from collections import deque
from pathlib import Path
import argparse, ctypes as C, hashlib, json, shutil, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
from test_save5 import Save
from test_creatures import Roster
from test_save4 import CampaignSave
PLAY,DIALOG,PAUSE,DEAD,SAVING,CONFIRM,EVOLVING=1,2,3,4,6,7,8
FIXTURE_SHA='8f603dff9d9893675b2864a900f77a4608d7de43b85fa1464ad3b5f820607809'
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class RegionJourney:
    def __init__(self,rom,symbols,output,fixture):
        self.source_rom=Path(rom).resolve();self.source_symbols=Path(symbols).resolve();self.out=Path(output).resolve();self.out.mkdir(parents=True,exist_ok=True)
        self.rom=self.out/'tested.gba';self.symbol_path=self.out/'tested.sym'
        if self.source_rom!=self.rom:shutil.copyfile(self.source_rom,self.rom)
        if self.source_symbols!=self.symbol_path:shutil.copyfile(self.source_symbols,self.symbol_path)
        self.sym={p[2]:int(p[0],16) for l in self.symbol_path.read_text().splitlines() if len(p:=l.split())==3}
        self.candidate={'rom_path':str(self.source_rom),'symbols_path':str(self.source_symbols),'rom_sha256':digest(self.rom),'symbols_sha256':digest(self.symbol_path),'rom_bytes':self.rom.stat().st_size}
        self.fixture=Path(fixture).resolve();assert digest(self.fixture)==FIXTURE_SHA,'Expected the hash-pinned controller-earned v4 finished-ending save'
        self.layout=json.loads((ROOT/'assets/region/layout.json').read_text())
        self.world=json.loads((ROOT/'assets/world_manifest.json').read_text())
        self.campaign=json.loads((ROOT/'assets/campaign_layouts.json').read_text());self.campaign_rooms={r['id']:r for r in self.campaign['rooms']}
        self.inputs=[];self.checks=[];self.snapshots={};self.failures=[];self.timings={}
        self.e=Emulator(self.rom);self.e.load_save(self.fixture);self.e.reset()
    def get(self,n,width=4):return self.e.read(self.sym[n],width)
    def state(self):return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
    def roster(self):return self.state().roster
    def selected(self):
        r=self.roster();return r.instances[r.party[r.selected_party]]
    def quest(self,q):s=self.state().quests.states;return (s[q>>2]>>((q&3)*2))&3
    def status(self):return {n:self.get(n) for n in ('game_state','room','px','py','hp','chapter_flags','camera_x','camera_y','save_failed','checkpoint_spawn','spirit','summoned','ability_cd','roll_cd')}
    def check(self,yes,label):
        self.checks.append({'label':label,'passed':bool(yes),'frame':self.e.frame})
        if not yes:raise AssertionError((label,self.status()))
    def step(self,n,keys=0):self.inputs.append({'frame':self.e.frame,'frames':int(n),'keys':keys});self.e.frames(n,keys)
    def tap(self,k,hold=2,release=2):self.step(hold,k);self.step(release)
    def settle(self,dialogs=True):
        for _ in range(80):
            s=self.get('game_state')
            if s==DIALOG and dialogs:self.tap('A',2,16)
            elif s in (SAVING,EVOLVING):self.step(20)
            else:break
        else:raise AssertionError(('modal did not finish',self.status()))
        self.step(3)
        self.check(not self.get('save_failed'),'autosave remains valid')
    def ready(self):
        self.settle()
        for _ in range(200):
            if not self.get('ability_cd') and not self.get('roll_cd'):break
            self.step(2)
        if not self.get('summoned'):self.tap('B');self.settle()
    def snapshot(self,name):
        self.settle();self.e.screenshot(self.out/(name+'.png'));state=self.out/(name+'.state');save=self.out/(name+'.sav')
        self.e.state(state);save.write_bytes(self.e.bytes(0x0e000000,32768))
        self.snapshots[name]={'state_path':str(state),'state_sha256':digest(state),'sram_path':str(save),'sram_sha256':digest(save),'status':self.status(),'quests':[self.quest(q) for q in range(11)]}
        self.report();print(name,self.status(),'quests',[self.quest(q) for q in range(11)],flush=True)
        return name
    def restore(self,name):
        saved=self.snapshots[name];self.e.load_save(saved['sram_path']);self.e.state(saved['state_path'],True);self.step(4)
    def report(self):
        data={'suite':'reedhaven-native-controller-journey','controller_only':True,'fixture':{'path':str(self.fixture),'sha256':FIXTURE_SHA,'scope':'prior story chapters only; no regional state or new companions'},**self.candidate,'checks':self.checks,'failures':self.failures,'snapshots':self.snapshots,'timings':self.timings,'inputs':self.inputs}
        (self.out/'region-journey.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    def mask(self):
        room=self.get('room');w,h=(480,320) if room in (1,16,17) else (240,160);rects=[];margin=0
        if room>=16:
            d=self.layout['rooms'][room-16];rects=[s['rect'] for s in d['solids']];margin=5
            if room==17 and not self.state().quests.objectives[1]&2:rects+=[[224,152,32,32]]
            if room==19:rects+=[[50,48,28,26],[162,48,28,26]]
            if room==20:
                raw=self.e.bytes(self.sym['region_game_crates'],8)
                for i in (0,4):
                    x=int.from_bytes(raw[i:i+2],'little');y=int.from_bytes(raw[i+2:i+4],'little');rects.append([x-7,y-7,14,14])
            bounds=(5,5,w-10,h-10)
        elif room==1:
            rects=list(self.world['static_collision_rectangles']);bounds=(12,24,456,284)
            if self.get('bridge_open'):rects += [[0,156,228,20],[252,156,228,20]]
            else:rects += [[0,156,480,20]]
        elif room in (14,15):
            bounds=(12,44,216,104)
            if room==15:
                for i in range(2):
                    x=self.e.read(self.sym['trial_parcels']+i*4,2);y=self.e.read(self.sym['trial_parcels']+i*4+2,2);rects.append([x-10,y-10,21,21])
        elif room>=4:
            d=self.campaign_rooms[room];rects=list(d['static_solids']);margin=4;bounds=(12,32,216,116)
            flagvalues={k:1<<v for k,v in self.campaign['flags'].items()};flagvalues.update(GROVE_CLEAR=1<<16,SKY_CLEAR=2<<16,CORE_CLEAR=4<<16)
            progress=self.get('room_flags')|(self.get('chapter_flags')<<16)
            for dynamic in d['dynamic_solids']:
                required=sum(flagvalues[k] for k in dynamic.get('blocking_unless_all',[]))
                if progress&required!=required:rects.append(dynamic['rect'])
        else:
            import re
            text=(ROOT/'src/asset_collisions.h').read_text();body=re.search(r'asset_solids_village\[.*?\] = \{(.*?)\};',text,re.S).group(1)
            rects=[list(map(int,row.split(','))) for row in re.findall(r'\{([^}]+)\}',body)];bounds=(12,28,216,125)
        b=bytearray(w*h);bx,by,bw,bh=bounds
        for y in range(h):
            for x in range(w):
                if not bx<=x<bx+bw or not by<=y<by+bh:b[y*w+x]=1
        for x,y,rw,rh in rects:
            left,right=max(0,x-margin),min(w,x+rw+margin)
            for yy in range(max(0,y-margin),min(h,y+rh+margin)):b[yy*w+left:yy*w+right]=b'\1'*(right-left)
        return b,w,h
    def path(self,tx,ty):
        b,w,h=self.mask();s=self.get('py')*w+self.get('px');g=ty*w+tx
        if b[g]:
            candidates=[(abs(x-tx)+abs(y-ty),x,y) for y in range(max(0,ty-3),min(h,ty+4)) for x in range(max(0,tx-3),min(w,tx+4)) if not b[y*w+x]]
            assert candidates,('blocked goal',self.get('room'),tx,ty)
            _,tx,ty=min(candidates);g=ty*w+tx
        q=deque([g]);parent={g:None}
        while q:
            p=q.popleft()
            if p==s:break
            x,y=p%w,p//w
            for n in (p-1,p+1,p-w,p+w):
                if 0<=n<w*h and abs(n%w-x)+abs(n//w-y)==1 and not b[n] and n not in parent:parent[n]=p;q.append(n)
        assert s in parent,('no walk route',self.status(),tx,ty)
        route=[];p=s
        while parent[p] is not None:p=parent[p];route.append(p)
        return route,b,w
    def goto(self,tx,ty,radius=4):
        old=self.get('room')
        for _ in range(650):
            self.settle()
            if self.get('room')!=old:return
            self.check(self.get('game_state')==PLAY,'walking occurs in active gameplay')
            x,y=self.get('px'),self.get('py')
            if abs(x-tx)+abs(y-ty)<=radius:return
            path,blocked,w=self.path(tx,ty)
            if not path:return
            direction=path[0]-(y*w+x);length=1
            for j in range(1,len(path)):
                if path[j]-path[j-1]!=direction:break
                length+=1
            # Q8 movement can skip a particular integer coordinate. Turn within
            # two clear pixels instead of oscillating forever on that waypoint.
            if length<=2 and len(path)>length:
                turn=path[length]-path[length-1];here=y*w+x
                if not blocked[here+turn] and not blocked[here+turn*2]:direction=turn;length=2
            key={1:'RIGHT',-1:'LEFT',w:'DOWN',-w:'UP'}[direction]
            self.step(max(2,min(12,int(length/1.25))),key)
        raise AssertionError(('navigation stalled',self.status(),tx,ty))
    def face(self,f):self.tap(('DOWN','UP','LEFT','RIGHT')[f],2,2)
    def act(self,x,y,f=None):
        self.goto(x,y)
        if f is not None:self.face(f)
        self.tap('A');self.settle()
    def open_tab(self,tab):
        self.settle();self.step(2);self.tap('START',2,4)
        for _ in range(6):
            if self.get('journal_tab')==tab:break
            self.tap('A',2,4)
        self.check(self.get('game_state')==PAUSE and self.get('journal_tab')==tab,f'journal tab{tab} opens')
    def close_menu(self):self.tap('B',2,4);self.settle()
    def equip_class(self,cls):
        self.step(90);self.open_tab(4)
        for _ in range(5):
            if self.get('gear_menu_slot')==0:break
            self.tap('UP',2,3)
        for _ in range(50):
            ref=self.get('gear_menu_candidate');item=self.state().equipment.bag[ref].item_id if ref<48 else 1
            actual=1 if item in (1,2) else 2 if item in (9,10) else 3 if item in (17,18) else 0
            if actual==cls:break
            self.tap('RIGHT',2,3)
        self.tap('R',2,25);self.settle();self.e.screenshot(self.out/f'weapon-class-{cls}.png');self.close_menu()
        self.check(self.e.read(self.sym['gear_stats']+12,1)==cls,f'controller equips weapon class{cls}')
    def refused_equip_case(self):
        # Start a real lance windup, then open the journal before it resolves.
        # This is intentionally different from the normal wait-before-equip path.
        self.step(90);self.face(0);self.tap('A',1,1);self.tap('START',1,3)
        self.check(self.get('game_state')==PAUSE,'journal can open during real weapon recovery')
        for _ in range(6):
            if self.get('journal_tab')==4:break
            self.tap('A',2,3)
        before=bytes(self.state().equipment);self.tap('RIGHT',2,3);self.tap('R',2,3)
        self.check(bytes(self.state().equipment)==before,'live attack/recovery refuses gear mutation')
        self.e.screenshot(self.out/'gear-change-refused-while-busy.png');self.close_menu();self.step(90)
    def select_slot(self,slot):self.tap('L+'+('UP','RIGHT','DOWN','LEFT')[slot],2,3);self.settle();self.check(self.roster().selected_party==slot,f'L direction selects party slot{slot}')
    def select_form(self,form):
        r=self.roster();slot=next((i for i in range(4) if r.party[i]<160 and r.instances[r.party[i]].form_id==form),None)
        self.check(slot is not None,f'form{form} is available in active party');self.select_slot(slot)
    def assign(self,slot,form):
        r=self.roster();index=next(i for i,c in enumerate(r.instances) if c.flags&1 and c.form_id==form)
        self.open_tab(2)
        for _ in range(4):
            if self.get('quickparty_menu_slot')==slot:break
            self.tap('RIGHT',2,3)
        for _ in range(161):
            if self.get('quickparty_menu_candidate')==index:break
            self.tap('DOWN',2,3)
        self.tap('R',2,25);self.settle();self.close_menu();self.check(self.roster().party[slot]==index,f'owned form{form} assigned to party slot{slot}')
    def cast(self,form,x,y):self.goto(x,y);self.select_form(form);self.ready();self.tap('R');self.settle()
    def leave_interior(self,target):
        self.goto(120,149);self.settle()
        if self.get('room')!=target:self.step(6,'DOWN');self.settle()
        self.check(self.get('room')==target,'south exit remains usable')
    def enter_town(self):
        if self.get('room')==17:self.goto(240,302);self.step(6,'DOWN');self.settle()
        self.check(self.get('room')==16,'returns to Reedhaven')
    def enter_basin(self):self.act(104,232);self.goto(240,36);self.step(10,'UP');self.settle();self.check(self.get('room')==17,'north gate enters basin')
    def foundry(self):self.goto(344,150);self.step(5,'UP');self.settle();self.check(self.get('room')==18,'foundry doorway opens')
    def town_and_training(self):
        self.step(150);self.tap('START',2,35);self.settle();self.check(self.get('loaded_save_version')==4,'authentic old cartridge save migrates')
        self.step(88,'UP');self.settle();self.check(self.get('room')==1,'village north exit reaches Grove')
        self.step(49,'LEFT');self.step(27,'UP');self.settle()
        for _ in range(20):
            if self.get('room')==16:break
            self.tap('A',2,22);self.settle()
        self.check(self.get('room')==16,'guarded Grove sign enters town without stealing camp');self.snapshot('01-town-entry')
        self.act(88,152,1);self.check(self.quest(5)==1,'Mira offers the storehouse clue');self.goto(88,120);self.settle();self.check(self.get('room')==20,'storehouse doorway')
        self.act(80,104,1);self.act(48,128);self.check([self.e.read(self.sym['region_game_crates']+2*i,2) for i in range(4)]==[80,88,144,88],'manual reset restores partial crates')
        for x,y,f in ((80,104,1),(80,88,1),(128,88,3),(160,72,0)):self.act(x,y,f)
        self.act(208,96,1);self.check(self.quest(5)==2,'real crate and plate solution reveals nook clue');self.snapshot('02-storehouse-solved');self.leave_interior(16)
        self.act(320,150,1);self.act(432,256,1);self.act(456,256,1)
        for cls in (1,2,3):
            self.equip_class(cls);self.goto(440,298 if cls<3 else 305);self.face(1);self.tap('A',2,45);self.settle()
            self.check(self.state().quests.objectives[0]&1<<(cls-1),f'actual class{cls} collision credits target');self.snapshot(f'03-practice-{cls}')
            if cls==2:self.refused_equip_case()
        self.act(320,150,1);self.check(self.quest(0)==3,'workshop reward claimed once')
        self.goto(344,234);self.step(12,'UP');self.settle();self.check(self.get('room')==21,'garden doorway');self.act(64,136,1)
        for i,(x,y) in enumerate(((72,90),(120,90),(168,122))):
            self.goto(x,y);self.face(1);self.step(45);self.tap('SELECT',2,18);self.settle();self.check(self.get('region_game_garden_step',1)==i+1,'distinct real roll advances one leaf')
        self.act(184,64,1);self.check(self.quest(9)==3,'garden reward earned by real rolls');self.snapshot('04-garden-complete');self.leave_interior(16)
    def regional_quests(self):
        self.equip_class(1);self.enter_basin();self.snapshot('05-basin-entry')
        self.act(264,216);self.cast(4,240,199);self.check(self.state().quests.objectives[1]==3,'sluice and Nature restore dry road')
        self.goto(120,232);self.act(120,232)
        self.cast(4,98,44);self.cast(7,184,88);self.act(184,88)
        self.check(self.quest(2)==3,'Water companion recruited through basin care');self.check(any(c.form_id==13 for c in self.roster().instances),'Water exists as owned instance');self.snapshot('06-water-recruited')
        self.act(72,44);self.check(self.quest(5)==3,'visible hinted nook awards woven belt');self.assign(3,13);self.select_form(13)
        self.enter_town();self.act(264,252);self.check(self.quest(1)==3,'dry-road boots claimed')
        self.foundry();self.cast(13,80,120);self.check(self.get('region_game_foundry_step',1)==0,'wrong first foundry tone gives no progress')
        self.cast(1,48,72);self.act(48,128);self.check(self.get('region_game_foundry_step',1)==0,'foundry manual reset works without power')
        self.cast(1,48,72);self.cast(13,80,120);self.cast(7,96,80);self.act(96,80)
        self.check(self.quest(3)==3,'three actual powers recruit Metal');self.snapshot('07-metal-recruited')
        self.assign(1,16);self.cast(16,184,72);self.check(self.quest(7)==3,'Metal tune opens latch and awards sword')
        self.cast(16,96,80);self.check(self.quest(10)==3,'Metal repairs bell and earns ring')
        self.assign(1,10);self.cast(1,48,72);self.cast(10,152,120);self.check(self.quest(8)==2,'Fire and Stone craft finish')
        self.leave_interior(16);self.act(320,150,1);self.check(self.quest(8)==3,'craft reward delivered at workshop')
        self.enter_basin();self.goto(360,63);self.step(7,'UP');self.settle();self.check(self.get('room')==19,'Tide courtyard doorway')
        self.cast(13,64,86);self.act(48,132);self.check(self.e.bytes(self.sym['region_game_pool_levels'],2)==bytes(2),'pool reset never needs an equipped power')
        self.cast(13,64,86);self.cast(13,176,86);self.act(64,130);self.act(176,130)
        self.check(self.quest(4)==3,'base Water9 completes paired pools without evolved power');self.check(self.selected().trial_flags&16,'Water personal trial recorded');self.snapshot('08-paired-pools')
        self.leave_interior(17);self.goto(120,232);self.act(120,232);self.select_form(13)
        self.open_tab(3);before=bytes(self.selected());self.tap('SELECT',2,4);self.check(self.get('game_state')==CONFIRM,'Water evolution requires confirmation');self.e.screenshot(self.out/'water-confirmation.png');self.tap('B',2,4);self.check(bytes(self.selected())==before,'decline preserves exact Water instance')
        self.tap('SELECT',2,4);self.tap('A',2,3);self.settle();self.check(self.selected().form_id==14,'confirmed Water evolution completes');self.check(self.selected().equipped[self.selected().selected_command]==9,'Water evolution keeps old command');self.close_menu()
        self.goto(296,140);self.ready();self.tap('R');self.settle();self.check(abs(self.get('px')-296)<=3,'retained Water9 fills rather than teleports')
        self.open_tab(3);self.tap('R',2,25);self.settle();self.check(self.selected().equipped[self.selected().selected_command]==10,'growth journal selects newly learned Water10');self.close_menu();self.ready();self.tap('R');self.settle()
        self.check(abs(self.get('px')-424)<=1 and abs(self.get('py')-124)<=1,'Water10 links to the other authored basin');self.snapshot('09-water-evolved-shortcut')
    def personal_wishes(self):
        # The first four personal trials are earned here too; the old-save
        # fixture never invents their flags. This makes quest6 a real return.
        self.enter_town();self.act(104,232);self.goto(240,302);self.step(6,'DOWN');self.settle();self.check(self.get('room')==1,'town south path returns to Grove')
        self.assign(1,4);self.assign(3,10)
        aids=((184,280,1),(296,208,1),(320,72,1),(80,136,4),(400,136,4),(304,280,4))
        for i,(x,y,form) in enumerate(aids):
            if self.get('hp')<=4:self.act(120,248)
            self.cast(form,x,y+12);self.check(self.roster().lifetime_field_aid[0]&(1<<i),f'original Grove aid{i} earned by controller')
        self.goto(240,302);self.step(10,'DOWN');self.settle();self.check(self.get('room')==0,'Grove south return')
        # Wind trial through its existing campaign portal.
        self.act(196,128);self.check(self.get('room')==4,'east campaign portal');self.act(204,75);self.check(self.get('room')==14,'wind personal-trial door')
        for x,y,n in ((88,80,2),(88,128,1)):
            for _ in range(n):self.cast(7,x,y)
        self.check(any(c.form_id in (7,8) and c.trial_flags&4 for c in self.roster().instances),'Wind personal wish completed')
        self.leave_interior(4);self.goto(120,142);self.step(8,'DOWN');self.settle();self.check(self.get('room')==0,'wind route returns to village')
        self.act(80,128);self.check(self.get('room')==9,'west campaign portal');self.act(208,130);self.check(self.get('room')==15,'Stone personal-trial door')
        for x,y,f in ((88,104,1),(88,88,1),(120,88,3),(152,72,0)):self.act(x,y,f)
        self.cast(10,200,80);self.check(any(c.form_id in (10,11) and c.trial_flags&8 for c in self.roster().instances),'Stone personal wish completed')
        self.leave_interior(9);self.goto(120,142);self.step(8,'DOWN');self.settle();self.check(self.get('room')==0,'Stone route returns to village')
        self.goto(120,32);self.step(8,'UP');self.settle();self.goto(168,260)
        for _ in range(25):
            if self.get('room')==16:break
            self.face(1);self.tap('A',2,22);self.settle()
        self.check(self.get('room')==16,'revisit town through guarded Grove sign');self.act(182,250);self.check(self.quest(6)==3,'all four real wishes earn return reward');self.snapshot('10-all-eleven-quests')
    def lifecycle(self):
        self.assign(1,16);self.select_form(16);self.ready();self.tap('R');self.settle();self.snapshot('11-metal-reselected-from-storage')
        self.assign(3,14);self.select_form(14);self.ready();self.tap('R');self.settle();self.snapshot('11-water-reselected-from-storage')
        # L selection is intentionally volatile until a normal save event.
        self.act(104,232)
        self.check(all(self.quest(q)==3 for q in range(11)),'all eleven regional quests claimed')
        before=bytes(self.state().equipment);quests=bytes(self.state().quests)
        for x,y in ((320,150),(88,152),(264,252),(182,250)):self.act(x,y)
        self.check(bytes(self.state().equipment)==before and bytes(self.state().quests)==quests,'repeated town rewards are byte-identical no-ops')
        self.snapshot('11-idempotent-revisit');save=self.out/'11-idempotent-revisit.sav'
        self.e.close();self.e=Emulator(self.rom);self.e.load_save(save);self.e.reset();self.step(150);self.tap('START',2,35);self.settle()
        self.check(bytes(self.state().equipment)==before and bytes(self.state().quests)==quests,'independent SRAM boot retains exact regional ledgers');self.check(self.get('room')==16,'finished-story regional checkpoint stays in town');self.check(self.selected().form_id==14,'evolved Water remains selected across SRAM reboot')
        self.enter_basin();self.goto(184,264)
        for _ in range(80):
            if self.get('game_state')==DEAD:break
            self.step(20)
        self.check(self.get('game_state')==DEAD,'ordinary enemy damage reaches death without injected HP');self.e.screenshot(self.out/'ordinary-death.png');self.tap('A',2,30);self.settle()
        self.check(self.get('room')==17 and self.get('hp')>0,'normal death retry reenters valid basin checkpoint');self.check(bytes(self.state().equipment)==before and bytes(self.state().quests)==quests,'death retry duplicates no reward and loses no quest');self.snapshot('12-death-retry')
    def cadence(self,label,count=180):
        self.settle();self.step(20);frames=[];flips=0;cycles=[];old=self.get('frame');page=self.e.read(0x04000000,2)&16
        for _ in range(count):
            self.step(1);new=self.get('frame');frames.append((new-old)&0xffffffff);old=new;now=self.e.read(0x04000000,2)&16;flips+=now!=page;page=now;cycles.append(self.get('render_cycles'))
        self.timings[label]={'hardware_frames':count,'game_updates':sum(frames),'page_flips':flips,'max_render_cycles':max(cycles),'cycles_per_hardware_frame':280896,'measurement':'actual emulated GBA hardware frames; not host elapsed time'}
    def run(self,scope):
        self.town_and_training();self.cadence('town_idle')
        if scope=='town':return
        self.regional_quests();self.cadence('basin_idle')
        if scope=='regional':return
        self.personal_wishes();self.lifecycle()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',required=True,type=Path);p.add_argument('--symbols',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--legacy-save',type=Path,default=ROOT/'tests/fixtures/v4/finished-ending.sav');p.add_argument('--scope',choices=('town','regional','full'),default='full');a=p.parse_args()
    run=RegionJourney(a.rom,a.symbols,a.output,a.legacy_save)
    try:run.run(a.scope)
    except Exception as exc:
        run.failures.append({'error':str(exc),'status':run.status()});run.e.screenshot(run.out/'failure.png');run.e.state(run.out/'failure.state');(run.out/'failure.sav').write_bytes(run.e.bytes(0x0e000000,32768));raise
    finally:run.report();run.e.close()
    return 0
if __name__=='__main__':raise SystemExit(main())
