#!/usr/bin/env python3
"""Frozen native regression for retiring Caldera Bell's unsupported shortcut.

The fixture is an explicitly synthetic, validated checkpoint of authenticated
earned SRAM. Controller input alone checks the old marker and walks the full
45→44→43→42→39→38 return. No fresh acquisition or gameplay RAM writes claimed.
"""
from pathlib import Path
from collections import deque
import argparse
import json
import shutil

from connected_roads_guardian_native import Probe,sha

ROOT=Path(__file__).resolve().parents[1]

class MagmaReturnProbe(Probe):
    def __init__(self,args,fixture,provenance):
        super().__init__(args,fixture,provenance)
        self.report.update(scope=__doc__,suite='connected-roads-magma-return',route=[],
            probe_sha256=sha(__file__),shared_probe_sha256=sha(ROOT/'tests/connected_roads_guardian_native.py'))
        source=args.output/'test-source';source.mkdir(exist_ok=True)
        for name in ('connected_roads_magma_return_native.py','connected_roads_guardian_native.py'):
            shutil.copyfile(ROOT/'tests'/name,source/name)
        assert ('magma_art_rooms' in self.sym and 'magma_game_puzzle' in self.sym)

    def settle(self):
        super().settle()
        # Ordinary arrivals deliberately save while PLAY continues. A cold
        # completion assertion must observe that writer finish explicitly.
        for _ in range(1200):
            if not self.get('save_feedback_background') and not self.get('save_requested'):
                self.check(not self.get('save_failed'),'ordinary background writer finished before cold-save checks');return
            self.step(1)
            if self.get('game_state')!=1:super().settle()
        raise AssertionError(('Background arrival save did not finish',self.status()))

    def mask(self):
        room=self.get('room');assert 38<=room<=45
        if room not in self.cache:
            addr=self.sym['magma_art_rooms']+(room-38)*28
            w,h=self.e.read(addr,2),self.e.read(addr+2,2)
            assert (w,h)==((480,320) if room<40 else (240,160))
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
        for (source,_),(end,_) in self.pairs.items():
            if source!=room:continue
            lo,hi=end['aperture']
            for d in range(32):
                for c in range(lo,hi):
                    x,y={'N':(c,d),'E':(w-1-d,c),'S':(c,h-1-d),'W':(d,c)}[end['edge']]
                    b[y*w+x]=int(d<5)
        positions=[]
        if room in (42,43,44):
            cells=self.e.bytes(self.sym['magma_game_puzzle'],2)
            positions=[(48+(c%7)*24,32+(c//7)*18) for c in cells[:1 if room==42 else 2]]
        elif room==39:positions=[(176 if self.state().quests.objectives[35]&1 else 128,264)]
        elif room==38:positions=[(144,232)]
        for x,y in positions:
            for yy in range(max(0,y-11),min(h,y+11)):
                lo,hi=max(0,x-11),min(w,x+11);b[yy*w+lo:yy*w+hi]=b'\1'*(hi-lo)
        return b,w,h

    def goto(self,tx,ty):
        # The all128 checkpoint has faster equipped movement than minimal12.
        # Use the retained journey's four-pixel goal tolerance so fixed-point
        # motion cannot oscillate forever around an unreachable integer pixel.
        room=self.get('room')
        for _ in range(500):
            self.settle();assert self.get('room')==room,('Unexpected doorway',room,self.status())
            x,y=self.get('px'),self.get('py')
            if abs(x-tx)+abs(y-ty)<=4:return
            b,w,h=self.mask();start=y*w+x;goal=ty*w+tx;assert not b[goal]
            todo=deque([goal]);parent={goal:None}
            while todo and start not in parent:
                p=todo.popleft();xx,yy=p%w,p//w
                for n in (p-1,p+1,p-w,p+w):
                    if 0<=n<w*h and abs(n%w-xx)+abs(n//w-yy)==1 and not b[n] and n not in parent:parent[n]=p;todo.append(n)
            assert start in parent,('No walk path',room,x,y,tx,ty)
            path=[];p=start
            while parent[p] is not None:p=parent[p];path.append(p)
            direction=path[0]-start;length=1
            for i in range(1,len(path)):
                if path[i]-path[i-1]!=direction:break
                length+=1
            if length<=2 and len(path)>length:
                turn=path[length]-path[length-1]
                if not b[start+turn] and not b[start+turn*2]:direction=turn;length=2
            self.step(max(1,min(6,int(length/1.8))),{1:16,-1:32,w:128,-w:64}[direction])
        raise AssertionError(('Navigation stalled',self.status(),tx,ty))

    def descend(self,target):
        old=self.get('room')
        # Room44's side service stair is intentionally still usable. Cross the
        # middle aisle first so this case proves the distinct southern stairs.
        if old in (43,44):self.goto(120,112)
        self.goto(120,140);self.settle()
        for _ in range(600):
            self.step(1,128)
            if self.get('room')!=old:break
        self.settle();self.check(self.get('room')==target,'ordinary southern stair returns to the preceding area')
        if old in (43,44,45):
            self.check(self.get('checkpoint_spawn')==0,'descending stair preserves canonical checkpoint0')
            self.check((self.get('px'),self.get('py'))==(216,80),'descending stair arrives beside its matching upstairs threshold')
        self.report['route'].append(target)

    def run(self):
        self.boot();self.check(self.get('room')==45,'validated checkpoint starts in Caldera Bell')
        self.check(self.get('magma_game_machine_stage',1)==5,'completed machine reconstructs without replay')
        before=self.state();quest=bytes(before.quests);roster=bytes(before.roster);equipment=bytes(before.equipment)
        self.goto(208,124);self.step(1,128);self.step(2);self.step(2,1);self.step(3);self.settle()
        self.check(self.get('room')==45,'A at the retired report marker cannot travel')
        self.goto(208,136)
        self.check(201<=self.get('px')<216 and 129<=self.get('py')<144,'walking negative case starts inside the retired footprint')
        self.step(5,16);self.settle()
        self.check(self.get('room')==45,'walking on the retired report footprint cannot travel')
        self.e.shot(self.out/'01-caldera-retired-marker.png')
        self.report['route']=[45]
        for target in (44,43,42,39):self.descend(target)
        self.cross(38);self.report['route'].append(38)
        self.check(self.report['route']==[45,44,43,42,39,38],'full ordinary reverse route reaches Kilnstep')
        self.check(self.get('checkpoint_spawn')==1,'field-to-town boundary retains canonical north checkpoint1')
        after=self.state()
        self.check(bytes(after.quests)==quest,'machine progress, all quest rewards and flags remain exact')
        self.check(bytes(after.roster)==roster and bytes(after.equipment)==equipment,'return traversal grants no extra companion or equipment')
        self.e.shot(self.out/'02-caldera-walked-home.png')
        self.power_cut('cold-caldera-return');self.check(self.get('room')==38 and self.get('checkpoint_spawn')==1,'walked return survives cold Continue')
        self.check(bytes(self.state().quests)==quest,'Q32 machine/report result survives cold return')
        self.report['result']='PASS'

    def finish(self,error=None):
        if error:self.report.update(result='FAIL',error=str(error),status=self.status())
        self.report['final_status']=self.status();self.report['frames']=self.frame
        (self.out/'magma-return-native.json').write_text(json.dumps(self.report,indent=2)+'\n');self.e.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fixtures',type=Path,default=ROOT/'build/connected-road-checkpoints-r0')
    p.add_argument('--diagnostic',action='store_true')
    for name in ('rom','symbols','bridge'):p.add_argument('--'+name,type=Path,required=True);p.add_argument('--'+name+'-sha',required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    proof=json.loads((args.fixtures/'provenance.json').read_text())
    assert proof['source_sha256']=='eec8efbfeaf83a51b66faa0c8e9d6a3061af36b88fb6d7b3aa77fbc47107122a'
    row=next(r for r in proof['fixtures'] if (r['room'],r['spawn'])==(45,0))
    fixture=args.fixtures/row['path'];assert sha(fixture)==row['sha256'] and row['validated_and_roundtripped']
    copied=args.output/fixture.name;shutil.copyfile(fixture,copied)
    provenance={'source':str(args.fixtures/'provenance.json'),'source_sha256':sha(args.fixtures/'provenance.json'),
        'authenticated_earned_source_sha256':proof['source_sha256'],'checkpoint':row,'scope':'Synthetic checkpoint only; no fresh acquisition'}
    probe=MagmaReturnProbe(args,copied,provenance)
    try:probe.run()
    except BaseException as exc:probe.finish(exc);raise
    else:probe.finish();print('PASS:',args.output/'magma-return-native.json')

if __name__=='__main__':main()
