/* Original Kilnstep chapter. Regional transient state is bounded; all durable
 * changes go through reviewed magma_quests transactions. No SRAM side route. */
#include "magma_game.h"
#include "magma_art.h"
#include "magma_quests.h"
#include "progression.h"
#include "assets.h"
#ifdef MAGMA_GAME_HOST_TEST
#include "magma_game_test_ui.h"
#else
#include "ui.h"
#endif
#if defined(__arm__)
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
#else
#define COLD
#endif
#define PLAY 1
#define KEY_A 1
#define KEY_B 2
#define RIGHT 16
#define LEFT 32
#define UP 64
#define DOWN 128
#define JOURNAL_TAB 8
extern volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
extern volatile unsigned chapter_flags;
extern int face,keys,journal_tab;
extern void enter_room(int,int),save_game(void),dialogue(int,int,int),toast(int),text(int,int,int,int),centered(int,int,int),box(int,int,int,int);
extern void rect(int,int,int,int,unsigned char),line(int,int,int,int,int),game_region_warp(int,int);
unsigned magma_game_revision,magma_game_journal_selection;
MagmaPuzzle magma_game_puzzle;
unsigned char magma_game_machine_stage,magma_game_machine_ticks,magma_game_machine_hp;
/* grab0/1 puzzle props,2 town jar,3 field screen;255 means free movement. */
static unsigned char grab=255,lesson_x=144,screen_x=128,hood,guide,seed,wind,brush,samples,hooks,bypass,basin;
static unsigned char shelf,pot_hood,pots,clapper,sound,spill,second,carrying,door_notice,reg_divert,reg_lane,reg_hit,reg_window_hit,action_hits;
static unsigned action_token[4];
static unsigned char dirty,branch_visible;
/* Small staged rest transaction; no save/roster copy and no skipped validation. */
static unsigned char pending_anchor_area,pending_anchor_spawn,pending_anchor_checkpoint;
static unsigned short world_clock;
/* One trial, one durable identity, independent distinct target bits. Ordinary
 * travel preserves evidence. Restart/death/load clears this entire record. */
