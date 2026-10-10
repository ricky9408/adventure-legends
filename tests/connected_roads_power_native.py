#!/usr/bin/env python3
"""Native91/106 performance beside connected-road exterior strips.

Cold-load the validated owned checkpoint fixture, assign an actually owned
eligible member, select its learned command, summon and cast through buttons.
For power cases only actor coordinates are explicitly prepared. Enemies,
effects, progression, collision, gates and timing stay active. These are synthetic-fixture regression
cases, never fresh progression acquisition. Separate representative arrival
captures use the bridge's verified internal I/O accessor for write-only BLDY.
"""
from __future__ import annotations
import argparse
import ctypes as C
import json
import shutil
import sys
from pathlib import Path

from connected_roads_native import ROOT,RoadSuite,KEYS,Save,Save5Tests,sha


class RoadPowerSuite(RoadSuite):
    def __init__(self,args):
        super().__init__(args)
        self.assignments=[]
        catalog=ROOT/'assets/creatures/source'
        self.forms={f['id']:f for p in sorted(catalog.glob('forms-*.json'))for f in json.loads(p.read_text())}
        self.abilities={f['id']:f for p in sorted(catalog.glob('abilities-*.json'))for f in json.loads(p.read_text())}
        for source in [Path(__file__).resolve(),*sorted(catalog.glob('forms-*.json')),*sorted(catalog.glob('abilities-*.json'))]:
            relative=str(source.relative_to(ROOT));target=self.out/'test-source'/relative
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            self.candidate['test_sources'][relative]=sha(target)

    def load(self,*args,**kwargs):
        super().load(*args,**kwargs)
        self.e.lib.eb_io16.argtypes=[C.c_void_p,C.c_uint]
        self.e.lib.eb_io16.restype=C.c_uint

    def shot(self,name,moving_key=None):
        super().shot(name,moving_key)
        brightness=self.e.lib.eb_io16(self.e.ptr,0x54)
        row=self.images[-1]
        row['verified_internal_io']={'accessor':'eb_io16','BLDY':brightness,
                                     'BLDCNT':self.e.lib.eb_io16(self.e.ptr,0x50)}
        (self.out/row['path']).with_suffix('.json').write_text(json.dumps(row,indent=2)+'\n')
        self.check('native internal BLDY confirms clear captured frame',brightness==0,
                   {'image':row['path'],'internal_io':row['verified_internal_io']})

    def state(self):
        result=super().state()
        names=('face','ability_cd','ability_max','hero_hp_q4','return_power_kind','return_power_time',
               'return_power_age','return_power_direction','return_power_origin_x','return_power_origin_y',
               'horizons_power_kind','horizons_power_time','horizons_power_age','horizons_power_direction',
               'horizons_power_origin_x','horizons_power_origin_y')
        result.update({n:self.g(n,signed=True)for n in names if n in self.sym})
        return result

    def save_state(self):
        return Save.from_buffer_copy(self.e.bytes(self.sym['adventure_save'],C.sizeof(Save)))

    def pause_commit(self):
        assert self.wait(lambda:self.g('game_state')==3 and not self.g('save_requested') and
                         not self.g('save_feedback_background'),1600),self.state()

    def choose_command(self,command):
        self.phase='selection_controls'
        roster=self.save_state().roster
        eligible=[i for i,c in enumerate(roster.instances)if c.flags&1 and
                  any(v['ability_id']==command and v['level']<=c.level for v in self.forms[c.form_id]['learnset'])]
        assert eligible,('No genuinely owned eligible member',command)
        slot=eligible[0];identity=roster.instances[slot].instance_id
        self.tap('START');self.tap('DOWN');self.tap('A')
        assert self.g('game_state')==3 and self.g('journal_tab')==2,self.state()
        for _ in range(4):
            if self.g('quickparty_menu_slot')==0:break
            self.tap('RIGHT')
        for _ in range(162):
            if self.g('quickparty_menu_candidate')==slot:break
            self.tap('DOWN')
        self.check('Party buttons find genuinely owned eligible member',self.g('quickparty_menu_candidate')==slot,
                   {'command':command,'roster_index':slot,'instance_id':identity})
        assert self.g('quickparty_menu_candidate')==slot
        self.tap('A');self.pause_commit();self.tap('START')
        self.step(3,'L+UP');self.step(3)
        roster=self.save_state().roster
        self.check('L buttons select assigned individual',roster.party[roster.selected_party]==slot)
        assert roster.party[roster.selected_party]==slot
        self.tap('START');self.tap('DOWN');self.tap('RIGHT');self.tap('A')
        assert self.g('game_state')==3 and self.g('journal_tab')==3,self.state()
        for _ in range(12):
            if self.g('progression_menu_command')==command:break
            self.tap('RIGHT')
        assert self.g('progression_menu_command')==command,(command,self.state())
        self.tap('A');self.pause_commit();self.tap('START')
        selected=self.save_state().roster.instances[slot]
        self.check('Growth A selects learned command without changing identity',
                   selected.equipped[selected.selected_command]==command and selected.instance_id==identity,
                   {'form':selected.form_id,'level':selected.level,'instance_id':selected.instance_id,'command':command})
        assert selected.equipped[selected.selected_command]==command
        if not self.g('summoned'):self.tap('B')
        assert self.g('summoned') and self.g('game_state')==1,self.state()
        assert self.wait(lambda:not self.g('ability_cd') and not self.g('save_requested') and
                         not self.g('save_feedback_background'),1600),self.state()
        self.assignments.append({'case':self.case,'command':command,'member':slot,'form':selected.form_id,
                                 'instance_id':identity,'selection':'Party/Growth/L/B controller buttons only'})

    def power(self,room,command,orientation):
        self.load(self.fixture_by_room[room])
        self.choose_command(command)
        edge=2 if room in (62,66,70)else 0
        road=next(r for r in self.rows if r['room']==room and r['edge']==edge and
                  (room!=62 or r['target']==61))
        self.phase='setup'
        self.prepare(*self.mouth_start(road,road['center']),edge=road['edge'],suppress=False)
        # Every case begins in the actual exterior strip. Face using a real
        # movement input, while remaining well inside the five-pixel threshold.
        edge={'outward':road['edge'],'tangent':(road['edge']+1)%4,'inward':(road['edge']+2)%4}[orientation]
        self.phase='measured';self.step(1,KEYS[edge]);self.step(3)
        self.check('power preparation remains in intended source room',self.g('room')==room,self.state())
        assert self.g('room')==room
        prefix='return'if command==91 else'horizons'
        before=self.state();cast_frame=self.e.frame
        self.step(1,'R');self.step(1)
        accepted=self.g(prefix+'_power_kind')==command and self.g(prefix+'_power_time')>0 and self.g('ability_cd')>0
        self.check('R starts actual placed power at exterior strip',accepted,
                   {'command':command,'orientation':orientation,'input_hw':cast_frame,'before':before,'after':self.state()})
        assert accepted
        reduction=75-self.e.read(self.sym['gear_stats']+9,1)
        expected=max(1,self.abilities[command]['cooldown_updates']-reduction)
        self.check('native cast retains authored cooldown under existing equipment',self.g('ability_max')==expected,
                   {'authored':self.abilities[command]['cooldown_updates'],'reduction':reduction,'actual':self.g('ability_max')})
        self.step(12);self.shot('power-%02d-%03d-%s-active'%(room,command,orientation))
        self.check('placed effect remains active for its authored simulation',self.g(prefix+'_power_time')>0,self.state())
        completed=self.wait(lambda:not self.g(prefix+'_power_time') and not self.g('ability_cd'),800)
        self.check('power and cooldown complete without suppression or room escape',completed and self.g('room')==room,self.state())
        self.step(20);self.bound_check('power recovery leaves actors and camera bounded')

    def report(self):
        super().report()
        path=self.out/'report.json';data=json.loads(path.read_text())
        data['suite']=__doc__
        data['power_assignments']=self.assignments
        data['power_scope']={'rooms':self.a.rooms,'commands':self.a.commands,
                             'directions':self.a.directions,
                             'selection_and_cast':'real Party/Growth/L/B/directional/R input',
                             'preparation':'actor coordinates only; no enemy, effect, gate or progress writes',
                             'timing':'all hardware frames from facing input through cast, active effect, cooldown and recovery; selection/cold/setup labeled separately'}
        data['clear_capture_probes']={'executed':not self.a.skip_clear_probes,'roads':[0,5,4,10,14,42,49,65],'doors':[1,3],'stairs':[[43,42]],
                                      'brightness':'verified eb_io16 reads internal I/O; busRead of write-only BLDY is never used',
                                      'preparation':'separate inherited seam/door cases retain logged source actor and enemy preparation; stair case is controller-only',
                                      'prior_failure':'acceptance-c2 retains the unsupported write-only bus observation; acceptance-c2-r2 uses software latches and displayed pages'}
        path.write_text(json.dumps(data,indent=2)+'\n')

    def run(self):
        for room in self.a.rooms:
            for command in self.a.commands:
                for orientation in self.a.directions:
                    self.section('power-%02d-%03d-%s'%(room,command,orientation),
                                 lambda room=room,command=command,orientation=orientation:self.power(room,command,orientation))
        if not self.a.skip_clear_probes:
            for index in (0,5,4,10,14,42,49,65):
                road=self.rows[index]
                self.section('clear-road-%02d'%index,lambda road=road:self.seam(road,road['center'],'center'))
            for index in (1,3):
                door=self.doors[index]
                self.section('clear-door-%d'%index,lambda door=door:self.door(door))
            self.section('clear-stair-43-42',lambda:self.stair(43,42,216))
        self.case='suite-verification'
        self.check('all fixture input bytes remain unchanged',all(sha(self.a.fixtures/r['path'])==r['sha256']for r in self.fixtures['fixtures']))
        self.check('power cases used only actor-coordinate RAM preparation',all(w['symbol']in
                   ('px','py','px_q8','py_q8','cx','cy','cx_q8','cy_q8')for w in self.writes if w['case'].startswith('power-')))
        cadence=self.cadence(self.measured)
        self.check('every measured frame passes native update, flip, cycle and publication limits',
                   not any(cadence[k]for k in ('update_misses','flip_misses','cycle_overruns','publication_spills')),cadence)
        self.report();self.trace.close()
        if self.e:self.e.close()
        Save5Tests.doClassCleanups()
        print(json.dumps({'output':str(self.out),'cases':len(self.cases),'failures':sum(not c['passed']for c in self.checks),'cadence':cadence}),flush=True)
        return int(any(not c['passed']for c in self.checks))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True)
    p.add_argument('--source-manifest',type=Path,required=True)
    p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True)
    p.add_argument('--bridge',type=Path,default=ROOT/'build/connected-roads-native-bridge/bridge.so')
    p.add_argument('--fixtures',type=Path,default=ROOT/'build/connected-road-checkpoints-r0')
    p.add_argument('--rooms',nargs='+',type=int,default=[30,38,46,62,66,70])
    p.add_argument('--commands',nargs='+',type=int,choices=[91,106],default=[91,106])
    p.add_argument('--directions',nargs='+',choices=['outward','tangent','inward'],default=['outward','tangent','inward'])
    p.add_argument('--skip-clear-probes',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    sys.exit(RoadPowerSuite(p.parse_args()).run())


if __name__=='__main__':main()
