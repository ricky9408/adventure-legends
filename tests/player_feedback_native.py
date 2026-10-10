#!/usr/bin/env python3
"""Reconstructed native QA harness after workspace loss on 2026-10-06.

Copy into the restored repository's tests directory alongside the bridge.
This reconstruction must be rerun; it is not the historical tested source hash.
All controller actions run on mGBA. Late-path preparation and same-ROM render
branches are logged separately and never counted as controller acquisition.
"""
from __future__ import annotations
import argparse,ctypes as C,gzip,hashlib,json,os,shutil,struct,subprocess,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
from mgba_runner import Emulator,keymask
from test_save5 import Save
LIMIT=280896

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Native(Emulator):
    def __init__(self,rom,bridge):
        self.lib=C.CDLL(str(bridge));self.ptr=None
        functions=[('eb_open',[C.c_char_p],C.c_void_p),('eb_close',[C.c_void_p],None),('eb_frames',[C.c_void_p,C.c_uint,C.c_uint],None),('eb_read',[C.c_void_p,C.c_uint32,C.c_uint],C.c_uint32),('eb_write',[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint],None),('eb_rgb',[C.c_void_p,C.c_void_p],None),('eb_framecounter',[C.c_void_p],C.c_uint),('eb_reset',[C.c_void_p],None),('eb_load_save',[C.c_void_p,C.c_char_p],C.c_int),('eb_save',[C.c_void_p,C.c_char_p],C.c_int),('eb_faults',[C.c_void_p],C.c_uint),('eb_state',[C.c_void_p,C.c_char_p,C.c_int],C.c_int)]
        for name,args,ret in functions:
            f=getattr(self.lib,name);f.argtypes=args;f.restype=ret
        if hasattr(self.lib,'eb_bytes'):
            self.lib.eb_bytes.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint];self.lib.eb_bytes.restype=None
        self.ptr=self.lib.eb_open(str(rom).encode());assert self.ptr,'mGBA open failed'
    def bytes(self,address,length):
        if not hasattr(self.lib,'eb_bytes'):return super().bytes(address,length)
        result=(C.c_ubyte*length)();self.lib.eb_bytes(self.ptr,address,result,length);return bytes(result)
    def save(self,path):
        cloned=bool(self.lib.eb_save(self.ptr,str(path).encode()));visible=self.bytes(0x0e000000,32768)
        if not cloned:Path(path).write_bytes(visible)
        assert Path(path).read_bytes()==visible,'export differs from cartridge SRAM'
        return 'mCore.savedataClone' if cloned else 'mCore.busRead8 exact 32768-byte cartridge SRAM'

