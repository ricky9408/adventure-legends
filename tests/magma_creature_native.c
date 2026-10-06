/* Actual production core under strict C99 and ASan/UBSan.
 * Fixtures deliberately use the raw historical grant primitive. They are not
 * evidence that a native acquisition route or source transaction is implemented.
 */
#include "creatures.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

#ifndef EXPECT_INVALID_CATALOG
static CreatureRoster roster, before;
static const CreatureEvolution expected_edges[35] = {
    {1,2,12,40,1,1}, {4,5,12,40,2,1}, {7,8,16,55,4,2},
    {10,11,20,60,8,4}, {13,14,15,45,16,8}, {19,20,16,40,32,16},
    {22,23,17,40,64,16}, {73,74,18,45,128,16}, {75,76,18,45,256,16},
    {77,78,20,50,512,16}, {25,26,20,40,1,64}, {28,29,22,45,1,64},
    {79,80,20,40,1,64}, {81,82,22,45,1,64}, {83,84,22,45,1,64},
    {85,86,20,40,1,64}, {87,88,24,45,1,64}, {89,90,22,45,1,64},
    {91,92,24,45,1,64}, {93,94,22,45,1,64},
    {31,32,26,45,1,256}, {32,33,32,60,3,512},
    {34,35,26,45,1,256}, {35,36,32,60,3,512},
    {37,38,26,45,1,256}, {37,39,26,45,2,256},
    {40,41,26,45,1,256}, {40,42,26,45,2,256},
    {43,44,26,45,1,256}, {43,45,26,45,2,256},
    {46,47,26,45,1,256}, {46,48,26,45,2,256},
    {95,96,26,45,1,256}, {97,98,26,45,1,256}, {99,100,26,45,1,256}
};
static const unsigned new_bases[] = {31,34,37,40,43,46,95,97,99};
static const unsigned branches[] = {37,40,43,46};
static const unsigned invalid_values[] = {0,129,255,256,65537,65538,0xffffffffu};

static void unchanged(void) { assert(!memcmp(&roster,&before,sizeof(roster))); }
static unsigned grant(unsigned form) {
    unsigned slot=creatures_grant(&roster,form,50,100,0,0);
    assert(slot<160);
    return slot;
}
static void fresh(void) { creatures_roster_init(&roster); }
static void trial(unsigned slot,unsigned key) {
    const CreatureForm *form=creatures_form(roster.instances[slot].form_id);
    assert(form);
    assert(creatures_mark_trial_qualified(&roster.instances[slot],form->family,key));
}
static void prepare_edge(unsigned form,unsigned mask) {
    const CreatureForm *f;
    fresh();grant(form);f=creatures_form(form);assert(f);
    if (mask==3) { trial(0,1);trial(0,2); }
    else {
        unsigned key=1;
        if (f->family>=13 && f->family<=16 && mask==2) key=2;
        trial(0,key);
    }
    assert(roster.instances[0].trial_flags==mask);
}

