#include "creatures.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static CreatureRoster live, frozen, expected, original;
static unsigned comparisons;
static unsigned complete(CreatureU32 token,unsigned budget) {
    unsigned steps=0;int result;
    do { result=creatures_admission_job_step(token,budget);assert(result>=0);assert(++steps<=160); } while(!result);
    return steps;
}
static void fresh(unsigned count) {
    unsigned i;
    creatures_roster_init(&live);
    for(i=0;i<count;++i)assert(creatures_grant(&live,1,50,100,0,0)==i);
}
static void check_grant(unsigned target,unsigned level,unsigned bond,unsigned flags,unsigned reward) {
    CreatureAdmission a,b;
    CreatureU32 token;
    unsigned slot=0,expected_slot=0;
    enum CreatureAdmissionStatus status,wanted;
    original=live;frozen=live;expected=live;
    wanted=creatures_admission_query_grant(&expected,target,&a);
    token=creatures_admission_job_begin(&frozen,target,255);assert(token);
    assert(creatures_admission_job_result(token,0)==CREATURE_ADMISSION_INVALID);
    complete(token,1+(comparisons%4));
    status=creatures_admission_job_result(token,&b);
    assert(status==wanted && !memcmp(&a,&b,sizeof(a)));
    wanted=creatures_grant_admitted(&expected,target,level,bond,flags,reward,&expected_slot);
    status=creatures_admission_job_commit_grant(token,&live,level,bond,flags,reward,&slot);
    assert(status==wanted && slot==expected_slot && !memcmp(&live,&expected,sizeof(live)));
    assert(!memcmp(&frozen,&original,sizeof(frozen)));
    original=live;assert(creatures_admission_job_commit_grant(token,&live,level,bond,flags,reward,&slot)==CREATURE_ADMISSION_INVALID);
    assert(!memcmp(&live,&original,sizeof(live)));++comparisons;
}
static void check_evolution(unsigned target,unsigned context,int sanctuary,int confirmed) {
    CreatureAdmission a,b;
    unsigned wanted,status;
    CreatureU32 token;
    original=live;frozen=live;expected=live;
    wanted=creatures_admission_query_evolution(&expected,0,target,&a);
    token=creatures_admission_job_begin(&frozen,target,0);assert(token);complete(token,4);
    status=creatures_admission_job_result(token,&b);
    assert(status==wanted && !memcmp(&a,&b,sizeof(a)));
    wanted=creatures_evolve_to(&expected,0,target,context,sanctuary,confirmed);
    status=creatures_admission_job_commit_evolution(token,&live,context,sanctuary,confirmed);
    assert(status==wanted && !memcmp(&live,&expected,sizeof(live)));
    assert(!memcmp(&frozen,&original,sizeof(frozen)));
    original=live;assert(creatures_admission_job_commit_evolution(token,&live,context,sanctuary,confirmed)==CREATURE_EVOLVE_INVALID);
    assert(!memcmp(&live,&original,sizeof(live)));++comparisons;
}
static void invalid_and_stale(void) {
    CreatureU32 token,previous;
    unsigned i,slot;
    fresh(1);frozen=live;
    assert(!creatures_admission_job_begin(0,49,255));
    assert(!creatures_admission_job_begin(&frozen,65585u,255));
    assert(!creatures_admission_job_begin(&frozen,49,65535u));
    token=creatures_admission_job_begin(&frozen,49,255);assert(token);
    assert(creatures_admission_job_step(token,0)==-1 && creatures_admission_job_step(token,5)==-1);
    assert(creatures_admission_job_step(token,0xffffffffu)==-1);
    assert(creatures_admission_job_commit_grant(token,&live,28,20,0,0,&slot)==CREATURE_ADMISSION_INVALID);
    token=creatures_admission_job_begin(&frozen,49,255);complete(token,4);
    assert(creatures_admission_job_commit_grant(token,&frozen,28,20,0,0,&slot)==CREATURE_ADMISSION_INVALID);
    for(i=0;i<sizeof(live);++i) {
        unsigned char *bytes=(unsigned char *)&live;
        fresh(1);frozen=live;token=creatures_admission_job_begin(&frozen,49,255);complete(token,4);
        bytes[i]^=1;original=live;
        assert(creatures_admission_job_commit_grant(token,&live,28,20,0,0,&slot)==CREATURE_ADMISSION_INVALID);
        assert(!memcmp(&live,&original,sizeof(live)));
    }
    fresh(1);frozen=live;previous=creatures_admission_job_begin(&frozen,49,255);
    token=creatures_admission_job_begin(&frozen,52,255);assert(token && token!=previous);
    assert(creatures_admission_job_step(previous,4)==-1);complete(token,4);
    assert(creatures_admission_job_commit_grant(previous,&live,28,20,0,0,&slot)==CREATURE_ADMISSION_INVALID);
    assert(creatures_admission_job_commit_grant(token,&live,28,20,0,0,&slot)==CREATURE_ADMISSION_READY);
    frozen=live;token=creatures_admission_job_begin(&frozen,55,255);complete(token,4);creatures_admission_job_cancel();
    original=live;assert(creatures_admission_job_commit_grant(token,&live,28,20,0,0,&slot)==CREATURE_ADMISSION_INVALID);assert(!memcmp(&live,&original,sizeof(live)));
}
int main(void) {
    unsigned count,id,mask,j;
    static const unsigned counts[]={0,1,4,50,88,89,90,159,160};
    assert(creatures_admission_job_bytes()<=196);
    for(count=0;count<sizeof(counts)/sizeof(counts[0]);++count) {
        for(id=49;id<=72;++id) {fresh(counts[count]);check_grant(id,28,20,0,0);}
        fresh(counts[count]);live.next_instance_id=0xffffffffu;check_grant(49,28,20,0,0);
        fresh(counts[count]);live.rewards[1]|=1;check_grant(49,28,20,0,9);
    }
    for(id=49;id<=70;id+=3)for(mask=0;mask<4;++mask)for(j=0;j<8;++j) {
        fresh(0);assert(creatures_grant(&live,id,28,45,0,0)==0);live.instances[0].trial_flags=(CreatureU16)mask;
        check_evolution(id+1+(j&1),j&2 ? 1024:0,!(j&4),1);
        fresh(0);assert(creatures_grant(&live,id,28,45,0,0)==0);live.instances[0].trial_flags=(CreatureU16)mask;
        check_evolution(id+1+(j&1),1024,1,0);
    }
    /* Every byte can hold malformed record/header evidence; job must match the
     * synchronous validator and preserve exact rejection bytes/precedence. */
    for(j=0;j<sizeof(live);++j) {fresh(2);((unsigned char *)&live)[j]^=0x80;check_grant(49,28,20,0,0);}
    invalid_and_stale();printf("Bounded admission:%u exact synchronous differentials,all4140 stale-byte denials,once-only tokens passed\n",comparisons);
    return 0;
}
