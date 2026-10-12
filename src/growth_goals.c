#include "growth_goals.h"
#include "growth_journal_text.h"
#include "progression.h"
#include "companion_guide.h"
#include "companion_guide_text.h"
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
extern unsigned short *screen;
extern void text_spans(const UiText*,int,int,int) __attribute__((weak));
extern void box(int,int,int,int),text(int,int,int,int),centered(int,int,int),rect(int,int,int,int,unsigned char);
COLD int growth_goals_query(const CreatureInstance*c,unsigned target,unsigned context,int sanctuary,GrowthGoal*out){
 const CreatureEvolution*e;GrowthGoal g={0,0,0,0,0};
 if(!out)return 0;
 *out=g;
 if(!c||!creatures_form(c->form_id)||(e=creatures_evolution_to(c->form_id,target))==0)return 0;
 g.target=target;g.min_level=e->min_level;g.min_bond=e->min_bond;
 if(c->level>=e->min_level)g.met|=GROWTH_LEVEL;
 if(c->bond>=e->min_bond)g.met|=GROWTH_BOND;
 if((context&e->chapter_flags)==e->chapter_flags)g.met|=GROWTH_STORY;
 if((c->trial_flags&e->trial_flag)==e->trial_flag)g.met|=GROWTH_TRIAL;
 if(sanctuary)g.met|=GROWTH_REST;
 if(c->level<CREATURE_MAX_LEVEL){CreatureU32 next=creatures_xp_threshold(c->level+1);g.next_xp=next>c->xp?next-c->xp:0;}
 *out=g;return 1;
}
COLD void growth_goals_text(unsigned label,int x,int y,int color){
 const UiText*t;const UiRun*r;unsigned n,ink;unsigned short*base;
 if(label>=GJ_COUNT)return;
 t=&growth_journal_texts[label];
 if(x<0||y<0||x+t->width>240||y+t->height>160)return;
 if(text_spans){text_spans(t,x,y,color);return;}
 r=t->runs[x&1];n=t->count[x&1];ink=(unsigned)color*257u;base=screen+y*120+(x>>1);
 while(n--){unsigned short*dst=base+r->offset;unsigned count=r->count,mask=r->mask;r++;
  if(mask==3)while(count--)*dst++=(unsigned short)ink;
  else if(mask==1)while(count--){*dst=(unsigned short)((*dst&65280)|(unsigned)color);dst++;}
  else while(count--){*dst=(unsigned short)((*dst&255)|((unsigned)color<<8));dst++;}
 }
}
COLD void growth_goals_center(unsigned label,int y,int color){if(label<GJ_COUNT)growth_goals_text(label,(240-growth_journal_texts[label].width)/2,y,color);}
COLD int growth_goals_number(unsigned value,unsigned places,int x,int y,int color){
 static const unsigned scale[6]={100000,10000,1000,100,10,1};unsigned i,started=0;
 if(value>999999)value=999999;
 if(places>6)places=6;
 for(i=0;i<6;i++){unsigned digit=0;while(value>=scale[i]){value-=scale[i];digit++;}
  if(digit||started||i>=6-places||i==5){growth_goals_text(GJ_DIGIT_0+digit,x,y,color);x+=growth_journal_texts[GJ_DIGIT_0].width;started=1;}
 }return x;
}
/* These are the authored trial texts already used at their actual fixtures.
 * Branch targets bind exact trials, rather than a first-edge family hint. */
