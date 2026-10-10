#!/usr/bin/env python3
"""Exact production include/art differential proof, independent of unfinished draw code.

Host synthetic states, not native controller/cadence or acquisition acceptance.
"""
import argparse, hashlib, json, os, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=('tests/check_covenants_geometry.py','src/covenants_geometry.inc','src/covenants_game.c','src/covenants_game.h','src/covenants_art.c','src/covenants_art.h','assets/covenants_world/geometry.json','tests/covenants_geometry_host.c')
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
def extract_function(source,name):
    match=re.search(r'^(?:static )?COLD [^\n]*\b'+re.escape(name)+r'\([^\n]*\)\{',source,re.M)
    assert match,name
    start=source.index('{',match.start());depth=1;end=start+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[match.start():end]+'\n'
def run(args,cwd=ROOT):
    try:return subprocess.check_output(args,cwd=cwd,text=True,stderr=subprocess.STDOUT,env={**os.environ,"ASAN_OPTIONS":"detect_leaks=0","UBSAN_OPTIONS":"halt_on_error=1"})
    except subprocess.CalledProcessError as e:
        print(e.output,flush=True);raise
def main():
    p=argparse.ArgumentParser();p.add_argument('--sanitize',action='store_true');p.add_argument('--arm',action='store_true');p.add_argument('--output',default='build/covenants-geometry-review');args=p.parse_args()
    out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True);before=hashes()
    game=(ROOT/'src/covenants_game.c').read_text()
    functions=extract_function(game,'ab')+extract_function(game,'covenants_game_is_room')
    common='#include "covenants_game.h"\n#include "covenants_art.h"\n'
    common+='#if defined(__arm__)\n#define COLD __attribute__((section(".text.rom"),long_call,noinline))\nextern volatile int room;extern short moving_x;extern unsigned short practice_ticks;extern unsigned geometry;\n#else\n#define COLD\nstatic int room;static short moving_x;static unsigned short practice_ticks;static unsigned geometry;\n#endif\n'
    common+=functions+'#include "covenants_geometry.inc"\n'
    unit=out/'covenants_geometry_extract.inc';unit.write_text(common)
    flags=['-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-Isrc','-I'+str(out)]
    name='sanitized' if args.sanitize else 'strict';exe=out/(name+'-geometry')
    hostflags=['-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie'] if args.sanitize else []
    run(['cc',*flags,*hostflags,'tests/covenants_geometry_host.c','src/covenants_art.c','-o',str(exe)])
    result=json.loads(run([str(exe)]));result.update(whole_room_rectangle_ceiling=16,power_query_rectangle_capacity=48,leak_sanitizer='disabled: ptrace environment; harness allocates no heap',scope='Exact production geometry/art in synthetic states; not native acceptance',source_sha256=before,sanitizers=['address','undefined'] if args.sanitize else [],extracted_helpers_sha256=hashlib.sha256(functions.encode()).hexdigest())
    if args.arm:
        prefix=os.environ.get('ARM_PREFIX',str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-'))
        probe=out/'arm-geometry.c';probe.write_text('#include "covenants_geometry_extract.inc"\n')
        obj=out/'arm-geometry.o'
        armflags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-fstack-usage']
        run([prefix+'gcc',*flags,*armflags,'-c',str(probe),'-o',str(obj)])
        sections=run([prefix+'objdump','-h',str(obj)]);(out/'arm-sections.txt').write_text(sections)
        sizes={n:int(s,16) for n,s in re.findall(r'^\s*\d+\s+(\S+)\s+([0-9a-fA-F]+)\s',sections,re.M)}
        assert sizes['.text']==sizes['.data']==sizes['.bss']==0,sizes
        stack={}
        for line in (out/'arm-geometry.su').read_text().splitlines():
            ident,size,kind=line.split('\t');assert kind=='static';stack[ident.rsplit(':',1)[-1]]=int(size)
        export_stack=sum(stack[n] for n in ('covenants_game_collision_rects','export_occupied','export_rect'))
        assert export_stack<=256,(export_stack,stack)
        result['arm']={'rom_code_bytes':sizes['.text.rom'],'new_iwram_bytes':0,'new_writable_bytes':0,'per_function_stack':stack,'exporter_nested_stack_bytes':export_stack,'compiler':run([prefix+'gcc','--version']).splitlines()[0]}
    assert hashes()==before,'Source changed during proof; rerun against the new source'
    (out/(name+'-report.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
