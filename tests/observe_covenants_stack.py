#!/usr/bin/env python3
"""Qualified startup-canary observation paired with an exact production relink.

Replays only passing genuine controller input logs. Host game-RAM writes and
machine-state APIs are unavailable. Diagnostic startup alone fills reserved
SYSTEM/IRQ/SVC stack bytes before main. Canary extent is not true minimum SP;
neither diagnostic cycles nor its ROM count as production timing acceptance.
"""
from __future__ import annotations
import argparse
from collections import Counter
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from run_covenants_native import frozen_copy
CANARY=0xA55AC33C
RANGES={'system':(0x03007000,0x03007F00,64),'irq':(0x03007F00,0x03007FA0,16),'svc':(0x03007FA0,0x03007FE0,16)}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hash_bytes(b):return hashlib.sha256(b).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def symbols(p):
    rows=[v for line in Path(p).read_text().splitlines() if len(v:=line.split())==3]
    counts=Counter(v[2] for v in rows)
    return {v[2]:int(v[0],16) for v in rows if counts[v[2]]==1}

def build(a):
    frozen=a.frozen_root.resolve();out=a.diagnostic.resolve();out.mkdir(parents=True,exist_ok=False)
    pins=json.loads((frozen/'run-status.json').read_text())['candidate']
    assert all(sha(frozen/'candidate'/name)==h for name,h in pins.items())
    manifest=json.loads((frozen/'candidate/source-hashes.json').read_text())
    assert all(sha(frozen/'runtime-source'/name)==h for name,h in manifest.items())
    build_root=a.build_root.resolve();makefile=ROOT/'Makefile'
    line=re.search(r'^OBJECTS := (.+)$',makefile.read_text(),re.M).group(1)
    objects=[build_root/Path(word.replace('$(BUILD)','build')).name for word in line.split()]
    before={str(p):sha(p) for p in objects};copied=[]
    for p in objects:
        dst=out/'objects'/p.name;frozen_copy(p,dst);copied.append(dst)
    for name in manifest:frozen_copy(frozen/'runtime-source'/name,out/'source'/name)
    original=(out/'source/src/startup.s').read_text();anchor='    ldr sp, =0x03007F00\n'
    assert original.count(anchor)==1
    fill=('    @ Diagnostic startup only; reserved stacks, no BIOS vector bytes.\n'
          '    ldr r1, =0x03007000\n    ldr r2, =0x03007FE0\n'
          '    ldr r3, =0xA55AC33C\n5:  cmp r1, r2\n'
          '    strlo r3, [r1], #4\n    blo 5b\n')
    # Break the immutable CAS link before writing the diagnostic variant.
    startup=out/'source/src/startup.s';startup.unlink();startup.write_text(original.replace(anchor,anchor+fill))
    diagnostic_manifest={name:sha(out/'source'/name) for name in manifest}
    assert [name for name in manifest if manifest[name]!=diagnostic_manifest[name]]==['src/startup.s']
    write(out/'diagnostic-source-hashes.json',diagnostic_manifest)
    frozen_copy(makefile,out/'build-inputs/Makefile');frozen_copy(ROOT/'tools/fix_header.py',out/'build-inputs/fix_header.py')
    prefix=os.environ.get('ARM_PREFIX',str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-'))
    cc=prefix+'gcc';cpu=['-mcpu=arm7tdmi','-mthumb-interwork'];commands=[];logs=[]
    def call(command,stdout=None):
        commands.append(list(map(str,command)))
        result=subprocess.run(commands[-1],cwd=ROOT,text=True,capture_output=True,check=True)
        if stdout:Path(stdout).write_text(result.stdout)
        logs.append(result.stdout+result.stderr)
    (out/'roms').mkdir()
    call([cc,*cpu,'-marm','-g','-x','assembler-with-cpp','-c',startup,'-o',out/'objects/diagnostic-startup.o'])
    for label in ('control','diagnostic'):
        target=out/'roms'/label
        linked=[out/'objects/diagnostic-startup.o' if label=='diagnostic' and p.name=='startup.o' else p for p in copied]
        call([cc,*cpu,'-mthumb','-nostdlib','-Wl,-T,'+str(out/'source/linker.ld')+',-Map,'+str(target.with_suffix('.map')),*linked,'-lgcc','-o',target.with_suffix('.elf')])
        call([prefix+'objcopy','-O','binary',target.with_suffix('.elf'),target.with_suffix('.gba')])
        call([sys.executable,out/'build-inputs/fix_header.py',target.with_suffix('.gba')])
        call([prefix+'nm','-n',target.with_suffix('.elf')],target.with_suffix('.sym'))
    for suffix in ('gba','elf','sym'):assert sha(out/'roms'/('control.'+suffix))==pins['emberbond.'+suffix],('control relink differs',suffix)
    assert all(sha(p)==h for p,h in before.items()),'Final production objects changed during diagnostic link'
    libgcc=Path(subprocess.check_output([cc,*cpu,'-mthumb','-print-libgcc-file-name'],text=True).strip())
    receipt={'suite':'covenants-startup-stack-build','production':pins,'frozen_root':str(frozen),
      'control_relink_byte_identical':True,'runtime_source_changes':['src/startup.s'],
      'source_manifest_sha256':pins['source-hashes.json'],'diagnostic_manifest_sha256':sha(out/'diagnostic-source-hashes.json'),
      'production_object_sha256':before,'frozen_object_sha256':{str(p.relative_to(out)):sha(p) for p in copied},
      'roms':{label:{s:sha(out/'roms'/(label+'.'+s)) for s in ('gba','elf','sym','map')} for label in ('control','diagnostic')},
      'compiler':subprocess.check_output([cc,'--version'],text=True).splitlines()[0],
      'compiler_sha256':sha(cc),'libgcc_sha256':sha(libgcc),'commands':commands,
      'canary_word':hex(CANARY),'filled_range':['0x03007000','0x03007fe0'],
      'bios_vectors_untouched':['0x03007fe0','0x03008000'],'observer_sha256':sha(__file__)}
    write(out/'build-receipt.json',receipt);(out/'build.log').write_text('\n'.join(logs))
    print('Byte-identical control and separate startup-only stack ROM built',flush=True)

def run(a):
    from horizons_journey import HorizonsEmulator
    from test_save5 import Save
    from return_native_dependencies import resolve_mgba
    diag=a.diagnostic.resolve();receipt=json.loads((diag/'build-receipt.json').read_text());pins=receipt['production']
    assert receipt['control_relink_byte_identical'] and receipt['runtime_source_changes']==['src/startup.s']
    assert all(sha(diag/'roms'/(label+'.'+s))==h for label,parts in receipt['roms'].items() for s,h in parts.items())
    producer=a.producer_report.resolve();assert sha(producer)==a.expected_producer_sha
    p=json.loads(producer.read_text())
    assert p['suite'] in ('covenants-native-controller-journey','covenants-core-prelude')
    assert p['finished_scope'] in ('full','controls','core-ending')
    assert p['controller_only'] and p['game_ram_writes']==p['machine_state_loads']==0
    assert p['timing_mode']=='strict' and not p['failures'] and all(c['passed'] for c in p['checks'])
    assert p['global_native']['closed'] and not p['global_native']['exceptions']
    for key,file in (('rom_sha256','emberbond.gba'),('elf_sha256','emberbond.elf'),('symbols_sha256','emberbond.sym'),('source_manifest_sha256','source-hashes.json')):assert p[key]==pins[file]
    fixture=producer.parent/'source-earned.sav';assert sha(fixture)==p['provenance']['sram_sha256']
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);(out/'sram').mkdir()
    frozen_copy(producer,out/'producer-report.json');frozen_copy(fixture,out/'source-earned.sav')
    helper_hashes={}
    for module in tuple(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name and Path(name).is_file() and Path(name).resolve().is_relative_to(ROOT):
            source=Path(name).resolve();relative=source.relative_to(ROOT);dest=out/'helper-source'/relative;frozen_copy(source,dest);helper_hashes[str(relative)]=sha(dest)
    for name in ('tools/horizons_mgba_bridge.c','tools/horizons_mgba_bridge.so','tools/horizons_mgba_bridge.build.json'):
        frozen_copy(ROOT/name,out/'helper-source'/name);helper_hashes[name]=sha(out/'helper-source'/name)
    library,soname,discovery=resolve_mgba(ROOT/'tools/horizons_mgba_bridge.so',os.environ.get('HORIZONS_MGBA_LIBRARY'))
    frozen_copy(library,out/'helper-source/tools/emulator-libs'/Path(soname).name)
    helper_hashes['tools/emulator-libs/'+Path(soname).name]=sha(library)
    write(out/'helper-hashes.json',helper_hashes)
    (out/'emulator-dependency.txt').write_text(discovery)
    syms={label:symbols(diag/'roms'/(label+'.sym')) for label in ('control','diagnostic')}
    emus={};epoch=1;observations=[];resets=[];failures=[];total=0;last_sample=-999
    result={'suite':'covenants-qualified-native-stack-replay','finished':False,'controller_only':True,
      'host_game_ram_writes':0,'machine_state_loads':0,'diagnostic_startup_canary_writes':True,
      'diagnostic_timing_is_release_evidence':False,'physical_hardware_tested':False,
      'build_receipt_sha256':sha(diag/'build-receipt.json'),'producer_sha256':sha(producer),
      'production':pins,'producer_scope':p['finished_scope'],'source_sram_sha256':sha(fixture),
      'observations':observations,'resets':resets,'failures':failures,
      'limitations':['Overwritten canary extent is not true minimum SP; unwritten allocated slots or writes equal to the canary are invisible.',
       'Finite replay coverage is not an exhaustive stack bound or physical-hardware proof.',
       'Only reserved SYSTEM/IRQ/SVC stacks are filled before main; BIOS vector bytes remain untouched.',
       'Pairing compares pointer-free gameplay fields, complete adventure_save bytes and ordinary native SRAM, not whole machine state.',
       'Startup instrumentation and code relocation cannot establish production timing acceptance.']}
    fields=('frame','game_state','room','px','py','hp','chapter_flags','checkpoint_spawn','journal_tab','save_failed','summoned','ability_cd','covenants_power_kind','covenants_power_time','covenants_power_age')
    def record():write(out/'stack-observations.json',result)
    def open_pair(paths):
        for label in ('control','diagnostic'):
            e=HorizonsEmulator(diag/'roms'/(label+'.gba'));e.load_save(paths[label]);e.reset();emus[label]=e
    def values(label):return {n:emus[label].read(syms[label][n]) for n in fields}
    def words(e,address,n):return b''.join(struct.pack('<I',e.read(address+i,4)) for i in range(0,n,4))
    def observe(label):
        nonlocal last_sample
        ranges={};e=emus['diagnostic']
        for name,(bottom,top,guard) in RANGES.items():
            raw=words(e,bottom,top-bottom);values32=struct.unpack('<'+'I'*((top-bottom)//4),raw)
            changed=[i for i,v in enumerate(values32) if v!=CANARY];lowest=bottom+4*min(changed) if changed else top
            ranges[name]={'range':[hex(bottom),hex(top)],'reserved_bytes':top-bottom,'lowest_overwritten_word':hex(lowest),
              'overwritten_extent_bytes':top-lowest,'changed_word_bytes':4*len(changed),'unmodified_prefix_bytes':lowest-bottom,
              'bottom_guard_bytes':guard,'bottom_guard_intact':all(v==CANARY for v in values32[:guard//4]),'true_minimum_sp':'not measured'}
        state={tag:words(e,syms[tag]['adventure_save'],C.sizeof(Save)) for tag,e in emus.items()}
        blobs={};paths={}
        for tag,e in emus.items():
            path=out/'sram'/('%04d-%s.sav'%(len(observations),tag));e.save(path);paths[tag]=str(path);blobs[tag]=path.read_bytes();assert len(blobs[tag])==32768
        paired={'fields':values('control'),'diagnostic_fields':values('diagnostic'),
          'adventure_save_sha256':{k:hash_bytes(v) for k,v in state.items()},'sram_sha256':{k:hash_bytes(v) for k,v in blobs.items()},'sram_paths':paths}
        paired['fields_equal']=paired['fields']==paired['diagnostic_fields'];paired['adventure_save_equal']=state['control']==state['diagnostic'];paired['sram_equal']=blobs['control']==blobs['diagnostic']
        row={'label':label,'boot_epoch':epoch,'total_hardware_frames':total,'hardware_frame':e.frame,'stacks':ranges,'paired':paired};observations.append(row);last_sample=total;record()
        assert all(r['bottom_guard_intact'] for r in ranges.values()),'A sampled reserved stack bottom guard was overwritten'
        assert paired['fields_equal'] and paired['adventure_save_equal'] and paired['sram_equal'],'Paired production/diagnostic gameplay or SRAM diverged'
        return paths
    try:
        open_pair({tag:fixture for tag in ('control','diagnostic')})
        for index,row in enumerate(p['inputs']):
            count=row['frames'];assert count==row.get('requested_frames',count)
            if row['frame']==0 and emus['control'].frame:
                paths=observe('before-ordinary-cold-reset-'+str(epoch));resets.append({'after_input':index-1,'source_sram':paths,'epoch':epoch})
                for e in emus.values():e.close()
                epoch+=1;open_pair(paths)
            assert all(e.frame==row['frame'] for e in emus.values()),('input frame discontinuity',index,row)
            for e in emus.values():e.frames(count,row['keys'])
            total+=count
            control,diagnostic=values('control'),values('diagnostic')
            # Cold startup/Continue may be between instructions. Compare only
            # settled nonzero-frame gameplay, then every ordinary input batch.
            active=control['frame'] and diagnostic['frame'] and control['game_state']!=0 and diagnostic['game_state']!=0
            if active:
                assert control==diagnostic,('paired fields differ after input batch',index,control,diagnostic)
                if total-last_sample>=a.sample_frames:observe('input-'+str(index))
        paths=observe('finished-'+p['finished_scope'])
        final_snapshot=a.final_snapshot or list(p['snapshots'])[-1]
        expected=p['snapshots'][final_snapshot]['sram_sha256']
        assert all(sha(path)==expected for path in paths.values()),'Replay final native SRAM differs from genuine producer snapshot'
        result.update(finished=True,all_sampled_bottom_guards_intact=True,paired_samples_equal=True,final_sram_matches_producer=True,
          input_batches=len(p['inputs']),hardware_frames_per_rom=total,cold_boots=epoch,
          maximum_overwritten_extent={name:max(row['stacks'][name]['overwritten_extent_bytes'] for row in observations) for name in RANGES})
        assert all(sha(out/'helper-source'/name)==h for name,h in helper_hashes.items())
    except Exception as exc:
        failures.append({'error':str(exc),'traceback':traceback.format_exc(),'hardware_frames':total,'boot_epoch':epoch});raise
    finally:
        record()
        for e in emus.values():e.close()
    print(json.dumps({'scope':p['finished_scope'],'extent':result['maximum_overwritten_extent'],'paired_samples':len(observations),'boots':epoch}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    b=sub.add_parser('build');b.add_argument('--frozen-root',type=Path,required=True);b.add_argument('--diagnostic',type=Path,required=True);b.add_argument('--build-root',type=Path,default=ROOT/'build')
    r=sub.add_parser('run');r.add_argument('--diagnostic',type=Path,required=True);r.add_argument('--producer-report',type=Path,required=True);r.add_argument('--expected-producer-sha',required=True);r.add_argument('--output',type=Path,required=True);r.add_argument('--final-snapshot');r.add_argument('--sample-frames',type=int,default=120)
    args=parser.parse_args();build(args) if args.action=='build' else run(args)