static void edge_tests(void) {
    unsigned i,j;
    assert(CREATURE_ENABLED_COUNT==65 && CREATURE_LEARNSET_COUNT==102);
    assert(CREATURE_EVOLUTION_COUNT==35 && CREATURE_ABILITY_COUNT==65);
    assert(CREATURE_CONTENT_REVISION==5 && sizeof(CreatureInstance)==24);
    assert(CREATURE_MAGMA_READY==256 && CREATURE_CALDERA_OPEN==512);
    assert(CREATURE_EVOLUTION_CONTEXT_MASK==1023);
    for (i=0;i<35;++i) {
        const CreatureEvolution *e=&expected_edges[i];
        const CreatureForm *f=creatures_form(e->from),*t=creatures_form(e->to);
        CreatureInstance expected;
        const CreatureEvolution *actual=creatures_evolution_to(e->from,e->to);
        assert(actual && !memcmp(actual,e,sizeof(*e)));
        assert(!memcmp(&creature_evolutions[i],e,sizeof(*e)));
        assert(f && t && f->family==t->family);
        assert((f->field_caps&t->field_caps)==f->field_caps);
        for (j=0;j<f->learnset_count;++j) {
            const CreatureLearn *l=&creature_learnsets[f->learnset_offset+j];
            assert(creatures_command_learned(t->id,l->level,l->ability_id));
        }
        prepare_edge(e->from,e->trial_flag);
        before=roster;
        assert(creatures_can_evolve_to(&roster.instances[0],e->to,e->chapter_flags,1)==CREATURE_EVOLVE_READY);
        assert(creatures_evolve_to(&roster,0,e->to,e->chapter_flags,1,0)==CREATURE_EVOLVE_DEFERRED);unchanged();
        assert(creatures_evolve_to(&roster,0,e->to,0,1,1)==CREATURE_EVOLVE_STORY);unchanged();
        assert(creatures_evolve_to(&roster,0,e->to,e->chapter_flags,0,1)==CREATURE_EVOLVE_SANCTUARY);unchanged();
        assert(creatures_evolve_to(&roster,0,e->to,1024,1,1)==CREATURE_EVOLVE_INVALID);unchanged();
        assert(creatures_evolve_to(&roster,0,e->to,65536u+e->chapter_flags,1,1)==CREATURE_EVOLVE_INVALID);unchanged();
        assert(creatures_evolve_to(&roster,0,e->to+256u,e->chapter_flags,1,1)==CREATURE_EVOLVE_INVALID);unchanged();
        expected=roster.instances[0];expected.form_id=e->to;expected.polarity=t->polarity;
        assert(creatures_evolve_to(&roster,0,e->to,e->chapter_flags,1,1)==CREATURE_EVOLVE_READY);
        assert(!memcmp(&roster.instances[0],&expected,sizeof(expected)));
        assert(creatures_roster_validate(&roster));
        assert(roster.obtained[(e->to-1u)/8]&(1u<<((e->to-1u)%8)));
        assert((f->polarity!=t->polarity)==(e->to==39 || e->to==48));
        prepare_edge(e->from,e->trial_flag);
        roster.instances[0].bond=(CreatureU8)(e->min_bond-1u);before=roster;
        assert(creatures_evolve_to(&roster,0,e->to,e->chapter_flags,1,1)==CREATURE_EVOLVE_BOND);unchanged();
        roster.instances[0].bond=100;roster.instances[0].level=(CreatureU8)(e->min_level-1u);
        roster.instances[0].xp=creatures_xp_threshold(roster.instances[0].level);before=roster;
        assert(creatures_evolve_to(&roster,0,e->to,e->chapter_flags,1,1)==CREATURE_EVOLVE_LEVEL);unchanged();
        roster.instances[0].level=50;roster.instances[0].xp=CREATURE_XP_CAP;roster.instances[0].trial_flags=0;before=roster;
        assert(creatures_evolve_to(&roster,0,e->to,e->chapter_flags,1,1)==CREATURE_EVOLVE_TRIAL);unchanged();
    }
}

static void trial_tests(void) {
    unsigned i,j,base,family;
    for (i=0;i<sizeof(new_bases)/sizeof(new_bases[0]);++i) {
        base=new_bases[i];fresh();grant(base);family=creatures_form(base)->family;
        assert(!creatures_family_trial(base));before=roster;
        for (j=0;j<sizeof(invalid_values)/sizeof(invalid_values[0]);++j) {
            unsigned bad=invalid_values[j];
            assert(!creatures_mark_trial(&roster.instances[0],bad));unchanged();
            assert(!creatures_mark_trial_qualified(&roster.instances[0],family,bad));unchanged();
            assert(!creatures_mark_trial_qualified(&roster.instances[0],bad,1));unchanged();
        }
        for (j=1;j<=1024;j*=2) { assert(!creatures_mark_trial(&roster.instances[0],j));unchanged(); }
        for (j=1;j<=60;++j) if (j!=family) {
            assert(!creatures_mark_trial_qualified(&roster.instances[0],j,1));unchanged();
            assert(!creatures_has_trial_qualified(&roster.instances[0],j,1));unchanged();
        }
        assert(creatures_trial_mask_for_key(family,1)==1);
        if (family==11 || family==12) {
            assert(creatures_trial_mask_for_key(family,2)==2);
            assert(!creatures_mark_trial_qualified(&roster.instances[0],family,2));unchanged();
            trial(0,1);before=roster;
            assert(!creatures_mark_trial_qualified(&roster.instances[0],family,2));unchanged();
            assert(creatures_trial_allowed_mask(base,5)==1);
            roster.instances[0].trial_flags=3;
            assert(!creatures_instance_validate(&roster.instances[0]));
            assert(!creatures_instance_validate_revision(&roster.instances[0],5));
            roster=before;
            assert(creatures_evolve_to(&roster,0,base+1,256,1,1)==CREATURE_EVOLVE_READY);
            assert(creatures_trial_allowed_mask(base+1,5)==3);
            trial(0,2);assert(roster.instances[0].trial_flags==3);
            roster.instances[0].trial_flags=2;
            assert(!creatures_instance_validate(&roster.instances[0]));
        } else if (family>=13 && family<=16) {
            trial(0,2);assert(roster.instances[0].trial_flags==2);
            assert(creatures_instance_validate(&roster.instances[0]));
            trial(0,1);assert(roster.instances[0].trial_flags==3);
        } else {
            assert(!creatures_trial_mask_for_key(family,2));
            assert(!creatures_mark_trial_qualified(&roster.instances[0],family,2));unchanged();trial(0,1);
        }
    }
    fresh();grant(1);assert(creatures_family_trial(1)==1);before=roster;
    assert(!creatures_mark_trial(&roster.instances[0],3));unchanged();
    assert(creatures_mark_trial(&roster.instances[0],1));
    before=roster;assert(!creatures_mark_trial_qualified(&roster.instances[0],11,1));unchanged();
}

