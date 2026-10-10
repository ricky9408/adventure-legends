#!/usr/bin/env python3
"""Synthetic real-engine feedback contracts; never native controller evidence.

Uses all production C modules, mocked GBA register pages and actual fault-
injected save5 SRAM. Pixel checks compare complete host framebuffers.
"""
import ctypes as C
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
from test_save5 import Save
from test_connected_roads_geometry import Road
ROOT=Path(__file__).resolve().parents[1]
from player_feedback_host_mapping import reserve_gba_pages,run_protected_probe
if __name__=='__main__' and os.environ.get('PLAYER_FEEDBACK_PROBE_CHILD')!='1':
 raise SystemExit(run_protected_probe(Path(__file__).resolve()))
# Reserve before loading any game code or beginning any game assertion.
libc=reserve_gba_pages()
class UiRun(C.Structure):
 _fields_=[('offset',C.c_ushort),('count',C.c_ubyte),('mask',C.c_ubyte)]
class UiText(C.Structure):
 _fields_=[('width',C.c_ushort),('height',C.c_ubyte),('reserved',C.c_ubyte),('runs',C.POINTER(UiRun)*2),('count',C.c_ushort*2)]
class Entry(C.Structure):
 _fields_=[('room',C.c_ubyte),('action',C.c_ubyte),('target',C.c_ubyte),('spawn',C.c_ubyte),('x',C.c_short),('y',C.c_short),('w',C.c_ubyte),('h',C.c_ubyte)]
class Door(C.Structure):
 _fields_=[(n,C.c_ubyte) for n in ('room','target','spawn','edge','gate','reserved')]+[(n,C.c_short) for n in ('x','y','w','h','arrival_x','arrival_y')]
class Enemy(C.Structure):
 _fields_=[(n,C.c_int) for n in ('x','y','hp','flash','kind')]
