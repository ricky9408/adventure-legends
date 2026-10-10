/* The Roads That Stay: local physical work, voluntary invitations and a return
 * home. Persistence is owned exclusively by covenants_quests.c. */
#include "covenants_game.h"
#include "connected_road_region.h"
#include "covenants_art.h"
#include "covenants_quests.h"
#include "covenants_powers.h"
#include "horizons_powers.h"
#include "return_powers.h"
#include "progression.h"
#include "assets.h"
#include "ui.h"
#if defined(__arm__)
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
#else
#define COLD
#endif
#define PLAY 1
#define A 1
#define B 2
#define RIGHT 16
#define LEFT 32
#define UP 64
#define DOWN 128
extern volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
extern int face,keys,journal_tab;
extern void enter_room(int,int),save_game(void),dialogue(int,int,int),toast(int);
extern void text(int,int,int,int),centered(int,int,int),box(int,int,int,int);
extern void rect(int,int,int,int,unsigned char),line(int,int,int,int,int);
extern void game_region_warp(int,int),game_health_fill(void),region_form_actor(unsigned,int,int);
extern int game_region_actor_overlap(int,int,int,int);
unsigned covenants_game_revision,covenants_game_journal_selection;
static unsigned scene=1,attempt=1,geometry=1,serial,ambient;
/* A setting is a settled piece of local ordinary work, never a reusable cast
 * credential. Leaving/reset/load reconstructs it from completed covenants. */
