#!/usr/bin/env python3
"""Southern save capacity, sanitizers and isolated ARM timing.

Host/setup mutations are synthetic fixtures, never native acquisition proof.
The 48-slot case expands equipment definitions only in a temporary C source;
the production authored catalog has31 items; this retained Southern scenario owns25. A separate temporary
codec whitelist enables those synthetic IDs in revision5 only for timing and
round-trip stress. The unmodified codec must reject synthetic records.
"""
import ctypes as C
import hashlib
import json
import os
import re
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

from test_save5 import ROOT, A, B, SIZE, BUSY, DONE, FAILED, Save, Equipment, compare_state, repair_crc

SOURCES=('save4','save5','creatures','creature_data','equipment','equipment_data','southern_quests')
FIXTURE=ROOT/'tests/fixtures/v5-revision3/northern-all21-town.sav'
FIXTURE_SHA='f4e853c85445b8567263a1a875eba967e552e0dcae30958ca42f39bfec4e4479'
EVIDENCE=ROOT/'docs/evidence'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(folder, synthetic=False, codec=False):
    """Generate harness inputs without modifying production files."""
    data=FIXTURE.read_bytes()
    assert hashlib.sha256(data).hexdigest()==FIXTURE_SHA
    header=folder/'southern_n5_fixture.h'
    header.write_text('static const unsigned char southern_n5_fixture[32768]={\n'+
        ',\n'.join(','.join(str(x) for x in data[i:i+64]) for i in range(0,len(data),64))+'\n};\n')
    result={}
    for name in SOURCES:
        path=folder/f'{name}.c'
        path.write_bytes((ROOT/'src'/f'{name}.c').read_bytes())
        result[name]=path
    if synthetic:
        original=result['equipment_data'].read_text()
        marker='const EquipmentDefinition equipment_definitions[EQUIPMENT_DEFINITION_CAPACITY] = {\n'
        assert original.count(marker)==1
        rows=''.join(f'    [{i}] = {{{i}, 1, 0, 0, 255, {{0, 0}}, {{0, 0, 0, 0, 0, 0, 0, 0}}}},\n' for i in range(100,147))
        result['equipment_data']=folder/'synthetic-equipment-data.c'
        result['equipment_data'].write_text(original.replace(marker,marker+rows))
    if codec:
        assert synthetic
        original=result['save5'].read_text()
        marker='static int revision_equipment_allowed(unsigned id) {\n'
        assert original.count(marker)==1
        result['save5']=folder/'synthetic-save5.c'
        original=original.replace(marker,marker+
            '    /* TEST ONLY: synthetic capacity records, never historical content. */\n'
            '    if (scan.revision == 5 && id >= 100 && id <= 146) return equipment_definition(id) != 0;\n')
        # Historical validation now has exact immutable record/category data.
        # Extend ONLY this temporary test source as well; the production policy
        # continues to reject every synthetic ID before any SRAM write.
        marker='static const Save5HistoryItem *history_item(unsigned id, unsigned revision) {\n'
        assert original.count(marker)==1
        rows=','.join('{%d,0,0,0,-1}'%i for i in range(100,147))
        original=original.replace(marker,marker+
            '    static const Save5HistoryItem synthetic_items[47]={'+rows+'};\n'
            '    if (revision == 5 && id >= 100 && id <= 146) return &synthetic_items[id-100];\n')
        result['save5'].write_text(original)
    return result


def configure(lib):
    for name in ('save5_load','save5_store','save5_begin','save5_validate','southern_test_northern','southern_test_full48'):
        getattr(lib,name).argtypes=[C.POINTER(Save)]
        getattr(lib,name).restype=C.c_int
    for name in ('southern_test_ready','southern_test_completed','southern_quest_claim'):
        getattr(lib,name).argtypes=[C.POINTER(Save),C.c_uint]
        getattr(lib,name).restype=C.c_int
    for name in ('equipment_validate',):
        getattr(lib,name).argtypes=[C.POINTER(Equipment)]
    lib.save5_quest_state.argtypes=[C.c_void_p,C.c_uint]
    lib.save5_step.argtypes=[C.c_uint]
    lib.save5_test_fail_after.argtypes=[C.c_int]
    return lib


