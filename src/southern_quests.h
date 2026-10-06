#ifndef EMBERBOND_SOUTHERN_QUESTS_H
#define EMBERBOND_SOUTHERN_QUESTS_H
#include "save5.h"
enum { SOUTH_FIRST_ROOM=30, SOUTH_LAST_ROOM=37, SOUTH_FIRST_QUEST=22, SOUTH_QUEST_COUNT=8,
 SOUTH_Q_WINDOW=22, SOUTH_Q_HINGE, SOUTH_Q_SUNWELL, SOUTH_Q_MARKET,
 SOUTH_Q_RAIN, SOUTH_Q_DELIVERY, SOUTH_Q_AWNING, SOUTH_Q_LOFT };
enum SouthQuestResult { SOUTH_INVALID=-1, SOUTH_UNCHANGED=0, SOUTH_CHANGED=1,
 SOUTH_NOW_READY=2, SOUTH_REWARDED=3, SOUTH_LOCKED=4, SOUTH_FULL=5, SOUTH_RESERVED=6 };
/* Typed source identities, independent of historical generic reward IDs. */
enum SouthSourceToken { SOUTH_SOURCE_NONE=0, SOUTH_SOURCE_WINDOW=1,
 SOUTH_SOURCE_HINGE=2, SOUTH_SOURCE_TANGLEAPER=16, SOUTH_SOURCE_DUNEROLL,
 SOUTH_SOURCE_WARMCROAK, SOUTH_SOURCE_SHELLWADDLE, SOUTH_SOURCE_SWAYLEMUR,
 SOUTH_SOURCE_RILLNEWT, SOUTH_SOURCE_GLIMMERBAT, SOUTH_SOURCE_NEEDLETROT };
/* These are event-only ledger helpers, not gameplay objective detectors.
 * Caller must validate actual tagged target, geometry, scene solution and
 * participating identity before objective/discovery/recruit/trial calls.
 * Partial scene arrangements are transient and never fabricated here.
 * No SRAM writes, automatic evolution, party replacement or source inference.
 * Failure leaves every byte unchanged. Main-thread synchronous calls only. */
int southern_can_enter(const Save5State *, unsigned room);
int southern_visit(Save5State *, unsigned room);
int southern_anchor(Save5State *, unsigned room);
unsigned southern_context(const Save5State *);
unsigned southern_quest_mask(unsigned quest);
int southern_quest_available(const Save5State *, unsigned quest);
int southern_quest_offer(Save5State *, unsigned quest);
int southern_quest_objective(Save5State *, unsigned quest, unsigned bit);
int southern_quest_claim(Save5State *, unsigned quest);
unsigned southern_recruit_level(const CreatureRoster *);
unsigned southern_source_family(unsigned source_token);
unsigned southern_source_token_for_family(unsigned family);
int southern_source_claimed(const Save5State *, unsigned source_token);
int southern_field_recruit(Save5State *, unsigned source_token);
/* discovery_id0: loft/Q29, 1: awning/Q28. READY suffices; gear claim is optional. */
int southern_discover(Save5State *, unsigned discovery_id);
/* The explicit slot+identity pins the actual participant, including stored
 * copies. A source token must resolve to this exact immutable family and an
 * actual claimed typed source. Prior generic event/aid credits do not suppress
 * this authored training floor. Only family-local key1 is authored here. */
int southern_trial_complete(Save5State *, unsigned roster_slot,
 CreatureU32 expected_instance_id, unsigned family, unsigned local_trial_key,
 unsigned source_token);
/* RESERVED means physically free slots are needed for missing terminal paths;
 * FULL means160 occupied slots. Neither consumes rewards, source or quest state.
 * Imported over-budget rosters remain legal; only nonworsening grants proceed. */
#endif
