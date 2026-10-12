#!/usr/bin/env python3
"""Current selected music in actual mGBA: routes, exact loops, PSG and cadence.

Regional's independent transport oracle is reused unchanged. Room/assembly
fixtures are synthetic; controller footage uses a blank cartridge. This suite
verifies native output, not physical hardware or subjective music quality.
"""
import argparse, gzip, hashlib, json, shutil, subprocess, sys, traceback
from pathlib import Path
import numpy as np
from scipy.signal import resample_poly
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
from regional_music_native import Regional, wav_read
from test_save5 import Save
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,value):p.write_text(json.dumps(value,indent=2)+'\n')

class Selected(Regional):
    def __init__(self,args):
        self.a=args;self.rom=args.rom.resolve();self.out=args.output.resolve();self.e=None
        assert not self.out.exists(),'Evidence directory must be fresh'
        assert sha(self.rom)==args.expected_rom_sha,'Unexpected ROM'
        self.manifest=json.loads((ROOT/'assets/music/selected/catalog.json').read_text())
        self.catalog=self.manifest['cues']
        self.sources=[np.frombuffer((ROOT/c['raw_path']).read_bytes(),np.int8).astype(np.int32) for c in self.catalog]
        for c in self.catalog:
            assert sha(ROOT/c['raw_path'])==c['raw_sha256'] and (ROOT/c['raw_path']).stat().st_size==c['sample_count']
        self.pcm=self.sources[0]
        plan=json.loads((ROOT/'assets/music/regional/room-plan.json').read_text())
        self.route=[next(i for i,c in enumerate(self.catalog) if c['id']==r['cue']) for r in plan['rooms']]
        frozen=json.loads((self.rom.parent/'source-hashes.json').read_text())
        actual={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'src').rglob('*') if p.is_file()}
        actual['linker.ld']=sha(ROOT/'linker.ld')
        assert frozen==actual,'Runtime changed after build'
        self.sym={v[2]:int(v[0],16) for line in self.rom.with_suffix('.sym').read_text().splitlines() if len(v:=line.split())==3}
        self.out.mkdir(parents=True)
        self.report={'suite':'selected-music-native','rom_sha256':sha(self.rom),'elf_sha256':sha(self.rom.with_suffix('.elf')),
            'symbols_sha256':sha(self.rom.with_suffix('.sym')),'catalog_sha256':sha(ROOT/'assets/music/selected/catalog.json'),
            'source_provider':self.manifest['source_provider'],'owner_selection':self.manifest['selection'],
            'physical_hardware_tested':False,'controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'sram_imports':0,'cross_rom_states':0,
            'checks':[],'cases':[],'audio':[],'inputs':[],'screenshots':[],'failures':[],
            'limitations':['Native mGBA, not physical hardware.','Exhaustive room, long-loop and assembly fixtures are synthetic, not a full earned campaign.',
                'Controller footage covers the opening/village/river route. Listening approval is the recorded owner instruction, not this test.']}
        self.bridge=self.out/'native-bridge.so';sysroot=args.sysroot.resolve();libdir=sysroot/'usr/lib/x86_64-linux-gnu'
        subprocess.run(['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(ROOT/'tests/player_feedback_mgba_bridge.c'),
            '-I'+str(sysroot/'usr/include'),'-L'+str(libdir),'-Wl,-rpath,'+str(libdir),'-o',str(self.bridge),'-lmgba'],check=True)
        self.report['provenance']={'bridge_sha256':sha(self.bridge),'libmgba_sha256':sha(libdir/'libmgba.so'),
            'harness_sha256':sha(__file__),'source_hashes_sha256':sha(self.rom.parent/'source-hashes.json')}
        for rel in ('tests/selected_music_native.py','tests/regional_music_native.py','tests/lanterns_native.py',
            'tests/player_feedback_native.py','tests/player_feedback_mgba_bridge.c','tools/mgba_bridge.c','tools/mgba_runner.py','tests/test_save5.py'):
            target=self.out/'test-source'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
        self.encoder=None;self.recording=False;self.rgb_hash=None;self.video_frames=0
        self.trace=gzip.open(self.out/'frames.jsonl.gz','wt');self.rows=[];self.case=None;self.assembly_rows=None
        rom=self.rom.read_bytes()
        for c in self.catalog:
            start=self.sym['music_'+c['id'].lower()]-0x08000000
            self.check('Exact cartridge PCM '+c['id'],rom[start:start+c['sample_count']]==(ROOT/c['raw_path']).read_bytes())
        self.check('ROM fits 32 MiB',len(rom)<=33554432)
        self.check('IWRAM below stack reserve',self.sym['__iwram_end']<=0x03007000)
        self.check('EWRAM holds ring and guard',0x02000000<=self.sym['music_ring'] and self.sym['music_ring']+8448<=self.sym['__bss_end']<=0x02040000)
        self.report['rom_bytes']=len(rom)
    def step(self, n, keys=0, measured=True):
        if self.assembly_rows is None:
            return Regional.step(self, n, keys, measured)
        for _ in range(n):
            Regional.step(self, 1, keys, measured)
            self.assembly_rows.append({"hardware_frame": self.e.frame, "active": self.g("horizons_music_active", 1),
                "note": self.g("horizons_music_note", 1), "left": self.g("horizons_music_left", 1),
                "paused": self.g("horizons_music_paused", 1), "frequency_rate": self.e.read(0x0400006c, 2) & 2047,
                "psg2_on": bool(self.e.read(0x04000084, 2) & 2), "bgm_track": self.g("music_track")})

    def fixture(self, name, value, width=4, offset=0):
        self.report["synthetic_fixture"]["writes"].append({"symbol": name, "value": value, "width": width,
            "offset": offset, "hardware_frame": self.e.frame})
        self.native_write(self.e.ptr, self.sym[name] + offset, value, width)
        self.report["game_ram_writes"] += 1

    def assembly(self):
        self.boot("synthetic-assembly-psg")
        self.new_game()
        self.report["controller_only"] = False
        self.report.setdefault("synthetic_fixture", {"purpose": "Explicit audio fixtures, not earned room access", "writes": []})
        for name, value in (("game_state", 1), ("room", 68), ("px", 120), ("py", 112),
                            ("px_q8", 120 * 256), ("py_q8", 112 * 256), ("cx", 134), ("cy", 115),
                            ("cx_q8", 134 * 256), ("cy_q8", 115 * 256), ("face", 1),
                            ("transition_lock", 0), ("arrival_input_mask", 0), ("prev_keys", 0),
                            ("hitstop", 0), ("quickparty_open", 0), ("camera_x", 0), ("camera_y", 0),
                            ("cache_valid", 0)):
            self.fixture(name, value)
        self.fixture("cache_valid", 0, offset=4)
        offset = Save.quests.offset + type(Save().quests).objectives.offset + 57 * 2
        self.fixture("adventure_save", 4, width=2, offset=offset)
        self.step(90)
        self.check("Assembly background selects selected HORIZONS", self.g("music_track") == 21)
        path = self.out / "assembly-native-mix.wav"
        self.e.audio_start(path)
        self.assembly_rows = []
        self.tap("A")
        self.step(15)
        self.check("Controller starts reviewed assembly phrase", self.g("horizons_music_active", 1) == 1)
        self.tap("START")
        held = (self.g("horizons_music_note", 1), self.g("horizons_music_left", 1))
        self.step(45)
        self.check("Pause holds PSG phrase while HORIZONS PCM continues", self.g("game_state") == 3 and
                   held == (self.g("horizons_music_note", 1), self.g("horizons_music_left", 1)) and self.g("music_track") == 21)
        self.tap("START")
        self.step(210)
        self.check("Assembly completes with background intact", self.g("horizons_music_active", 1) == 0 and self.g("music_track") == 21)
        self.e.audio_stop()
        rows = self.assembly_rows
        first = next(index for index, row in enumerate(rows) if row["active"])
        last = next(index for index in range(first + 1, len(rows)) if not rows[index]["active"])
        progressed = []
        for row in rows[first:last]:
            self.check("Assembly note remains in twelve-note table", 0 <= row["note"] < 12)
            progressed.append(sum(self.manifest["assembly"]["lengths"][:row["note"]]) + self.manifest["assembly"]["lengths"][row["note"]] - row["left"])
            if not row["paused"]:
                self.check("Native PSG2 uses reviewed pitch", row["frequency_rate"] == self.manifest["assembly"]["psg_frequency_rates"][row["note"]])
        progressed.append(180)
        self.check("Assembly advances one active tick and completes exactly 180", progressed[0] in (0, 1) and
                   all(after - before in (0, 1) for before, after in zip(progressed, progressed[1:])) and progressed[-1] == 180)
        self.check("All twelve selected assembly notes observed", set(range(12)) <= {row["note"] for row in rows if row["active"]})
        self.check("PSG2 overlaps running selected PCM", any(row["psg2_on"] and row["bgm_track"] == 21 for row in rows))
        write_json(self.out / "assembly-registers.json", {"rows": rows, "mixed_audio_sha256": sha(path)})
        self.report["audio"].append({"file": path.name, "sha256": sha(path), "scope": "Actual selected HORIZONS plus PSG2 native mixed output"})
        self.report["cases"].append({"name": self.case, "observed_notes": 12, "active_ticks": 180})
        self.assembly_rows = None
        self.save_report()

    def finish(self):
        quality=[]
        for path in sorted(self.out.glob('*.wav')):
            pcm,meta=wav_read(path)
            for channel in range(2):
                values=pcm[:,channel].astype(float)/32768
                peak=float(np.max(np.abs(resample_poly(values,4,1))))
                self.check(path.name+' channel '+str(channel)+' has headroom',0<peak<1 and not meta['clipped_samples'])
                quality.append({'file':path.name,'channel':channel,'peak_4x':peak,'clipped_samples':meta['clipped_samples']})
        self.report['native_audio_quality']=quality
        super().finish()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba')
    p.add_argument('--expected-rom-sha',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--sysroot',type=Path,default=ROOT/'tools/sysroot')
    p.add_argument('--cases',default='controllers,synthetic,regional_loops,assembly')
    args=p.parse_args();suite=Selected(args)
    try:
        cases=args.cases.split(',')
        assert set(cases)<=set(('controllers','synthetic','regional_loops','assembly'))
        for name in cases:getattr(suite,name)()
        suite.report['all_audio_cases_run']=set(cases)==set(('controllers','synthetic','regional_loops','assembly'))
        suite.finish()
    except Exception as exc:
        suite.report['result']='FAIL';suite.report['failures'].append({'error':str(exc),'traceback':traceback.format_exc()});suite.save_report()
        if suite.e:suite.e.screenshot(suite.out/'failure.png')
        raise
    finally:suite.close()
if __name__=='__main__':main()
