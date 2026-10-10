/* Real companion menus/core plus host-only engine bridges. No ROM QA claim. */
#define main original_menu_main
#include "player_feedback_menu_host.c"
#undef main
#include "companion_guide.h"
#include "companion_guide_text.h"
#include "ui.h"
static unsigned original_cancellations;
static void same(const Save5State*before,unsigned cooldown,unsigned heal){assert(!memcmp(before,&adventure_save,sizeof *before));assert((unsigned)ability_cd==cooldown&&(unsigned)heal_cd==heal);assert(!saves);assert(selection_cancellations==original_cancellations);}
static void browsing(void){
 Save5State before;unsigned i,stored;
 fresh(2);stored=creatures_grant(&adventure_save.roster,5,50,100,0,0);assert(stored<160);
 /* A stored creature must remain inspectable while absent from all four slots. */
 for(i=0;i<4;i++)if(adventure_save.roster.party[i]==stored)adventure_save.roster.party[i]=255;
 journal_tab=2;quickparty_menu_reset();quickparty_menu_candidate=(int)stored;before=adventure_save;original_cancellations=selection_cancellations;ability_cd=37;heal_cd=211;
 assert(quickparty_menu_input(1)&&quickparty_menu_detail);same(&before,37,211);
 for(i=0;i<200;i++){assert(quickparty_menu_input(i&1?16:32));assert(quickparty_menu_input(i&1?64:128));same(&before,37,211);}
 assert(journal_nav_input(2)==JOURNAL_CONSUMED&&!quickparty_menu_detail&&journal_tab==2);same(&before,37,211);
 assert(quickparty_menu_input(1)&&quickparty_menu_detail);assert(journal_nav_input(8)==JOURNAL_CLOSE);same(&before,37,211);quickparty_menu_reset();assert(!quickparty_menu_detail);
 journal_tab=3;progression_menu_reset();assert(progression_menu_input(1)&&progression_menu_detail);same(&before,37,211);
 for(i=0;i<200;i++){assert(progression_menu_input(i&1?16:32));assert(progression_menu_input(i&1?64:128));same(&before,37,211);}
 assert(!progression_menu_input(4));assert(!progression_menu_input(256));same(&before,37,211);
 assert(journal_nav_input(2)==JOURNAL_CONSUMED&&!progression_menu_detail&&journal_tab==3);same(&before,37,211);
 puts("PASS companion browse: stored inspection,200 repeated command/page previews each, nested Back, Start, Select/R inert, complete Save5 and recovery unchanged");
}
static void coverage(void){
 unsigned form,command,i,count=0,phases=0,polarities=0;CreatureInstance c;
 for(command=1;command<=128;command++){
  const CompanionGuideCopy*copy=&companion_guide_commands[command];const CreatureAbility*a=creatures_ability(command);assert(a);
  assert(copy->combat[0]<CG_COUNT&&copy->combat[1]<CG_COUNT&&copy->field<CG_COUNT);
  assert(companion_guide_texts[copy->combat[0]].count[0]&&companion_guide_texts[copy->combat[1]].count[0]&&companion_guide_texts[copy->field].count[0]);
  assert(companion_guide_recovery(command)==(command<=4?75:a->cooldown_updates));
 }
 assert(!companion_guide_recovery(0)&&!companion_guide_recovery(129));
 for(form=1;form<=128;form++){
  const CreatureForm*f=creatures_form(form);assert(f);assert(progression_name_id(form)!=TX_C_UNKNOWN);phases|=1u<<f->phase;polarities|=1u<<f->polarity;
  memset(&c,0,sizeof c);c.form_id=(CreatureU8)form;c.level=50;c.polarity=f->polarity;command=f->signature_ability;
  for(i=0;i<f->learnset_count;i++){
   assert(creatures_command_learned(form,50,command));assert(progression_command_name_id(command)!=TX_E_COMMAND_OLD);
   companion_guide_page=0;companion_guide_draw(&c,command,COMPANION_GUIDE_GROWTH);
   companion_guide_page=1;companion_guide_draw(&c,command,COMPANION_GUIDE_GROWTH);
   command=companion_guide_command_next(&c,command,1);count++;
  }
  assert(command==f->signature_ability);
 }
 assert(phases==31&&polarities==3&&count==CREATURE_LEARNSET_COUNT);
 for(i=0;i<CG_COUNT;i++)assert(companion_guide_texts[i].width<=214&&companion_guide_texts[i].height==15);
 puts("PASS guide coverage:128 forms,128 actual commands,209 learned-command pages,five phases,two polarities,combat recovery values and bounded text");
}
void companion_visual_checks(void);
int main(void){fresh(1);companion_visual_checks();coverage();browsing();party();field_picker();growth();committed_boundary();puts("PASS companion integration: explicit second-A commits; original evolution transaction complete old/new SRAM boundary unchanged");return 0;}
