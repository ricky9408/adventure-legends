/* Shared Horizons: a walkable makers' circuit and bound local work attempts.
 * Durable effects are exclusively the incremental horizons_job transaction. */
#include "horizons_game.h"
#include "connected_road_region.h"
#include "horizons_art.h"
#include "horizons_quests.h"
#include "horizons_powers.h"
#include "return_powers.h"
#include "horizons_audio.h"
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
extern void enter_room(int,int),save_game(void),dialogue(int,int,int),toast(int),text(int,int,int,int),centered(int,int,int),box(int,int,int,int);
extern void rect(int,int,int,int,unsigned char),line(int,int,int,int,int),game_region_warp(int,int),game_health_fill(void),region_form_actor(unsigned,int,int);
extern void return_powers_geometry_changed(void);
extern int game_region_actor_overlap(int,int,int,int);
extern void game_horizons_performance_start(void),game_horizons_performance_stop(void);
unsigned horizons_game_revision,horizons_game_journal_selection;
static unsigned scene=1,attempt=1,serial,ambient;
static unsigned char setting[16],reset_confirm,invite_confirm,dirty,transition_area,transition_spawn,transition_ready;
static short carriage_x;
static unsigned wax_token;
static unsigned short performance_ticks;
typedef struct {unsigned id,scene,attempt,party,token;short x,y;unsigned char slot,selected,form,command,face,hits[2];} Cast;
static Cast cast;
enum {MODE_NONE,MODE_INITIAL,MODE_REPEAT,MODE_TRIAL,MODE_PRACTICE};
typedef struct {unsigned id,party,scene,attempt,cast_token;unsigned char mode,index,slot,selected,form,command,stage,setting,hits,walk,replay;} Proof;
static Proof proof;
typedef struct {HorizonsRequest request;unsigned party;unsigned char selected;} WorldIntent;
static WorldIntent events[4];static unsigned event_handle,event_scene,event_attempt;static unsigned char event_count,event_index;
static const unsigned char spawn_counts[8]={6,4,2,4,3,4,1,2};
static const short spawns[8][6][2]={{{240,288},{448,160},{32,160},{240,32},{72,272},{416,32}},{{24,128},{456,128},{208,32},{400,32}},{{120,140},{24,112}},{{32,160},{448,160},{240,32},{80,272}},{{120,288},{48,24},{208,272}},{{80,272},{400,272},{240,32},{32,144}},{{120,140}},{{120,140},{208,112}}};
static const int room_names[8]={TX_HZ_ROOM62,TX_HZ_ROOM63,TX_HZ_ROOM64,TX_HZ_ROOM65,TX_HZ_ROOM66,TX_HZ_ROOM67,TX_HZ_ROOM68,TX_HZ_ROOM69};
static const int qnames[6]={TX_HZ_Q54,TX_HZ_Q55,TX_HZ_Q56,TX_HZ_Q57,TX_HZ_Q58,TX_HZ_Q59};
static const int qclues[6][2]={{TX_HZ_CLUE54A,TX_HZ_CLUE54B},{TX_HZ_CLUE55A,TX_HZ_CLUE55B},{TX_HZ_CLUE56A,TX_HZ_CLUE56B},{TX_HZ_CLUE57A,TX_HZ_CLUE57B},{TX_HZ_CLUE58A,TX_HZ_CLUE58B},{TX_HZ_CLUE59A,TX_HZ_CLUE59B}};
/* Each distinct workbench owns its invitation, controls, marked target and walk.
 * Optional sources are started explicitly; first four are story invitations. */
