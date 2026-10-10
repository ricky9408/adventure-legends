#ifndef EMBERBOND_UNDERWATER_QUESTS_H
#define EMBERBOND_UNDERWATER_QUESTS_H
#include "save5.h"
enum { UNDERWATER_FIRST_ROOM=46, UNDERWATER_LAST_ROOM=53,
 UNDERWATER_FIRST_QUEST=38, UNDERWATER_QUEST_COUNT=8,
 UNDERWATER_Q_LISTENS=38, UNDERWATER_Q_RISE, UNDERWATER_Q_STORIES,
 UNDERWATER_Q_SHELLSCRIBE, UNDERWATER_Q_NACREPOINT, UNDERWATER_Q_PEARLWEAVE,
 UNDERWATER_Q_DRIFTSTEP, UNDERWATER_Q_QUIETWATER };
enum UnderwaterQuestResult { UNDERWATER_INVALID=-1, UNDERWATER_UNCHANGED=0,
 UNDERWATER_CHANGED=1, UNDERWATER_NOW_READY=2, UNDERWATER_REWARDED=3,
 UNDERWATER_LOCKED=4, UNDERWATER_FULL=5, UNDERWATER_SPACE_RESERVED=6,
 UNDERWATER_ID_EXHAUSTED=7 };
enum UnderwaterSourceToken { UW_SOURCE_NONE=0, UW_SOURCE_17=1, UW_SOURCE_18,
 UW_SOURCE_19, UW_SOURCE_20, UW_SOURCE_21, UW_SOURCE_22, UW_SOURCE_23,
 UW_SOURCE_24, UW_REPEAT_17=17, UW_REPEAT_18, UW_REPEAT_19, UW_REPEAT_20,
 UW_REPEAT_21, UW_REPEAT_22, UW_REPEAT_23, UW_REPEAT_24 };
/* Durable event transactions, called only after runtime proves exact tagged
 * geometry and consumes/locks the current room attempt. Full validation is a
 * blocking cold transition: do not invoke repeatedly from active-play ticks.
 * These APIs never award XP/events, replace party members, write SRAM, evolve,
 * or interpret a global aid/history bit as selected-individual proof.
 * Denial leaves all state bytes identical. No full Save5State stack copies. */
int underwater_can_enter(const Save5State *, unsigned room);
int underwater_visit(Save5State *, unsigned room);
int underwater_anchor(Save5State *, unsigned room);
unsigned underwater_context(const Save5State *);
unsigned underwater_quest_mask(unsigned quest);
int underwater_quest_available(const Save5State *, unsigned quest);
int underwater_quest_offer(Save5State *, unsigned quest);
int underwater_quest_objective(Save5State *, unsigned quest, unsigned bit);
int underwater_quest_claim(Save5State *, unsigned quest);
unsigned underwater_recruit_level(const CreatureRoster *);
unsigned underwater_source_family(unsigned source_token);
unsigned underwater_source_token_for_family(unsigned family);
unsigned underwater_source_form(unsigned source_token);
unsigned underwater_source_aid(unsigned source_token); /*78..83, or255*/
int underwater_source_claimed(const Save5State *, unsigned source_token);
int underwater_source_status(const Save5State *, unsigned source_token);
int underwater_field_recruit(Save5State *, unsigned source_token);
/* Repeat APIs accept FIRST source token1..8. The runtime retains a distinct
 * solved attempt generation and consumes it exactly once on REWARDED. A fresh
 * explicit attempt may invite another individual; byte17 is provenance only. */
int underwater_branch_status(const Save5State *, unsigned source_token);
int underwater_branch_recruit(Save5State *, unsigned source_token);
unsigned underwater_discovery_state(const Save5State *, unsigned family);
int underwater_discover(Save5State *, unsigned family, unsigned step_bit);
unsigned underwater_trial_aid(unsigned family, unsigned local_key); /*62..77*/
int underwater_trial_status(const Save5State *, unsigned roster_slot,
 CreatureU32 expected_instance_id, unsigned family, unsigned local_key,
 unsigned source_token);
int underwater_trial_complete(Save5State *, unsigned roster_slot,
 CreatureU32 expected_instance_id, unsigned family, unsigned local_key,
 unsigned source_token);
const char *underwater_result_message(int result);
/* Gameplay uses this exclusive, bounded read-only preflight + staged commit
 * path. Zero-initialize requests; unused fields must remain zero. One opaque
 * job owns the existing save scratch. Each step performs at most one bounded
 * stage and returns SAVE5_BUSY/DONE/FAILED; result retains the typed outcome.
 * QUEST_PROGRESS atomically offers an inactive quest and records one bit.
 * TRIAL_STATUS is read-only. No job grants XP/events; the world applies those
 * only after the successful corresponding result and releases this job.
 * Copying/mutating the original request after begin cannot redirect the job. */
enum UnderwaterRequestOperation {
 UW_REQUEST_VISIT=1, UW_REQUEST_ANCHOR, UW_REQUEST_QUEST_OFFER,
 UW_REQUEST_QUEST_OBJECTIVE, UW_REQUEST_QUEST_PROGRESS, UW_REQUEST_QUEST_CLAIM,
 UW_REQUEST_FIELD_RECRUIT, UW_REQUEST_REPEAT_RECRUIT, UW_REQUEST_DISCOVER,
 UW_REQUEST_TRIAL_STATUS, UW_REQUEST_TRIAL_COMPLETE
};
typedef struct UnderwaterRequest {
 unsigned operation, room, quest, bit, source, slot, family, key;
 CreatureU32 instance_id;
} UnderwaterRequest;
Save4U32 underwater_job_begin(Save5State *,const UnderwaterRequest *,
 CreatureU32 scene_generation);
unsigned underwater_job_step(Save4U32 token,unsigned byte_budget,
 CreatureU32 scene_generation);
unsigned underwater_job_status(Save4U32 token);
unsigned underwater_job_phase(Save4U32 token);
int underwater_job_result(Save4U32 token);
void underwater_job_cancel(void);
#endif
