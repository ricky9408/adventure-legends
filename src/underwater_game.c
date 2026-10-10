/* Nacreway: original world, reversible acoustic/ballast puzzles and sixteen
 * same-individual field trials. Durable changes use underwater_quests only. */
#include "underwater_game.h"
#include "connected_road_region.h"
#include "magma_game.h"
#include "underwater_art.h"
#include "underwater_quests.h"
#include "progression.h"
#include "assets.h"
#ifdef UNDERWATER_GAME_HOST_TEST
#include "underwater_game_test_ui.h"
#else
#include "ui.h"
#endif
#if defined(__arm__)
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
#define COLLISION_HOT __attribute__((section(".iwram.text.underwater_collision"),long_call,noinline))
#else
#define COLD
#define COLLISION_HOT
#endif
#define PLAY 1
#define KEY_A 1
#define KEY_B 2
#define RIGHT 16
#define LEFT 32
#define UP 64
#define DOWN 128
#define JOURNAL_TAB 9
extern volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
extern int face,keys,journal_tab;
extern void enter_room(int,int),save_game(void),dialogue(int,int,int),toast(int),text(int,int,int,int),centered(int,int,int),box(int,int,int,int);
extern void rect(int,int,int,int,unsigned char),line(int,int,int,int,int),game_region_warp(int,int);
extern void underwater_powers_geometry_changed(void);
unsigned underwater_game_revision,underwater_game_journal_selection;
UnderwaterPuzzle underwater_game_puzzle;
UnderwaterTrialProof underwater_game_trial;
unsigned char underwater_game_guardian_stage,underwater_game_guardian_ticks,underwater_game_guardian_hits;
static unsigned room_generation=1,action_serial;
static unsigned action_token[4],cast_id,cast_form,cast_generation,cast_command;
static unsigned char action_hits,field_hits,dirty,door_notice,reset_pending,projection;
static unsigned char source_state[8],repeat_state[8],repeat_used,branch_visible;
static unsigned char lesson,parade,parade_rotation,migration,bench,glass,guardian_side,guardian_hurt,route_stage;
typedef struct {unsigned instance_id;unsigned char op,area,quest,bit,source,slot,family,key;} WorldIntent;
static WorldIntent events[4];
static unsigned event_handle,event_generation;
static unsigned char event_count,event_index,transition_area,transition_spawn,transition_ready;
static COLD int queue(unsigned op,unsigned area,unsigned quest,unsigned bit,unsigned source,unsigned slot,unsigned family,unsigned key,unsigned id);
static COLD void event_present(const WorldIntent*,int);
static unsigned short world_clock;
static const short spawns[8][4][2]={
 {{240,288},{240,32},{80,272},{448,160}},{{240,288},{400,48},{64,272}},
 {{240,288},{240,32},{448,160}},{{120,140},{208,112}},{{120,140},{208,112}},
 {{240,288},{432,112},{32,160}},{{120,140},{208,112},{32,112}},{{120,140},{208,112}}};
