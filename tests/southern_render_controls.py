#!/usr/bin/env python3
"""Native selected-instance, Leafbound-anchor and post-modal OBJ pixel checks."""
import argparse,hashlib
from pathlib import Path
from southern_native_performance import SouthernPerformance
from southern_combat_tests import *
FORMS=[25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94]
def tiled(raw):return b''.join(raw[(ty+y)*16+tx:(ty+y)*16+tx+8] for ty in (0,8) for tx in (0,8) for y in range(8))
class SouthernRender(SouthernPerformance):
 def tile_check(self,label):
  hero=self.get('gfx_hero_frame');actual=self.e.bytes(0x06014000+6144,256);expected=tiled(self.e.bytes(self.sym['hero_frames']+hero*256,256));self.check(actual==expected,'resumed hero tile bytes equal exact current ROM pose')
  form=self.selected().form_id;self.check(form in FORMS,'render probe uses real selected Southern instance');code=self.get('gfx_companion_frame');index=FORMS.index(form);direction=code%16//4;casting=code>=32768
  ptr=self.sym['southern_creature_ability_frames']+((index*4+direction)*2+((code//65536)&1))*256 if casting else self.sym['southern_creature_direction_frames']+((index*4+direction)*4+code%4)*256
  actual=self.e.bytes(0x06014000+6400,256);expected=tiled(self.e.bytes(ptr,256));self.check(actual==expected,'selected companion tile bytes equal exact authored form and pose')
  actors=[]
  for slot in range(self.get('region_actor_cursor')):
   key=self.e.read(self.sym['region_actor_keys']+slot*4)
   if 4096<=key<4200:ptr=self.sym['south_sprites']+(key-4096)*256
   elif 200<=key<256:ptr=self.sym['world_sprites']+(key-200)*256
   else:continue
   offset=8448+slot*256 if slot<8 else 10816+(slot-8)*256
   self.check(self.e.bytes(0x06014000+offset,256)==tiled(self.e.bytes(ptr,256)),'actual regional actor cache contains exact keyed ROM tile pixels');actors.append(dict(slot=slot,key=key,offset=offset))
  self.check(bool(actors),'tile resume check includes visible keyed regional actors')
  return dict(label=label,hero_frame=hero,selected_form=form,selected_id=self.selected().instance_id,companion_code=code,casting=casting,companion_sha256=hashlib.sha256(actual).hexdigest(),actor_tiles=actors)
 def resume_pixels(self):
  self.restore('candidate-town-source');self.ready();records=[]
  for tab in range(8):
   self.open_tab(tab);self.step(4);self.check(all(o['priority']==0 for o in self.oam()),'opaque journal suppresses world OBJ');self.close_menu();self.step(4,'RIGHT');self.step(4,'LEFT');self.step(2);records.append(self.tile_check('journal-'+str(tab)))
   self.check(any(o['tile']==712 for o in self.oam()),'selected companion is actually submitted after closing journal')
  self.cases.append(dict(case='all-eight-journals-exact-OBJ-resume',records=records,passed=True))
 def leafbound_anchor(self):
  self.prepare(23,(240,224),1,False);self.step(1,'R');previous=self.row();trace=[];shifted=0
  for _ in range(16):
   self.step(1);row=self.row();p=row['power'];camera=self.display_camera();body=[o for o in self.oam() if o['tile']==712];self.check(len(body)==1,'Leafbound displays one actual selected companion body')
   candidates=[]
   for q in (row,previous):
    power=q['power'];x,y=(power['ex'],power['ey']) if power['time'] and power['age']<=12 else q['companion'];candidates.append((x-8-camera[0],y-9-camera[1]))
   self.check((body[0]['x'],body[0]['y']) in candidates,'Leafbound rendered body follows current or boundary-inflight authenticated pose')
   self.check(any(o['tile']==720 and o['x']==body[0]['x'] and o['y']==body[0]['y']+3 for o in self.oam()),'Leafbound shadow uses the same visual anchor as companion body')
   if p['age']<=8 and body[0]['x']!=row['companion'][0]-8-camera[0]:shifted+=1
   trace.append(dict(row=row,body=body[0],expected_positions=candidates));previous=row
  self.check(shifted>0,'native Leafbound visibly sidesteps away from ordinary follower anchor')
  self.cases.append(dict(case='Leafbound-native-body-shadow-anchor',shifted_frames=shifted,trace=trace,passed=True))
 def swapped_cast(self):
  self.prepare(23,(240,224),1,False);self.assign(0,26);self.assign(1,90);self.select_form(26);self.set_command(23);self.ready();self.step(1,'R');before=self.row();self.step(1,'L');self.step(1,'L+RIGHT');self.step(1);self.step(2);after=self.row()
  self.check(after['selected_form']==90 and after['power']['caster_id']==before['selected_id'],'real party swap preserves original cast owner')
  record=self.tile_check('swapped-active-Leafbound');self.check(not record['casting'],'different selected instance cannot borrow original casting art')
  self.cases.append(dict(case='cast-visual-matches-actual-selected-instance',before=before,after=after,pixels=record,passed=True))
 def run(self,only=None):
  self.boot()
  for name,fn in [('resume-pixels',self.resume_pixels),('Leafbound-anchor',self.leafbound_anchor),('swapped-cast',self.swapped_cast)]:self.run_case(name,fn)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('rom','symbols','elf','output','source-report','source-manifest'):p.add_argument('--'+k,type=Path,required=True)
 for k in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+k,required=True)
 a=p.parse_args();r=SouthernRender(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.source_report,a.source_manifest,a.elf)
 try:r.run()
 finally:r.report();r.e.close()
 return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
