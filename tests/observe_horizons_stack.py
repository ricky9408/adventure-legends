#!/usr/bin/env python3
"""Startup-only final-C stack diagnostic with a same-input production control.

Build: python3 tests/observe_horizons_stack.py build --diagnostic build/horizons-stack-c
Run: python3 tests/observe_horizons_stack.py run --diagnostic build/horizons-stack-c \
  --producer-report build/native-horizons-final-c01/full/horizons-journey.json \
  --expected-producer-sha 1d4e000918e7b77bd5f6e2585abff3e7e13c3c703eb4b50a14546e647d6cc45a \
  --source-snapshot 07-all120-cold-reboot-after --scope controls --output build/horizons-stack-c/controls

No production sources/objects are edited. Only diagnostic startup fills reserved
stack bytes, before main. The existing QA bridge cannot write game RAM or load
machine states. All continuing progress uses real controller inputs. Extent of
overwritten canary is NOT true minimum SP; diagnostic timing is not acceptance.
"""
from __future__ import annotations
import argparse
from collections import Counter
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import traceback

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = '4166bdafdba0bf689a8230d6d8d407ae7faf0271925df480b4e3b0aa917f1a91'
ELF_SHA = 'c5648eb363bdcfaf2e9f553d003dd4ca2150f23bb8607d042470ae85ee19dc28'
SYM_SHA = 'e0cd163b6233c850c8c86711aeff39ce2c7f62de3cffab0e9fcf76ebea693d71'
MANIFEST_SHA = 'e4f99d30802a5e6a97f1d5c639ff3f3d8d59ddb2ad4a91d6c61b212b0ed91a54'
CANARY = 0xa55ac33c
RANGES = {'system': (0x03007000,0x03007f00,64),
          'irq': (0x03007f00,0x03007fa0,16),
          'svc': (0x03007fa0,0x03007fe0,16)}


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def byte_sha(b): return hashlib.sha256(b).hexdigest()
def write_json(p, value): Path(p).write_text(json.dumps(value,indent=2)+'\n')
def symbols(p):
    rows=[v for line in Path(p).read_text().splitlines() if len(v:=line.split())==3]
    counts=Counter(v[2] for v in rows)
    return {v[2]:int(v[0],16) for v in rows if counts[v[2]]==1}


def production_identity():
    expected={'build/emberbond.gba':ROM_SHA,'build/emberbond.elf':ELF_SHA,
              'build/emberbond.sym':SYM_SHA,'build/source-hashes.json':MANIFEST_SHA}
    assert all(sha(ROOT/p)==v for p,v in expected.items())
    manifest=json.loads((ROOT/'build/source-hashes.json').read_text())
    assert all(sha(ROOT/p)==v for p,v in manifest.items())
    return expected,manifest


