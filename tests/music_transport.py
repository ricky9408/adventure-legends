#!/usr/bin/env python3
"""Native mGBA audio transport checks; no cross-ROM machine states.

Long WAVs are actual emulator output. Correlation checks transport fidelity,
not artistic listening approval. Game fixtures are authenticated earned SRAM.
"""
from pathlib import Path
import argparse, gzip, hashlib, json, sys, wave
import numpy as np
from scipy.signal import correlate
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT
sys.path.insert(0,str(BASE/'tools'))
from mgba_runner import Emulator
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def symbols(rom):
    return {v[2]:int(v[0],16) for line in rom.with_suffix('.sym').read_text().splitlines() if len(v:=line.split())==3}

class Native:
    def __init__(self,rom):
        self.s=symbols(rom);self.e=Emulator(rom);self.rows=[]
        def denied(*args,**kwargs):raise AssertionError('No game RAM write or machine-state import is permitted')
        self.e.write=denied;self.e.state=denied;self.e.lib.eb_write=denied
    def g(self,n):return self.e.read(self.s[n])
    def step(self,n,keys=0,strict=True):
        for _ in range(n):
            before=self.g('frame');page=self.e.read(0x04000000,2)&16
            self.e.frames(1,keys)
            row=dict(hw=self.e.frame,frame=self.g('frame'),update_delta=(self.g('frame')-before)&0xffffffff,page_flip=(self.e.read(0x04000000,2)&16)!=page,cycles=self.g('render_cycles'),state=self.g('game_state'),room=self.g('room'),faults=self.g('music_faults'),irq=self.g('music_irq_count'),late=self.g('music_irq_late_max'),cursor=self.g('music_source_cursor'),track=self.g('music_track'),produced=self.g('music_produced'),consumed=self.g('music_consumed'),strict=strict)
            self.rows.append(row)
            assert not row['faults'],row
            if strict:assert row['update_delta']==1 and row['page_flip'] and row['cycles']<280896,row
    def boot(self,fixture=None):
        if fixture:self.e.load_save(fixture);self.e.reset()
        self.step(150,strict=False)
        if fixture:self.step(2,'START',False);self.step(180,strict=False)
    def close(self):self.e.close()

def pcm(slug):
    return np.array([int(v) for p in sorted((ROOT/'src/music_data').glob(slug+'_*.inc')) for v in p.read_text().replace('\n','').split(',') if v],np.int16)

def analyze_audio(path,slug,approx):
    with wave.open(str(path),'rb') as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(32768,2,2)
        a=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2)
    assert np.array_equal(a[:,0],a[:,1])
    actual=a[:,0].astype(np.int32)
    source=pcm(slug).astype(np.int32)*96
    # A frame's approximate cursor narrows the alignment search to +/-1024
    # source samples; offsets are measured rather than assumed.
    start=max(0,approx-1024);end=approx+2048
    ref=np.repeat(np.resize(source,end+32768),2)[start*2:(end+32768)*2]
    probe=actual[:16384].astype(float)
    corr=correlate(ref.astype(float),probe,mode='valid',method='fft')
    offset=int(np.argmax(corr))+start*2
    expected=np.repeat(np.resize(source,(offset+len(actual)+1)//2),2)[offset:offset+len(actual)]
    errors=actual-expected
    result=dict(file=path.name,sha256=sha(path),frames=len(actual),rate=32768,seconds=len(actual)/32768,alignment_output_samples=offset,peak_pcm=int(max(abs(actual))),rms_pcm=float(np.sqrt(np.mean(actual.astype(float)**2))),clipped_samples=int(np.count_nonzero(abs(actual)>=32767)),mismatched_samples=int(np.count_nonzero(errors)),maximum_transport_error=int(max(abs(errors))),source_loops_spanned=len(actual)/(2*len(source)),sample_identical_to_expected=not np.any(errors))
    assert result['sample_identical_to_expected'],result
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba');p.add_argument('--output',type=Path,required=True);p.add_argument('--producer-report',type=Path,required=True);p.add_argument('--producer-sha',required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    assert sha(a.producer_report)==a.producer_sha
    producer=json.loads(a.producer_report.read_text());cases=[];audio=[]
    assert producer['rom_sha256']==sha(a.rom) and producer['symbols_sha256']==sha(a.rom.with_suffix('.sym'))
    assert producer['source_manifest_sha256']==sha(a.rom.parent/'source-hashes.json')
    assert producer['finished_scope']=='full' and not producer['failures'] and producer['controller_only'] and not producer['game_ram_writes'] and not producer['machine_state_loads']
    for slug,key,frames in [('village',None,6360),('dungeon','room61-causeway-first',4920)]:
        fixture=None
        if key:
            item=producer['snapshots'][key];fixture=Path(item['sram_path']);assert fixture.resolve().is_relative_to(a.producer_report.resolve().parent) and sha(fixture)==item['sram_sha256']
        n=Native(a.rom)
        try:
            n.boot(fixture);n.step(180)
            if fixture:
                n.step(2,'START');n.step(120)
                assert n.g('game_state')==3
            assert n.g('music_track')==int(slug=='dungeon')
            approx=n.g('music_source_cursor')-(n.g('music_produced')-n.g('music_consumed'))
            path=a.output/(slug+'-native-two-loops.wav');n.e.audio_start(path)
            n.step(frames);n.e.audio_stop()
            audio.append(analyze_audio(path,slug,approx))
            cases.append(dict(name=slug+'-two-native-loops',frames=frames,max_cycles=max(r['cycles'] for r in n.rows if r['strict']),irq_count=n.g('music_irq_count'),max_irq_lateness_samples=n.g('music_irq_late_max'),loops=n.g('music_loops'),music_faults=n.g('music_faults'),fixture_sha256=sha(fixture) if fixture else None))
            with gzip.open(a.output/(slug+'-frames.jsonl.gz'),'wt') as f:
                for row in n.rows:f.write(json.dumps(row,separators=(',',':'))+'\n')
        finally:n.close()
    result=dict(rom_sha256=sha(a.rom),symbols_sha256=sha(a.rom.with_suffix('.sym')),elf_sha256=sha(a.rom.with_suffix('.elf')),source_manifest_sha256=sha(a.rom.parent/'source-hashes.json'),producer_sha256=a.producer_sha,game_ram_writes=0,cross_rom_machine_states=0,physical_hardware_tested=False,listening_review=False,cases=cases,audio=audio)
    (a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