static int ab(int x){return x<0?-x:x;}
static int near(int x,int y,int xx,int yy,int r){return ab(x-xx)+ab(y-yy)<=r;}
/* Deliberate facing cone; reset/talk/rest never steal an adjacent object A. */
static int close(int x,int y){int f,s;if(face==1){f=py-y;s=ab(px-x);}else if(face==0){f=y-py;s=ab(px-x);}else if(face==2){f=px-x;s=ab(py-y);}else{f=x-px;s=ab(py-y);}return f>=6&&f<=26&&s<=10&&s<=f/2;}
static int hit(int x,int y,int bx,int by,int w,int h){return x+5>=bx&&x-5<bx+w&&y+5>=by&&y-5<by+h;}
int underwater_game_is_room(unsigned a){return a>=46&&a<=53;}
unsigned underwater_game_spawn_count(unsigned a){return !underwater_game_is_room(a)?0:a==46?4:a==47||a==48||a==51||a==52?3:2;}
int underwater_game_spawn(unsigned a,unsigned s,int*x,int*y){if(s>=underwater_game_spawn_count(a))return 0;if(x)*x=spawns[a-46][s][0];if(y)*y=spawns[a-46][s][1];return 1;}
static unsigned state(unsigned q){unsigned s=save5_quest_state(&adventure_save.quests,q),bits=adventure_save.quests.objectives[q],i;if(s==3)return s;for(i=event_index;i<event_count;i++)if(events[i].quest==q){if(events[i].op==UW_REQUEST_QUEST_OFFER&&s==0)s=1;if(events[i].op==UW_REQUEST_QUEST_PROGRESS||events[i].op==UW_REQUEST_QUEST_OBJECTIVE){bits|=events[i].bit;if(s==0)s=1;}}return s&&bits==underwater_quest_mask(q)?2:s;}
static int done(unsigned q){return save5_quest_state(&adventure_save.quests,q)==3;}
static void changed(void){underwater_game_revision++;progression_revision++;}
static COLD void persist(void){if(dirty){adventure_save.campaign.room=(Save4U8)room;adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;changed();save_game();dirty=0;}}
static COLD void say(int a,int b){persist();dialogue(a,b,PLAY);}
static COLD int offer(unsigned q){if(state(q))return 1;if(!underwater_quest_available(&adventure_save,q))return 0;return queue(UW_REQUEST_QUEST_OFFER,0,q,0,0,0,0,0,0);}
static COLD int objective(unsigned q,unsigned bit){if(done(q)||(adventure_save.quests.objectives[q]&bit))return 0;return queue(UW_REQUEST_QUEST_PROGRESS,0,q,bit,0,0,0,0,0);}
static COLD void claim(unsigned q){queue(UW_REQUEST_QUEST_CLAIM,0,q,0,0,0,0,0,0);}
static int room_text(unsigned a){static const int names[8]={TX_UW_ROOM46,TX_UW_ROOM47,TX_UW_ROOM48,TX_UW_ROOM49,TX_UW_ROOM50,TX_UW_ROOM51,TX_UW_ROOM52,TX_UW_ROOM53};return underwater_game_is_room(a)?names[a-46]:TX_UW_ROOM46;}
static const int qnames[8]={TX_UW_Q38,TX_UW_Q39,TX_UW_Q40,TX_UW_Q41,TX_UW_Q42,TX_UW_Q43,TX_UW_Q44,TX_UW_Q45};
static const int clues[8][2]={{TX_UW_CLUE38A,TX_UW_CLUE38B},{TX_UW_CLUE39A,TX_UW_CLUE39B},{TX_UW_CLUE40A,TX_UW_CLUE40B},{TX_UW_CLUE41A,TX_UW_CLUE41B},{TX_UW_CLUE42A,TX_UW_CLUE42B},{TX_UW_CLUE43A,TX_UW_CLUE43B},{TX_UW_CLUE44A,TX_UW_CLUE44B},{TX_UW_CLUE45A,TX_UW_CLUE45B}};
static COLD void talk(unsigned q){if(state(q)==2){claim(q);return;}if(done(q)){say(TX_UW_KNOWN,TX_UW_HOME);return;}if(offer(q))say(clues[q-38][0],clues[q-38][1]);else say(TX_UW_LOCKED,TX_UW_LOCKEDB);}
static CreatureInstance*active(void){unsigned p=adventure_save.roster.selected_party,s;if(!summoned||p>=4)return 0;s=adventure_save.roster.party[p];if(s>=160)return 0;return &adventure_save.roster.instances[s];}
static unsigned party_signature(void){const CreatureRoster*r=&adventure_save.roster;return r->party[0]|(unsigned)r->party[1]<<8|(unsigned)r->party[2]<<16|(unsigned)r->party[3]<<24;}
static void clear_trial(void){unsigned i,old=projection;if(projection)projection=(unsigned char)(underwater_game_is_room((unsigned)room)&&underwater_puzzle_solid(&underwater_game_puzzle,(unsigned)room,px,py)?2:0);if(old!=projection)underwater_powers_geometry_changed();underwater_game_trial.index=255;underwater_game_trial.instance_id=0;underwater_game_trial.generation=0;underwater_game_trial.slot=255;for(i=0;i<4;i++)underwater_game_trial.setting[i]=0;underwater_game_trial.casts=underwater_game_trial.walk=underwater_game_trial.order=underwater_game_trial.failed=0;}
static void invalidate_actions(void){unsigned i;for(i=0;i<4;i++)action_token[i]=0;cast_id=cast_form=cast_generation=cast_command=0;field_hits=action_hits=0;}
void underwater_puzzle_reset(UnderwaterPuzzle*p,unsigned a){unsigned char*z=(unsigned char*)p;unsigned i;for(i=0;i<sizeof(*p);i++)z[i]=0;p->mode=(unsigned char)a;}
COLLISION_HOT int underwater_game_geometry_solid(unsigned a,int x,int y){const UnderwaterArtRoom*r;const unsigned short*b;unsigned n,i;if(!underwater_game_is_room(a))return 1;{int seam=road_region_point(a,x,y);if(seam>=0)return seam;}r=&underwater_art_rooms[a-46];if(x<5||y<5||x>r->width-6||y>r->height-6)return 1;b=r->collision_bands+r->collision_rows[y];n=*b++;for(i=0;i<n;i++,b+=2)if(x>=b[0]&&x<b[1])return 1;return 0;}
COLLISION_HOT int underwater_puzzle_solid(const UnderwaterPuzzle*p,unsigned a,int x,int y){if(underwater_game_geometry_solid(a,x,y))return 1;
 if(a==50)return p->ballast?hit(x,y,100,48,32,12):hit(x,y,132,80,40,12);
 if(a==51)return p->ballast?hit(x,y,272,128,24,16):hit(x,y,208,128,64,16);
 if(a==53&&!p->ballast)return hit(x,y,48,56,32,12)||hit(x,y,160,56,32,12);
 if(a==52)return hit(x,y,66+p->baffle[0]*16,60,12,24)||hit(x,y,162-p->baffle[1]*16,60,12,24);
 return 0;}
int underwater_puzzle_toggle(UnderwaterPuzzle*p,unsigned a,unsigned t,int x,int y){UnderwaterPuzzle c=*p;
 if(a==50){if(t==0)c.rotation=(c.rotation+1)&3;else if(t==1)c.ballast^=1;else return-1;}
 else if(a==51){if(t==0)c.ballast^=1;else if(t==1)c.aux^=1;else return-1;}
 else if(a==52){if(t>1)return-1;c.baffle[t]^=1;c.echo=0;}
 else if(a==53){if(t!=1)return-1;c.ballast^=1;}
 else return-1;
 if(underwater_puzzle_solid(&c,a,x,y))return 0;
 *p=c;return 1;}
int underwater_puzzle_solved(const UnderwaterPuzzle*p,unsigned a){if(a==50)return p->echo&&p->rotation==1&&p->ballast;if(a==51)return p->ballast&&p->aux&&p->walk;if(a==52)return p->echo&&p->baffle[0]&&!p->baffle[1];return 0;}
COLLISION_HOT int underwater_game_solid(int x,int y){if(!underwater_game_is_room((unsigned)room))return 0;if(projection)return underwater_game_geometry_solid((unsigned)room,x,y);return underwater_puzzle_solid(&underwater_game_puzzle,(unsigned)room,x,y);}
/* Exact conservative broad phase for cast geometry. Inclusive integer bounds
 * use the same radius-five row bands and movable rectangles as solid(). */