def build(args):
    expected,manifest=production_identity();out=args.diagnostic.resolve()
    out.mkdir(parents=True,exist_ok=False);(out/'build').mkdir();(out/'source/src').mkdir(parents=True)
    prefix=os.environ.get('ARM_PREFIX',str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-'))
    cc=prefix+'gcc'
    make=subprocess.check_output(['make','-pn','ARM_PREFIX='+prefix],cwd=ROOT,text=True)
    line=next(x for x in make.splitlines() if x.startswith('OBJECTS := '))
    objects=line.split(':= ',1)[1].split()
    before={p:sha(ROOT/p) for p in objects}
    original=(ROOT/'src/startup.s').read_text()
    anchor='    ldr sp, =0x03007F00\n'
    assert original.count(anchor)==1
    fill=('    @ Diagnostic only: reserved SYSTEM/IRQ/SVC stacks; BIOS bytes untouched.\n'
          '    ldr r1, =0x03007000\n    ldr r2, =0x03007FE0\n'
          '    ldr r3, =0xA55AC33C\n5:  cmp r1, r2\n'
          '    strlo r3, [r1], #4\n    blo 5b\n')
    for name in manifest:
        dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if name=='src/startup.s':dest.write_text(original.replace(anchor,anchor+fill))
        else:dest.symlink_to(os.path.relpath(ROOT/name,dest.parent))
    diagnostic_manifest={p:sha(out/'source'/p) for p in manifest}
    assert [p for p in manifest if manifest[p]!=diagnostic_manifest[p]]==['src/startup.s']
    write_json(out/'build/source-hashes.json',diagnostic_manifest)
    commands=[];logs=[]
    def run(command,stdout=None):
        commands.append(command)
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,check=True)
        if stdout:Path(stdout).write_text(result.stdout)
        logs.append(result.stdout+result.stderr)
    cpu=['-mcpu=arm7tdmi','-mthumb-interwork']
    run([cc,*cpu,'-marm','-g','-x','assembler-with-cpp','-c',str(out/'source/src/startup.s'),'-o',str(out/'build/startup.o')])
    # A second link with the unchanged production objects proves these exact
    # inputs reproduce the frozen cartridge before substituting startup.o.
    for label in ('control','diagnostic'):
        target=out/'build'/label
        linked=[str(out/'build/startup.o') if label=='diagnostic' and p=='build/startup.o' else p for p in objects]
        run([cc,*cpu,'-mthumb','-nostdlib','-Wl,-T,linker.ld,-Map,'+str(target.with_suffix('.map')),*linked,'-lgcc','-o',str(target.with_suffix('.elf'))])
        run([prefix+'objcopy','-O','binary',str(target.with_suffix('.elf')),str(target.with_suffix('.gba'))])
        run(['python3','tools/fix_header.py',str(target.with_suffix('.gba'))])
        run([prefix+'nm','-n',str(target.with_suffix('.elf'))],target.with_suffix('.sym'))
    assert sha(out/'build/control.gba')==ROM_SHA
    assert sha(out/'build/control.elf')==ELF_SHA
    assert sha(out/'build/control.sym')==SYM_SHA
    assert all(sha(ROOT/p)==h for p,h in before.items());production_identity()
    libgcc=Path(subprocess.check_output([cc,*cpu,'-mthumb','-print-libgcc-file-name'],text=True).strip())
    receipt={'production':expected,'runtime_source_changes':['src/startup.s'],
             'production_object_sha256':before,'diagnostic_startup_object_sha256':sha(out/'build/startup.o'),
             'diagnostic':{s:sha(out/'build'/('diagnostic.'+s)) for s in ('gba','elf','sym','map')},
             'diagnostic_manifest_sha256':sha(out/'build/source-hashes.json'),
             'control_relink_exact':True,'control':{s:sha(out/'build'/('control.'+s)) for s in ('gba','elf','sym','map')},
             'compiler':subprocess.check_output([cc,'--version'],text=True).splitlines()[0],
             'compiler_sha256':sha(cc),'libgcc_path':str(libgcc),'libgcc_sha256':sha(libgcc),
             'linker_sha256':sha(ROOT/'linker.ld'),'commands':commands,
             'canary_word':hex(CANARY),'filled_range':['0x03007000','0x03007fe0'],
             'bios_vector_range_untouched':['0x03007fe0','0x03008000'],
             'source_overlay':'Unchanged runtime files are read-only-used symlinks to verified production sources; only startup.s is a separate file.',
             'observer_script_sha256':sha(__file__)}
    write_json(out/'build-receipt.json',receipt);(out/'build.log').write_text('\n'.join(logs))
    print(json.dumps({'diagnostic':receipt['diagnostic'],'control_relink_exact':True}),flush=True)


