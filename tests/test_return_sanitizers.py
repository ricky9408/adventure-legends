#!/usr/bin/env python3
"""ASan/UBSan host differential walks over synthetic Return states."""
import tempfile,subprocess,os,shlex,unittest
from pathlib import Path
from return_host_support import *
HARNESS=r'''
#include "return_quests.h"
#include "progression_events.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static Save5State base,s,before;
static unsigned random_state=0x52455437u;
static unsigned rnd(void){random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;return random_state;}
#define REQUIRE(x) do{if(!(x)){fprintf(stderr,"FAIL line%d case%u\n",__LINE__,n);return 1;}}while(0)
int main(int argc,char**argv){
 unsigned n=0,k,status,token,expected,slot;FILE*f;
 ReturnRequest r={0};
 REQUIRE(argc==2);f=fopen(argv[1],"rb");REQUIRE(f);REQUIRE(fread(&base,sizeof base,1,f)==1);fclose(f);
 REQUIRE(creatures_catalog_validate());REQUIRE(save5_validate(&base));
 for(n=0;n<16000;++n){
  s=base;if(n)for(k=0;k<1+n%3;++k)((unsigned char*)&s)[rnd()%sizeof s]=(unsigned char)rnd();
  before=s;expected=save5_validate(&s);token=save5_preflight_begin(&s);REQUIRE(token);
  for(k=0;k<500;++k){status=save5_preflight_step(token,(k%4)==0?1:(k%4)==1?64:(k%4)==2?1024:0xffffffffu);if(status!=SAVE5_BUSY)break;}
  REQUIRE(status==(expected?SAVE5_DONE:SAVE5_FAILED));REQUIRE(!memcmp(&s,&before,sizeof s));save5_preflight_cancel();
 }
 for(n=0;n<10000;++n){
  CreatureInstance c;slot=rnd()%160;c=base.roster.instances[slot];
  ((unsigned char*)&c)[rnd()%sizeof c]=(unsigned char)rnd();
  (void)creatures_instance_validate(&c);for(k=1;k<=7;++k)(void)creatures_instance_validate_revision(&c,k);
  (void)creatures_trial_mask_for_key(rnd(),rnd());(void)creatures_supports_capability(rnd(),rnd());
  (void)progression_encounter_event(rnd(),rnd());
 }
 /* Actual new-family completion from base commands plus bounded cancellation. */
 for(slot=0;slot<160&&base.roster.instances[slot].form_id!=101;++slot){}REQUIRE(slot<160);
 base.roster.party[0]=(unsigned char)slot;for(k=1;k<4;++k)base.roster.party[k]=255;base.roster.selected_party=0;
 r.operation=RETURN_REQUEST_TRIAL_COMPLETE;r.room=56;r.slot=slot;r.family=39;r.key=1;r.form=101;r.command=102;r.instance_id=base.roster.instances[slot].instance_id;
 for(n=0;n<64;++n){
  s=base;before=s;token=return_job_begin(&s,&r,100+n,1);REQUIRE(token);
  for(k=0;k<n&&return_job_status(token)==SAVE5_BUSY;++k)(void)return_job_step(token,64,100+n,1);
  if(return_job_status(token)==SAVE5_BUSY){return_job_cancel();REQUIRE(!memcmp(&s,&before,sizeof s));}
  else{REQUIRE(return_job_status(token)==SAVE5_DONE);REQUIRE(return_job_result(token)==RETURN_REWARDED);REQUIRE(save5_validate(&s));}
 }
 puts("ASan/UBSan:16000 malformed preflight differentials,10000 record/API fuzz,64 bounded trial cancellations passed");return 0;
}
'''
class ReturnSanitizers(unittest.TestCase):
 def test_address_undefined(self):
  with tempfile.TemporaryDirectory(prefix='return-sanitize-') as tmp:
   tmp=Path(tmp);lib=build(tmp/'host');s,_=initial_chapter(lib);(tmp/'state.bin').write_bytes(bytes(s));(tmp/'probe.c').write_text(HARNESS)
   sources=('save4','save5','creatures','creature_data','equipment','equipment_data','return_quests','progression_events')
   subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+['-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(ROOT/'src'),*[str(ROOT/'src'/f'{x}.c') for x in sources],str(tmp/'probe.c'),'-o',str(tmp/'probe')],check=True)
   subprocess.run([str(tmp/'probe'),str(tmp/'state.bin')],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))
if __name__=='__main__':unittest.main(verbosity=2)