static int clear_box_overlaps(int x0,int y0,int x1,int y1,int bx,int by,int w,int h){return x1>=bx-5&&x0<bx+w+5&&y1>=by-5&&y0<by+h+5;}
COLLISION_HOT int underwater_game_clear_box(int x0,int y0,int x1,int y1){
 const UnderwaterArtRoom*r;const unsigned short*previous=0;unsigned a=(unsigned)room;int y;
 if(!underwater_game_is_room(a)||x0>x1||y0>y1)return 0;
 if(road_region_box_added(a,x0,y0,x1,y1))return 0;
 r=&underwater_art_rooms[a-46];
 if(x0<5||y0<5||x1>r->width-6||y1>r->height-6)return 0;
 for(y=y0;y<=y1;y++){const unsigned short*b=r->collision_bands+r->collision_rows[y];unsigned n,i;
  /* Same immutable band identity and unchanged query x interval prove this
   * row has the same result. Movable rectangles are still checked below. */
  if(b==previous)continue;
  previous=b;n=*b++;
  /* collision_bands() emits sorted, disjoint half-open intervals. */
  for(i=0;i<n;i++,b+=2){if(x1<b[0])break;if(x0<b[1])return 0;}
 }
 if(projection)return 1;
 if(a==50)return underwater_game_puzzle.ballast?!clear_box_overlaps(x0,y0,x1,y1,100,48,32,12):!clear_box_overlaps(x0,y0,x1,y1,132,80,40,12);
 if(a==51)return underwater_game_puzzle.ballast?!clear_box_overlaps(x0,y0,x1,y1,272,128,24,16):!clear_box_overlaps(x0,y0,x1,y1,208,128,64,16);
 if(a==52)return !clear_box_overlaps(x0,y0,x1,y1,66+underwater_game_puzzle.baffle[0]*16,60,12,24)&&!clear_box_overlaps(x0,y0,x1,y1,162-underwater_game_puzzle.baffle[1]*16,60,12,24);
 if(a==53&&!underwater_game_puzzle.ballast)return !clear_box_overlaps(x0,y0,x1,y1,48,56,32,12)&&!clear_box_overlaps(x0,y0,x1,y1,160,56,32,12);
 return 1;
}
typedef struct {const UnderwaterArtRoom*r;short rect[2][4];unsigned count;const unsigned short*band;unsigned mask,span;} UnderwaterRayWorld;
static void ray_rect(UnderwaterRayWorld*c,int x,int y,int w,int h){short*r=c->rect[c->count++];r[0]=(short)(x-5);r[1]=(short)(y-5);r[2]=(short)(x+w+4);r[3]=(short)(y+h+4);}
/* Snapshot only this bounded call's geometry parameters, never a cached epoch.
 * Preparation is cold; the repeated exact row scan is the hot operation. */
static COLD void ray_world(UnderwaterRayWorld*c,unsigned a){c->r=&underwater_art_rooms[a-46];c->count=0;c->band=0;c->mask=c->span=0;if(projection)return;
 if(a==50){if(underwater_game_puzzle.ballast)ray_rect(c,100,48,32,12);else ray_rect(c,132,80,40,12);}
 else if(a==51){if(underwater_game_puzzle.ballast)ray_rect(c,272,128,24,16);else ray_rect(c,208,128,64,16);}
 else if(a==52){ray_rect(c,66+underwater_game_puzzle.baffle[0]*16,60,12,24);ray_rect(c,162-underwater_game_puzzle.baffle[1]*16,60,12,24);}
 else if(a==53&&!underwater_game_puzzle.ballast){ray_rect(c,48,56,32,12);ray_rect(c,160,56,32,12);}
}
/* Maximal inclusive empty interval containing x on row y; zero means blocked.
 * The public ray has already proved both endpoints inside world bounds, so
 * monotone Bresenham intermediate x/y also stay within this row table. */
