#!/usr/bin/env python3
"""Same-ROM notice-cache/full-render equivalence during real91/106 field powers.

Owned member selection and casts use the existing controller harness. Only
actor coordinates prepare the site; differential branches explicitly modify
cache controls and presentation-only toast/reward fields, then restore the
original live state. They compare matching completed logical frames, since the
uncached reference may be slower. The active cache starts naturally warm; text-ID changes exercise cold builds.
OBJ bytes are diagnostic because the next actor upload can already be in flight
at a hardware-frame boundary. This is a pixel/state oracle, not cadence or
fresh progression acquisition evidence; run the ordinary power suite for that.
"""
from pathlib import Path
import argparse,hashlib,json,re,sys,shutil
from connected_roads_power_native import RoadPowerSuite
from connected_roads_native import ROOT,Save5Tests,sha,KEYS

def sha_bytes(data):return hashlib.sha256(data).hexdigest()

class NoticeSuite(RoadPowerSuite):
    def __init__(self,args):
        super().__init__(args);self.pixel_results=[];self.restores=0
        self.text_ids=list(dict.fromkeys(re.findall(r'\bTX_[A-Z0-9_]+\b',(ROOT/'src/ui.h').read_text())))
        self.notice_ids=[self.text_ids.index(n)for n in ('TX_PF_ROUTE_LATER','TX_C_SAVE_FAILED')]
        self.candidate['notice_helper_sha256']=sha(__file__);shutil.copyfile(__file__,self.out/'notice-helper.py')
    def power(self,room,command,orientation):
        if not self.a.cast_from_snapshot:return super().power(room,command,orientation)
        self.load(self.fixture_by_room[room]);self.choose_command(command)
        edge=2 if room in (62,66,70)else 0
        road=next(r for r in self.rows if r['room']==room and r['edge']==edge and(room!=62 or r['target']==61))
        self.phase='setup';self.prepare(*self.mouth_start(road,road['center']),edge=road['edge'],suppress=False)
        self.phase='measured';self.step(1,KEYS[(edge+1)%4]);self.step(3)
        self.shot('before-cast-%02d-%03d'%(room,command))
    def shot(self,name,moving_key=None):
        super().shot(name,moving_key)
        base=self.out/(name+'.state');self.e.state(base);original_phase=self.phase
        samples=[];start=self.g('render_profile_frame')
        for disabled in (0,1):
            self.e.state(base,load=True);self.restores+=1
            self.phase='prepared_notice_reference'if disabled else'prepared_notice_cache'
            self.put('play_notice_cache_disabled',disabled,reason='same-ROM old notice raster reference')
            rows=[]
            for index in range(180 if self.a.cast_from_snapshot else 28):
                # Same viewport is redrawn in both branches, retaining all
                # moving world, actor, power, sound and gameplay simulation.
                if self.a.force_full:
                    self.put('cache_valid',0,reason='force identical full-render path')
                    self.put('cache_valid',0,offset=4,reason='force identical full-render path')
                if self.a.presentation_probes and index in (2,7):
                    self.put('toast_id',self.notice_ids[(index==7)],reason='presentation-only notice width/key switch')
                    self.put('toast_ticks',5 if index==7 else 20,reason='presentation-only expiry coverage')
                if self.a.presentation_probes and index==16:
                    for n,v in [('reward_ticks',8),('game_shop_reward_xp',180),('game_shop_reward_gold',6),('game_shop_revision',self.g('game_shop_revision')+1)]:
                        self.put(n,v,reason='presentation-only reward over notice priority')
                target=start+index+1
                for attempt in range(5):
                    self.step(1,'R'if self.a.cast_from_snapshot and index==0 else 0)
                    if self.g('render_profile_frame')>=target:break
                completed=self.g('render_profile_frame')
                assert completed==target,(index,target,completed)
                page=int(bool(self.e.read(0x04000000,2)&16))
                image=self.e.screenshot();image.save(self.out/('%s-%d-%02d.png'%(self.case,disabled,index)));pixels=image.tobytes();oam=self.e.bytes(0x07000000,1024)
                bitmap=self.e.bytes(0x0600a000 if page else 0x06000000,38400)
                state={k:self.g(k)for k in ('frame','room','px','py','camera_x','camera_y','return_power_kind','return_power_time','horizons_power_kind','horizons_power_time','ability_cd','toast_ticks','reward_ticks')}
                rows.append({'completed':completed,'page':page,'pixels':hashlib.sha256(pixels).hexdigest(),'notice_rgb':sha_bytes(image.crop((0,138,240,160)).tobytes()),'outside_notice_rgb':sha_bytes(image.crop((0,0,240,138)).tobytes()),'bitmap':hashlib.sha256(bitmap).hexdigest(),'notice_bitmap':sha_bytes(bitmap[138*240:]),'outside_notice_bitmap':sha_bytes(bitmap[:138*240]),'oam':hashlib.sha256(oam).hexdigest(),'obj_tiles':sha_bytes(self.e.bytes(0x06014000,16384)),'palettes':sha_bytes(self.e.bytes(0x05000000,1024)),'state':state,'diagnostic':{'hardware_frame':self.e.frame,'io':{hex(offset):self.e.lib.eb_io16(self.e.ptr,offset)for offset in(0,6,0x0c,0x20,0x22,0x24,0x26,0x28,0x2a,0x2c,0x2e,0x40,0x42,0x44,0x46,0x48,0x4a,0x50,0x52,0x54)},'profile':{n:self.g(n)for n in('render_profile_frame','render_profile_serial','render_profile_world','render_profile_card','render_profile_actors','render_profile_vblank_start','render_profile_vblank_end','render_profile_commit','render_profile_deferred_actors','presented_transition','scene_actor_pending')}}})
            samples.append(rows)
        for index,(a,b)in enumerate(zip(*samples)):
            comparable=('completed','page','pixels','bitmap','oam','palettes','state')
            ok=all(a[k]==b[k]for k in comparable)and a['diagnostic']['io']==b['diagnostic']['io'];row={'case':self.case,'index':index,'passed':ok,'optimized':a,'uncached':b};self.pixel_results.append(row)
            self.check('notice cache matches old full renderer at completed frame %d'%a['completed'],ok,row if not ok else None)
        self.e.state(base,load=True);self.restores+=1;self.phase=original_phase
    def run(self):
        for room in self.a.rooms:
            for command in self.a.commands:
                self.section('notice-%02d-%03d'%(room,command),lambda room=room,command=command:self.power(room,command,'tangent'))
        self.report();self.trace.close()
        if self.e:self.e.close()
        Save5Tests.doClassCleanups()
        failures=[c for c in self.checks if not c['passed']]
        report={'scope':__doc__,'passed':not failures,'candidate':self.candidate,'forced_full_world':self.a.force_full,'presentation_probes':self.a.presentation_probes,'cast_from_snapshot':self.a.cast_from_snapshot,'same_rom_state_restores':self.restores,'comparisons':self.pixel_results,'failures':failures}
        report['equal_counts']={key:sum(row['optimized'][key]==row['uncached'][key]for row in self.pixel_results)for key in('pixels','notice_rgb','outside_notice_rgb','bitmap','notice_bitmap','outside_notice_bitmap','oam','obj_tiles','palettes','state')}
        report['display_io_equal_count']=sum(row['optimized']['diagnostic']['io']==row['uncached']['diagnostic']['io']for row in self.pixel_results)
        (self.out/'notice-equivalence.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'passed':not failures,'comparisons':len(self.pixel_results),'failure_count':len(failures),'equal_counts':report['equal_counts'],'display_io_equal_count':report['display_io_equal_count']},indent=2));return int(bool(failures))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','symbols','source-manifest','bridge','fixtures','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+name,required=True)
    p.add_argument('--rooms',nargs='+',type=int,default=[30,46,70]);p.add_argument('--commands',nargs='+',type=int,choices=[91,106],default=[91,106])
    p.add_argument('--force-full',action='store_true',help='Diagnostic stress: disable world bitmap reuse on every frame')
    p.add_argument('--presentation-probes',action='store_true',help='Inject explicit synthetic toast/reward changes')
    p.add_argument('--cast-from-snapshot',action='store_true',help='Replay full180-frame R cast lifecycle in both branches')
    a=p.parse_args();a.directions=['tangent'];a.skip_clear_probes=True
    return NoticeSuite(a).run()
if __name__=='__main__':sys.exit(main())
