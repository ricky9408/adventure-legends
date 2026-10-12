/* Synthetic boundary states, real production query/nav/draw/commit code.
 * These tests are not controller-earned acquisition or native timing proof. */
#define main original_menu_main
#include "player_feedback_menu_host.c"
#undef main
#define text framebuffer_text
#define centered framebuffer_centered
#include "player_feedback_menu_draw.c"
#undef text
#undef centered
#include "growth_goals.h"
#include "growth_journal_text.h"
#include "collection_journal.h"
#if defined(__APPLE__)
/* Mach-O does not resolve these optional ELF weak symbols to zero. Map is
 * outside this isolated journal test; native integration uses its real module. */
void journey_map_begin(void){}
void journey_map_open(void){}
int journey_map_input(int input){(void)input;return 0;}
void journey_map_draw(void){}
#endif
static int observed[64];static unsigned observed_count;
void text(int id,int x,int y,int color){if(observed_count<64)observed[observed_count++]=id;framebuffer_text(id,x,y,color);}
void centered(int id,int y,int color){text(id,(240-ui_texts[id].width)/2,y,color);}
static int saw(unsigned id){unsigned i;for(i=0;i<observed_count;i++)if(observed[i]==(int)id)return 1;return 0;}
static void query_and_pixels(void){unsigned i,mask,page,cases=0;GrowthGoal g;CreatureInstance c,before;
 for(i=0;i<CREATURE_EVOLUTION_COUNT;i++){
  const CreatureEvolution*e=&creature_evolutions[i];const CreatureForm*f=creatures_form(e->from);
  memset(&c,0,sizeof c);c.form_id=e->from;c.flags=1;c.polarity=f->polarity;c.instance_id=1;c.equipped[0]=creature_learnsets[f->learnset_offset].ability_id;
  for(mask=0;mask<=31;mask++){
   c.level=(CreatureU8)(mask&GROWTH_LEVEL?e->min_level:e->min_level-1);c.xp=creatures_xp_threshold(c.level);
   c.bond=(CreatureU8)(mask&GROWTH_BOND?e->min_bond:e->min_bond-1);c.trial_flags=(CreatureU16)(mask&GROWTH_TRIAL?e->trial_flag:0);before=c;
   assert(growth_goals_query(&c,e->to,mask&GROWTH_STORY?e->chapter_flags:0,!!(mask&GROWTH_REST),&g));
   assert(g.min_level==e->min_level&&g.min_bond==e->min_bond&&g.met==mask&&g.next_xp==creatures_xp_threshold(c.level+1)-c.xp);
   for(page=0;page<3;page++){clear();observed_count=0;growth_goals_draw(&c,e->to,mask&GROWTH_STORY?e->chapter_flags:0,!!(mask&GROWTH_REST),page,creatures_evolution_count(c.form_id)>1?2:1,0);assert(!bad_bounds);
    if(page<2)assert(saw(growth_goals_trial_text(c.form_id,e->to,0)));
    assert(!memcmp(&c,&before,sizeof c));cases++;
   }
  }
  c.level=50;c.xp=CREATURE_XP_CAP;assert(growth_goals_query(&c,e->to,e->chapter_flags,1,&g)&&g.next_xp==0);
 }
 assert(growth_goals_trial_text(37,38,0)!=growth_goals_trial_text(37,39,0));
 assert(growth_goals_trial_text(49,50,0)!=growth_goals_trial_text(49,51,0));
 assert(!growth_goals_query(0,2,0,0,&g));assert(!growth_goals_query(&c,0,0,0,&g));
 /* Explicitly capture the original hidden-wish case and both low-level branches. */
 memset(&c,0,sizeof c);c.form_id=1;c.level=12;c.bond=30;c.xp=creatures_xp_threshold(12);clear();growth_goals_draw(&c,2,1,1,0,1,0);capture("growth-homura-missing-bond-and-wish");
 c.form_id=37;c.level=1;c.bond=0;c.xp=0;clear();growth_goals_draw(&c,38,0,0,0,1,0);capture("growth-magma-first-branch-goals");clear();growth_goals_draw(&c,39,0,0,1,1,0);capture("growth-magma-second-branch-clues");
 printf("PASS goals: %u actual-raster cases,all68edges×32independent gate combinations×3pages; branch wishes visible belowLv/bond,accurate XP/max-level and no mutation\n",cases);
}
static void collection_boundaries(void){unsigned forms,families,known,i,filter;Save5State before;unsigned cancellations;
 fresh(1);memset(&adventure_save.roster,0,sizeof adventure_save.roster);before=adventure_save;collection_journal_open();collection_journal_counts(&forms,&families,&known);assert(!forms&&!families&&!known);
 clear();collection_journal_draw();assert(!bad_bounds);assert(!memcmp(&before,&adventure_save,sizeof before));
 /* A seen-only family must be discoverable without claiming acquisition. */
 adventure_save.roster.seen[(49-1)>>3]=(unsigned char)(1u<<((49-1)&7));before=adventure_save;collection_journal_open();collection_journal_counts(&forms,&families,&known);assert(!forms&&!families&&known==1&&collection_journal_family==17);
 collection_journal_input(1);clear();collection_journal_draw();assert(!bad_bounds);assert(!memcmp(&before,&adventure_save,sizeof before));
 /* Complete cumulative history,160 stored duplicate identities: counts must
  * remain128forms/60families, never count instances as collection completion. */
 memset(adventure_save.roster.seen,255,16);memset(adventure_save.roster.obtained,255,16);
 for(i=0;i<160;i++){CreatureInstance*c=&adventure_save.roster.instances[i];c->form_id=(CreatureU8)(i%128+1);c->flags=1;c->instance_id=i+1;c->level=50;c->bond=100;}
 for(i=0;i<4;i++)adventure_save.roster.party[i]=(CreatureU8)i;before=adventure_save;cancellations=selection_cancellations;ability_cd=37;heal_cd=211;
 collection_journal_open();collection_journal_counts(&forms,&families,&known);assert(forms==128&&families==60&&known==60);clear();collection_journal_draw();capture("collection-complete-history-family-list");
 for(filter=0;filter<3;filter++){
  for(i=0;i<120;i++){collection_journal_input(128);clear();collection_journal_draw();assert(!bad_bounds);}
  collection_journal_input(16);
 }
 assert(!memcmp(&before,&adventure_save,sizeof before)&&ability_cd==37&&heal_cd==211&&selection_cancellations==cancellations&&!saves);
 collection_journal_open();collection_journal_input(1);clear();collection_journal_draw();capture("collection-owned-form");
 for(i=0;i<128;i++){collection_journal_input(16);clear();collection_journal_draw();assert(!bad_bounds);}
 assert(collection_journal_back()&&!collection_journal_back());
 /* A opens the same stored individual in Party but changes no assignment. */
 journal_nav_open();journal_nav_category=8;assert(journal_nav_input(1)==JOURNAL_CONSUMED&&journal_tab==JOURNAL_COLLECTION);assert(journal_nav_input(1)==JOURNAL_CONSUMED&&collection_journal_detail==1);
 assert(journal_nav_input(1)==JOURNAL_CONSUMED&&journal_tab==JOURNAL_PARTY&&quickparty_menu_candidate==0);assert(!memcmp(&before,&adventure_save,sizeof before)&&!saves);
 /* Unobtained target with an owned predecessor opens readonly requirements. */
 fresh(37);adventure_save.roster.obtained[(38-1)>>3]&=(CreatureU8)~(1u<<((38-1)&7));adventure_save.roster.obtained[(39-1)>>3]&=(CreatureU8)~(1u<<((39-1)&7));before=adventure_save;collection_journal_open();collection_journal_input(1);collection_journal_input(16);assert(collection_journal_form==38);assert(collection_journal_input(1)==COLLECTION_CONSUMED&&collection_journal_detail==2);clear();collection_journal_draw();assert(!bad_bounds);capture("collection-missing-form-goals");
 for(i=0;i<10;i++){collection_journal_input(128);clear();collection_journal_draw();assert(!bad_bounds);}assert(collection_journal_back()&&collection_journal_detail==1);assert(collection_journal_back()&&!collection_journal_detail);assert(!memcmp(&before,&adventure_save,sizeof before)&&!saves);
 puts("PASS collection:0/seen-only/full128history,60family grouping,160individuals,filters/wrap/nestedBack,exact Party handoff and missing-branch goals; Save5/recovery/selection unchanged");
}
int main(void){fresh(1);query_and_pixels();collection_boundaries();fresh(1);navigation();growth();committed_boundary();assert(!bad_bounds);puts("PASS retainedfresh-A evolution/irreversiblecommit and menu navigation");return 0;}
