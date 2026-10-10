#!/usr/bin/env python3
"""Independent art/geometry checks for shared, edge-connected road mouths."""
from pathlib import Path
import importlib.util,json,sys,unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets'))
from generate_assets import P
DATA=json.loads((ROOT/'assets/connected_roads.json').read_text())
ROOMS={}
base=json.loads((ROOT/'assets/manifest.json').read_text())
ROOMS[0]={'image':ROOT/'assets/village.png','solids':[{'rect':v} for v in base['village']['solid_rectangles']]}
grove=json.loads((ROOT/'assets/world_manifest.json').read_text())
ROOMS[1]={'image':ROOT/'assets/overworld.png','solids':[{'rect':v} for v in grove['static_collision_rectangles']]}
for r in json.loads((ROOT/'assets/campaign_layouts.json').read_text())['rooms']:
    ROOMS[r['id']]={'image':ROOT/f"assets/campaign_{r['key']}.png",'solids':[{'rect':v} for v in r['static_solids']]}
for directory in ('region','northern_region','southern_region','magma_region','underwater_region','return_region','horizons_region','covenants_world'):
    path=ROOT/'assets'/directory
    data=json.loads((path/('geometry.json' if directory in ('horizons_region','covenants_world') else 'layout.json')).read_text())
    for r in data['rooms']:ROOMS[r['id']]={**r,'image':path/(r.get('key','room'+str(r['id']))+'.png')}

class ConnectedRoadArt(unittest.TestCase):
    def test_reciprocal_geometry_and_unique_mouths(self):
        used=[];opposite={'N':'S','S':'N','E':'W','W':'E'}
        for road in DATA['roads']:
            a,b=road['ends'];self.assertEqual(opposite[a['edge']],b['edge'],road['key'])
            self.assertFalse(road.get('one_way'),road['key'])
            for e in (a,b):
                lo,hi=e['aperture'];self.assertLess(lo,hi);self.assertTrue(lo<=e['center']<hi)
                for r,side,start,end in used:
                    if (r,side)==(e['room'],e['edge']):self.assertTrue(hi<=start or lo>=end,(road['key'],e))
                used.append((e['room'],e['edge'],lo,hi))
    def test_every_aperture_is_painted_through_actual_map_edge(self):
        ramps={'dirt':['grass1','dirt1','dirt2','dirt3','dirt4'],
               'stone':['stone1','stone2','stone3','stone4','stone5'],
               'wood':['wood0','wood1','wood2','wood3','wood4','wood5']}
        for road in DATA['roads']:
            for e in road['ends']:
                im=Image.open(ROOMS[e['room']]['image']);self.assertEqual(im.size,tuple(e['size']))
                allowed={P.get('bg_sunlit_'+name,P[name]) for name in ramps[e['paint'][0]['material']]}
                for q in range(*e['aperture']):
                    x,y={'N':(q,0),'S':(q,im.height-1),'W':(0,q),'E':(im.width-1,q)}[e['edge']]
                    self.assertIn(im.getpixel((x,y)),allowed,(road['key'],e['room'],x,y))
    def test_full_arrival_apertures_clear_authored_landmarks(self):
        for road in DATA['roads']:
            for e in road['ends']:
                radius=5 if e['room']>=16 else 4 if e['room']>=4 else 0
                for q in range(*e['aperture']):
                    x,y=e['arrival']
                    if e['edge'] in ('N','S'):x+=q-e['center']
                    else:y+=q-e['center']
                    for s in ROOMS[e['room']]['solids']:
                        sx,sy,w,h=s['rect']
                        hit=x+radius>=sx and x-radius<sx+w and y+radius>=sy and y-radius<sy+h
                        self.assertFalse(hit,(road['key'],e['room'],x,y,s['rect']))
    def test_service_stairs_change_only_background_pixels(self):
        import generate_magma_region as magma
        for room in (39,40,42,43,44,45):
            r,a=magma.field() if room==39 else magma.interior(room-38)
            before=json.dumps(r,sort_keys=True);pixels=a.im.tobytes()
            magma.service_passages(a,r)
            self.assertEqual(json.dumps(r,sort_keys=True),before,room)
            self.assertNotEqual(a.im.tobytes(),pixels,room)
            self.assertNotIn(0,a.im.tobytes(),room)
    def test_memorial_and_story_landmarks_retained(self):
        self.assertIn([40,115,27,36],base['village']['solid_rectangles'])
        self.assertEqual(base['village']['props']['shrine'],[53,141])
        self.assertIn([156,72,36,144],[s['rect'] for s in ROOMS[54]['solids']])
        self.assertIn([288,144,48,48],[s['rect'] for s in ROOMS[54]['solids']])
        self.assertIn([216,88,40,104],[s['rect'] for s in ROOMS[57]['solids']])
    def test_converted_entries_do_not_draw_roadside_warp_arches(self):
        managed={(a['room'],b['room']) for r in DATA['roads'] for a,b in [r['ends'],list(reversed(r['ends']))]}
        retired=managed|{(0,60),(16,55),(53,46),(45,38)}
        entries=json.loads((ROOT/'assets/feedback_travel_entries.json').read_text())['entries']
        for e in entries:self.assertNotIn((e['room'],e['target']),retired)
        # Canopy silhouettes would hide the village's new left/right mouths.
        spec=importlib.util.spec_from_file_location('feedback_art',ROOT/'assets/generate_feedback_world.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        images=module.pictures(entries)
        self.assertIsNone(images[4].getbbox() if 4 in images else None)
        self.assertIsNone(images[9].getbbox() if 9 in images else None)

if __name__=='__main__':unittest.main(verbosity=2)