def host_library(folder,synthetic=False,codec=False):
    folder.mkdir(parents=True,exist_ok=True)
    sources=prepare(folder,synthetic,codec)
    so=folder/'limits.so'
    subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+[
        '-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin',
        '-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-DSOUTHERN_SETUP_ONLY','-shared','-fPIC',
        '-I'+str(ROOT/'src'),'-I'+str(folder),str(ROOT/'tests/southern_save_sanitizer.c'),
        *map(str,sources.values()),'-o',str(so)],check=True)
    lib=configure(C.CDLL(str(so)))
    lib._southern_compiled_hashes={name:sha(path) for name,path in sources.items()}
    return lib


class SouthernSaveLimitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='southern-save-limits-')
        cls.addClassCleanup(cls.tmp.cleanup)
        root=Path(cls.tmp.name)
        cls.evidence=[]
        cls.normal=host_library(root/'normal')
        cls.augmented=host_library(root/'augmented',True)
        cls.synthetic=host_library(root/'synthetic',True,True)

    @classmethod
    def tearDownClass(cls):
        if len(cls.evidence)==4:
            report={'purpose':'Southern full-capacity and atomicity host tests; not native acquisition proof',
                'result':'PASS','fixture_sha256':FIXTURE_SHA,
                'source_sha256':cls.normal._southern_compiled_hashes,
                'compiled_source_sha256_by_variant':{name:getattr(cls,name)._southern_compiled_hashes
                    for name in ('normal','augmented','synthetic')},
                'source_unchanged_during_measurement':cls.normal._southern_compiled_hashes=={
                    name:sha(ROOT/'src'/f'{name}.c') for name in SOURCES},
                'tests_sha256':sha(Path(__file__)),
                'production_catalog_modified':False,'checks':cls.evidence}
            EVIDENCE.mkdir(parents=True,exist_ok=True)
            (EVIDENCE/'magma-revision5-southern-save-limits-host.json').write_text(json.dumps(report,indent=2)+'\n')

    def test_mixed_Q22_full48_inventory_rolls_back_every_byte(self):
        lib=self.augmented;s=Save()
        self.assertEqual(lib.southern_test_northern(C.byref(s)),0)
        self.assertEqual(lib.southern_test_ready(C.byref(s),22),0)
        self.assertEqual(lib.southern_test_full48(C.byref(s)),0)
        self.assertEqual(lib.equipment_catalog_validate(),0)
        self.assertEqual(lib.equipment_validate(C.byref(s.equipment)),1)
        self.assertEqual(lib.save5_validate(C.byref(s)),1)
        ids=[x.item_id for x in s.equipment.bag]
        self.assertEqual(ids,[1,*range(100,147)])
        self.assertEqual(len(set(ids)),48)
        before=bytes(s)
        for _ in range(10):
            self.assertEqual(lib.southern_quest_claim(C.byref(s),22),5)
            self.assertEqual(bytes(s),before)
            self.assertEqual(lib.save5_quest_state(C.byref(s.quests),22),2)
            self.assertFalse(any(x.form_id in (79,80) for x in s.roster.instances))
        # Free one synthetic slot; the exact READY transaction is now retryable.
        C.memset(C.byref(s.equipment.bag[47]),0,C.sizeof(s.equipment.bag[47]))
        self.assertEqual(lib.southern_quest_claim(C.byref(s),22),3)
        self.assertEqual(lib.save5_quest_state(C.byref(s.quests),22),3)
        self.assertEqual(sum(x.form_id==79 for x in s.roster.instances),1)
        self.assertEqual(sum(x.item_id==4 for x in s.equipment.bag),1)
        self.assertEqual(lib.save5_validate(C.byref(s)),1)

        self.evidence.append({'test':'mixed-Q22-full48-atomicity','unique_inventory_records':48,
            'temporary_catalog_ids':[100,146],'runtime_equipment_validate':True,
            'production_catalog_validate':False,'full_retries':10,'result':'SOUTH_FULL',
            'entire_state_byte_identical':True,'quest_remains':'READY','companion_count':0,
            'one_slot_freed_retry':'SOUTH_REWARDED, exactly one companion and item4'})

    def test_real_catalog_full160_all41_forms_all30_quests_all25_items(self):
        lib=self.normal;s=Save();out=Save()
        self.assertEqual(lib.southern_test_completed(C.byref(s),1),0)
        self.assertEqual(lib.equipment_catalog_validate(),1)
        self.assertEqual(sum(bool(x.form_id) for x in s.roster.instances),160)
        self.assertEqual(len(set(x.form_id for x in s.roster.instances)),41)
        self.assertEqual(sum(x.bit_count() for x in s.roster.obtained),41)
        self.assertEqual(sum(bool(x.item_id) for x in s.equipment.bag),25)
        self.assertTrue(all(lib.save5_quest_state(C.byref(s.quests),q)==3 for q in range(30)))
        for budget in (0,1,64,1024,3072,4096):
            self.assertEqual(lib.save5_begin(C.byref(s)),1)
            lib.save5_step(budget)
            self.assertLessEqual(lib.save5_test_step_work(),min(budget,3072))
            while lib.save5_status()==BUSY:lib.save5_step(max(1,budget))
            self.assertEqual(lib.save5_status(),DONE)
            self.assertEqual(lib.save5_load(C.byref(out)),1)
            self.assertEqual(compare_state(out),compare_state(s))

        self.evidence.append({'test':'actual-catalog-full160-roundtrip','roster':160,
            'physical_forms':41,'obtained_forms':41,'claimed_quests':30,'gear':25,
            'budgets':[0,1,64,1024,3072,4096],'effective_cap':3072,'all_roundtrips_match':True})

    def test_synthetic_codec_is_scoped_and_production_stream_rejects_it(self):
        lib=self.synthetic;s=Save();out=Save()
        self.assertEqual(lib.southern_test_completed(C.byref(s),1),0)
        self.assertEqual(lib.southern_test_full48(C.byref(s)),0)
        self.assertEqual(lib.save5_store(C.byref(s)),1)
        self.assertEqual(lib.save5_load(C.byref(out)),1)
        self.assertEqual(compare_state(out),compare_state(s))
        # Production stream validates historical identities independently of runtime catalog.
        real=self.augmented;real_sram=(C.c_ubyte*32768).in_dll(real,'save5_test_sram')
        real.southern_test_northern(C.byref(out));before=bytes(real_sram)
        writes=real.save5_test_write_count()
        self.assertEqual(real.save5_validate(C.byref(s)),1)
        self.assertEqual(real.save5_begin(C.byref(s)),1)
        while real.save5_status()==BUSY:real.save5_step(4096)
        self.assertEqual(real.save5_status(),FAILED)
        self.assertEqual(real.save5_test_write_count(),writes)
        self.assertEqual(bytes(real_sram),before)
        synthetic_sram=(C.c_ubyte*32768).in_dll(lib,'save5_test_sram')
        # Remove both older fallback banks, leaving only the synthetic revision5 image.
        latest=max((A,B),key=lambda off:int.from_bytes(bytes(synthetic_sram[off+8:off+12]),'little'))
        real_sram[:]=bytes([255])*32768
        real_sram[A:A+SIZE]=bytes(synthetic_sram[latest:latest+SIZE])
        before=bytes(out)
        self.assertEqual(real.save5_load(C.byref(out)),0)
        self.assertEqual(bytes(out),before)

        # Isolate historical ID rejection using Northern-only content with no Southern fields.
        historical=Save()
        self.assertEqual(lib.southern_test_northern(C.byref(historical)),0)
        historical.quests.region_flags[2]=0
        self.assertEqual(lib.southern_test_full48(C.byref(historical)),0)
        self.assertEqual(lib.save5_store(C.byref(historical)),1)
        latest=max((A,B),key=lambda off:int.from_bytes(bytes(synthetic_sram[off+8:off+12]),'little'))
        bank=bytearray(synthetic_sram[latest:latest+SIZE]);bank[12:14]=(3).to_bytes(2,'little')
        synthetic_sram[:]=bytes([255])*32768;synthetic_sram[A:A+SIZE]=repair_crc(bank)
        self.assertEqual(lib.save5_load(C.byref(out)),0)
        self.evidence.append({'test':'temporary-synthetic-codec-isolation',
            'revision5_full48_roundtrip':True,'production_stream_rejects_before_write':True,
            'production_load_rejects_synthetic_bank':True,'temporary_codec_rejects_revision3_synthetic_ids':True})

    def test_asan_ubsan_full_completed_state_and_invalid_snapshots(self):
        folder=Path(self.tmp.name)/'sanitizer';folder.mkdir()
        sources=prepare(folder)
        exe=folder/'southern-sanitizer'
        command=shlex.split(os.environ.get('HOST_CC','cc'))+[
            '-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-pedantic',
            '-fsanitize=address,undefined','-fno-omit-frame-pointer',
            '-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(ROOT/'src'),'-I'+str(folder),
            str(ROOT/'tests/southern_save_sanitizer.c'),*map(str,sources.values()),'-o',str(exe)]
        subprocess.run(command,check=True)
        run=subprocess.run([str(exe)],env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
            UBSAN_OPTIONS='halt_on_error=1'),check=False,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+'\n'+run.stderr)
        result=json.loads(run.stdout.strip())
        report={'purpose':'Southern host memory/undefined-behavior and randomized codec stress; not native acquisition proof',
            'fixture_sha256':FIXTURE_SHA,'sanitizers':['address','undefined'],'result':'PASS',
            'source_sha256':{name:sha(path) for name,path in sources.items()},
            'source_unchanged_during_measurement':all(sha(path)==sha(ROOT/'src'/f'{name}.c')
                for name,path in sources.items()),
            'harness_sha256':sha(ROOT/'tests/southern_save_sanitizer.c'),
            'roster':160,'physical_forms':41,'obtained_forms':41,'claimed_quests':30,'authored_gear':25,
            'budget_range':[0,8192],'production_effective_cap':3072,**result}
        EVIDENCE.mkdir(parents=True,exist_ok=True)
        (EVIDENCE/'magma-revision5-southern-save-limits-sanitizers.json').write_text(json.dumps(report,indent=2)+'\n')
        self.evidence.append({'test':'ASan/UBSan',**result,'result':'PASS'})


