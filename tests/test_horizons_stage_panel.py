#!/usr/bin/env python3
"""Compare actual optimized Horizons stage art against the original pixel contract.
Extracts current functions and indexed art; simulates only synchronous 16-bit DMA.
All 38,400 pixels are checked across clipping, camera offsets and odd/even x.
This is a host pixel oracle, not native cadence or complete gameplay acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,os,shlex,subprocess,tempfile
from test_horizons_camera import extract_function
ROOT=Path(__file__).resolve().parents[1]
HEAD='''#include <cstdio>
#include <cstring>
#include <cstdint>
#include <cstdlib>
#include "assets.h"
#define COLD
#define GAME_HOST_TEST
#define WHITE PAL_WHITE
using u8=unsigned char;using u16=unsigned short;using u32=unsigned int;
int camera_x,camera_y;u16 pixels[19200];u16*screen=pixels;
'''
DMA='''static uintptr_t dma_src,dma_dst;
struct Register{unsigned address;void operator=(uintptr_t value)const{
 if(address==0x040000D4){dma_src=value;return;}if(address==0x040000D8){dma_dst=value;return;}
 if(address!=0x040000DC||((value&0xffff)!=16&&(value&0xffff)!=17)||(dma_src&1)||(dma_dst&1)||dma_dst<(uintptr_t)pixels||dma_dst+(value&0xffff)*2>(uintptr_t)pixels+sizeof pixels)std::abort();
 std::memcpy((void*)dma_dst,(const void*)dma_src,(value&0xffff)*2);
}};
#define HZ_REG32(a) Register{a}
'''
ORACLE='''void original(int x,int y){rr(x-16,y-9,33,18,PAL_ROSE4);for(int dx=-14;dx<=14;dx+=4)rl(x+dx,y-7,x+dx+1,y+7,PAL_GOLD4);rl(x-17,y-10,x+17,y-10,PAL_WOOD1);}
int main(){unsigned char expected[38400];unsigned cases=0;
 for(int camera=0;camera<4;camera++){camera_x=camera*73;camera_y=camera*41;
  for(int y=-24;y<=184;y+=4)for(int x=-24;x<=264;x+=3){
   for(unsigned i=0;i<19200;i++)pixels[i]=(i*173+cases*13)&65535;
   original(x+camera_x,y+camera_y);std::memcpy(expected,pixels,sizeof expected);
   for(unsigned i=0;i<19200;i++)pixels[i]=(i*173+cases*13)&65535;
   stage_panel(x+camera_x,y+camera_y);
   if(std::memcmp(expected,pixels,sizeof expected)){std::fprintf(stderr,"different: %d,%d camera%d\\n",x,y,camera);return 1;}cases++;
  }
 }
 std::printf("PASS: %u full-screen original/panel pixel comparisons\\n",cases);
}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,default=ROOT);p.add_argument('--report',type=Path);a=p.parse_args();root=a.source_root.resolve();game=(root/'src/game.c').read_text().replace('} int','}\nint');draw=(root/'src/horizons_game_draw.inc').read_text();start=draw.index('/* Exact raster');stop=draw.index('static COLD void rr',start);actual=draw[start:stop];assert 'stage_panel_pixels' in actual and 'HZ_REG32' in actual
 parts=[HEAD]+[extract_function(game,n,'src/game.c')for n in ('ab','sign','pix','rect','line','sprite')]+[extract_function(draw,n,'src/horizons_game_draw.inc')for n in ('rr','rl')]+[DMA,actual,ORACLE];source=''.join(parts);compiler=shlex.split(os.environ.get('CXX','c++'));results={}
 with tempfile.TemporaryDirectory(prefix='horizons-stage-pixel-')as tmp:
  tmp=Path(tmp)
  for name,text,flags in [('strict',source,['-O2']),('sanitized',source,['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']),('negative_shift',source.replace('x-=camera_x;y-=camera_y;','x+=1-camera_x;y-=camera_y;'),['-O2'])]:
   file=tmp/(name+'.cpp');file.write_text(text);binary=tmp/name;cmd=compiler+['-std=c++17','-Wall','-Wextra','-Werror',*flags,'-I',str(root/'src'),str(file),'-o',str(binary)];subprocess.run(cmd,check=True);run=subprocess.run([str(binary)],env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'},text=True,capture_output=True);results[name]={'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
   if name=='negative_shift':assert text!=source and run.returncode!=0,'Shifted art must fail'
   else:assert run.returncode==0,run.stderr
 result={'scope':__doc__,'source_root':str(root),'sources':{name:hashlib.sha256((root/name).read_bytes()).hexdigest()for name in ('src/game.c','src/horizons_game_draw.inc','src/assets.h')},'pixel_cases':20564,'pixels_per_case':38400,'strict_and_asan_ubsan_passed':True,'negative_shift_rejected':True,'leak_check':'Disabled only because ptrace container prevents LeakSanitizer; ASan and UBSan active','results':results}
 if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n')
 print('PASS:20,564 complete-screen pixel cases; strict+ASan/UBSan; shifted-art mutation rejected')
if __name__=='__main__':main()