static COLLISION_HOT unsigned ray_span(UnderwaterRayWorld*c,int x,int y){const unsigned short*b=c->r->collision_bands+c->r->collision_rows[y],*band=b;unsigned n,i,mask=0;int lo=5,hi=c->r->width-6;
 for(i=0;i<c->count;i++)if(y>=c->rect[i][1]&&y<=c->rect[i][3])mask|=1u<<i;
 /* Row identity plus dynamic row activity is an exact same-call proof. No
  * interval survives this ray or depends on a remembered collision epoch. */
 if(band==c->band&&mask==c->mask&&c->span&&(unsigned)x>=(c->span>>16)&&(unsigned)x<=(c->span&65535u))return c->span;
 n=*b++;
 for(i=0;i<n;i++,b+=2){if(x>=b[0]&&x<b[1])return 0;if(b[1]<=x){if(b[1]>lo)lo=b[1];}else if(b[0]>x){if(b[0]-1<hi)hi=b[0]-1;break;}}
 for(i=0;i<c->count;i++){const short*r=c->rect[i];if(!(mask&(1u<<i)))continue;if(x>=r[0]&&x<=r[2])return 0;
  if(r[2]<x){if(r[2]+1>lo)lo=r[2]+1;}else if(r[0]>x&&r[0]-1<hi)hi=r[0]-1;}
 c->band=band;c->mask=mask;c->span=((unsigned)lo<<16)|(unsigned)hi;return c->span;
}
COLLISION_HOT int underwater_game_supercover(int x,int y,int tx,int ty){UnderwaterRayWorld context;unsigned span;int ax,ay,sx,sy,e;
 if(!underwater_game_is_room((unsigned)room))return -1;
 {int seam=road_region_ray((unsigned)room,x,y,tx,ty,underwater_game_solid);if(seam>=0)return seam;}
 if((unsigned)x>1023u||(unsigned)y>1023u||(unsigned)tx>1023u||(unsigned)ty>1023u)return 0;
 ax=tx-x;ay=ty-y;sx=ax<0?-1:1;sy=ay<0?-1:1;if(ax<0)ax=-ax;if(ay<0)ay=-ay;
 if(ax+ay>160||underwater_game_solid(x,y)||underwater_game_solid(tx,ty))return 0;
 ray_world(&context,(unsigned)room);span=ray_span(&context,x,y);if(!span)return 0;
 ay=-ay;e=ax+ay;
 while(x!=tx||y!=ty){int twice=e*2,nx=x,ny=y;
  if(twice>=ay){e+=ay;nx+=sx;}if(twice<=ax){e+=ax;ny+=sy;}
  /* Old row at new x, then new row at old x and new x: exactly the two
   * diagonal side cells and destination, without repeated point dispatch. */
  if(nx!=x&&((unsigned)nx<(span>>16)||(unsigned)nx>(span&65535u)))return 0;
  if(ny!=y){span=ray_span(&context,x,ny);if(!span||(unsigned)nx<(span>>16)||(unsigned)nx>(span&65535u))return 0;}
  x=nx;y=ny;
 }return 1;
}
void underwater_game_collision_inputs(unsigned out[3]){if(!out)return;out[0]=projection?256+projection:underwater_game_puzzle.ballast;out[1]=underwater_game_puzzle.baffle[0]|(underwater_game_puzzle.baffle[1]<<8);out[2]=room_generation;}
static void refresh_branches(void){unsigned i;branch_visible=0;for(i=0;i<160;i++){unsigned f=adventure_save.roster.instances[i].form_id;if(f>=49&&f<=72&&(f-49)%3)branch_visible|=(unsigned char)(1u<<((f-49)/3));}}
static void reset_scene(void){unsigned i;clear_trial();invalidate_actions();room_generation++;if(!room_generation)room_generation=1;projection=0;underwater_puzzle_reset(&underwater_game_puzzle,(unsigned)room);for(i=0;i<8;i++)source_state[i]=repeat_state[i]=0;repeat_used=0;refresh_branches();lesson=parade=parade_rotation=migration=bench=glass=reset_pending=door_notice=guardian_hurt=0;world_clock=0;underwater_game_guardian_stage=(unsigned char)((adventure_save.quests.objectives[40]&8)?4:0);underwater_game_guardian_ticks=0;underwater_game_guardian_hits=(unsigned char)(underwater_game_guardian_stage==4?3:0);changed();}
void underwater_game_cancel_event(void){underwater_job_cancel();event_count=event_index=0;event_handle=0;transition_area=transition_ready=0;}
COLD void underwater_game_reset(void){if(magma_game_return_pending())magma_game_cancel_return();underwater_game_cancel_event();route_stage=0;reset_scene();}
void underwater_game_selection_changed(void){if(!underwater_game_is_room((unsigned)room))return;refresh_branches();if(underwater_game_trial.index<16){clear_trial();changed();}invalidate_actions();}
int underwater_game_can_enter(unsigned a){return underwater_can_enter(&adventure_save,a);}
COLD int underwater_game_request_enter(unsigned a,unsigned s){int x,y;if(!underwater_game_spawn(a,s,&x,&y)||!underwater_can_enter(&adventure_save,a))return 0;if(s==2&&(a==46||a==47)&&!(adventure_save.quests.anchors[4]&(1u<<(a-46))))return 0;if(adventure_save.quests.region_flags[4]&(1u<<(a-46)))return 1;if(event_count)return 0;transition_area=(unsigned char)a;transition_spawn=(unsigned char)s;transition_ready=0;return queue(UW_REQUEST_VISIT,a,0,0,0,0,0,0,0)?2:0;}
int underwater_game_take_transition(unsigned*a,unsigned*s){if(!transition_ready)return 0;if(a)*a=transition_area;if(s)*s=transition_spawn;transition_ready=0;transition_area=0;return 1;}
COLD int underwater_game_enter(unsigned a,unsigned s){int x,y;if(!underwater_game_spawn(a,s,&x,&y)||!underwater_can_enter(&adventure_save,a)||!(adventure_save.quests.region_flags[4]&(1u<<(a-46))))return 0;if(s==2&&(a==46||a==47)&&!(adventure_save.quests.anchors[4]&(1u<<(a-46))))return 0;underwater_game_cancel_event();room=(int)a;checkpoint_spawn=(int)s;px=x;py=y;reset_scene();adventure_save.campaign.room=(Save4U8)a;adventure_save.campaign.spawn=(Save4U8)s;if(done(40)&&(adventure_save.quests.objectives[45]&1)){if(a==46&&route_stage==4){route_stage=5;objective(45,2);}else if(a==46&&route_stage!=5)route_stage=1;else if(a==48&&route_stage==1)route_stage=2;else if(a==49&&route_stage==2)route_stage=3;else if(a==48&&route_stage==3)route_stage=4;else if(a!=46&&a!=48&&a!=49)route_stage=0;}if(a>=50)offer(40);dirty=1;persist();return 1;}
unsigned underwater_game_enemy_spawns(unsigned a,const UnderwaterEnemySpawn**out){static const UnderwaterEnemySpawn commons[4]={{96,176,5,0,0},{304,264,5,0,1},{432,112,5,2,3},{304,80,5,0,4}},promenade[2]={{320,272,5,0,2},{416,176,5,0,3}},vestibule[1]={{200,32,4,0,2}},stacks[2]={{64,112,5,0,3},{424,208,5,2,1}},listening[1]={{200,32,4,0,4}},court[2]={{32,40,4,0,2},{208,40,4,0,0}};const UnderwaterEnemySpawn*p=a==47?commons:a==48?promenade:a==50?vestibule:a==51?stacks:a==52?listening:a==53?court:0;if(out)*out=p;return a==47?4:a==48||a==51||a==53?2:a==50||a==52?1:0;}
static COLD int door(unsigned a,unsigned s){if(event_count){transition_area=(unsigned char)a;transition_spawn=(unsigned char)s;transition_ready=2;return 1;}if(!underwater_can_enter(&adventure_save,a)){if(!door_notice){say(TX_UW_LOCKED,TX_UW_LOCKEDB);door_notice=40;}return 1;}persist();enter_room((int)a,(int)s);return 1;}
/* The physical court return preserves the same queued story operation as the
 * old portal. The engine binds its live road landing before this call; door()
 * waits for those intents and lets the normal event callback perform entry. */
