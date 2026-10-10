/* Return I: original town consequences, manual invitations and13 situated
 * same-instance trials. Every durable mutation runs through bounded jobs. */
#include "return_game.h"
#include "connected_road_region.h"
#include "return_art.h"
#include "return_quests.h"
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
#define UP 64
#define DOWN 128
extern volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
extern int face,keys,journal_tab;
extern void enter_room(int,int),save_game(void),dialogue(int,int,int),toast(int),text(int,int,int,int),centered(int,int,int),box(int,int,int,int);
extern void return_powers_geometry_changed(void);
extern void rect(int,int,int,int,unsigned char),line(int,int,int,int,int),game_region_warp(int,int),game_health_fill(void),region_form_actor(unsigned,int,int);
unsigned return_game_revision,return_game_journal_selection;
ReturnTrialProof return_game_trial;
static unsigned scene=1,attempt=1,serial;
static unsigned cast_token,cast_id,cast_scene,cast_attempt,cast_party;
static short cast_x,cast_y;
static unsigned char cast_form,cast_command,cast_slot,cast_selected,cast_face,field_hits;
static unsigned char setting[6],phase_step,repeat_active,repeat_used,repeat_stage,repeat_setting;
static unsigned repeat_id,repeat_party;static unsigned char repeat_form,repeat_slot,repeat_command,repeat_selected;
static unsigned char reset_confirm,invite_confirm,dirty,transition_area,transition_spawn,transition_ready;
static unsigned short ambient_clock;
typedef struct {ReturnRequest request;unsigned party;unsigned char selected;} WorldIntent;
static WorldIntent events[4];static unsigned event_handle,event_scene,event_attempt;
static unsigned char event_count,event_index;
#include "return_trials_data.inc"
static const short spawns[8][3][2]={{{240,288},{240,32},{72,272}},{{120,140},{208,116},{40,132}},{{240,288},{432,256}},{{240,288},{432,272}},{{240,288},{432,256}},{{120,140},{208,116}},{{120,140},{208,116}},{{120,140},{208,116}}};
static const unsigned char parents[8]={0,16,17,22,30,58,0,60};
static const unsigned char parent_spawns[8]={0,3,0,4,4,1,0,1};
static const int room_names[8]={TX_RT_ROOM54,TX_RT_ROOM55,TX_RT_ROOM56,TX_RT_ROOM57,TX_RT_ROOM58,TX_RT_ROOM59,TX_RT_ROOM60,TX_RT_ROOM61};
static const int qnames[8]={TX_RT_Q46,TX_RT_Q47,TX_RT_Q48,TX_RT_Q49,TX_RT_Q50,TX_RT_Q51,TX_RT_Q52,TX_RT_Q53};
static const int qclues[8][2]={{TX_RT_CLUE46A,TX_RT_CLUE46B},{TX_RT_CLUE47A,TX_RT_CLUE47B},{TX_RT_CLUE48A,TX_RT_CLUE48B},{TX_RT_CLUE49A,TX_RT_CLUE49B},{TX_RT_CLUE50A,TX_RT_CLUE50B},{TX_RT_CLUE51A,TX_RT_CLUE51B},{TX_RT_CLUE52A,TX_RT_CLUE52B},{TX_RT_CLUE53A,TX_RT_CLUE53B}};
static int ab(int n){return n<0?-n:n;}
static int near(int x,int y,int xx,int yy,int r){return ab(x-xx)+ab(y-yy)<=r;}
static int close(int x,int y){int f,s;if(face==1){f=py-y;s=ab(px-x);}else if(face==0){f=y-py;s=ab(px-x);}else if(face==2){f=px-x;s=ab(py-y);}else{f=x-px;s=ab(py-y);}return f>=6&&f<=26&&s<=10&&s<=f/2;}
static void changed(void){return_game_revision++;progression_revision++;}
static unsigned party(void){const CreatureRoster*r=&adventure_save.roster;return r->party[0]|(unsigned)r->party[1]<<8|(unsigned)r->party[2]<<16|(unsigned)r->party[3]<<24;}
static CreatureInstance*active(void){unsigned p=adventure_save.roster.selected_party,s;if(!summoned||p>=4)return 0;s=adventure_save.roster.party[p];return s<160?&adventure_save.roster.instances[s]:0;}
static unsigned state(unsigned q){unsigned s=save5_quest_state(&adventure_save.quests,q),bits=adventure_save.quests.objectives[q],i;if(s==3)return 3;for(i=event_index;i<event_count;i++){ReturnRequest*r=&events[i].request;if(r->quest==q){if(r->operation==RETURN_REQUEST_QUEST_OFFER&&!s)s=1;if(r->operation==RETURN_REQUEST_QUEST_PROGRESS){bits|=r->bit;if(!s)s=1;}}}return s&&bits==return_quest_mask(q)?2:s;}
static int done(unsigned q){return save5_quest_state(&adventure_save.quests,q)==3;}
static void invalidate_cast(void){cast_token=cast_id=cast_scene=cast_attempt=0;field_hits=0;}
static void cancel_proof(void){return_game_trial.index=255;return_game_trial.instance_id=0;repeat_active=repeat_stage=0;invite_confirm=0;invalidate_cast();if(++attempt==0)++attempt;}
void return_game_cancel_event(void){if(event_handle)return_job_cancel();event_handle=event_count=event_index=0;transition_ready=transition_area=0;}
static COLD void persist(void){if(dirty){adventure_save.campaign.room=(Save4U8)room;adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;changed();save_game();dirty=0;}}
static COLD void say(int a,int b){persist();dialogue(a,b,PLAY);}
static COLD int enqueue(ReturnRequest r){unsigned i;if(event_handle)return 0;for(i=event_index;i<event_count;i++){ReturnRequest*p=&events[i].request;if(p->operation==r.operation&&p->room==r.room&&p->quest==r.quest&&p->bit==r.bit&&p->source==r.source&&p->instance_id==r.instance_id&&p->key==r.key)return 1;if(r.operation==RETURN_REQUEST_QUEST_PROGRESS&&p->operation==RETURN_REQUEST_QUEST_OFFER&&p->quest==r.quest){*p=r;return 1;}}if(event_count>=4)return 0;if(!event_count){event_scene=scene;event_attempt=attempt;}events[event_count].request=r;events[event_count].party=party();events[event_count].selected=adventure_save.roster.selected_party;event_count++;changed();return 1;}
static COLD int simple(unsigned op,unsigned area,unsigned q,unsigned bit,unsigned source){ReturnRequest r={0};r.operation=op;r.room=area;r.quest=q;r.bit=bit;r.source=source;return enqueue(r);}
static COLD int offer(unsigned q){if(state(q))return 1;if(!return_quest_available(&adventure_save,q))return 0;return simple(RETURN_REQUEST_QUEST_OFFER,0,q,0,0);}
static COLD int objective(unsigned q,unsigned bit){if(done(q)||(adventure_save.quests.objectives[q]&bit))return 1;if(!return_quest_available(&adventure_save,q))return 0;return simple(RETURN_REQUEST_QUEST_PROGRESS,0,q,bit,0);}
static COLD int claim(unsigned q){return simple(RETURN_REQUEST_QUEST_CLAIM,0,q,0,q==47?1:q==49?2:0);}
static COLD int report(unsigned q,unsigned bit,int a,int b){if(state(q)==2){claim(q);return 1;}if(done(q)){say(a,b);return 1;}if(offer(q)){if(bit)objective(q,bit);if(state(q)==2)claim(q);else say(a,b);}else say(TX_RT_LOCKED,TX_RT_LOCKEDB);return 1;}
int return_game_is_room(unsigned a){return a>=54&&a<=61;}
unsigned return_game_spawn_count(unsigned a){return !return_game_is_room(a)?0:a<=55?3:2;}
int return_game_spawn(unsigned a,unsigned s,int*x,int*y){if(s>=return_game_spawn_count(a))return 0;if(x)*x=spawns[a-54][s][0];if(y)*y=spawns[a-54][s][1];return 1;}
int return_game_can_enter(unsigned a){return return_can_enter(&adventure_save,a);}
int return_game_request_enter(unsigned a,unsigned s){if(s>=return_game_spawn_count(a)||!return_can_enter(&adventure_save,a))return 0;if(s==2&&a<=55&&!(adventure_save.quests.anchors[5]&(1u<<(a-54))))return 0;if(adventure_save.quests.region_flags[5]&(1u<<(a-54)))return 1;if(event_count)return 0;transition_area=a;transition_spawn=s;transition_ready=0;return simple(RETURN_REQUEST_VISIT,a,0,0,0)?2:0;}
int return_game_take_transition(unsigned*a,unsigned*s){if(!transition_ready)return 0;if(a)*a=transition_area;if(s)*s=transition_spawn;transition_ready=transition_area=0;return 1;}
void return_game_reset(void){unsigned i;return_game_cancel_event();cancel_proof();if(++scene==0)++scene;for(i=0;i<6;i++)setting[i]=0;phase_step=0;repeat_used=0;reset_confirm=0;ambient_clock=0;changed();}
int return_game_enter(unsigned a,unsigned s){int x,y;if(!return_game_spawn(a,s,&x,&y)||!return_can_enter(&adventure_save,a)||!(adventure_save.quests.region_flags[5]&(1u<<(a-54))))return 0;if(s==2&&a<=55&&!(adventure_save.quests.anchors[5]&(1u<<(a-54))))return 0;return_game_reset();room=a;checkpoint_spawn=s;px=x;py=y;adventure_save.campaign.room=a;adventure_save.campaign.spawn=s;if(a==55&&(adventure_save.quests.objectives[47]&2))setting[0]=setting[1]=1;if(a==58&&(adventure_save.quests.objectives[49]&1))setting[0]=setting[1]=1;if(a==58&&(adventure_save.quests.objectives[49]&2))setting[2]=1;if(a==57&&(adventure_save.quests.objectives[48]&2))setting[2]=1;if(a==60&&(adventure_save.quests.objectives[51]&2))phase_step=5;dirty=1;persist();return 1;}
int return_game_is_sanctuary(void){return (room==54&&(adventure_save.quests.anchors[5]&1)&&near(px,py,72,256,32))||(room==55&&(adventure_save.quests.anchors[5]&2)&&near(px,py,40,116,32));}
void return_game_selection_changed(void){if(!return_game_is_room((unsigned)room)&&!event_count)return;return_game_cancel_event();cancel_proof();changed();}
void return_game_menu_abandoned(void){if(return_game_is_room((unsigned)room)&&(return_game_trial.index<13||repeat_active)){return_game_cancel_event();cancel_proof();changed();}}
/* At most two moving rectangles; no corridor can seal the southern escape. */
static unsigned dynamic_rects(unsigned area,const unsigned char*s,short out[2][4]){if(area==55){for(unsigned i=0;i<2;i++){out[i][0]=(short)(88+i*48);out[i][1]=s[i]?56:88;out[i][2]=s[i]?8:24;out[i][3]=s[i]?24:8;}return 2;}if(area==57){out[0][0]=s[2]?432:352;out[0][1]=200;out[0][2]=s[2]?16:64;out[0][3]=10;return 1;}return 0;}
COLD unsigned return_game_collision_rects(short out[2][4]){unsigned i,n;
 if(!out||!return_game_is_room((unsigned)room))return 0;
 n=dynamic_rects((unsigned)room,setting,out);
 for(i=0;i<n;i++){short *r=out[i];r[2]=(short)(r[0]+r[2]+4);r[3]=(short)(r[1]+r[3]+4);r[0]-=5;r[1]-=5;}
 return n;
}
static int rect_hit(int x,int y,const short*r){return x+5>=r[0]&&x-5<r[0]+r[2]&&y+5>=r[1]&&y-5<r[1]+r[3];}
static int dynamic_solid(unsigned area,const unsigned char*s,int x,int y){short rr[2][4];unsigned n=dynamic_rects(area,s,rr),i;for(i=0;i<n;i++)if(rect_hit(x,y,rr[i]))return 1;return 0;}
static COLD int set_mechanism(unsigned index,unsigned value){unsigned char next[6];unsigned i;if(index>=6)return 0;for(i=0;i<6;i++)next[i]=setting[i];next[index]=(unsigned char)value;if(dynamic_solid((unsigned)room,next,px,py)){toast(TX_RT_STEP_CLEAR);return 0;}setting[index]=(unsigned char)value;return_powers_geometry_changed();changed();return 1;}
COLD int return_game_geometry_solid(unsigned a,int x,int y){const ReturnArtRoom*r;const unsigned short*b;unsigned n,i;if(!return_game_is_room(a))return 1;{int seam=road_region_point(a,x,y);if(seam>=0)return seam;}r=&return_art_rooms[a-54];if(x<5||y<5||x>r->width-6||y>r->height-6)return 1;b=r->collision_bands+r->collision_rows[y];n=*b++;for(i=0;i<n;i++,b+=2)if(x>=b[0]&&x<b[1])return 1;return 0;}
int return_game_solid(int x,int y){return return_game_is_room((unsigned)room)?(return_game_geometry_solid((unsigned)room,x,y)||dynamic_solid((unsigned)room,setting,x,y)):0;}
COLD int return_game_clear_box(int x0,int y0,int x1,int y1){const ReturnArtRoom*r;const unsigned short*prev=0;int y;if(!return_game_is_room((unsigned)room)||x0>x1||y0>y1)return 0;if(road_region_box_added((unsigned)room,x0,y0,x1,y1))return 0;r=&return_art_rooms[room-54];if(x0<5||y0<5||x1>r->width-6||y1>r->height-6)return 0;for(y=y0;y<=y1;y++){const unsigned short*b=r->collision_bands+r->collision_rows[y];unsigned n,i;if(b==prev)continue;prev=b;n=*b++;for(i=0;i<n;i++,b+=2){if(x1<b[0])break;if(x0<b[1])return 0;}}{short rr[2][4];unsigned n=dynamic_rects((unsigned)room,setting,rr),i;for(i=0;i<n;i++)if(x1>=rr[i][0]-5&&x0<rr[i][0]+rr[i][2]+5&&y1>=rr[i][1]-5&&y0<rr[i][1]+rr[i][3]+5)return 0;}return 1;}
/* Local same-call interval proof avoids repeated ROM dispatch per ray pixel. */
static unsigned span(const ReturnArtRoom*r,int x,int y){const unsigned short*b=r->collision_bands+r->collision_rows[y];unsigned n=*b++,i;int lo=5,hi=r->width-6;for(i=0;i<n;i++,b+=2){if(x>=b[0]&&x<b[1])return 0;if(b[1]<=x)lo=b[1]>lo?b[1]:lo;else{hi=b[0]-1<hi?b[0]-1:hi;break;}}{short rr[2][4];unsigned n=dynamic_rects((unsigned)room,setting,rr),i;for(i=0;i<n;i++){short*p=rr[i];if(y<p[1]-5||y>=p[1]+p[3]+5)continue;if(x>=p[0]-5&&x<p[0]+p[2]+5)return 0;if(p[0]+p[2]+4<x){if(p[0]+p[2]+5>lo)lo=p[0]+p[2]+5;}else if(p[0]-6<hi)hi=p[0]-6;}}return ((unsigned)lo<<16)|(unsigned)hi;}
COLD int return_game_supercover(int x,int y,int tx,int ty){const ReturnArtRoom*r;unsigned s;int dx,dy,sx,sy,e;if(!return_game_is_room((unsigned)room))return-1;{int seam=road_region_ray((unsigned)room,x,y,tx,ty,return_game_solid);if(seam>=0)return seam;}if((unsigned)x>1023u||(unsigned)y>1023u||(unsigned)tx>1023u||(unsigned)ty>1023u)return 0;dx=ab(tx-x);dy=ab(ty-y);if(dx+dy>160||return_game_solid(x,y)||return_game_solid(tx,ty))return 0;r=&return_art_rooms[room-54];sx=x<tx?1:-1;sy=y<ty?1:-1;dy=-dy;e=dx+dy;s=span(r,x,y);if(!s)return 0;while(x!=tx||y!=ty){int twice=e*2,nx=x,ny=y;if(twice>=dy){e+=dy;nx+=sx;}if(twice<=dx){e+=dx;ny+=sy;}if(nx!=x&&((unsigned)nx<(s>>16)||(unsigned)nx>(s&65535)))return 0;if(ny!=y){s=span(r,x,ny);if(!s||(unsigned)nx<(s>>16)||(unsigned)nx>(s&65535))return 0;}x=nx;y=ny;}return 1;}
void return_game_collision_inputs(unsigned out[3]){if(out){out[0]=setting[0]|((unsigned)setting[1]<<8);out[1]=setting[2];out[2]=scene;}}
unsigned return_game_enemy_spawns(unsigned a,const ReturnEnemySpawn**out){static const ReturnEnemySpawn e54[]={{104,248,5,0,0},{416,240,5,0,1}},e56[]={{208,64,5,0,2},{368,264,5,0,4}},e57[]={{208,240,5,0,3},{288,64,5,0,1},{432,176,5,2,2}},e58[]={{192,176,5,0,0},{432,48,5,0,4}},e61[]={{40,32,5,0,1},{200,32,5,0,3},{120,112,6,2,2}};const ReturnEnemySpawn*p=a==54?e54:a==56?e56:a==57?e57:a==58?e58:a==61?e61:0;if(out)*out=p;return a==54||a==56||a==58?2:a==57||a==61?3:0;}
#include "return_trials.inc"
#include "return_events.inc"
#include "return_interact.inc"
#include "return_fields.inc"
#include "return_game_draw.inc"
