/* Exact pre-second-optimization validator snapshots. Test-only, never linked
 * into a ROM. Source SHA158fcec4bddcab1a2294d96352e6bb8153feaeee6e6ed1c9cc50be04c8453a18.
 * Policy/registry helpers are intentionally shared and unchanged; this test
 * isolates XP interval, party traversal and collection-bit optimizations. */
#include "creatures.c"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int reference_creatures_instance_validate(const CreatureInstance *c) {
    const CreatureForm *f;
    const CreatureFamilyPolicy *family;
    unsigned j, legacy;
    if (!c) return 0;
    if (!c->form_id) return instance_is_zero(c);
    f = creatures_form(c->form_id);
    family = f ? family_policy_for_id(f->family) : 0;
    legacy = creatures_legacy_spirit(c->form_id);
    if (!f || !family || !(c->flags & CREATURE_OCCUPIED) || (c->flags & ~CREATURE_FLAGS_MASK) ||
        c->level < 1 || c->level > 50 || c->bond > 100 || c->xp > CREATURE_XP_CAP ||
        c->level != creatures_level_for_xp(c->xp) || !c->instance_id ||
        c->instance_id == U32_MAX_VALUE || c->nickname_id > CREATURE_NICKNAME_MAX ||
        (c->trial_flags & ~family->trial) ||
        ((c->flags & CREATURE_STORY_LOCKED) && legacy >= CREATURE_LEGACY_COUNT) || c->polarity != f->polarity ||
        c->selected_command > 1 || !c->equipped[c->selected_command] ||
        (c->equipped[0] && c->equipped[0] == c->equipped[1])) return 0;
    for (j = 0; j < 2; ++j)
        if (c->equipped[j] && !creatures_command_learned(c->form_id, c->level, c->equipped[j])) return 0;
    if (f->tier > 1) {
        const CreatureEvolution *e = incoming_evolution(c->form_id);
        if (!e || c->level < e->min_level) return 0;
    }
    return 1;
}

int reference_creatures_party_validate(const CreatureRoster *r) {
    unsigned i, j, members = 0, legendary = 0;
    if (!r) return 0;
    for (i = 0; i < 4; ++i) {
        unsigned slot = r->party[i];
        const CreatureInstance *c;
        if (slot == CREATURE_EMPTY_SLOT) continue;
        if (slot >= 160) return 0;
        c = &r->instances[slot];
        if (!c->form_id || !reference_creatures_instance_validate(c)) return 0;
        for (j = 0; j < i; ++j) if (slot == r->party[j]) return 0;
        ++members;
        legendary += creatures_form(c->form_id)->rarity != 0;
    }
    if (legendary > 1) return 0;
    if (!members) return r->selected_party == CREATURE_EMPTY_SLOT;
    return r->selected_party < 4 && r->party[r->selected_party] != CREATURE_EMPTY_SLOT;
}

int reference_creatures_roster_validate(const CreatureRoster *r) {
    unsigned i, j, stories = 0;
    if (!r || !r->next_instance_id || !reference_creatures_party_validate(r)) return 0;
    for (i = 0; i < 128; ++i) {
        if ((bit_get(r->seen, i) || bit_get(r->obtained, i)) && !creatures_form(i + 1)) return 0;
        if (bit_get(r->obtained, i) && !bit_get(r->seen, i)) return 0;
    }
    for (i = 0; i < 160; ++i) {
        const CreatureInstance *c = &r->instances[i];
        unsigned legacy;
        if (!reference_creatures_instance_validate(c) || r->expedition_bond[i] > 10) return 0;
        if (!c->form_id) { if (r->expedition_bond[i]) return 0; continue; }
        if (c->instance_id >= r->next_instance_id || !bit_get(r->obtained, c->form_id - 1)) return 0;
        for (j = 0; j < i; ++j)
            if (c->instance_id == r->instances[j].instance_id) return 0;
        if (c->flags & CREATURE_STORY_LOCKED) {
            legacy = creatures_legacy_spirit(c->form_id);
            if (legacy >= 4 || (stories & (1u << legacy)) || !bit_get(r->rewards, legacy)) return 0;
            stories |= 1u << legacy;
        }
    }
    return stories == (r->rewards[0] & 15u);
}