typedef struct {unsigned char area,form,command,claim;short invite[2],manual[2],target[2],walk[2];int clue[2];} SourceDef;
static const SourceDef sources[12]={
 {62,105,106,54,{352,224},{352,256},{352,176},{384,208},{TX_HZ_SOURCE1A,TX_HZ_SOURCE1B}},
 {63,107,108,55,{416,96},{416,128},{392,96},{440,96},{TX_HZ_SOURCE2A,TX_HZ_SOURCE2B}},
 {66,109,110,56,{64,256},{64,224},{48,240},{80,272},{TX_HZ_SOURCE3A,TX_HZ_SOURCE3B}},
 {68,111,112,57,{192,112},{160,136},{176,112},{216,112},{TX_HZ_SOURCE4A,TX_HZ_SOURCE4B}},
 {63,113,114,54,{64,64},{80,96},{48,64},{112,96},{TX_HZ_SOURCE5A,TX_HZ_SOURCE5B}},
 {64,114,115,54,{200,112},{176,120},{200,104},{160,112},{TX_HZ_SOURCE6A,TX_HZ_SOURCE6B}},
 {65,115,116,54,{416,256},{384,224},{384,256},{416,224},{TX_HZ_SOURCE7A,TX_HZ_SOURCE7B}},
 {67,116,117,54,{64,192},{48,144},{64,144},{96,192},{TX_HZ_SOURCE8A,TX_HZ_SOURCE8B}},
 {69,117,118,54,{208,112},{48,48},{192,64},{176,112},{TX_HZ_SOURCE9A,TX_HZ_SOURCE9B}},
 {66,118,119,54,{48,208},{48,176},{48,160},{80,208},{TX_HZ_SOURCE10A,TX_HZ_SOURCE10B}},
 {62,119,120,54,{304,272},{304,240},{320,240},{336,272},{TX_HZ_SOURCE11A,TX_HZ_SOURCE11B}},
 {68,120,121,54,{48,112},{80,112},{80,88},{48,136},{TX_HZ_SOURCE12A,TX_HZ_SOURCE12B}}
};
typedef struct {unsigned char area,form,command;short lectern[2],manual[2],target[2][2],walk[2][2];int name,clue[2];} TrialDef;
static const TrialDef trials[4]={
 {64,105,106,{32,48},{32,80},{{64,56},{176,56}},{{64,120},{120,112}},TX_HZ_T41,{TX_HZ_T41A,TX_HZ_T41B}},
 {67,107,108,{368,208},{300,232},{{288,208},{312,208}},{{400,240},{368,272}},TX_HZ_T42,{TX_HZ_T42A,TX_HZ_T42B}},
 {66,109,110,{48,72},{80,160},{{144,248},{176,248}},{{80,248},{64,288}},TX_HZ_T43,{TX_HZ_T43A,TX_HZ_T43B}},
 {68,111,112,{48,112},{80,112},{{80,88},{160,88}},{{112,112},{160,136}},TX_HZ_T44,{TX_HZ_T44A,TX_HZ_T44B}}
};
static const TrialDef practice_trials[4]={
 {63,106,107,{336,128},{336,104},{{336,64},{368,96}},{{336,112},{400,112}},TX_HZ_T41,{TX_HZ_P41A,TX_HZ_P41B}},
 {67,108,109,{368,208},{300,232},{{288,208},{312,208}},{{400,240},{368,272}},TX_HZ_T42,{TX_HZ_P42A,TX_HZ_P42B}},
 {66,110,111,{48,72},{80,160},{{144,248},{176,248}},{{80,248},{64,288}},TX_HZ_T43,{TX_HZ_P43A,TX_HZ_P43B}},
 {68,112,113,{48,112},{80,112},{{80,88},{116,102}},{{112,112},{160,136}},TX_HZ_T44,{TX_HZ_P44A,TX_HZ_P44B}}
};
static COLD const TrialDef*work_trial(void){return proof.mode==MODE_PRACTICE?&practice_trials[proof.index]:&trials[proof.index];}
static COLD int ab(int n){return n<0?-n:n;}
static COLD int near(int x,int y,int xx,int yy,int r){return ab(x-xx)+ab(y-yy)<=r;}
static COLD int close(int x,int y){int f,s;if(face==1){f=py-y;s=ab(px-x);}else if(face==0){f=y-py;s=ab(px-x);}else if(face==2){f=px-x;s=ab(py-y);}else{f=x-px;s=ab(py-y);}return f>=6&&f<=26&&s<=10&&s<=f/2;}
static COLD void changed(void){horizons_game_revision++;progression_revision++;}
static COLD unsigned party(void){CreatureRoster*r=&adventure_save.roster;return r->party[0]|(unsigned)r->party[1]<<8|(unsigned)r->party[2]<<16|(unsigned)r->party[3]<<24;}
static COLD CreatureInstance*active(void){unsigned p=adventure_save.roster.selected_party,s;if(!summoned||p>=4)return 0;s=adventure_save.roster.party[p];return s<160?&adventure_save.roster.instances[s]:0;}
static COLD unsigned state(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
static COLD int done(unsigned q){return state(q)==3;}
static COLD unsigned bits(unsigned q){return adventure_save.quests.objectives[q];}
static COLD void invalidate_cast(void){cast.token=cast.id=0;cast.hits[0]=cast.hits[1]=0;wax_token=0;}
COLD void horizons_game_revoke_cast(unsigned token){if(token&&token==cast.token)invalidate_cast();}
static COLD void cancel_proof(void){proof.mode=0;proof.id=0;invite_confirm=0;invalidate_cast();if(++attempt==0)++attempt;}
COLD void horizons_game_cancel_event(void){if(event_handle)horizons_job_cancel();event_handle=event_count=event_index=0;transition_ready=transition_area=0;}
static COLD void persist(void){if(dirty){adventure_save.campaign.room=(Save4U8)room;adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;changed();save_game();dirty=0;}}
static COLD void say(int a,int b){persist();dialogue(a,b,PLAY);}
static COLD int enqueue(HorizonsRequest r){unsigned i;if(event_handle)return 0;for(i=event_index;i<event_count;i++){HorizonsRequest*p=&events[i].request;if(p->operation==r.operation&&p->room==r.room&&p->quest==r.quest&&p->bit==r.bit&&p->source==r.source&&p->instance_id==r.instance_id)return 1;}if(event_count>=4)return 0;if(!event_count){event_scene=scene;event_attempt=attempt;}events[event_count].request=r;events[event_count].party=party();events[event_count].selected=adventure_save.roster.selected_party;event_count++;changed();return 1;}
static COLD int simple(unsigned op,unsigned area,unsigned q,unsigned bit,unsigned source){HorizonsRequest r={0};r.operation=op;r.room=area;r.quest=q;r.bit=bit;r.source=source;return enqueue(r);}
static COLD int objective(unsigned q,unsigned bit){if(done(q)||(bits(q)&bit))return 1;return simple(HORIZONS_REQUEST_QUEST_PROGRESS,(unsigned)room,q,bit,0);}
static COLD int offer(unsigned q){if(state(q))return 1;return simple(HORIZONS_REQUEST_QUEST_OFFER,(unsigned)room,q,0,0);}
static COLD int claim(unsigned q){return simple(HORIZONS_REQUEST_QUEST_CLAIM,(unsigned)room,q,0,0);}
static COLD int source_owned(unsigned i){return i<12&&(adventure_save.quests.region_flags[12+i/8]&(1u<<(i%8)));}
static COLD int participant(void){CreatureInstance*c=active();return proof.mode&&proof.scene==scene&&proof.attempt==attempt&&c&&proof.slot<160&&c==&adventure_save.roster.instances[proof.slot]&&c->instance_id==proof.id&&c->form_id==proof.form&&proof.command==progression_command()&&proof.party==party()&&proof.selected==adventure_save.roster.selected_party;}
static COLD void bind(unsigned mode,unsigned index,CreatureInstance*c,unsigned command){cancel_proof();proof.mode=mode;proof.index=index;proof.scene=scene;proof.attempt=attempt;proof.id=c?c->instance_id:0;proof.form=c?c->form_id:0;proof.command=command;proof.slot=c?adventure_save.roster.party[adventure_save.roster.selected_party]:255;proof.selected=adventure_save.roster.selected_party;proof.party=party();proof.stage=proof.setting=proof.hits=proof.walk=proof.replay=0;proof.cast_token=0;}
COLD int horizons_game_is_room(unsigned a){return a>=62&&a<=69;}
COLD unsigned horizons_game_spawn_count(unsigned a){return horizons_game_is_room(a)?spawn_counts[a-62]:0;}
COLD int horizons_game_spawn(unsigned a,unsigned s,int*x,int*y){if(s>=horizons_game_spawn_count(a))return 0;if(x)*x=spawns[a-62][s][0];if(y)*y=spawns[a-62][s][1];return 1;}
COLD int horizons_game_can_enter(unsigned a){return horizons_can_enter(&adventure_save,a);}
static COLD int spawn_allowed(unsigned a,unsigned s){if(s>=horizons_game_spawn_count(a)||!horizons_can_enter(&adventure_save,a))return 0;if((a==62&&s==4)&&!(adventure_save.quests.anchors[6]&1))return 0;if(a==62&&s==5&&(!done(57)||!(adventure_save.quests.region_flags[7]&1)||(adventure_save.quests.objectives[60]&3)!=3))return 0;if((a==65&&s==3)&&!(adventure_save.quests.anchors[6]&2))return 0;if(a==62&&s>=1&&s<=3&&!done(54))return 0;if(((a==63&&s==3)||(a==65&&s==2))&&(!done(55)||!done(56)))return 0;if(((a==67&&s==3)||(a==69&&s==1))&&!done(57))return 0;return 1;}
COLD int horizons_game_route_allowed(unsigned a,unsigned s){return spawn_allowed(a,s);}
COLD int horizons_game_request_enter(unsigned a,unsigned s){if(!spawn_allowed(a,s))return 0;if(adventure_save.quests.region_flags[6]&(1u<<(a-62)))return 1;if(event_count)return 0;transition_area=a;transition_spawn=s;transition_ready=0;return simple(HORIZONS_REQUEST_VISIT,a,0,0,0)?2:0;}
COLD int horizons_game_take_transition(unsigned*a,unsigned*s){if(!transition_ready)return 0;if(a)*a=transition_area;if(s)*s=transition_spawn;transition_ready=transition_area=0;return 1;}
static COLD void reconstruct(void){unsigned i;for(i=0;i<16;i++)setting[i]=0;wax_token=0;if(room==62&&(bits(54)&2))setting[0]=3;if(room==63&&(bits(55)&2)){setting[0]=2;setting[1]=1;}if(room==64&&(bits(55)&4)){setting[0]=5;setting[1]=1;setting[2]=5;}if(room==65&&(bits(56)&2)){setting[0]=1;setting[1]=3;}if(room==66&&(bits(56)&4)){setting[0]=1;setting[1]=6;}if(room==67){setting[2]=1;if(bits(57)&1)setting[0]=1;if(bits(57)&2)setting[1]=1;}if(room==68&&(bits(57)&4))setting[0]=7;carriage_x=192+setting[0]*32;}
COLD void horizons_game_reset(void){game_horizons_performance_stop();performance_ticks=0;horizons_game_cancel_event();cancel_proof();if(++scene==0)++scene;reset_confirm=0;ambient=0;reconstruct();changed();}
COLD int horizons_game_enter(unsigned a,unsigned s){int x,y;if(!horizons_game_spawn(a,s,&x,&y)||!spawn_allowed(a,s)||!(adventure_save.quests.region_flags[6]&(1u<<(a-62))))return 0;room=a;checkpoint_spawn=s;horizons_game_reset();px=x;py=y;adventure_save.campaign.room=a;adventure_save.campaign.spawn=s;dirty=1;persist();return 1;}
COLD int horizons_game_is_sanctuary(void){return(room==62&&(adventure_save.quests.anchors[6]&1)&&near(px,py,72,256,32))||(room==65&&(adventure_save.quests.anchors[6]&2)&&near(px,py,80,256,32));}
COLD void horizons_game_selection_changed(void){if(!horizons_game_is_room((unsigned)room)&&!event_count)return;horizons_game_cancel_event();if(proof.mode==MODE_INITIAL){invalidate_cast();invite_confirm=0;}else cancel_proof();changed();}
COLD void horizons_game_menu_abandoned(void){if(horizons_game_is_room((unsigned)room)&&proof.mode){horizons_game_cancel_event();cancel_proof();changed();}}
/* Only one moving solid, always above the uninterrupted southern promenade. */
static COLD int dynamic_solid(int x,int y){return room==63&&x+5>=carriage_x-7&&x-5<carriage_x+8&&y+5>=65&&y-5<80;}
COLD int horizons_game_geometry_solid(unsigned a,int x,int y){const HorizonsArtRoom*r;const unsigned short*b;unsigned n,i;if(!horizons_game_is_room(a))return 1;{int seam=road_region_point(a,x,y);if(seam>=0)return seam;}r=&horizons_art_rooms[a-62];if(x<5||y<5||x>r->width-6||y>r->height-6)return 1;b=r->collision_bands+r->collision_rows[y];n=*b++;for(i=0;i<n;i++,b+=2)if(x>=b[0]&&x<b[1])return 1;return 0;}
COLD int horizons_game_solid(int x,int y){return horizons_game_is_room((unsigned)room)?horizons_game_geometry_solid((unsigned)room,x,y)||dynamic_solid(x,y):0;}
COLD int horizons_game_clear_box(int x0,int y0,int x1,int y1){const HorizonsArtRoom*r;const unsigned short*prev=0;int y;if(!horizons_game_is_room((unsigned)room)||x0>x1||y0>y1)return 0;if(road_region_box_added((unsigned)room,x0,y0,x1,y1))return 0;r=&horizons_art_rooms[room-62];if(x0<5||y0<5||x1>r->width-6||y1>r->height-6)return 0;for(y=y0;y<=y1;y++){const unsigned short*b=r->collision_bands+r->collision_rows[y];unsigned n,i;if(b==prev)continue;prev=b;n=*b++;for(i=0;i<n;i++,b+=2){if(x1<b[0])break;if(x0<b[1])return 0;}}if(room==63&&x1>=carriage_x-12&&x0<carriage_x+13&&y1>=60&&y0<85)return 0;return 1;}
/* One row-band lookup per changed y, rather than one ROM collision dispatch
 * per supercover cell; the moving carriage still splits the exact free span. */
static COLD unsigned span(const HorizonsArtRoom*r,int x,int y){const unsigned short*b=r->collision_bands+r->collision_rows[y];unsigned n=*b++,i;int lo=5,hi=r->width-6;for(i=0;i<n;i++,b+=2){if(x>=b[0]&&x<b[1])return 0;if(b[1]<=x)lo=b[1]>lo?b[1]:lo;else{hi=b[0]-1<hi?b[0]-1:hi;break;}}if(room==63&&y>=60&&y<85){int left=carriage_x-12,right=carriage_x+13;if(x>=left&&x<right)return 0;if(right<=x){if(right>lo)lo=right;}else if(left-1<hi)hi=left-1;}return ((unsigned)lo<<16)|(unsigned)hi;}
COLD int horizons_game_supercover(int x,int y,int tx,int ty){const HorizonsArtRoom*r;unsigned s;int dx,dy,sx,sy,e;if(!horizons_game_is_room((unsigned)room))return-1;{int seam=road_region_ray((unsigned)room,x,y,tx,ty,horizons_game_solid);if(seam>=0)return seam;}if((unsigned)x>1023u||(unsigned)y>1023u||(unsigned)tx>1023u||(unsigned)ty>1023u)return 0;dx=ab(tx-x);dy=ab(ty-y);if(dx+dy>160||horizons_game_solid(x,y)||horizons_game_solid(tx,ty))return 0;r=&horizons_art_rooms[room-62];sx=x<tx?1:-1;sy=y<ty?1:-1;dy=-dy;e=dx+dy;s=span(r,x,y);if(!s)return 0;while(x!=tx||y!=ty){int twice=e*2,nx=x,ny=y;if(twice>=dy){e+=dy;nx+=sx;}if(twice<=dx){e+=dx;ny+=sy;}if(nx!=x&&((unsigned)nx<(s>>16)||(unsigned)nx>(s&65535)))return 0;if(ny!=y){s=span(r,x,ny);if(!s||(unsigned)nx<(s>>16)||(unsigned)nx>(s&65535))return 0;}x=nx;y=ny;}return 1;}
COLD void horizons_game_collision_inputs(unsigned out[3]){if(out){out[0]=(unsigned)(unsigned short)carriage_x;out[1]=setting[3]|((unsigned)setting[4]<<8);out[2]=scene;}}
COLD unsigned horizons_game_enemy_spawns(unsigned a,const HorizonsEnemySpawn**out){static const HorizonsEnemySpawn e63[]={{176,104,5,0,0},{304,104,5,0,1},{440,64,5,2,2}},e65[]={{64,64,5,0,2},{368,64,5,0,4},{208,240,5,2,1}},e66[]={{32,104,5,0,0},{208,176,5,0,4}},e67[]={{176,192,5,0,2},{304,152,5,0,1},{400,96,5,2,3}},e69[]={{120,112,5,0,2}};const HorizonsEnemySpawn*p=a==63?e63:a==65?e65:a==66?e66:a==67?e67:a==69?e69:0;if(out)*out=p;return a==63||a==65||a==67?3:a==66?2:a==69?1:0;}
#include "horizons_attempts.inc"
#include "horizons_events.inc"
#include "horizons_fields.inc"
#include "horizons_interact.inc"
#include "horizons_game_draw.inc"
