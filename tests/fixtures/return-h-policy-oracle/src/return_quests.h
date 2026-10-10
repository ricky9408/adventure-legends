#ifndef EMBERBOND_RETURN_QUESTS_H
#define EMBERBOND_RETURN_QUESTS_H
#include "save5.h"
enum { RETURN_FIRST_ROOM=54, RETURN_LAST_ROOM=61,
 RETURN_FIRST_QUEST=46, RETURN_QUEST_COUNT=8,
 RETURN_Q_FOOTSTEPS=46, RETURN_Q_LISTENER, RETURN_Q_HARBOUR,
 RETURN_Q_SHADE, RETURN_Q_RIVER, RETURN_Q_LIGHTS, RETURN_Q_ROOF, RETURN_Q_SURVEY };
enum ReturnQuestResult { RETURN_INVALID=-1, RETURN_UNCHANGED=0,
 RETURN_CHANGED=1, RETURN_NOW_READY=2, RETURN_REWARDED=3,
 RETURN_LOCKED=4, RETURN_FULL=5, RETURN_SPACE_RESERVED=6,
 RETURN_ID_EXHAUSTED=7 };
enum ReturnSourceToken { RETURN_SOURCE_NONE=0, RETURN_SOURCE_39=1,
 RETURN_SOURCE_40=2, RETURN_REPEAT_39=17, RETURN_REPEAT_40=18 };
enum ReturnRequestOperation { RETURN_REQUEST_VISIT=1, RETURN_REQUEST_ANCHOR,
 RETURN_REQUEST_QUEST_OFFER, RETURN_REQUEST_QUEST_OBJECTIVE,
 RETURN_REQUEST_QUEST_PROGRESS, RETURN_REQUEST_QUEST_CLAIM,
 RETURN_REQUEST_REPEAT_RECRUIT, RETURN_REQUEST_TRIAL_STATUS,
 RETURN_REQUEST_TRIAL_COMPLETE };
/* All fields are full-width until checked. Zero unused fields. A claim of
 * q47/q49 must carry its initial source1/2; repeat requires exact17/18.
 * Trials bind room, slot, instance_id, family/key, from_form and the actual
 * selected learned command. The runtime owns and consumes each fresh solved
 * geometry attempt only after REWARDED; provenance is never an attempt token. */
typedef struct ReturnRequest {
 unsigned operation, room, quest, bit, source, slot, family, key, form, command;
 CreatureU32 instance_id;
} ReturnRequest;
int return_can_enter(const Save5State *,unsigned room);
unsigned return_context(const Save5State *);
unsigned return_quest_mask(unsigned quest);
int return_quest_available(const Save5State *,unsigned quest);
unsigned return_source_family(unsigned token);
unsigned return_source_form(unsigned token);
int return_source_claimed(const Save5State *,unsigned token);
unsigned return_recruit_level(const CreatureRoster *);
unsigned return_trial_aid(unsigned family,unsigned key);
unsigned return_trial_form(unsigned family,unsigned key);
unsigned return_trial_room(unsigned family,unsigned key);
int return_trial_status(const Save5State *,unsigned slot,CreatureU32 instance_id,
 unsigned family,unsigned key,unsigned form,unsigned command);
const char *return_result_message(int result);
/* Exclusive shared save scratch, no extra save clone; begin and each step are
 * bounded. Scene AND attempt generations are mandatory and checked each step.
 * Exact live-byte equality is checked immediately before the sole commit.
 * A consumed job cannot run again; cancel on exit/load/death/menu/selection.
 * No job awards credit. Runtime awards it only after its typed success. */
Save4U32 return_job_begin(Save5State *,const ReturnRequest *,
 CreatureU32 scene_generation,CreatureU32 attempt_generation);
unsigned return_job_step(Save4U32 token,unsigned byte_budget,
 CreatureU32 scene_generation,CreatureU32 attempt_generation);
unsigned return_job_status(Save4U32 token);
unsigned return_job_phase(Save4U32 token);
int return_job_result(Save4U32 token);
void return_job_cancel(void);
#endif