with tempfile.TemporaryDirectory(prefix='feedback-engine-') as tmp:
 library=Path(tmp)/'engine.so'
 # Keep the pinned historical full-world/picker underlay byte-for-byte. Only
 # the intentionally superseded WIN presentation is adapted to the current
 # ending contract. This independent byte renderer does not call either
 # production ending_credits_draw or ending_credits_card_hint.
 reference=(ROOT/'tests/fixtures/player-feedback-prior/render_static_r5.inc').read_text()
 prior_card='if(game_state==WIN){copy_bg(BACK_TITLE);box(17,40,206,103);centered(TX_COMPLETE,49,GOLD);centered(TX_THANKS,75,CREAM);centered(TX_C_POSTGAME,122,CREAM);centered(TX_C_FINAL_SMALL,149,GOLD);}'
 assert reference.count(prior_card)==1
 reference=reference.replace(prior_card,'if(game_state==WIN)reference_ending_presentation();')
 ending_reference=r'''
#include "ending_credits_text.h"
int reference_ending_mutation;
static void reference_ending_text(unsigned id,int y,int color,int top,int bottom){
 const UiText*t=&ending_credits_texts[id];int x=(240-t->width)/2;
 for(unsigned i=0;i<t->count[x&1];i++){
  UiRun r=t->runs[x&1][i];int yy=y+r.offset/120;
  if(yy<top||yy>=bottom)continue;
  for(unsigned j=0;j<r.count;j++)for(unsigned bit=0;bit<2;bit++)
   if(r.mask&(1u<<bit))((unsigned char*)screen)[yy*240+(x/2+r.offset%120+j)*2+bit]=(unsigned char)color;
 }
}
static void reference_ending_presentation(void){
 if(!ending_credits_phase){
  copy_bg(BACK_TITLE);box(8,40,224,105);centered(TX_COMPLETE,49,GOLD);centered(TX_THANKS,67,CREAM);
  JourneyGoal g=journey_goal_read(&adventure_save,chapter_flags,(unsigned)room);centered(g.title,83,TEAL);
  if(reference_ending_mutation==1)centered(TX_C_POSTGAME,126,CREAM);
  else if(reference_ending_mutation!=2)reference_ending_text(ending_credits_armed?EC_CARD_HINT:EC_RELEASE_HINT,128,PAL_TEAL2,0,160);
  centered(TX_C_FINAL_SMALL,149,GOLD);
 }else{
  rect(0,0,240,160,PAL_INK);reference_ending_text(EC_TITLE,5,PAL_GOLD3,0,160);
  rect(12,20,216,1,PAL_TEAL2);rect(12,140,216,1,PAL_TEAL2);
  if(ending_credits_phase==2){
   reference_ending_text(EC_THANKS,64,PAL_GOLD4,0,160);
   reference_ending_text(ending_credits_armed?EC_DONE_HINT:EC_RELEASE_HINT,145,PAL_TEAL2,0,160);
  }else{
   for(unsigned i=EC_LINE_0;i<EC_COUNT;i++)reference_ending_text(i,144+(int)(i-EC_LINE_0)*20-(int)ending_credits_scroll,PAL_GOLD4,24,138);
   reference_ending_text(ending_credits_armed?EC_ROLL_HINT:EC_RELEASE_HINT,145,PAL_TEAL2,0,160);
  }
 }
 if(reference_ending_mutation==3)((unsigned char*)screen)[32*240+12]^=1;
}
'''
 host_game=Path(tmp)/'game.c';host_game.write_text((ROOT/'src/game.c').read_text()+'\n'+ending_reference+'\n'+reference)
 modules=re.findall(r'\$\(BUILD\)/(\w+)\.o',(ROOT/'Makefile').read_text().split('OBJECTS :=',1)[1].split('\n\n',1)[0]);modules=[n for n in dict.fromkeys(modules) if n!='startup']
 subprocess.run([os.environ.get('HOST_CC','cc'),'-shared','-fPIC','-O1','-std=c99','-fno-builtin','-Wno-attributes','-Wno-pointer-to-int-cast','-Wno-int-to-pointer-cast','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-DGAME_HOST_TEST','-Dmain=gba_main','-I'+str(ROOT/'src'),*[str(host_game) if n=='game' else str(ROOT/'src'/(n+'.c')) for n in modules],'-o',str(library)],check=True)
 lib=C.CDLL(str(library));lib.save5_load.argtypes=[C.POINTER(Save)]
 for fn in ('economy_award_combat','economy_begin_use','economy_begin_purchase'):getattr(lib,fn).argtypes=[C.POINTER(Save),C.c_uint]
 lib.save5_test_fail_after.argtypes=[C.c_int];lib.kill_enemy.argtypes=[C.POINTER(Enemy)]
 ids=list(dict.fromkeys(re.findall(r'\bTX_[A-Z0-9_]+\b',(ROOT/'src/ui.h').read_text())))
 def get(name):return C.c_int.in_dll(lib,name).value
 def put(name,value):C.c_int.in_dll(lib,name).value=value
 ram=(C.c_ubyte*32768).in_dll(lib,'save5_test_sram');ram[:]=b'\xff'*32768
 old=(C.c_ubyte*256).in_dll(lib,'save4_test_sram');old[:]=b'\xff'*256
 live=Save.in_dll(lib,'adventure_save');lib.save5_test_fail_after(-1)
 def frame(keys=0,pressed=0):
  put('keys',keys);put('pressed',pressed);lib.update();lib.save_frame()
  if get('scene_present_phase'):
   lib.render();lib.publish_scene_actors();lib.game_display_brightness();put('page',get('page')^1)
 def drain(limit=1000):
  modes=[]
  for _ in range(limit):
   modes.append(get('game_state'));frame()
   if not get('save_requested') and not get('save_feedback_background') and get('game_state') not in (6,10,12):return modes
  raise AssertionError('Writer or event failed to settle')
 def new_game():
  # Complete the real opening before making assertions about the initial
  # checkpoint. No synthetic state overwrite can stand in for this boundary.
  lib.start_game(0);assert get('game_state')==14
  frame();frame(8,8);frame();drain();assert get('game_state')==1
 def load():
  result=Save();assert lib.save5_load(C.byref(result))==1;return result
 count=C.c_uint.in_dll(lib,'travel_entry_count').value;entries=(Entry*count).in_dll(lib,'travel_entries')
 for e in entries:
  x=e.x+e.w//2;y=e.y+e.h//2;lib.travel_feedback_reset()
  assert lib.travel_feedback_step(e.room,x,y,1,0)==-1
  assert lib.travel_feedback_step(e.room,x,y,64,1)==-1
  assert lib.travel_feedback_step(e.room,x,y,64,0)>=0
  for _ in range(100):assert lib.travel_feedback_step(e.room,x,y,64,0)==-1
  lib.travel_feedback_arrive(e.room,x,y);assert lib.travel_feedback_step(e.room,x,y,64,0)==-1
  lib.travel_feedback_step(e.room,-100,-100,64,0);assert lib.travel_feedback_step(e.room,x,y,64,0)>=0
 new_game();assert lib.save5_validate(C.byref(live))==1
 enemies=(Enemy*6).in_dll(lib,'enemies')
 # Narrative transports retain their own hostile/quest guards.
 for source,target in ((22,30),(30,38),(38,46)):
  e=next(e for e in entries if e.room==source and e.target==target)
  for n,v in {'room':source,'px':e.x+e.w//2,'py':e.y+e.h//2,'keys':64,'pressed':0,'transition_lock':0,'game_state':1}.items():put(n,v)
  for enemy in enemies:enemy.hp=0
  enemies[0].x=get('px');enemies[0].y=get('py');enemies[0].hp=2;prior_live=bytes(live);lib.travel_feedback_reset()
  assert lib.walk_entry()==0 and get('room')==source and get('game_state')==1 and bytes(live)==prior_live
  enemies[0].hp=0;assert lib.game_region_entry_safe()==1
  assert lib.walk_entry()==0 and get('room')==source and get('game_state')==1 and get('toast_ticks')==110
 roads=(Road*C.c_uint.in_dll(lib,'connected_road_count').value).in_dll(lib,'connected_roads')
 doors=(Door*C.c_uint.in_dll(lib,'connected_door_count').value).in_dll(lib,'connected_doors')
 def road_point(r,distance):
  return ((r.center,distance),(r.width-1-distance,r.center),(r.center,r.height-1-distance),(distance,r.center))[r.edge]
 # Converted river/northern roads use a validated full-progress host fixture,
 # so an actual nearby enemy, rather than a closed quest gate, is the blocker.
 fixture=ROOT/'tests/fixtures/v5-revision9/covenants-all128-72-cold.sav'
 assert __import__('hashlib').sha256(fixture.read_bytes()).hexdigest()=='eec8efbfeaf83a51b66faa0c8e9d6a3061af36b88fb6d7b3aa77fbc47107122a'
 lib.save5_store.argtypes=[C.POINTER(Save)]
 for source,target in ((1,16),(16,22)):
  ram[:]=fixture.read_bytes();lib.save5_test_reset_writer();prepared=load();prepared.campaign.room=source;prepared.campaign.spawn=0
  assert lib.save5_store(C.byref(prepared))==1;put('has_save',1);lib.start_game(1);drain()
  r=next(r for r in roads if r.room==source and r.target==target);x,y=road_point(r,5)
  for n,v in {'px':x,'py':y,'keys':(64,16,128,32)[r.edge],'pressed':0,'transition_lock':0,'game_state':1}.items():put(n,v)
  for enemy in enemies:enemy.hp=0
  enemies[0].x=x;enemies[0].y=y;enemies[0].hp=2;prior_live=bytes(live)
  assert lib.game_region_entry_safe()==0 and lib.game_road_step()==0 and get('room')==source and bytes(live)==prior_live
  enemies[0].hp=0;assert lib.game_region_entry_safe()==1 and lib.game_road_step()==1;drain();assert get('room')==target
 # A fresh adventure has physical closed roads and a real locked house door.
 # Their brief hints preserve A/R and the current attack, with a rearm margin.
 for target in (4,9,54,60):
  new_game()
  if target==60:
   d=next(d for d in doors if d.room==0 and d.target==target);x,y=d.x+d.w//2,d.y+d.h//2;held=64
  else:
   r=next(r for r in roads if r.room==0 and r.target==target);x,y=road_point(r,r.barrier_inset+7);held=(64,16,128,32)[r.edge]
  for n,v in {'px':x,'py':y,'keys':held,'pressed':257,'transition_lock':0,'swing':5,'toast_ticks':0}.items():put(n,v)
  assert lib.game_road_step()==0
  assert get('game_state')==1 and get('room')==0 and get('pressed')==257 and get('swing')==5
  assert get('toast_id')==ids.index('TX_PF_ROUTE_LATER') and get('toast_ticks')==110
  put('toast_ticks',70);assert lib.game_road_step()==0 and get('toast_ticks')==70,'standing/holding must not refresh the route hint'
  put('px',120);put('py',76);lib.game_road_step();put('px',x);put('py',y)
  assert lib.game_road_step()==0 and get('toast_ticks')==110,'leaving the route margin rearms the hint'
 new_game()
 put('swing',0);put('pressed',0);put('toast_ticks',0)
 # The merchant hint and A interaction share one read-only exact range gate.
 for x,y,expected in ((56,100,1),(77,100,1),(78,100,0),(56,121,1),(56,122,0),(67,110,1),(67,111,0)):
  put('room',0);put('game_state',1);put('px',x);put('py',y)
  prior_live=bytes(live);assert lib.game_shop_in_range()==expected and bytes(live)==prior_live
 for mode in (0,2,3,6,7,8,11,12,13):
  put('game_state',mode);put('px',56);put('py',100);assert lib.game_shop_in_range()==0
 put('game_state',1);put('room',1);assert lib.game_shop_in_range()==0
 put('room',0);put('px',120);put('py',126);put('game_state',1);put('keys',0);lib.travel_feedback_reset()
 before=get('save_feedback_started');lib.save_game_ordinary();lib.save_frame()
 assert get('save_feedback_started')==before and get('save_feedback_skipped')>=1
 # A critical request freezes first, then performs exact dedup on the next
 # update. An unchanged verified state never admits another writer.
 skipped=get('save_feedback_skipped');lib.save_game();lib.save_frame()
 assert get('game_state')==6 and get('save_dedup_pending')==1
 assert get('save_feedback_started')==before and get('save_feedback_skipped')==skipped
 frame();assert get('game_state')==1 and get('save_feedback_skipped')==skipped+1 and get('save_feedback_started')==before
 assert lib.economy_award_combat(C.byref(live),6)==6
 lib.save_game_ordinary();lib.save_frame()
 assert lib.game_save_badge_id()==ids.index('TX_FB_SAVING'),'pending warmup must paint the same Saving badge'
 frame();frame();assert get('save_feedback_background')==1 and get('game_state')==1
 x=get('px');frame(16);frame(16);assert get('px')>x
 assert lib.economy_award_combat(C.byref(live),6)==6
 for _ in range(20):lib.save_game_ordinary()
 assert set(drain())=={1};assert load().economy.gold==12 and get('save_feedback_started')==before+2
 prior=bytes(ram);assert lib.economy_award_combat(C.byref(live),6)==6
 lib.save5_test_fail_after(0);lib.save_game_ordinary();assert set(drain())=={1}
 assert get('save_failed')==get('save_failure_notice')==1 and bytes(ram)==prior and load().economy.gold==12
 put('game_state',3);put('journal_tab',13)
 for _ in range(140):frame()
 assert get('toast_ticks')==0 and get('save_failure_notice')==1
 lib.toast(ids.index('TX_HEALED'))
 for _ in range(140):frame()
 assert get('save_failed')==get('save_failure_notice')==1
 # Independent glyph, border and OBJ clipping oracle for the durable notice.
 notice=(UiText*len(ids)).in_dll(lib,'ui_texts')[ids.index('TX_C_SAVE_FAILED')]
 x=(240-notice.width)//2;left=(240-notice.width-10)//2;top=8;height=19;width=240-2*left
 pixels=(C.c_ubyte*(240*160))();C.c_void_p.in_dll(lib,'screen').value=C.addressof(pixels)
 expected=bytearray([1]*(width*height));glyphs=set()
 for yy in range(height):
  for xx in range(width):
   if yy in (0,height-1) or xx in (0,width-1):expected[yy*width+xx]=45
 for i in range(notice.count[x&1]):
  run=notice.runs[x&1][i]
  for pair in range(run.count):
   pixel=((top+2)*120+x//2+run.offset+pair)*2
   for side in range(2):
    if run.mask&(1<<side):
     xx=(pixel+side)%240-left;yy=(pixel+side)//240-top;assert 0<xx<width-1 and 0<yy<height-1
     expected[yy*width+xx]=47;glyphs.add((xx,yy))
 assert len(glyphs)>200
 for mode in (2,3,4,5,7,8,11,13):
  put('game_state',mode);pixels[:]=bytes([241])*len(pixels)
  assert lib.game_save_badge_id()==0;lib.game_draw_save_badge();assert bytes(pixels)==bytes([241])*len(pixels)
  lib.draw_save_failure_notice()
  for yy in range(160):
   for xx in range(240):
    assert pixels[yy*240+xx]==(expected[(yy-top)*width+xx-left] if left<=xx<left+width and top<=yy<top+height else 241)
  for priority in (0,1,2):
   put('obj_count',0);lib.obj_add(0,left,top,16,16,priority,9999,0);assert get('obj_count')==0
  put('obj_count',0);lib.obj_add(0,left+width,top,8,8,0,9999,0);assert get('obj_count')==1
 for mode in (0,1,6):
  put('game_state',mode);pixels[:]=bytes([241])*len(pixels);lib.draw_save_failure_notice();assert bytes(pixels)==bytes([241])*len(pixels)
 put('game_state',3);put('journal_tab',13);frame(2,2)
 assert get('game_state')==1 and get('save_failure_notice')==0 and get('save_failed')==1
 assert lib.game_save_badge_id()==ids.index('TX_FB_SAVE_ERROR')
 put('chapter_flags',2);lib.save_game();assert 6 in drain();assert get('save_failed')==get('save_failure_notice')==1 and bytes(ram)==prior
 put('chapter_flags',0);lib.save5_test_fail_after(-1);lib.save_game()
 assert get('save_failed')==get('save_failure_notice')==1;lib.save_frame();assert get('save_failed')==1
 critical=drain();assert 6 in critical and load().economy.gold==18 and not get('save_failed')
 # A critical shop operation takes scratch ownership from ordinary saving.
 lib.economy_award_combat(C.byref(live),100);lib.save_game_ordinary();lib.save_frame();frame();frame()
 assert get('save_feedback_background')==1
 put('px',56);put('py',100);assert lib.game_shop_interact()==1
 frame(1,1);assert get('game_shop_confirm')==1;cash=live.economy.gold
 frame(2,2);assert get('game_shop_confirm')==0 and live.economy.gold==cash
 frame(1,1);frame();frame(1,1);assert get('game_state')==12 and live.economy.gold==cash
 drain();assert get('game_state')==11 and live.economy.gold==cash-18 and live.economy.supplies[0]==1
 assert load().economy.gold==cash-18 and get('save_feedback_preemptions')>=1
 frame(2,2);frame(4,4);assert get('roll_ticks')==0 and get('game_state')==1
 frame(8,8);assert get('game_state')==3 and get('journal_tab')==13
 frame(1,1);assert get('journal_tab')==15
 frame(2,2);assert get('game_state')==3 and get('journal_tab')==13
 frame(8,8);assert get('game_state')==1
 # Exact full-card reuse, with outside-world and badge keys protected.
 framebuffer=(C.c_ubyte*(240*160))();C.c_void_p.in_dll(lib,'screen').value=C.addressof(framebuffer)
 cache=(C.c_uint*90).in_dll(lib,'cache_fields');valid=(C.c_int*2).in_dll(lib,'cache_valid');rows=(C.c_ushort*224).in_dll(lib,'modal_world_row')
 backdrop=bytes((x*7+y*11)%40+50 for y in range(160) for x in range(240))
 put('page',0);put('game_state',3);put('save_failed',0);put('save_failure_notice',0)
 for target in (1,2,3,4,13,14,15,16):
  framebuffer[:]=backdrop
  for i in range(112):rows[i]=backdrop[153*240+8+i*2]|backdrop[153*240+9+i*2]<<8
  put('journal_tab',13);lib.draw_journal_panel()
  for i in range(90):cache[i]=0
  cache[1]=3;cache[10]=13;cache[44]=3;valid[0]=1;valid[1]=0
  key=(C.c_uint*45)(*cache[:45]);key[10]=target;key[38]=7;put('journal_tab',target)
  assert lib.reuse_modal_bitmap(key)==1;actual=bytes(framebuffer)
  framebuffer[:]=backdrop;lib.draw_journal_panel();lib.game_draw_save_badge();lib.draw_save_failure_notice();assert bytes(framebuffer)==actual
  key[17]=1;assert lib.reuse_modal_bitmap(key)==0
  key[17]=0;key[39]=1;assert lib.reuse_modal_bitmap(key)==0
 framebuffer[:]=backdrop;put('game_state',8);lib.progression_draw_evolution()
 for i in range(90):cache[i]=0
 cache[1]=8;cache[44]=8;valid[0]=1;valid[1]=0;key=(C.c_uint*45)(*cache[:45]);key[19]=9;lib.progression_evolution_tick()
 assert lib.reuse_modal_bitmap(key)==1;actual=bytes(framebuffer)
 framebuffer[:]=backdrop;lib.progression_draw_evolution();lib.game_draw_save_badge();lib.draw_save_failure_notice();assert bytes(framebuffer)==actual
 valid[0]=valid[1]=0;put('game_state',1)
 # Compare optimized covered-world primitives and every entrance view against
 # a fully rendered reference, then paint the independent opaque cover.
 rng=random.Random(1846);primitives=[(rng.randrange(-10,225),rng.randrange(-10,150),rng.randrange(1,40),rng.randrange(1,35),rng.randrange(40,90)) for _ in range(40)]
 sprite=(C.c_ubyte*256)(*[(i*13)%59 if i%5 else 0 for i in range(256)]);lib.sprite.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_int,C.c_int]
 covers=[(26,29,188,131),(8,31,224,119),(8,31,224,122),(12,42,216,105),(20,38,200,114),(6,99,228,56)]
 def composite(cover,enabled,scene=None):
  left,top,w,h=cover;framebuffer[:]=backdrop
  for name,value in [('world_mask_left',left),('world_mask_top',top),('world_mask_right',left+w),('world_mask_bottom',top+h),('world_mask_active',enabled)]:put(name,value)
  if scene is not None:lib.feedback_world_draw(*scene)
  else:
   for x,y,w0,h0,color in primitives:lib.rect(x,y,w0,h0,color);lib.line(x,y,239-x,159-y,color);lib.sprite(sprite,x,y,16,16,0);lib.pix(x,y,color)
  put('world_mask_active',0);lib.box(left,top,w,h);return bytes(framebuffer)
 for cover in covers:
  assert composite(cover,1)==composite(cover,0)
  for e in entries:
   scene=(e.room,max(0,e.x-112),max(0,e.y-80));assert composite(cover,1,scene)==composite(cover,0,scene)
 # The title ROM patch must reproduce the old ordered rect renderer over
 # every original background pixel, including shadow/glyph overlaps.
 title=(C.c_ubyte*38400).in_dll(lib,'background_title');font=((C.c_ubyte*7)*26).in_dll(lib,'alphabet')
 framebuffer[:]=bytes(title);expected_title=bytearray(title)
 for letter_index,letter in enumerate('EMBERBOND'):
  for glyph_y in range(7):
   for glyph_x in range(5):
    if font[ord(letter)-65][glyph_y]&(16>>glyph_x):
     for x,y,color in ((43+letter_index*18+glyph_x*3,37+glyph_y*3,1),(42+letter_index*18+glyph_x*3,35+glyph_y*3,47 if glyph_y<3 else 46)):
      for row in range(y,y+3):expected_title[row*240+x:row*240+x+3]=bytes([color])*3
 lib.wordmark();assert bytes(framebuffer)==bytes(expected_title),'title patch must match the original full framebuffer'
 subprocess.run(['python3',str(ROOT/'tools/generate_feedback_title.py'),'--check'],check=True)
 # Bottom-overlay reuse restores only the raw strip belonging to this
 # framebuffer page. Every non-bottom key remains an exact world guard.
 for test_page in (0,1):
  put('page',test_page);put('game_state',1);put('quickparty_open',0)
  pattern=bytes((value+test_page*7)%240 for value in backdrop);framebuffer[:]=pattern
  lib.toast(ids.index('TX_SAVED'));lib.game_shop_reward(12,6);lib.capture_play_strip()
  lib.draw_play_toast();lib.draw_play_hint();lib.game_shop_draw_reward()
  for i in range(90):cache[i]=0
  off=test_page*45;cache[off+1]=1;cache[off+44]=1;cache[off+7]=1;cache[off+8]=ids.index('TX_SAVED');cache[off+40]=get('game_shop_revision');cache[off+42]=1
  valid[test_page]=1;key=(C.c_uint*45)(*cache[off:off+45])
  lib.toast(ids.index('TX_HEALED'));lib.game_shop_reward(120,10);key[8]=ids.index('TX_HEALED');key[40]=get('game_shop_revision')
  assert lib.reuse_play_strip(key)==1;actual=bytes(framebuffer)
  framebuffer[:]=pattern;lib.draw_play_toast();lib.draw_play_hint();lib.game_shop_draw_reward()
  assert bytes(framebuffer)==actual,'bottom reuse must match full overlay repaint on each page'
  for index in (0,2,3,17,18,19,24,39,43,44):
   original=key[index];key[index]=original+1;assert lib.reuse_play_strip(key)==0,('world guard',index);key[index]=original
  put('play_strip_disabled',1);assert lib.reuse_play_strip(key)==0;put('play_strip_disabled',0)
 valid[0]=valid[1]=0;put('page',0)
 # A clean framebuffer can acquire its raw strip lazily, but only when
 # every non-overlay key and the old no-overlay provenance both match.
 strip_state=(C.c_int*2).in_dll(lib,'play_strip_valid');strip_clean=(C.c_int*2).in_dll(lib,'play_strip_clean')
 for test_page in (0,1):
  put('page',test_page);put('game_state',1);put('quickparty_open',0);put('toast_ticks',0);lib.game_shop_reset()
  for reset in ('southern_powers_reset','magma_powers_reset','underwater_powers_reset','return_powers_reset','horizons_powers_reset','covenants_powers_reset'):getattr(lib,reset)()
  put('room',0);pattern=bytes((i*17+test_page)%256 for i in range(38400));framebuffer[:]=pattern;lib.capture_play_strip();assert not strip_state[test_page] and strip_clean[test_page]
  off=test_page*45
  for i in range(90):cache[i]=0
  cache[off+1]=1;cache[off+44]=1;valid[test_page]=1;key=(C.c_uint*45)(*cache[off:off+45])
  lib.toast(ids.index('TX_HEALED'));key[7]=1;key[8]=ids.index('TX_HEALED')
  for index in (0,2,3,17,18,19,24,39,43,44):
   old=key[index];key[index]=old+1;assert lib.reuse_play_strip(key)==0;key[index]=old
  valid[test_page]=0;assert lib.reuse_play_strip(key)==0;valid[test_page]=1
  strip_clean[test_page]=0;assert lib.reuse_play_strip(key)==0;strip_clean[test_page]=1
  cache[off+7]=1;assert lib.reuse_play_strip(key)==0,'dirty pixels cannot masquerade as a clean page';cache[off+7]=0
  put('play_strip_disabled',1);assert lib.reuse_play_strip(key)==0;put('play_strip_disabled',0)
  assert lib.reuse_play_strip(key)==1 and strip_state[test_page]==1 and not strip_clean[test_page]
  actual=bytes(framebuffer);framebuffer[:]=pattern;lib.draw_play_toast();lib.draw_play_hint();lib.game_shop_draw_reward();assert bytes(framebuffer)==actual
  for i in range(45):cache[off+i]=key[i]
  put('toast_ticks',0);key[7]=0;assert lib.reuse_play_strip(key)==1 and bytes(framebuffer)==pattern
  put('room',3);put('toast_ticks',0);lib.capture_play_strip();assert strip_state[test_page]==1 and not strip_clean[test_page],'boss bar requires an owned raw strip'
 put('room',0);put('page',0);put('toast_ticks',0);valid[0]=valid[1]=0
 # Reset after verified consumption but BEFORE transient health/cooldown
 # effect. Cold resume restores full health/ready power, consumed once.
 lib.game_health_hurt(16,0);put('ability_cd',37);assert lib.game_gear_hp()<lib.game_gear_base_hp()
 assert lib.economy_begin_use(C.byref(live),0)==1
 while lib.economy_step()==1:pass
 assert live.economy.supplies[0]==0 and lib.game_gear_hp()<lib.game_gear_base_hp()
 lib.start_game(1);drain();assert live.economy.supplies[0]==0 and lib.game_gear_hp()==lib.game_gear_base_hp() and get('ability_cd')==0
 assert lib.economy_begin_purchase(C.byref(live),1)==1
 while lib.economy_step()==1:pass
 put('ability_cd',53);assert lib.economy_begin_use(C.byref(live),1)==1
 while lib.economy_step()==1:pass
 assert live.economy.supplies[1]==0 and get('ability_cd')==53
 lib.start_game(1);drain();assert live.economy.supplies[1]==0 and get('ability_cd')==0
 put('room',1);lib.spawn_enemies();enemies=(Enemy*6).in_dll(lib,'enemies')
 before_xp=sum(live.roster.instances[n].xp for n in live.roster.party if n<160);before_gold=live.economy.gold;before_kills=get('kills');enemies[0].hp=0
 lib.kill_enemy(C.byref(enemies[0]));xp=sum(live.roster.instances[n].xp for n in live.roster.party if n<160)-before_xp
 assert live.economy.gold-before_gold==6 and get('game_shop_reward_gold')==6 and get('game_shop_reward_xp')==xp
 lib.kill_enemy(C.byref(enemies[0]));assert live.economy.gold==before_gold+6 and get('kills')==before_kills+1
 put('game_state',1);put('room',21);put('transition_lock',1000);put('keys',0);lib.save5_quest_set_state(C.byref(live.quests),9,1);lib.region_game_reset()
 source=(ROOT/'src/region_game.c').read_text();row=re.search(r'garden_stones\[3\]\[2\]=\{(.*?)\};',source).group(1)
 stones=[tuple(map(int,v)) for v in re.findall(r'\{(\d+),(\d+)\}',row)];assert len(stones)==3
 for step,(x,y) in enumerate(stones):
  put('px',x);put('py',y);lib.region_game_tick();assert C.c_ubyte.in_dll(lib,'region_game_garden_step').value==step+1
  for _ in range(20):lib.region_game_tick()
  assert C.c_ubyte.in_dll(lib,'region_game_garden_step').value==step+1
  put('px',120);put('py',140);lib.region_game_tick()
 # Old room77 teardown remains before destination reconstruction, and the
 # first village tick must not introduce a second post-render revision.
 new_game()
 assert lib.economy_award_combat(C.byref(live),6)==6;lib.save_game_ordinary();frame();frame();frame();assert get('save_feedback_background')==1
 put('room',77);lib.spawn_enemies();lib.covenants_game_reset();assert lib.game_covenants_spawn_wave(1)==1
 assert lib.game_covenants_enemies_alive()>0
 lib.leave_extended_scene(0);assert get('room')==77 and lib.game_covenants_enemies_alive()==0 and all(not e.hp for e in enemies)
 assert lib.game_covenants_spawn_wave(1)==1
 put('game_state',1);lib.enter_room(0,3)
 assert get('room')==0 and get('px')==120 and get('py')==118
 assert all(not e.hp for e in enemies)
 assert live.campaign.room==0 and live.campaign.spawn==3
 revision=get('covenants_game_revision');lib.covenants_game_tick_old()
 assert get('covenants_game_revision')==revision,'arrival must prepare the old-scene adapter before caching'
 # Admission holds exactly the old bitmap/OAM/brightness. Then two frozen
 # updates paint and copy the new scene; only the completed copy can service
 # ordinary saving, and copied keys remain the keys of pixels actually drawn.
 vram=[(C.c_ubyte*38400).from_address(0x06000000),(C.c_ubyte*38400).from_address(0x0600A000)]
 oam=(C.c_ubyte*1024).in_dll(lib,'obj_entries');oam[:]=bytes((i*7)%256 for i in range(1024));old_oam=bytes(oam)
 old_picture=bytes((i*11+19)%256 for i in range(38400));vram[1][:]=old_picture;vram[0][:]=bytes([227])*38400
 put('page',0);put('presented_transition',4);put('transition',10)
 steps=get('save_feedback_background_frames');lib.save_frame();assert get('save_feedback_background_frames')==steps
 lib.render();assert get('scene_present_phase')==2 and bytes(vram[0])==old_picture and bytes(oam)==old_oam
 assert lib.game_display_brightness()==4;put('page',1)
 timers={name:get(name) for name in ('px','py','ticks','ability_cd','invuln','transition_lock','toast_ticks','area_ticks','transition')}
 chord=1|2|4|8|256|512|16
 frame(chord,chord);assert get('scene_present_phase')==3 and get('game_state')==1
 assert all(get(name)==value for name,value in timers.items()) and get('save_feedback_background_frames')==steps
 new_picture=bytes(vram[1]);new_oam=bytes(oam);new_keys=list(cache[45:90]);assert lib.game_display_brightness()==10
 frame(chord,chord);assert get('scene_present_phase')==0 and get('game_state')==1
 assert bytes(vram[0])==new_picture and bytes(oam)==new_oam and list(cache[:45])==new_keys
 assert all(get(name)==value for name,value in timers.items()) and get('save_feedback_background_frames')==steps+1
 assert valid[0] and valid[1] and list(cache[:45])==list(cache[45:90])
 before_x=get('px');frame(chord,0);assert get('px')>before_x and get('game_state')==1 and not get('quickparty_open') and not get('swing')
 assert get('save_feedback_background_frames')==steps+2
 # Repeated death/room admission also replaces the scene phase safely.
 put('game_state',4);put('scene_present_phase',0);frame();frame(1,1);assert get('scene_present_phase')==2 and get('game_state')==1
 frame();frame();assert get('scene_present_phase')==0 and get('game_state')==1
 C.c_void_p.in_dll(lib,'screen').value=C.addressof(framebuffer)
 # Graphics-changing boss/campaign returns may not overwrite the old OAM's
 # referenced tiles during admission/hold. Host mirrors the real upload DMA.
 tile_memory=(C.c_ubyte*16384).from_address(0x06014000)
 for source,target in ((2,3),(16,0)):
  put('room',source);put('game_state',1);put('scene_present_phase',0);tile_memory[:]=bytes([233])*16384
  lib.enter_room(target,0);assert get('scene_present_phase')==1 and bytes(tile_memory)==bytes([233])*16384
  lib.render();assert get('scene_present_phase')==2 and bytes(tile_memory)==bytes([233])*16384
  put('page',get('page')^1);put('keys',0);put('pressed',0);lib.update();lib.save_frame();old_records=bytes(oam);lib.render()
  assert get('scene_present_phase')==3 and get('scene_actor_pending')==1 and bytes(tile_memory)==bytes([233])*16384 and bytes(oam)==old_records
  lib.publish_scene_actors();assert get('scene_actor_pending')==0 and bytes(tile_memory)!=bytes([233])*16384
  lib.game_display_brightness();put('page',get('page')^1)
  frame();assert get('scene_present_phase')==0
 C.c_void_p.in_dll(lib,'screen').value=C.addressof(framebuffer)
 # A queued critical arrival must never reuse the prior Saved status while
 # the bank still contains the previous state. Writer admission stays deferred.
 new_game();assert load().economy.gold==0
 assert lib.economy_award_combat(C.byref(live),1)==1;lib.save_game();lib.enter_room(0,3)
 for expected_phase in (1,2,3,0):
  assert get('scene_present_phase')==expected_phase and get('game_state')==1 and get('save_requested') and not get('save_feedback_ordinary')
  assert lib.game_save_badge_id()==ids.index('TX_FB_SAVING') and load().economy.gold==0
  frame()
 assert get('game_state')==6;drain();assert load().economy.gold==1
 # Full-frame independent ending composition over the retained full-world
 # underlay, both pages, picker interruption and failure overlays. Exercise
 # every presentation phase, release gate and representative clip boundaries.
 win_cases=win_negatives=0
 for test_page in (0,1):
  put('page',test_page);put('room',0);put('game_state',5);put('scene_present_phase',0);put('area_ticks',70)
  for ending_phase,scrolls in ((0,(0,)),(1,(0,6,7,120,340,440,590,700,849,856)),(2,(856,))):
   for scroll in scrolls:
    for armed in (0,1):
     put('ending_credits_phase',ending_phase);put('ending_credits_scroll',scroll);put('ending_credits_armed',armed)
     for failure in (0,1):
      for picker in (0,1):
       put('save_failed',failure);put('save_failure_notice',failure);put('quickparty_open',picker)
       before=(bytes(live),bytes(ram),tuple(get(n)for n in ('ending_credits_phase','ending_credits_scroll','ending_credits_armed','ending_credits_revision','save_feedback_requests')))
       put('reference_ending_mutation',0)
       vram[test_page][:]=bytes([219])*38400;lib.reference_render_static();expected_win=bytes(vram[test_page])
       (C.c_int*2).in_dll(lib,'play_strip_valid')[test_page]=(C.c_int*2).in_dll(lib,'play_strip_clean')[test_page]=1
       vram[test_page][:]=bytes([131])*38400;lib.render_static();assert bytes(vram[test_page])==expected_win,(test_page,ending_phase,scroll,armed,failure,picker)
       assert before==(bytes(live),bytes(ram),tuple(get(n)for n in ('ending_credits_phase','ending_credits_scroll','ending_credits_armed','ending_credits_revision','save_feedback_requests')))
       assert not (C.c_int*2).in_dll(lib,'play_strip_valid')[test_page] and not (C.c_int*2).in_dll(lib,'play_strip_clean')[test_page];win_cases+=1
       # Prove this matrix rejects old/missing card hints and a wrong roll
       # pixel, rather than just accepting a shared production drawing call.
       for mutation in ((1,2,3)if ending_phase==0 else (3,)):
        put('reference_ending_mutation',mutation);lib.reference_render_static()
        assert bytes(vram[test_page])!=expected_win,('insensitive ending oracle',mutation);win_negatives+=1
 put('reference_ending_mutation',0);put('ending_credits_phase',0);put('ending_credits_scroll',0);put('ending_credits_armed',0)
 put('quickparty_open',0);C.c_void_p.in_dll(lib,'screen').value=C.addressof(framebuffer)
 print('PASS current ending composition:',win_cases,'full frames;',win_negatives,'mutation negatives')
 # The four compact status labels occupy only the reserved HUD gap. Exact
 # rendered glyphs/borders and OBJ edge exclusion are checked independently.
 lib.save_feedback_reset();lib.game_shop_reset();put('save_failure_notice',0);put('save_requested',0)
 texts=(UiText*len(ids)).in_dll(lib,'ui_texts')
 palette=dict((name,int(value)) for name,value in re.findall(r'#define (PAL_\w+) (\d+)',(ROOT/'src/assets.h').read_text()))
 for label,mode,failed,background in [('TX_FB_SAVING',1,0,1),('TX_FB_SAVED',1,0,0),('TX_FB_WORKING',10,0,0),('TX_FB_SAVE_ERROR',1,1,0)]:
  lib.save_feedback_complete(1);put('game_state',mode);put('save_failed',failed);put('save_feedback_background',background)
  badge=texts[ids.index(label)];assert badge.width<=56
  assert lib.game_save_badge_id()==ids.index(label)
  left=200-badge.width-8;top=3;width=badge.width+8;height=17;x=left+4
  assert lib.game_save_badge_left()==left and left>=136
  expected_badge=bytearray([241])*38400
  for yy in range(top,top+height):
   for xx in range(left,200):expected_badge[yy*240+xx]=45 if yy in (top,top+height-1) or xx in (left,199) else 1
  for i in range(badge.count[x&1]):
   run=badge.runs[x&1][i]
   for pair in range(run.count):
    pixel=(top*120+x//2+run.offset+pair)*2
    for side in range(2):
     if run.mask&(1<<side):
      xx=(pixel+side)%240;yy=(pixel+side)//240;assert left<xx<199 and top<=yy<top+height-1
      expected_badge[pixel+side]=palette['PAL_TEAL2']
  framebuffer[:]=bytes([241])*38400;lib.game_draw_save_badge();assert bytes(framebuffer)==expected_badge
  for xx,yy,w,h,visible in [(left,3,8,8,False),(left-8,3,8,8,True),(200,3,8,8,True),(left,20,8,8,True),(204,8,8,8,True),(216,3,16,16,True)]:
   put('obj_count',0);lib.obj_add(0,xx,yy,w,h,0,9999,0);assert get('obj_count')==int(visible),(label,xx,yy)
  for heart in range(12):
   put('obj_count',0);lib.obj_add(0,3+heart*9,3,16,16,0,9999,0);assert get('obj_count')==1
 lib.save_feedback_reset();put('save_failed',0);put('game_state',1)
 assert lib.game_save_badge_left()==240
 put('obj_count',0);lib.obj_add(0,196,3,64,8,0,9999,0);assert get('obj_count')==1
 report={'passed':True,'scope':'fresh reconstructed real-engine host integration','walking_entries':count,'hostile_and_quest_gates':True,'closed_routes_keep_actions_and_latches':4,'shop_prompt_exact_range':True,'ordinary_blocked_updates':0,'dirty_requests':21,'coalesced_writes':2,'critical_frozen_updates':critical.count(6),'failure_glyph_pixels':len(glyphs),'failure_retry_verified_only':True,'card_and_animation_pixel_exact':True,'world_composite_views':len(covers)*count,'bottom_strip_pages_pixel_exact':True,'clean_strip_lazy_capture_pages':2,'title_wordmark_pixel_exact':True,'status_badge_labels_pixel_exact':4,'arrival_reset_and_wave_teardown':True,'scene_handoff_bitmap_oam_brightness_and_input':True,'arrival_obj_tile_upload_deferred':True,'queued_critical_arrival_status':True,'win_current_ending_full_frame_cases':win_cases,'win_mutation_negatives':win_negatives,'tonic_reset_boundary_safe':True,'gold_once_per_spawn':6,'actual_party_xp':xp}
 if os.environ.get('PLAYER_FEEDBACK_RESULT'):Path(os.environ['PLAYER_FEEDBACK_RESULT']).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