COLD int underwater_game_road_departure(unsigned a,unsigned s){
 if(room!=53||a!=52||s!=1||underwater_game_guardian_stage!=4)return 0;
 if(game_state!=PLAY||event_count)return 1;
 offer(45);objective(45,1);persist();return door(a,s);
}
/* Kept for older engine bridge callers; rest now uses the ordinary intent job. */
int underwater_game_save_prepare_pending(void){return 0;}
int underwater_game_prepare_save(void){return 0;}
static COLD void rest(void){queue(UW_REQUEST_ANCHOR,(unsigned)room,0,0,0,0,0,0,0);}
#include "underwater_trials.inc"
#include "underwater_events.inc"
static COLD int recruit(unsigned token,int repeat){if(repeat&&(repeat_used&(1u<<(token-1)))){toast(TX_UW_INVITED);return 1;}queue(repeat?UW_REQUEST_REPEAT_RECRUIT:UW_REQUEST_FIELD_RECRUIT,0,0,0,token,0,0,0,0);return 1;}
static COLD void discover(unsigned family,unsigned bit){queue(UW_REQUEST_DISCOVER,0,0,bit,0,0,family,0,0);}
static COLD int source_invite(unsigned token,unsigned goal){if(underwater_source_claimed(&adventure_save,token)){toast(TX_UW_KNOWN);return 1;}if(source_state[token-1]!=goal&&!((token==7&&adventure_save.quests.region_flags[20]==3)||(token==8&&adventure_save.quests.region_flags[21]==7))){toast(TX_UW_OBSERVE);return 1;}return recruit(token,0);}
static COLD int repeat_invite(unsigned token,unsigned goal){if(!(branch_visible&(1u<<(token-1)))){toast(TX_UW_BRANCH_LATER);return 1;}if(repeat_state[token-1]!=goal){toast(TX_UW_REPEAT_CLUE);return 1;}return recruit(token,1);}
/* Trial RESET and room RESET are two explicit A presses on the same isolated
 * pedestal. Walking away cancels confirmation. An invitation never reopens
 * itself after success: a new attempt needs this RESET or room re-entry. */