ARM_TIMING_MAIN=r'''
#include "southern_quests.h"
int southern_test_completed(Save5State *,unsigned);
int southern_test_full48(Save5State *);
#ifndef BENCH_BUDGET
#define BENCH_BUDGET 1024
#endif
#define REG16(a) (*(volatile unsigned short *)(a))
/* Exact freestanding byte-copy behavior from game.c; setup only. */
void *memcpy(void *d,const void *s,unsigned n) {
    unsigned char *a=d;const unsigned char *b=s;while(n--)*a++=*b++;return d;
}
static Save5State state;
volatile unsigned begin_cycles[3],step_cycles[3][256],step_counts[3],results[3],completed,fixture_error;
const char sram_id[]="SRAM_V113";
static unsigned now(void) {
    unsigned hi,lo,hi2;
    do {hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);
    return (hi<<16)|lo;
}
static void bench(unsigned n) {
    unsigned t=now(),i=0;
    results[n]=(unsigned)save5_begin(&state);begin_cycles[n]=now()-t;
    while(save5_status()==SAVE5_BUSY&&i<256) {
        t=now();save5_step(BENCH_BUDGET);step_cycles[n][i++]=now()-t;
    }
    step_counts[n]=i;results[n]=save5_status();
}
int main(void) {
    REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
    REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
    fixture_error=(unsigned)southern_test_completed(&state,1);
#ifdef SYNTHETIC_FULL48
    if(!fixture_error)fixture_error=(unsigned)southern_test_full48(&state);
#endif
    if(!fixture_error){bench(0);bench(1);bench(2);completed=1;}else completed=2;
    while(1) { }
    return 0;
}
'''


