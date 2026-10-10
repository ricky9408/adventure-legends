#!/usr/bin/env python3
"""Independent world-boundary/arrival checks for the shared road manifest.

Compiles production geometry. This is host evidence, not controller gameplay.
"""
from pathlib import Path
import ctypes as C,json,subprocess,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
class Road(C.Structure):
    _fields_=[(n,C.c_ubyte)for n in ('room','target','spawn','edge','gate','entry_safe')]+[(n,C.c_ushort)for n in ('width','height')]+[(n,C.c_short)for n in ('low','high','center','target_center','arrival_x','arrival_y')]+[(n,C.c_ubyte)for n in ('barrier_inset','reserved')]

class ConnectedRoadGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='connected-roads-geometry-');cls.addClassCleanup(cls.tmp.cleanup)
        library=Path(cls.tmp.name)/'roads.so'
        subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC','-Isrc','src/connected_roads.c','-o',str(library)],cwd=ROOT,check=True)
        cls.lib=C.CDLL(str(library));n=C.c_uint.in_dll(cls.lib,'connected_road_count').value
        cls.rows=(Road*n).in_dll(cls.lib,'connected_roads');cls.manifest=json.loads((ROOT/'assets/connected_roads.json').read_text())
        cls.lib.connected_road_point.argtypes=[C.POINTER(Road),C.c_int,C.c_int,C.c_int]
        cls.lib.connected_road_outward.argtypes=[C.POINTER(Road),C.c_uint]
        cls.lib.connected_road_arrival.argtypes=[C.POINTER(Road),C.c_int,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int)]
        cls.lib.connected_road_box.argtypes=[C.POINTER(Road),C.c_int,C.c_int,C.c_int,C.c_int]

    def at(self,r,distance,lateral):
        return ((lateral,distance),(r.width-1-distance,lateral),(lateral,r.height-1-distance),(distance,lateral))[r.edge]

    def test_manifest_identity_and_unique_reciprocal_mouths(self):
        self.assertEqual(C.sizeof(Road),24)
        expected={}
        for pair in self.manifest['roads']:
            a,b=pair['ends'];self.assertFalse(pair.get('one_way'),pair['key'])
            for src,dst in ((a,b),(b,a)):
                expected[src['room'],dst['room']]=(src,dst)
        self.assertEqual(len(expected),len(self.rows))
        for r in self.rows:
            src,dst=expected[r.room,r.target]
            self.assertEqual((r.edge,r.low,r.high,r.width,r.height),('NESW'.index(src['edge']),*src['aperture'],*src['size']))
            self.assertEqual((r.arrival_x,r.arrival_y,r.spawn),(*dst['arrival'],dst['saved_spawn']))
            self.assertEqual(r.reserved,0)
            reverse=next(q for q in self.rows if(q.room,q.target)==(r.target,r.room))
            self.assertEqual((r.edge+2)%4,reverse.edge)
            for other in self.rows:
                if r.room==other.room and r.target!=other.target and r.edge==other.edge:
                    self.assertTrue(r.high<=other.low or other.high<=r.low)

    def test_exact_world_perimeter_and_closed_fence(self):
        cases=0
        for r in self.rows:
            for lateral in (r.low,r.center,r.high-1):
                for distance in range(0,40):
                    x,y=self.at(r,distance,lateral)
                    opened=self.lib.connected_road_point(C.byref(r),x,y,1)
                    closed=self.lib.connected_road_point(C.byref(r),x,y,0)
                    if distance<5:self.assertEqual((opened,closed),(1,1))
                    elif distance<32:
                        self.assertEqual(opened,0)
                        self.assertEqual(closed,int(distance<=r.barrier_inset+5))
                    else:self.assertEqual((opened,closed),(-1,-1))
                    cases+=1
                for outside in (r.low-1,r.high):
                    x,y=self.at(r,5,outside);self.assertEqual(self.lib.connected_road_point(C.byref(r),x,y,1),-1)
            for x,y in ((-1,0),(r.width,0),(0,-1),(0,r.height)):
                self.assertEqual(self.lib.connected_road_point(C.byref(r),x,y,1),-1)
            # A middle camera boundary in a scrolling map is not a world seam.
            if r.width>240 and r.edge in(1,3):self.assertEqual(self.lib.connected_road_point(C.byref(r),240,r.center,1),-1)
            if r.height>160 and r.edge in(0,2):self.assertEqual(self.lib.connected_road_point(C.byref(r),r.center,160,1),-1)
        self.assertGreater(cases,1000)

    def test_cardinal_intent_and_every_lateral_arrival(self):
        bits=(64,16,128,32)
        for r in self.rows:
            bit=bits[r.edge];opposite=bits[(r.edge+2)%4]
            self.assertTrue(self.lib.connected_road_outward(C.byref(r),bit))
            self.assertFalse(self.lib.connected_road_outward(C.byref(r),0))
            self.assertFalse(self.lib.connected_road_outward(C.byref(r),1))
            self.assertFalse(self.lib.connected_road_outward(C.byref(r),opposite))
            self.assertFalse(self.lib.connected_road_outward(C.byref(r),bit|opposite))
            reverse=next(q for q in self.rows if(q.room,q.target)==(r.target,r.room))
            for lateral in range(r.low-3,r.high+3):
                x,y=self.at(r,5,lateral);ax=C.c_int();ay=C.c_int()
                self.lib.connected_road_arrival(C.byref(r),x,y,C.byref(ax),C.byref(ay))
                self.assertTrue(5<=ax.value<reverse.width-5 and 5<=ay.value<reverse.height-5)
                transverse=ax.value if r.edge in(0,2)else ay.value
                self.assertTrue(reverse.low<=transverse<reverse.high)
                distance=(ay.value,reverse.width-1-ax.value,reverse.height-1-ay.value,ax.value)[reverse.edge]
                self.assertGreater(distance,reverse.barrier_inset+5)

    def test_broad_phase_only_rejects_changed_strip(self):
        for r in self.rows:
            x,y=self.at(r,16,r.center)
            self.assertEqual(self.lib.connected_road_box(C.byref(r),x,y,x,y),1)
            x,y=self.at(r,40,r.center)
            self.assertEqual(self.lib.connected_road_box(C.byref(r),x,y,x,y),0)
            x,y=self.at(r,16,r.high)
            self.assertEqual(self.lib.connected_road_box(C.byref(r),x,y,x,y),0)

    def test_retired_and_moved_entry_shortcuts_remain_managed(self):
        for source,target in ((53,46),(0,60),(60,0),(16,55),(55,16)):
            self.assertEqual(self.lib.connected_road_managed(source,target),1)
        self.assertFalse(any(r.room==53 and r.target==46 for r in self.rows))
        self.assertEqual(self.lib.connected_road_managed(0,77),0)

if __name__=='__main__':unittest.main()