static void branch_tests(void) {
    unsigned i,target;
    for (i=0;i<4;++i) {
        unsigned base=branches[i];
        assert(creatures_evolution_count(base)==2 && !creatures_evolution(base));
        assert(creatures_evolution_at(base,0)->to==base+1);
        assert(creatures_evolution_at(base,1)->to==base+2);
        assert(!creatures_evolution_at(base,2) && !creatures_evolution_at(base,0xffffffffu));
        for (target=base+1;target<=base+2;++target) {
            fresh();grant(base);trial(0,target-base);before=roster;
            assert(creatures_can_evolve(&roster.instances[0],256,1)==CREATURE_EVOLVE_AMBIGUOUS);
            assert(creatures_evolve(&roster,0,256,1,1)==CREATURE_EVOLVE_AMBIGUOUS);unchanged();
            assert(creatures_defer_evolution(&roster.instances[0])==CREATURE_EVOLVE_DEFERRED);unchanged();
            assert(creatures_evolve_to(&roster,0,target,256,1,0)==CREATURE_EVOLVE_DEFERRED);unchanged();
            assert(creatures_can_evolve_to(&roster.instances[0],base+3-(target-base),256,1)==CREATURE_EVOLVE_TRIAL);
            assert(creatures_evolve_to(&roster,0,target,256,1,1)==CREATURE_EVOLVE_READY);
        }
        /* Two copies choosing the same branch preserve enough reserve to
         * acquire a real third base, then retain both eventual alternatives. */
        fresh();
        for (target=0;target<3;++target) {
            unsigned slot=255,status=creatures_grant_admitted(&roster,base,50,100,0,0,&slot);
            assert(status==CREATURE_ADMISSION_READY && slot==target);
            trial(slot,target==2 ? 2 : 1);
            assert(creatures_evolve_to(&roster,slot,base+(target==2 ? 2 : 1),256,1,1)==CREATURE_EVOLVE_READY);
            assert(roster.instances[slot].instance_id==slot+1);
        }
        assert(roster.instances[0].form_id==base+1 && roster.instances[1].form_id==base+1 && roster.instances[2].form_id==base+2);
    }
}

