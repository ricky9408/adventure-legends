#!/usr/bin/env python3
"""Native connected-road regression from authenticated minimal12 cold SRAM.

Only the offline fixture's room/spawn are changed through the real codec. The
native probe uses controller input, reset, and read-only observation, never RAM
writes or imported machine states. This is regression, not fresh acquisition.
"""
from pathlib import Path
from collections import deque
import argparse
import ctypes as C
import hashlib
import json
import shutil
import sys

from test_save5 import Save,Save5Tests

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tests/fixtures/v5-revision6/underwater-minimal12-town.sav'
SOURCE_SHA='3f5bbccab022f86b38f4d180e8cf66b04c055791fe4804ddbebbdefb5406aeda'
KEY={'N':64,'E':16,'S':128,'W':32,'A':1,'START':8}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def prepare(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert sha(SOURCE)==SOURCE_SHA
    source_row=next(r for r in json.loads((SOURCE.parent/'provenance.json').read_text())['fixtures'] if r['fixture']==SOURCE.name)
    assert source_row['sha256']==SOURCE_SHA and source_row['controller_only'] and source_row['game_ram_writes']==0
    Save5Tests.setUpClass()
    try:
        t=Save5Tests();t.reset();t.put(SOURCE.read_bytes());s=t.load()
        original=(bytes(s.roster),bytes(s.quests),bytes(s.equipment),bytes(s.economy))
        assert t.lib.save5_quest_state(s.quests,40)==3 and not s.quests.objectives[45]
        assert s.quests.region_flags[4]&128,'Minimal source must have visited the court'
        s.campaign.room=53;s.campaign.spawn=0
        assert t.lib.save5_validate(C.byref(s))
        t.reset();t.store(s);fixture=out/'guardian-minimal12-room53.sav'
        fixture.write_bytes(bytes(t.sram));loaded=t.load()
        assert (loaded.campaign.room,loaded.campaign.spawn)==(53,0)
        assert (bytes(loaded.roster),bytes(loaded.quests),bytes(loaded.equipment),bytes(loaded.economy))==original
        provenance={'scope':__doc__,'source':str(SOURCE.relative_to(ROOT)),
            'source_sha256':sha(SOURCE),'source_provenance_sha256':sha(SOURCE.parent/'provenance.json'),
            'fixture':fixture.name,'fixture_sha256':sha(fixture),'synthetic_changes':['campaign.room','campaign.spawn'],
            'validated_and_roundtripped':True,'all_noncheckpoint_state_unchanged':True,
            'source_q40_claimed':True,'source_q45_unstarted':True,
            'codec_sources':{n:sha(ROOT/'src'/n) for n in ('save5.c','save5.h','save4.c','save4.h')}}
        (out/'guardian-fixture-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
        return fixture,provenance
    finally:Save5Tests.doClassCleanups()

class Emulator:
    """Deliberately offers no gameplay-memory write or machine-state import."""
    def __init__(self,bridge,rom):
        self.lib=C.CDLL(str(Path(bridge).resolve()))
        for n,args,result in [('eb_open',[C.c_char_p],C.c_void_p),('eb_close',[C.c_void_p],None),
            ('eb_frames',[C.c_void_p,C.c_uint,C.c_uint],None),('eb_read',[C.c_void_p,C.c_uint32,C.c_uint],C.c_uint32),
            ('eb_reset',[C.c_void_p],None),('eb_load_save',[C.c_void_p,C.c_char_p],C.c_int),
            ('eb_rgb',[C.c_void_p,C.c_void_p],None)]:
            f=getattr(self.lib,n);f.argtypes=args;f.restype=result
        self.ptr=self.lib.eb_open(str(Path(rom).resolve()).encode());assert self.ptr
    def close(self):
        if self.ptr:self.lib.eb_close(self.ptr);self.ptr=None
    def frames(self,n,keys=0):self.lib.eb_frames(self.ptr,n,keys)
    def read(self,address,width=4):return self.lib.eb_read(self.ptr,address,width)
    def bytes(self,address,size):return bytes(self.read(address+i,1) for i in range(size))
    def reset(self):self.lib.eb_reset(self.ptr)
    def load(self,path):assert self.lib.eb_load_save(self.ptr,str(Path(path).resolve()).encode())
    def shot(self,path):
        from PIL import Image
        pixels=(C.c_ubyte*(240*160*3))();self.lib.eb_rgb(self.ptr,pixels)
        Image.frombytes('RGB',(240,160),bytes(pixels)).save(path)

class Probe:
    def __init__(self,args,fixture,provenance):
        self.args=args;self.out=args.output;self.checks=[];self.inputs=[];self.cache={};self.frame=0
        for path,expected in ((args.rom,args.rom_sha),(args.symbols,args.symbols_sha),(args.bridge,args.bridge_sha)):
            assert expected and sha(path)==expected,('Unpinned probe input',str(path))
        self.rom=self.out/'tested.gba';self.symbols=self.out/'tested.sym'
        shutil.copyfile(args.rom,self.rom);shutil.copyfile(args.symbols,self.symbols)
        self.sym={p[2]:int(p[0],16) for line in self.symbols.read_text().splitlines() if len(p:=line.split())==3}
        for required in ('underwater_game_road_departure','game_road_managed','connected_roads','adventure_save'):assert required in self.sym,required
        self.manifest=json.loads((ROOT/'assets/connected_roads.json').read_text())
        assert not any({e['room'] for e in r['ends']}=={53,46} for r in self.manifest['roads'])
        self.pairs={}
        for road in self.manifest['roads']:
            a,b=road['ends'];self.pairs[a['room'],b['room']]=(a,b)
            if not road.get('one_way'):self.pairs[b['room'],a['room']]=(b,a)
        self.report={'scope':__doc__,'fixture_provenance':provenance,'rom_sha256':sha(self.rom),
            'symbols_sha256':sha(self.symbols),'bridge_sha256':sha(args.bridge),
            'manifest_sha256':sha(ROOT/'assets/connected_roads.json'),'probe_sha256':sha(__file__),
            'game_ram_writes':0,'source_machine_states_loaded':False,'diagnostic_only':args.diagnostic,
            'checks':self.checks,'inputs':self.inputs}
        self.e=Emulator(args.bridge,self.rom);self.e.load(fixture);self.e.reset()
    def get(self,name,width=4):return self.e.read(self.sym[name],width)
    def state(self):return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))
    def q45(self):return self.state().quests.objectives[45]
    def check(self,truth,label):
        self.checks.append({'passed':bool(truth),'label':label,'frame':self.frame,'room':self.get('room')})
        assert truth,(label,self.status())
    def status(self):return {n:self.get(n) for n in ('game_state','room','px','py','checkpoint_spawn','save_failed')}
    def step(self,n,keys=0):
        self.inputs.append([self.frame,n,keys]);self.e.frames(n,keys);self.frame+=n
    def settle(self):
        stable=0;previous=self.get('frame')
        for _ in range(4000):
            mode=self.get('game_state');frame=self.get('frame')
            # A hardware-frame boundary can interrupt enter_room after room and
            # PLAY change but before it queues/presents the arrival save. Wait
            # for completed live updates and an empty scene/save handoff too.
            ready=mode==1 and not self.get('save_requested') and not self.get('scene_present_phase')
            if ready:
                if frame!=previous:stable+=1
                if stable>=3:
                    self.check(not self.get('save_failed'),'ordinary incremental save reports no failure');return
                self.step(1)
            else:stable=0
            previous=frame
            if mode==2:self.step(1,1);self.step(2)
            elif mode in (6,8,10):self.step(1)
            elif mode==1:
                if not ready:self.step(1)
            else:raise AssertionError(('Unexpected gameplay mode',self.status()))
        raise AssertionError(('Frozen job did not settle',self.status()))
    def boot(self):
        self.step(150);self.step(2,8);self.step(90);self.settle();self.step(4);self.settle()
        self.check(self.get('game_state')==1,'cold SRAM resumes through ordinary Continue')
    def power_cut(self,label):
        # mGBA temporary-save lifetime is not a cartridge battery guarantee.
        # Reopen the exact bytes present at the cut; never replace with a fixture
        # or a reconstructed live Save5State, and never load a machine state.
        raw=self.e.bytes(0x0e000000,32768);path=self.out/(label+'.sav');path.write_bytes(raw)
        self.report.setdefault('power_cuts',[]).append({'label':label,'frame':self.frame,
            'sram_sha256':sha(path),'status':self.status(),'bytes_from_live_sram':True})
        self.e.load(path);self.e.reset();self.boot()
    def mask(self):
        room=self.get('room');assert 46<=room<=53
        if room not in self.cache:
            addr=self.sym['underwater_art_rooms']+(room-46)*28
            w,h=self.e.read(addr,2),self.e.read(addr+2,2)
            assert (w,h) in ((240,160),(480,320))
            rows,bands=self.e.read(addr+20),self.e.read(addr+24)
            b=bytearray(w*h);memo={}
            for y in range(h):
                index=self.e.read(rows+2*y,2)
                if index not in memo:
                    count=self.e.read(bands+2*index,2)
                    memo[index]=[(self.e.read(bands+2*(index+1+2*i),2),self.e.read(bands+2*(index+2+2*i),2)) for i in range(count)]
                for lo,hi in memo[index]:b[y*w+lo:y*w+hi]=b'\1'*(hi-lo)
            self.cache[room]=(b,w,h)
        original,w,h=self.cache[room];b=bytearray(original)
        for (source,_),(e,_) in self.pairs.items():
            if source!=room:continue
            lo,hi=e['aperture']
            for d in range(32):
                for c in range(lo,hi):
                    x,y={'N':(c,d),'E':(w-1-d,c),'S':(c,h-1-d),'W':(d,c)}[e['edge']]
                    b[y*w+x]=int(d<5)
        p=self.e.bytes(self.sym['underwater_game_puzzle'],8);ballast=p[2]
        rects=([(100,48,32,12)] if ballast else [(132,80,40,12)]) if room==50 else \
              ([(272,128,24,16)] if ballast else [(208,128,64,16)]) if room==51 else \
              [(66+p[3]*16,60,12,24),(162-p[4]*16,60,12,24)] if room==52 else \
              [(48,56,32,12),(160,56,32,12)] if room==53 and not ballast else []
        for x,y,rw,rh in rects:
            for yy in range(max(0,y-5),min(h,y+rh+5)):
                lo,hi=max(0,x-5),min(w,x+rw+5);b[yy*w+lo:yy*w+hi]=b'\1'*(hi-lo)
        return b,w,h
    def goto(self,tx,ty):
        room=self.get('room')
        for _ in range(900):
            self.settle();assert self.get('room')==room
            x,y=self.get('px'),self.get('py')
            if abs(x-tx)+abs(y-ty)<=2:return
            b,w,h=self.mask();start=y*w+x;goal=ty*w+tx;assert not b[goal],('Blocked target',room,tx,ty)
            todo=deque([goal]);parent={goal:None}
            while todo and start not in parent:
                p=todo.popleft();px,py=p%w,p//w
                for n in (p-1,p+1,p-w,p+w):
                    if 0<=n<w*h and abs(n%w-px)+abs(n//w-py)==1 and not b[n] and n not in parent:parent[n]=p;todo.append(n)
            assert start in parent,('No static walk path',room,x,y,tx,ty)
            path=[];p=start
            while parent[p] is not None:p=parent[p];path.append(p)
            direction=path[0]-start;length=1
            for i in range(1,len(path)):
                if path[i]-path[i-1]!=direction:break
                length+=1
            if length<=2 and len(path)>length:
                turn=path[length]-path[length-1]
                if not b[start+turn] and not b[start+turn*2]:direction=turn;length=2
            self.step(max(1,min(8,int(length/1.3))),{1:16,-1:32,w:128,-w:64}[direction])
        raise AssertionError(('Navigation stalled',self.status(),tx,ty))
    def approach(self,target):
        source,dest=self.pairs[self.get('room'),target];self.goto(*source['arrival']);self.settle();return source,dest
    def cross(self,target,stop=None,offset=0):
        old=self.get('room');source,dest=self.approach(target)
        if offset:
            x,y=source['arrival']
            self.goto(x+offset if source['edge'] in 'NS' else x,y+offset if source['edge'] in 'EW' else y)
            self.settle()
        self.last_cross_offset=(self.get('px') if source['edge'] in 'NS' else self.get('py'))-source['center']
        for _ in range(500):
            self.step(1,KEY[source['edge']])
            if stop and stop():return
            if self.get('room')!=old and not stop:
                self.check(self.get('room')==target,'road crossing reaches its neighbor')
                self.check(self.get('checkpoint_spawn')==dest['saved_spawn'],'road keeps its legal saved spawn')
                self.settle();return
        raise AssertionError(('Road did not cross',old,target,self.status()))
    def run(self):
        self.boot();self.check(self.get('room')==53 and self.q45()==0,'minimal court checkpoint starts before Q45')
        self.check(self.get('underwater_game_guardian_stage',1)==4,'guardian completion reconstructs from earned Q40')
        roster=bytes(self.state().roster);equipment=bytes(self.state().equipment)
        self.cross(52,lambda:self.get('game_state')==10,offset=7)
        self.check(self.get('room')==53 and self.q45()==0,'departure freezes before quest mutation or room change')
        pending=self.get('connected_road_pending');count=self.get('connected_road_count')
        self.check(pending<count,'typed departure retains a bounded pending road owner')
        self.check(self.e.bytes(self.sym['connected_roads']+pending*24,4)==bytes((53,52,1,3)),
                   'pending owner is specifically the west53-to-east52 existing-spawn1 route')
        self.e.shot(self.out/'01-guardian-departure-pending.png')
        self.power_cut('cut-before-departure-commit')
        self.check(self.get('room')==53 and self.q45()==0,'power interruption before commit retains the old cold checkpoint')
        self.cross(52,lambda:self.get('room')==52 and self.get('game_state')==6,offset=7)
        self.check(self.get('room')==52 and self.q45()==1,'typed Q45 fact commits before the52 arrival save')
        self.check(self.last_cross_offset!=0 and self.get('py')==112+self.last_cross_offset,
                   'queued guardian arrival preserves the nonzero road offset rather than falling back to canonical spawn')
        self.e.shot(self.out/'02-guardian-arrival-saving.png')
        self.power_cut('cut-during-arrival-save')
        self.check(self.get('room') in (52,53) and self.q45() in (0,1),'interrupted writer loads a complete old or new checkpoint')
        if self.get('room')==53:self.cross(52)
        self.check(self.get('room')==52 and self.q45()==1,'retry reaches52 with one Q45 fact')
        self.check(bytes(self.state().roster)==roster and bytes(self.state().equipment)==equipment,'travel and interruption grant no roster or equipment changes')
        self.power_cut('cold-arrival-complete')
        self.check(self.get('room')==52 and self.q45()==1,'completed arrival survives cold Continue')
        self.cross(53);self.check(self.q45()==1,'guardian revisit retains its single departure fact')
        self.cross(52);self.check(self.q45()==1,'repeated departure is idempotent')
        for room in (51,48,46):self.cross(room)
        self.check(self.q45()==1,'walking home through adjacent maps does not skip the required Q45 circuit')
        for room in (48,49,48,46):self.cross(room)
        self.check(self.q45()==3,'the original outbound-and-return garden circuit records Q45 bit2')
        self.goto(240,254);self.step(2,128);self.step(2);self.step(2,1);self.step(2);self.settle()
        s=self.state();claimed=(s.quests.states[45>>2]>>((45&3)*2))&3
        self.check(claimed==3 and s.quests.objectives[45]==7,'original return conversation claims the preserved Q45 reward')
        self.e.shot(self.out/'03-return-quest-preserved.png')
        self.power_cut('cold-quest-complete');s=self.state()
        self.check(((s.quests.states[45>>2]>>((45&3)*2))&3)==3,'Q45 reward survives cold Continue')
        self.report['result']='PASS'
    def finish(self,error=None):
        if error:self.report.update(result='FAIL',error=str(error),status=self.status())
        self.report['final_status']=self.status();self.report['frames']=self.frame
        (self.out/'guardian-native.json').write_text(json.dumps(self.report,indent=2)+'\n');self.e.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--diagnostic',action='store_true',help='Provisional candidate; excluded from final acceptance')
    for name in ('rom','symbols','bridge'):p.add_argument('--'+name,type=Path);p.add_argument('--'+name+'-sha')
    args=p.parse_args();fixture,provenance=prepare(args.output)
    if args.prepare_only:print(fixture);return
    for name in ('rom','symbols','bridge'):assert getattr(args,name) and getattr(args,name+'_sha'),name
    probe=Probe(args,fixture,provenance)
    try:probe.run()
    except BaseException as exc:probe.finish(exc);raise
    else:probe.finish();print('PASS:',args.output/'guardian-native.json')

if __name__=='__main__':main()