static unsigned char setting[24],reset_confirm,invite_confirm,porch_confirm,dirty;
static unsigned char transition_area,transition_spawn,transition_ready;
static short moving_x,npc_x,npc_y;
static unsigned short movement_ticks,practice_ticks;
static unsigned char moving_state,npc_stage,practice_mode,escort_stage,npc_walk_recent,npc_walk_phase,npc_blocked_ticks;
static unsigned heat_token;
static unsigned char work_area=255;
typedef struct {
 unsigned id;
 unsigned char form,command_slot,commands[2];
 unsigned short flags;
} PartyMemberProof;
typedef struct {
 unsigned token,id,scene,attempt,geometry;
 short x,y;
 unsigned char slot,selected,form,command,face,hits[2],refs[4],gear_refs[5];
 PartyMemberProof members[4];
 EquipmentRecord gear[5];
} WorldCast;
static WorldCast cast;
static CovenantsRequest events[4];
static unsigned event_handle,event_scene,event_attempt;
static unsigned char event_count,event_index;
static const unsigned char spawn_counts[8]={5,2,2,2,4,2,2,2};
static const short spawns[8][5][2]={
 {{240,288},{448,160},{32,160},{240,32},{80,272}},
 {{24,272},{208,32}},{{24,128},{448,128}},{{208,128},{24,128}},
 {{240,288},{448,160},{32,160},{80,272}},
 {{24,272},{208,32}},{{24,128},{448,128}},{{208,128},{24,128}}
};
static const short resets[8][2]={{48,296},{48,296},{48,136},{48,136},{48,296},{48,296},{48,136},{48,136}};
static const short invitations[8][2]={{432,272},{192,272},{432,112},{192,112},{432,272},{192,272},{432,112},{192,112}};
#include "covenants_work_data.inc"
static const int room_names[8]={TX_CV_ROOM70,TX_CV_ROOM71,TX_CV_ROOM72,TX_CV_ROOM73,TX_CV_ROOM74,TX_CV_ROOM75,TX_CV_ROOM76,TX_CV_ROOM77};
static const int quest_names[4]={TX_CV_Q60,TX_CV_Q61,TX_CV_Q62,TX_CV_Q63};
static const int quest_clues[4][2]={{TX_CV_CLUE60A,TX_CV_CLUE60B},{TX_CV_CLUE61A,TX_CV_CLUE61B},{TX_CV_CLUE62A,TX_CV_CLUE62B},{TX_CV_CLUE63A,TX_CV_CLUE63B}};
static const int trial_clues[8][2]={{TX_CV_TRIAL1A,TX_CV_TRIAL1B},{TX_CV_TRIAL2A,TX_CV_TRIAL2B},{TX_CV_TRIAL3A,TX_CV_TRIAL3B},{TX_CV_TRIAL4A,TX_CV_TRIAL4B},{TX_CV_TRIAL5A,TX_CV_TRIAL5B},{TX_CV_TRIAL6A,TX_CV_TRIAL6B},{TX_CV_TRIAL7A,TX_CV_TRIAL7B},{TX_CV_TRIAL8A,TX_CV_TRIAL8B}};
static const int after_lines[8][2]={{TX_CV_AFTER1A,TX_CV_AFTER1B},{TX_CV_AFTER2A,TX_CV_AFTER2B},{TX_CV_AFTER3A,TX_CV_AFTER3B},{TX_CV_AFTER4A,TX_CV_AFTER4B},{TX_CV_AFTER5A,TX_CV_AFTER5B},{TX_CV_AFTER6A,TX_CV_AFTER6B},{TX_CV_AFTER7A,TX_CV_AFTER7B},{TX_CV_AFTER8A,TX_CV_AFTER8B}};
static const int invite_lines[8][2]={{TX_CV_INVITE1A,TX_CV_INVITE1B},{TX_CV_INVITE2A,TX_CV_INVITE2B},{TX_CV_INVITE3A,TX_CV_INVITE3B},{TX_CV_INVITE4A,TX_CV_INVITE4B},{TX_CV_INVITE5A,TX_CV_INVITE5B},{TX_CV_INVITE6A,TX_CV_INVITE6B},{TX_CV_INVITE7A,TX_CV_INVITE7B},{TX_CV_INVITE8A,TX_CV_INVITE8B}};
static COLD int ab(int x){return x<0?-x:x;}
static COLD int near(int x,int y,int xx,int yy,int r){return ab(x-xx)+ab(y-yy)<=r;}
static COLD int close(int x,int y){
 int f,s;
 if(face==1){f=py-y;s=ab(px-x);}else if(face==0){f=y-py;s=ab(px-x);}
 else if(face==2){f=px-x;s=ab(py-y);}else{f=x-px;s=ab(py-y);}
 return f>=6&&f<=26&&s<=10&&s<=f/2;
}
static COLD void next_generation(unsigned *p){if(++*p==0)++*p;}
static COLD void changed(void){next_generation(&covenants_game_revision);}
static COLD unsigned state(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
static COLD unsigned bits(unsigned q){return adventure_save.quests.objectives[q];}
static COLD int done(unsigned q){return state(q)==SAVE5_QUEST_CLAIMED;}
static COLD int fulfilled(unsigned i){return i<8&&covenants_fulfilled(&adventure_save,i+1);}
static COLD int owned(unsigned i){return i<8&&covenants_source_claimed(&adventure_save,i+1);}
static COLD CreatureInstance *active(void){
 CreatureRoster *r=&adventure_save.roster;unsigned s;
 if(!summoned||r->selected_party>=4)return 0;
 s=r->party[r->selected_party];
 return s<CREATURE_ROSTER_CAPACITY&&(r->instances[s].flags&CREATURE_OCCUPIED)?&r->instances[s]:0;
}
static COLD void zero_bytes(void *dst,unsigned n){unsigned char *p=dst;while(n--)*p++=0;}
static COLD int equal_bytes(const void *a,const void *b,unsigned n){const unsigned char*x=a,*y=b;while(n--)if(*x++!=*y++)return 0;return 1;}
static COLD void invalidate_cast(void){cast.token=cast.id=0;cast.hits[0]=cast.hits[1]=0;heat_token=0;}
COLD void covenants_game_revoke_cast(unsigned token){if(token&&token==cast.token)invalidate_cast();}
static COLD void geometry_changed(void){
 next_generation(&geometry);invalidate_cast();
 return_powers_geometry_changed();horizons_powers_geometry_changed();covenants_powers_geometry_changed();changed();
}
COLD unsigned covenants_game_scene_generation(void){return scene;}
COLD unsigned covenants_game_attempt_generation(void){return attempt;}
COLD unsigned covenants_game_geometry_revision(void){return geometry;}
COLD int covenants_game_is_room(unsigned a){return a-70u<8u;}
COLD unsigned covenants_game_spawn_count(unsigned a){return covenants_game_is_room(a)?spawn_counts[a-70]:0;}
COLD int covenants_game_spawn(unsigned a,unsigned s,int*x,int*y){
 if(s>=covenants_game_spawn_count(a))return 0;
 if(x)*x=spawns[a-70][s][0];
 if(y)*y=spawns[a-70][s][1];
 return 1;
}
COLD int covenants_game_can_enter(unsigned a){return covenants_can_enter(&adventure_save,a);}
static COLD int spawn_allowed(unsigned a,unsigned s){
 if(s>=covenants_game_spawn_count(a)||!covenants_game_can_enter(a))return 0;
 if(a==70&&s==4&&!(adventure_save.quests.anchors[7]&1))return 0;
 if(a==74&&s==3&&!(adventure_save.quests.anchors[7]&2))return 0;
 if(a==70&&(s==1||s==2)&&!done(60))return 0;
 if(a==70&&s==3&&!done(61))return 0;
 if(a==74&&(s==1||s==2)&&!done(61))return 0;
 return 1;
}
COLD void covenants_game_cancel_event(void){
 if(event_handle)covenants_job_cancel();
 event_handle=event_count=event_index=0;
 transition_ready=transition_area=0;
}
static COLD void persist(void){
 if(!dirty)return;
 adventure_save.campaign.room=(Save4U8)room;adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;
 changed();save_game();dirty=0;
}
static COLD void say(int a,int b){persist();dialogue(a,b,PLAY);}
static COLD int enqueue(CovenantsRequest r){
 unsigned i;if(event_handle)return 0;
 for(i=event_index;i<event_count;i++)if(equal_bytes(&events[i],&r,sizeof r))return 1;
 if(event_count>=4)return 0;
 if(!event_count){event_scene=scene;event_attempt=attempt;}
 events[event_count++]=r;changed();return 1;
}
static COLD int simple(unsigned op,unsigned area,unsigned q,unsigned bit,unsigned source){
 CovenantsRequest r={0};r.operation=op;r.room=area;r.quest=q;r.bit=bit;r.source=source;return enqueue(r);
}
static COLD int offer(unsigned q){return state(q)?1:simple(COVENANTS_REQUEST_QUEST_OFFER,(unsigned)room,q,0,0);}
static COLD int objective(unsigned q,unsigned bit){
 if(done(q)||(bits(q)&bit))return 1;
 return simple(COVENANTS_REQUEST_ORDINARY_OBJECTIVE,(unsigned)room,q,bit,0);
}
static COLD int claim(unsigned q){return simple(COVENANTS_REQUEST_QUEST_CLAIM,(unsigned)room,q,0,0);}
static COLD int complete_covenant(void){
 unsigned i=(unsigned)room-70;
 if(i>=8||fulfilled(i))return 0;
 return simple(COVENANTS_REQUEST_COVENANT_COMPLETE,(unsigned)room,0,0,i+1);
}
COLD int covenants_game_event_pending(void){return event_count!=0;}
COLD int covenants_game_route_allowed(unsigned a,unsigned s){return spawn_allowed(a,s);}
COLD int covenants_game_request_enter(unsigned a,unsigned s){
 if(!spawn_allowed(a,s))return 0;
 if(adventure_save.quests.region_flags[7]&(1u<<(a-70)))return 1;
 if(event_count)return 0;
 transition_area=a;transition_spawn=s;transition_ready=0;
 return simple(COVENANTS_REQUEST_VISIT,a,0,0,0)?2:0;
}
COLD int covenants_game_take_transition(unsigned*a,unsigned*s){
 if(!transition_ready)return 0;
 if(a)*a=transition_area;
 if(s)*s=transition_spawn;
 transition_ready=transition_area=0;return 1;
}
static COLD void present(const CovenantsRequest*r,int result){
 int good=result==COVENANTS_CHANGED||result==COVENANTS_NOW_READY||result==COVENANTS_REWARDED;
 if(r->operation==COVENANTS_REQUEST_VISIT){
  if(good||result==COVENANTS_UNCHANGED)transition_ready=1;else transition_area=0;return;
 }
 if(r->operation==COVENANTS_REQUEST_ANCHOR){
  if(good||result==COVENANTS_UNCHANGED){checkpoint_spawn=room==70?4:3;adventure_save.campaign.spawn=checkpoint_spawn;game_health_fill();dirty=1;toast(TX_CV_REST);}return;
 }
 if(!good){if(result!=COVENANTS_UNCHANGED)toast(result==COVENANTS_FULL?TX_CV_FULL:result==COVENANTS_SPACE_RESERVED||result==COVENANTS_COVERAGE_LOSS?TX_CV_RESERVED:result==COVENANTS_ID_EXHAUSTED?TX_CV_ID_LIMIT:TX_CV_FIT);return;}
 dirty=1;
 if(r->operation==COVENANTS_REQUEST_UNIQUE_INVITE){invite_confirm=0;progression_refresh();toast(TX_CV_INVITED);}
 else if(r->operation==COVENANTS_REQUEST_COVENANT_COMPLETE){invalidate_cast();invite_confirm=0;toast(TX_CV_FULFILLED);}
 else if(r->operation==COVENANTS_REQUEST_QUEST_CLAIM){progression_refresh();if(r->quest==63)setting[23]=1;toast(TX_CV_RECEIVED);}
 else if(result==COVENANTS_NOW_READY)toast(TX_CV_READY);
 changed();
}
COLD unsigned covenants_game_prepare_event(void){
 unsigned status;int result;CovenantsRequest r;
 if(!event_count)return SAVE5_DONE;
 if(event_scene!=scene||event_attempt!=attempt){covenants_game_cancel_event();return SAVE5_FAILED;}
 r=events[event_index];
 if(!event_handle){
  event_handle=covenants_job_begin(&adventure_save,&r,event_scene,event_attempt);
  if(!event_handle){covenants_game_cancel_event();toast(TX_CV_FIT);return SAVE5_FAILED;}
  return SAVE5_BUSY;
 }
 status=covenants_job_step(event_handle,1024,event_scene,event_attempt);
 if(status==SAVE5_BUSY)return status;
 result=covenants_job_result(event_handle);covenants_job_cancel();event_handle=0;
 if(status==SAVE5_FAILED){covenants_game_cancel_event();toast(TX_CV_FIT);return status;}
 event_index++;present(&r,result);
 if(event_index>=event_count){event_count=event_index=0;persist();return SAVE5_DONE;}
 if(event_scene!=scene||event_attempt!=attempt){covenants_game_cancel_event();return SAVE5_FAILED;}
 return SAVE5_BUSY;
}
/* Included layers keep cold object code and editable source fragments bounded. */
#include "covenants_geometry.inc"
#include "covenants_work.inc"
#include "covenants_fields.inc"
#include "covenants_interact.inc"
#include "covenants_draw.inc"