/* Pinned final topology, including all currently disabled destinations. */
static const unsigned char expected_topology[129][2] = {
    {0,0},
    {1,1}, /* form1 */
    {1,1}, /* form2 */
    {1,1}, /* form3 */
    {2,1}, /* form4 */
    {2,1}, /* form5 */
    {2,1}, /* form6 */
    {3,1}, /* form7 */
    {3,1}, /* form8 */
    {3,1}, /* form9 */
    {4,1}, /* form10 */
    {4,1}, /* form11 */
    {4,1}, /* form12 */
    {5,1}, /* form13 */
    {5,1}, /* form14 */
    {5,1}, /* form15 */
    {6,1}, /* form16 */
    {6,1}, /* form17 */
    {6,1}, /* form18 */
    {7,1}, /* form19 */
    {7,1}, /* form20 */
    {7,1}, /* form21 */
    {8,1}, /* form22 */
    {8,1}, /* form23 */
    {8,1}, /* form24 */
    {9,1}, /* form25 */
    {9,1}, /* form26 */
    {9,1}, /* form27 */
    {10,1}, /* form28 */
    {10,1}, /* form29 */
    {10,1}, /* form30 */
    {11,1}, /* form31 */
    {11,1}, /* form32 */
    {11,1}, /* form33 */
    {12,1}, /* form34 */
    {12,1}, /* form35 */
    {12,1}, /* form36 */
    {13,3}, /* form37 */
    {13,1}, /* form38 */
    {13,2}, /* form39 */
    {14,3}, /* form40 */
    {14,1}, /* form41 */
    {14,2}, /* form42 */
    {15,3}, /* form43 */
    {15,1}, /* form44 */
    {15,2}, /* form45 */
    {16,3}, /* form46 */
    {16,1}, /* form47 */
    {16,2}, /* form48 */
    {17,3}, /* form49 */
    {17,1}, /* form50 */
    {17,2}, /* form51 */
    {18,3}, /* form52 */
    {18,1}, /* form53 */
    {18,2}, /* form54 */
    {19,3}, /* form55 */
    {19,1}, /* form56 */
    {19,2}, /* form57 */
    {20,3}, /* form58 */
    {20,1}, /* form59 */
    {20,2}, /* form60 */
    {21,3}, /* form61 */
    {21,1}, /* form62 */
    {21,2}, /* form63 */
    {22,3}, /* form64 */
    {22,1}, /* form65 */
    {22,2}, /* form66 */
    {23,3}, /* form67 */
    {23,1}, /* form68 */
    {23,2}, /* form69 */
    {24,3}, /* form70 */
    {24,1}, /* form71 */
    {24,2}, /* form72 */
    {25,1}, /* form73 */
    {25,1}, /* form74 */
    {26,1}, /* form75 */
    {26,1}, /* form76 */
    {27,1}, /* form77 */
    {27,1}, /* form78 */
    {28,1}, /* form79 */
    {28,1}, /* form80 */
    {29,1}, /* form81 */
    {29,1}, /* form82 */
    {30,1}, /* form83 */
    {30,1}, /* form84 */
    {31,1}, /* form85 */
    {31,1}, /* form86 */
    {32,1}, /* form87 */
    {32,1}, /* form88 */
    {33,1}, /* form89 */
    {33,1}, /* form90 */
    {34,1}, /* form91 */
    {34,1}, /* form92 */
    {35,1}, /* form93 */
    {35,1}, /* form94 */
    {36,1}, /* form95 */
    {36,1}, /* form96 */
    {37,1}, /* form97 */
    {37,1}, /* form98 */
    {38,1}, /* form99 */
    {38,1}, /* form100 */
    {39,1}, /* form101 */
    {39,1}, /* form102 */
    {40,1}, /* form103 */
    {40,1}, /* form104 */
    {41,1}, /* form105 */
    {41,1}, /* form106 */
    {42,1}, /* form107 */
    {42,1}, /* form108 */
    {43,1}, /* form109 */
    {43,1}, /* form110 */
    {44,1}, /* form111 */
    {44,1}, /* form112 */
    {45,1}, /* form113 */
    {46,1}, /* form114 */
    {47,1}, /* form115 */
    {48,1}, /* form116 */
    {49,1}, /* form117 */
    {50,1}, /* form118 */
    {51,1}, /* form119 */
    {52,1}, /* form120 */
    {53,1}, /* form121 */
    {54,1}, /* form122 */
    {55,1}, /* form123 */
    {56,1}, /* form124 */
    {57,1}, /* form125 */
    {58,1}, /* form126 */
    {59,1}, /* form127 */
    {60,1}, /* form128 */
};

static CreatureInstance fixture_instances[129];
static void init_fixtures(void) {
    unsigned id;
    for (id=1;id<=128;++id) if (creatures_form(id)) {
        fresh();grant(id);fixture_instances[id]=roster.instances[0];
    }
}
static void fixture(const unsigned *forms,unsigned count) {
    unsigned i;
    assert(count<=160);fresh();
    for (i=0;i<count;++i) {
        unsigned id=forms[i];assert(id && id<=128 && fixture_instances[id].form_id);
        roster.instances[i]=fixture_instances[id];roster.instances[i].instance_id=i+1;
        roster.seen[(id-1)/8]|=(CreatureU8)(1u<<((id-1)%8));
        roster.obtained[(id-1)/8]|=(CreatureU8)(1u<<((id-1)%8));
        if (i<4) roster.party[i]=(CreatureU8)i;
    }
    roster.selected_party=count ? 0 : CREATURE_EMPTY_SLOT;roster.next_instance_id=count+1;
    assert(creatures_roster_validate(&roster));
}

/* Independent augmenting-path maximum matching, rather than the production
 * capped-count/union formula. Each actual retained instance owns one node. */
