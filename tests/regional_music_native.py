#!/usr/bin/env python3
"""Regional soundtrack native mGBA tests, with explicit synthetic route labels.

Controller footage is blank-cartridge earned. Exhaustive room and long-loop
fixtures change the room only during the opening; they do not claim gameplay
acquisition, imported saves, or machine-state transport.
"""
import argparse,ctypes as C,hashlib,json,sys,traceback,shutil,subprocess
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.signal import correlate
from lanterns_native import Suite,ROOT,N,FPS,LIMIT,sha,wav_read
from mgba_runner import keymask
class Regional(Suite):
    def __init__(self,a):
        super().__init__(a)
        self.report['provenance']['regional_harness_sha256']=sha(__file__)
        shutil.copyfile(__file__,self.out/'test-source/tests/regional_music_native.py')
        self.catalog=json.loads((ROOT/'assets/music/regional/catalog.json').read_text())['cues']
        self.sources=[np.frombuffer((ROOT/c['raw_path']).read_bytes(),np.int8).astype(np.int32) for c in self.catalog]
        plan=json.loads((ROOT/'assets/music/regional/room-plan.json').read_text())
        self.route=[next(i for i,c in enumerate(self.catalog) if c['id']==r['cue']) for r in plan['rooms']]
        self.report['suite']='regional-music-native';self.report['catalog_sha256']=sha(ROOT/'assets/music/regional/catalog.json')
        self.report['limitations'].append('Exhaustive room, death-state and long-loop fixtures are explicitly synthetic music tests, not a full controller-earned campaign.')
        for c,pcm in zip(self.catalog,self.sources):
            self.check('Exact cartridge PCM '+c['id'],(ROOT/c['raw_path']).read_bytes() in self.rom.read_bytes())
        self.check('ROM retains at least one MiB headroom',self.rom.stat().st_size<=32*1024*1024-1024*1024)
        self.report['rom_bytes']=self.rom.stat().st_size
    def step(self,n,keys=0,measured=True):
        self.report['inputs'].append({'case':self.case,'hardware_frame':self.e.frame,'frames':n,'keys':keymask(keys),'measured':measured,'video_offset':self.video_frames if self.recording else None})
        for _ in range(n):
            old=self.g('frame');oldstate=self.g('game_state');page=self.e.read(0x04000000,2)&16
            self.e.frames(1,keys)
            row={'case':self.case,'hw':self.e.frame,'frame':self.g('frame'),'state':self.g('game_state'),'room':self.g('room'),'delta':(self.g('frame')-old)&0xffffffff,'flip':bool((self.e.read(0x04000000,2)&16)!=page),'cycles':self.g('render_cycles'),'core_faults':int(self.e.lib.eb_faults(self.e.ptr)),'measured':measured,'player':[self.g('px'),self.g('py')],'swing':self.g('swing'),'summoned':self.g('summoned'),'psg1_on':bool(self.e.read(0x04000084,2)&1),'psg2_on':bool(self.e.read(0x04000084,2)&2)}
            row['music']={n:self.g(n)for n in ('music_faults','music_recoveries','music_stopped','music_irq_count','music_irq_late_max','music_track','music_requested','music_source_cursor','music_loops','music_transitions','music_produced','music_consumed')}
            row['music_cycles']=self.g('render_profile_music')
            self.rows.append(row);self.trace.write(json.dumps(row,separators=(',',':'))+'\n')
            assert not row['core_faults'],row
            assert not any(row['music'][n]for n in ('music_faults','music_recoveries','music_stopped')),row
            assert row['music']['music_track']<23 and row['music']['music_requested']<23,row
            if measured:
                reset=oldstate in(0,9) and row['state']==14 and row['frame']==0
                assert (row['delta']==1 or reset) and row['flip'] and row['cycles']<LIMIT,row
                assert row['music']['music_irq_late_max']<208,row
                assert row['music_cycles']<=20896,row
            if getattr(self,'transport_model',None):self.model_block()
            if self.recording:
                rgb=self.e.screenshot().tobytes();self.rgb_hash.update(rgb);self.encoder.stdin.write(rgb);self.video_frames+=1
    def ring_check(self):
        self.check('Repeated guard equals current first256',self.e.bytes(self.sym['music_ring'],256)==self.e.bytes(self.sym['music_ring']+8192,256))
        self.check('Current source cursor bounded',self.g('music_source_cursor')<len(self.sources[self.g('music_track')]))
    def finish_video(self):
        self.recording=False;samples=self.e.audio_stop();self.encoder.stdin.close();assert self.encoder.wait()==0;self.encoder_log.close();self.encoder=None
        audio_pcm,mixed=wav_read(self.out/'controller-native-audio.wav')
        mixed['nonzero_samples']=int(np.count_nonzero(audio_pcm))
        mixed['scope']='Native mixed output containing two regional cues and PSG1 effects; no single-cue sample correlation claim.'
        self.report['audio'].append(mixed)
        self.check('Controller capture is non-silent with concurrent native PSG1 effects',mixed['nonzero_samples']>0 and any(r['psg1_on'] and r['music']['music_consumed']>0 for r in self.rows if r['case']==self.case))
        subprocess.run(['ffmpeg','-y','-i',str(self.out/'controller-silent.mp4'),'-i',str(self.out/'controller-native-audio.wav'),'-c:v','copy','-c:a','aac','-ar','48000','-b:a','160k','-movflags','+faststart',str(self.out/'regional-gameplay.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(self.out/'regional-gameplay.mp4')],text=True));video=next(s for s in probe['streams']if s['codec_type']=='video');audio=next(s for s in probe['streams']if s['codec_type']=='audio')
        self.check('MP4 decoder preserves every hardware frame',int(video['nb_frames'])==int(video['nb_read_frames'])==self.video_frames==self.e.frame-self.video_start_hw and Fraction(video['r_frame_rate'])==FPS)
        self.check('Native audio/video sync is within one GBA hardware frame',abs(mixed['seconds']-self.video_frames/float(FPS))<1/float(FPS) and abs(float(audio['duration'])-float(video['duration']))<1/float(FPS))
        decoder=subprocess.Popen(['ffmpeg','-v','error','-i',str(self.out/'controller-native-lossless.mkv'),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE);h=hashlib.sha256();size=0
        while data:=decoder.stdout.read(1048576):h.update(data);size+=len(data)
        self.check('Lossless master independently decodes to exact native RGB frames',decoder.wait()==0 and size==self.video_frames*240*160*3 and h.hexdigest()==self.rgb_hash.hexdigest())
        self.report['video']={'file':'regional-gameplay.mp4','sha256':sha(self.out/'regional-gameplay.mp4'),'frames':self.video_frames,'frame_rate_ratio':str(FPS),'seconds':self.video_frames/float(FPS),'native_audio_samples':samples,'audio_minus_video_seconds':mixed['seconds']-self.video_frames/float(FPS),'cuts':0,'sram_imports':0,'game_ram_writes':0,'machine_states':0,'actual_mixed_audio':True,'native_rgb_sha256':h.hexdigest()}
    def controllers(self):
        super().controllers()
        rows=[r for r in self.rows if r['case']==self.case]
        self.check('Controller village to river changes original cue', {0,1}.issubset({r['music']['music_track'] for r in rows}))
        self.report['video']['regional_cues']=[self.catalog[i]['id'] for i in sorted({r['music']['music_track'] for r in rows})]
        self.save_report()
    def write_fixture(self,symbol,value,width=4):
        self.report['synthetic_fixture']['writes'].append({'symbol':symbol,'value':value,'width':width,'hardware_frame':self.e.frame})
        self.native_write(self.e.ptr,self.sym[symbol],value,width);self.report['game_ram_writes']+=1
    def synthetic(self):
        self.boot('synthetic-scene-fade-transport');self.tap('A');self.step(30)
        self.check('Paused opening isolates exhaustive route fixtures',self.g('game_state')==14)
        self.report['controller_only']=False;self.report['synthetic_fixture']={'purpose':'Exhaustive soundtrack transport, not controller-earned region access','writes':[]}
        produced=self.g('music_produced');ring=np.frombuffer(self.e.bytes(self.sym['music_ring'],8192),np.int8).astype(np.int32)
        self.timeline_first=produced-8192;self.timeline=[np.concatenate((ring[produced%8192:],ring[:produced%8192]))]
        self.transport_model={'track':0,'cursor':self.g('music_source_cursor'),'fade':False,'produced':produced,'blocks':0,'fade_blocks':0}
        approx=self.g('music_consumed');path=self.out/'all-room-transitions-native.wav';self.e.audio_start(path);self.step(60)
        expected_transitions=0;previous=0
        for room in list(range(78))+[77,70,62,68,69,68,67,0,54,60,1,17,56,1,0,78,255,0xffffffff]:
            expected=self.route[room] if room<78 else 0
            self.write_fixture('room',room);self.step(48)
            expected_transitions+=expected!=previous;previous=expected
            self.check('Native room route '+str(room),self.g('music_requested')==self.g('music_track')==expected)
            self.check('Only cue changes trigger fades '+str(room),self.g('music_transitions')==expected_transitions)
        self.e.audio_stop();a,meta=wav_read(path);v=a[:,0];expanded=np.repeat(np.concatenate(self.timeline),2)*96
        start=max(0,approx*2-2*self.timeline_first-4096);found=expanded[start:start+32768].tobytes().find(v[:8192].tobytes());assert found>=0 and found%4==0
        expected=expanded[start+found//4:start+found//4+len(v)];assert len(expected)==len(v)
        error=v-expected;meta.update(mismatched_samples=int(np.count_nonzero(error)),sample_identical_to_modeled_fades=not np.any(error),native_blocks_checked=self.transport_model['blocks'],native_fade_blocks_checked=self.transport_model['fade_blocks'])
        self.check('All route fades sample-identical in real mixed output',not np.any(error));self.report['audio'].append(meta)
        self.report['cases'].append({'name':self.case,'all_rooms':78,'invalid_ids':[78,255,0xffffffff],'transitions':expected_transitions,'fade_blocks':self.transport_model['fade_blocks'],'game_ram_writes':self.report['game_ram_writes']})
        self.transport_model=None;self.timeline=[];self.save_report()
    def regional_loops(self):
        self.boot('synthetic-all-cue-exact-loops');self.tap('A');self.step(30)
        self.report['controller_only']=False;self.report.setdefault('synthetic_fixture',{'purpose':'Explicit synthetic audio transport only','writes':[]})
        for i,c in enumerate(self.catalog):
            room=self.route.index(i);self.write_fixture('room',room);self.step(120)
            assert self.g('music_track')==i
            pcm=self.sources[i];approx=self.g('music_source_cursor')-(self.g('music_produced')-self.g('music_consumed'))
            path=self.out/(c['id'].lower()+'-two-native-loops.wav');self.e.audio_start(path)
            frames=int(np.ceil((2*len(pcm)+2048)/16384*float(FPS)));startloops=self.g('music_loops');self.step(frames);self.e.audio_stop()
            a,meta=wav_read(path);v=a[:,0]
            # Search source alignment around actual queued cursor; circular reference.
            base=approx-2048;ref=np.repeat(pcm[np.arange(base,base+8192)%len(pcm)],2)*96
            found=ref.tobytes().find(v[:8192].tobytes());assert found>=0 and found%4==0,(c['id'],approx)
            offset=base*2+found//4;expected=pcm[(np.arange(len(v))+offset)//2%len(pcm)]*96
            error=v-expected;meta.update(cue=c['id'],mismatched_samples=int(np.count_nonzero(error)),sample_identical_to_exact_period=not np.any(error),source_samples=len(pcm),loop_wraps=self.g('music_loops')-startloops)
            self.check(c['id']+' native two-loop exactness',not np.any(error) and meta['loop_wraps']>=2 and np.array_equal(a[:,0],a[:,1]));self.report['audio'].append(meta)
            self.report['cases'].append({'name':'two-loops-'+c['id'],'frames':frames,'loop_wraps':meta['loop_wraps']});self.save_report()
            print('PASS native exact loops',c['id'],flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba');p.add_argument('--output',type=Path,required=True);p.add_argument('--raw',type=Path,default=ROOT/'assets/music/lanterns/lanterns-gba-16384-s8.raw');p.add_argument('--expected-rom-sha',required=True);p.add_argument('--sysroot',type=Path,default=ROOT/'tools/sysroot');p.add_argument('--cases',default='controllers,synthetic,regional_loops');a=p.parse_args();s=Regional(a)
    try:
        for name in a.cases.split(','):getattr(s,name)()
        s.finish()
    except Exception as exc:
        s.report['result']='FAIL';s.report['failures'].append({'error':str(exc),'traceback':traceback.format_exc()});s.save_report()
        if s.e:s.e.screenshot(s.out/'failure.png')
        raise
    finally:s.close()
if __name__=='__main__':main()
