#!/usr/bin/env python3
"""Exact differential proof against the unmodified archived candidate-J Magma.

The production geometry is never adapted in the oracle. Only read-only test
accessors are appended. Every integer point in each frame's complete raw-path
bounding rectangle (expanded by the largest path radius and one more pixel) is
compared using its exact per-path hit bitmask, without sampling or digest-only
comparison. Endpoints, clipping flags, active masks, and full OBJ draw calls are
also compared byte-for-byte across complete casts and collision invalidations.
This is synthetic host evidence, not native/controller acceptance evidence.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/magma-geometry-equivalence'
FROZEN = ROOT / 'tests/fixtures/magma_powers_candidate_j.c'
PIN = '65764bcc3c056e6b55a8b69559637109dd47927e76a38e78e677603d0e3ca3a5'
SOURCES = [
    'tests/legacy_underwater_hooks.c', 'src/magma_power_art.c',
    'src/southern_powers.c', 'src/southern_power_art.c',
    'src/northern_powers.c', 'src/northern_power_art.c',
    'src/advanced_powers.c', 'src/regional_powers.c', 'src/gear_runtime.c', 'tests/legacy_return_hooks.c',
    'src/weapon_actions.c', 'src/combat_rules.c', 'src/equipment.c',
    'src/equipment_data.c', 'src/creatures.c', 'src/creature_data.c', 'src/assets.c',
]

WRAPPER = r'''
/* Read-only test accessors: the source above is byte-for-byte frozen. */
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
void emit_int(int value);
void emit_byte(unsigned value);
static uint64_t oracle_points,oracle_paths,oracle_clipped,oracle_five_ray_frames;
static void oracle_path(const Path *p){
 emit_int(p->x);emit_int(p->y);emit_int(p->tx);emit_int(p->ty);
 emit_int(p->ex);emit_int(p->ey);emit_int(p->valid);emit_int(p->open);
 emit_int(p->whole);emit_int(p->radius);emit_int(p->parent);emit_int(p->group);
 emit_int(p->from);emit_int(p->to);
}
void oracle_frame(void){
 unsigned i,mask=geometry();int x,y,x0=1024,y0=1024,x1=-1,y1=-1,r=0;
 emit_int(magma_power_kind);emit_int(magma_power_age);emit_int(magma_power_time);
 emit_int(magma_power_direction);emit_int(magma_power_origin_x);emit_int(magma_power_origin_y);
 emit_int(mask);emit_int(path_count);emit_int(hit_mask);emit_int(spent);emit_int(ended_mask);
 emit_int(aimed);emit_int(cast_side);emit_int(active());emit_int(live_window());
 /* Record real tick/draw cache state before forcing the remaining paths. */
 for(i=0;i<path_count;i++)oracle_path(&paths[i]);
 for(i=0;i<path_count;i++)refresh(i);
 for(i=0;i<path_count;i++){
  const Path *p=&paths[i];oracle_path(p);oracle_paths++;
  if(p->open&&!p->whole)oracle_clipped++;
  if(p->x<x0)x0=p->x;if(p->tx<x0)x0=p->tx;
  if(p->y<y0)y0=p->y;if(p->ty<y0)y0=p->ty;
  if(p->x>x1)x1=p->x;if(p->tx>x1)x1=p->tx;
  if(p->y>y1)y1=p->y;if(p->ty>y1)y1=p->ty;
  if(p->radius>r)r=p->radius;
 }
 if(magma_power_kind==66){assert(path_count==5);oracle_five_ray_frames++;}
 assert(path_count>0&&path_count<=5);
 x0-=r+1;y0-=r+1;x1+=r+1;y1+=r+1;
 emit_int(x0);emit_int(y0);emit_int(x1);emit_int(y1);
 /* Outside these raw bounds every on_path rejects on its own bounding test.
  * Inside, exhaust all pixels, including walls, margins and clipped tails. */
 for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++){
  unsigned hits=0;for(i=0;i<path_count;i++)if(on_path(i,x,y))hits|=1u<<i;
  emit_byte(hits);oracle_points++;
 }
}
int oracle_ray(int x,int y,int tx,int ty){return clear(x,y,tx,ty);}
void oracle_metrics(void){
 fprintf(stderr,"{\"point_pixels\":%llu,\"exact_path_records\":%llu,\"clipped_path_records\":%llu,\"command66_five_ray_frames\":%llu}\n",
  (unsigned long long)oracle_points,(unsigned long long)oracle_paths,
  (unsigned long long)oracle_clipped,(unsigned long long)oracle_five_ray_frames);
}
'''

DRIVER = r'''
#define main original_magma_integration_main
#define obj_add original_obj_add
#define game_clear_box original_game_clear_box
#include "magma_powers_native.c"
#undef game_clear_box
#undef obj_add
#undef main
#include <stdint.h>
void oracle_frame(void);
int oracle_ray(int,int,int,int);
void oracle_metrics(void);
static unsigned char record[32768];
static unsigned record_size,mark_count,certificate_calls,certificate_successes;
static int marks[32][8],last_marks[32][8],want_marks;
int game_clear_box(int x0,int y0,int x1,int y1){
 int empty=original_game_clear_box(x0,y0,x1,y1);certificate_calls++;
 certificate_successes+=(unsigned)empty;return empty;
}
void emit_byte(unsigned value){assert(value<256&&record_size<sizeof record);record[record_size++]=(unsigned char)value;}
void emit_int(int value){uint32_t v=(uint32_t)value;unsigned n;for(n=0;n<4;n++)emit_byte((v>>(8*n))&255u);}
static void begin_record(int c,int dir,int side,int scene,int n){
 record_size=0;emit_int(c);emit_int(dir);emit_int(side);emit_int(scene);emit_int(n);
}
static void end_record(void){
 unsigned char header[4];unsigned i;for(i=0;i<4;i++)header[i]=(unsigned char)(record_size>>(8*i));
 assert(fwrite(header,1,4,stdout)==4);assert(fwrite(record,1,record_size,stdout)==record_size);
}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip){
 original_obj_add(off,x,y,w,h,priority,depth,flip);
 if(want_marks){int *p;assert(mark_count<32);p=marks[mark_count++];
  p[0]=off;p[1]=x;p[2]=y;p[3]=w;p[4]=h;p[5]=priority;p[6]=depth;p[7]=flip;}
}
static void relative_point(int f,int s,int *x,int *y){
 static const int dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
 *x=px+f*dx[face]-s*dy[face];*y=py+f*dy[face]+s*dx[face];
}
static void relative_wall(int f,int s,int w,int h){
 int x0,y0,x1,y1;relative_point(f,s,&x0,&y0);relative_point(f+w-1,s+h-1,&x1,&y1);
 wall(x0<x1?x0:x1,y0<y1?y0:y1,abs(x1-x0)+1,abs(y1-y0)+1);
}
static void remove_walls(void){wall_count=0;southern_powers_geometry_changed();magma_powers_geometry_changed();}
static void initialize_scene(unsigned c,unsigned scene,int side){
 int x,y;
 if(scene==1)relative_wall(18,-40,1,81);
 if(scene==2){relative_wall(1,0,1,1);relative_wall(0,side,1,1);}
 if(scene==3){relative_wall(13,9,1,1);relative_wall(26,-9,3,4);relative_wall(38,0,1,1);}
 if(scene==5)relative_wall(24,9*side,1,1);
 if(scene==6){px=3;py=3;}
 if(scene==7){px=476;py=316;}
 if(scene==8){relative_point(28,8,&x,&y);enemy(0,x,y,100);
  relative_point(38,-4,&x,&y);enemy(1,x,y,100);}
 if(scene==10){relative_wall(32,0,1,1);relative_wall(10,30,1,1);
  relative_wall(-26,19,1,1);relative_wall(-26,-19,1,1);relative_wall(10,-30,1,1);}
 (void)c;
}
static int change_scene(unsigned c,unsigned scene,unsigned n,int side){int aimed=-1;
 if(scene==4&&n==5)relative_wall(12,-35,1,71);
 if(scene==4&&n==16)remove_walls();
 if(scene==4&&n==25)relative_wall(24,-18,1,37);
 if(scene==4&&n==31)remove_walls();
 if(scene==5&&n==12){remove_walls();relative_wall(12,0,1,1);}
 if(scene==5&&n==20)remove_walls();
 if(scene==5&&n==27)relative_wall(24,9*side,1,1);
 if(scene==8&&n==2&&c==51){face=(face+1)&3;aimed=magma_powers_aim();}
 if(scene==8&&n==7){enemies[0].x+=2;enemies[0].y-=2;}
 if(scene==9&&n==10)wall(px,py,1,1);
 if(scene==9&&n==14)remove_walls();
 if(scene==10&&n==22)remove_walls();
 if(scene==10&&n==30){relative_wall(8,0,1,1);relative_wall(3,9,1,1);
  relative_wall(-8,6,1,1);relative_wall(-8,-6,1,1);relative_wall(3,-9,1,1);}
 return aimed;
}
static void render_and_record(void){unsigned i,j,count;
 draws=solid_calls=0;mark_count=0;want_marks=1;magma_powers_draw();want_marks=0;
 assert(mark_count<=24);count=mark_count;memcpy(last_marks,marks,sizeof marks);
 /* No scenery mutation: repeated draw must preserve every sprite attribute. */
 draws=solid_calls=0;mark_count=0;want_marks=1;magma_powers_draw();want_marks=0;
 assert(mark_count==count&&memcmp(last_marks,marks,count*sizeof marks[0])==0);
 assert(solid_calls==0);
 emit_int((int)count);for(i=0;i<count;i++)for(j=0;j<8;j++)emit_int(marks[i][j]);
}
int main(void){unsigned c,dir,scene,n,i,life;int side,accepted,aimed,x,y;
 for(c=43;c<=66;c++)for(dir=0;dir<4;dir++)for(side=-1;side<=1;side+=2)for(scene=0;scene<11;scene++){
  setup(c);face=(int)dir;initialize_scene(c,scene,side);accepted=magma_power_side(c,side);
  life=start[c-43]+act[c-43]+recover[c-43];
  for(n=0;n<=(accepted?life+2:0);n++){
   aimed=change_scene(c,scene,n,side);if(n&&accepted)magma_powers_tick();
   begin_record((int)c,(int)dir,side,(int)scene,(int)n);emit_int(accepted);emit_int(aimed);
   if(accepted){render_and_record();oracle_frame();
    for(i=0;i<6;i++){emit_int(enemies[i].hp);emit_int(enemy_hp_q4[i]);emit_int(enemies[i].flash);
     emit_int(rooted_enemies[i]);emit_int(slowed_enemies[i]);emit_int(enemy_stagger_ticks[i]);}}
   end_record();
  }
 }
 /* Exhaust all endpoint offsets in every octant, reverse each segment, test
  * near-world edges, invalid endpoints, exact distance limits and mutations. */
 setup(66);assert(magma_power(66));
 for(scene=0;scene<5;scene++){
  remove_walls();
  if(scene==1){wall(103,87,1,28);wall(91,92,13,1);}
  if(scene==2){wall(101,100,1,1);wall(100,101,1,1);}
  if(scene==3){wall(100,100,1,1);}
  if(scene==4){wall(140,100,1,1);wall(100,60,1,1);}
  for(y=-40;y<=40;y++){
   begin_record(-1,0,0,(int)scene,y);
   for(x=-40;x<=40;x++){
    emit_int(oracle_ray(100,100,100+x,100+y));
    emit_int(oracle_ray(100+x,100+y,100,100));
    emit_int(oracle_ray(100+x,100+y,97-x,104-y));
    emit_int(oracle_ray(3,3,3+x,3+y));
    emit_int(oracle_ray(476,316,476+x,316+y));
   }end_record();
  }
  begin_record(-2,0,0,(int)scene,0);
  emit_int(oracle_ray(-1,0,3,3));emit_int(oracle_ray(100,100,1024,100));
  emit_int(oracle_ray(100,100,292,100));emit_int(oracle_ray(100,100,293,100));
  emit_int(oracle_ray(100,100,100,100));end_record();
 }
 oracle_metrics();
 fprintf(stderr,"{\"certificate_calls\":%u,\"certified_empty_boxes\":%u}\n",certificate_calls,certificate_successes);
 return 0;
}
'''


def read_record(stream):
    header = stream.read(4)
    if not header:
        return None
    assert len(header) == 4, 'Truncated record length'
    size, = struct.unpack('<I', header)
    data = stream.read(size)
    assert len(data) == size, 'Truncated record body'
    return header + data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sanitize', action='store_true', help='Run the complete differential under ASan/UBSan')
    args = parser.parse_args()
    assert hashlib.sha256(FROZEN.read_bytes()).hexdigest() == PIN, 'Frozen candidate J was edited'
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'driver.c').write_text(DRIVER)
    flags = ['-std=c99', '-O2', '-g', '-Wall', '-Wextra', '-Werror',
             '-Wno-misleading-indentation', '-pedantic', '-Isrc', '-Itests']
    suffix = '-sanitized' if args.sanitize else ''
    if args.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    paths = {'reference': FROZEN, 'optimized': ROOT/'src/magma_powers.c'}
    source_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    processes = {}
    errors = {}
    writers = {}
    hashes = {name: hashlib.sha256() for name in paths}
    count = cast_frames = rejected = size = 0
    try:
        for name, path in paths.items():
            generated = OUT/(name+'.c')
            generated.write_bytes(path.read_bytes()+WRAPPER.encode())
            exe = OUT/(name+suffix)
            subprocess.run(['cc', *flags, str(OUT/'driver.c'), str(generated), *SOURCES,
                            '-o', str(exe)], cwd=ROOT, check=True)
            errors[name] = open(OUT/(name+suffix+'.stderr'), 'wb')
            writers[name] = gzip.open(OUT/(name+suffix+'.bin.gz'), 'wb', compresslevel=1)
            processes[name] = subprocess.Popen([str(exe)], cwd=ROOT, stdout=subprocess.PIPE,
                stderr=errors[name], env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0'))
        while True:
            rows = {name: read_record(proc.stdout) for name, proc in processes.items()}
            reference, candidate = rows['reference'], rows['optimized']
            for name, row in rows.items():
                if row is not None:
                    writers[name].write(row)
                    hashes[name].update(row)
            if reference != candidate:
                context = struct.unpack('<5i', (reference or candidate)[4:24])
                mismatch = next((i for i, (a,b) in enumerate(zip(reference or b'',candidate or b'')) if a != b), None)
                failure = {'record_index': count, 'command_direction_side_scene_frame': context,
                           'first_different_byte': mismatch,
                           'reference_bytes': len(reference or b''), 'optimized_bytes': len(candidate or b'')}
                (OUT/('mismatch'+suffix+'.json')).write_text(json.dumps(failure, indent=2)+'\n')
                raise AssertionError(('Magma geometry mismatch; expectations remain unchanged', failure))
            if reference is None:
                break
            count += 1
            size += len(reference)
            if struct.unpack('<i', reference[4:8])[0] >= 43:
                accepted, = struct.unpack('<i', reference[24:28])
                cast_frames += bool(accepted)
                rejected += not bool(accepted)
        for name, proc in processes.items():
            assert proc.wait() == 0, (name, (OUT/(name+suffix+'.stderr')).read_text())
    finally:
        for proc in processes.values():
            if proc.poll() is None:
                proc.terminate()
            proc.wait()
        for file in [*errors.values(), *writers.values()]:
            file.close()
    statistics = {name: [json.loads(line) for line in (OUT/(name+suffix+'.stderr')).read_text().splitlines()] for name in paths}
    metrics = {name: rows[0] for name, rows in statistics.items()}
    certificates = {name: rows[1] for name, rows in statistics.items()}
    assert metrics['reference'] == metrics['optimized']
    assert certificates['reference']['certificate_calls'] == 0
    assert 0 < certificates['optimized']['certified_empty_boxes'] < certificates['optimized']['certificate_calls']
    assert metrics['reference']['clipped_path_records'] > 0
    assert metrics['reference']['command66_five_ray_frames'] > 0
    for name, path in paths.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source_hashes[name], 'Source changed during differential'
    report = {
        'kind': 'synthetic-host-exact-differential-not-controller-acceptance',
        'frozen_oracle_source': 'build/underwater-candidate-j/runtime-source/src/magma_powers.c',
        'frozen_oracle_sha256': PIN, 'source_sha256': source_hashes,
        'reference_adaptations': 'none; read-only test accessors appended after original bytes',
        'sanitizers': ['address', 'undefined'] if args.sanitize else [],
        'matched_records': count, 'matched_cast_frame_records': cast_frames,
        'matched_rejected_admissions': rejected, 'matched_uncompressed_bytes': size,
        'exact_output_sha256': {name: digest.hexdigest() for name,digest in hashes.items()},
        'commands': list(range(43,67)), 'directions': 4, 'cast_sides': [-1,1],
        'collision_scenes': 11, 'certificate_coverage': certificates, 'matched_direct_ray_checks': 5*(81*81*5+5),
        'point_coverage': 'Every integer pixel in raw path union bounds expanded by maximum radius + 1; exact per-path bitmasks, no sampling',
        'path_coverage': 'All 14 Path fields before and after refresh, including ex/ey/valid/open/whole/parent/from/to; active/ended masks',
        'draw_coverage': 'All 8 obj_add attributes for every mark; identical repeat draw and zero repeat scenery probes',
        'scenes': ['open', 'one-pixel rotated barrier', 'diagonal side-cell corner',
                   'off-axis sparse obstacles', 'add/remove/move barriers',
                   'parent elbow and origin-link mutations', 'near lower world edge',
                   'near upper world edge', 'enemy hits and command51 re-aim',
                   'origin blocked/unblocked during cast', 'five-ray endpoint and inner-ray mutations'],
        **metrics['reference'],
    }
    (OUT/('report'+suffix+'.json')).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