static unsigned match_forms[161];
static int matched[120];
static unsigned char visited[120];
static int augment(unsigned instance) {
    unsigned form=match_forms[instance],family=expected_topology[form][0];
    unsigned mask=expected_topology[form][1],bit;
    for (bit=0;bit<2;++bit) if (mask&(1u<<bit)) {
        unsigned terminal=2*(family-1)+bit;
        if (visited[terminal]) continue;
        visited[terminal]=1;
        if (matched[terminal]<0 || augment((unsigned)matched[terminal])) {
            matched[terminal]=(int)instance;return 1;
        }
    }
    return 0;
}
static void reference_coverage(const CreatureRoster *r,unsigned replaced,unsigned target,int append,CreatureCoverage *out) {
    unsigned slot,count=0,viable=0;
    memset(out,0,sizeof(*out));
    for (slot=0;slot<160;++slot) if (r->instances[slot].form_id)
        match_forms[count++]=slot==replaced ? target : r->instances[slot].form_id;
    if (append) match_forms[count++]=target;
    for (slot=0;slot<120;++slot) matched[slot]=-1;
    for (slot=0;slot<count;++slot) {
        memset(visited,0,sizeof(visited));viable+=(unsigned)augment(slot);
    }
    out->occupied=(CreatureU16)count;out->viable=(CreatureU16)viable;
    out->excess=(CreatureU16)(count-viable);out->free_slots=(CreatureU16)(160-count);
    out->missing_opportunities=(CreatureU16)(72-viable);out->admission_safe=(CreatureU16)(count-viable<=88);
}
static unsigned coverage_checks,query_checks;
static void coverage_check(unsigned count,unsigned viable) {
    CreatureCoverage actual,expected;
    memset(&actual,0xa5,sizeof(actual));assert(creatures_collection_coverage(&roster,&actual));
    reference_coverage(&roster,255,0,0,&expected);
    assert(!memcmp(&actual,&expected,sizeof(actual)));
    assert(actual.occupied==count && actual.viable==viable);
    ++coverage_checks;
}
static unsigned reference_admission(const CreatureCoverage *a,const CreatureCoverage *b,int evolution) {
    if (a->occupied==160 && !evolution) return CREATURE_ADMISSION_FULL;
    if (a->admission_safe) {
        if (b->excess<=88) return CREATURE_ADMISSION_READY;
    } else if (b->excess<=a->excess && b->viable>=a->viable)
        return CREATURE_ADMISSION_GRANDFATHERED_READY;
    return evolution ? CREATURE_ADMISSION_COVERAGE_LOSS : CREATURE_ADMISSION_RESERVED;
}
static unsigned query_grant(unsigned form) {
    CreatureAdmission actual,expected;
    unsigned status,want;
    before=roster;memset(&actual,0xa5,sizeof(actual));
    reference_coverage(&roster,255,0,0,&expected.before);
    reference_coverage(&roster,255,form,1,&expected.after);
    want=reference_admission(&expected.before,&expected.after,0);
    status=creatures_admission_query_grant(&roster,form,&actual);unchanged();
    assert(status==want);
    /* A full candidate is rejected before representing an impossible161-slot
     * roster. For physically possible candidates, exact details must agree. */
    if (status!=CREATURE_ADMISSION_FULL) assert(!memcmp(&actual,&expected,sizeof(actual)));
    ++query_checks;return status;
}
static unsigned query_evolution(unsigned slot,unsigned form) {
    CreatureAdmission actual,expected;
    unsigned status,want;
    before=roster;memset(&actual,0xa5,sizeof(actual));
    reference_coverage(&roster,255,0,0,&expected.before);
    reference_coverage(&roster,slot,form,0,&expected.after);
    want=reference_admission(&expected.before,&expected.after,1);
    status=creatures_admission_query_evolution(&roster,slot,form,&actual);unchanged();
    assert(status==want);assert(!memcmp(&actual,&expected,sizeof(actual)));
    ++query_checks;return status;
}

static void topology_and_invalid_tests(void) {
    unsigned i;
    CreatureCoverage detail,zero;
    CreatureAdmission admission,zero_admission;
    memset(&zero,0,sizeof(zero));memset(&zero_admission,0,sizeof(zero_admission));
    for (i=1;i<=128;++i) {
        assert(creatures_terminal_family(i)==expected_topology[i][0]);
        assert(creatures_terminal_mask(i)==expected_topology[i][1]);
    }
    for (i=0;i<sizeof(invalid_values)/sizeof(invalid_values[0]);++i) {
        unsigned id=invalid_values[i];
        assert(!creatures_terminal_family(id));assert(!creatures_terminal_mask(id));
    }
    assert(CREATURE_TERMINAL_OPPORTUNITIES==72 && CREATURE_EXTRA_COPY_BUDGET==88);
    for (i=0;i<12;++i) assert(creatures_admission_allowed((enum CreatureAdmissionStatus)i)==(i<2));
    memset(&detail,0xa5,sizeof(detail));assert(!creatures_collection_coverage(0,&detail));assert(!memcmp(&detail,&zero,sizeof(detail)));
    fresh();coverage_check(0,0);
    for (i=1;i<=128;++i) if (!creatures_form(i)) {
        before=roster;
        assert(creatures_admission_query_grant(&roster,i,0)==CREATURE_ADMISSION_INVALID);unchanged();
    }
    grant(37);roster.instances[0].polarity^=1;before=roster;
    memset(&detail,0xa5,sizeof(detail));assert(!creatures_collection_coverage(&roster,&detail));unchanged();
    assert(!memcmp(&detail,&zero,sizeof(detail)));
    memset(&admission,0xa5,sizeof(admission));
    assert(creatures_admission_query_grant(&roster,31,&admission)==CREATURE_ADMISSION_INVALID);unchanged();
    assert(!memcmp(&admission,&zero_admission,sizeof(admission)));
    fresh();grant(1);grant(4);roster.instances[1].instance_id=roster.instances[0].instance_id;
    assert(!creatures_collection_coverage(&roster,&detail));
    fresh();grant(37);before=roster;
    assert(creatures_admission_query_evolution(&roster,0,40,0)==CREATURE_ADMISSION_INVALID);unchanged();
    assert(creatures_admission_query_evolution(&roster,160,38,0)==CREATURE_ADMISSION_INVALID);unchanged();
    assert(creatures_admission_query_evolution(&roster,0,38+256u,0)==CREATURE_ADMISSION_INVALID);unchanged();
}

