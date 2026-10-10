#ifndef EMBERBOND_HORIZONS_QUESTS_H
#define EMBERBOND_HORIZONS_QUESTS_H
#include "save5.h"
enum { HORIZONS_FIRST_ROOM=62,HORIZONS_LAST_ROOM=69,HORIZONS_FIRST_QUEST=54,HORIZONS_QUEST_COUNT=6,
 HORIZONS_Q_INVITATION=54,HORIZONS_Q_STAGE,HORIZONS_Q_PRINT,HORIZONS_Q_PROCESSION,HORIZONS_Q_SEATS,HORIZONS_Q_MARKS };
enum HorizonsQuestResult { HORIZONS_INVALID=-1,HORIZONS_UNCHANGED=0,HORIZONS_CHANGED=1,
 HORIZONS_NOW_READY=2,HORIZONS_REWARDED=3,HORIZONS_LOCKED=4,HORIZONS_FULL=5,
 HORIZONS_SPACE_RESERVED=6,HORIZONS_ID_EXHAUSTED=7,HORIZONS_COVERAGE_LOSS=8 };
enum HorizonsRequestOperation { HORIZONS_REQUEST_VISIT=1,HORIZONS_REQUEST_ANCHOR,
 HORIZONS_REQUEST_QUEST_OFFER,HORIZONS_REQUEST_QUEST_OBJECTIVE,HORIZONS_REQUEST_QUEST_PROGRESS,
 HORIZONS_REQUEST_QUEST_CLAIM,HORIZONS_REQUEST_INITIAL_RECRUIT,HORIZONS_REQUEST_REPEAT_RECRUIT,
 HORIZONS_REQUEST_TRIAL_STATUS,HORIZONS_REQUEST_TRIAL_COMPLETE };
/* Full-width values are checked before narrowing. Zero every unused field.
 * Quest objective/claim requests carry their exact current room. Initial
 * invitations carry source1..12, family41..52, room; repeats33..44 additionally
 * bind exact selected slot,instance_id,form,base command. Runtime authorizes
 * geometry and explicit confirmation, with fresh scene/attempt generations. */
typedef struct HorizonsRequest { unsigned operation,room,quest,bit,source,slot,family,key,form,command;
 CreatureU32 instance_id; } HorizonsRequest;
int horizons_can_enter(const Save5State*,unsigned room);
unsigned horizons_context(const Save5State*);
unsigned horizons_quest_mask(unsigned quest);
int horizons_quest_available(const Save5State*,unsigned quest);
unsigned horizons_source_family(unsigned token);
unsigned horizons_source_form(unsigned token);
unsigned horizons_source_room(unsigned token);
int horizons_source_claimed(const Save5State*,unsigned token);
unsigned horizons_recruit_level(const CreatureRoster*);
unsigned horizons_trial_aid(unsigned family,unsigned key);
unsigned horizons_trial_form(unsigned family,unsigned key);
unsigned horizons_trial_room(unsigned family,unsigned key);
int horizons_trial_status(const Save5State*,unsigned slot,CreatureU32 instance_id,unsigned family,unsigned key,unsigned form,unsigned command);
const char*horizons_result_message(int result);
Save4U32 horizons_job_begin(Save5State*,const HorizonsRequest*,CreatureU32 scene_generation,CreatureU32 attempt_generation);
unsigned horizons_job_step(Save4U32 token,unsigned byte_budget,CreatureU32 scene_generation,CreatureU32 attempt_generation);
unsigned horizons_job_status(Save4U32 token);
unsigned horizons_job_phase(Save4U32 token);
int horizons_job_result(Save4U32 token);
void horizons_job_cancel(void);
/* Uses existing exclusive save scratch; <=8 preflight / <=4 admission records
 * per step. Failed/cancelled jobs leave all bytes unchanged. Job success does
 * not write SRAM. Runtime requests save and once-per-expedition quest credit
 * only after REWARDED; credit never authorizes a source or trial. */
#endif