def run(args):
    # Imports are deferred so the build recipe needs only Python and ARM tools.
    from horizons_journey import HorizonsJourney, HorizonsEmulator, H_PRODUCERS, PLAY, PAUSE
    from magma_journey import MagmaJourney
    from northern_journey import newest_bank
    from test_save5 import Save
    diagnostic=args.diagnostic.resolve();receipt=json.loads((diagnostic/'build-receipt.json').read_text())
    production_identity()
    assert receipt['runtime_source_changes']==['src/startup.s'] and receipt['control_relink_exact']
    assert all(sha(ROOT/p)==h for p,h in receipt['production_object_sha256'].items())
    assert all(sha(diagnostic/'build'/('diagnostic.'+s))==h for s,h in receipt['diagnostic'].items())
    producer=args.producer_report.resolve();assert sha(producer)==args.expected_producer_sha
    data=json.loads(producer.read_text());saved=data['snapshots'][args.source_snapshot]
    assert data['rom_sha256']==ROM_SHA and data['elf_sha256']==ELF_SHA and data['symbols_sha256']==SYM_SHA
    assert data['source_manifest_sha256']==MANIFEST_SHA and data['timing_mode']=='strict'
    assert data['controller_only'] and not data['game_ram_writes'] and not data['machine_state_loads']
    assert not data['failures'] and all(c['passed'] for c in data['checks'])
    assert data['global_native']['closed'] and not data['global_native']['exceptions']
    fixture=producer.parent/Path(saved['sram_path']).name
    assert sha(fixture)==saved['sram_sha256'];assert saved['rom_sha256']==ROM_SHA
    # The ancestor is used only to initialize the unmodified navigator. Neither
    # emulator executes frames before both are cold-reset with the final-C save.
    ancestry=args.ancestral_producer.resolve();ancestral=json.loads(ancestry.read_text())
    ancestry_sha=sha(ancestry);assert ancestry_sha in H_PRODUCERS
    ancestral_snapshot=next(iter(H_PRODUCERS[ancestry_sha]))
    ancestor_fixture=ancestry.parent/'source-earned.sav'
    if not ancestor_fixture.exists():ancestor_fixture=Path(ancestral['snapshots'][ancestral_snapshot]['sram_path'])

    class StackJourney(HorizonsJourney):
        def __init__(self):
            self.stack_rows=[];self.paired_rows=[];self.control=None;self.boot_epoch=1
            rom=diagnostic/'build/diagnostic.gba';manifest=diagnostic/'build/source-hashes.json'
            super().__init__(rom,rom.with_suffix('.sym'),args.output,sha(rom),sha(rom.with_suffix('.sym')),sha(rom.with_suffix('.elf')),
                manifest,sha(manifest),source_root=diagnostic/'source',timing_mode='stack-diagnostic-no-release-timing',
                producer=ancestry,producer_sha=ancestry_sha,source_snapshot=ancestral_snapshot,fixture=ancestor_fixture)
            self.close_global_trace();self.global_enabled=False
            self.global_native.update(enabled=False,diagnostic_only=True,timing_is_release_acceptance_evidence=False)
            self.fixture=fixture;self.source_bytes=fixture.read_bytes();self.source_bank=newest_bank(self.source_bytes)
            self.prior_count=len(saved['individuals']);self.prior_history=len(saved['obtained_form_ids']);self.minimal=False
            self.same_candidate_source=True
            self.provenance={'fixture_path':str(fixture),'sram_sha256':sha(fixture),'source_rom_sha256':ROM_SHA,
                'producer_report':str(producer),'producer_sha256':sha(producer),'source_snapshot':args.source_snapshot,
                'source_individuals':self.prior_count,'source_history':self.prior_history,
                'cross_rom_machine_state_loaded':False,'cross_rom_sram_diagnostic':True}
            self.e.close();self.e=HorizonsEmulator(self.rom);self.e.load_save(fixture);self.e.reset()
            self.control=HorizonsEmulator(diagnostic/'build/control.gba');self.control.load_save(fixture);self.control.reset()
            self.control_symbols=symbols(diagnostic/'build/control.sym')

        def step(self,n,keys=0):
            if self.control is not None:self.control.frames(n,keys)
            return MagmaJourney.step(self,n,keys)

        def measured(self,name,callback,cold_continue=False,strict=True):
            result=callback();self.observe(name)
            if cold_continue:self.check(self.get('game_state')==PLAY and not self.get('save_failed'),name+' reaches live play')
            return result

        def snapshot(self,name,settle=True):
            result=super().snapshot(name,settle);self.observe(name);return result

        def observe(self,label):
            ranges={}
            for name,(bottom,top,guard) in RANGES.items():
                words=struct.unpack('<'+'I'*((top-bottom)//4),self.e.bytes(bottom,top-bottom))
                changed=[i for i,v in enumerate(words) if v!=CANARY]
                lowest=bottom+4*min(changed) if changed else top
                ranges[name]={'range':[hex(bottom),hex(top)],'reserved_bytes':top-bottom,
                    'lowest_overwritten_word':hex(lowest),'overwritten_extent_bytes':top-lowest,
                    'changed_word_bytes':4*len(changed),'unmodified_prefix_bytes':lowest-bottom,
                    'bottom_guard_bytes':guard,'bottom_guard_intact':all(v==CANARY for v in words[:guard//4]),
                    'true_minimum_sp':'not measured'}
                self.check(ranges[name]['bottom_guard_intact'],name+' sampled bottom guard remains intact')
            fields=('frame','game_state','room','px','py','hp','journal_tab','save_failed','horizons_power_kind','horizons_power_time')
            actual={n:self.get(n) for n in fields};control={n:self.control.read(self.control_symbols[n]) for n in fields}
            state=self.e.bytes(self.sym['adventure_save'],C.sizeof(Save));control_state=self.control.bytes(self.control_symbols['adventure_save'],C.sizeof(Save))
            sram=self.e.bytes(0x0e000000,32768);control_sram=self.control.bytes(0x0e000000,32768)
            paired={'label':label,'hardware_frame':self.e.frame,'control_hardware_frame':self.control.frame,
                    'fields':actual,'control_fields':control,'fields_equal':actual==control,
                    'adventure_save_sha256':byte_sha(state),'control_adventure_save_sha256':byte_sha(control_state),
                    'adventure_save_equal':state==control_state,'sram_sha256':byte_sha(sram),
                    'control_sram_sha256':byte_sha(control_sram),'sram_equal':sram==control_sram}
            self.paired_rows.append(paired)
            self.stack_rows.append({'label':label,'boot_epoch':self.boot_epoch,'hardware_frame':self.e.frame,
                'status':self.status(),'retained_individuals':len(self.live()),'obtained_histories':len(self.collection()),'stacks':ranges})
            self.stack_report()
            print(json.dumps({'label':label,'frame':self.e.frame,'extent':{k:v['overwritten_extent_bytes'] for k,v in ranges.items()},
                              'paired_equal':all(paired[k] for k in ('fields_equal','adventure_save_equal','sram_equal'))}),flush=True)

        def stack_report(self):
            write_json(self.out/'stack-observations.json',{'suite':'horizons-c-startup-only-stack-canary',
                'finished_scope':self.finished_scope,'controller_only':True,'game_ram_writes':0,'machine_state_loads':0,
                'production_pairing':receipt,'build_receipt_sha256':sha(diagnostic/'build-receipt.json'),
                'observer_script_sha256':sha(__file__),'source_sram':self.provenance,'observations':self.stack_rows,
                'paired_production':self.paired_rows,'diagnostic_timing_is_release_evidence':False,'physical_hardware_tested':False,
                'limitations':['Overwritten extent is not true minimum SP: allocated unwritten slots and writes equal to the canary are invisible.',
                    'Finite controller routes on native mGBA do not prove exhaustive stack bounds or physical hardware safety.',
                    'Relocated code and startup instrumentation invalidate diagnostic timing as release evidence.',
                    'Paired control compares selected pointer-free gameplay fields, full adventure_save bytes and cartridge SRAM; it does not compare whole machine state.',
                    'Each stack observation is cumulative within one cold boot. BIOS/vector area 0x03007fe0..0x03008000 is neither filled nor claimed.',
                    'Authentic retained roster count is recorded; no synthetic capacity roster is fabricated.']})

        def wait_evolution(self,target_state=7,require_ready=True,max_frames=180):
            pairing=self.evolution_observer();trace=[]
            for _ in range(max_frames+1):
                state=self.get('game_state');phase=self.e.read(pairing['address']+8)
                if state==target_state and phase==0:break
                self.check(state==7 and 1<=phase<=5,'diagnostic observes actual evolution preparation/commit')
                self.step(1);trace.append({'frame':self.e.frame,'state':self.get('game_state'),'phase':self.e.read(pairing['address']+8)})
            self.check(self.get('game_state')==target_state and self.e.read(pairing['address']+8)==0,'actual evolution reaches requested state')
            if require_ready and target_state==7:self.check(self.get('progression_evolution_reason')==0,'earned evolution is ready')
            self.cases.append({'actual_evolution_target_state':target_state,'trace':trace,'diagnostic_only':True})
            self.observe('actual-evolution-boundary-'+str(target_state))

        def boot(self):
            self.step(150);self.observe('cold-title')
            self.measured('cold-authentic-c-continue',lambda:(self.tap('START',2,90),self.settle()),cold_continue=True)
            self.check(newest_bank(self.e.bytes(0x0e000000,32768))[32:]==self.source_bank[32:],'cold Continue retains exact producer durable payload')
            self.check(len(self.live())==self.prior_count and len(self.collection())==self.prior_history,'cold Continue retains authenticated counts')
            self.old_ids={c.instance_id for c in self.live()};self.old_history=self.collection();self.old_equipped=bytes(self.state().equipment.equipped)
            self.snapshot('cold-authentic-c-continued')

        def menus(self):
            for tab in range(12):
                self.open_tab(tab);self.tap('DOWN',2,4);self.tap('UP',2,4);self.observe('journal-tab-'+str(tab));self.close_menu()

    r=StackJourney()
    try:
        r.boot()
        if args.scope=='entry':r.initialize_horizons()
        elif args.scope=='evolution':
            identity,slot=r.begin_horizons_trial(0);r.solve_horizons_trial(0)
            r.snapshot('genuine-personal-trial0-earned');r.evolve_horizons(105,106,identity,slot)
        elif args.scope=='controls':r.menus();r.controls()
        elif args.scope=='roster':r.menus();r.travel(62);r.target(72,256)
        r.snapshot('finished-'+args.scope)
        r.finished_scope=args.scope;r.verify_closures()
        production_identity();assert all(sha(ROOT/p)==h for p,h in receipt['production_object_sha256'].items())
        r.check(all(row[k] for row in r.paired_rows for k in ('fields_equal','adventure_save_equal','sram_equal')),'every sampled paired control matches gameplay state and SRAM')
    except Exception as exc:
        r.failures.append({'error':str(exc),'traceback':traceback.format_exc(),'status':r.status()});raise
    finally:
        r.report();r.stack_report();r.e.close()
        if r.control:r.control.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('build','run'))
    parser.add_argument('--diagnostic',type=Path,required=True);parser.add_argument('--output',type=Path)
    parser.add_argument('--producer-report',type=Path);parser.add_argument('--expected-producer-sha')
    parser.add_argument('--source-snapshot');parser.add_argument('--scope',choices=('controls','evolution','entry','roster'))
    parser.add_argument('--ancestral-producer',type=Path,default=ROOT/'build/native-horizons-final-c01/full/source-producer.json')
    args=parser.parse_args()
    if args.action=='build':build(args)
    else:
        assert all((args.output,args.producer_report,args.expected_producer_sha,args.source_snapshot,args.scope))
        run(args)
if __name__=='__main__':main()