static void multiset_matching_tests(void) {
    unsigned family,bases,a,b,n,i,padding,forms[160];
    static const unsigned pads[]={0,87,88,89,140};
    for (family=0;family<4;++family) {
        unsigned base=branches[family];
        for (bases=0;bases<=6;++bases) for (a=0;a+bases<=6;++a) for (b=0;a+b+bases<=6;++b) {
            unsigned union_count=(bases+a>0)+(bases+b>0),size=bases+a+b;
            unsigned viable=size<union_count ? size : union_count;
            for (padding=0;padding<sizeof(pads)/sizeof(pads[0]);++padding) {
                n=0;
                for(i=0;i<bases;++i)forms[n++]=base;
                for(i=0;i<a;++i)forms[n++]=base+1;
                for(i=0;i<b;++i)forms[n++]=base+2;
                for(i=0;i<pads[padding];++i)forms[n++]=1;
                fixture(forms,n);coverage_check(n,viable+(pads[padding]>0));
                query_grant(base);query_grant(base+1);query_grant(base+2);query_grant(31);
                if(bases) {query_evolution(0,base+1);query_evolution(0,base+2);}
            }
        }
    }
}

static void capacity_and_atomicity_tests(void) {
    unsigned forms[160],i,slot,status;
    CreatureCoverage coverage;
    for(i=0;i<160;++i)forms[i]=1;
    fixture(forms,89);coverage_check(89,1);
    before=roster;slot=0;
    assert(creatures_grant_admitted(&roster,1,50,100,0,9,&slot)==CREATURE_ADMISSION_RESERVED);
    assert(slot==255);unchanged();
    /* Old history claiming every enabled form provides no terminal coverage. */
    for(i=1;i<=128;++i)if(creatures_form(i)) {
        roster.seen[(i-1)/8]|=(CreatureU8)(1u<<((i-1)%8));
        roster.obtained[(i-1)/8]|=(CreatureU8)(1u<<((i-1)%8));
    }
    coverage_check(89,1);assert(query_grant(1)==CREATURE_ADMISSION_RESERVED);
    assert(creatures_grant_admitted(&roster,37,50,100,0,9,&slot)==CREATURE_ADMISSION_READY && slot==89);
    assert(creatures_grant_admitted(&roster,37,50,100,0,0,&slot)==CREATURE_ADMISSION_READY && slot==90);
    coverage_check(91,3);trial(89,1);trial(89,2);trial(90,1);trial(90,2);
    assert(creatures_evolve_to(&roster,89,38,256,1,1)==CREATURE_EVOLVE_READY);
    assert(query_evolution(90,38)==CREATURE_ADMISSION_COVERAGE_LOSS);
    before=roster;
    assert(creatures_can_evolve_to(&roster.instances[90],38,256,1)==CREATURE_EVOLVE_READY);unchanged();
    assert(creatures_can_evolve_roster_to(&roster,90,38,256,1)==CREATURE_EVOLVE_COLLECTION_RESERVED);unchanged();
    assert(creatures_evolve_to(&roster,90,38,256,1,0)==CREATURE_EVOLVE_DEFERRED);unchanged();
    assert(creatures_evolve_to(&roster,90,38,256,1,1)==CREATURE_EVOLVE_COLLECTION_RESERVED);unchanged();
    assert(roster.instances[90].trial_flags==3);
    assert(creatures_grant_admitted(&roster,37,50,100,0,9,&slot)==CREATURE_ADMISSION_ALREADY_CLAIMED);unchanged();
    assert(slot==255);
    assert(creatures_evolve_to(&roster,90,39,256,1,1)==CREATURE_EVOLVE_READY);coverage_check(91,3);
    /* At E87 a duplicate choice may consume the last extra-copy allowance,
     * and a later real base still restores the missing branch coverage. */
    fixture(forms,88);grant(38);slot=grant(37);trial(slot,1);trial(slot,2);
    assert(query_evolution(slot,38)==CREATURE_ADMISSION_READY);
    assert(creatures_evolve_to(&roster,slot,38,256,1,1)==CREATURE_EVOLVE_READY);coverage_check(90,2);
    assert(creatures_grant_admitted(&roster,37,50,100,0,0,&slot)==CREATURE_ADMISSION_READY);
    trial(slot,2);assert(creatures_evolve_to(&roster,slot,39,256,1,1)==CREATURE_EVOLVE_READY);coverage_check(91,3);
    /* Preserving another flexible base makes an otherwise duplicate choice
     * legal at E88; reject no more than the exact matching invariant requires. */
    fixture(forms,88);grant(38);slot=grant(37);grant(37);trial(slot,1);
    coverage_check(91,3);assert(query_evolution(slot,38)==CREATURE_ADMISSION_READY);
    assert(creatures_evolve_to(&roster,slot,38,256,1,1)==CREATURE_EVOLVE_READY);
    /* Grandfathered excess does not leak into old OR current legality. */
    fixture(forms,150);coverage_check(150,1);
    for(i=1;i<=5;++i)assert(creatures_roster_validate_revision(&roster,i));
    assert(query_grant(1)==CREATURE_ADMISSION_RESERVED);
    assert(query_grant(31)==CREATURE_ADMISSION_GRANDFATHERED_READY);
    status=creatures_grant_admitted(&roster,31,50,100,0,0,&slot);
    assert(status==CREATURE_ADMISSION_GRANDFATHERED_READY && slot==150);coverage_check(151,2);
    trial(slot,1);assert(creatures_evolve_to(&roster,slot,32,256,1,1)==CREATURE_EVOLVE_READY);
    assert(creatures_collection_coverage(&roster,&coverage) && !coverage.admission_safe);
    fixture(forms,160);coverage_check(160,1);
    for(i=1;i<=5;++i)assert(creatures_roster_validate_revision(&roster,i));
    before=roster;assert(query_grant(31)==CREATURE_ADMISSION_FULL);
    assert(creatures_grant_admitted(&roster,31,50,100,0,12,&slot)==CREATURE_ADMISSION_FULL);unchanged();
    assert(slot==255);trial(0,1);
    assert(creatures_evolve_to(&roster,0,2,1,1,1)==CREATURE_EVOLVE_READY);coverage_check(160,1);
    fresh();grant(1);roster.next_instance_id=0xffffffffu;before=roster;
    assert(creatures_grant_admitted(&roster,31,50,100,0,0,&slot)==CREATURE_ADMISSION_ID_EXHAUSTED);unchanged();
    /* Full/overbudget retries of a claimed receipt remain idempotent. */
    fixture(forms,160);roster.rewards[1]|=1u;before=roster;
    assert(creatures_grant_admitted(&roster,1,50,100,0,9,&slot)==CREATURE_ADMISSION_ALREADY_CLAIMED);unchanged();
}

