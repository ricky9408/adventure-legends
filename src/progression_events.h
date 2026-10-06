#ifndef EMBERBOND_PROGRESSION_EVENTS_H
#define EMBERBOND_PROGRESSION_EVENTS_H
/* Stable credit IDs, never acquisition receipts. Unknown encounter returns512.
 * Historical IDs0..179 retain their published room/slot meaning. New chapters
 * use reviewed explicit rows, never unbounded room*6 arithmetic. */
unsigned progression_encounter_event(unsigned area,unsigned enemy_slot);
#endif
