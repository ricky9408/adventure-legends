#include "relationships.h"

static int events_valid(unsigned events)
{
    return events == 0 || events == 1 || events == 3 || events == 7 ||
           events == 15 || events == 31;
}

int relationships_valid(const RelationshipState *state)
{
    unsigned i;
    if (!state) return 0;
    for (i = 0; i < REL_PERSON_COUNT; ++i)
        if (!events_valid(state->events[i])) return 0;
    return 1;
}

unsigned relationships_affinity(const RelationshipState *state, unsigned person)
{
    unsigned events, score = 0;
    if (!state || person >= REL_PERSON_COUNT) return 0;
    events = state->events[person];
    if (!events_valid(events)) return 0;
    if (events & (1u << REL_SHARED_TASK)) score += 10;
    if (events & (1u << REL_RETURN_VISIT)) score += 20;
    if (events & (1u << REL_PERSONAL_STORY)) score += 30;
    return score;
}

unsigned relationships_stage(const RelationshipState *state, unsigned person)
{
    unsigned events;
    if (!state || person >= REL_PERSON_COUNT) return REL_UNMET;
    events = state->events[person];
    if (!events_valid(events)) return REL_UNMET;
    if (events & (1u << REL_ACCEPT_MARRIAGE)) return REL_SPOUSE;
    if (events & (1u << REL_ACCEPT_DATING)) return REL_PARTNER;
    if (events & (1u << REL_RETURN_VISIT)) return REL_FRIEND;
    return events ? REL_ACQUAINTED : REL_UNMET;
}

int relationships_record(RelationshipState *state, unsigned person, unsigned event)
{
    unsigned bit;
    if (!relationships_valid(state) || person >= REL_PERSON_COUNT ||
        event >= REL_EVENT_COUNT) return 0;
    bit = 1u << event;
    if (state->events[person] != bit - 1u) return 0;
    state->events[person] |= bit;
    return 1;
}