class Run:
    def __init__(self,a):
        self.a=a;self.out=a.output.resolve()
        if self.out.exists() and any(self.out.iterdir()):raise FileExistsError('Use a fresh output directory; evidence is never overwritten: '+str(self.out))
        self.out.mkdir(parents=True,exist_ok=True);self.rom=a.rom.resolve();self.symbols=a.symbols.resolve()
        self.hashes={'rom_sha256':sha(self.rom),'symbols_sha256':sha(self.symbols),'test_sha256':sha(__file__),'reconstructed_after_workspace_loss':True}
        for option,key in (('expected_rom_sha','rom_sha256'),('expected_symbols_sha','symbols_sha256')):
            expected=getattr(a,option,None)
            if expected:assert self.hashes[key]==expected,(key,self.hashes[key],expected)
        sources=self.out/'test-source';sources.mkdir();self.hashes['test_sources']={}
        for relative in ('tests/player_feedback_native.py','tests/player_feedback_mgba_bridge.c','tools/mgba_bridge.c','tools/mgba_runner.py','tests/test_save5.py','tests/test_save4.py'):
            source=ROOT/relative;target=sources/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);self.hashes['test_sources'][relative]=sha(target)
        self.sym={v[2]:int(v[0],16) for line in self.symbols.read_text().splitlines() if len(v:=line.split())==3}
        self.bridge=self.out/'bridge.so'
        subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(ROOT/'tests/player_feedback_mgba_bridge.c'),'-I'+str(ROOT/'tools/sysroot/usr/include'),'-L'+str(ROOT/'tools/sysroot/usr/lib/x86_64-linux-gnu'),'-Wl,-rpath,'+str((ROOT/'tools/sysroot/usr/lib/x86_64-linux-gnu').resolve()),'-o',str(self.bridge),'-lmgba'],check=True)
        self.hashes['bridge_sha256']=sha(self.bridge)
        self.hashes['libmgba_sha256']=sha(ROOT/'tools/sysroot/usr/lib/x86_64-linux-gnu/libmgba.so')
        self.checks=[];self.writes=[];self.inputs=[];self.frames=[];self.cases=[];self.case='';self.e=None;self.phase_override=None;self.emulator_id=0;self.state_loads=0;self.complete=False
        self.fixture=ROOT/'tests/fixtures/v5-revision9/covenants-all128-72-cold.sav';provenance=json.loads((self.fixture.parent/'provenance.json').read_text());f=next(f for f in provenance['fixtures'] if f['path'].endswith(self.fixture.name));assert sha(self.fixture)==f['sha256'];self.fixture_sha=f['sha256']
    def g(self,n,w=4):return self.e.read(self.sym[n],w)
    def put(self,n,v,w=4,offset=0,reason='late-path state preparation'):
        self.writes.append({'case':self.case,'emulator_id':self.emulator_id,'frame':self.e.frame,'symbol':n,'offset':offset,'width':w,'value':v,'reason':reason});self.e.write(self.sym[n]+offset,v&((1<<(8*w))-1),w)
    def save_state(self):return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
    def state(self):return {n:self.g(n) for n in ('game_state','room','px','py','frame','journal_tab','journal_nav_category','title_option','save_failed','save_feedback_background','roll_ticks','roll_cd','game_shop_reward_xp','game_shop_reward_gold') if n in self.sym}
    def check(self,label,value,detail=None):
        row={'case':self.case,'check':label,'passed':bool(value)}
        if detail is not None:row['detail']=detail
        self.checks.append(row)
        if not value:print('FAIL',self.case,label,detail or self.state(),flush=True)
    def step(self,n=1,keys=0,phase='measured'):
        if phase=='measured' and self.phase_override:phase=self.phase_override
        self.inputs.append({'case':self.case,'emulator_id':self.emulator_id,'frame':self.e.frame,'frames':n,'keys':keymask(keys),'phase':phase});previous=self.g('frame');page=self.e.read(0x04000000,2)&16
        for _ in range(n):
            self.e.frames(1,keys);now=self.g('frame');current=self.e.read(0x04000000,2)&16
            row={'case':self.case,'emulator_id':self.emulator_id,'hw':self.e.frame,'phase':phase,'delta':(now-previous)&0xffffffff,'flip':int(page!=current),'cycles':self.g('render_cycles'),'mode':self.g('game_state'),'room':self.g('room'),'x':self.g('px'),'y':self.g('py'),'bg':self.g('save_feedback_background'),'faults':self.e.lib.eb_faults(self.e.ptr)}
            row['camera_x']=self.g('camera_x');row['camera_y']=self.g('camera_y')
            for metric in ('save_begin_cycles','save_begin_max_cycles','save_step_cycles','save_step_max_cycles','render_world_cycles','render_card_cycles','render_actors_cycles'):
                if metric in self.sym:row[metric]=self.g(metric)
            row['music']={name:self.g(name) for name in ('music_faults','music_recoveries','music_stopped','music_irq_count','music_irq_late_max','music_track','music_source_cursor') if name in self.sym}
            if 'render_profile_serial' in self.sym:
                serial=self.g('render_profile_serial')
                if not serial&1:
                    profile={name:self.g('render_profile_'+name) for name in ('world','card','actors','save_begin','save_step','frame','state','room','cycles','total','update','save','render','music','deferred_actors','vblank_cycles','vblank_start','vblank_end','commit') if 'render_profile_'+name in self.sym}
                    if self.g('render_profile_serial')==serial:row['completed_profile']={'serial':serial,**profile}
            self.frames.append(row);previous=now;page=current
    def tap(self,k,hold=2,release=3):self.step(hold,k);self.step(release)
    def wait(self,pred,limit=800,keys=0):
        for _ in range(limit):
            if pred():return True
            self.step(1,keys)
        return False
    def boot(self,saved=False):
        if self.e:self.check('mGBA core/log faults remain zero',self.e.lib.eb_faults(self.e.ptr)==0);self.e.close()
        self.emulator_id+=1;self.e=Native(self.rom,self.bridge)
        if saved:self.e.load_save(self.fixture if saved is True else saved);self.e.reset()
        self.step(160,phase='boot');self.check('title ready',self.g('game_state')==0)
    def play(self,saved=False):
        self.phase_override='cold_continue' if saved else 'cold_new_game';self.boot(saved);self.tap('A');self.wait(lambda:self.g('game_state') not in (6,10,12))
        for _ in range(15):
            if self.g('game_state') in (2,14):self.tap('A')
            else:break
        self.wait(lambda:self.g('game_state')==1 and (not saved or self.g('frame')>0))
        self.continue_checkpoint=None
        if saved:
            self.continue_checkpoint={'frame':self.g('frame'),'room':self.g('room'),'health_q4':self.g('hero_hp_q4'),'maximum_q4':self.e.read(self.sym['gear_stats'],2),'gold':self.save_state().economy.gold,'save_failed':self.g('save_failed')}
        self.step(100);self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1000);self.check('controller reaches play',self.g('game_state')==1);self.phase_override=None
    def shot(self,name):
        # A mode can change before its native bitmap reaches the display.
        # Wait through both pages before naming a visible proof capture.
        self.step(3);path=self.out/(name+'.png');self.e.screenshot(path)
        path.with_suffix('.json').write_text(json.dumps({'case':self.case,'emulator_id':self.emulator_id,'hardware_frame':self.e.frame,'rom_sha256':self.hashes['rom_sha256'],'png_sha256':sha(path),'status':self.state()},indent=2)+'\n')
    def navigate(self,x,y,limit=220):
        for _ in range(limit):
            dx=x-self.g('px');dy=y-self.g('py')
            if abs(dx)<=2 and abs(dy)<=2:return True
            k=('RIGHT' if dx>0 else 'LEFT') if abs(dx)>2 else ('DOWN' if dy>0 else 'UP');self.step(1,k)
            if self.g('game_state')!=1:return False
        return False
    def location(self,room,x,y):
        for n,v in [('game_state',1),('room',room),('px',x),('py',y),('px_q8',x*256),('py_q8',y*256),('cx',x+14),('cy',y+3),('cx_q8',(x+14)*256),('cy_q8',(y+3)*256),('transition_lock',0),('arrival_input_mask',0),('prev_keys',0),('hitstop',0),('camera_x',0),('camera_y',0),('cache_valid',0)]:self.put(n,v)
        self.put('cache_valid',0,offset=4)
    def static_floor(self,room,x,y):
        if room>=22:
            first,name=next((first,name) for first,name in reversed(((22,'north'),(30,'south'),(38,'magma'),(46,'underwater'),(54,'return'),(62,'horizons'),(70,'covenants'))) if room>=first);record=self.sym[name+'_art_rooms']+(room-first)*28;width=self.e.read(record,2);height=self.e.read(record+2,2)
            if x<5 or y<5 or x>=width-5 or y>=height-5:return False
            rows=self.e.read(record+20);bands=self.e.read(record+24);band=bands+2*self.e.read(rows+2*y,2);count=self.e.read(band,2)
            return not any(self.e.read(band+2+i*4,2)<=x<self.e.read(band+4+i*4,2) for i in range(count))
        if room>=16:
            record=self.sym['region_art_rooms']+(room-16)*20;width=self.e.read(record,2);height=self.e.read(record+2,2);pointer=self.e.read(record+12);count=self.e.read(record+16,2)
            if x<5 or y<5 or x>=width-5 or y>=height-5:return False
            return not any(x+5>=a and x-5<a+w and y+5>=b and y-5<b+h for a,b,w,h in (struct.unpack('<hhhh',self.e.bytes(pointer+i*8,8)) for i in range(count)))
        if room==0:
            if not (12<=x<=227 and 28<=y<=152):return False
            p=self.sym['asset_solids_village'];return not any(a<=x<a+w and b<=y<b+h for a,b,w,h in (struct.unpack('<hhhh',self.e.bytes(p+i*8,8)) for i in range(18)))
        return (12<=x<468 and 24<=y<308) if room==1 else (12<=x<228 and 32<=y<148)
    def section(self,name,fn):
        self.case=name;start=len(self.checks);write_start=len(self.writes)
        try:fn()
        except Exception as ex:self.check('case completed without harness exception',False,repr(ex));traceback.print_exc()
        finally:self.phase_override=None
        self.cases.append({'case':name,'checks':len(self.checks)-start,'preparation_writes':len(self.writes)-write_start});self.report()

    def title(self):
        self.boot();self.tap('SELECT');self.check('Select does not start empty title',self.g('game_state')==0);self.phase_override='cold_new_game';self.tap('A');self.wait(lambda:self.g('game_state')==14);self.phase_override=None;self.check('A starts the village opening',self.g('game_state')==14)
        for cancel in ('B','START','A+B'):
            self.boot(True);before=self.e.bytes(0x0e000000,32768);self.tap('DOWN');self.tap('A');self.check(cancel+' opens guarded New adventure',self.g('game_state')==9);self.step(30);self.check('unconfirmed wait preserves New prompt',self.g('game_state')==9);self.step(3);self.tap(cancel);self.check(cancel+' returns to title',self.g('game_state')==0);self.check(cancel+' leaves SRAM unchanged',self.e.bytes(0x0e000000,32768)==before)
        self.boot(True);self.phase_override='cold_continue';self.tap('A');self.wait(lambda:self.g('game_state')==1);self.step(100);self.phase_override=None;self.check('title A continues existing history',sum(bool(i.flags&1) for i in self.save_state().roster.instances)==72)
        self.boot(True);self.tap('DOWN');self.step(45,'A');self.check('held opening A never confirms New',self.g('game_state')==9);self.step(3);self.phase_override='cold_new_game';self.tap('A');self.wait(lambda:self.g('game_state')==14);self.phase_override=None;self.check('fresh A confirms New opening',self.g('game_state')==14 and sum(bool(i.flags&1) for i in self.save_state().roster.instances)==2)
    def menus(self):
        self.play();self.tap('START');self.check('Start opens hub',self.g('game_state')==3 and self.g('journal_tab')==13)
        for k,c in [('RIGHT',1),('LEFT',0),('DOWN',2),('DOWN',4),('DOWN',6),('DOWN',0)]:self.tap(k);self.check(k+' selects visible hub cell '+str(c),self.g('journal_nav_category')==c)
        self.tap('A');self.check('A opens Items',self.g('journal_tab')==15);self.tap('B');self.check('B goes from Items to hub',self.g('journal_tab')==13 and self.g('game_state')==3)
        self.tap('RIGHT');self.tap('A');self.check('A opens Gear',self.g('journal_tab')==4);self.tap('B');self.check('B goes from Gear to hub',self.g('journal_tab')==13)
        self.tap('LEFT');self.tap('DOWN');self.tap('A');self.check('A opens Party',self.g('journal_tab')==2);self.tap('B');self.tap('RIGHT');self.tap('A');self.check('A opens Growth',self.g('journal_tab')==3);self.tap('B');self.tap('LEFT');self.tap('DOWN');self.tap('A');self.check('A opens Map',self.g('journal_tab')==1);self.tap('B');self.tap('RIGHT');self.tap('A');self.check('A opens Quests',self.g('journal_tab')==14);self.tap('A');self.check('A opens current quest',self.g('journal_tab')==0);self.tap('B');self.check('B returns quest list',self.g('journal_tab')==14);self.tap('B')
        c=self.g('journal_nav_category');self.tap('LEFT+RIGHT');self.check('conflicting directions leave category alone',self.g('journal_nav_category')==c);self.tap('SELECT+A');self.check('Select+A has no hidden menu action',self.g('journal_tab')==13);self.tap('START');self.check('Start closes journal',self.g('game_state')==1)
        self.tap('START');self.step(19,'DOWN');self.check('held direction repeats after deliberate delay',self.g('journal_nav_category')==4);self.step(3);self.tap('B');self.check('B closes hub',self.g('game_state')==1);self.tap('START');self.shot('native-journal-hub');self.tap('START')
        before=(self.g('px'),self.g('py'));self.step(30,'SELECT');self.check('field Select has no movement/dodge',before==(self.g('px'),self.g('py')) and self.g('roll_ticks')==self.g('roll_cd')==0)
        selected=self.save_state().roster.selected_party;self.step(4,'L+RIGHT');self.check('hold L+Right opens picker without commit',self.g('quickparty_open')==1 and self.save_state().roster.selected_party==selected);self.step(3);self.check('release L commits quick slot',self.save_state().roster.selected_party==1);self.step(4,'L+UP');self.step(3,'L+START');self.check('Start cancels picker into hub',self.g('game_state')==3 and not self.g('quickparty_open'));self.step(3);self.tap('B')
        selected=self.save_state().roster.selected_party;self.step(18,'L');self.step(3);self.check('long neutral L hold never becomes a tap cycle',self.save_state().roster.selected_party==selected)
        self.tap('L');self.tap('L');self.check('fresh repeated L taps cycle only assigned slots and wrap',self.save_state().roster.selected_party==selected)
        self.step(3,'L+UP+RIGHT');self.step(3);self.check('ambiguous quick-party direction does not commit or tap-cycle',self.save_state().roster.selected_party==selected)
        self.step(3,'L+DOWN');self.step(3);self.check('empty quick-party slot does not commit or tap-cycle',self.save_state().roster.selected_party==selected)
        summoned=self.g('summoned');position=(self.g('px'),self.g('py'));self.step(3,'L+B+RIGHT');self.step(8,'L+A+R+SELECT+START');self.check('B cancels picker and consumes further actions until L release',self.g('game_state')==1 and self.g('summoned')==summoned and (self.g('px'),self.g('py'))==position and self.save_state().roster.selected_party==selected);self.step(3);self.tap('B');self.check('fresh B works after canceled picker releases L',self.g('summoned')!=summoned);self.tap('B')
    def legacy_shop(self):
        self.play(True);self.check('legacy migration starts with zero economy',self.save_state().economy.gold==0 and self.save_state().economy.boss_claims==0);self.check('walk north around town exits',self.navigate(120,100));self.check('walk to merchant',self.navigate(56,100));self.tap('A');self.check('walk and A opens village merchant',self.g('game_state')==11);assert self.g('game_state')==11
        self.tap('A');self.check('A asks before spending',self.g('game_shop_confirm')==1);self.tap('B');self.check('B cancels purchase',self.g('game_state')==11 and not self.g('game_shop_confirm'));self.tap('A');self.tap('A');self.check('insufficient gold cannot spend',self.g('game_state')==11 and self.save_state().economy.gold==0);self.tap('B')
        for _ in range(3):self.tap('DOWN')
        bonuses=[]
        for boss,gold in enumerate((60,100,160)):
            before=self.save_state();stats_before=self.e.bytes(self.sym['gear_stats'],14);self.tap('A');self.tap('A');self.check('legacy claim uses transaction '+str(boss),self.g('game_state')==12);self.wait(lambda:self.g('game_state')!=12);after=self.save_state();self.check('legacy named treasure receipt '+str(boss),self.g('game_state')==13);self.check('legacy boss pays exact once '+str(boss),after.economy.gold-before.economy.gold==gold and after.economy.relics&(1<<boss) and after.economy.boss_claims&(1<<boss));stats_after=self.e.bytes(self.sym['gear_stats'],14)
            if boss==0:self.check('seed relic adds one actual health heart',int.from_bytes(stats_after[:2],'little')==int.from_bytes(stats_before[:2],'little')+16)
            if boss==1:self.check('sky relic removes eight actual power cooldown updates',stats_after[9]==stats_before[9]-8)
            if boss==2:self.check('core relic adds four actual attack q4',stats_after[6]==stats_before[6]+4)
            bonuses.append({'boss':boss,'gold':after.economy.gold,'hero_hp_q4':self.g('hero_hp_q4'),'gear_stats':list(stats_after)})
            if boss==0:self.shot('native-boss-relic-receipt')
            self.tap('A')
        # Content11 exposes four additional missing treasures for this genuine
        # pre-economy completed fixture. Loading pays none; explicit recovery
        # must finish before the merchant returns to three purchase rows.
        for treasure,gold in enumerate((80,100,120,160)):
            before=self.save_state();before_hp=self.g('hero_hp_q4');before_cd=self.g('ability_cd')
            self.tap('A');self.tap('A');self.check('later recovery uses transaction '+str(treasure),self.g('game_state')==12)
            self.wait(lambda:self.g('game_state')!=12);after=self.save_state()
            self.check('later named treasure receipt '+str(treasure),self.g('game_state')==13)
            self.check('later treasure pays exactly once '+str(treasure),after.economy.gold-before.economy.gold==gold and after.economy.later_claims==((1<<(treasure+1))-1))
            self.check('later legacy recovery preserves earned quest and companion history '+str(treasure),bytes(after.quests)==bytes(before.quests) and bytes(after.roster)==bytes(before.roster))
            self.check('later collection neither refills HP nor resets cooldown '+str(treasure),self.g('hero_hp_q4')==before_hp and self.g('ability_cd')==before_cd)
            self.tap('A')
        self.check('claim row disappears after all earned claims',self.g('game_shop_selection')==0);cash=self.save_state().economy.gold
        for _ in range(3):self.tap('DOWN')
        self.check('merchant three-item navigation wraps without repeat claim',self.g('game_shop_selection')==0 and self.save_state().economy.gold==cash)
        self.tap('A');self.tap('A');self.wait(lambda:self.g('game_state')!=12);self.check('purchase tonic commits 18 gold and one supply',self.save_state().economy.gold==cash-18 and self.save_state().economy.supplies[0]==1)
        self.tap('DOWN');self.tap('A');self.tap('A');self.wait(lambda:self.g('game_state')!=12);self.check('purchase spirit dew commits 24 gold',self.save_state().economy.gold==cash-42 and self.save_state().economy.supplies[1]==1)
        self.tap('DOWN');self.tap('A');self.tap('A');self.wait(lambda:self.g('game_state')!=12);self.check('purchase permanent edge upgrade',self.save_state().economy.gold==cash-162 and self.save_state().economy.upgrade==1);same=bytes(self.save_state().economy);self.tap('A');self.tap('A');self.check('duplicate edge spends nothing',bytes(self.save_state().economy)==same);self.tap('B');self.tap('B')
        self.tap('START');self.tap('A');before_hp=self.g('hero_hp_q4');self.tap('A');self.check('tonic A asks before use after seed heart increase',self.g('game_shop_confirm')==1);self.tap('B');self.check('B cancels item confirmation in Items',self.g('journal_tab')==15 and self.save_state().economy.supplies[0]==1);self.tap('A');self.tap('A');self.wait(lambda:self.g('game_state')!=12);self.check('confirmed tonic consumes once and heals',self.save_state().economy.supplies[0]==0 and self.g('hero_hp_q4')>before_hp)
        self.tap('DOWN');self.tap('A');self.check('ready-power dew not consumed',self.save_state().economy.supplies[1]==1 and not self.g('game_shop_confirm'));self.tap('START');path=self.out/'controller-shop-claims.sav';method=self.e.save(path);self.cases.append({'case':'controller-shop-export','method':method,'sha256':sha(path)});expected=bytes(self.save_state().economy);self.play(path);self.check('independent cold reload preserves all purchases and claims',bytes(self.save_state().economy)==expected);self.cases.append({'case':'legacy-claim-effects-observation','bonuses':bonuses})
    def combat_save(self):
        self.play();self.location(1,144,224);self.put('face',1);self.put('transition_lock',1000)
        for en in range(6):self.put('enemies',0,offset=en*20+8)
        for offset,value in ((0,144),(4,209),(8,1),(12,0),(16,0)):self.put('enemies',value,offset=offset)
        self.put('enemy_hp_q4',1);self.put('enemy_phases',255,w=1);self.put('defeated_enemy_mask',0,w=1);self.step(4,phase='prepared');before=self.save_state();before_xp=sum(before.roster.instances[i].xp for i in before.roster.party if i<160);kills=self.g('kills');blocked=self.g('save_feedback_blocked_frames')
        self.step(2,'A');self.wait(lambda:self.g('kills')>kills,50);after=self.save_state();xp=sum(after.roster.instances[i].xp for i in after.roster.party if i<160)-before_xp
        self.check('native attack defeats prepared enemy exactly once',self.g('kills')==kills+1);self.check('native kill earns six gold',after.economy.gold-before.economy.gold==6);self.check('visible EXP equals actual party XP increase',xp>0 and self.g('game_shop_reward_xp')==xp,{'actual_party_xp':xp,'shown':self.g('game_shop_reward_xp')});self.check('visible gold equals actual earned gold',self.g('game_shop_reward_gold')==6);self.shot('native-combat-exp-gold')
        start=len(self.frames);x=self.g('px');initial_hitstop=self.g('hitstop');self.step(70,'RIGHT');self.wait(lambda:not self.g('save_feedback_background'),500);window=self.frames[start:];active=[f for f in window if f['bg']];motion_latency=next((i+1 for i,f in enumerate(window[:70]) if f['x']!=x),None);writer_motion_steps=sum(a['bg'] and b['x']!=a['x'] for a,b in zip(window[:70],window[1:70]))
        self.check('background input latency is bounded by existing combat hitstop',motion_latency is not None and motion_latency<=initial_hitstop+2 and writer_motion_steps>0,{'hardware_frames_to_move':motion_latency,'initial_combat_hitstop':initial_hitstop,'movement_steps_during_writer':writer_motion_steps})
        self.check('background writer observed during real movement',bool(active) and self.g('px')>x,{'active_frames':len(active),'x_before':x,'x_after':self.g('px')});self.check('ordinary save does not enter frozen save mode',all(f['mode']==1 for f in window) and self.g('save_feedback_blocked_frames')==blocked);self.check('every active writer frame advances simulation',all(f['delta']==1 for f in active),{'missed':sum(f['delta']!=1 for f in active)});self.check('every active writer frame stays below hardware cycle limit',all(f['cycles']<=LIMIT for f in active),{'peak':max((f['cycles'] for f in active),default=0)})
        self.step(80);self.check('dead enemy never pays again',self.g('kills')==kills+1 and self.save_state().economy.gold==after.economy.gold);self.check('ordinary native save completes without error',not self.g('save_failed'));path=self.out/'native-combat-save.sav';method=self.e.save(path);gold=self.save_state().economy.gold;self.play(path);self.check('combat earnings survive real cold reload',self.save_state().economy.gold==gold);self.cases.append({'case':'native-combat-writer','actual_xp':xp,'export_method':method,'active_frames':len(active),'peak_cycles':max((f['cycles'] for f in active),default=0),'input_latency_frames':motion_latency,'initial_combat_hitstop':initial_hitstop,'movement_steps_during_writer':writer_motion_steps})
    def garden(self):
        self.play();self.location(21,72,98);self.put('transition_lock',1000);stateoffset=Save.quests.offset+2;old=self.e.read(self.sym['adventure_save']+stateoffset,1);self.put('adventure_save',(old&~12)|4,w=1,offset=stateoffset,reason='synthetic active garden quest; walking reachability only');self.put('region_game_garden_step',0,w=1);self.step(3,phase='prepared')
        self.check('walk onto first garden stone',self.navigate(72,72));self.check('first stone advances once',self.g('region_game_garden_step',1)==1);self.step(25);self.check('standing on first stone does not repeat',self.g('region_game_garden_step',1)==1);self.check('walk to second garden stone',self.navigate(120,72));self.check('second stone advances in order',self.g('region_game_garden_step',1)==2);self.navigate(168,72);self.navigate(168,104);self.check('third stone reached on foot completes sequence',self.g('region_game_garden_step',1)==3);self.check('garden route requires no dodge state',self.g('roll_ticks')==self.g('roll_cd')==0);self.shot('native-garden-walkable')
    def full_roster_scroll(self):
        self.play(True);self.check('scrolling writer starts from authentic72-member roster',sum(bool(c.flags&1) for c in self.save_state().roster.instances)==72);blocked=self.g('save_feedback_blocked_frames');start=len(self.frames);self.wait(lambda:self.g('room')==1,180,'UP');self.check('controller walk enters scrolling Grove',self.g('room')==1);self.step(160,'UP');self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1200);window=self.frames[start:];active=[f for f in window if f['bg'] and f['room']==1];camera_moves=sum(a['bg'] and a['room']==b['room']==1 and (a['camera_x'],a['camera_y'])!=(b['camera_x'],b['camera_y']) for a,b in zip(window,window[1:]))
        self.check('actual camera scroll occurs during full-roster background write',bool(active) and camera_moves>0,{'active_frames':len(active),'camera_moves':camera_moves});self.check('full-roster scrolling writer stays in live play',all(f['mode']==1 for f in active) and self.g('save_feedback_blocked_frames')==blocked);self.check('full-roster scrolling writer advances every hardware frame',all(f['delta']==1 and f['flip'] for f in active));peak=max((f['cycles'] for f in active),default=0);self.check('full-roster scrolling writer meets native cycle budget',peak<=LIMIT,{'peak_cycles':peak});self.check('full-roster travel save finishes without error',not self.g('save_failed') and self.g('game_state')==1);self.cases.append({'case':'full-roster-scrolling-writer','controller_only':True,'active_frames':len(active),'camera_moves':camera_moves,'peak_cycles':peak})
    def save_fault(self):
        self.play();self.put('adventure_save',6,offset=Save.economy.offset);self.put('adventure_save',6,w=2,offset=Save.economy.offset+8);self.put('save_requested',1,reason='inject an ordinary dirty request for cartridge fault test');self.put('save_feedback_ordinary',1);reached=self.wait(lambda:self.g('writer_phase')==13 and self.g('save_feedback_background'),500);self.check('native writer reaches precommit verification',reached)
        if not reached:return
        destination=self.g('writer_destination');position=self.g('writer_position');address=0x0e000000+destination+min(position+600,6000);value=self.e.read(address,1)^1;self.writes.append({'case':self.case,'frame':self.e.frame,'address':hex(address),'value':value,'width':1,'reason':'inject inactive SRAM corruption before native verification'});self.e.write(address,value,1);self.wait(lambda:not self.g('save_feedback_background'),500)
        self.check('native corruption produces visible failure',self.g('save_failed')==1 and self.g('save_failure_notice')==1);self.check('failed ordinary save keeps play responsive',self.g('game_state')==1);x=self.g('px');self.step(8,'RIGHT');self.check('movement continues after save error',self.g('px')>x);self.shot('native-save-error');path=self.out/'native-failed-writer.sav';self.e.save(path)
        self.tap('START');self.tap('UP');self.tap('A');self.check('Controls exposes retry page',self.g('journal_tab')==16);self.check('navigation keeps unresolved error visible',self.g('save_failed')==1);self.tap('A');self.check('retry keeps failure visible until successful commit',self.g('save_failed')==1 and self.g('game_state')==6);self.wait(lambda:self.g('game_state')!=6,700);self.check('A retry clears save error after native successful commit',not self.g('save_failed'));self.play(path);self.check('failed new bank leaves previous committed economy loadable',self.save_state().economy.gold==0)
    def reward_caps(self):
        self.play();self.location(1,144,224);self.put('face',1);self.put('transition_lock',1000);s=self.save_state()
        for slot in s.roster.party:
            if slot>=160:continue
            offset=Save.roster.offset+slot*24;self.put('adventure_save',50,w=1,offset=offset+2,reason='synthetic max-level boundary fixture');self.put('adventure_save',470596,offset=offset+4,reason='synthetic XP-cap boundary fixture')
        self.put('adventure_save',9998,offset=Save.economy.offset,reason='synthetic near-wallet-cap earned gold');self.put('adventure_save',9998,w=2,offset=Save.economy.offset+8)
        for en in range(6):self.put('enemies',0,offset=en*20+8)
        for offset,value in ((0,144),(4,209),(8,1),(12,0),(16,0)):self.put('enemies',value,offset=offset)
        self.put('enemy_hp_q4',1);self.put('enemy_phases',255,w=1);self.put('defeated_enemy_mask',0,w=1);self.step(4,phase='prepared');kills=self.g('kills');self.tap('A');self.wait(lambda:self.g('kills')>kills,60);self.check('wallet clamps native kill reward at9999',self.save_state().economy.gold==9999 and self.g('game_shop_reward_gold')==1);self.check('max-XP party displays zero EXP earned',self.g('game_shop_reward_xp')==0 and all(self.save_state().roster.instances[i].xp==470596 for i in s.roster.party if i<160));self.wait(lambda:not self.g('save_feedback_background'),1000);self.check('bounded cap earnings save validly',not self.g('save_failed'))
    def death_retry(self):
        self.play();prior=self.out/'death-prior-valid.sav';self.e.save(prior);self.location(1,144,224)
        for en in range(6):self.put('enemies',0,offset=en*20+8)
        self.put('adventure_save',6,offset=Save.economy.offset,reason='synthetic ordinary dirty economy before death');self.put('adventure_save',6,w=2,offset=Save.economy.offset+8);self.put('save_requested',1);self.put('save_feedback_ordinary',1);self.wait(lambda:self.g('save_feedback_background')==1,200);self.check('ordinary writer is in flight before hostile hit',self.g('save_feedback_background')==1)
        for n,v in [('hero_hp_q4',1),('hp',1),('invuln',0),('guard_invuln',0),('stone_guard',0),('hitstop',0)]:self.put(n,v,reason='synthetic one-health collision setup; actual hostile update must cause death')
        for offset,value in ((0,self.g('px')),(4,self.g('py')),(8,1),(12,0),(16,0)):self.put('enemies',value,offset=offset)
        self.put('enemy_hp_q4',16);self.put('enemy_phases',255,w=1);deaths=self.g('deaths');self.step(1);self.wait(lambda:self.g('game_state')==4,20);self.check('native hostile hit causes one real death',self.g('game_state')==4 and self.g('deaths')==deaths+1 and self.g('hero_hp_q4')==0);self.check('death occurs while ordinary writer is active',self.g('save_feedback_background')==1)
        during=self.out/'death-writer-inflight.sav';self.e.save(during);self.tap('SELECT');self.tap('R');self.check('Select and R are inert on death screen',self.g('game_state')==4 and self.g('deaths')==deaths+1);self.tap('A');self.wait(lambda:self.g('game_state')==1,500);self.check('A retry restores live checkpoint and health',self.g('game_state')==1 and self.g('room')==1 and self.g('checkpoint_spawn')==0 and self.g('hero_hp_q4')==self.e.read(self.sym['gear_stats'],2));self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1200);self.check('writer and retry finish without save corruption',not self.g('save_failed') and self.save_state().economy.gold==6)
        completed=self.out/'death-retry-complete.sav';self.e.save(completed);self.play(during);self.check('power cut at death loads prior valid committed bank',self.save_state().economy.gold==0 and self.g('hero_hp_q4')>0 and not self.g('save_failed'));self.play(completed);loaded=self.continue_checkpoint;self.check('completed retry restores full health and pending earnings before active enemies advance',loaded is not None and loaded['room']==1 and loaded['gold']==6 and loaded['health_q4']==loaded['maximum_q4'] and not loaded['save_failed'],loaded);self.check('completed retry keeps checkpoint and earnings after the ordinary writer settles',self.g('room')==1 and self.save_state().economy.gold==6 and self.g('hero_hp_q4')>0 and not self.g('save_failed'))
    def supply_caps(self):
        self.play(True);economy=Save.economy.offset;self.put('adventure_save',1000,offset=economy,reason='synthetic earned-money setup for stock-cap coverage');self.put('adventure_save',1000,w=2,offset=economy+8);self.navigate(120,100);self.navigate(56,100);self.tap('A');self.check('full original equipment bag still opens merchant',self.g('game_state')==11 and sum(bool(i.item_id) for i in self.save_state().equipment.bag)==48)
        for count in range(1,10):
            self.tap('A');self.tap('A');self.wait(lambda:self.g('game_state')!=12);self.check('tonic stock '+str(count)+' persists',self.save_state().economy.supplies[0]==count)
        before=bytes(self.save_state().economy);self.tap('A');self.tap('A');self.check('tenth tonic refused without charge',bytes(self.save_state().economy)==before and self.g('game_state')==11);self.tap('B');self.tap('B');self.tap('START');self.tap('A');self.tap('A');self.check('full-health tonic refuses waste',self.save_state().economy.supplies[0]==9 and not self.g('game_shop_confirm'));self.tap('START');self.put('hero_hp_q4',self.g('hero_hp_q4')-32,reason='synthetic wounded-health setup for explicit item use');self.tap('START');self.tap('A');self.tap('A');self.tap('A');self.wait(lambda:self.g('game_state')!=12);self.check('tonic heals exactly32q4 and consumes one',self.save_state().economy.supplies[0]==8 and self.g('hero_hp_q4')==self.e.read(self.sym['gear_stats'],2));path=self.out/'native-stock-cap.sav';self.e.save(path);expected=bytes(self.save_state().economy);self.play(path);self.check('cap and use outcome survive independent reload',bytes(self.save_state().economy)==expected)
    def power_cooldowns(self):
        path=getattr(self.a,'earned_shop_save',None) or self.out/'controller-shop-claims.sav';assert path.exists(),'Run legacy_shop first to earn relic claims by controller';self.play(path);catalog=ROOT/'assets/creatures/source';forms={f['id']:f for p in sorted(catalog.glob('forms-*.json')) for f in json.loads(p.read_text())};abilities={f['id']:f for p in sorted(catalog.glob('abilities-*.json')) for f in json.loads(p.read_text())}
        self.tap('START');self.tap('RIGHT');self.tap('A')
        for gear_slot,item_id in ((2,52),(3,69),(4,88)):
            for _ in range(5):
                if self.g('gear_menu_slot')==gear_slot:break
                self.tap('RIGHT')
            bag=self.save_state().equipment.bag;reference=next(i for i,item in enumerate(bag) if item.item_id==item_id)
            for _ in range(49):
                if self.g('gear_menu_candidate')==reference:break
                self.tap('DOWN')
            self.tap('A');self.wait(lambda:self.g('game_state')==3,800);self.check('native Gear A equips owned recovery item '+str(item_id),self.save_state().equipment.equipped[gear_slot]==reference)
        self.tap('START');passives=self.save_state().economy;expected_recovery=16+(4 if passives.later_claims&4 else 0);self.check('earned source includes Feather',bool(passives.relics&2));self.check('gear8 and earned Feather8 plus optional Bell4 stack exactly',75-self.e.read(self.sym['gear_stats']+9,1)==expected_recovery,{'expected_recovery':expected_recovery,'later_claims':passives.later_claims});observations=[]
        for command in (1,5,9,13,23,43,67,91,106,122):
            roster=self.save_state().roster;eligible=[i for i,c in enumerate(roster.instances) if c.flags&1 and any(v['ability_id']==command and v['level']<=c.level for v in forms[c.form_id]['learnset'])];assert eligible,('No genuinely owned eligible command',command);slot=eligible[0];self.tap('START');self.tap('DOWN');self.tap('A');self.check('Party opens for command '+str(command),self.g('journal_tab')==2)
            for _ in range(4):
                if self.g('quickparty_menu_slot')==0:break
                self.tap('RIGHT')
            for _ in range(162):
                if self.g('quickparty_menu_candidate')==slot:break
                self.tap('DOWN')
            self.check('72-member collection navigation finds owned command '+str(command),self.g('quickparty_menu_candidate')==slot);prior_party=bytes(self.save_state().roster.party);self.tap('A');self.check('first A inspects stored companion without assignment '+str(command),self.g('quickparty_menu_detail')==1 and bytes(self.save_state().roster.party)==prior_party);self.tap('A');self.wait(lambda:self.g('game_state')==3,800);self.tap('START');self.step(3,'L+UP');self.step(3);self.check('hold L selects the newly assigned member '+str(command),self.save_state().roster.party[self.save_state().roster.selected_party]==slot);self.tap('START');self.tap('DOWN');self.tap('RIGHT');self.tap('A');self.check('Growth opens for chosen member '+str(command),self.g('journal_tab')==3)
            for _ in range(12):
                if self.g('progression_menu_command')==command:break
                self.tap('RIGHT')
            self.check('left/right command preview reaches learned ability '+str(command),self.g('progression_menu_command')==command);prior_roster=bytes(self.save_state().roster);self.tap('A');self.check('first A inspects command without equipping '+str(command),self.g('progression_menu_detail')==1 and bytes(self.save_state().roster)==prior_roster);self.tap('A');self.wait(lambda:self.g('game_state')==3,800);self.tap('START')
            if not self.g('summoned'):self.tap('B')
            self.step(190);cast_frame=self.e.frame;self.tap('R',hold=1,release=1);reduction=75-self.e.read(self.sym['gear_stats']+9,1);expected=max(1,abilities[command]['cooldown_updates']-reduction);record={'command':command,'form':self.save_state().roster.instances[slot].form_id,'authored_base':abilities[command]['cooldown_updates'],'actual_reduction':reduction,'expected':expected,'observed':self.g('ability_max'),'emulator_id':self.emulator_id,'cast_input_hardware_frame':cast_frame};observations.append(record);self.check('native cast keeps stacked gear and earned treasure reduction '+str(command),self.g('ability_cd')>0 and self.g('ability_max')==expected,record);self.step(max(220,expected+10))
        self.cases.append({'case':'native-power-cooldowns','controller_only':True,'casts':observations})
    def town_travel(self):
        self.play();before=self.g('chapter_flags');self.navigate(180,124);self.step(60,'RIGHT')
        self.check('closed east road has a physical nonmodal boundary fence',self.g('room')==0 and self.g('game_state')==1 and 210<=self.g('px')<=220 and self.g('toast_ticks')>0 and self.g('chapter_flags')==before)
        hint=self.g('toast_ticks');position=(self.g('px'),self.g('py'));self.step(3);self.step(3,'RIGHT')
        self.check('held closed-road movement neither crosses nor refreshes hint',self.g('room')==0 and (self.g('px'),self.g('py'))==position and self.g('toast_ticks')==hint-6)
        self.play(True);self.tap('B');self.check('companion summoned before road crossing',self.g('summoned')==1);self.navigate(180,124);self.step(12,'L+RIGHT')
        self.check('quick picker near road pauses movement/travel',self.g('room')==0 and self.g('quickparty_open')==1);self.step(3);self.wait(lambda:self.g('room')==4,90,'RIGHT')
        self.check('controller reaches actual village east boundary and enters ridge',self.g('room')==4);self.wait(lambda:self.g('game_state')==1,500);self.step(25)
        self.check('opposite-edge arrival companion stays close',max(abs(self.g('cx')-self.g('px')),abs(self.g('cy')-self.g('py')))<=32)
        self.wait(lambda:self.g('room')==0,100,'LEFT');self.check('matching ridge west road returns to village east',self.g('room')==0);self.step(25);self.step(12,'LEFT')
        self.check('continuing crossing direction moves into village without bounce',self.g('room')==0);self.step(15);self.check('neutral east arrival stays in village',self.g('room')==0)
        self.navigate(120,109);self.wait(lambda:self.g('room')==9,160,'LEFT');self.check('west road bends above memorial then crosses real boundary',self.g('room')==9)
        self.wait(lambda:self.g('game_state')==1,500);self.step(25);self.wait(lambda:self.g('room')==0,100,'RIGHT');self.step(25);self.step(10,'RIGHT')
        self.check('cave east return arrives on village west and keeps direction',self.g('room')==0);self.step(15);self.check('neutral west arrival stays in village',self.g('room')==0)
        self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1000);self.check('real road crossings save without error',not self.g('save_failed'));self.shot('native-village-connected-roads')
    def portals(self):
        self.play(True);raw=self.e.bytes(self.sym['travel_entries'],self.g('travel_entry_count')*10);rows=[struct.unpack('<BBBBhhBB',raw[i:i+10]) for i in range(0,len(raw),10)];self.check('authored entry table is nonempty',len(rows)>=29,len(rows));outcomes=[]
        for i,(room,action,target,spawn,x,y,w,h) in enumerate(rows):
            cx,cy=x+w//2,y+h//2;choices=[(cx,y+h+14,'UP',[(cx,yy) for yy in range(y+h-1,y+h+15)]),(cx,y-14,'DOWN',[(cx,yy) for yy in range(y-14,y+1)]),(x-14,cy,'RIGHT',[(xx,cy) for xx in range(x-14,x+1)]),(x+w+14,cy,'LEFT',[(xx,cy) for xx in range(x+w-1,x+w+15)])]
            if room==0:choices[0],choices[1]=choices[1],choices[0]
            legal=[v for v in choices if all(self.static_floor(room,xx,yy) for xx,yy in v[3])];self.check(f'entry {i}: has a legal outside-latch approach',bool(legal),{'room':room,'rectangle':[x,y,w,h]})
            if not legal:outcomes.append({'entry':i,'source':room,'target':target,'passed':False,'reason':'no legal straight approach from static floor'});continue
            approach=legal[0][:3];self.location(room,*approach[:2])
            for n in ('save_requested','save_feedback_background','quickparty_open'):self.put(n,0)
            self.put('chapter_flags',15);self.put('summoned',1)
            if room==45:self.put('magma_game_machine_stage',5,w=1)
            if room==53:self.put('underwater_game_guardian_stage',4,w=1)
            for en in range(6):self.put('enemies',0,offset=en*20+8)
            self.step(2,phase='prepared');self.wait(lambda:self.g('room')!=room or self.g('game_state') not in (1,6,10),65,approach[2]);self.step(3);self.wait(lambda:self.g('game_state') not in (6,10,12),500);observed=self.state();ok=self.g('room')==target;self.check(f'entry {i}: walk {room} to {target}',ok,observed)
            if ok:
                distance=max(abs(self.g('cx')-self.g('px')),abs(self.g('cy')-self.g('py')));self.check(f'entry {i}: companion arrives nearby',distance<=32,distance);arrived=self.g('room');self.step(15);self.check(f'entry {i}: neutral arrival never bounces',self.g('room')==arrived)
            outcomes.append({'entry':i,'source':room,'target':target,'action':action,'approach':list(approach),'static_floor_verified':True,'passed':ok,'state':observed});settled=self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),800);self.check(f'entry {i}: destination save settles without error',settled and not self.g('save_failed'))
        self.cases.append({'case':'portal-outcomes','entries':outcomes})
    def render_equivalence(self):
        self.play(True);base=self.out/'same-rom-render-base.state';self.e.state(base);views=[(room,3,13,False) for room in range(78)];views += [(room,3,tab,False) for room in (0,1,22,30,38,46,54,62,70) for tab in (2,3,4,15,16)];views += [(0,11,0,False)]+[(room,13,0,False) for room in (0,3,8,13)];views += [(room,8,3,False) for room in (0,16,62,70)];views += [(room,1,0,True) for room in (0,1,22,30,38,46,54,62,70)];results=[];captures=0
        for index,(room,mode,tab,picker) in enumerate(views):
            branches=[]
            for disabled in (0,1):
                self.e.state(base,load=True);self.state_loads+=1;self.location(room,120,128);self.put('game_state',mode);self.put('journal_tab',tab);self.put('frame',240);self.put('world_mask_disabled',disabled,reason='paired native underlay-culling renderer branch');self.put('quickparty_open',int(picker));self.put('quickparty_candidate',0)
                if mode==8:self.put('evolution_tick',0);self.put('evolution_before',102)
                checkpoints=[]
                for length in (6,14):
                    self.step(length,'L' if picker else 0,phase='prepared_render');checkpoints.append((self.e.screenshot(),self.e.bytes(0x07000000,1024)))
                branches.append(checkpoints)
            for checkpoint,hardware_frames in enumerate((6,20)):
                pair=[branch[checkpoint] for branch in branches];same=pair[0][0].tobytes()==pair[1][0].tobytes() and pair[0][1]==pair[1][1];row={'view':index,'hardware_frames':hardware_frames,'room':room,'state':mode,'journal_tab':tab,'quickparty':picker,'passed':same,'optimized_rgb_sha256':hashlib.sha256(pair[0][0].tobytes()).hexdigest(),'unmasked_rgb_sha256':hashlib.sha256(pair[1][0].tobytes()).hexdigest(),'oam_equal':pair[0][1]==pair[1][1]};results.append(row);self.check(f'prepared render {index} at{hardware_frames}: masked and unmasked native pixels/OAM agree',same,row)
                if not same and captures<8:
                    for label,(pixels,_oam) in zip(('optimized','unmasked'),pair):pixels.save(self.out/(f'mismatch-{index}-at{hardware_frames}-{label}.png'))
                    captures+=1
        self.cases.append({'case':'native-underlay-pixel-equivalence','prepared_view_count':len(views),'comparison_count':len(results),'same_rom_machine_state_branches':self.state_loads,'controller_acquisition_claimed':False,'views':results})
    def report(self):
        measured=[f for f in self.frames if f['phase']=='measured'];exceptions=[f for f in measured if f['cycles']>LIMIT or f['delta']!=1 or not f['flip']];phases={}
        for phase in sorted({f['phase'] for f in self.frames}):
            rows=[f for f in self.frames if f['phase']==phase];phases[phase]={'frames':len(rows),'peak_cycles':max((f['cycles'] for f in rows),default=0),'native_fault_peak':max((f['faults'] for f in rows),default=0),'over_cycle_limit':sum(f['cycles']>LIMIT for f in rows),'missed_updates':sum(f['delta']==0 for f in rows)}
            phases[phase]['music_maxima']={name:max((f.get('music',{}).get(name,0) for f in rows),default=0) for name in ('music_faults','music_recoveries','music_stopped','music_irq_late_max') if name in self.sym}
        d={'suite':'player-feedback-native','complete':self.complete,'requested_cases':self.a.cases.split(','),'scope':'Real native input; controller-only opening/menu/shop cases; individually logged RAM setup in late-path tests','provenance':self.hashes,'fixture_sha256':self.fixture_sha,'hardware_cycle_limit':LIMIT,'checks':self.checks,'failures':[c for c in self.checks if not c['passed']],'cases':self.cases,'game_ram_writes':len(self.writes),'machine_state_loads':self.state_loads,'performance':{'measured_frames':len(measured),'peak_cycles':max((f['cycles'] for f in measured),default=0),'exceptions':len(exceptions),'exception_examples':exceptions[:40],'mGBA_faults':max((f['faults'] for f in self.frames),default=0),'phases':phases,'strict_measured_pacing_pass':not exceptions,'full_frames':'native-frames.jsonl.gz'},'exact_files_unchanged':sha(self.rom)==self.hashes['rom_sha256'] and sha(self.symbols)==self.hashes['symbols_sha256']};(self.out/'report.json').write_text(json.dumps(d,indent=2)+'\n');return d
    def finish(self):
        deferred=[f['completed_profile'] for f in self.frames if f['phase']=='measured' and f.get('completed_profile',{}).get('deferred_actors',0)]
        if deferred:
            bad=[p for p in deferred if not (160<=p['vblank_start']<=p['vblank_end']<228 and p['vblank_cycles']<=83776)]
            self.check('deferred native OBJ work and publication stay wholly inside VBlank',not bad,{'samples':len(deferred),'peak_deferred_actor_cycles':max(p['deferred_actors'] for p in deferred),'peak_vblank_cycles':max(p['vblank_cycles'] for p in deferred),'latest_end_scanline':max(p['vblank_end'] for p in deferred),'failures':bad[:8]})
        measured_music=[f['music'] for f in self.frames if f['phase']=='measured' and f.get('music')]
        if measured_music:
            transport={name:max(f.get(name,0) for f in measured_music) for name in ('music_faults','music_recoveries','music_stopped','music_irq_count','music_irq_late_max')}
            self.check('measured native music transport runs without faults, recovery or stop',all(transport[n]==0 for n in ('music_faults','music_recoveries','music_stopped')) and transport['music_irq_count']>0,transport)
        if self.e:self.check('final native fault count zero',self.e.lib.eb_faults(self.e.ptr)==0);self.e.close();self.e=None
        for name,data in [('native-frames',self.frames),('inputs',self.inputs),('preparation-writes',self.writes)]:
            with gzip.open(self.out/(name+'.jsonl.gz'),'wt') as f:
                for row in data:f.write(json.dumps(row,separators=(',',':'))+'\n')
        self.complete=True
        d=self.report();print(json.dumps({'output':str(self.out),'checks':len(self.checks),'failures':len(d['failures']),'performance':d['performance'],'rom_sha256':self.hashes['rom_sha256']},indent=2));return d

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba');p.add_argument('--symbols',type=Path,default=ROOT/'build/emberbond.sym');p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-rom-sha');p.add_argument('--expected-symbols-sha');p.add_argument('--earned-shop-save',type=Path);p.add_argument('--allow-pacing-exceptions',action='store_true',help='Diagnostic only; all timing exceptions remain in evidence');p.add_argument('--cases',default='title,menus,legacy_shop,town_travel,portals,combat_save,full_roster_scroll,garden,save_fault,supply_caps,reward_caps,death_retry,power_cooldowns');a=p.parse_args();r=Run(a)
    for name in a.cases.split(','):r.section(name,getattr(r,name))
    d=r.finish();return int(bool(d['failures']) or not d['exact_files_unchanged'] or (not a.allow_pacing_exceptions and not d['performance']['strict_measured_pacing_pass']))
if __name__=='__main__':raise SystemExit(main())