def object_sizes(prefix,path):
    raw=subprocess.check_output([prefix+'size',str(path)],text=True)
    values=raw.splitlines()[-1].split()
    return {'text_rom_bytes':int(values[0]),'data_rom_and_ram_bytes':int(values[1]),
        'bss_ram_bytes':int(values[2]),'total_bytes':int(values[3])}


def review_static_call_chains(prefix, out):
    """Conservative direct-call C frame sum, never a runtime high-water claim."""
    frames={};calls={}
    for name in (*SOURCES,'main'):
        for line in (out/f'{name}.su').read_text().splitlines():
            symbol,size,_kind=line.rsplit(':',1)[-1].split('\t')
            frames[symbol]=int(size)
        dump=subprocess.check_output([prefix+'objdump','-dr',str(out/f'{name}.o')],text=True)
        function=None
        for line in dump.splitlines():
            match=re.match(r'^\w+ <([^>]+)>:',line)
            if match:function=match[1];calls.setdefault(function,set())
            match=re.search(r'R_ARM_THM_CALL\s+([^+\s]+)',line)
            if match and function:calls[function].add(match[1])
            match=re.search(r'\bbl\s+[a-f0-9]+\s+<([^+>]+)',line)
            if match and function and match[1]!=function:calls[function].add(match[1])
    # GCC .su omits the numeric suffix of some cloned internal symbols.
    for function in calls:
        original=re.sub(r'\.\d+$','',function)
        if function not in frames and original in frames:frames[function]=frames[original]
    def paths(function,seen=()):
        if function in seen:return []
        child=[path for callee in calls.get(function,()) if callee in frames
            for path in paths(callee,seen+(function,))]
        return [(frames.get(function,0)+n,[function]+route) for n,route in child] if child else [(frames.get(function,0),[function])]
    entries=[]
    for function in ('save5_step','southern_quest_claim'):
        size,path=max(paths(function));reachable=set()
        def visit(fn):
            if fn in reachable:return
            reachable.add(fn)
            for callee in calls.get(fn,()):visit(callee)
        visit(function)
        entries.append({'entry':function,'reviewed_static_c_frame_sum_bytes':size,
            'chain':[{'function':fn,'own_frame_bytes':frames[fn]} for fn in path],
            'unresolved_reachable_callees':sorted(fn for fn in reachable if fn not in frames)})
    return {'method':'ARM O2 .su own-function frames plus objdump direct BL/THM_CALL edges',
        'limitations':'Conservative static direct-call C frame sums, not runtime stack high-water; excludes interrupts, unresolved runtime helpers and indirect calls',
        'entries':entries}


