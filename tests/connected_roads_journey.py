"""Current-candidate walking adapters; historical journey helpers stay intact.

Use these subclasses (or the mixin first in an existing harness MRO) only with
the connected-roads manifest paired to the tested ROM. This adapts navigation,
not acquisition provenance, fixture policy, timing acceptance, or quest work.
"""
from pathlib import Path
import hashlib
import json

from underwater_journey import UnderwaterJourney
from return_journey import ReturnJourney
from horizons_journey import HorizonsJourney
from covenants_journey import CovenantsJourney

ROOT=Path(__file__).resolve().parents[1]
KEY={'N':'UP','E':'RIGHT','S':'DOWN','W':'LEFT'}

class ConnectedRoadJourneyMixin:
    def road_manifest(self):
        if not hasattr(self,'_connected_road_manifest'):
            base=Path(getattr(self,'source_root',ROOT))
            path=base/'assets/connected_roads.json'
            if not path.is_file():
                raise AssertionError(('Frozen candidate lacks connected-road manifest',str(path)))
            self._connected_road_manifest=json.loads(path.read_text())
            self.connected_road_manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        return self._connected_road_manifest

    def road_pair(self,source,target):
        for road in self.road_manifest()['roads']:
            a,b=road['ends']
            if (a['room'],b['room'])==(source,target):return a,b
            if not road.get('one_way') and (b['room'],a['room'])==(source,target):return b,a
        return None

    def mask(self):
        # Original work/dynamic masks remain authoritative away from boundary
        # strips. This is a navigation estimate only: actual controller motion
        # still proves the production gate and collision at every crossing.
        raw,w,h=super().mask();b=bytearray(raw);area=self.get('room')
        for road in self.road_manifest()['roads']:
            for e in road['ends']:
                if e['room']!=area:continue
                lo,hi=e['aperture'];edge=e['edge']
                for d in range(32):
                    for c in range(lo,hi):
                        x,y={'N':(c,d),'E':(w-1-d,c),'S':(c,h-1-d),'W':(d,c)}[edge]
                        if 0<=x<w and 0<=y<h:b[y*w+x]=int(d<5)
        return b,w,h

    def guardian_walk_home(self):
        self.check(self.get('room')==53,'guardian homeward walk starts in the court')
        for area in (52,51,48,46):self.entry(area)

    def machine_walk_home(self):
        self.check(self.get('room')==45,'machine homeward walk starts in Caldera Bell')
        for area in (44,43,42,39,38):self.entry(area)

    def connected_door(self,target):
        here=self.get('room')
        for door in self.road_manifest().get('doorways',[]):
            if (here,target)==(door['room'],door['target']):
                x,y,w,h=door['footprint'];approach=(x+w//2,y+h+8);key='UP';spawn=0
            elif (here,target)==(door['target'],door['room']):
                approach=(120,132);key='DOWN';spawn=door['saved_spawn']
            else:continue
            self.goto(*approach,radius=2);self.settle()
            for _ in range(600):
                if self.get('room')!=here:break
                self.step(1,key)
            self.settle()
            self.check(self.get('room')==target,'walking through a real house/stair threshold reaches its room')
            self.check(self.get('checkpoint_spawn')==spawn,'house/stair retains its existing checkpoint ID')
            return True
        return False

    def entry(self,target):
        here=self.get('room')
        if (here,target)==(53,46):
            # The historical main-route helper requested its former shortcut.
            # Reach the same town through actual neighboring maps, with no A.
            self.guardian_walk_home();return
        if (here,target)==(45,38):self.machine_walk_home();return
        if 40<=here<=45 and target==(38 if here==40 else 39 if here in (41,42) else here-1):
            self.leave_interior(target);return
        pair=self.road_pair(here,target)
        if not pair:
            if self.connected_door(target):return
            return super().entry(target)
        source,destination=pair
        x,y=source['arrival']
        self.goto(x,y,radius=2)
        self.check(self.get('room')==here,'road approach stays on its source map')
        self.settle()
        before_checkpoint=self.get('checkpoint_spawn')
        for _ in range(600):
            if self.get('room')!=here:break
            self.step(1,KEY[source['edge']])
        self.settle()
        self.check(self.get('room')==target,f'outward {KEY[source["edge"]]} crossing reaches area {target}')
        self.check(self.get('checkpoint_spawn')==destination['saved_spawn'],'road retains the existing legal checkpoint ID')
        if hasattr(self,'transitions') and self.transitions:
            self.transitions[-1].update(verified_destination=target,travel_kind='physical_world_edge',
                source_edge=source['edge'],destination_edge=destination['edge'],
                source_checkpoint=before_checkpoint,manifest_sha256=self.connected_road_manifest_sha256)

class ConnectedUnderwaterJourney(ConnectedRoadJourneyMixin,UnderwaterJourney):pass
class ConnectedReturnJourney(ConnectedRoadJourneyMixin,ReturnJourney):pass
class ConnectedHorizonsJourney(ConnectedRoadJourneyMixin,HorizonsJourney):pass
class ConnectedCovenantsJourney(ConnectedRoadJourneyMixin,CovenantsJourney):pass
