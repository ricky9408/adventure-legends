/* Synthetic strict adapter differential. UI/engine calls are inert stubs;
 * production save/creature/equipment/quest code and byte-exact frozen SRAM
 * loading are real. Not native cadence or controller-obtainability evidence. */
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "south_game.h"
#include "southern_quests.h"
#include "progression.h"
Save5State adventure_save;
unsigned progression_revision,progression_forms[PROGRESSION_SPIRIT_COUNT];
volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
volatile unsigned chapter_flags;
int face,keys,journal_tab;
static unsigned saved;
CreatureInstance *progression_selected(void){return 0;}
unsigned progression_command(void){return 0;}
void progression_refresh(void){++progression_revision;}
void save_game(void){++saved;}
void dialogue(int a,int b,int c){(void)a;(void)b;game_state=c;}
void toast(int a){(void)a;}
void text(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void centered(int a,int b,int c){(void)a;(void)b;(void)c;}
void box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void rect(int a,int b,int c,int d,unsigned char e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void line(int a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void south_actor(unsigned a,int b,int c){(void)a;(void)b;(void)c;}
void region_form_actor(unsigned a,int b,int c){(void)a;(void)b;(void)c;}
void game_health_fill(void){}
void game_region_warp(int x,int y){px=x;py=y;}
unsigned game_weapon_class(void){return 1;}
void game_north_hurt(unsigned a){(void)a;}
#include SOUTH_SOURCE
#ifdef NEW_ADAPTER
static unsigned inject_offset=~0u,inject_scene,probe_apply,callback_mode;
#endif
void enter_room(int r,int s){
#ifdef NEW_ADAPTER
 int result;
 if(callback_mode==1)return;
 if(callback_mode==2){assert(!south_game_commit_enter());}
 if(callback_mode==3){south_game_cancel_enter();assert(!south_game_enter((unsigned)r,(unsigned)s));return;}
 if(callback_mode==4){assert(!south_game_request_enter((unsigned)r,(unsigned)s+1));assert(!south_game_enter((unsigned)r,(unsigned)s));return;}
 if(callback_mode==7){assert(!south_game_request_enter((unsigned)r+1,(unsigned)s));return;}
 if(callback_mode==8){assert(!south_game_enter((unsigned)r,(unsigned)s));return;}
 if(south_game_request_enter((unsigned)r,(unsigned)s)!=1)return;
 room=r;checkpoint_spawn=s;
 if(callback_mode==5){assert(!south_game_commit_enter());}
 if(callback_mode==6)south_game_cancel_enter();
 if(inject_offset<sizeof adventure_save)((unsigned char*)&adventure_save)[inject_offset]^=1;
 switch(inject_scene){case 1:room++;break;case 2:checkpoint_spawn++;break;case 3:face^=1;break;
  case 4:chapter_flags^=1;break;case 5:progression_revision++;break;case 6:game_state++;break;default:break;}
 if(probe_apply)(void)south_enter_apply((unsigned)r,(unsigned)s,&result);
 else (void)south_game_enter((unsigned)r,(unsigned)s);
#else
 room=r;checkpoint_spawn=s;
#endif
}
static Save5State bases[16],mutant;
#ifdef NEW_ADAPTER
static Save5State before;
#endif
static unsigned nbase,cases,accepted,queued,max_steps;
static void load(const char *path){
 FILE *f=fopen(path,"rb");assert(f);assert(fread(save5_test_sram,1,32768,f)==32768);assert(!fclose(f));
 save5_test_reset_writer();assert(save5_load(&bases[nbase]));assert(save5_validate(&bases[nbase]));++nbase;
}
static void setup(const Save5State *s){
 south_game_reset();save5_test_reset_writer();adventure_save=*s;
#ifdef NEW_ADAPTER
 inject_offset=~0u;inject_scene=probe_apply=callback_mode=0;
#endif
 room=s->campaign.room;checkpoint_spawn=s->campaign.spawn;
 chapter_flags=s->campaign.chapter_flags;px=144;py=218;face=1;game_state=1;
 summoned=1;transition_lock=7;camera_x=20;camera_y=25;keys=3;journal_tab=7;
 progression_revision=31;south_game_revision=17;south_game_journal_selection=2;saved=0;
 south_game_puzzle.mirror[0]=1;south_game_puzzle.mirror[1]=0;south_game_puzzle.shade=1;
 south_game_machine_stage=2;south_game_machine_ticks=8;south_game_machine_hp=67;
 demo=hood=quiet=roots=drain=panels=ripple=runnel=pins=sun=loft=moisture=alignment=overflow=door_notice=machine_hit=1;
 machine_x=112;dirty=1;trial_index=4;trial_slot=3;trial_bits=2;trial_revealed=1;trial_id=73;
}
static void emit(int result){
 struct Observation {Save5State save;unsigned v[64];} o;
 unsigned i=0;memset(&o,0,sizeof o);o.save=adventure_save;
#define WORD(x) o.v[i++]=(unsigned)(x)
 WORD(result);WORD(room);WORD(checkpoint_spawn);WORD(px);WORD(py);WORD(game_state);WORD(face);
 WORD(chapter_flags);WORD(progression_revision);WORD(south_game_revision);WORD(saved);WORD(dirty);
 WORD(south_game_puzzle.mirror[0]);WORD(south_game_puzzle.mirror[1]);WORD(south_game_puzzle.shade);
 WORD(south_game_machine_stage);WORD(south_game_machine_ticks);WORD(south_game_machine_hp);
 WORD(demo);WORD(hood);WORD(quiet);WORD(roots);WORD(drain);WORD(panels);WORD(ripple);WORD(runnel);
 WORD(pins);WORD(sun);WORD(loft);WORD(moisture);WORD(alignment);WORD(overflow);WORD(door_notice);
 WORD(machine_hit);WORD(machine_x);WORD(trial_index);WORD(trial_slot);WORD(trial_bits);WORD(trial_revealed);WORD(trial_id);
 WORD(south_game_journal_selection);WORD(summoned);WORD(transition_lock);WORD(camera_x);WORD(camera_y);WORD(keys);WORD(journal_tab);
#undef WORD
 assert(i<=64);assert(fwrite(&o,1,sizeof o,stdout)==sizeof o);++cases;if(result)++accepted;
}
#ifdef NEW_ADAPTER
static unsigned prepare(void){
 unsigned steps=0,status;game_state=10;
 do{status=south_game_prepare_enter();assert(++steps<100);}while(status==SAVE5_BUSY);
 if(steps>max_steps)max_steps=steps;
 game_state=1;return status;
}
static int queue_entry(unsigned a,unsigned s){
 unsigned status;int r=south_game_request_enter(a,s);
 if(r!=2){assert(!r);return 0;}++queued;before=adventure_save;
 status=prepare();assert(!memcmp(&before,&adventure_save,sizeof before));
 if(status!=SAVE5_DONE){assert(status==SAVE5_FAILED);return 0;}
 r=south_game_commit_enter();assert(r==1);assert(!south_game_enter_pending());
 assert(!south_game_commit_enter());return r;
}
static void stale_tests(void){
 unsigned i,seen=0;const Save5State *valid=&bases[2];
 for(i=0;i<sizeof(Save5State);++i){
  setup(valid);assert(south_game_request_enter(30,0)==2);assert(prepare()==SAVE5_DONE);
  ((unsigned char*)&adventure_save)[i]^=1;before=adventure_save;
  assert(!south_game_commit_enter());assert(!south_game_enter_pending());
  assert(!memcmp(&before,&adventure_save,sizeof before));++seen;
  setup(valid);assert(south_game_request_enter(30,0)==2);assert(prepare()==SAVE5_DONE);
  before=adventure_save;((unsigned char*)&before)[i]^=1;
  inject_offset=i;probe_apply=1;
  assert(!south_game_commit_enter());assert(!south_game_enter_pending());
  assert(!memcmp(&before,&adventure_save,sizeof before));++seen;
 }
 for(i=0;i<12;++i){
  setup(valid);assert(south_game_request_enter(30,0)==2);assert(prepare()==SAVE5_DONE);
  switch(i){case 0:room++;break;case 1:checkpoint_spawn++;break;case 2:px++;break;case 3:py++;break;
   case 4:face^=1;break;case 5:chapter_flags^=1;break;case 6:progression_revision++;break;
   case 7:game_state++;break;case 8:save5_preflight_cancel();break;
   case 9:assert(!south_game_request_enter(31,0));continue;
   case 10:assert(!south_game_request_enter(30,1));continue;
   default:assert(!south_game_request_enter(30,0));continue;}
  assert(!south_game_commit_enter());assert(!south_game_enter_pending());++seen;
 }
 /* The armed lease is still bound to the actual engine destination and
  * unchanged runtime identity until the exact patch is consumed. */
 for(i=1;i<=6;++i){
  setup(valid);assert(south_game_request_enter(30,0)==2);assert(prepare()==SAVE5_DONE);
  before=adventure_save;inject_scene=i;probe_apply=1;
  assert(!south_game_commit_enter());
  assert(!south_game_enter_pending());assert(!memcmp(&before,&adventure_save,sizeof before));++seen;
 }
 /* Failed/reentrant engine callbacks cannot retain the private lease or
  * turn a revoked prepared operation into a synchronous fallback mutation. */
 for(i=1;i<=8;++i){
  setup(valid);assert(south_game_request_enter(30,0)==2);assert(prepare()==SAVE5_DONE);
  before=adventure_save;callback_mode=i;assert(!south_game_commit_enter());
  assert(!south_game_enter_pending()&&!south_enter_job.owned);
  assert(!memcmp(&before,&adventure_save,sizeof before));++seen;
 }
 /* A stale owner cannot revoke another generation's private shared scratch. */
 setup(valid);assert(south_game_request_enter(30,0)==2);save5_preflight_cancel();
 {Save4U32 token=save5_preflight_begin(&adventure_save);assert(token);south_game_cancel_enter();assert(save5_preflight_status(token)==SAVE5_BUSY);save5_preflight_cancel();}
 /* Rest/load/new-scene reset revokes proof; the same pair cannot replay it. */
 setup(valid);assert(south_game_request_enter(30,0)==2);assert(prepare()==SAVE5_DONE);south_game_reset();assert(!south_game_commit_enter());
 fprintf(stderr,"stale_exact_bytes_and_scene=%u\n",seen);
}
#endif
static void one(const Save5State *source,unsigned a,unsigned s,int mode){
 setup(source);
#ifdef NEW_ADAPTER
 emit(mode?queue_entry(a,s):south_game_enter(a,s));
#else
 (void)mode;emit(south_game_enter(a,s));
#endif
}
static void first_visit_bases(void){
 Save5State *s=&bases[nbase];unsigned q,b;
 *s=bases[0];assert(southern_visit(s,30)==SOUTH_CHANGED);
 for(q=22;q<=23;++q){if(q==23)assert(southern_visit(s,31)==SOUTH_CHANGED);
  assert(southern_quest_offer(s,q)==SOUTH_CHANGED);
  for(b=1;b<=2;b<<=1)assert(southern_quest_objective(s,q,b)>=SOUTH_CHANGED);
  assert(southern_quest_claim(s,q)==SOUTH_REWARDED);
 }
 assert(save5_validate(s));++nbase;
 for(q=34;q<=36;++q){s=&bases[nbase];*s=bases[nbase-1];assert(southern_visit(s,q)==SOUTH_CHANGED);
  if(q==34)assert(southern_quest_offer(s,24)==SOUTH_CHANGED);
  assert(southern_quest_objective(s,24,1u<<(q-34))>=SOUTH_CHANGED);
  assert(save5_validate(s));++nbase;
 }
}
int main(int argc,char **argv){
 unsigned a,s,i,j,v;int mode;static const unsigned areas[]={0,29,30,31,32,33,34,35,36,37,38,UINT_MAX};
 static const unsigned spawns[]={0,1,2,3,4,5,UINT_MAX};
 assert(argc==7);mode=atoi(argv[1]);for(i=2;i<7;++i)load(argv[i]);first_visit_bases();
#ifdef NEW_ADAPTER
 if(mode==2){stale_tests();return 0;}
#endif
 for(i=0;i<nbase;++i)for(a=0;a<sizeof areas/sizeof areas[0];++a)for(s=0;s<sizeof spawns/sizeof spawns[0];++s)one(&bases[i],areas[a],spawns[s],mode);
 /* Every byte in the whole Save5 structure, including padding and unused
  * records, is independently corrupted at low/high/all bit patterns. */
 for(i=0;i<sizeof(Save5State);++i)for(j=0;j<3;++j){mutant=bases[2];((unsigned char*)&mutant)[i]^=(unsigned char)(j==0?1:j==1?128:255);one(&mutant,30,0,mode);}
 /* All visit-byte/quest24 state/objective combinations. Both accepted and
  * rejected cases go through the unchanged original gate/validator oracle. */
 for(i=0;i<256;++i)for(j=0;j<4;++j)for(v=0;v<16;++v){
  mutant=bases[5];mutant.quests.region_flags[2]=(Save4U8)i;
  save5_quest_set_state(&mutant.quests,24,j);mutant.quests.objectives[24]=(Save4U16)v;
  if(j==3)mutant.quests.rewards[3]|=1;else mutant.quests.rewards[3]&=(Save4U8)~1u;
  one(&mutant,34+(v%4),0,mode);
 }
 fprintf(stderr,"cases=%u accepted=%u queued=%u max_prepare_updates=%u save_bytes=%u\n",cases,accepted,queued,max_steps,(unsigned)sizeof(Save5State));return 0;
}
