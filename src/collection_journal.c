#include "collection_journal.h"
#include "growth_goals.h"
#include "growth_journal_text.h"
#include "progression.h"
#include "companion_guide.h"
#include "assets.h"
#include "ui.h"
#if defined(__arm__)
#define COLD __attribute__((section(".text.rom")))
#else
#define COLD
#endif
#define GOLD PAL_GOLD3
#define CREAM PAL_GOLD4
#define TEAL PAL_TEAL2
extern void box(int,int,int,int),text(int,int,int,int),centered(int,int,int),rect(int,int,int,int,unsigned char),sprite(const unsigned char*,int,int,int,int,int);
extern const unsigned char*companion_form_pixels(unsigned,unsigned,unsigned);
/* 300 bytes of menu-only EWRAM. Open rebuilds once from the paused roster,
 * avoiding60 repeated160-record scans in a cold native draw. */
static unsigned char root[60],known[60],obtained[60],total[60],owned[60];
static unsigned form_count,family_count,known_count,goal_page;
unsigned collection_journal_family,collection_journal_form,collection_journal_filter,collection_journal_detail;
static int bit(const CreatureU8*b,unsigned form){return form&&form<=128&&(b[(form-1)>>3]&(1u<<((form-1)&7)));}
static COLD int eligible(unsigned family){unsigned i=family-1;return family&&family<=60&&known[i]&&(!collection_journal_filter||(collection_journal_filter==1?owned[i]!=0:obtained[i]<total[i]));}
static COLD unsigned first_form(unsigned family){unsigned i;for(i=1;i<=128;i++){const CreatureForm*f=creatures_form(i);if(f&&f->family==family)return i;}return 0;}
COLD void collection_journal_counts(unsigned*forms,unsigned*families,unsigned*discovered){if(forms)*forms=form_count;if(families)*families=family_count;if(discovered)*discovered=known_count;}
COLD void collection_journal_open(void){unsigned i;
 for(i=0;i<60;i++)root[i]=known[i]=obtained[i]=total[i]=owned[i]=0;
 form_count=family_count=known_count=0;collection_journal_filter=collection_journal_detail=goal_page=0;
 for(i=1;i<=128;i++){const CreatureForm*f=creatures_form(i);unsigned family=f?f->family:0;if(!family||family>60)continue;
  if(!root[family-1])root[family-1]=(unsigned char)i;
  total[family-1]++;
  if(bit(adventure_save.roster.seen,i)||bit(adventure_save.roster.obtained,i))known[family-1]=1;
  if(bit(adventure_save.roster.obtained,i)){obtained[family-1]++;form_count++;}
 }
 for(i=0;i<160;i++){const CreatureInstance*c=&adventure_save.roster.instances[i];const CreatureForm*f=(c->flags&CREATURE_OCCUPIED)?creatures_form(c->form_id):0;if(f&&f->family<=60){owned[f->family-1]=1;known[f->family-1]=1;}}
 for(i=0;i<60;i++){family_count+=obtained[i]!=0;known_count+=known[i]!=0;}
 collection_journal_family=0;for(i=1;i<=60;i++)if(eligible(i)){collection_journal_family=i;break;}
 collection_journal_form=first_form(collection_journal_family);
}
static COLD void family_move(int delta){unsigned i,next=collection_journal_family;for(i=0;i<60;i++){next=delta>0?(next>=60?1:next+1):(next<=1?60:next-1);if(eligible(next)){collection_journal_family=next;collection_journal_form=first_form(next);return;}}collection_journal_family=collection_journal_form=0;}
static COLD void form_move(int delta){unsigned i,next=collection_journal_form;for(i=0;i<128;i++){const CreatureForm*f;next=delta>0?(next>=128?1:next+1):(next<=1?128:next-1);f=creatures_form(next);if(f&&f->family==collection_journal_family){collection_journal_form=next;return;}}}
COLD unsigned collection_journal_instance(void){unsigned i;for(i=0;i<160;i++){const CreatureInstance*c=&adventure_save.roster.instances[i];if((c->flags&CREATURE_OCCUPIED)&&c->form_id==collection_journal_form)return i;}return CREATURE_EMPTY_SLOT;}
static COLD unsigned predecessor(void){unsigned i,j;for(i=0;i<CREATURE_EVOLUTION_COUNT;i++)if(creature_evolutions[i].to==collection_journal_form)for(j=0;j<160;j++){const CreatureInstance*c=&adventure_save.roster.instances[j];if((c->flags&CREATURE_OCCUPIED)&&c->form_id==creature_evolutions[i].from)return j;}return CREATURE_EMPTY_SLOT;}
COLD int collection_journal_back(void){if(!collection_journal_detail)return 0;collection_journal_detail--;return 1;}
COLD int collection_journal_input(int input){unsigned dir=(unsigned)input&240u;
 if(input&(2|8|4|256|512))return COLLECTION_CONSUMED;
 if(collection_journal_detail==2){if(dir==64||dir==128)goal_page=(goal_page+(dir==64?2u:1u))%3u;return COLLECTION_CONSUMED;}
 if(!collection_journal_detail){
  if(dir==64||dir==128)family_move(dir==128?1:-1);
  else if(dir==16||dir==32){collection_journal_filter=(collection_journal_filter+(dir==16?1u:2u))%3u;if(!eligible(collection_journal_family))family_move(1);}
  else if(!dir&&(input&1)&&collection_journal_family)collection_journal_detail=1;
  return COLLECTION_CONSUMED;
 }
 if(dir==16||dir==32)form_move(dir==16?1:-1);
 else if(!dir&&(input&1)){
  if(collection_journal_instance()!=CREATURE_EMPTY_SLOT)return COLLECTION_OPEN_PARTY;
  if(predecessor()!=CREATURE_EMPTY_SLOT){collection_journal_detail=2;goal_page=0;}
 }
 return COLLECTION_CONSUMED;
}
static COLD unsigned region(unsigned form){unsigned adapter=progression_form_spirit(form);
 unsigned i;for(i=0;i<CREATURE_EVOLUTION_COUNT;i++)if(creature_evolutions[i].to==form){
  if(creature_evolutions[i].chapter_flags&CREATURE_RETURN_READY)return GJ_REGION_RETURN;
  if(creature_evolutions[i].chapter_flags&CREATURE_HORIZONS_READY)return GJ_REGION_HORIZONS;
 }
 if(adapter<4)return GJ_REGION_CORE;
 if(adapter<6)return GJ_REGION_REED;
 if(adapter<11)return GJ_REGION_NORTH;
 if(adapter<21)return GJ_REGION_SOUTH;
 if(adapter<30)return GJ_REGION_MAGMA;
 if(adapter<38)return GJ_REGION_UNDERWATER;
 if(adapter<40)return GJ_REGION_RETURN;
 if(adapter<52)return GJ_REGION_HORIZONS;
 return GJ_REGION_COVENANTS;
}
static COLD void ratio(unsigned value,unsigned max,int x,int y){x=growth_goals_number(value,3,x,y,CREAM);growth_goals_text(GJ_SLASH,x,y,TEAL);growth_goals_number(max,3,x+growth_journal_texts[GJ_SLASH].width,y,GOLD);}
COLD void collection_journal_draw(void){unsigned i,p,shown=0,family=collection_journal_family,form=collection_journal_form;const CreatureForm*f=creatures_form(form);
 if(collection_journal_detail==2){p=predecessor();if(p<160){growth_goals_draw(&adventure_save.roster.instances[p],form,progression_evolution_context(),progression_is_sanctuary(),goal_page,0,0);return;}collection_journal_detail=1;}
 box(8,31,224,123);growth_goals_center(GJ_COLLECTION,33,GOLD);
 if(!collection_journal_detail){unsigned pos=0,first=0,count=0;
  growth_goals_text(GJ_FORMS,16,49,TEAL);ratio(form_count,128,42,49);growth_goals_text(GJ_FAMILIES,132,49,TEAL);ratio(family_count,60,163,49);
  growth_goals_center(collection_journal_filter==1?GJ_OWNED_FILTER:collection_journal_filter==2?GJ_MISSING_FILTER:GJ_KNOWN,65,TEAL);
  for(i=1;i<=60;i++)if(eligible(i)){if(i==family)pos=count;count++;}
  if(pos>2)first=pos-2;
  count=0;for(i=1;i<=60&&shown<3;i++)if(eligible(i)){if(count++<first)continue;
   int y=82+(int)shown*17;if(i==family)rect(13,y-1,214,16,PAL_STONE2);
   /* One known family reveals its potential evolution names, just as Growth
    * does. Completely unseen families never enter this list. */
   text(progression_name_id(root[i-1]),18,y,i==family?GOLD:CREAM);ratio(obtained[i-1],total[i-1],172,y);shown++;
  }
  if(!shown)growth_goals_center(GJ_NO_FAMILIES,99,CREAM);
  growth_goals_center(GJ_FAMILY_KEYS,138,TEAL);return;
 }
 if(!f||!family)return;
 centered(progression_name_id(form),49,GOLD);
 {const unsigned char*pixels=companion_form_pixels(form,0,0);if(pixels)sprite(pixels,112,67,16,16,0);}
 growth_goals_center(region(form),84,TEAL);p=collection_journal_instance();
 growth_goals_center(p<160?GJ_OWNED:bit(adventure_save.roster.obtained,form)?GJ_HISTORY:GJ_MISSING,100,CREAM);
 if(p<160){growth_goals_text(GJ_INSTANCE,85,116,TEAL);growth_goals_number(p+1,3,110,116,CREAM);growth_goals_center(GJ_FORM_KEYS,138,TEAL);}
 else if(bit(adventure_save.roster.obtained,form)){growth_goals_center(GJ_HISTORY_KEEP,116,CREAM);growth_goals_center(GJ_FORM_KEYS,138,TEAL);}
 else if(predecessor()<160)growth_goals_center(GJ_GOALS_OPEN,138,TEAL);
 else{
  /* Branch repeats are authored only in Magma/Underwater. Never promise a
   * nonexistent repeat source for story or fixed legendary families. */
  unsigned label=(f->family>=13&&f->family<=24)?GJ_REPEAT_FIRST:GJ_PREDECESSOR_FIRST;
  growth_goals_center(label,116,CREAM);growth_goals_center(GJ_FORM_KEYS,138,TEAL);
 }
}