def arm_timing():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--arm-timing',action='store_true')
    parser.add_argument('--output',type=Path,default=EVIDENCE/'southern-save-limits-arm.json')
    parser.add_argument('--mgba-tools',type=Path,default=ROOT/'tools')
    args=parser.parse_args()
    sys.path.insert(0,str(args.mgba_tools.resolve()))
    from mgba_runner import Emulator
    default=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-'
    prefix=os.environ.get('ARM_PREFIX',str(default) if Path(str(default)+'gcc').exists() else 'arm-none-eabi-')
    cc=prefix+'gcc'
    flags=['-I',str(ROOT/'src'),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2',
        '-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer',
        '-Wall','-Wextra','-Werror','-fstack-usage']
    report={'purpose':'Isolated Southern save ARM7TDMI cycle microbenchmark; not native acquisition or whole-frame proof',
        'fixture_sha256':FIXTURE_SHA,'waitcnt':'0x4317','timer_clock_hz':16777216,'frame_cycles':280896,
        'production_effective_cap':3072,'required_max_begin_cycles':70000,
        'required_max_step_cycles':{'1024':70000,'3072':230000,'4096':230000},
        'source_sha256':{name:sha(ROOT/'src'/f'{name}.c') for name in SOURCES},
        'harness_sha256':sha(ROOT/'tests/southern_save_sanitizer.c'),
        'tests_sha256':sha(Path(__file__)),
        'compiler':subprocess.check_output([cc,'--version'],text=True).splitlines()[0],
        'production_source_edits_by_test':False,'variants':[]}
    with tempfile.TemporaryDirectory(prefix='southern-save-arm-') as temp:
        for synthetic in (False,True):
            out=Path(temp)/('synthetic-full48' if synthetic else 'authored-all25');out.mkdir()
            sources=prepare(out,synthetic,synthetic)
            main=out/'main.c';main.write_text(ARM_TIMING_MAIN)
            localflags=flags+['-I',str(out)]
            for name,path in sources.items():
                subprocess.run([cc,*localflags,'-c',str(path),'-o',str(out/f'{name}.o')],check=True)
            subprocess.run([cc,*localflags,'-DSOUTHERN_SETUP_ONLY','-c',str(ROOT/'tests/southern_save_sanitizer.c'),
                '-o',str(out/'setup.o')],check=True)
            subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp',
                '-c',str(ROOT/'src/startup.s'),'-o',str(out/'startup.o')],check=True)
            variant={'scenario':'full160-all41-forms-all30-quests-'+('synthetic48' if synthetic else 'authored25'),
                'synthetic':synthetic,'physical_forms':41,'obtained_forms':41,'roster':160,'quests':30,
                'gear_records':48 if synthetic else 25,'authored_catalog_count':25,
                'temporary_changes':(['equipment definitions 100..146, zero-stat body items',
                    'revision5-only synthetic-ID stream whitelist'] if synthetic else []),
                'compiled_source_sha256':{name:sha(path) for name,path in sources.items()},
                'object_sizes':{name:object_sizes(prefix,out/f'{name}.o') for name in SOURCES},
                'stack_usage':{name:(out/f'{name}.su').read_text() for name in SOURCES},
                'max_static_frame_bytes':{name:max(int(line.split('\t')[1]) for line in
                    (out/f'{name}.su').read_text().splitlines()) if (out/f'{name}.su').read_text().strip() else 0
                    for name in SOURCES},
                'stack_scope':'Compiler static own-function frames, not cumulative call-chain stack high-water',
                'budgets':[]}
            for budget in (1024,3072,4096):
                subprocess.run([cc,*localflags,f'-DBENCH_BUDGET={budget}',
                    *(['-DSYNTHETIC_FULL48'] if synthetic else []),'-c',str(main),'-o',str(out/'main.o')],check=True)
                elf=out/f'timing-{budget}.elf';rom=out/f'timing-{budget}.gba'
                subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib',
                    '-Wl,-T,'+str(ROOT/'linker.ld'),*[str(out/f'{name}.o') for name in ('startup','main','setup',*SOURCES)],
                    '-lgcc','-o',str(elf)],check=True)
                subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True)
                subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,capture_output=True)
                nm=subprocess.check_output([prefix+'nm','-n',str(elf)],text=True)
                symbols={x[2]:int(x[0],16) for line in nm.splitlines() if len(x:=line.split())==3}
                scenarios=[]
                with Emulator(rom) as e:
                    for _ in range(100):
                        e.frames(600)
                        if e.read(symbols['completed']):break
                    assert e.read(symbols['completed'])==1,('ARM harness setup failed',e.read(symbols['fixture_error']))
                    for index,label in enumerate(('after-authentic-N5','mixed-banks','two-current-banks')):
                        count=e.read(symbols['step_counts']+index*4)
                        assert 0<count<256,(budget,label,count)
                        values=[e.read(symbols['step_cycles']+index*1024+j*4) for j in range(count)]
                        begin=e.read(symbols['begin_cycles']+index*4);status=e.read(symbols['results']+index*4)
                        assert status==DONE,(budget,label,status)
                        scenarios.append({'bank_state':label,'begin_cycles':begin,'steps':count,
                            'max_step_cycles':max(values),'step_cycles':values,'status':status})
                max_begin=max(x['begin_cycles'] for x in scenarios);max_step=max(x['max_step_cycles'] for x in scenarios)
                passed=max_begin<70000 and max_step<(70000 if budget==1024 else 230000)
                variant['budgets'].append({'requested_budget':budget,'effective_cap':3072,
                    'max_begin_cycles':max_begin,'max_step_cycles':max_step,'within_cycle_limits':passed,
                    'rom_sha256':sha(rom),'linked_harness_size':object_sizes(prefix,elf),'scenarios':scenarios})
                print(variant['scenario'],'budget',budget,'max begin',max_begin,'max step',max_step,
                      'PASS' if passed else 'OVER LIMIT',flush=True)
            variant['reviewed_static_call_chains']=review_static_call_chains(prefix,out)
            report['variants'].append(variant)
    report['source_unchanged_during_measurement']=report['source_sha256']=={
        name:sha(ROOT/'src'/f'{name}.c') for name in SOURCES}
    report['within_cycle_limits']=all(b['within_cycle_limits'] for v in report['variants'] for b in v['budgets'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('Report:',args.output)
    if not report['within_cycle_limits']:raise SystemExit('Production timing optimization or work-charge change required')


if __name__=='__main__':
    if '--arm-timing' in sys.argv:arm_timing()
    else:unittest.main(verbosity=2)
