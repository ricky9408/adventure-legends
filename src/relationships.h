#ifndef EMBER_RELATIONSHIPS_H
#define EMBER_RELATIONSHIPS_H

enum {
    REL_EDDA, REL_RESSA, REL_MINA, REL_LYRA, REL_PERSON_COUNT
};
enum {
    REL_SHARED_TASK, REL_RETURN_VISIT, REL_PERSONAL_STORY,
    REL_ACCEPT_DATING, REL_ACCEPT_MARRIAGE, REL_EVENT_COUNT
};
enum { REL_UNMET, REL_ACQUAINTED, REL_FRIEND, REL_PARTNER, REL_SPOUSE };

typedef struct {
    unsigned char events[REL_PERSON_COUNT];
} RelationshipState;

/* Content13 stores this ledger; older revisions must keep the new bytes zero
 * rather than inventing past events. */
/* Header-local validation lets standalone save-codec tools share the same
 * four-byte rule without pulling scene or relationship runtime objects in. */
static inline int relationships_state_valid(const RelationshipState *state)
{
    unsigned i, events;
    if (!state) return 0;
    for (i = 0; i < REL_PERSON_COUNT; ++i) {
        events = state->events[i];
        if (events != 0 && events != 1 && events != 3 && events != 7 &&
            events != 15 && events != 31) return 0;
    }
    return 1;
}
int relationships_valid(const RelationshipState *state);
unsigned relationships_affinity(const RelationshipState *state, unsigned person);
unsigned relationships_stage(const RelationshipState *state, unsigned person);
/* Scene code may commit acceptance only after both characters agree and the
 * player confirms. A threshold alone must never choose a partner for them. */
int relationships_record(RelationshipState *state, unsigned person, unsigned event);
#endif
