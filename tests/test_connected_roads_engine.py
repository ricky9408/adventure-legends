#!/usr/bin/env python3
"""Real-engine host travel ownership and deferred-arrival regressions.

Uses validated synthetic SRAM checkpoints. Position placement is explicitly
synthetic host setup; this does not claim controller-earned travel or timing.
"""
from pathlib import Path
import ctypes as C,hashlib,json,os,re,subprocess,tempfile
from test_save5 import Save
from test_connected_roads_geometry import Road
from player_feedback_host_mapping import reserve_gba_pages

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=Path(os.environ.get('CONNECTED_ROAD_FIXTURES',ROOT/'build/connected-road-checkpoints-r0'))

def main():
    reserve_gba_pages()
    provenance=json.loads((FIXTURES/'provenance.json').read_text())
    files={(r['room'],r['spawn']):r for r in provenance['fixtures']}
    with tempfile.TemporaryDirectory(prefix='connected-road-engine-')as temp:
        library=Path(temp)/'engine.so'
        modules=list(dict.fromkeys(re.findall(r'\$\(BUILD\)/(\w+)\.o',(ROOT/'Makefile').read_text().split('OBJECTS :=',1)[1].split('\n\n',1)[0])))
        modules=[n for n in modules if n!='startup']
        subprocess.run([os.environ.get('HOST_CC','cc'),'-shared','-fPIC','-O1','-std=c99','-fno-builtin','-Wno-attributes','-Wno-pointer-to-int-cast','-Wno-int-to-pointer-cast','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-DGAME_HOST_TEST','-Dmain=gba_main','-I'+str(ROOT/'src'),*[str(ROOT/'src'/(n+'.c'))for n in modules],'-o',str(library)],check=True)
        lib=C.CDLL(str(library));lib.save5_validate.argtypes=[C.POINTER(Save)]
        ram=(C.c_ubyte*32768).in_dll(lib,'save5_test_sram');old=(C.c_ubyte*256).in_dll(lib,'save4_test_sram');live=Save.in_dll(lib,'adventure_save')
        rows=(Road*C.c_uint.in_dll(lib,'connected_road_count').value).in_dll(lib,'connected_roads')
        get=lambda n:C.c_int.in_dll(lib,n).value
        def put(n,v):C.c_int.in_dll(lib,n).value=v
        def frame(keys=0,pressed=0):
            put('keys',keys);put('pressed',pressed);put('invuln',9999);lib.update();lib.save_frame()
            if get('scene_present_phase'):
                lib.render();lib.publish_scene_actors();lib.game_display_brightness();put('page',get('page')^1)
        def settle():
            for _ in range(1600):
                if get('game_state')==2:lib.finish_dialogue()
                if get('game_state')==14:
                    frame();frame(8,8)  # release title controls, then explicit skip
                frame()
                if get('game_state')==1 and not get('scene_present_phase')and not get('save_requested')and not get('save_feedback_background'):return
            raise AssertionError(('unsettled',get('game_state'),get('room'),get('connected_road_pending')))
        def load(room,spawn=0):
            record=files[room,spawn];data=(FIXTURES/record['path']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==record['sha256']
            lib.save5_test_reset_writer();lib.save5_test_fail_after(-1);ram[:]=data;old[:]=data[:256]
            put('has_save',1);lib.start_game(1);settle()
            assert get('room')==room and lib.save5_validate(C.byref(live)),('load',room,get('room'))
        def row(source,target):return next(r for r in rows if(r.room,r.target)==(source,target))
        def point(r,distance=5,lateral=None):
            v=r.center if lateral is None else lateral
            return ((v,distance),(r.width-1-distance,v),(v,r.height-1-distance),(distance,v))[r.edge]
        def place(r,distance=5,lateral=None):
            x,y=point(r,distance,lateral);lib.game_region_warp(x,y)
            assert (get('px'),get('py'))==(x,y),('source collision',r.room,r.target,x,y)
            put('transition_lock',0);put('keys',(64,16,128,32)[r.edge]);put('pressed',0);put('face',(1,3,0,2)[r.edge]);lib.game_geometry_sync()
            return x,y
        def enter(r):
            place(r);source=get('room');assert lib.game_road_step()==1,(source,r.target)
            pending=get('connected_road_pending')
            if get('game_state')==10:
                assert get('room')==source and pending>=0
            settle();assert get('room')==r.target
            assert (get('px'),get('py'))==(r.arrival_x,r.arrival_y),('arrival',r.room,r.target,get('px'),get('py'))
            assert get('connected_road_pending')==-1 and lib.save5_validate(C.byref(live))
        samples=((0,1),(0,4),(0,9),(1,16),(16,1),(16,17),(16,22),(22,16),(22,23),(30,31),(31,30))
        for source,target in samples:
            load(source);r=row(source,target);place(r,33)
            assert lib.game_road_step()==0 and get('room')==source,('early trigger',source,target)
            enter(r)
            # The same held direction points into the new room. It must not
            # bounce even after the transition lock expires.
            destination=get('room')
            for _ in range(25):frame((64,16,128,32)[r.edge])
            assert get('room')==destination,('bounce',source,target)
        # Synthetic all-lateral checks use the real post-entry point predicate.
        for source,target in ((0,4),(0,9),(1,16),(16,22),(30,31)):
            r=row(source,target)
            for lateral in (r.low,r.high-1):
                load(source);place(r,lateral=lateral);assert lib.game_road_step()==1;settle()
                delta=lateral-r.center;expected=(r.arrival_x+(delta if r.edge in(0,2)else 0),r.arrival_y+(delta if r.edge in(1,3)else 0))
                assert(get('px'),get('py'))==expected,(source,target,lateral,expected,get('px'),get('py'))
                assert not lib.solid(*expected)
        # Real building thresholds travel only when walking into the doorway;
        # each return lands outside that same authored building/stair.
        doors=((0,60,184,100,64,(120,140)),(60,0,120,145,128,(184,108)),
               (16,55,424,144,64,(120,140)),(55,16,120,145,128,(424,156)))
        for source,target,x,y,key,expected in doors:
            load(source);lib.game_region_warp(x,y);assert(get('px'),get('py'))==(x,y)
            put('transition_lock',0);put('keys',1);put('pressed',1)
            assert lib.game_road_step()==0 and get('room')==source,'A alone is not doorway travel'
            put('keys',key);put('pressed',0);assert lib.game_road_step()==1;settle()
            assert get('room')==target and(get('px'),get('py'))==expected,(source,target,get('px'),get('py'))
            assert get('connected_door_pending')==-1 and lib.save5_validate(C.byref(live))
        stairs=((27,26),(28,27),(29,28),(35,34),(36,35),(37,36),(43,42),(44,43),(45,44))
        for source,target in stairs:
            load(source);lib.game_region_warp(120,138);put('transition_lock',0)
            for _ in range(1600):
                frame(128)
                if get('room')!=source:break
            assert get('room')==target,('descending stair',source,target,get('room'))
            settle();expected=(216 if target>=42 else 208,80)
            assert(get('px'),get('py'))==expected and get('checkpoint_spawn')==0,(source,target,expected,get('px'),get('py'))
            assert not lib.solid(*expected)and get('px_q8')==get('px')*256 and get('py_q8')==get('py')*256
            for _ in range(12):frame(128)
            assert get('room')==target,'held Down must leave the lower landing without returning upstairs'
            load(target);canonical=(120,136 if target>=42 else 132)
            assert(get('px'),get('py'))==canonical,('canonical load changed',target)
            put('game_state',4);frame(1,1);settle()
            assert(get('px'),get('py'))==canonical and get('checkpoint_spawn')==0,('canonical retry changed',target)
        # The old roadside action squares cannot provide parallel shortcuts.
        for source,x,y in ((0,196,128),(0,80,128),(0,176,112),(0,104,112),
                           (1,168,248),(16,400,280),(22,240,264)):
            load(source);lib.game_region_warp(x,y);put('transition_lock',0)
            lib.try_interaction();assert get('room')==source,('old A shortcut',source,x,y)
        # Every summon/recall and immediate replacement keeps coordinates and
        # fixed point state inside the same authoritative world collision.
        for target in (1,4,9,54):
            load(0);r=row(0,target);place(r,7);put('summoned',0)
            for _ in range(4):
                frame(2,2)
                assert 5<=get('cx')<240-5 and 5<=get('cy')<160-5
                assert not lib.solid(get('cx'),get('cy'))
                assert get('cx')==get('cx_q8')>>8 and get('cy')==get('cy_q8')>>8
                frame()
            frame(2,2);assert get('summoned')==1
            lib.quickparty_cycle()
            assert 5<=get('cx')<240-5 and 5<=get('cy')<160-5 and not lib.solid(get('cx'),get('cy'))
            for _ in range(40):
                frame();assert not lib.solid(get('cx'),get('cy'))
                assert 5<=get('cx')<240-5 and 5<=get('cy')<160-5
        # A failed owner transfer cannot leave a delayed road request behind.
        load(30);r=row(30,31);place(r);assert lib.game_road_step()==1 and get('game_state')==10
        assert get('connected_road_pending')>=0
        x,y=get('px'),get('py');lib.game_region_warp(x,y)
        assert get('connected_road_pending')==-1 and not lib.south_game_enter_pending()and get('game_state')==1
        for _ in range(40):frame()
        assert get('room')==30
        load(30);place(r);assert lib.game_road_step()==1;lib.enter_room(16,0);settle()
        assert get('room')==16 and get('connected_road_pending')==-1
        assert(get('px'),get('py'))==(240,284),'redirect must use its ordinary checkpoint'
        load(30);place(r);assert lib.game_road_step()==1;lib.start_game(1);settle()
        assert get('connected_road_pending')==-1 and get('room')==30
        # Fresh game locks remain solid/nonmodal without swallowing A/R.
        lib.start_game(0);settle();r=row(0,4);place(r,23);put('pressed',257);put('swing',5)
        assert lib.game_road_step()==0 and get('room')==0 and get('game_state')==1
        assert get('pressed')==257 and get('swing')==5 and get('toast_ticks')==110
        assert lib.solid(*point(r,16))==1
        put('toast_ticks',70);lib.game_road_step();assert get('toast_ticks')==70
        result={'passed':True,'scope':__doc__,'geometry_rows':len(rows),'real_engine_road_samples':len(samples),'lateral_endpoint_cases':10,'real_doorway_roundtrips':4,'descending_stairs_with_canonical_load_retry':len(stairs),'old_action_shortcut_checks':7,'companion_summon_recall_replacement_edges':4,'staged_same_position_warp_cancel':True,'redirect_cancels_arrival':True,'load_cancels_arrival':True,'closed_fence_preserves_actions':True,'fixture_provenance_sha256':hashlib.sha256((FIXTURES/'provenance.json').read_bytes()).hexdigest()}
        print(json.dumps(result,indent=2))
if __name__=='__main__':main()
