#!/usr/bin/env python3
"""Isolated ARM7TDMI/mGBA transaction timing, with synthetic report context and
capacity/wallet cases derived from authenticated G7 generated saves. This is
bounded-core diagnostic evidence, not controller journey or hardware timing.
"""
import ctypes as C,hashlib,json,subprocess,sys
from pathlib import Path
from test_later_rewards import LaterRewardTests,Save,Instance,context,SOURCES
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
OUT=ROOT/'build/later-rewards-arm';OUT.mkdir(parents=True,exist_ok=True)
LaterRewardTests.setUpClass();case=LaterRewardTests();inputs=[];descriptions=[]
for t in range(4):
 case.setUp();s,c=case.state(t,True);inputs.append((bytes(s),t,SOURCES[t][0],bytes(c)));descriptions.append(f'fresh-Q{(21,24,32,40)[t]}')
case.setUp();row=json.loads((ROOT/'tests/fixtures/v5-revision9/provenance.json').read_text())['fixtures'][0];data=(ROOT/row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];case.ram[:]=data;s=case.load()
for i in range(160):
 if not s.roster.instances[i].form_id:
  template=Instance.from_buffer_copy(bytes(s.roster.instances[0]));template.flags=1;template.instance_id=s.roster.next_instance_id;s.roster.instances[i]=template;s.roster.next_instance_id+=1
s.campaign.room=s.campaign.spawn=0;s.economy.gold=s.economy.earned=9999;assert case.l.save5_validate(C.byref(s))
inputs.append((bytes(s),3,6,bytes(context(6))));descriptions.append('recovery-Pearl-full48-160-wallet9999')
source=OUT/'bench.c'
arrays='\n'.join('static const unsigned char input_%d[%d]={%s};'%(i,len(b),','.join(map(str,b)))for i,(b,*_)in enumerate(inputs))
contexts='\n'.join('static const unsigned char context_%d[%d]={%s};'%(i,len(c),','.join(map(str,c)))for i,(*_,c)in enumerate(inputs))
main=r'''
#include "later_rewards.h"
#define REG16(a) (*(volatile unsigned short *)(a))
void *memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
static Save5State live;
static LaterRewardContext context;
volatile unsigned cycles[5][2][5],steps[5][2],results[5][2],done,failed;
const char sram_id[]="SRAM_V113";
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010c);lo=REG16(0x04000108);hi2=REG16(0x0400010c);}while(hi!=hi2);return(hi<<16)|lo;}
'''+arrays+'\n'+contexts+r'''
int main(void){unsigned row,bank,t,status,phase,i,elapsed,n;
 const unsigned char*states[5]={input_0,input_1,input_2,input_3,input_4};
 const unsigned char*contexts[5]={context_0,context_1,context_2,context_3,context_4};
 const unsigned treasures[5]={0,1,2,3,3},sources[5]={0,2,4,5,6};
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010c)=0;REG16(0x0400010e)=0x84;REG16(0x04000108)=0;REG16(0x0400010a)=0x80;
 for(row=0;row<5;row++)for(bank=0;bank<2;bank++){
  for(i=0;i<32768;i++)((volatile unsigned char*)0x0e000000)[i]=255;
  memcpy(&live,states[row],sizeof live);memcpy(&context,contexts[row],sizeof context);
  if(!save5_store(&live)||(bank&&!save5_store(&live))){failed=10+row;while(1){}}
  t=now();status=later_rewards_begin(&live,treasures[row],sources[row],&context);cycles[row][bank][0]=now()-t;
  if(!status){failed=20+row;while(1){}}
  for(n=0;n<400;n++){
   phase=later_rewards_phase();t=now();status=later_rewards_step(&context);elapsed=now()-t;
   if(elapsed>cycles[row][bank][phase])cycles[row][bank][phase]=elapsed;
   if(status!=SAVE5_BUSY)break;
  }
  steps[row][bank]=n+1;results[row][bank]=status;
  t=now();i=(unsigned)save5_validate(&live);cycles[row][bank][4]=now()-t;
  if(status!=SAVE5_DONE||!i){failed=30+row;while(1){}}
 }
 done=1;while(1){}return 0;
}
'''
source.write_text(main);arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc';prefix=str(arm).removesuffix('gcc')
flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-ffunction-sections','-fdata-sections','-fstack-usage','-Isrc']
objects=[]
for path in [source,*[ROOT/'src'/n for n in ('save4.c','save5.c','creatures.c','creature_data.c','equipment.c','equipment_data.c')]]:
 obj=OUT/(path.stem+'.o');subprocess.run([str(arm),*flags,'-c',str(path),'-o',str(obj)],cwd=ROOT,check=True);objects.append(obj)
startup=OUT/'startup.o';subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-c','src/startup.s','-o',str(startup)],cwd=ROOT,check=True)
elf=OUT/'bench.elf';rom=OUT/'bench.gba';subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections','-Wl,-T,linker.ld',str(startup),*[str(p)for p in objects],'-lgcc','-o',str(elf)],cwd=ROOT,check=True)
subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,'tools/fix_header.py',str(rom)],cwd=ROOT,check=True)
sym={p[2]:int(p[0],16)for line in subprocess.check_output([prefix+'nm','-n',str(elf)],text=True).splitlines()if len(p:=line.split())==3}
with Emulator(rom)as e:
 for _ in range(200):
  e.frames(100)
  if e.read(sym['done'])or e.read(sym['failed']):break
 assert e.read(sym['done'])and not e.read(sym['failed']),e.read(sym['failed'])
 rows=[]
 for row,label in enumerate(descriptions):
  for bank in range(2):
   cs=[e.read(sym['cycles']+((row*2+bank)*5+op)*4)for op in range(5)]
   rows.append(dict(label=label,destination='A'if bank else'B',begin_cycles=cs[0],max_preflight_step_cycles=cs[1],admission_cycles=cs[2],max_writer_step_cycles=cs[3],blocking_validation_cycles=cs[4],steps=e.read(sym['steps']+(row*2+bank)*4),status=e.read(sym['results']+(row*2+bank)*4)))
report={'scope':__doc__,'frame_cycles':280896,'waitcnt':'0x4317','rows':rows,'stack_usage':(OUT/'save5.su').read_text(),'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [ROOT/'src/save5.c',ROOT/'src/save5_preflight.inc',ROOT/'src/save5_later_rewards.inc',ROOT/'src/later_rewards.h']},'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest()}
(OUT/'timing.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
assert max(max(r[k]for k in ('begin_cycles','max_preflight_step_cycles','admission_cycles','max_writer_step_cycles'))for r in rows)<100000,'bounded core exceeds100000-cycle diagnostic allowance'
