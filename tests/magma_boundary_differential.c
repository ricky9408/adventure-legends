/* Portable F-source oracle versus current typed Magma adapters. This is
 * synthetic state/transaction proof, not native cadence/acquisition evidence. */
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "magma_game.h"
#include "magma_quests.h"
#include "progression.h"
Save5State adventure_save;
unsigned progression_revision,progression_forms[PROGRESSION_SPIRIT_COUNT];
volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
volatile unsigned chapter_flags;
int face,keys,journal_tab;
static unsigned saved,health_fills,last_toast;
CreatureInstance *progression_selected(void){return 0;}
unsigned progression_command(void){return 0;}
void progression_refresh(void){++progression_revision;}
void save_game(void){++saved;adventure_save.campaign.room=(Save4U8)room;adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;}
void dialogue(int a,int b,int c){(void)a;(void)b;game_state=c;}
void toast(int a){last_toast=(unsigned)a;}
void text(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void centered(int a,int b,int c){(void)a;(void)b;(void)c;}
void box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void rect(int a,int b,int c,int d,unsigned char e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void line(int a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void magma_actor(unsigned a,int b,int c){(void)a;(void)b;(void)c;}
void region_form_actor(unsigned a,int b,int c){(void)a;(void)b;(void)c;}
void game_health_fill(void){health_fills++;}
void game_region_warp(int x,int y){px=x;py=y;}
unsigned game_weapon_class(void){return 1;}
void game_north_hurt(unsigned a){(void)a;}
int game_magma_actor_overlap(int a,int b,int c){(void)a;(void)b;(void)c;return 0;}
#include MAGMA_SOURCE
#ifdef NEW_ADAPTER
static unsigned inject_offset=~0u,inject_scene,probe_apply,callback_mode;
#endif
void enter_room(int r,int s){
#ifdef NEW_ADAPTER
 int result;
 if(magma_return_job.applying==1){
  if(magma_game_request_return()!=1)return;
  room=r;checkpoint_spawn=s;(void)magma_game_enter((unsigned)r,(unsigned)s);return;
 }
 if(callback_mode==1)return;
 if(callback_mode==2)assert(!magma_game_commit_enter());
 if(callback_mode==3){magma_game_cancel_enter();assert(!magma_game_enter((unsigned)r,(unsigned)s));return;}
 if(callback_mode==4){assert(!magma_game_request_enter((unsigned)r,(unsigned)s+1));assert(!magma_game_enter((unsigned)r,(unsigned)s));return;}
 if(callback_mode==7){assert(!magma_game_request_enter((unsigned)r+1,(unsigned)s));return;}
 if(callback_mode==8){assert(!magma_game_enter((unsigned)r,(unsigned)s));return;}
 if(magma_game_request_enter((unsigned)r,(unsigned)s)!=1)return;
 room=r;checkpoint_spawn=s;px=120;py=132;
 if(callback_mode==5)assert(!magma_game_commit_enter());
 if(callback_mode==6)magma_game_cancel_enter();
 if(inject_offset<sizeof adventure_save)((unsigned char*)&adventure_save)[inject_offset]^=1;
 switch(inject_scene){case 1:room++;break;case 2:checkpoint_spawn++;break;case 3:face^=1;break;case 4:chapter_flags^=1;break;case 5:progression_revision++;break;case 6:game_state++;break;case 7:magma_scene++;break;default:break;}
 if(probe_apply)(void)magma_enter_apply((unsigned)r,(unsigned)s,&result);
 else (void)magma_game_enter((unsigned)r,(unsigned)s);
#else
 room=r;checkpoint_spawn=s;
#endif
}
static Save5State bases[16],mutant;
#ifdef NEW_ADAPTER
static Save5State before;
#endif
static unsigned nbase,cases,max_entry_steps,max_anchor_steps;
static void load(const char *path){FILE*f=fopen(path,"rb");assert(f);assert(fread(save5_test_sram,1,32768,f)==32768);assert(!fclose(f));save5_test_reset_writer();assert(save5_load(&bases[nbase]));assert(save5_validate(&bases[nbase]));++nbase;}
static void setup(const Save5State*s){
 magma_game_reset();save5_test_reset_writer();adventure_save=*s;
#ifdef NEW_ADAPTER
 inject_offset=~0u;inject_scene=probe_apply=callback_mode=0;
#endif
 room=s->campaign.room;checkpoint_spawn=s->campaign.spawn;chapter_flags=s->campaign.chapter_flags;
 px=144;py=218;face=1;game_state=1;summoned=1;transition_lock=7;camera_x=20;camera_y=25;keys=3;journal_tab=8;
 progression_revision=31;magma_game_revision=17;magma_game_journal_selection=2;saved=health_fills=last_toast=0;
 magma_scene=71;grab=255;dirty=1;branch_visible=3;lesson_x=168;screen_x=152;hood=guide=seed=wind=brush=samples=hooks=bypass=basin=1;
 shelf=pot_hood=pots=clapper=sound=spill=second=carrying=door_notice=reg_divert=reg_lane=reg_hit=reg_window_hit=action_hits=1;
 trial_index=4;trial_slot=3;trial_bits=2;trial_aux=1;trial_order=1;trial_id=73;
 magma_game_puzzle.cell[0]=2;magma_game_puzzle.cell[1]=5;magma_game_puzzle.heat=1;magma_game_puzzle.brace=1;
 magma_game_machine_stage=2;magma_game_machine_ticks=8;magma_game_machine_hp=67;world_clock=43;
 pending_anchor_area=0;pending_anchor_spawn=0;pending_anchor_checkpoint=0;
}
static void emit(int result){struct Observation{Save5State save;unsigned v[80];}o;unsigned i=0;memset(&o,0,sizeof o);o.save=adventure_save;
#define W(x) o.v[i++]=(unsigned)(x)
 W(result);W(room);W(checkpoint_spawn);W(px);W(py);W(game_state);W(face);W(chapter_flags);W(progression_revision);W(magma_game_revision);W(saved);W(health_fills);W(last_toast);W(dirty);W(magma_scene);W(grab);W(branch_visible);W(lesson_x);W(screen_x);W(hood);W(guide);W(seed);W(wind);W(brush);W(samples);W(hooks);W(bypass);W(basin);W(shelf);W(pot_hood);W(pots);W(clapper);W(sound);W(spill);W(second);W(carrying);W(door_notice);W(reg_divert);W(reg_lane);W(reg_hit);W(reg_window_hit);W(action_hits);W(trial_index);W(trial_slot);W(trial_bits);W(trial_aux);W(trial_order);W(trial_id);W(magma_game_puzzle.cell[0]);W(magma_game_puzzle.cell[1]);W(magma_game_puzzle.heat);W(magma_game_puzzle.brace);W(magma_game_machine_stage);W(magma_game_machine_ticks);W(magma_game_machine_hp);W(world_clock);W(pending_anchor_area);W(pending_anchor_spawn);W(pending_anchor_checkpoint);W(magma_game_journal_selection);W(summoned);W(transition_lock);W(camera_x);W(camera_y);W(keys);W(journal_tab);
#undef W
 assert(i<=80);assert(fwrite(&o,1,sizeof o,stdout)==sizeof o);++cases;
}
#ifdef NEW_ADAPTER
static unsigned prepare_entry(void){unsigned n=0,status;game_state=10;do{status=magma_game_prepare_enter();assert(++n<128);}while(status==SAVE5_BUSY);if(n>max_entry_steps)max_entry_steps=n;game_state=1;return status;}
static int queued_entry(unsigned a,unsigned s){int r;unsigned status;
 if(room==46&&a==38&&s==4){
  unsigned n=0;before=adventure_save;assert(!magma_game_request_enter(a,s));assert(!memcmp(&before,&adventure_save,sizeof before));
  r=magma_game_request_return();if(r!=2){assert(!r);return 0;}
  game_state=10;do{status=magma_game_prepare_return();assert(++n<128);}while(status==SAVE5_BUSY);
  game_state=1;if(status!=SAVE5_DONE)return 0;return magma_game_commit_return();
 }
 r=magma_game_request_enter(a,s);if(r!=2){assert(!r);return 0;}before=adventure_save;status=prepare_entry();assert(!memcmp(&before,&adventure_save,sizeof before));if(status!=SAVE5_DONE)return 0;r=magma_game_commit_enter();assert(r);assert(!magma_game_enter_pending());assert(!magma_game_commit_enter());return r;}
static int queued_anchor(void){unsigned n=0,status;do{status=magma_game_prepare_save_step();assert(++n<128);}while(status==SAVE5_BUSY);if(n>max_anchor_steps)max_anchor_steps=n;return status==SAVE5_DONE;}
static void queue_rest(void){setup(&bases[4]);room=39;checkpoint_spawn=0;adventure_save.campaign.room=39;adventure_save.campaign.spawn=0;rest();game_state=6;assert(magma_game_save_prepare_pending());}
static void ready_anchor(void){unsigned n=0;assert(magma_game_prepare_save_step()==SAVE5_BUSY);while(magma_anchor_job.phase!=2){assert(magma_game_prepare_save_step()==SAVE5_BUSY);assert(++n<128);}}
static void stale(void){unsigned i,count=0;const Save5State*s=&bases[4];
 for(i=0;i<sizeof(Save5State);i++){
  setup(s);assert(magma_game_request_enter(38,0)==2);assert(prepare_entry()==SAVE5_DONE);((unsigned char*)&adventure_save)[i]^=1;before=adventure_save;assert(!magma_game_commit_enter());assert(!memcmp(&before,&adventure_save,sizeof before));assert(!magma_game_enter_pending());count++;
  setup(s);assert(magma_game_request_enter(38,0)==2);assert(prepare_entry()==SAVE5_DONE);before=adventure_save;((unsigned char*)&before)[i]^=1;inject_offset=i;probe_apply=1;assert(!magma_game_commit_enter());assert(!memcmp(&before,&adventure_save,sizeof before));count++;
  queue_rest();ready_anchor();((unsigned char*)&adventure_save)[i]^=1;before=adventure_save;assert(magma_game_prepare_save_step()==SAVE5_FAILED);assert(!memcmp(&before,&adventure_save,sizeof before));assert(!magma_game_save_prepare_pending());count++;
 }
 for(i=0;i<13;i++){setup(s);assert(magma_game_request_enter(38,0)==2);assert(prepare_entry()==SAVE5_DONE);switch(i){case 0:room++;break;case 1:checkpoint_spawn++;break;case 2:px++;break;case 3:py++;break;case 4:face^=1;break;case 5:chapter_flags^=1;break;case 6:progression_revision++;break;case 7:game_state++;break;case 8:save5_preflight_cancel();break;case 9:assert(!magma_game_request_enter(39,0));continue;case 10:assert(!magma_game_request_enter(38,1));continue;case 11:assert(!magma_game_request_enter(38,0));continue;default:magma_scene++;break;}assert(!magma_game_commit_enter());assert(!magma_game_enter_pending());count++;}
 for(i=1;i<=7;i++){setup(s);assert(magma_game_request_enter(38,0)==2);assert(prepare_entry()==SAVE5_DONE);before=adventure_save;inject_scene=i;probe_apply=1;assert(!magma_game_commit_enter());assert(!memcmp(&before,&adventure_save,sizeof before));count++;}
 for(i=1;i<=8;i++){setup(s);assert(magma_game_request_enter(38,0)==2);assert(prepare_entry()==SAVE5_DONE);before=adventure_save;callback_mode=i;assert(!magma_game_commit_enter());assert(!magma_game_enter_pending()&&!magma_enter_job.owned);assert(!memcmp(&before,&adventure_save,sizeof before));count++;}
 for(i=0;i<11;i++){queue_rest();ready_anchor();before=adventure_save;switch(i){case 0:room++;break;case 1:checkpoint_spawn++;break;case 2:px++;break;case 3:py++;break;case 4:face^=1;break;case 5:chapter_flags^=1;break;case 6:progression_revision++;break;case 7:game_state++;break;case 8:save5_preflight_cancel();break;case 9:magma_scene++;break;default:pending_anchor_spawn++;break;}assert(magma_game_prepare_save_step()==SAVE5_FAILED);assert(!memcmp(&before,&adventure_save,sizeof before));assert(!magma_game_save_prepare_pending());count++;}
 setup(s);assert(magma_game_request_enter(38,0)==2);save5_preflight_cancel();{Save4U32 t=save5_preflight_begin(&adventure_save);assert(t);magma_game_cancel_enter();assert(save5_preflight_status(t)==SAVE5_BUSY);save5_preflight_cancel();}
 queue_rest();ready_anchor();save5_preflight_cancel();{Save4U32 t=save5_preflight_begin(&adventure_save);assert(t);cancel_anchor_prepare();assert(save5_preflight_status(t)==SAVE5_BUSY);save5_preflight_cancel();}
 setup(s);assert(magma_game_request_enter(38,0)==2);assert(prepare_entry()==SAVE5_DONE);magma_game_reset();assert(!magma_game_commit_enter());queue_rest();ready_anchor();magma_game_reset();assert(magma_game_prepare_save_step()==SAVE5_FAILED);
 queue_rest();ready_anchor();before=adventure_save;magma_game_cancel_save_prepare();
 assert(!magma_game_save_prepare_pending()&&!magma_anchor_job.token&&checkpoint_spawn==0);
 assert(!memcmp(&before,&adventure_save,sizeof before));magma_game_cancel_save_prepare();
 game_state=1;assert(magma_game_request_enter(38,0)==2);assert(prepare_entry()==SAVE5_DONE);assert(magma_game_commit_enter());count++;
 fprintf(stderr,"stale_byte_scene_ownership_checks=%u\n",count);
}
#endif
static void one(const Save5State*s,unsigned area,unsigned spawn,int mode){setup(s);
#ifdef NEW_ADAPTER
 emit(mode?queued_entry(area,spawn):magma_game_enter(area,spawn));
#else
 (void)mode;emit(magma_game_enter(area,spawn));
#endif
}
static void anchor_one(const Save5State*s,unsigned area,unsigned spawn,int mode){setup(s);room=(int)area;checkpoint_spawn=(int)spawn;adventure_save.campaign.room=(Save4U8)area;adventure_save.campaign.spawn=(Save4U8)spawn;rest();game_state=6;
#ifdef NEW_ADAPTER
 emit(mode?queued_anchor():magma_game_prepare_save());
#else
 (void)mode;emit(magma_game_prepare_save());
#endif
}
static void first_visits(void){unsigned q,b;Save5State*s=&bases[nbase];*s=bases[0];assert(magma_visit(s,38)==MAGMA_CHANGED);assert(save5_validate(s));++nbase;
 for(q=30;q<=31;q++){s=&bases[nbase];*s=bases[nbase-1];if(q==31)assert(magma_visit(s,39)==MAGMA_CHANGED);assert(magma_quest_offer(s,q)==MAGMA_CHANGED);for(b=1;b<=magma_quest_mask(q);b<<=1)if(magma_quest_mask(q)&b)assert(magma_quest_objective(s,q,b)>=MAGMA_CHANGED);assert(magma_quest_claim(s,q)==MAGMA_REWARDED);assert(save5_validate(s));++nbase;}
 for(q=42;q<=44;q++){s=&bases[nbase];*s=bases[nbase-1];assert(magma_visit(s,q)==MAGMA_CHANGED);if(q==42)assert(magma_quest_offer(s,32)==MAGMA_CHANGED);assert(magma_quest_objective(s,32,1u<<(q-42))>=MAGMA_CHANGED);assert(save5_validate(s));++nbase;}
}
int main(int argc,char**argv){unsigned a,s,i,j,v;int mode;static const unsigned areas[]={0,37,38,39,40,41,42,43,44,45,46,UINT_MAX},spawns[]={0,1,2,3,4,5,UINT_MAX};assert(argc==7);mode=atoi(argv[1]);for(i=2;i<7;i++)load(argv[i]);first_visits();
#ifdef NEW_ADAPTER
 if(mode==2){stale();return 0;}
#endif
 for(i=0;i<nbase;i++)for(a=0;a<12;a++)for(s=0;s<7;s++)one(&bases[i],areas[a],spawns[s],mode);
 for(i=0;i<nbase;i++)for(a=38;a<=39;a++)for(s=0;s<5;s++)anchor_one(&bases[i],a,s,mode);
 for(i=0;i<sizeof(Save5State);i++)for(j=0;j<3;j++){mutant=bases[4];((unsigned char*)&mutant)[i]^=(unsigned char)(j==0?1:j==1?128:255);one(&mutant,38,0,mode);anchor_one(&mutant,39,0,mode);}
 for(i=0;i<256;i++)for(j=0;j<4;j++)for(v=0;v<16;v++){mutant=bases[7];mutant.quests.region_flags[3]=(Save4U8)i;save5_quest_set_state(&mutant.quests,32,j);mutant.quests.objectives[32]=(Save4U16)v;if(j==3)mutant.quests.rewards[4]|=1;else mutant.quests.rewards[4]&=(Save4U8)~1u;one(&mutant,42+(v%4),0,mode);}
 fprintf(stderr,"cases=%u max_entry_updates=%u max_anchor_updates=%u save_bytes=%u\n",cases,max_entry_steps,max_anchor_steps,(unsigned)sizeof(Save5State));return 0;
}
