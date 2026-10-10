/* Actual core assertions, including exhaustive u16 trial masks. Host evidence
 * only: these fixtures never establish controller-earned native acquisition. */
#include "creatures.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static CreatureRoster roster, before;
static void unchanged(void) { assert(!memcmp(&roster,&before,sizeof(roster))); }
static unsigned grant(unsigned id) {
    unsigned slot=creatures_grant(&roster,id,50,100,0,0);
    assert(slot<160);return slot;
}
static void tables_and_masks(void) {
    unsigned i,j,mask;
    assert(creatures_catalog_validate());
    assert(CREATURE_CONTENT_REVISION==8 && CREATURE_ENABLED_COUNT==120);
    assert(CREATURE_LEARNSET_COUNT==200 && CREATURE_EVOLUTION_COUNT==68 && CREATURE_ABILITY_COUNT==120);
    assert(sizeof(CreatureInstance)==24 && CREATURE_EVOLUTION_CONTEXT_MASK==32767);
    for(i=0;i<8;++i) {
        unsigned base=49+3*i, family=17+i;
        const CreatureForm *f=creatures_form(base);
        assert(f && f->family==family && f->tier==1 && f->signature_ability==67+3*i);
        assert(creatures_evolution_count(base)==2 && !creatures_evolution(base));
        assert(creatures_family_trial(base)==0);
        assert(creatures_trial_mask_for_key(family,1)==1 && creatures_trial_mask_for_key(family,2)==2);
        assert(!creatures_trial_mask_for_key(family,3));
        for(j=0;j<3;++j) {
            CreatureInstance c;
            const CreatureForm *form=creatures_form(base+j);
            memset(&c,0,sizeof(c));c.form_id=(CreatureU8)(base+j);c.flags=1;c.instance_id=1;
            c.level=28;c.xp=creatures_xp_threshold(28);c.bond=45;c.polarity=form->polarity;c.equipped[0]=(CreatureU8)(67+3*i);
            assert(creatures_command_learned(base+j,1,67+3*i));
            for(mask=0;mask<=65535u;++mask) {
                int expected=mask<4 && (!j || (mask & j));
                c.trial_flags=(CreatureU16)mask;
                assert(creatures_instance_validate(&c)==!!expected);
                assert(creatures_instance_validate_revision(&c,6)==!!expected);
                assert(creatures_instance_validate_revision(&c,7)==!!expected);
                assert(!creatures_instance_validate_revision(&c,5));
            }
            c.trial_flags=3;
            if(j) { c.bond=44;assert(!creatures_instance_validate(&c));c.bond=45;c.level=27;c.xp=creatures_xp_threshold(27);assert(!creatures_instance_validate(&c)); }
        }
        for(j=1;j<=2;++j) {
            unsigned slot;
            creatures_roster_init(&roster);slot=grant(base);before=roster;
            assert(!creatures_mark_trial_qualified(&roster.instances[slot],family+1,j));unchanged();
            assert(!creatures_mark_trial_qualified(&roster.instances[slot],family,j+65536u));unchanged();
            assert(creatures_mark_trial_qualified(&roster.instances[slot],family,j));before=roster;
            assert(creatures_can_evolve(&roster.instances[slot],1024,1)==CREATURE_EVOLVE_AMBIGUOUS);
            assert(creatures_evolve_to(&roster,slot,base+j,1024,1,0)==CREATURE_EVOLVE_DEFERRED);unchanged();
            assert(creatures_evolve_to(&roster,slot,base+j,4096,1,1)==CREATURE_EVOLVE_STORY);unchanged();
            assert(creatures_evolve_to(&roster,slot,base+j,8192,1,1)==CREATURE_EVOLVE_STORY);unchanged();
            assert(creatures_evolve_to(&roster,slot,base+j,16384,1,1)==CREATURE_EVOLVE_STORY);unchanged();
            assert(creatures_evolve_to(&roster,slot,base+j+256,1024,1,1)==CREATURE_EVOLVE_INVALID);unchanged();
            assert(creatures_evolve_to(&roster,slot,base+j,1024,1,1)==CREATURE_EVOLVE_READY);
            assert(roster.instances[slot].instance_id==1 && roster.instances[slot].equipped[0]==67+3*i);
            assert(roster.instances[slot].trial_flags==j && roster.instances[slot].polarity==creatures_form(base+j)->polarity);
            before=roster;
            assert(creatures_evolve_to(&roster,slot,base+3-j,1024,1,1)==CREATURE_EVOLVE_NO_EDGE);unchanged();
            assert(creatures_evolve_to(&roster,slot,base,1024,1,1)==CREATURE_EVOLVE_NO_EDGE);unchanged();
        }
    }
}
static void admission_and_rollback(void) {
    unsigned i,slot=255,first,second;
    CreatureCoverage coverage;
    creatures_roster_init(&roster);assert(creatures_collection_coverage(&roster,&coverage));
    assert(coverage.missing_opportunities==72);
    for(i=0;i<89;++i) grant(1);
    assert(creatures_grant_admitted(&roster,49,50,100,0,0,&first)==CREATURE_ADMISSION_READY);
    assert(creatures_grant_admitted(&roster,49,50,100,0,0,&second)==CREATURE_ADMISSION_READY);
    before=roster;
    assert(creatures_grant_admitted(&roster,49,50,100,0,0,&slot)==CREATURE_ADMISSION_RESERVED && slot==255);unchanged();
    assert(creatures_mark_trial_qualified(&roster.instances[first],17,1));
    assert(creatures_mark_trial_qualified(&roster.instances[second],17,1));
    assert(creatures_mark_trial_qualified(&roster.instances[second],17,2));
    assert(creatures_evolve_to(&roster,first,50,1024,1,1)==CREATURE_EVOLVE_READY);before=roster;
    assert(creatures_evolve_to(&roster,second,50,1024,1,1)==CREATURE_EVOLVE_COLLECTION_RESERVED);unchanged();
    assert(creatures_evolve_to(&roster,second,51,1024,1,1)==CREATURE_EVOLVE_READY);
    creatures_roster_init(&roster);for(i=0;i<90;++i)grant(1);
    assert(creatures_roster_validate(&roster));assert(creatures_collection_coverage(&roster,&coverage));assert(!coverage.admission_safe);
    assert(creatures_grant_admitted(&roster,49,50,100,0,0,&slot)==CREATURE_ADMISSION_GRANDFATHERED_READY);
    before=roster;assert(creatures_grant_admitted(&roster,1,50,100,0,0,&slot)==CREATURE_ADMISSION_RESERVED);unchanged();
    roster.next_instance_id=0xffffffffu;before=roster;
    assert(creatures_grant_admitted(&roster,52,50,100,0,0,&slot)==CREATURE_ADMISSION_ID_EXHAUSTED);unchanged();
    creatures_roster_init(&roster);for(i=0;i<160;++i)grant(1);before=roster;
    assert(creatures_grant_admitted(&roster,49,50,100,0,0,&slot)==CREATURE_ADMISSION_FULL);unchanged();
}
int main(void) { tables_and_masks();admission_and_rollback();puts("Underwater strict core:1,572,864 mask cases,16 branches,72-opportunity admission and atomic denials passed");return 0; }
