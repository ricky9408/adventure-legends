/* Independent bounded-core differential with legal grandfathered stress. */
#include "creatures.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static CreatureRoster source,live,frozen,wanted,original;
static unsigned comparisons,queries;
static void finish(CreatureU32 t){unsigned n=0;int done;do{done=creatures_admission_job_step(t,1+(n%4));assert(done>=0);assert(++n<162);}while(!done);}
static void compare_grant(unsigned id,unsigned level,unsigned bond,unsigned flags,unsigned reward){
 CreatureAdmission a,b;CreatureU32 t;unsigned slot1,slot2;int s1,s2;
 live=source;wanted=source;frozen=source;original=source;
 s1=creatures_admission_query_grant(&wanted,id,&a);
 t=creatures_admission_job_begin(&frozen,id,255);assert(t);finish(t);
 s2=creatures_admission_job_result(t,&b);assert(s1==s2&&!memcmp(&a,&b,sizeof a));++queries;
 s1=creatures_grant_admitted(&wanted,id,level,bond,flags,reward,&slot1);
 s2=creatures_admission_job_commit_grant(t,&live,level,bond,flags,reward,&slot2);
 assert(s1==s2&&slot1==slot2&&!memcmp(&wanted,&live,sizeof live));assert(!memcmp(&frozen,&original,sizeof frozen));
 original=live;assert(creatures_admission_job_commit_grant(t,&live,level,bond,flags,reward,&slot2)==CREATURE_ADMISSION_INVALID);assert(!memcmp(&live,&original,sizeof live));++comparisons;
}
static void compare_evolution(unsigned slot,unsigned id,unsigned context,int sanctuary,int confirmed){
 CreatureAdmission a,b;CreatureU32 t;int s1,s2;
 live=source;wanted=source;frozen=source;original=source;
 s1=creatures_admission_query_evolution(&wanted,slot,id,&a);
 t=creatures_admission_job_begin(&frozen,id,slot);assert(t);finish(t);
 s2=creatures_admission_job_result(t,&b);assert(s1==s2&&!memcmp(&a,&b,sizeof a));++queries;
 s1=(int)creatures_evolve_to(&wanted,slot,id,context,sanctuary,confirmed);
 s2=(int)creatures_admission_job_commit_evolution(t,&live,context,sanctuary,confirmed);
 assert(s1==s2&&!memcmp(&wanted,&live,sizeof live));assert(!memcmp(&frozen,&original,sizeof frozen));++comparisons;
}
static void populate(unsigned count,unsigned pattern){unsigned i,id,slot;const CreatureForm *f;creatures_roster_init(&source);
 for(i=0;i<count;++i){id=pattern?1+i%128:1;while(!(f=creatures_form(id)))id=id%128+1;
  if(id>=49&&id<=72){unsigned base=49+3*((id-49)/3);slot=creatures_grant(&source,base,50,100,0,0);assert(slot!=255);
   source.instances[slot].trial_flags=3;source.instances[slot].form_id=(CreatureU8)id;source.instances[slot].polarity=f->polarity;
   source.seen[(id-1)>>3]|=(CreatureU8)(1u<<((id-1)&7));source.obtained[(id-1)>>3]|=(CreatureU8)(1u<<((id-1)&7));
  }else assert(creatures_grant(&source,id,50,100,0,0)!=255);
 }
 assert(creatures_roster_validate(&source));
}
int main(void){unsigned count,p,id,i,slot,mask,context;static const unsigned counts[]={0,1,50,88,89,90,159,160};
 static const unsigned levels[]={0,1,27,28,50,51};static const unsigned rewards[]={0,1,4,5,128,129};
 for(count=0;count<sizeof counts/sizeof counts[0];++count)for(p=0;p<2;++p){
  populate(counts[count],p);
  for(id=1;id<=128;++id)if(creatures_form(id)){
   compare_grant(id,50,100,0,0);
   for(i=0;i<6;++i){compare_grant(id,levels[i],i&1?20:101,i&2?CREATURE_FAVORITE:0,rewards[i]);}
  }
  source.next_instance_id=0xffffffffu;compare_grant(49,28,20,0,0);source.rewards[1]|=1;compare_grant(49,28,20,0,9);
 }
 for(id=49;id<=70;id+=3)for(mask=0;mask<4;++mask)for(context=0;context<4;++context){
  populate(89,0);slot=creatures_grant(&source,id,28,45,0,0);assert(slot==89);source.instances[slot].trial_flags=(CreatureU16)mask;
  for(i=0;i<2;++i){compare_evolution(slot,id+1+i,context&1?CREATURE_UNDERWATER_READY:0,context&2,1);compare_evolution(slot,id+1+i,CREATURE_UNDERWATER_READY,1,0);}
 }
 populate(4,1);
 for(i=0;i<sizeof(source);++i){((unsigned char*)&source)[i]^=128;compare_grant(49,28,20,0,0);((unsigned char*)&source)[i]^=128;}
 printf("{\"core_queries\":%u,\"core_commit_differentials\":%u,\"status\":\"pass\"}\n",queries,comparisons);return 0;}