static void all_branch_orders_tests(void) {
    unsigned a,b,c,d,directions,orders=0;
    for(a=0;a<4;++a)for(b=0;b<4;++b)if(b!=a)for(c=0;c<4;++c)if(c!=a && c!=b)for(d=0;d<4;++d)if(d!=a && d!=b && d!=c) {
        unsigned permutation[4];permutation[0]=a;permutation[1]=b;permutation[2]=c;permutation[3]=d;
        for(directions=0;directions<16;++directions) {
            unsigned j,slot;
            fresh();
            for(j=0;j<4;++j) {
                unsigned branch=permutation[j],base=branches[branch],key=1+((directions>>branch)&1u);
                assert(creatures_grant_admitted(&roster,base,50,100,0,0,&slot)==CREATURE_ADMISSION_READY);
                trial(slot,key);assert(creatures_evolve_to(&roster,slot,base+key,256,1,1)==CREATURE_EVOLVE_READY);
                assert(creatures_grant_admitted(&roster,base,50,100,0,0,&slot)==CREATURE_ADMISSION_READY);
                trial(slot,3-key);assert(creatures_evolve_to(&roster,slot,base+3-key,256,1,1)==CREATURE_EVOLVE_READY);
            }
            coverage_check(8,8);++orders;
        }
    }
    assert(orders==384);
}

