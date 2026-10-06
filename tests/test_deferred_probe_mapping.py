#!/usr/bin/env python3
"""Synthetic OS mapping/cleanup check of the exact probe mapping implementation."""
import hashlib,json,os,shlex,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/evidence/deferred-anchor/engine_probe.c'
class MappingTests(unittest.TestCase):
 def check_build(self,sanitize):
  text=SOURCE.read_text();fragment=text[text.index('uintptr_t probe_map_error_address;'):]
  harness=r'''
int main(void){
 const uintptr_t a[]={0x04000000,0x05000000,0x06000000,0x07000000};
 unsigned i;void *p[4];
 for(i=0;i<4;i++){
  p[i]=mmap((void*)a[i],0x20000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
  if(p[i]!=(void*)a[i]){fprintf(stderr,"host setup unavailable at %lx errno %d\n",(unsigned long)a[i],errno);return 77;}
 }
 for(i=0;i<4;i++)if(i!=1)assert(munmap(p[i],0x20000)==0);
 ((volatile unsigned char*)p[1])[0]=0xa5;
 assert(probe_map()==0);
 assert(probe_map_error_address==a[1] && probe_map_error_number==EEXIST && probe_map_success_count==1);
 assert(((volatile unsigned char*)p[1])[0]==0xa5); /* Pre-existing bytes survived. */
 p[0]=mmap((void*)a[0],0x20000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
 assert(p[0]==(void*)a[0]); /* Earlier owned partial mapping was cleaned up. */
 assert(munmap(p[0],0x20000)==0 && munmap(p[1],0x20000)==0);
 assert(probe_map()==1 && probe_map_success_count==4 && !probe_map_error_address && !probe_map_error_number);
 for(i=0;i<4;i++)assert(munmap((void*)a[i],0x20000)==0);
 puts("exact mapping function: collision diagnosed, pre-existing bytes preserved, partial cleanup and clean success pass");
 return 0;
}
'''
  with tempfile.TemporaryDirectory(prefix='probe-map-test-') as tmp:
   src=Path(tmp)/'test.c';exe=Path(tmp)/'test'
   src.write_text('#define _GNU_SOURCE\n#include <sys/mman.h>\n#include <stdint.h>\n#include <errno.h>\n#include <assert.h>\n#include <stdio.h>\n#define NI\n'+fragment+harness)
   flags=['-std=c99','-O1','-Wall','-Wextra','-Werror']
   if sanitize:flags+=['-fsanitize=undefined','-fno-sanitize-recover=all']
   subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+flags+[str(src),'-o',str(exe)],check=True)
   result=subprocess.run([str(exe)],text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertIn('collision diagnosed',result.stdout)
   print(json.dumps(dict(synthetic=True,gameplay_claim=False,ubsan=sanitize,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),fragment_sha256=hashlib.sha256(fragment.encode()).hexdigest(),result=result.stdout.strip())))
 def test_strict_exact_mapping(self):self.check_build(False)
 def test_ubsan_exact_mapping(self):self.check_build(True)
if __name__=='__main__':unittest.main(verbosity=2)