static void reset_point(int*x,int*y){*x=(room==46||room==47||room==48||room==51)?40:24;*y=(room==46||room==47||room==48||room==51)?276:132;}
static COLD int reset_interact(void){int x,y,xx=120,yy=140;reset_point(&x,&y);if(!close(x,y))return 0;if(!reset_pending){reset_pending=1;toast(TX_UW_RESET_CONFIRM);return 1;}underwater_game_spawn((unsigned)room,0,&xx,&yy);reset_scene();game_region_warp(xx,yy);toast(TX_UW_RESET_DONE);return 1;}
COLD int underwater_game_input(unsigned pressed,unsigned held){(void)held;if(!underwater_game_is_room((unsigned)room)||game_state!=PLAY)return 0;if(pressed&KEY_B)reset_pending=0;return 0;}
static COLD int toggle_main(unsigned n){int r=underwater_puzzle_toggle(&underwater_game_puzzle,(unsigned)room,n,px,py);if(r==1){underwater_powers_geometry_changed();changed();toast(TX_UW_ADJUSTED);}else toast(TX_UW_STEP_CLEAR);return 1;}
COLD int underwater_game_interact(void){if(!underwater_game_is_room((unsigned)room)||game_state!=PLAY)return 0;
 if(reset_interact())return 1;
 if(projection==2){toast(TX_UW_STEP_CLEAR);return 1;}
 /* Trial lecterns have separate floor markings; no source or ordinary prop
  * shares their strict26px facing cone. Active fixtures take input first. */
 if(underwater_game_trial.index<16){if(trial_interact())return 1;}else if(room>=48){int large=room==48||room==51;int ly=large?240:112;if(close(large?80:48,ly))return begin_trial(1);if(close(large?400:192,ly))return begin_trial(2);}
 if(underwater_game_trial.index<16)return 0;
 if(room==46){
  if(close(80,256)){rest();return 1;}
  if(close(120,72)){if(done(38)){if(state(40)==2)claim(40);else if(done(40)&&state(45)==2)claim(45);else talk(40);}else{offer(38);if(adventure_save.quests.objectives[38]&1)objective(38,2);if(state(38)==2)claim(38);else say(TX_UW_CLUE38A,TX_UW_CLUE38B);}return 1;}
  if(close(96,104)){offer(38);say(TX_UW_PLAQUE_SOLID,TX_UW_PLAQUE_HINT);return 1;}
  if(close(144,104)){offer(38);objective(38,1);say(TX_UW_PLAQUE_HOLLOW,TX_UW_PLAQUE_HINT);return 1;}
  if(close(340,72)){talk(39);return 1;}
  if(close(340,108)){offer(39);lesson^=1;if(!lesson)objective(39,1);changed();say(lesson?TX_UW_LEVER_UP:TX_UW_LEVER_DOWN,TX_UW_LEVER_HINT);return 1;}
  if(close(160,176)){if(offer(41))objective(41,1);say(TX_UW_COOK,TX_UW_COOKB);return 1;}
  if(close(304,176)){if(offer(41))objective(41,2);say(TX_UW_FRAMER,TX_UW_FRAMERB);return 1;}
  if(close(240,240)){parade|=4;say(TX_UW_DANCER,TX_UW_DANCERB);return 1;}
  if(close(240,104)){if(state(41)==2){claim(41);return 1;}parade_rotation=(parade_rotation+1)%3;if(parade_rotation==2&&(parade&4)&&adventure_save.quests.objectives[41]==3)objective(41,4);changed();toast(TX_UW_MURAL);return 1;}
  if(close(384,128)){offer(44);objective(44,1);say(TX_UW_GLASS,TX_UW_GLASSB);return 1;}
  if(close(384,160)){if(adventure_save.quests.objectives[44]==3)claim(44);else talk(44);return 1;}
  if(close(64,72)){if(!(branch_visible&1)){toast(TX_UW_BRANCH_LATER);return 1;}repeat_state[0]=(repeat_state[0]+1)&3;changed();toast(TX_UW_LEAVES);return 1;}
  if(close(64,104))return repeat_invite(1,2);
  if(close(416,72)){if(!(branch_visible&2)){toast(TX_UW_BRANCH_LATER);return 1;}repeat_state[1]^=1;changed();toast(TX_UW_BASINS);return 1;}
  if(close(416,108))return repeat_invite(2,2);
  if(close(240,272)){if(!done(40)){say(TX_UW_RETURN_LATER,TX_UW_HOME);return 1;}offer(45);if((adventure_save.quests.objectives[45]&3)==3)objective(45,4);talk(45);return 1;}
 }
 if(room==47){
  if(close(64,256)){rest();return 1;}
  if(close(64,112)){offer(43);if(!(adventure_save.quests.objectives[43]&1))objective(43,1);else if(bench)objective(43,2);if(state(43)==2)claim(43);else say(TX_UW_BENCH,TX_UW_BENCHB);return 1;}
  if(close(112,112)){bench^=1;changed();toast(TX_UW_ADJUSTED);return 1;}
  if(close(240,164)){offer(39);say(TX_UW_RETURN_LOOP,TX_UW_RETURN_LOOPB);return 1;}
  if(close(352,160)){source_state[3]^=1;changed();toast(TX_UW_GUIDE);return 1;}
  if(close(376,184))return source_invite(4,1);
  if(close(392,240)){repeat_state[3]=(repeat_state[3]+1)&3;changed();toast(TX_UW_BEAD);return 1;}
  if(close(416,264))return repeat_invite(4,3);
 }
 if(room==48){
  if(close(112,92)){source_state[2]=(source_state[2]+1)%3;changed();toast(TX_UW_FROND);return 1;}
  if(close(144,92))return source_invite(3,1);
  if(close(368,208)){repeat_state[2]^=1;changed();toast(TX_UW_FROND);return 1;}
  if(close(368,256))return repeat_invite(3,3);
  if(close(64,224)){source_state[5]=(source_state[5]+1)%5;changed();toast(TX_UW_MEDALLION);return 1;}
  if(close(96,224))return source_invite(6,1);
  if(close(304,80)){repeat_state[5]=(repeat_state[5]+1)%5;changed();toast(TX_UW_MEDALLION);return 1;}
  if(close(272,80)){if(repeat_state[5]==3)repeat_state[5]=5;else if(repeat_state[5]==5)repeat_state[5]=3;changed();toast(TX_UW_OPEN_EXIT);return 1;}
  if(close(336,80))return repeat_invite(6,5);
  if(close(240,80)){offer(42);objective(42,1);say(TX_UW_SHOAL,TX_UW_SHOALB);return 1;}
  if(close(280,224)){if(px>280&&adventure_save.quests.objectives[42]&1){migration=1;objective(42,2);changed();toast(TX_UW_LANE_OPEN);}else toast(TX_UW_FAR_HANDLE);return 1;}
  if(close(432,256)){talk(42);return 1;}
  if(close(368,112)){repeat_state[4]=(repeat_state[4]+1)&3;changed();toast(TX_UW_SHUTTERS);return 1;}
 }
 if(room==49){
  if(close(120,48)){offer(44);if(adventure_save.quests.objectives[44]&1)objective(44,2);discover(24,1);say(TX_UW_GARDEN_MURAL,TX_UW_GARDEN_MURALB);return 1;}
  if(close(144,52)){source_state[4]^=1;changed();toast(TX_UW_SHADE);return 1;}
  if(close(172,52))return source_invite(5,1);
  if(close(208,64)){repeat_state[4]=(repeat_state[4]+1)&3;changed();toast(TX_UW_SHUTTERS);return 1;}
  if(close(208,96))return repeat_invite(5,2);
  if(close(64,56)){if(adventure_save.quests.region_flags[21]==3)discover(24,4);source_state[7]=(unsigned char)(adventure_save.quests.region_flags[21]>=3);return source_invite(8,1);}
  if(close(80,88)){repeat_state[7]=(repeat_state[7]+1)&3;changed();toast(TX_UW_LEAVES);return 1;}
  if(close(112,88)){if(repeat_state[7]==1)repeat_state[7]=3;else repeat_state[7]=0;changed();toast(TX_UW_DIAGONAL);return 1;}
  if(close(64,88))return repeat_invite(8,3);
 }
 if(room==50){
  if(close(120,104)){toggle_main(0);if(underwater_puzzle_solved(&underwater_game_puzzle,50)){objective(40,1);persist();toast(TX_UW_RECORD);}return 1;}
  if(close(88,72)||close(152,72)){say(TX_UW_OVERLAY,TX_UW_OVERLAYB);return 1;}
 }
 if(room==51){
  if(close(240,80)){if(underwater_puzzle_solved(&underwater_game_puzzle,51)){objective(40,2);persist();say(TX_UW_SKETCH,TX_UW_SKETCHB);}else say(TX_UW_STACKS,TX_UW_STACKSB);return 1;}
  if(close(160,80)){discover(23,1);say(TX_UW_HINGE,TX_UW_HINGEB);return 1;}
  if(close(160,112)){if(adventure_save.quests.region_flags[20]&1)discover(23,2);source_state[6]=(unsigned char)(adventure_save.quests.region_flags[20]>=1);changed();toast(TX_UW_OPEN_EXIT);return 1;}
  if(close(144,96))return source_invite(7,1);
  if(close(384,64)){repeat_state[6]=(repeat_state[6]+1)&3;changed();toast(TX_UW_HINGE);return 1;}
  if(close(416,64)){if(repeat_state[6]==1||repeat_state[6]==3)repeat_state[6]=4;changed();toast(TX_UW_SWEEP_CLEAR);return 1;}
  if(close(400,96))return repeat_invite(7,4);
 }
 if(room==52){
  if(close(80,72))return toggle_main(0);
  if(close(160,72))return toggle_main(1);
  if(close(120,112)){if(underwater_puzzle_solved(&underwater_game_puzzle,52)){objective(40,4);persist();say(TX_UW_QUIET,TX_UW_QUIETB);}else say(TX_UW_LISTEN,TX_UW_LISTENB);return 1;}
 }
 if(room==53){
  if(close(176,80)){underwater_game_puzzle.aux=1;changed();say(TX_UW_MEMORY,TX_UW_MEMORYB);return 1;}
  if(close(120,112)){if(underwater_game_guardian_stage==0&&underwater_game_puzzle.echo&&underwater_game_puzzle.ballast&&underwater_game_puzzle.aux){underwater_game_guardian_stage=1;underwater_game_guardian_ticks=72;guardian_side=(unsigned char)(px>120);changed();toast(TX_UW_GUARDIAN_WAKE);}else say(TX_UW_COURT,TX_UW_COURTB);return 1;}
  if(!road_region_managed(53,46)&&close(208,112)&&underwater_game_guardian_stage==4){offer(45);objective(45,1);persist();return door(46,1);}
 }
 /* General signs give the next readable clue; no invisible range pickup. */
 return 0;
}
int underwater_game_power(unsigned command){(void)command;return 0;}
unsigned underwater_game_action_begin(unsigned channel){CreatureInstance*c;if(channel>3)return 0;if(++action_serial==0)++action_serial;action_token[channel]=action_serial;action_hits&=(unsigned char)~(1u<<channel);if(channel==3){c=active();cast_id=c?c->instance_id:0;cast_form=c?c->form_id:0;cast_generation=room_generation;cast_command=progression_command();field_hits=0;}return action_serial;}
int underwater_game_field_target(unsigned i,int*x,int*y,int*r){int xx=0,yy=0;if(!underwater_game_is_room((unsigned)room)||i>=8||projection==2)return 0;if(underwater_game_trial.index<16){if(i>=6)return 0;trial_point(i,&xx,&yy);}else if(room==50&&i<2){xx=i?152:88;yy=72;}else if(room==51&&i<2){xx=i?304:176;yy=144;}else if(room==52&&i==0){xx=120;yy=48;}else if(room==53&&i<2){xx=i?64:120;yy=i?80:48;}else if(room==49&&i==0){xx=120;yy=48;}else if(room==47&&i<2){xx=i?240:144;yy=i?144:112;}else return 0;if(x)*x=xx;if(y)*y=yy;if(r)*r=10;return 1;}
COLD int underwater_game_field_hit(unsigned i,unsigned command,unsigned id,unsigned form,unsigned token){CreatureInstance*c=active();int r,x,y;if(!token||token!=action_token[3]||cast_generation!=room_generation||id!=cast_id||form!=cast_form||!c||c->instance_id!=id||c->form_id!=form||command!=cast_command||command!=progression_command()||!underwater_game_field_target(i,&x,&y,0))return 0;if(field_hits&(1u<<i))return 0;field_hits|=(unsigned char)(1u<<i);
 if(underwater_game_trial.index<16){if(!participant()||command!=underwater_game_trial.command)return 0;return trial_cast(i);}
 if((room==50&&i==0)||(room==52&&i==0)||(room==53&&i==0)||(room==49&&i==0)||(room==47&&i==0)){if(command!=67){toast(TX_UW_ECHO_NEEDED);return 2;}underwater_game_puzzle.echo=1;if(room==49&&adventure_save.quests.region_flags[21]==1)discover(24,2);changed();toast(TX_UW_TRACE);return 1;}
 if((room==50&&i==1)||(room==51&&i<2)||(room==53&&i==1)||(room==47&&i==1)){if(command!=70){toast(TX_UW_BALLAST_NEEDED);return 2;}if(room==47){underwater_game_puzzle.ballast^=1;changed();toast(TX_UW_ADJUSTED);return 1;}if(room==51&&i==1&&!underwater_game_puzzle.walk){toast(TX_UW_FAR_LANDING);return 2;}r=underwater_puzzle_toggle(&underwater_game_puzzle,(unsigned)room,room==50||room==53?1:i,px,py);if(r==1){underwater_powers_geometry_changed();changed();toast(TX_UW_ADJUSTED);if(room==50&&underwater_puzzle_solved(&underwater_game_puzzle,50)){objective(40,1);persist();}return 1;}toast(TX_UW_STEP_CLEAR);return 2;}
 return 0;}
