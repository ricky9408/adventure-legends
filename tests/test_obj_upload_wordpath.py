#!/usr/bin/env python3
"""Differential exact live OBJ swizzle versus preserved bytewise algorithm.
Host register writes are captured (DMA not emulated); native engine QA separately
checks actual uploaded VRAM/OAM. Every source/destination byte and DMA descriptor
must match, including the untouched tail and misaligned-source fallback.
"""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/obj-wordpath-host';OUT.mkdir(parents=True,exist_ok=True)
s=(ROOT/'src/game.c').read_text();start=s.index('void obj_upload(');brace=s.index('{',start);level=1;end=brace+1
while level:
 level+=(s[end]=='{')-(s[end]=='}');end+=1
candidate=s[start:end]
reference='''void bytewise_upload(const u8 *data,int w,int h,int offset){int tx,ty,x,y,k=0;u16 *dst=(u16*)(0x06014000+offset);
 for(ty=0;ty<h;ty+=8)for(tx=0;tx<w;tx+=8)for(y=0;y<8;y++)for(x=0;x<8;x+=2){int p=(ty+y)*w+tx+x;obj_tiles[k++]=data[p]|(data[p+1]<<8);}
 REG32(0x040000D4)=(u32)obj_tiles;REG32(0x040000D8)=(u32)dst;REG32(0x040000DC)=0x84000000|(k/2);}
'''
source='''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef unsigned char u8;typedef unsigned short u16;typedef unsigned int u32;
static u16 obj_tiles[512] __attribute__((aligned(4)));static u32 regs[3];
#define REG32(a) regs[((a)-0x040000D4)/4]
'''+reference+candidate+'''
int main(void){static u8 input[2048] __attribute__((aligned(4)));u16 before[512];u32 oldregs[3],seed=0x194831;unsigned cases=0;int w,h,shift,pattern,k;
 for(w=8;w<=64;w+=8)for(h=8;h<=64;h+=8)if(w*h<=1024)for(shift=0;shift<8;shift++)for(pattern=0;pattern<32;pattern++){
  for(k=0;k<2048;k++){seed=seed*1664525u+1013904223u;input[k]=(u8)(pattern==0?0:pattern==1?255:pattern==2?(u32)k:seed>>24);}
  memset(obj_tiles,0xcd,sizeof obj_tiles);memset(regs,0,sizeof regs);bytewise_upload(input+shift,w,h,10816);memcpy(before,obj_tiles,sizeof before);memcpy(oldregs,regs,sizeof regs);
  memset(obj_tiles,0xcd,sizeof obj_tiles);memset(regs,0,sizeof regs);obj_upload(input+shift,w,h,10816);
  assert(!memcmp(before,obj_tiles,sizeof before));assert(!memcmp(oldregs,regs,sizeof regs));cases++;
 }
 printf("PASS %u exact OBJ bytes, DMA descriptors and untouched-tail cases\\n",cases);return 0;}
'''
p=OUT/'probe.c';p.write_text(source);runs=[]
for sanitizer in (False,True):
 exe=OUT/('sanitized' if sanitizer else 'strict');flags=['-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-pointer-to-int-cast','-Wno-int-to-pointer-cast','-fno-strict-aliasing']
 if sanitizer:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
 subprocess.run([os.environ.get('HOST_CC','cc'),*flags,str(p),'-o',str(exe)],check=True)
 r=subprocess.run([str(exe)],text=True,capture_output=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'});(OUT/(exe.name+'.log')).write_text(r.stdout+r.stderr);runs.append(dict(sanitizer=sanitizer,exit=r.returncode,stdout=r.stdout));assert r.returncode==0,r.stderr
report=dict(scope=__doc__,candidate_function_sha256=hashlib.sha256(candidate.encode()).hexdigest(),reference_function_sha256=hashlib.sha256(reference.encode()).hexdigest(),game_source_sha256=hashlib.sha256(s.encode()).hexdigest(),test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),runs=runs)
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(runs,indent=2))
