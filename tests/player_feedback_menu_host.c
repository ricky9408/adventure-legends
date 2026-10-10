/* Actual menu/core/save code with explicit host-only engine bridges. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "progression.h"
#include "gear_menu.h"
#include "quickparty.h"
#include "journal_nav.h"
volatile int room,px,py,spirit,game_state,has_save,save_failed;
volatile unsigned chapter_flags;
int journal_tab,frame,ability_cd,heal_cd,gfx_companion_frame,checkpoint_spawn;
unsigned region_game_journal_selection,north_game_journal_selection,south_game_journal_selection,magma_game_journal_selection,underwater_game_journal_selection,return_game_journal_selection,horizons_game_journal_selection,covenants_game_journal_selection;
static unsigned pages=13,saves,hp=96,busy,applies;
unsigned journal_page_count(void){return pages;}
void save_game(void){saves++;}
void toast(int id){(void)id;}
void sfx(int id){(void)id;}
unsigned game_gear_base_hp(void){return 96;}
unsigned game_power_cooldown(unsigned base){return base;}
unsigned game_gear_hp(void){return hp;}
unsigned game_gear_busy(void){return busy;}
void game_gear_apply(unsigned value){hp=value;applies++;}
void game_gear_apply_stats(unsigned value,const EquipmentStats*stats){assert(stats);hp=value;applies++;}
void game_gear_bonus_stats(EquipmentStats*s){(void)s;}
static unsigned selection_cancellations;
#define CANCEL_BRIDGE(name) void name(void){selection_cancellations++;}
CANCEL_BRIDGE(south_game_cancel_rest)
CANCEL_BRIDGE(magma_game_cancel_return)
CANCEL_BRIDGE(underwater_powers_selection_changed)
CANCEL_BRIDGE(underwater_game_selection_changed)
CANCEL_BRIDGE(return_powers_selection_changed)
CANCEL_BRIDGE(return_legacy_cancel)
CANCEL_BRIDGE(return_game_selection_changed)
CANCEL_BRIDGE(horizons_powers_selection_changed)
CANCEL_BRIDGE(horizons_game_selection_changed)
CANCEL_BRIDGE(covenants_powers_selection_changed)
CANCEL_BRIDGE(covenants_game_selection_changed)
int return_game_is_sanctuary(void){return 0;}
int horizons_game_is_sanctuary(void){return 0;}
int covenants_game_is_sanctuary(void){return 0;}
static void fresh(unsigned form){
 progression_evolution_cancel();save5_test_reset_writer();memset(&adventure_save,0,sizeof adventure_save);
 creatures_roster_init(&adventure_save.roster);equipment_init(&adventure_save.equipment);assert(creatures_grant(&adventure_save.roster,form,50,100,0,0)==0);
 room=0;px=py=120;game_state=3;chapter_flags=1;adventure_save.campaign.chapter_flags=1;adventure_save.roster.instances[0].trial_flags=1;
 saves=applies=busy=0;save_failed=0;hp=80;progression_refresh();progression_menu_reset();gear_menu_reset();quickparty_menu_reset();assert(creatures_roster_validate(&adventure_save.roster));
}
static void repeat(void){unsigned i;journal_nav_open();assert(journal_nav_keys(16,16)==16);for(i=0;i<17;i++)assert(!journal_nav_keys(16,0));assert(journal_nav_keys(16,0)==16);for(i=0;i<5;i++)assert(!journal_nav_keys(16,0));assert(journal_nav_keys(16,0)==16);
 assert(!journal_nav_keys(0,0));assert(journal_nav_keys(64,64)==64);assert(journal_nav_keys(1,1)==1);for(i=0;i<100;i++)assert(!journal_nav_keys(1,0));assert(journal_nav_input(journal_nav_keys(48,48))==1&&journal_nav_category==0);assert(journal_nav_input(journal_nav_keys(24,24))==2);
}
static void navigation(void){unsigned r,i;static const unsigned count[]={11,11,18,24,24,21,10,12};journal_nav_open();assert(journal_tab==13);assert(journal_nav_input(16)==1&&journal_nav_category==1);assert(journal_nav_input(1)==1&&journal_tab==4);assert(journal_nav_input(3)==1&&journal_tab==13&&!saves);assert(journal_nav_input(9)==2&&!saves);
 journal_nav_category=5;assert(journal_nav_input(1)==1&&journal_tab==14);assert(journal_nav_input(1)==1&&journal_tab==0);assert(journal_nav_input(1)==0&&journal_tab==0);assert(journal_nav_input(2)==1&&journal_tab==14);
 for(r=0;r<8;r++){journal_nav_quest=(int)r+1;assert(journal_nav_input(1)==1&&journal_tab==(int)r+5&&!journal_nav_detail);for(i=0;i<count[r]+1;i++)assert(journal_nav_input(128)==1);assert(journal_nav_input(1)==1&&journal_nav_detail);assert(journal_nav_input(128)==1&&journal_nav_detail);assert(journal_nav_input(2)==1&&!journal_nav_detail&&journal_tab==(int)r+5);assert(journal_nav_input(2)==1&&journal_tab==14);}
 pages=7;journal_nav_quest=2;assert(journal_nav_input(128)==1&&!journal_nav_quest);pages=13;assert(journal_nav_input(2)==1&&journal_tab==13);journal_nav_category=7;assert(journal_nav_input(1)==2);journal_nav_open();assert(journal_nav_input(5)==1&&journal_tab==13&&!saves);
 journal_tab=16;assert(journal_nav_input(1)==1&&!saves);save_failed=1;assert(journal_nav_input(5)==1&&!saves);assert(journal_nav_input(17)==1&&!saves);assert(journal_nav_input(1)==1&&saves==1);save_failed=0;
}
static void equipment(void){EquipmentState before;unsigned ref;fresh(1);journal_tab=4;assert(equipment_claim(&adventure_save.equipment,33,equipment_reward_source(33),&ref)==EQUIPMENT_OK);before=adventure_save.equipment;
 assert(gear_menu_input(16)==1&&gear_menu_slot==1);assert(gear_menu_input(128)==1&&gear_menu_candidate==(int)ref);assert(!memcmp(&before,&adventure_save.equipment,sizeof before)&&hp==80&&!saves);assert(!gear_menu_input(256)&&!gear_menu_input(4)&&!saves);
 assert(gear_menu_input(1)==1&&adventure_save.equipment.equipped[1]==ref&&saves==1&&applies==1&&hp<=80);assert(gear_menu_input(128)==1&&gear_menu_candidate==255);before=adventure_save.equipment;busy=EQUIPMENT_BUSY_ATTACKING;assert(gear_menu_input(1)==1&&!memcmp(&before,&adventure_save.equipment,sizeof before)&&saves==1);busy=0;assert(gear_menu_input(1)==1&&adventure_save.equipment.equipped[1]==255&&saves==2);assert(gear_menu_input(32)==1&&!gear_menu_slot);assert(gear_menu_input(32)==1&&gear_menu_slot==4);before=adventure_save.equipment;assert(!gear_menu_input(3)&&!gear_menu_input(9));assert(!memcmp(&before,&adventure_save.equipment,sizeof before));assert(gear_menu_input(49)==1&&saves==2);
}
static void party(void){CreatureRoster before;unsigned second,third;fresh(1);journal_tab=2;assert(creatures_grant(&adventure_save.roster,4,50,100,0,0)==1);assert(creatures_grant(&adventure_save.roster,7,50,100,0,0)==2);quickparty_menu_reset();before=adventure_save.roster;
 assert(quickparty_menu_input(128)==1&&quickparty_menu_candidate==1&&!memcmp(&before,&adventure_save.roster,sizeof before));assert(!quickparty_menu_input(256)&&!quickparty_menu_input(4)&&!saves);assert(quickparty_menu_input(1)==1&&quickparty_menu_detail&&!memcmp(&before,&adventure_save.roster,sizeof before)&&!saves);assert(quickparty_menu_input(1)==1&&adventure_save.roster.party[0]==1&&adventure_save.roster.party[1]==0&&saves==1);assert(creatures_roster_validate(&adventure_save.roster));before=adventure_save.roster;assert(!quickparty_assign(0,159)&&!memcmp(&before,&adventure_save.roster,sizeof before));quickparty_menu_candidate=255;assert(quickparty_menu_input(1)==1&&adventure_save.roster.party[0]==255&&saves==2);
 fresh(1);journal_tab=2;quickparty_menu_candidate=255;before=adventure_save.roster;assert(quickparty_menu_input(1)==1&&!memcmp(&before,&adventure_save.roster,sizeof before)&&!saves);assert(!quickparty_menu_input(3)&&!quickparty_menu_input(9));
 fresh(1);second=creatures_grant(&adventure_save.roster,121,50,100,0,0);third=creatures_grant(&adventure_save.roster,122,50,100,0,0);assert(second<160&&third<160);assert(quickparty_assign(1,second)||adventure_save.roster.party[1]==second);before=adventure_save.roster;assert(!quickparty_assign(2,third)&&!memcmp(&before,&adventure_save.roster,sizeof before));assert(creatures_roster_validate(&adventure_save.roster));
}
static void field_picker(void){fresh(1);assert(creatures_grant(&adventure_save.roster,4,50,100,0,0)==1);game_state=1;quickparty_reset(0);assert(quickparty_update(512,512)&&quickparty_open);assert(quickparty_update(528,16)&&quickparty_candidate==1&&!adventure_save.roster.selected_party);assert(quickparty_update(0,0)&&!quickparty_open&&adventure_save.roster.selected_party==1);assert(quickparty_update(512,512));assert(quickparty_update(576,64));assert(quickparty_update(514,2)&&!quickparty_open&&adventure_save.roster.selected_party==1);assert(quickparty_update(512,0)&&!quickparty_open);assert(quickparty_update(0,0));assert(quickparty_update(512,512));assert(quickparty_update(520,8)&&game_state==3&&journal_tab==13);}
static void settle(void){unsigned i;for(i=0;i<300&&progression_evolution_busy();i++)progression_confirm_input(0);assert(i<300);}
static void growth(void){CreatureRoster before;unsigned original;fresh(2);journal_tab=3;before=adventure_save.roster;original=progression_command();assert(progression_menu_input(16)==1&&progression_menu_command!=original);assert(!memcmp(&before,&adventure_save.roster,sizeof before)&&!saves);assert(!progression_menu_input(256)&&!progression_menu_input(4)&&progression_command()==original);assert(progression_menu_input(1)==1&&progression_menu_detail&&!memcmp(&before,&adventure_save.roster,sizeof before)&&!saves);assert(progression_menu_input(1)==1&&progression_command()==progression_menu_command&&saves==1);assert(creatures_roster_validate(&adventure_save.roster));
 fresh(1);journal_tab=3;adventure_save.roster.instances[0].bond=0;before=adventure_save.roster;assert(progression_menu_input(128)==1&&progression_menu_row==1);assert(progression_menu_input(1)==1&&game_state==3&&!memcmp(&before,&adventure_save.roster,sizeof before));
 fresh(1);journal_tab=3;before=adventure_save.roster;assert(save5_validate(&adventure_save));progression_menu_input(128);assert(progression_menu_input(1)==1&&game_state==7);settle();assert(game_state==7&&!memcmp(&before,&adventure_save.roster,sizeof before));progression_confirm_input(4);assert(game_state==7&&!memcmp(&before,&adventure_save.roster,sizeof before));progression_confirm_input(3);assert(game_state==3&&!progression_evolution_busy()&&!memcmp(&before,&adventure_save.roster,sizeof before));progression_menu_input(1);settle();assert(game_state==7);progression_confirm_input(9);assert(game_state==1&&!progression_evolution_busy()&&!memcmp(&before,&adventure_save.roster,sizeof before));game_state=3;progression_menu_input(1);settle();progression_confirm_input(17);settle();assert(game_state==7&&!memcmp(&before,&adventure_save.roster,sizeof before));progression_confirm_input(0);progression_confirm_input(1);settle();assert(game_state==8&&adventure_save.roster.instances[0].form_id==2&&adventure_save.roster.instances[0].instance_id==before.instances[0].instance_id);assert(creatures_roster_validate(&adventure_save.roster));
}
static void writer_done(void){unsigned status,n=0;do{status=save5_step(512);assert(++n<1000);}while(status==SAVE5_BUSY);assert(status==SAVE5_DONE);}
static void committed_boundary(void){Save5State recovered;unsigned char bank[32768];unsigned identity,n=0;
 fresh(1);journal_tab=3;memset(save5_test_sram,255,32768);assert(save5_begin(&adventure_save));writer_done();memcpy(bank,save5_test_sram,sizeof bank);identity=adventure_save.roster.instances[0].instance_id;
 progression_menu_input(128);progression_menu_input(1);settle();assert(game_state==7&&!progression_evolution_busy());progression_confirm_input(1);
 while(!progression_evolution_handoff()){assert(game_state==7&&progression_evolution_busy());progression_confirm_input(0);assert(++n<300);}
 assert(game_state==7&&save5_preflight_active()&&adventure_save.roster.instances[0].form_id==2);assert(!memcmp(bank,save5_test_sram,sizeof bank));
 /* A+B+Start+Select+directions cannot revoke an already committed individual. */
 progression_confirm_input(255);assert(game_state==8&&!progression_evolution_busy()&&!save5_preflight_active());assert(adventure_save.roster.instances[0].form_id==2&&adventure_save.roster.instances[0].instance_id==identity&&!saves);
 assert(save5_load(&recovered)&&recovered.roster.instances[0].form_id==1&&recovered.roster.instances[0].instance_id==identity);
 for(n=0;n<80;n++)progression_evolution_tick();assert(game_state==3&&saves==1&&progression_menu_row==0);
 assert(save5_begin(&adventure_save));writer_done();assert(save5_load(&recovered)&&recovered.roster.instances[0].form_id==2&&recovered.roster.instances[0].instance_id==identity);assert(creatures_roster_count(&recovered.roster)==1);
 puts("PASS evolution commit handoff: immutable lease, cancel chord ignored after commit, publish once, complete old/new SRAM records");
}
void menu_visual_checks(void);
int main(void){fresh(1);repeat();navigation();equipment();party();field_picker();growth();committed_boundary();fresh(1);menu_visual_checks();puts("PASS actual menu C: repeat/backstack, equipment preview/commit/busy, party ownership/swap/last member/legendary, held-L picker, command preview and fresh-A evolution/cancel");return 0;}
