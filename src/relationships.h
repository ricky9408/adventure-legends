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

/* This core is not yet connected to runtime or SRAM. Save5 reserved bytes
 * cannot carry new progress without a separately reviewed content revision. */
int relationships_valid(const RelationshipState *state);
unsigned relationships_affinity(const RelationshipState *state, unsigned person);
unsigned relationships_stage(const RelationshipState *state, unsigned person);
/* Scene code may commit acceptance only after both characters agree and the
 * player confirms. A threshold alone must never choose a partner for them. */
int relationships_record(RelationshipState *state, unsigned person, unsigned event);
#endif
