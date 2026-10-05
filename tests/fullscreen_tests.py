#!/usr/bin/env python3
"""Native 240x160 framebuffer, transparent HUD and hardware-cadence regression.

Controller-only setup, read-only ROM/VRAM/OAM observation. Pixel comparisons use
all160 source rows; only authored trial floor decorations and an opened bridge
are excluded from bitmap comparison. Hardware actors/HUD need NO bitmap mask.
The native screenshot is separately checked outside actual nonzero OBJ pixels.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
import hashlib
from pathlib import Path
import struct
from evolution_tests import EvolutionRun, ROOT, PLAY, PAUSE, AIDS

CYCLES_PER_FRAME=280896
REFRESH_HZ=16777216/CYCLES_PER_FRAME
SHAPES=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))

class FullscreenRun(EvolutionRun):
    def oam(self):
        entries=[]
        raw=self.e.bytes(0x07000000,1024)
        for i in range(128):
            a0,a1,a2,_=struct.unpack_from('<HHHH',raw,i*8)
            if a0&0x300==0x200:continue
            shape=a0>>14;size=a1>>14
            assert shape<3 and not(a0&0x100), 'test expects non-affine ordinary OBJ'
            w,h=SHAPES[shape][size];x=a1&511;y=a0&255
            if x>=256:x-=512
            if y>=160:y-=256
            entries.append({'slot':i,'x':x,'y':y,'w':w,'h':h,'tile':a2&1023,'priority':a2>>10&3,'flipx':bool(a1&0x1000),'flipy':bool(a1&0x2000),'eightbit':bool(a0&0x2000)})
        return entries

    def bitmap_mask(self,cx,cy):
        mask=bytearray(38400)
        def box(x,y,w,h):
            for yy in range(max(0,y),min(160,y+h)):
                for xx in range(max(0,x),min(240,x+w)):mask[yy*240+xx]=1
        for x,y,_ in AIDS:
            # Exact documented decoration bounds, not a reserved screen strip.
            if 12<=y-cy<=153:box(x-cx-14,y-cy-5,29,15)
        if self.get('bridge_open'):box(226-cx,152-cy,31,29)
        return mask

    def obj_mask(self):
        mask=bytearray(38400);tiles=self.e.bytes(0x06010000,32768)
        for o in self.oam():
            assert o['eightbit'], 'test expects 8-bit OBJ'
            for sy in range(o['h']):
                y=o['y']+sy
                if not 0<=y<160:continue
                ty=o['h']-1-sy if o['flipy'] else sy
                for sx in range(o['w']):
                    x=o['x']+sx
                    if not 0<=x<240:continue
                    tx=o['w']-1-sx if o['flipx'] else sx
                    index=o['tile']*32+(ty//8)*(o['w']//8)*64+(tx//8)*64+(ty%8)*8+tx%8
                    if tiles[index]:mask[y*240+x]=1
        return mask

    def pixel_case(self,name):
        self.step(150)
        self.check(self.get('game_state')==PLAY and not self.get('toast_ticks') and not self.get('area_ticks'),name+': source comparison has no transient text or transition')
        cx,cy=self.get('camera_x'),self.get('camera_y');atlas=self.e.bytes(self.sym['overworld_bitmap'],480*320)
        page=0x0600a000 if self.e.read(0x04000000,2)&16 else 0x06000000
        actual=self.e.bytes(page,38400);expected=b''.join(atlas[(cy+y)*480+cx:(cy+y)*480+cx+240] for y in range(160))
        mask=self.bitmap_mask(cx,cy);mismatch=[i for i,(a,b) in enumerate(zip(actual,expected)) if not mask[i] and a!=b]
        rows=[sum(not mask[y*240+x] for x in range(240)) for y in range(160)]
        result={'camera':[cx,cy],'bitmap_compared_pixels':sum(rows),'bitmap_mismatched_pixels':len(mismatch),
                'mismatch_examples':[[i%240,i//240,actual[i],expected[i]] for i in mismatch[:12]],'compared_pixels_by_row':rows}
        self.observations.setdefault('full_viewport_source_pixels',{})[name]=result
        self.shot(name)
        self.check(not mismatch,name+': all240x160 viewport rows match source pixels exactly outside authored floor details')
        self.check(all(n>0 for n in rows),name+': no top or bottom strip was omitted from pixel verification')
        # Screenshots are native RGB, using the core's 5->8-bit color expansion.
        palette=self.e.bytes(0x05000000,512);colors=[]
        for i in range(256):
            c=int.from_bytes(palette[i*2:i*2+2],'little');colors.append(tuple(((((c>>s)&31)<<3)|(((c>>s)&31)>>2)) for s in (0,5,10)))
        objmask=self.obj_mask();rgb=self.e.screenshot().tobytes();bad=[];n=0
        for i,pixel in enumerate(expected):
            if mask[i] or objmask[i]:continue
            n+=1
            if tuple(rgb[i*3:i*3+3])!=colors[pixel]:bad.append(i)
        result.update({'screenshot_compared_pixels':n,'screenshot_mismatched_pixels':len(bad),'masked_nonzero_obj_pixels':sum(objmask)})
        self.check(not bad,name+': native screenshot matches source behind transparent actors and floating HUD')
        return cx%4

    def alignment_case(self):
        base=self.snapshot('fullscreen-alignment-start');self.navigate(240,280);seen=set()
        for i in range(18):
            self.step(45);phase=self.get('camera_x')%4
            if phase not in seen:seen.add(self.pixel_case(f'viewport-alignment-{phase}'))
            if len(seen)==4:break
            self.step(1,'RIGHT')
        self.check(seen=={0,1,2,3},'all four DMA viewport word alignments are source-pixel exact')
        self.restore(base)

    def hud_case(self,name,hearts):
        self.step(140);entries=self.oam()
        positions={(o['x'],o['y'],o['w'],o['h']) for o in entries if o['priority']==0}
        self.check(self.get('max_hp')==hearts,name+': expected permanent heart capacity')
        self.check(all((3+9*i,3,16,16) in positions for i in range(hearts)),name+': all hearts float upper left')
        self.check((216,3,16,16) in positions and (204,8,8,8) in positions,name+': companion and action icons float upper right')
        for o in entries:
            if o['priority'] in (1,2):self.check(o['y']<160 and o['y']+o['h']>0,name+': actor is culled against full160-row viewport')
        self.shot(name);self.observations[name+'_oam']=entries

    def cadence_native(self,name,frames=240,keys=None):
        state=self.snapshot(name+'-before-cadence');self.step(8)
        before=self.get('frame');page=self.e.read(0x04000000,2)&16;deltas=[];flips=[];cycles=[]
        for i in range(frames):
            self.raw_step(1,keys(i) if keys else 0)
            now=self.get('frame');p=self.e.read(0x04000000,2)&16
            deltas.append((now-before)&0xffffffff);flips.append(p!=page);cycles.append(self.get('render_cycles'));before,page=now,p
        result={'scene':name,'hardware_frames':frames,'native_hz':REFRESH_HZ,'simulation_updates':sum(deltas),'display_flips':sum(flips),
                'update_histogram':dict(Counter(deltas)),'maximum_cycles':max(cycles),'frame_budget_cycles':CYCLES_PER_FRAME,
                'source':'emulated GBA VBlank and displayed DISPCNT page, never wall-clock host FPS'}
        self.scenes.append(result);self.restore(state)
        self.check(all(d==1 for d in deltas) and all(flips),name+': one update and present every59.73Hz hardware frame')
        self.check(max(cycles)<CYCLES_PER_FRAME,name+': measured rendering/input work fits native hardware frame budget')

    def top_edge_case(self):
        base=self.snapshot('top-edge-before');self.navigate(240,100);self.step(90)
        # Grove aid at(320,72) moves through top of screen as camera scrolls south.
        seen_partial=False;seen_hidden=False
        displayed_cy=self.get('camera_y')
        for _ in range(100):
            cy=self.get('camera_y');expected_y=72-8-displayed_cy
            # OBJ_PROP+2*256 =130? use declared tile formula directly.
            matches=[o for o in self.oam() if o['tile']==512+(12352+2*256)//32]
            if -16<expected_y<0:
                seen_partial=True;self.check(any(o['y']==expected_y for o in matches),'top-edge trial actor survives partial clipping without24-pixel offset')
            if expected_y<=-16:
                seen_hidden=True;self.check(not matches,'top-edge trial actor culls only when fully above screen');break
            displayed_cy=cy
            self.raw_step(1,'DOWN')
        self.check(seen_partial and seen_hidden,'controller scroll observes both partial and fully culled top-edge actor')
        self.shot('top-edge-culling');self.restore(base)

    def run(self):
        # Frozen campaign collision-table fingerprint:76 original world rectangles.
        collision=self.e.bytes(self.sym['overworld_solids'],608)
        self.check(hashlib.sha256(collision).hexdigest()=='99978d22a28f0c996f38e4a3913aabdc2844f6e396902a1ad02a7826393ec10f','compiled grove collision coordinates remain byte-identical to frozen campaign')
        self.step(90);self.tap('SELECT',4,4);self.dialogs();self.hud_case('six-hearts-village',6);self.menu_case('fullscreen-village')
        self.nextroom(1);self.snapshot('fullscreen-grove-entry');self.alignment_case();self.hud_case('six-hearts-grove',6)
        self.cadence_native('fullscreen-grove-scroll',360,lambda i:'LEFT' if i<90 else 'RIGHT' if i<180 else 'LEFT' if i<270 else 'RIGHT')
        self.goto(x=240);self.goto(y=180);self.select(1);self.ready();self.tap('R');self.dialogs()
        self.navigate(92,72,radius=10);self.tap('A');self.dialogs();self.hud_case('eight-hearts-grove',8)
        self.top_edge_case();self.menu_case('fullscreen-eight-hearts')
        self.cadence_native('fullscreen-eight-hearts-companion',360)
        self.snapshot('fullscreen-eight-hearts-grove');self.report()

    def report(self):
        super().report();r=json.loads((self.out/'evolution-report.json').read_text());r['suite']='fullscreen-native-pixel-and-cadence'
        (self.out/'fullscreen-report.json').write_text(json.dumps(r,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'build/fullscreen-qa');a=p.parse_args();r=FullscreenRun(a.rom,a.symbols,a.output)
    try:r.run()
    except Exception as exc:r.failures.append({'error':str(exc),'status':r.status()});r.shot('failure');raise
    finally:r.report();r.e.close()
    return int(bool(r.failures))

if __name__=='__main__':raise SystemExit(main())
