#!/usr/bin/env python3
"""Current final-chapter mixed-axis camera/copy/OAM oracle, not native timing."""
from pathlib import Path
import hashlib,json,re,shlex,os,tempfile
import test_horizons_camera as old
from test_covenants_engine import function
ROOT=Path(__file__).resolve().parents[1]
def main():
 paths=['src/game.c','src/covenants_engine.inc','src/modal_blit.inc','src/covenants_art.h','src/covenants_art.c','src/covenants_creature_art.c','src/covenants_creature_art.h','src/covenants_draw.inc','assets/covenants_world/geometry.json']
 sources={p:(ROOT/p).read_text()for p in paths}
 for inc in re.findall(r'^#include "(covenants_art_data/[^\"]+)"',sources['src/covenants_art.c'],re.M):
  p='src/'+inc;t=(ROOT/p).read_text()
  if 'covenants_art_rooms['in t:sources[p]=t;table=t
 rows=re.findall(r'\{(\d+),(\d+),covenants_background_room(\d+),([^,]+),',table)
 rooms=[(int(a),int(w),int(h),odd!='0')for w,h,a,odd in rows]
 assert [r[0]for r in rooms]==list(range(70,78))
 geometry=json.loads(sources['assets/covenants_world/geometry.json'])['rooms']
 assert [(r['id'],r['width'],r['height'])for r in geometry]==[r[:3]for r in rooms]
 game=sources['src/game.c'];defines=[]
 for name in ('PLAY','DIALOG','PAUSE','DEAD','SAVE_PENDING','EVOLVE_CONFIRM','EVOLVE_ANIM','EVENT_PENDING','SAVE_NOTICE_Y','SAVE_NOTICE_H'):
  defines+=re.findall(r'^#define '+name+r'\s+[^\n]+',game,re.M)
 head=old.HEAD.replace('#include "horizons_art.h"','#include "horizons_art.h"').replace('const CovenantsArtRoom covenants_art_rooms[8] = {};','const HorizonsArtRoom horizons_art_rooms[8] = {};').replace('unsigned covenants_creature_art_walk_index(unsigned, unsigned) { std::abort(); }','')
 head=head.replace('const u8 horizons_sprites[HORIZONS_SPR_COUNT][256]','const u8 covenants_sprites[COVENANTS_SPR_COUNT][256]').replace('return horizons_sprites[0];','return covenants_sprites[0];')
 head+='#include "journal_nav.h"\nint world_mask_disabled; int display_state_override=-1; int save_failed; int economy_pending(void){return 0;} unsigned save_feedback_badge(void){return 0;} unsigned game_shop_reward_visible(void){return 0;} int game_save_badge_id(void){return 0;} int game_save_badge_left(void){return 240;} int game_display_state(void){return display_state_override<0?game_state:display_state_override;}\n'
 head+='#include "covenants_creature_art.h"\n'
 art=sources['src/covenants_creature_art.c'];start=art.index('const struct CovenantsCreatureArtEntry');end=art.index('\n};',start)+3
 head+=art[start:end]+'\n'+function(art,'covenants_creature_art_index')+function(art,'covenants_creature_art_walk_index')
 storage=[];maps=[]
 for i,(_,w,h,odd)in enumerate(rooms):
  storage.append(f'static u8 pattern_{i}[{w*h}];');ptr='nullptr'
  if odd:storage.append(f'static u8 shifted_{i}[{w*h}];');ptr=f'shifted_{i}'
  maps.append(f'{{{w},{h},pattern_{i},{ptr},nullptr,0,nullptr,nullptr}}')
 storage.append('const CovenantsArtRoom covenants_art_rooms[8]={'+','.join(maps)+'};')
 parts=[head,'\n'.join(defines),'\n'.join(storage)]
 for name in ('scrolling_room','world_width','world_height','camera_update'):parts.append(old.extract_function(game,name,'src/game.c'))
 parts.append(sources['src/modal_blit.inc']);parts.append(old.extract_function(sources['src/covenants_engine.inc'],'copy_covenants','src/covenants_engine.inc'))
 for name in ('obj_add','region_pixels_actor','covenants_actor','region_form_actor'):parts.append(old.extract_function(game,name,'src/game.c'))
 # These are the engine-owned world-coordinate entrypoints; world actor layout
 # and NPC position checks belong to the separate world and native tests.
 wrappers=old.extract_function(sources['src/covenants_draw.inc'],'ra','src/covenants_draw.inc')+old.extract_function(sources['src/covenants_draw.inc'],'rf','src/covenants_draw.inc')
 checks=old.CHECKS.replace('room = 62; room < 70','room = 70; room < 78').replace('HorizonsArtRoom','CovenantsArtRoom').replace('horizons_art_rooms[room - 62]','covenants_art_rooms[room - 70]').replace('copy_horizons()','copy_covenants()').replace('rf(105,','rf(121,')
 actor=r'''static unsigned actor_checks(void) {
    unsigned checks=0;
    for(room=70;room<78;++room)for(int xc:sample_cameras(world_width()-240,false))for(int yc:sample_cameras(world_height()-160,true)) {
        camera_x=xc;camera_y=yc;game_state=PLAY;
        for(int y:{-16,-2,-1,0,7,15,159,160,167,168,174,175,176})for(int x=-10;x<252;x+=7) {
            obj_count=region_actor_cursor=0;ra(0,xc+x,yc+y);rf(121,xc+x,yc+y);
            bool npc=x>-8&&x<248&&y>-1&&y<175,creature=x>-8&&x<248&&y>-8&&y<168;
            check(obj_count==(int)npc+(int)creature,"actor foot-anchor visible count");int n=0;
            if(npc){check((obj_entries[n].a0&255)==((y-15)&255),"actor NPC foot anchor y");n++;}
            if(creature)check((obj_entries[n].a0&255)==((y-8)&255),"actor creature center anchor y");
            for(n=0;n<obj_count;n++){check((obj_entries[n].a1&511)==((x-8)&511),"actor x exactly one camera subtraction");check(obj_depth[n]==yc+y,"actor world foot depth");}checks++;
        }
    }
    return checks;
}
'''
 # Expected geometry is independent of the production coverage predicate.
 checks=checks.replace('for (int state : {PLAY, PAUSE, SAVE_PENDING, EVOLVE_CONFIRM,\n                                  EVOLVE_ANIM, EVENT_PENDING})','for (int state : {PLAY,DIALOG,PAUSE,SAVE_PENDING,EVOLVE_CONFIRM,EVOLVE_ANIM,EVENT_PENDING,11,12,13})')
 checks=checks.replace('journal_tab < 2','journal_tab < 17')
 checks=checks.replace('selected = has_selected; game_state = state;','selected = has_selected; game_state = state; display_state_override=(state==SAVE_PENDING||state==EVENT_PENDING||state==12)?(journal_tab&1?DIALOG:PAUSE):-1;')
 first=checks.index('                            if (width == 480 ||');last=checks.index('                            for (int y = 0;',first)
 expected=r"""                            int mode=(state==SAVE_PENDING||state==EVENT_PENDING||state==12)?(journal_tab&1?DIALOG:PAUSE):state;
                            if(mode==PAUSE){left=8;first=31;last=journal_tab==0?150:153;}
                            else if(mode==11||state==13){left=8;first=31;last=153;}
                            else if(mode==EVOLVE_CONFIRM){left=12;first=42;last=147;}
                            else if(mode==EVOLVE_ANIM&&selected){left=20;first=38;last=152;}
                            else if(mode==DIALOG){left=6;first=99;last=155;}
"""
 checks=checks[:first]+expected+checks[last:]
 checks=checks.replace('camera_x=xc;camera_y=yc;game_state=PLAY;', 'camera_x=xc;camera_y=yc;game_state=PLAY;display_state_override=-1;')
 checks=re.sub(r'static unsigned actor_checks\(void\) \{.*?\n\}\nint main',actor+'int main',checks,flags=re.S)
 results={};compiler=shlex.split(os.environ.get('CXX','c++'))
 with tempfile.TemporaryDirectory(prefix='covenants-camera-')as td:
  path=Path(td);body='\n'.join(parts)+wrappers+checks
  results['strict']=old.run(compiler,path,'strict',body)
  results['sanitized']=old.run(compiler,path,'sanitized',body,sanitize=True)
  assert results['strict']==results['sanitized']
  bad=wrappers.replace('(sprite,x,y)','(sprite,x-camera_x,y-camera_y)').replace('(form,x,y)','(form,x-camera_x,y-camera_y)');assert bad!=wrappers
  results['negative_control']=old.run(compiler,path,'double-camera','\n'.join(parts)+bad+checks,must_fail=True)
  foot_bad=body.replace('obj_add(off,x-8,y-15','obj_add(off,x-8,y-8');assert foot_bad!=body
  results['foot_anchor_negative_control']=old.run(compiler,path,'center-instead-of-foot',foot_bad,must_fail=True)
 out=ROOT/'build/covenants-camera-host.json';out.write_text(json.dumps({'scope':__doc__,'native_gameplay':False,'room_dimensions':rooms,'results':results,'sources':{p:hashlib.sha256(t.encode()).hexdigest()for p,t in sources.items()}},indent=2)+'\n')
 print('PASS: '+json.dumps(results['strict'])+' strict + ASan/UBSan; double-camera mutation rejected')
if __name__=='__main__':main()
