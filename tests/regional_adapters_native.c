#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "progression.h"
#include "quickparty.h"
#include "regional_quests.h"
#include "regional_creature_art.h"
#include "ui.h"

volatile int room,px,py,spirit,game_state,has_save,save_failed;
volatile unsigned chapter_flags;
int journal_tab,frame,ability_cd,heal_cd,gfx_companion_frame,checkpoint_spawn;
static unsigned checks, saves, art_calls, forms_seen[256], last_toast;
static const unsigned char fallback_art[256]={1};
#define CHECK(x) do{if(!(x)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);exit(1);}++checks;}while(0)
void rect(int a,int b,int c,int d,unsigned char e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void text(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void centered(int a,int b,int c){(void)a;(void)b;(void)c;}
void sprite(const unsigned char*a,int b,int c,int d,int e,int f){CHECK(a!=NULL);(void)b;(void)c;(void)d;(void)e;(void)f;}
void save_game(void){++saves;}
void toast(int n){last_toast=(unsigned)n;}
void sfx(int a){(void)a;}
const unsigned char* companion_pixels(int family,int d,int f){(void)d;(void)f;fprintf(stderr,"FAIL legacy companion_pixels(%d) called in adapter\n",family);exit(1);}
const unsigned char* companion_form_pixels(unsigned form,unsigned d,unsigned f){CHECK(creatures_form_id_valid(form));CHECK(d<4);CHECK(f<4);++art_calls;++forms_seen[form];return fallback_art;}

static void clean(void){
 memset(save5_test_sram,255,sizeof save5_test_sram);memset(save4_test_sram,255,sizeof save4_test_sram);
 save5_test_reset_writer();save5_test_fail_after(-1);save5_test_corrupt_write(-1,0);
 room=0;px=120;py=120;spirit=0;game_state=3;chapter_flags=0;journal_tab=3;
 saves=0;art_calls=0;memset(forms_seen,0,sizeof forms_seen);
 progression_new();CHECK(equipment_validate(&adventure_save.equipment));CHECK(equipment_count(&adventure_save.equipment)==1);CHECK(save5_validate(&adventure_save));
}
static void fresh(unsigned chapter){clean();chapter_flags=chapter;adventure_save.campaign.chapter_flags=chapter;adventure_save.campaign.story_seen=(chapter&1?2:0)|(chapter&2?8:0);progression_story();CHECK(save5_validate(&adventure_save));}
static unsigned find(unsigned form){unsigned i;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==form)return i;return 255;}
static void claim(unsigned q){unsigned bit,mask=regional_quest_mask(q);CHECK(regional_quest_offer(&adventure_save,q)==REGION_QUEST_CHANGED);for(bit=1;bit<=4;bit<<=1)if(mask&bit){int n=regional_quest_objective(&adventure_save,q,bit);CHECK(n==REGION_QUEST_CHANGED||n==REGION_QUEST_NOW_READY);}CHECK(regional_quest_claim(&adventure_save,q)==REGION_QUEST_REWARDED);CHECK(save5_validate(&adventure_save));}
static void regional(void){CHECK(regional_visit(&adventure_save,16)==REGION_QUEST_CHANGED);claim(2);claim(3);}
static void selection(void){
 unsigned water,metal,ordinary,legacy,identity,before[4],i;CreatureRoster*r=&adventure_save.roster;CreatureInstance*selected;Save5State snapshot;
 fresh(7);regional();water=find(13);metal=find(16);CHECK(water<160&&metal<160);CHECK(!(r->instances[water].flags&CREATURE_STORY_LOCKED));CHECK(!(r->instances[metal].flags&CREATURE_STORY_LOCKED));
 legacy=r->party[1];CHECK(quickparty_assign(1,water));CHECK(r->party[1]==water);CHECK(quickparty_select(1));CHECK(progression_current_spirit()==4);CHECK(spirit==4);CHECK(adventure_save.campaign.spirit==0);CHECK(progression_command()==9);
 identity=progression_selected()->instance_id;CHECK(quickparty_assign(3,water));CHECK(r->party[3]==water&&r->selected_party==3);CHECK(progression_selected()->instance_id==identity);CHECK(r->party[1]!=water);
 CHECK(quickparty_assign(2,metal));CHECK(quickparty_select(2));CHECK(progression_current_spirit()==5&&spirit==5);CHECK(progression_command()==11);CHECK(adventure_save.campaign.spirit==0);
 CHECK(quickparty_cycle());CHECK(progression_selected()->instance_id==identity);CHECK(progression_current_spirit()==4);
 CHECK(quickparty_assign(2,legacy));CHECK(quickparty_select(2));CHECK(progression_current_spirit()==1&&spirit==1);CHECK(adventure_save.campaign.spirit==1);
 ordinary=creatures_grant(r,1,12,50,0,0);CHECK(ordinary<160);CHECK(quickparty_assign(2,ordinary));CHECK(quickparty_select(2)||r->selected_party==2);selected=progression_selected();CHECK(selected->instance_id==r->instances[ordinary].instance_id);CHECK(!(selected->flags&CREATURE_STORY_LOCKED));
 identity=selected->instance_id;spirit=3;progression_story();CHECK(progression_selected()->instance_id==identity);CHECK(spirit==0&&progression_current_spirit()==0);
 CHECK(quickparty_select(3));identity=progression_selected()->instance_id;spirit=0;adventure_save.campaign.spirit=1;CHECK(progression_save_begin());CHECK(progression_selected()->instance_id==identity);CHECK(adventure_save.campaign.spirit==0);for(i=0;i<200&&save5_status()==SAVE5_BUSY;i++)progression_save_step();CHECK(save5_status()==SAVE5_DONE);
 snapshot=adventure_save;memset(&adventure_save,0xcc,sizeof adventure_save);spirit=0;CHECK(progression_load());CHECK(progression_selected()->instance_id==identity);CHECK(progression_current_spirit()==4&&spirit==4);CHECK(adventure_save.campaign.spirit==0);CHECK(!memcmp(&adventure_save.roster,&snapshot.roster,sizeof r[0]));CHECK(equipment_validate(&adventure_save.equipment));
 for(i=0;i<4;i++)before[i]=r->party[i];CHECK(!quickparty_assign(4,water));CHECK(!quickparty_assign(0,160));CHECK(!quickparty_assign(0,254));CHECK(!quickparty_select(4));for(i=0;i<4;i++)CHECK(r->party[i]==before[i]);
 quickparty_candidate=3;quickparty_draw();quickparty_menu_candidate=water;quickparty_draw_journal();CHECK(forms_seen[13]>0);CHECK(art_calls>0);
}
static void evolution(void){
 unsigned water,identity,i;CreatureInstance*c;Save5State snapshot;fresh(7);regional();water=find(13);CHECK(quickparty_assign(1,water));CHECK(quickparty_select(1));c=progression_selected();identity=c->instance_id;
 CHECK(creatures_add_xp(c,creatures_xp_threshold(15)-c->xp));c->bond=45;CHECK(creatures_mark_trial(c,CREATURE_TRIAL_PAIRED_POOLS));CHECK(progression_command()==9);room=16;CHECK(progression_is_sanctuary());
 CHECK(save5_quest_set_state(&adventure_save.quests,2,SAVE5_QUEST_READY));chapter_flags=15;game_state=3;CHECK(progression_menu_input(4));CHECK(game_state==3);CHECK(c->form_id==13);game_state=7;progression_confirm_input(1);CHECK(game_state==3&&c->form_id==13);
 CHECK(save5_quest_set_state(&adventure_save.quests,2,SAVE5_QUEST_CLAIMED));c->trial_flags=0;game_state=3;CHECK(progression_menu_input(4));CHECK(game_state==3&&c->form_id==13);claim(4);CHECK(c->trial_flags&CREATURE_TRIAL_PAIRED_POOLS);
 room=17;px=120;py=232;CHECK(progression_is_sanctuary());px=150;CHECK(!progression_is_sanctuary());px=120;py=263;CHECK(!progression_is_sanctuary());room=18;CHECK(!progression_is_sanctuary());room=16;
 game_state=3;CHECK(progression_menu_input(4));CHECK(game_state==7);snapshot=adventure_save;progression_confirm_input(2);CHECK(game_state==3);CHECK(!memcmp(&snapshot,&adventure_save,sizeof snapshot));
 CHECK(progression_menu_input(4));CHECK(game_state==7);progression_confirm_input(1);CHECK(game_state==8);CHECK(c->form_id==14);CHECK(c->instance_id==identity&&c->equipped[0]==9&&c->selected_command==0);CHECK(progression_current_spirit()==4&&spirit==4);
 progression_draw_evolution();for(i=0;i<40;i++)progression_evolution_tick();progression_draw_evolution();for(;i<80;i++)progression_evolution_tick();CHECK(game_state==3);
 progression_draw_tab();CHECK(progression_command()==9);CHECK(progression_menu_input(256));CHECK(progression_command()==10);CHECK(progression_menu_input(256));CHECK(progression_command()==9);CHECK(c->instance_id==identity&&c->form_id==14);CHECK(creatures_instance_validate(c));CHECK(save5_validate(&adventure_save));
 CHECK(creatures_equip(c,1,10));CHECK(progression_command()==9);CHECK(progression_menu_input(256));CHECK(c->selected_command==1&&progression_command()==10);CHECK(c->equipped[0]==9&&c->equipped[1]==10);CHECK(progression_menu_input(256));CHECK(c->selected_command==0&&progression_command()==9);CHECK(c->equipped[0]==9&&c->equipped[1]==10);
 /* Inspect both normal draw fallback and selected malformed command safely. */
 c->selected_command=255;CHECK(progression_command()==0);progression_draw_tab();c->selected_command=0;
}
static void controls(void){
 unsigned water,metal,i,old_saves;CreatureRoster*r=&adventure_save.roster;CreatureInstance*c;CreatureU8 party[4];
 fresh(7);regional();water=find(13);metal=find(16);
 CHECK(quickparty_assign(1,water));CHECK(quickparty_assign(2,metal));quickparty_reset(0);
 CHECK(quickparty_update(512,512));CHECK(quickparty_open);CHECK(quickparty_update(512|16,16));CHECK(quickparty_candidate==1);CHECK(quickparty_update(0,0));CHECK(!quickparty_open);CHECK(progression_current_form()==13&&spirit==4);
 CHECK(quickparty_update(512,512));CHECK(quickparty_update(0,0));CHECK(progression_current_form()==16&&spirit==5);
 old_saves=saves;journal_tab=3;CHECK(progression_menu_input(256));CHECK(progression_command()==11&&saves==old_saves);CHECK(progression_menu_input(4));CHECK(game_state==3);progression_draw_tab();
 CHECK(quickparty_update(512,512));CHECK(quickparty_update(512|32,32));CHECK(quickparty_update(512|2,2));CHECK(!quickparty_open&&progression_current_form()==16);CHECK(quickparty_update(0,0));
 journal_tab=2;quickparty_menu_slot=0;quickparty_menu_candidate=water;CHECK(quickparty_menu_input(256));CHECK(r->party[0]==water);CHECK(r->party[1]!=water);CHECK(progression_current_form()==16);
 c=progression_selected();i=c->instance_id;progression_select(5);CHECK(progression_selected()->instance_id==i);progression_select(255);CHECK(progression_selected()->instance_id==i);progression_select(4);CHECK(progression_current_form()==13&&spirit==4);
 for(i=0;i<4;i++)party[i]=r->party[i];quickparty_menu_candidate=255;CHECK(quickparty_menu_input(128));CHECK(quickparty_menu_candidate<160);for(i=0;i<4;i++)CHECK(r->party[i]==party[i]);
 for(i=1;i<4;i++)CHECK(quickparty_assign(i,255));CHECK(r->party[0]==water&&r->selected_party==0);old_saves=saves;CHECK(!quickparty_assign(0,255));CHECK(saves==old_saves);CHECK(r->party[0]==water);CHECK(!quickparty_cycle());
 for(i=0;i<CREATURE_ENABLED_COUNT;i++){unsigned form=creature_forms[i].id;CHECK(progression_form_spirit(form)<6);CHECK(progression_name_id(form)!=TX_C_UNKNOWN);}
 for(i=0;i<256;i++)if(!creatures_form_id_valid(i)){CHECK(progression_form_spirit(i)==255);CHECK(progression_name_id(i)==TX_C_UNKNOWN);}
}
static void invalid(void){
 CreatureRoster snapshot;CreatureRoster*r=&adventure_save.roster;unsigned i;fresh(0);snapshot=*r;for(i=0;i<256;i++)if(!creatures_form_id_valid(i)){CHECK(creatures_grant(r,i,1,1,0,0)==255);CHECK(!memcmp(r,&snapshot,sizeof snapshot));}
 r->instances[10]=r->instances[0];r->instances[10].form_id=121;r->instances[10].instance_id=100;CHECK(!quickparty_assign(2,10));quickparty_menu_candidate=10;quickparty_draw_journal();
 r->party[2]=10;r->selected_party=2;CHECK(!quickparty_select(2));CHECK(!progression_selected());CHECK(progression_current_spirit()==0);progression_draw_tab();progression_draw_evolution();
 r->selected_party=255;CHECK(!progression_selected());CHECK(progression_command()==0);progression_confirm_input(1);progression_draw_evolution();
}
int main(void){selection();evolution();controls();invalid();printf("regional adapter host checks: %u passed (real save5/creatures/equipment, rendering stubs)\n",checks);return 0;}
