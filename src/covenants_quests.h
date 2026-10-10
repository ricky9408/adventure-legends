#ifndef EMBERBOND_COVENANTS_QUESTS_H
#define EMBERBOND_COVENANTS_QUESTS_H
#include "save5.h"
enum { COVENANTS_FIRST_ROOM=70,COVENANTS_LAST_ROOM=77,COVENANTS_FIRST_QUEST=60,COVENANTS_QUEST_COUNT=4,
 COVENANTS_Q_HOME=60,COVENANTS_Q_LOWER,COVENANTS_Q_UPPER,COVENANTS_Q_RETURN };
enum CovenantsQuestResult { COVENANTS_INVALID=-1,COVENANTS_UNCHANGED=0,COVENANTS_CHANGED=1,
 COVENANTS_NOW_READY=2,COVENANTS_REWARDED=3,COVENANTS_LOCKED=4,COVENANTS_FULL=5,
 COVENANTS_SPACE_RESERVED=6,COVENANTS_ID_EXHAUSTED=7,COVENANTS_COVERAGE_LOSS=8 };
enum CovenantsRequestOperation { COVENANTS_REQUEST_VISIT=1,COVENANTS_REQUEST_ANCHOR,
 COVENANTS_REQUEST_QUEST_OFFER,COVENANTS_REQUEST_ORDINARY_OBJECTIVE,
 COVENANTS_REQUEST_QUEST_CLAIM,COVENANTS_REQUEST_COVENANT_COMPLETE,COVENANTS_REQUEST_UNIQUE_INVITE };
/* Full-width parsing before narrowing. Every unused field must be zero.
 * Source1..8 is scoped here, maps forms121..128 and exact rooms70..77.
 * Completion derives its quest/objective; generic objective cannot write
 * Q61/Q62. Runtime proves geometry/actions and explicit invitation consent,
 * then retains the exact fresh scene/attempt throughout this bounded job. */
typedef struct CovenantsRequest { unsigned operation,room,quest,bit,source; } CovenantsRequest;
int covenants_can_enter(const Save5State*,unsigned room);
unsigned covenants_quest_mask(unsigned quest);
int covenants_quest_available(const Save5State*,unsigned quest);
unsigned covenants_source_form(unsigned source);
unsigned covenants_source_family(unsigned source);
unsigned covenants_source_room(unsigned source);
int covenants_fulfilled(const Save5State*,unsigned source);
int covenants_source_claimed(const Save5State*,unsigned source);
const char*covenants_result_message(int result);
Save4U32 covenants_job_begin(Save5State*,const CovenantsRequest*,CreatureU32 scene_generation,CreatureU32 attempt_generation);
unsigned covenants_job_step(Save4U32 token,unsigned byte_budget,CreatureU32 scene_generation,CreatureU32 attempt_generation);
unsigned covenants_job_status(Save4U32 token);
unsigned covenants_job_phase(Save4U32 token);
int covenants_job_result(Save4U32 token);
void covenants_job_cancel(void);
/* Exclusive existing preflight scratch; <=8 preflight / <=4 admission records
 * per step. Fail/cancel leaves every live byte unchanged. No SRAM write, XP,
 * trial or lifetime credit. UNIQUE_INVITE never repeats or evicts a member. */
#endif