int underwater_game_target(int*x,int*y,int*r){if(room!=53||underwater_game_guardian_stage!=3||!underwater_game_puzzle.ballast)return 0;if(x)*x=120;if(y)*y=48;if(r)*r=14;return 1;}
COLD int underwater_game_weapon_hit(unsigned cls,int x,int y,unsigned damage,unsigned channel,unsigned token){if(channel>3||!token||token!=action_token[channel]||(action_hits&(1u<<channel))||(cls<1||cls>3)||!damage||!underwater_game_target(0,0,0)||!near(x,y,120,48,20))return 0;action_hits|=(unsigned char)(1u<<channel);underwater_game_guardian_hits++;if(underwater_game_guardian_hits>=3){underwater_game_guardian_stage=4;objective(40,8);persist();toast(TX_UW_GUARDIAN_DONE);}else{underwater_game_guardian_stage=1;underwater_game_guardian_ticks=72;guardian_side=(unsigned char)(px>120);guardian_hurt=0;toast(TX_UW_GUARDIAN_REST);}changed();return 1;}
int underwater_game_command_hit(int x,int y,unsigned damage,unsigned token){(void)x;(void)y;(void)damage;(void)token;return 0;}
COLD void underwater_game_tick(void){int x,y;if(!underwater_game_is_room((unsigned)room)||game_state!=PLAY)return;world_clock++;if(projection==2&&!underwater_puzzle_solid(&underwater_game_puzzle,(unsigned)room,px,py)){projection=0;underwater_powers_geometry_changed();changed();}if(door_notice)door_notice--;reset_point(&x,&y);if(reset_pending&&!close(x,y))reset_pending=0;
 if(event_count)return;
 if(underwater_game_trial.index<16)trial_walk();
 else {
  if(room==46&&done(40)&&(adventure_save.quests.objectives[45]&1)&&!route_stage)route_stage=1;
  if(room==46&&(branch_visible&2)&&repeat_state[1]==1&&near(px,py,448,108,10)){repeat_state[1]=2;changed();}
  if(room==47){if(!(adventure_save.quests.objectives[39]&2)){unsigned char s=source_state[1];if(!s&&near(px,py,176,164,12))source_state[1]=1;else if(s==1&&near(px,py,304,164,12))source_state[1]=2;else if(s==2&&near(px,py,240,192,12)){source_state[1]=3;offer(39);objective(39,2);persist();toast(TX_UW_RETURN_PROVED);}}if(repeat_state[3]==1&&near(px,py,424,240,10)){repeat_state[3]=3;changed();}}
  if(room==48&&repeat_state[2]==1&&near(px,py,400,208,10)){repeat_state[2]=3;changed();}
  if(room==51&&underwater_game_puzzle.ballast&&!underwater_game_puzzle.walk&&near(px,py,312,112,12)){underwater_game_puzzle.walk=1;changed();toast(TX_UW_RETURN_PROVED);}
  if(room==53&&underwater_game_guardian_stage>0&&underwater_game_guardian_stage<3){if(underwater_game_guardian_ticks)underwater_game_guardian_ticks--;if(underwater_game_guardian_stage==1&&!underwater_game_guardian_ticks){underwater_game_guardian_stage=2;underwater_game_guardian_ticks=36;guardian_hurt=0;changed();}else if(underwater_game_guardian_stage==2){int sy=80, sx=guardian_side?24:88;if(!guardian_hurt&&px>=sx&&px<=sx+128&&py>=sy&&py<=sy+24){guardian_hurt=1;game_north_hurt(16);if(game_state!=PLAY)return;}changed();if(!underwater_game_guardian_ticks){underwater_game_guardian_stage=3;changed();toast(TX_UW_JOINT_OPEN);}}}
 }
 persist();if(transition_lock||game_state!=PLAY)return;
 if(room==46){if(py>=304&&ab(px-240)<=16&&(keys&DOWN)){enter_room(38,4);return;}if(!road_region_managed((unsigned)room,47)&&(px>=464&&ab(py-160)<=16&&(keys&RIGHT))){door(47,0);return;}if(!road_region_managed((unsigned)room,48)&&(py<=16&&ab(px-240)<=16&&(keys&UP))){door(48,0);return;}}
 else if(room==47){if(!road_region_managed((unsigned)room,46)&&(py>=304&&ab(px-240)<=16&&(keys&DOWN))){door(46,3);return;}if(!road_region_managed((unsigned)room,50)&&(py<=16&&ab(px-400)<=16&&(keys&UP))){door(50,0);return;}}
 else if(room==48){if(!road_region_managed((unsigned)room,46)&&(py>=304&&ab(px-240)<=16&&(keys&DOWN))){door(46,1);return;}if(!road_region_managed((unsigned)room,49)&&(py<=16&&ab(px-240)<=16&&(keys&UP))){door(49,0);return;}if(!road_region_managed((unsigned)room,51)&&(px>=464&&ab(py-160)<=16&&(keys&RIGHT))){door(51,2);return;}}
 else if(room==49){if(!road_region_managed((unsigned)room,48)&&(py>=144&&ab(px-120)<=16&&(keys&DOWN))){door(48,1);return;}if(!road_region_managed((unsigned)room,52)&&(px>=224&&ab(py-112)<=16&&(keys&RIGHT))){door(52,2);return;}}
 else if(room==50){if(!road_region_managed((unsigned)room,47)&&(py>=144&&ab(px-120)<=16&&(keys&DOWN))){door(47,1);return;}if(!road_region_managed((unsigned)room,51)&&(px>=224&&ab(py-112)<=16&&(keys&RIGHT))){door(51,0);return;}}
 else if(room==51){if(!road_region_managed((unsigned)room,50)&&(py>=304&&ab(px-240)<=16&&(keys&DOWN))){door(50,1);return;}if(!road_region_managed((unsigned)room,52)&&(px>=464&&ab(py-112)<=16&&(keys&RIGHT))){door(52,0);return;}if(!road_region_managed((unsigned)room,48)&&(px<=16&&ab(py-160)<=16&&(keys&LEFT))){door(48,2);return;}}
 else if(room==52){if(!road_region_managed((unsigned)room,51)&&(py>=144&&ab(px-120)<=16&&(keys&DOWN))){door(51,1);return;}if(!road_region_managed((unsigned)room,53)&&(px>=224&&ab(py-112)<=16&&(keys&RIGHT))){door(53,0);return;}if(!road_region_managed((unsigned)room,49)&&(px<=16&&ab(py-112)<=16&&(keys&LEFT))){door(49,1);return;}}
 else if(room==53){if(!road_region_managed((unsigned)room,52)&&(py>=144&&ab(px-120)<=16&&(keys&DOWN))){door(52,1);return;}if(!road_region_managed(53,46)&&px>=224&&ab(py-112)<=16&&(keys&RIGHT)&&underwater_game_guardian_stage==4){offer(45);objective(45,1);persist();door(46,1);return;}}
}
COLD int underwater_game_name(void){return room_text((unsigned)room);}
COLD int underwater_game_quest_text(void){if(!done(38))return TX_UW_HUD_ECHO;if(!done(39))return TX_UW_HUD_BALLAST;if(!done(40))return TX_UW_HUD_ARCHIVE;return TX_UW_HUD_HOME;}
#include "underwater_game_draw.inc"
