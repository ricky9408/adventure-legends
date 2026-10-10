#include "journey_goal.h"
#include "ui.h"
static unsigned state(const Save5State*s,unsigned q){return save5_quest_state(&s->quests,q);}
static int done(const Save5State*s,unsigned q){return state(s,q)==SAVE5_QUEST_CLAIMED;}
static JourneyGoal goal(int title,int detail,unsigned target,unsigned stage){JourneyGoal g={title,detail,target,stage};return g;}
JourneyGoal journey_goal_read(const Save5State*s,unsigned flags,unsigned room){
 if(!s)return goal(TX_JG_BEGIN,TX_JG_MAP_HELP,0,JOURNEY_LIGHTS);
 if(done(s,63))return goal(TX_JG_HOME,TX_JG_HOME_FREE,0,JOURNEY_HOME);
 if(done(s,57)){
  if(!(flags&SAVE4_ENDING_SEEN))return goal(TX_JG_ELDER,TX_JG_ELDER_LIGHTS,0,JOURNEY_LIGHTS);
  if(!(s->quests.objectives[60]&1))return goal(TX_JG_ELDER,TX_JG_ELDER_NEW,0,JOURNEY_COVENANTS);
  if(!(s->quests.objectives[60]&2))return goal(TX_JG_LETTER,TX_JG_LETTER_DETAIL,62,JOURNEY_COVENANTS);
  if(!done(s,60))return goal(TX_JG_TERRACE,TX_JG_TERRACE_WELCOME,70,JOURNEY_COVENANTS);
  if(!done(s,61))return goal(TX_JG_FIRST_WORK,TX_JG_FIRST_WORK_DETAIL,70,JOURNEY_COVENANTS);
  if(!done(s,62))return goal(TX_JG_NEXT_WORK,TX_JG_NEXT_WORK_DETAIL,74,JOURNEY_COVENANTS);
  if(!(s->quests.objectives[63]&1))return goal(TX_JG_PORCH,TX_JG_PORCH_DETAIL,70,JOURNEY_COVENANTS);
  if(!(s->quests.objectives[63]&2))return goal(TX_JG_MEET,TX_JG_MEET_DETAIL,62,JOURNEY_COVENANTS);
  return goal(TX_JG_ELDER,TX_JG_HOME_REPORT,0,JOURNEY_COVENANTS);
 }
 if(done(s,51)){
  if(!(s->quests.objectives[54]&1))return goal(TX_JG_INVITATION,TX_JG_INVITATION_DETAIL,60,JOURNEY_HORIZONS);
  if(!done(s,54))return goal(TX_JG_FAIR,TX_JG_FAIR_DETAIL,62,JOURNEY_HORIZONS);
  if(!done(s,55))return goal(TX_JG_YARD,TX_JG_YARD_DETAIL,63,JOURNEY_HORIZONS);
  if(!done(s,56))return goal(TX_JG_COURT,TX_JG_COURT_DETAIL,65,JOURNEY_HORIZONS);
  if(state(s,57)==SAVE5_QUEST_READY)return goal(TX_JG_FAIR_REPORT,TX_JG_FAIR_REPORT_DETAIL,62,JOURNEY_HORIZONS);
  return goal(TX_JG_SKY_GATHERING,TX_JG_SKY_GATHERING_DETAIL,67,JOURNEY_HORIZONS);
 }
 if(done(s,40)){
  if(!done(s,46))return s->quests.objectives[46]&1?
   goal(TX_JG_HOME_DESK,TX_JG_HOME_DESK_DETAIL,0,JOURNEY_RETURN):
   goal(TX_JG_RECORD_COPY,TX_JG_RECORD_COPY_DETAIL,46,JOURNEY_RETURN);
  if(!(s->quests.region_flags[5]&1))return goal(TX_JG_COMMON,TX_JG_COMMON_DETAIL,54,JOURNEY_RETURN);
  if(!done(s,47))return goal(TX_JG_BELL_SMITH,TX_JG_BELL_SMITH_DETAIL,16,JOURNEY_RETURN);
  if(!done(s,49))return goal(TX_JG_SOUTH_CURATOR,TX_JG_SOUTH_CURATOR_DETAIL,30,JOURNEY_RETURN);
  if(!done(s,48))return goal(TX_JG_NORTH_RIGGING,TX_JG_NORTH_RIGGING_DETAIL,22,JOURNEY_RETURN);
  if(!done(s,50))return goal(TX_JG_WEAVER,TX_JG_WEAVER_DETAIL,16,JOURNEY_RETURN);
  if((s->quests.objectives[51]&7)==7)return goal(TX_JG_HOME_DESK,TX_JG_MAP_REPORT,0,JOURNEY_RETURN);
  if((s->quests.objectives[51]&3)==3)return goal(TX_JG_CAUSEWAY,TX_JG_CAUSEWAY_DETAIL,61,JOURNEY_RETURN);
  return goal(TX_JG_MAPROOM,TX_JG_MAPROOM_DETAIL,60,JOURNEY_RETURN);
 }
 if(done(s,32)){
  if(!(s->quests.region_flags[4]&1))return goal(TX_JG_PEARL_ROAD,TX_JG_PEARL_ROAD_DETAIL,46,JOURNEY_UNDERWATER);
  if(!done(s,38))return goal(TX_JG_ECHO,TX_JG_ECHO_DETAIL,46,JOURNEY_UNDERWATER);
  if(!done(s,39))return goal(TX_JG_BALLAST,TX_JG_BALLAST_DETAIL,46,JOURNEY_UNDERWATER);
  if(state(s,40)==SAVE5_QUEST_READY)return goal(TX_JG_KEEPER_REPORT,TX_JG_KEEPER_REPORT_DETAIL,46,JOURNEY_UNDERWATER);
  return goal(TX_JG_ARCHIVE,TX_JG_ARCHIVE_DETAIL,50,JOURNEY_UNDERWATER);
 }
 if(done(s,24)){
  if(!(s->quests.region_flags[3]&1))return goal(TX_JG_KILNSTEP,TX_JG_KILNSTEP_DETAIL,38,JOURNEY_MAGMA);
  if(!done(s,30))return goal(TX_JG_HEARTH,TX_JG_HEARTH_DETAIL,38,JOURNEY_MAGMA);
  if(!done(s,31))return goal(TX_JG_WALKWAY,TX_JG_WALKWAY_DETAIL,39,JOURNEY_MAGMA);
  if(state(s,32)==SAVE5_QUEST_READY)return goal(TX_JG_RESSA_REPORT,TX_JG_RESSA_REPORT_DETAIL,38,JOURNEY_MAGMA);
  return goal(TX_JG_CALDERA,TX_JG_CALDERA_DETAIL,42,JOURNEY_MAGMA);
 }
 if(done(s,21)){
  if(!(s->quests.region_flags[2]&1))return goal(TX_JG_SUNLACE,TX_JG_SUNLACE_DETAIL,30,JOURNEY_SOUTH);
  if(!done(s,22))return goal(TX_JG_SUN_WINDOW,TX_JG_SUN_WINDOW_DETAIL,30,JOURNEY_SOUTH);
  if(!done(s,23))return goal(TX_JG_SUN_HINGE,TX_JG_SUN_HINGE_DETAIL,31,JOURNEY_SOUTH);
  if(state(s,24)==SAVE5_QUEST_READY)return goal(TX_JG_SUNWELL_REPORT,TX_JG_SUNWELL_REPORT_DETAIL,37,JOURNEY_SOUTH);
  return goal(TX_JG_SUNWELL,TX_JG_SUNWELL_DETAIL,34,JOURNEY_SOUTH);
 }
 /* The home celebration is an unfinished original chapter step, not a
  * barrier to already-started regional work elsewhere. */
 if(room==0&&(flags&SAVE4_CORE_CLEAR)&&!(flags&SAVE4_ENDING_SEEN))return goal(TX_JG_ELDER,TX_JG_ELDER_LIGHTS,0,JOURNEY_LIGHTS);
 if((s->quests.region_flags[1]&1)||((flags&SAVE4_SKY_CLEAR)&&done(s,2)&&done(s,3))){
  if(!(s->quests.region_flags[1]&1))return goal(TX_JG_HEARTHWAKE,TX_JG_HEARTHWAKE_DETAIL,22,JOURNEY_NORTH);
  if(!done(s,11))return goal(TX_JG_CARGO,TX_JG_CARGO_DETAIL,22,JOURNEY_NORTH);
  if(!done(s,13))return goal(TX_JG_BEARING,TX_JG_BEARING_DETAIL,23,JOURNEY_NORTH);
  if(state(s,21)==SAVE5_QUEST_READY)return room==29?
   goal(TX_JG_CROWN_REPORT,TX_JG_CROWN_REPORT_DETAIL,29,JOURNEY_NORTH):
   goal(TX_JG_PORT_REPORT,TX_JG_PORT_REPORT_DETAIL,22,JOURNEY_NORTH);
  return goal(TX_JG_LIGHTHOUSE,TX_JG_LIGHTHOUSE_DETAIL,26,JOURNEY_NORTH);
 }
 if((flags&SAVE4_ENDING_SEEN)||(room>=16&&room<=21)){
  if(!(s->quests.region_flags[0]&1))return goal(TX_JG_REEDHAVEN,TX_JG_REEDHAVEN_DETAIL,16,JOURNEY_RIVER);
  if(!done(s,2))return goal(TX_JG_WATER_FRIEND,TX_JG_WATER_FRIEND_DETAIL,17,JOURNEY_RIVER);
  if(!done(s,3))return goal(TX_JG_BELL_FRIEND,TX_JG_BELL_FRIEND_DETAIL,18,JOURNEY_RIVER);
 }
 if(flags&SAVE4_CORE_CLEAR)return goal(TX_JG_ELDER,TX_JG_ELDER_LIGHTS,0,JOURNEY_LIGHTS);
 if(flags&SAVE4_SKY_CLEAR)return goal(TX_C_QUEST_ACT3,TX_JG_CORE_DETAIL,9,JOURNEY_LIGHTS);
 if(flags&SAVE4_GROVE_CLEAR)return goal(TX_C_QUEST_ACT2,TX_JG_SKY_DETAIL,4,JOURNEY_LIGHTS);
 return goal(TX_JG_BEGIN,TX_JG_BEGIN_DETAIL,1,JOURNEY_LIGHTS);
}
