#ifndef EMBERBOND_MAGMA_QUESTS_H
#define EMBERBOND_MAGMA_QUESTS_H
#include "save5.h"
enum { MAGMA_FIRST_ROOM=38, MAGMA_LAST_ROOM=45, MAGMA_FIRST_QUEST=30, MAGMA_QUEST_COUNT=8,
 MAGMA_Q_HEARTH=30, MAGMA_Q_FOOTPATH, MAGMA_Q_BREATHE, MAGMA_Q_POTS,
 MAGMA_Q_CUP, MAGMA_Q_HOME, MAGMA_Q_CHIME, MAGMA_Q_SEEDBED };
enum MagmaQuestResult { MAGMA_INVALID=-1, MAGMA_UNCHANGED=0, MAGMA_CHANGED=1,
 MAGMA_NOW_READY=2, MAGMA_REWARDED=3, MAGMA_LOCKED=4, MAGMA_FULL=5,
 MAGMA_SPACE_RESERVED=6, MAGMA_ID_EXHAUSTED=7 };
enum MagmaSourceToken { MAGMA_SOURCE_NONE=0, MAGMA_SOURCE_HEARTH=1,
 MAGMA_SOURCE_FOOTPATH=2, MAGMA_SOURCE_FIELD_0=16, MAGMA_SOURCE_FIELD_1,
 MAGMA_SOURCE_FIELD_2, MAGMA_SOURCE_FIELD_3, MAGMA_SOURCE_FIELD_4,
 MAGMA_SOURCE_FIELD_5, MAGMA_SOURCE_FIELD_6 };
/* Event-only durable transactions. The caller proves tagged object, geometry,
 * scene solution and selected participant. These functions never detect world
 * objectives, grant XP/event credit, evolve, overwrite a party or write SRAM.
 * Non-success leaves state byte-identical; no complete Save5State stack copy.
 * READY source retries are idempotent before admission. Main thread only. */
int magma_can_enter(const Save5State *, unsigned room);
int magma_visit(Save5State *, unsigned room);
int magma_anchor(Save5State *, unsigned room);
unsigned magma_context(const Save5State *);
unsigned magma_quest_mask(unsigned quest);
int magma_quest_available(const Save5State *, unsigned quest);
int magma_quest_offer(Save5State *, unsigned quest);
int magma_quest_objective(Save5State *, unsigned quest, unsigned bit);
int magma_quest_claim(Save5State *, unsigned quest);
unsigned magma_recruit_level(const CreatureRoster *);
unsigned magma_source_family(unsigned token);
unsigned magma_source_token_for_family(unsigned family);
unsigned magma_source_form(unsigned token);
unsigned magma_source_aid(unsigned token); /* 55..61 field; 255 otherwise */
int magma_source_claimed(const Save5State *, unsigned token);
int magma_source_status(const Save5State *, unsigned token);
int magma_field_recruit(Save5State *, unsigned token);
/* Branch token is the original FIELD_0..3. Each explicit encounter grants a
 * real new instance; no repeated source/item/XP/bond/event reward is issued.
 * The receipt records the first extra only and never blocks later repeats. */
/* Cheap display eligibility only. It cannot authorize a grant. */
int magma_branch_hint_available(const Save5State *, unsigned token);
/* Main-thread bounded branch-only transaction. Nonzero scene binds the request;
 * every step verifies ownership; cancellation and failure leave durable state
 * unchanged. DONE is terminal and stepping it cannot repeat a grant. */
Save4U32 magma_recruit_job_begin(Save5State *, unsigned source, CreatureU32 scene);
unsigned magma_recruit_job_step(Save4U32, unsigned byte_budget, CreatureU32 scene);
unsigned magma_recruit_job_status(Save4U32);
unsigned magma_recruit_job_phase(Save4U32);
int magma_recruit_job_result(Save4U32);
void magma_recruit_job_cancel(void);
int magma_branch_status(const Save5State *, unsigned token);
int magma_branch_recruit(Save5State *, unsigned token);
/* discovery step is a single bit1/2/4, prefix0/1/3/7; status uses quest states. */
int magma_discover(Save5State *, unsigned step_bit);
unsigned magma_discovery_state(const Save5State *);
unsigned magma_trial_aid(unsigned family, unsigned local_trial_key); /*40..54*/
/* Caller retains the selected slot+instance ID throughout a transient trial.
 * Exact from-form, source, key prerequisites and context are checked here.
 * An existing completed key is unchanged, never re-awarded or floor-cloned.
 * Qualified proof must be cleared on death/load by the world runtime. */
int magma_trial_status(const Save5State *, unsigned roster_slot,
 CreatureU32 expected_instance_id, unsigned family, unsigned local_trial_key,
 unsigned source_token);
int magma_trial_complete(Save5State *, unsigned roster_slot,
 CreatureU32 expected_instance_id, unsigned family, unsigned local_trial_key,
 unsigned source_token);
const char *magma_result_message(int result);
#endif