static unsigned char trial_index=255,trial_slot=255,trial_bits,trial_aux,trial_order;
static CreatureU32 trial_id;
/* Current-r6 shell-lift return appends slot4; historical slots0..3 stay exact. */
static const short spawns[8][5][2]={{{240,284},{304,32},{80,152},{112,264},{416,240}},{{240,284},{80,104},{400,72},{80,280}},{{120,136}},{{120,136}},{{120,136}},{{120,136}},{{120,136}},{{120,136}}};
int magma_game_is_room(unsigned a){return a>=38&&a<=45;}
unsigned magma_game_spawn_count(unsigned a){return !magma_game_is_room(a)?0:a==38?5:a==39?4:1;}
int magma_game_spawn(unsigned a,unsigned s,int*x,int*y){if(s>=magma_game_spawn_count(a))return 0;if(x)*x=spawns[a-38][s][0];if(y)*y=spawns[a-38][s][1];return 1;}
#include "magma_puzzle.inc"
static int near(int x,int y,int xx,int yy,int r){return ab(x-xx)+ab(y-yy)<r;}
static int close(int x,int y){if((face==1&&y>py+8)||(face==0&&y<py-8)||(face==2&&x>px+8)||(face==3&&x<px-8))return 0;return near(px,py,x,y,23);}
static int npc_close(int x,int y){int forward,side;if(!close(x,y))return 0;if(face==1){forward=py-y;side=ab(px-x);}else if(face==0){forward=y-py;side=ab(px-x);}else if(face==2){forward=px-x;side=ab(py-y);}else{forward=x-px;side=ab(py-y);}return side<=forward+4;}
static unsigned state(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
static int done(unsigned q){return state(q)==3;}
static int sen_x(void){return done(35)?136+ab((int)((world_clock>>2)%96)-48):136;}
static int sen_y(void){return done(35)?240:216;}
static void changed(void){magma_game_revision++;progression_revision++;}
static void sync(void){adventure_save.campaign.chapter_flags=(Save4U8)chapter_flags;}
static COLD void persist(void){if(dirty){sync();if(magma_game_is_room((unsigned)room)){adventure_save.campaign.room=(Save4U8)room;adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;}changed();save_game();dirty=0;}}
static COLD void say(int a,int b){persist();dialogue(a,b,PLAY);}
static COLD int offer(unsigned q){int r=magma_quest_offer(&adventure_save,q);if(r==MAGMA_CHANGED)dirty=1;return r!=MAGMA_LOCKED&&r!=MAGMA_INVALID;}
static COLD int objective(unsigned q,unsigned bit){int r=magma_quest_objective(&adventure_save,q,bit);if(r==MAGMA_CHANGED||r==MAGMA_NOW_READY){dirty=1;changed();return 1;}return 0;}
static COLD void result(int r){if(r==MAGMA_FULL)say(TX_MG_FULL,TX_MG_FULLB);else if(r==MAGMA_SPACE_RESERVED)say(TX_MG_RESERVED,TX_MG_RESERVEDB);else if(r==MAGMA_UNCHANGED)toast(TX_MG_KNOWN);else toast(TX_MG_ARRANGE);}
static COLD void claim(unsigned q){int r=magma_quest_claim(&adventure_save,q);if(r==MAGMA_REWARDED){creatures_credit_event(&adventure_save.roster,240+q-30,160,CREATURE_CREDIT_PERSONAL_QUEST);dirty=1;progression_refresh();say(q==32?TX_MG_END:TX_MG_RECEIVED,q==32?TX_MG_ENDB:TX_MG_RECEIVEDB);}else result(r);}
static const int qnames[8]={TX_MG_Q30,TX_MG_Q31,TX_MG_Q32,TX_MG_Q33,TX_MG_Q34,TX_MG_Q35,TX_MG_Q36,TX_MG_Q37};
static const int clues[8][2]={{TX_MG_CLUE30A,TX_MG_CLUE30B},{TX_MG_CLUE31A,TX_MG_CLUE31B},{TX_MG_CLUE32A,TX_MG_CLUE32B},{TX_MG_CLUE33A,TX_MG_CLUE33B},{TX_MG_CLUE34A,TX_MG_CLUE34B},{TX_MG_CLUE35A,TX_MG_CLUE35B},{TX_MG_CLUE36A,TX_MG_CLUE36B},{TX_MG_CLUE37A,TX_MG_CLUE37B}};
static COLD void talk(unsigned q){if(q==33&&state(q)==1&&adventure_save.quests.objectives[q]==3)objective(q,4);if(state(q)>=2){claim(q);return;}if(offer(q))say(clues[q-30][0],clues[q-30][1]);else say(TX_MG_LOCKED,TX_MG_LOCKEDB);}
static CreatureInstance*active(void){CreatureInstance*c=progression_selected();unsigned p=adventure_save.roster.selected_party,s;if(!summoned||p>=4)return 0;s=adventure_save.roster.party[p];if(s>=160||c!=&adventure_save.roster.instances[s]||!creatures_instance_validate(c))return 0;return c;}
static int line_clear(int tx,int ty){const MagmaArtRoom*r;unsigned j,k;int ox=0,oy=0,dx=tx-px,dy=ty-py,n=ab(dx)>ab(dy)?ab(dx):ab(dy),i,x,y;if(!magma_game_is_room((unsigned)room)||n>128)return 0;
r=&magma_art_rooms[room-38];for(i=1;i<n;i++){x=px+dx*i/n;y=py+dy*i/n;for(j=0;j<r->solid_count;j++){const MagmaArtRect*b=&r->solids[j];if(x>=b->x&&x<b->x+b->w&&y>=b->y&&y<b->y+b->h)return 0;}if(room>=42&&room<=44)for(k=0;k<magma_puzzle_count((unsigned)room);k++)if(magma_puzzle_position(&magma_game_puzzle,(unsigned)room,k,&ox,&oy)&&(ox!=tx||oy!=ty)&&x>=ox-6&&x<ox+6&&y>=oy-6&&y<oy+6)return 0;}return 1;}
static int field(unsigned cap,int x,int y){CreatureInstance*c=active();return c&&close(x,y)&&line_clear(x,y)&&creatures_supports_capability(c->form_id,cap);}
static COLD int wrong(int id){toast(id);return 2;}
#include "magma_recruit_event.inc"
static int has_branch(unsigned token){return magma_branch_hint_available(&adventure_save,token);}
static COLD int recruit(unsigned token,int valid,int repeat,int hint){int r;if(!repeat&&magma_source_claimed(&adventure_save,token)){toast(TX_MG_KNOWN);return 1;}if(!valid){toast(hint);return 1;}if(repeat){if(!magma_queue_recruit(token))result(MAGMA_INVALID);return 1;}r=magma_field_recruit(&adventure_save,token);if(r==MAGMA_REWARDED){if(!repeat){unsigned aid=magma_source_aid(token);if(aid<128)creatures_credit_event(&adventure_save.roster,384+aid,120,CREATURE_CREDIT_FIELD_AID);}dirty=1;progression_refresh();persist();toast(TX_MG_RECRUITED);}else result(r);return r==MAGMA_REWARDED?3:1;}
static COLD void discover(unsigned bit){int r=magma_discover(&adventure_save,bit);if(r==MAGMA_CHANGED||r==MAGMA_NOW_READY){dirty=1;changed();}}
static void clear_trial(void){trial_index=trial_slot=255;trial_bits=trial_aux=trial_order=0;trial_id=0;}
static void reset_scene(void){unsigned bi;magma_game_cancel_event();if(magma_scene<0xffffffffu)++magma_scene;else magma_scene=0;branch_visible=0;for(bi=0;bi<160;bi++){unsigned f=adventure_save.roster.instances[bi].form_id;if(f==38||f==39)branch_visible|=1;if(f==41||f==42)branch_visible|=2;if(f==44||f==45)branch_visible|=4;if(f==47||f==48)branch_visible|=8;}if(trial_index==0)trial_aux=0;magma_puzzle_reset(&magma_game_puzzle,(unsigned)room);grab=255;lesson_x=144;/* The Q35 screen stays in its storage bay after the authored route
 * repair. This durable objective never supplies a trial or teaching proof. */
screen_x=(unsigned char)((adventure_save.quests.objectives[35]&1)?176:128);hood=guide=seed=wind=brush=samples=hooks=bypass=basin=0;shelf=pot_hood=pots=clapper=sound=spill=second=door_notice=reg_divert=reg_hit=reg_window_hit=action_hits=0;action_token[0]=action_token[1]=action_token[2]=action_token[3]=0;reg_lane=0;world_clock=0;magma_game_machine_stage=(unsigned char)((adventure_save.quests.objectives[32]&8)?5:0);magma_game_machine_ticks=0;magma_game_machine_hp=(unsigned char)(magma_game_machine_stage==5?0:192);changed();}
static struct {Save4U32 token;unsigned phase,revision,chapter,scene;int x,y,facing;} magma_anchor_job;
static void cancel_anchor_job(void){
 if(magma_anchor_job.token&&save5_preflight_status(magma_anchor_job.token)!=SAVE5_FAILED)save5_preflight_cancel();
 magma_anchor_job.token=0;magma_anchor_job.phase=0;
}
static void cancel_anchor_prepare(void){cancel_anchor_job();if(pending_anchor_area&&(unsigned)room==pending_anchor_area&&checkpoint_spawn==3)checkpoint_spawn=pending_anchor_checkpoint;pending_anchor_area=0;}
COLD void magma_game_cancel_save_prepare(void){cancel_anchor_prepare();}
COLD void magma_game_reset(void){magma_game_cancel_enter();magma_game_cancel_return();cancel_anchor_prepare();carrying=0;clear_trial();reset_scene();}
int magma_game_can_enter(unsigned a){sync();return magma_can_enter(&adventure_save,a);}
#include "magma_return_job.inc"
#include "magma_enter_job.inc"
COLD int magma_game_enter(unsigned a,unsigned s){int r,x,y,prepared=0;sync();
 if(!magma_game_spawn(a,s,&x,&y)||!magma_can_enter(&adventure_save,a)||(a==38&&s==4&&!(adventure_save.quests.region_flags[4]&1))){magma_game_cancel_enter();return 0;}
 if(magma_enter_job.phase==MAGMA_ENTER_COMMIT){prepared=magma_enter_apply(a,s,&r);if(!prepared)return 0;}
 else if(magma_enter_job.owned){magma_game_cancel_enter();return 0;}
 else{magma_game_cancel_enter();r=magma_return_consume(a,s)?MAGMA_UNCHANGED:magma_visit(&adventure_save,a);}
 if(r==MAGMA_INVALID||r==MAGMA_LOCKED)return 0;
 room=(int)a;checkpoint_spawn=(int)s;px=x;py=y;reset_scene();
 if(a>=42){if(prepared){
  /* The validated legal visit preserves Save5 validity. This is exactly the
   * q32 offer's inactive->active patch after both main prerequisite rewards. */
  if(magma_quest_available(&adventure_save,32)&&!state(32)){
   save5_quest_set_state(&adventure_save.quests,32,SAVE5_QUEST_ACTIVE);dirty=1;
  }
 }else offer(32);}
 adventure_save.campaign.room=(Save4U8)a;adventure_save.campaign.spawn=(Save4U8)s;dirty=1;persist();return 1;
}
static int trial_brick(void){return room==40&&(trial_index==0||trial_index==1);}
int magma_game_solid(int x,int y){if(!magma_game_is_room((unsigned)room))return 0;if(room>=42&&room<=44)return magma_puzzle_solid(&magma_game_puzzle,(unsigned)room,x,y);if(trial_brick())return magma_puzzle_solid(&magma_game_puzzle,40,x,y);if(magma_game_geometry_solid((unsigned)room,x,y))return 1;if(room==38&&prop_hit(x,y,lesson_x,232))return 1;if(room==39&&prop_hit(x,y,screen_x,264))return 1;return 0;}
COLD int magma_game_clear_box(int x0,int y0,int x1,int y1){const MagmaArtRoom*r;const unsigned short*previous=0;int y,ox,oy;
 if((room!=38&&room!=39)||x0>x1||y0>y1)return 0;
 r=&magma_art_rooms[room-38];if(x0<0||y0<0||x1>=r->width||y1>=r->height)return 0;
 for(y=y0;y<=y1;y++){const unsigned short*b=r->collision_bands+r->collision_rows[y];unsigned n;
  if(b==previous)continue;
  previous=b;n=*b++;
  /* The shared generator emits sorted, disjoint half-open intervals. */
  while(n--){if(x1<b[0])break;if(x0<b[1])return 0;b+=2;}
 }
 ox=room==38?lesson_x:screen_x;oy=room==38?232:264;
 return !(x1>=ox-11&&x0<ox+11&&y1>=oy-11&&y0<oy+11);
}
void magma_game_collision_inputs(unsigned out[3]){if(!out)return;out[0]=out[1]=out[2]=0;if(room>=42&&room<=44){out[0]=magma_game_puzzle.cell[0];out[1]=magma_puzzle_count((unsigned)room)>1?magma_game_puzzle.cell[1]:0;}else if(trial_brick()){out[0]=magma_game_puzzle.cell[0];out[2]=1;}else if(room==38)out[0]=lesson_x;else if(room==39)out[0]=screen_x;}
unsigned magma_game_enemy_spawns(unsigned a,const MagmaEnemySpawn**out){static const MagmaEnemySpawn f[5]={{184,116,5,0,0},{256,264,5,0,1},{424,120,5,2,3},{328,56,5,0,4},{56,232,5,0,2}},g[2]={{56,120,4,0,3},{184,136,4,0,1}},one[1]={{24,88,4,0,2}},two[2]={{24,88,4,0,2},{216,88,4,0,0}};const MagmaEnemySpawn*p=a==39?f:a==41?g:a==42||a==43?one:a==44?two:0;if(out)*out=p;return a==39?5:a==41||a==44?2:a==42||a==43?1:0;}
static COLD int door(unsigned dest,unsigned spawn){if(!magma_can_enter(&adventure_save,dest)){if(!door_notice){say(TX_MG_LOCKED,TX_MG_LOCKEDB);door_notice=40;}return 1;}persist();enter_room((int)dest,(int)spawn);return 1;}
int magma_game_save_prepare_pending(void){return pending_anchor_area!=0;}
COLD int magma_game_prepare_save(void){unsigned area=pending_anchor_area;int r;
 if(!area)return 0;
 if(magma_anchor_job.phase){cancel_anchor_prepare();return 0;}
 /* A cancelled, redirected, or re-stamped request must never create an anchor.
  * Consume the queue even on failure; the engine must show save failure. */
 if(game_state!=6||(area!=38&&area!=39)||(unsigned)room!=area||
    adventure_save.campaign.room!=area||checkpoint_spawn!=3||
    adventure_save.campaign.spawn!=pending_anchor_spawn){cancel_anchor_prepare();return 0;}
 r=magma_anchor(&adventure_save,area);
 if(r!=MAGMA_CHANGED&&r!=MAGMA_UNCHANGED){cancel_anchor_prepare();return 0;}
 pending_anchor_area=0;
 /* The validator saw the original legal spawn. Only the successful typed
  * anchor transaction authorizes anchor spawn3 in the ensuing save snapshot.
  * The request already invalidated the notice; REST itself is streamed OBJ. */
 adventure_save.campaign.spawn=3;
 return 1;
}
#include "magma_anchor_job.inc"
static COLD void rest(void){if(pending_anchor_area)return;
 pending_anchor_area=(unsigned char)room;pending_anchor_spawn=adventure_save.campaign.spawn;pending_anchor_checkpoint=(unsigned char)checkpoint_spawn;
 checkpoint_spawn=3;game_health_fill();changed();dirty=1;persist();
 /* Normal save_game stamps the requested checkpoint before returning. Keep
  * this single field at its prior legal value until the frozen prepare stage. */
 adventure_save.campaign.spawn=pending_anchor_spawn;
 toast(TX_MG_RESTED);
}
static int participant(void){CreatureInstance*c=active();return trial_index<15&&trial_slot<160&&c==&adventure_save.roster.instances[trial_slot]&&c->instance_id==trial_id;}
#include "magma_trials.inc"
static COLD void check_slide(void){if(room==38&&lesson_x==192){if(offer(30))objective(30,1);if(trial_index==0&&trial_aux&1&&participant()){trial_mark(1);trial_aux&=(unsigned char)~1;}}if(room==39&&screen_x==176){if(offer(35))objective(35,1);}if(room==42&&magma_puzzle_solved(&magma_game_puzzle,42)){objective(32,1);if(trial_index==0&&(trial_aux&4)&&participant())trial_mark(4);toast(TX_MG_SOLVED);}if(room==40&&trial_brick())trial_slide();persist();}
static COLD int begin_grab(unsigned i){grab=(unsigned char)i;toast(TX_MG_GRABBED);changed();return 1;}
int magma_game_grabbed(void){return grab!=255;}
COLD int magma_game_input(unsigned pressed,unsigned held){unsigned d;int x,y,nx,ny,r,oldx,oldy,ox,oy,i;MagmaPuzzle candidate;(void)held;if(!magma_game_is_room((unsigned)room)||game_state!=PLAY)return 0;if(grab==255)return 0;if(pressed&(KEY_A|KEY_B)){grab=255;changed();toast(TX_MG_RELEASED);return 1;}if(!(pressed&(UP|DOWN|LEFT|RIGHT)))return 1;d=pressed&UP?1:pressed&DOWN?0:pressed&LEFT?2:3;
 if(grab<2){candidate=magma_game_puzzle;r=magma_puzzle_move(&candidate,(unsigned)room,grab,d,px,py,&nx,&ny);if(r!=1){toast(TX_MG_BLOCKED);return 1;}if(!magma_puzzle_position(&candidate,(unsigned)room,grab,&x,&y)||!magma_puzzle_position(&magma_game_puzzle,(unsigned)room,grab,&oldx,&oldy)){grab=255;return 1;}for(i=1;i<=24;i++)if(game_magma_actor_overlap(oldx+(x-oldx)*i/24,oldy+(y-oldy)*i/24,7)||game_magma_actor_overlap(px+(nx-px)*i/24,py+(ny-py)*i/24,5)){toast(TX_MG_BLOCKED);return 1;}magma_game_puzzle=candidate;game_region_warp(nx,ny);}
 else{if(d<2){toast(TX_MG_BLOCKED);return 1;}oldx=grab==2?lesson_x:screen_x;oldy=grab==2?232:264;x=oldx+(d==2?-24:24);y=oldy;if(x<(grab==2?144:128)||x>(grab==2?192:176)){toast(TX_MG_BLOCKED);return 1;}nx=px+x-oldx;ny=py;for(i=1;i<=24;i++){ox=oldx+(x-oldx)*i/24;oy=y;if(raw_prop_wall((unsigned)room,ox,oy)||magma_game_geometry_solid((unsigned)room,px+(nx-px)*i/24,ny)||prop_hit(px+(nx-px)*i/24,ny,ox,oy)){toast(TX_MG_BLOCKED);return 1;}}for(i=1;i<=24;i++)if(game_magma_actor_overlap(oldx+(x-oldx)*i/24,y,7)||game_magma_actor_overlap(px+(nx-px)*i/24,ny,5)){toast(TX_MG_BLOCKED);return 1;}if(grab==2)lesson_x=(unsigned char)x;else screen_x=(unsigned char)x;game_region_warp(nx,ny);}
 if(room==44&&trial_index==3&&participant()&&magma_game_puzzle.cell[1]==4&&magma_game_puzzle.cell[0]==20)trial_aux|=4;
changed();check_slide();return 1;}
COLD int magma_game_interact(void){unsigned i;int x,y,r;if(game_state!=PLAY||!magma_game_is_room((unsigned)room))return 0;sync();
 /* Trial object A proofs have priority only for the explicitly selected trial. */
 r=trial_interact();if(r)return r;
 if(room>=40&&npc_close(24,136)){reset_scene();clear_trial();toast(TX_MG_RESET);return 1;}
 if((room==38&&(npc_close(432,280)||npc_close(400,280)))||(room==39&&(npc_close(208,248)||npc_close(272,248)))||(room>=40&&(npc_close(24,112)||npc_close(216,112))))return begin_trial((room==38?close(400,280):room==39?close(272,248):close(216,112))?2:1);
 if((room>=42&&room<=44)||trial_brick()){for(i=0;i<magma_puzzle_count((unsigned)room);i++){if(!magma_puzzle_position(&magma_game_puzzle,(unsigned)room,i,&x,&y))continue;if(close(x,y))return begin_grab(i);}}
 if(room==38){
  if(close(lesson_x,232))return begin_grab(2);
  if(close(224,208)){hood^=1;changed();if(hood&&offer(30))objective(30,2);persist();toast(hood?TX_MG_HOOD_OPEN:TX_MG_HOOD_CLOSED);return 1;}
  if(npc_close(160,176)){if(!done(30))talk(30);else if(state(32)>=2)talk(32);else say(TX_MG_RESSA,TX_MG_RESSAB);return 1;}
  if(npc_close(96,176)){talk(33);return 1;}if(npc_close(384,176)){talk(36);return 1;}
  if(close(112,248)){rest();return 1;}if(close(384,208)){if(offer(36))objective(36,1);say(TX_MG_PELL,TX_MG_PELLB);return 1;}
  if(close(304,208)){say(TX_MG_BRANCH,TX_MG_BRANCHB);return 1;}
  if(close(80,136)||close(80,152))return door(40,0);
  if(close(240,268)){persist();enter_room(30,0);return 1;}
 }
 else if(room==39){
  if(close(screen_x,264))return begin_grab(3);
  if(close(192,192)){if(offer(31))objective(31,1);guide=1;changed();persist();toast(TX_MG_FOLLOW);return 1;}
  if(close(240,192)){if(adventure_save.quests.objectives[31]&1){guide=2;changed();toast(TX_MG_FOLLOW);}else toast(TX_MG_CLUE31A);return 1;}
  if(close(288,192)){if(guide==2){if(offer(31))objective(31,2);}talk(31);return 1;}
  if(npc_close(304,232)){if(done(37))say(TX_MG_HINT_PIKA,TX_MG_HINT_KITE);else if(magma_quest_available(&adventure_save,37))talk(37);else say(TX_MG_OMI,TX_MG_OMIB);return 1;}
  if(npc_close(sen_x(),sen_y())){talk(35);return 1;}
  if(close(80,264)){rest();return 1;}if(close(48,280)){reset_scene();clear_trial();toast(TX_MG_RESET);return 1;}
  if(close(80,88)||close(80,104))return door(41,0);
if(close(400,56)||close(400,72))return door(42,0);
  if(close(104,112)){if(adventure_save.quests.objectives[35]&2)return door(40,0);if((adventure_save.quests.objectives[35]&1)&&offer(35))objective(35,2);persist();toast(TX_MG_CHANGED);return 1;}
  if(close(72,208)){seed=1;changed();toast(TX_MG_CHANGED);return 1;}
  if(close(104,208))return recruit(16,seed,0,TX_MG_HINT_PIKA);
  if(close(80,232)){if(!has_branch(16)){say(TX_MG_BRANCH,TX_MG_BRANCHB);return 1;}if(!(second&1)){second|=1;toast(TX_MG_CHANGED);return 1;}r=recruit(16,1,1,TX_MG_HINT_PIKA);if(r==3)second&=(unsigned char)~1;return 1;}
  if(close(392,208)){wind=(unsigned char)((wind+1)%3);changed();toast(wind==1?TX_MG_HOOD_OPEN:TX_MG_HOOD_CLOSED);return 1;}
  if(close(424,208))return recruit(19,wind==1,0,TX_MG_HINT_KITE);
  if(close(424,240)){if(!has_branch(19)){say(TX_MG_BRANCH,TX_MG_BRANCHB);return 1;}if(!(second&8)){second|=8;toast(TX_MG_CHANGED);return 1;}r=recruit(19,1,1,TX_MG_HINT_KITE);if(r==3)second&=(unsigned char)~8;return 1;}
  if(close(272,96)){brush=1;toast(TX_MG_HINT_SCREE);return 1;}if(close(304,96)){if(brush==1){brush=2;changed();toast(TX_MG_CHANGED);return 1;}return recruit(20,brush==2,0,TX_MG_HINT_SCREE);}
  if(close(368,264)){if(offer(37))objective(37,1);persist();toast(TX_MG_CLUE37B);return 1;}
  if(close(336,240)){if(carrying&&(adventure_save.quests.objectives[37]&2)){objective(37,4);carrying=0;persist();toast(TX_MG_SOLVED);}else toast(TX_MG_TRAY_CARRY);return 1;}
 }
 else if(room==40){
  if(close(208,136)){if(adventure_save.quests.objectives[35]&2)return door(39,1);toast(TX_MG_CLUE35B);return 1;}
  if(npc_close(208,80)){if(done(33))say(TX_MG_HINT_ORE,TX_MG_HINT_MOSS);else talk(33);return 1;}
  if(close(48,64)){if(offer(33))objective(33,1);say(TX_MG_NEMI,TX_MG_NEMIB);return 1;}
  if(close(88,64)){shelf=(unsigned char)((shelf+1)%3);changed();toast(shelf==0?TX_MG_POTS0:shelf==1?TX_MG_POTS1:TX_MG_POTS2);return 1;}
  if(close(128,64)){pot_hood^=1;changed();toast(pot_hood?TX_MG_HOOD_OPEN:TX_MG_HOOD_CLOSED);return 1;}
  if(close(168,64)){if((adventure_save.quests.objectives[33]&1)&&pot_hood==(shelf==2)){pots|=(unsigned char)(1u<<shelf);if(pots==7)objective(33,2);persist();toast(TX_MG_PROGRESS);}else toast(TX_MG_ARRANGE);return 1;}
  if(close(48,96)){if(adventure_save.quests.objectives[36]&1){clapper|=1;toast(TX_MG_PROGRESS);}else toast(TX_MG_CLUE36A);return 1;}
  if(close(80,96)||close(112,96)){clapper|=(unsigned char)(close(80,96)?2:4);changed();if(clapper==7){objective(36,2);persist();toast(TX_MG_SOLVED);}else toast(TX_MG_PROGRESS);return 1;}
  if(close(144,96)||close(176,96)){samples|=(unsigned char)(close(144,96)?1:2);changed();toast(TX_MG_HINT_ORE);return 1;}
  if(close(192,112))return recruit(18,samples==3,0,TX_MG_HINT_ORE);
  if(close(160,112)){if(!has_branch(18)){say(TX_MG_BRANCH,TX_MG_BRANCHB);return 1;}if(!(second&4)){second|=4;toast(TX_MG_CHANGED);return 1;}r=recruit(18,1,1,TX_MG_HINT_ORE);if(r==3)second&=(unsigned char)~4;return 1;}
  if(close(56,112)||close(88,112)){hooks|=(unsigned char)(close(56,112)?1:2);changed();toast(TX_MG_HINT_MOSS);return 1;}
  if(close(120,112))return recruit(21,hooks==3,0,TX_MG_HINT_MOSS);
 }
 else if(room==41){
  if(npc_close(208,80)){if(state(34)==2){claim(34);return 1;}if(!adventure_save.quests.region_flags[19]){discover(1);offer(34);say(TX_MG_DISCOVERY,TX_MG_DISCOVERYB);}else if(done(34))say(TX_MG_HINT_SPONGE,TX_MG_HINT_URCHIN);else talk(34);return 1;}
  if(close(48,64)){if(offer(34))objective(34,1);persist();toast(TX_MG_PROGRESS);return 1;}
  if(close(80,64)){bypass^=1;changed();toast(TX_MG_CHANGED);return 1;}
  if(close(112,64)){if(bypass&&(adventure_save.quests.objectives[34]&1)){basin=1;objective(34,2);persist();toast(TX_MG_SOLVED);}else toast(TX_MG_ARRANGE);return 1;}
  if(close(144,64))return recruit(17,bypass&&basin,0,TX_MG_HINT_SPONGE);
  if(close(176,64)){if(!has_branch(17)){say(TX_MG_BRANCH,TX_MG_BRANCHB);return 1;}if(!(second&2)){second|=2;spill=1;toast(TX_MG_CHANGED);return 1;}r=recruit(17,spill,1,TX_MG_HINT_SPONGE);if(r==3){second&=(unsigned char)~2;spill=0;}return 1;}
  if(close(48,96)){discover(1);say(TX_MG_DISCOVERY,TX_MG_DISCOVERYB);return 1;}
  if(close(80,96)||close(144,96)){sound^=(unsigned char)(close(80,96)?1:2);changed();if(sound==3)discover(2);persist();toast(TX_MG_CHANGED);return 1;}
  if(close(176,96)){if(sound==3&&adventure_save.quests.region_flags[19]==3){discover(4);say(TX_MG_DISCOVERY_READY,TX_MG_DISCOVERY_READYB);}else toast(TX_MG_HINT_URCHIN);return 1;}
  if(close(192,112))return recruit(22,adventure_save.quests.region_flags[19]==7,0,TX_MG_HINT_URCHIN);
 }
 else if(room<=44){
  if(close(216,56)){unsigned bit=1u<<(room-42);if(adventure_save.quests.objectives[32]&bit)return door((unsigned)room+1,0);say(room==42?TX_MG_MAIN_A:room==43?TX_MG_MAIN_B:TX_MG_MAIN_C,room==42?TX_MG_MAIN_AB:room==43?TX_MG_MAIN_BB:TX_MG_MAIN_CB);return 1;}
  if(close(24,64)){say(room==42?TX_MG_MAIN_A:room==43?TX_MG_MAIN_B:TX_MG_MAIN_C,TX_MG_GRAB_HELPB);return 1;}
  if(room==44&&close(216,136)){if(adventure_save.quests.objectives[32]&4)return door(39,2);toast(TX_MG_ARRANGE);return 1;}
  if(room==44&&close(72,112)){if((adventure_save.quests.objectives[37]&1)&&offer(37)){objective(37,2);carrying=1;persist();toast(TX_MG_TRAY_CARRY);}else toast(TX_MG_CLUE37A);return 1;}
 }
 else{
  if(close(120,112)){if(!magma_game_machine_stage){magma_game_machine_stage=1;magma_game_machine_ticks=60;reg_lane=0;changed();say(TX_MG_BOSS,TX_MG_BOSSB);}else toast(TX_MG_BOSS);return 1;}
  if(close(32,80)||close(208,80)){reg_divert=1;changed();toast(magma_game_machine_stage==3?TX_MG_OPEN:TX_MG_CHANGED);return 1;}
  if(close(208,136)&&magma_game_machine_stage==5)return door(38,0);
  if(close(24,48)){say(TX_MG_BOSS,TX_MG_BOSSB);return 1;}
 }
 return 0;}
COLD int magma_game_power(unsigned command){int x,y,r;(void)command;if(game_state!=PLAY||!magma_game_is_room((unsigned)room)||grab!=255)return 0;sync();
 if((room==42||room==44)&&magma_puzzle_position(&magma_game_puzzle,(unsigned)room,0,&x,&y)&&close(x,y)){if(!field(23,x,y))return wrong(TX_MG_WRONG);if(!magma_puzzle_charge(&magma_game_puzzle,(unsigned)room))return wrong(TX_MG_COLD);if(trial_index==0&&participant())trial_aux|=4;changed();toast(TX_MG_CHARGED);return 1;}
 if((room==43||room==44)&&close(168,104)){if(!field(15,168,104))return wrong(TX_MG_WRONG);if(!magma_puzzle_brace(&magma_game_puzzle,(unsigned)room))return wrong(TX_MG_ARRANGE);changed();if(room==43){objective(32,2);if(trial_index==2&&participant())trial_mark(4);}persist();toast(room==43?TX_MG_SOLVED:TX_MG_PIN);return 1;}
 r=trial_power();if(r)return r;return 0;}
unsigned magma_game_action_begin(unsigned channel){if(channel>3)return 0;action_token[channel]++;if(!action_token[channel])action_token[channel]++;action_hits&=(unsigned char)~(1u<<channel);return action_token[channel];}
COLD int magma_game_target(int*x,int*y,int*r){if(room==44&&magma_puzzle_solved(&magma_game_puzzle,44)&&!(adventure_save.quests.objectives[32]&4)){if(x)*x=192;if(y)*y=104;if(r)*r=7;return 1;}if(room!=45||magma_game_machine_stage!=3||!reg_divert||!magma_game_machine_hp)return 0;if(x)*x=120;if(y)*y=64;if(r)*r=13;return 1;}
static COLD int boss_damage(int x,int y,unsigned damage,unsigned channel,unsigned token){if(channel>3||!token||action_token[channel]!=token||room!=45||game_state!=PLAY||(action_hits&(1u<<channel))||!magma_game_target(0,0,0)||!damage||!near(x,y,120,64,27))return 0;action_hits|=(unsigned char)(1u<<channel);reg_window_hit=1;if(damage>magma_game_machine_hp)damage=magma_game_machine_hp;magma_game_machine_hp=(unsigned char)(magma_game_machine_hp-damage);changed();if(!magma_game_machine_hp){magma_game_machine_stage=5;magma_game_machine_ticks=0;objective(32,8);progression_encounter(45,0);persist();toast(TX_MG_MACHINE_DONE);}return 1;}
COLD int magma_game_weapon_hit(unsigned cls,int x,int y,unsigned damage,unsigned channel,unsigned token){if(channel>2||!token||action_token[channel]!=token||game_state!=PLAY||cls<1||cls>3||cls!=game_weapon_class()||!damage)return 0;if(room==44&&magma_game_target(0,0,0)&&near(x,y,192,104,20)&&line_clear(192,104)){objective(32,4);persist();toast(TX_MG_SOLVED);return 1;}return boss_damage(x,y,damage,channel,token);}
COLD int magma_game_command_hit(int x,int y,unsigned damage,unsigned token){return boss_damage(x,y,damage,3,token);}
COLD void magma_game_tick(void){if(game_state!=PLAY||!magma_game_is_room((unsigned)room))return;if(door_notice)door_notice--;world_clock++;if((world_clock&31)==0)changed();
 if(room==45&&magma_game_machine_stage>=1&&magma_game_machine_stage<=4){if(magma_game_machine_ticks){magma_game_machine_ticks--;/* The bitmap sweep moves with its damaging position, not the slower
 * ambient animation clock. Modal early returns freeze both this revision
 * and the sweep timer. Avoid dirtying unrelated progression UI per frame. */
if(magma_game_machine_stage==2)magma_game_revision++;}if(magma_game_machine_stage==2&&!reg_hit&&px>=48+(36-magma_game_machine_ticks)*4&&px<=60+(36-magma_game_machine_ticks)*4&&py>=(reg_lane?94:76)&&py<=(reg_lane?112:94)){reg_hit=1;game_north_hurt(16);}if(!magma_game_machine_ticks){if(magma_game_machine_stage==1){magma_game_machine_stage=2;magma_game_machine_ticks=36;reg_hit=0;}else if(magma_game_machine_stage==2){magma_game_machine_stage=3;magma_game_machine_ticks=90;toast(reg_divert?TX_MG_OPEN:TX_MG_BOSSB);}else if(magma_game_machine_stage==3){magma_game_machine_stage=4;magma_game_machine_ticks=30;}else{magma_game_machine_stage=1;magma_game_machine_ticks=60;if(magma_game_machine_hp<=96)reg_lane^=1;if(reg_window_hit)reg_divert=0;reg_window_hit=0;toast(TX_MG_WARN);}changed();}}
 if(transition_lock||grab!=255)return;
 if(room==38){if((keys&UP)&&px>=288&&px<=320&&py<=18){door(39,0);return;}}
 else if(room==39){if((keys&DOWN)&&px>=224&&px<=255&&py>=298){door(38,1);return;}}
 else if((keys&DOWN)&&px>=108&&px<=132&&py>=143){unsigned dest=room==40?38:room==41||room==42?39:(unsigned)room-1,spawn=room==40||room==42?2:room==41?1:0;door(dest,spawn);}
}
COLD int magma_game_name(void){static const int n[8]={TX_MG_ROOM38,TX_MG_ROOM39,TX_MG_ROOM40,TX_MG_ROOM41,TX_MG_ROOM42,TX_MG_ROOM43,TX_MG_ROOM44,TX_MG_ROOM45};return magma_game_is_room((unsigned)room)?n[room-38]:0;}
COLD int magma_game_quest_text(void){unsigned q;for(q=30;q<=37;q++)if(state(q)==2)return qnames[q-30];if(!done(30))return TX_MG_Q30;if(!done(31))return TX_MG_Q31;if(!done(32))return TX_MG_Q32;return TX_MG_JOURNAL;}
#include "magma_game_draw.inc"