static CreatureRoster roster;
static unsigned long long xp_pairs,party_pairs,collection_pairs,corrupt_pairs;
static void compare_roster(void) {
    assert(reference_creatures_party_validate(&roster)==creatures_party_validate(&roster));
    assert(reference_creatures_roster_validate(&roster)==creatures_roster_validate(&roster));
}
int main(void) {
    CreatureInstance c;
    unsigned xp,level,i,j,a,b,d,e,selected;
    static const unsigned char refs[9]={0,1,2,3,4,159,160,254,255};
    static const unsigned char selections[6]={0,1,2,3,4,255};
    creatures_roster_init(&roster);
    assert(creatures_grant(&roster,1,1,20,0,0)==0);c=roster.instances[0];
    /* Exhaust every legal XP integer against every possible authored level.
     * The reference derives level by binary search; production checks range. */
    for(xp=0;xp<=CREATURE_XP_CAP;++xp)for(level=1;level<=CREATURE_MAX_LEVEL;++level) {
        c.xp=xp;c.level=(CreatureU8)level;
        assert(reference_creatures_instance_validate(&c)==creatures_instance_validate(&c));++xp_pairs;
    }
    for(i=0;i<256;++i) {
        static const unsigned values[7]={0,1,470595,470596,470597,0x7fffffffu,0xffffffffu};
        for(j=0;j<7;++j){c.level=(CreatureU8)i;c.xp=values[j];
            assert(reference_creatures_instance_validate(&c)==creatures_instance_validate(&c));++xp_pairs;}
    }
    creatures_roster_init(&roster);
    for(i=0;i<160;++i)assert(creatures_grant(&roster,1,50,100,0,0)==i);
    for(a=0;a<9;++a)for(b=0;b<9;++b)for(d=0;d<9;++d)for(e=0;e<9;++e)for(selected=0;selected<6;++selected) {
        roster.party[0]=refs[a];roster.party[1]=refs[b];roster.party[2]=refs[d];roster.party[3]=refs[e];
        roster.selected_party=selections[selected];compare_roster();++party_pairs;
    }
    /* Every byte-valued reference and selected index, independently. */
    for(i=0;i<4;++i)for(j=0;j<256;++j)for(selected=0;selected<256;++selected) {
        for(a=0;a<4;++a)roster.party[a]=(CreatureU8)a;
        roster.party[i]=(CreatureU8)j;roster.selected_party=(CreatureU8)selected;
        compare_roster();++party_pairs;
    }
    for(a=0;a<4;++a)roster.party[a]=(CreatureU8)a;
    roster.selected_party=0;
    /* Active and stored corruption: skipping redundant party validation must
     * never skip the authoritative all-record check. */
    for(i=0;i<6;++i) {
        unsigned slot=i==5?159:i;CreatureInstance original=roster.instances[slot];
        for(j=0;j<24;++j)for(a=1;a<256;++a) {
            roster.instances[slot]=original;
            ((unsigned char*)&roster.instances[slot])[j]^=(unsigned char)a;
            compare_roster();++corrupt_pairs;
        }
        roster.instances[slot]=original;
    }
    creatures_roster_init(&roster);
    /* Every pair of seen/obtained byte values at all16 identity positions. */
    for(i=0;i<16;++i) {
        for(a=0;a<256;++a)for(b=0;b<256;++b) {
            roster.seen[i]=(CreatureU8)a;roster.obtained[i]=(CreatureU8)b;
            compare_roster();++collection_pairs;
        }
        roster.seen[i]=roster.obtained[i]=0;
    }
    printf("{\"xp_level_pairs\":%llu,\"party_reference_pairs\":%llu,\"collection_byte_pairs\":%llu,\"instance_corruptions\":%llu}\n",xp_pairs,party_pairs,collection_pairs,corrupt_pairs);
    return 0;
}