static void thirteen_individual_collection_tests(void) {
    unsigned i,slot,id;
    CreatureCoverage coverage;
    fresh();
    for(i=0;i<sizeof(new_bases)/sizeof(new_bases[0]);++i) {
        unsigned base=new_bases[i];
        assert(creatures_grant_admitted(&roster,base,50,100,0,0,&slot)==CREATURE_ADMISSION_READY);
        trial(slot,1);assert(creatures_evolve_to(&roster,slot,base+1,256,1,1)==CREATURE_EVOLVE_READY);
        if(base==31 || base==34) {
            unsigned command=roster.instances[slot].equipped[0];
            trial(slot,2);assert(roster.instances[slot].trial_flags==3);
            assert(creatures_evolve_to(&roster,slot,base+2,512,1,1)==CREATURE_EVOLVE_READY);
            assert(roster.instances[slot].equipped[0]==command);
            assert(creatures_equip(&roster.instances[slot],1,creatures_form(base+2)->signature_ability));
        } else if(base>=37 && base<=46) {
            assert(creatures_grant_admitted(&roster,base,50,100,0,0,&slot)==CREATURE_ADMISSION_READY);
            trial(slot,2);assert(creatures_evolve_to(&roster,slot,base+2,256,1,1)==CREATURE_EVOLVE_READY);
        }
    }
    coverage_check(13,13);assert(roster.next_instance_id==14);
    for(id=31;id<=100;++id)if(id<=48 || id>=95) {
        assert(roster.seen[(id-1)/8]&(1u<<((id-1)%8)));
        assert(roster.obtained[(id-1)/8]&(1u<<((id-1)%8)));
    }
    assert(creatures_roster_validate(&roster));
    assert(creatures_collection_coverage(&roster,&coverage));
    assert(coverage.free_slots==147 && coverage.missing_opportunities==59);
}

static void future_reserve_tests(void) {
    static const unsigned remaining_roots[]={4,7,10,13,16,19,22,73,75,77,25,28,79,81,83,85,87,89,91,93,
        31,34,37,37,40,40,43,43,46,46,95,97,99};
    unsigned forms[89],i,slot;
    CreatureCoverage coverage;
    for(i=0;i<89;++i)forms[i]=1;
    fixture(forms,89);
    for(i=0;i<sizeof(remaining_roots)/sizeof(remaining_roots[0]);++i) {
        assert(creatures_grant_admitted(&roster,remaining_roots[i],50,100,0,0,&slot)==CREATURE_ADMISSION_READY);
        assert(slot==89+i);
    }
    coverage_check(122,34);
    assert(creatures_collection_coverage(&roster,&coverage));
    assert(coverage.excess==88 && coverage.free_slots==38 && coverage.missing_opportunities==38);
    /* Those38 physically empty slots are reserved for future outcomes even
     * though no future form is enabled in this content revision. */
    for(i=1;i<=128;++i)if(creatures_form(i)) {
        before=roster;
        assert(query_grant(i)==CREATURE_ADMISSION_RESERVED);unchanged();
    }
}

static unsigned random_state=0x4d41474du;
static unsigned random_next(void) {random_state=random_state*1664525u+1013904223u;return random_state;}
static void randomized_transition_tests(void) {
    unsigned sequence,step;
    for(sequence=0;sequence<200;++sequence) {
        fresh();
        for(step=0;step<220;++step) {
            CreatureCoverage a,b;
            unsigned count=creatures_roster_count(&roster),slot,status,base=branches[(random_next()>>16)%4];
            assert(creatures_collection_coverage(&roster,&a));
            if(count && (random_next()>>16)%3==0) {
                slot=(random_next()>>16)%count;
                if(creatures_evolution_count(roster.instances[slot].form_id)==2) {
                    unsigned target=roster.instances[slot].form_id+1+(random_next()>>16)%2;
                    trial(slot,1);trial(slot,2);status=query_evolution(slot,target);before=roster;
                    if(creatures_admission_allowed((enum CreatureAdmissionStatus)status)) {
                        assert(creatures_evolve_to(&roster,slot,target,256,1,1)==CREATURE_EVOLVE_READY);
                    } else {
                        assert(creatures_evolve_to(&roster,slot,target,256,1,1)==CREATURE_EVOLVE_COLLECTION_RESERVED);unchanged();
                    }
                }
            } else {
                unsigned form=(random_next()>>16)%5 ? base : 1;
                status=query_grant(form);before=roster;
                if(creatures_admission_allowed((enum CreatureAdmissionStatus)status)) {
                    assert(creatures_grant_admitted(&roster,form,50,100,0,0,&slot)==status);
                    assert(slot==count && roster.instances[slot].instance_id==before.next_instance_id);
                } else {
                    assert(creatures_grant_admitted(&roster,form,50,100,0,0,&slot)==status);unchanged();assert(slot==255);
                }
            }
            assert(creatures_collection_coverage(&roster,&b) && b.admission_safe);
            assert(b.free_slots>=b.missing_opportunities);
            assert(creatures_roster_validate(&roster));
        }
    }
}
#endif

int main(void) {
#ifdef EXPECT_INVALID_CATALOG
    assert(!creatures_catalog_validate());
#else
    assert(creatures_catalog_validate());
    edge_tests();trial_tests();branch_tests();init_fixtures();topology_and_invalid_tests();
    multiset_matching_tests();capacity_and_atomicity_tests();all_branch_orders_tests();thirteen_individual_collection_tests();future_reserve_tests();randomized_transition_tests();
    printf("Magma native:35 edges,384 complete branch orders,%u coverage and %u admission comparisons passed\n",coverage_checks,query_checks);
#endif
    return 0;
}