COLD unsigned growth_goals_trial_text(unsigned from,unsigned target,unsigned line){
 static const int magma[15][3]={
  {TX_MG_TRIAL0,TX_MG_TRIAL0A,TX_MG_TRIAL0B},{TX_MG_TRIAL1,TX_MG_TRIAL1A,TX_MG_TRIAL1B},
  {TX_MG_TRIAL2,TX_MG_TRIAL2A,TX_MG_TRIAL2B},{TX_MG_TRIAL3,TX_MG_TRIAL3A,TX_MG_TRIAL3B},
  {TX_MG_TRIAL4,TX_MG_TRIAL4A,TX_MG_TRIAL4B},{TX_MG_TRIAL5,TX_MG_TRIAL5A,TX_MG_TRIAL5B},
  {TX_MG_TRIAL6,TX_MG_TRIAL6A,TX_MG_TRIAL6B},{TX_MG_TRIAL7,TX_MG_TRIAL7A,TX_MG_TRIAL7B},
  {TX_MG_TRIAL8,TX_MG_TRIAL8A,TX_MG_TRIAL8B},{TX_MG_TRIAL9,TX_MG_TRIAL9A,TX_MG_TRIAL9B},
  {TX_MG_TRIAL10,TX_MG_TRIAL10A,TX_MG_TRIAL10B},{TX_MG_TRIAL11,TX_MG_TRIAL11A,TX_MG_TRIAL11B},
  {TX_MG_TRIAL12,TX_MG_TRIAL12A,TX_MG_TRIAL12B},{TX_MG_TRIAL13,TX_MG_TRIAL13A,TX_MG_TRIAL13B},
  {TX_MG_TRIAL14,TX_MG_TRIAL14A,TX_MG_TRIAL14B}};
 static const int underwater[16][3]={
  {TX_UW_TRIAL0,TX_UW_TRIAL0A,TX_UW_TRIAL0B},{TX_UW_TRIAL1,TX_UW_TRIAL1A,TX_UW_TRIAL1B},
  {TX_UW_TRIAL2,TX_UW_TRIAL2A,TX_UW_TRIAL2B},{TX_UW_TRIAL3,TX_UW_TRIAL3A,TX_UW_TRIAL3B},
  {TX_UW_TRIAL4,TX_UW_TRIAL4A,TX_UW_TRIAL4B},{TX_UW_TRIAL5,TX_UW_TRIAL5A,TX_UW_TRIAL5B},
  {TX_UW_TRIAL6,TX_UW_TRIAL6A,TX_UW_TRIAL6B},{TX_UW_TRIAL7,TX_UW_TRIAL7A,TX_UW_TRIAL7B},
  {TX_UW_TRIAL8,TX_UW_TRIAL8A,TX_UW_TRIAL8B},{TX_UW_TRIAL9,TX_UW_TRIAL9A,TX_UW_TRIAL9B},
  {TX_UW_TRIAL10,TX_UW_TRIAL10A,TX_UW_TRIAL10B},{TX_UW_TRIAL11,TX_UW_TRIAL11A,TX_UW_TRIAL11B},
  {TX_UW_TRIAL12,TX_UW_TRIAL12A,TX_UW_TRIAL12B},{TX_UW_TRIAL13,TX_UW_TRIAL13A,TX_UW_TRIAL13B},
  {TX_UW_TRIAL14,TX_UW_TRIAL14A,TX_UW_TRIAL14B},{TX_UW_TRIAL15,TX_UW_TRIAL15A,TX_UW_TRIAL15B}};
 unsigned index=255;if(line>2||!creatures_evolution_to(from,target))return TX_C_UNKNOWN;
 if(from>=49&&from<=70&&(from-49)%3==0){index=((from-49)/3)*2+(target==from+2);return underwater[index][line];}
 if(from==31)index=0;else if(from==32)index=1;else if(from==34)index=2;else if(from==35)index=3;
 else if(from==37)index=4+(target==39);else if(from==40)index=6+(target==42);
 else if(from==43)index=8+(target==45);else if(from==46)index=10+(target==48);
 else if(from==95)index=12;else if(from==97)index=13;else if(from==99)index=14;
 if(index<15)return magma[index][line];
 return progression_wish_id(from);
}
static COLD unsigned story_label(unsigned mask){
 switch(mask){case CREATURE_GROVE_CLEAR:return GJ_STORY_GROVE;case CREATURE_SKY_CLEAR:return GJ_STORY_SKY;
 case CREATURE_CORE_CLEAR:return GJ_STORY_CORE;case CREATURE_REED_RESTORED:return GJ_STORY_REED;
 case CREATURE_NORTH_HARBOR_READY:return GJ_STORY_NORTH;case CREATURE_COUNTERWORKS_STABLE:return GJ_STORY_COUNTER;
 case CREATURE_SOUTH_READY:return GJ_STORY_SOUTH;case CREATURE_SUNWELL_OPEN:return GJ_STORY_SUNWELL;
 case CREATURE_MAGMA_READY:return GJ_STORY_MAGMA;case CREATURE_CALDERA_OPEN:return GJ_STORY_CALDERA;
 case CREATURE_UNDERWATER_READY:return GJ_STORY_UNDERWATER;case CREATURE_PALINODE_OPEN:return GJ_STORY_PALINODE;
 case CREATURE_RETURN_READY:return GJ_STORY_RETURN;case CREATURE_HORIZONS_READY:return GJ_STORY_HORIZONS;
 default:return GJ_STORY;}
}
static COLD void mark(int x,int y,int met){rect(x,y+3,7,7,PAL_STONE1);if(met){rect(x+1,y+6,2,2,TEAL);rect(x+3,y+4,3,2,TEAL);}else rect(x+2,y+5,3,2,PAL_GOLD2);}
COLD void growth_goals_draw(const CreatureInstance*c,unsigned target,unsigned context,int sanctuary,unsigned page,int confirm,int preparing){
 GrowthGoal g;const CreatureForm*f=creatures_form(target);const CreatureEvolution*e=c?creatures_evolution_to(c->form_id,target):0;
 box(8,31,224,123);if(!f||!growth_goals_query(c,target,context,sanctuary,&g)){centered(TX_E_NO_MEMBER,81,CREAM);return;}
 centered(progression_name_id(target),33,GOLD);
 if(page==2){companion_guide_axes(target,f->polarity,49);centered(progression_command_name_id(f->signature_ability),65,GOLD);companion_guide_combat(f->signature_ability,81);companion_guide_center(CG_EVOLVE,113,TEAL);}
 else if(page==1){growth_goals_center(GJ_TRIAL,49,TEAL);centered((int)growth_goals_trial_text(c->form_id,target,0),65,GOLD);
  if(growth_goals_trial_text(c->form_id,target,1)!=growth_goals_trial_text(c->form_id,target,0))centered((int)growth_goals_trial_text(c->form_id,target,1),81,CREAM);
  if(growth_goals_trial_text(c->form_id,target,2)!=growth_goals_trial_text(c->form_id,target,1))centered((int)growth_goals_trial_text(c->form_id,target,2),97,CREAM);
  growth_goals_center(g.met&GROWTH_TRIAL?GJ_DONE:GJ_SAME_INDIVIDUAL,113,g.met&GROWTH_TRIAL?TEAL:CREAM);
 }else{
  growth_goals_center(GJ_CURRENT_REQUIRED,49,TEAL);
  mark(16,65,g.met&GROWTH_LEVEL);growth_goals_text(GJ_LEVEL,27,65,CREAM);growth_goals_number(c->level,1,46,65,CREAM);growth_goals_text(GJ_SLASH,63,65,TEAL);growth_goals_number(g.min_level,1,72,65,GOLD);
  mark(119,65,g.met&GROWTH_BOND);growth_goals_text(GJ_BOND,130,65,CREAM);growth_goals_number(c->bond,1,146,65,CREAM);growth_goals_text(GJ_SLASH,171,65,TEAL);growth_goals_number(g.min_bond,1,180,65,GOLD);
  growth_goals_text(GJ_NEXT_XP,22,81,TEAL);if(c->level==CREATURE_MAX_LEVEL)growth_goals_text(GJ_LEVEL_MAX,131,81,GOLD);else growth_goals_number(g.next_xp,1,131,81,CREAM);
  mark(16,97,g.met&GROWTH_STORY);growth_goals_text(story_label(e->chapter_flags),27,97,CREAM);
  mark(159,97,g.met&GROWTH_REST);growth_goals_text(GJ_REST,170,97,CREAM);
  mark(16,113,g.met&GROWTH_TRIAL);text((int)growth_goals_trial_text(c->form_id,target,0),27,113,CREAM);
 }
 if(preparing)centered(TX_UW_PREPARING,138,TEAL);
 else growth_goals_center(!confirm?GJ_INSPECT_KEYS:g.met==GROWTH_ALL?(confirm>1?GJ_READY_BRANCH_KEYS:GJ_READY_KEYS):(confirm>1?GJ_GOAL_KEYS:GJ_GOAL_SINGLE_KEYS),138,TEAL);
}
