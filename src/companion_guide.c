/* ROM-only display code; transient page cursor is ordinary EWRAM. */
#include "companion_guide.h"
#include "companion_guide_text.h"
#include "progression.h"
#include "assets.h"
#include "gear_runtime.h"
extern unsigned short *screen;
extern void text_spans(const UiText*,int,int,int) __attribute__((weak));
extern void box(int,int,int,int),text(int,int,int,int),centered(int,int,int),rect(int,int,int,int,unsigned char);
#define GOLD PAL_GOLD3
#define CREAM PAL_GOLD4
#define TEAL PAL_TEAL2
unsigned companion_guide_page;
void companion_guide_text(unsigned label,int x,int y,int color){
 const UiText*t;const UiRun*r;unsigned n,ink;unsigned short*base;
 if(label>=CG_COUNT)return;t=&companion_guide_texts[label];
 if(x<0||y<0||x+t->width>240||y+t->height>160)return;
 if(text_spans){text_spans(t,x,y,color);return;}
 r=t->runs[x&1];n=t->count[x&1];ink=(unsigned)color*257u;base=screen+y*120+(x>>1);
 while(n--){unsigned short*dst=base+r->offset;unsigned count=r->count,mask=r->mask;r++;
  if(mask==3)while(count--)*dst++=(unsigned short)ink;
  else if(mask==1)while(count--){*dst=(unsigned short)((*dst&65280)|(unsigned)color);dst++;}
  else while(count--){*dst=(unsigned short)((*dst&255)|((unsigned)color<<8));dst++;}
 }
}
void companion_guide_center(unsigned label,int y,int color){if(label<CG_COUNT)companion_guide_text(label,(240-companion_guide_texts[label].width)/2,y,color);}
/* Small fixed-width GBJ numbers keep the collection line steady while scrolling.
 * This display-only identifier is the stable storage slot plus one, not a form ID.
 * No save encoding or instance allocation is changed. */
int companion_guide_number(unsigned value,unsigned places,int x,int y,int color){
 unsigned digits[3],i;int cell=companion_guide_texts[CG_PARTY_DIGIT_0].width;
 if(value>999)value=999;if(places<1)places=1;if(places>3)places=3;
 digits[0]=value/100;digits[1]=(value/10)%10;digits[2]=value%10;
 for(i=3-places;i<3;i++){companion_guide_text(CG_PARTY_DIGIT_0+digits[i],x,y,color);x+=cell;}
 return x;
}
static void party_title(const CreatureInstance*c,int id,unsigned destination){
 unsigned i;int suffix,x;
 if(destination<CREATURE_PARTY_CAPACITY)for(i=0;i<CREATURE_ROSTER_CAPACITY;i++)if(c==&adventure_save.roster.instances[i]){
  suffix=companion_guide_texts[CG_PARTY_INSTANCE].width+3*(companion_guide_texts[CG_PARTY_DIGIT_0].width);
  x=(240-ui_texts[id].width-8-suffix)/2;text(id,x,33,GOLD);x+=ui_texts[id].width+8;
  companion_guide_text(CG_PARTY_INSTANCE,x,33,TEAL);companion_guide_number(i+1,3,x+companion_guide_texts[CG_PARTY_INSTANCE].width,33,TEAL);return;
 }
 centered(id,33,GOLD);
}
unsigned companion_guide_command_next(const CreatureInstance*c,unsigned command,int delta){
 const CreatureForm*f;unsigned i,index=0;
 if(!c||(f=creatures_form(c->form_id))==0||!f->learnset_count||f->learnset_offset+f->learnset_count>CREATURE_LEARNSET_COUNT)return command;
 for(i=0;i<f->learnset_count;i++)if(creature_learnsets[f->learnset_offset+i].ability_id==command){index=i;break;}
 for(i=0;i<f->learnset_count;i++){unsigned next;index=delta>0?(index+1==f->learnset_count?0:index+1):(index?index-1:(unsigned)f->learnset_count-1);next=creature_learnsets[f->learnset_offset+index].ability_id;if(creatures_command_learned(c->form_id,c->level,next))return next;}
 return command;
}
static unsigned command_base(unsigned command){const CreatureAbility*a=creatures_ability(command);return a?(command<=4?75u:a->cooldown_updates):0;}
unsigned companion_guide_recovery_stats(unsigned command,const EquipmentStats*s){
 unsigned base=command_base(command),reduction;
 if(!base||!s)return 0;
 reduction=EQUIPMENT_BASE_POWER_COOLDOWN-s->power_cooldown;
 return base>reduction?base-reduction:1u;
}
unsigned companion_guide_recovery(unsigned command){unsigned base=command_base(command);return base?game_power_cooldown(base):0;}
void companion_guide_axes(unsigned form,unsigned polarity,int y){
 static const int phases[5]={TX_E_WOOD,TX_E_FIRE,TX_E_EARTH,TX_E_METAL,TX_E_WATER};
 const CreatureForm*f=creatures_form(form);if(!f||f->phase>=5||polarity>1)return;
 companion_guide_text(CG_PHASE,24,y,TEAL);text(phases[f->phase],62,y,GOLD);
 companion_guide_text(CG_POLARITY,132,y,TEAL);text(polarity?TX_E_YANG:TX_E_YIN,170,y,GOLD);
}
void companion_guide_combat(unsigned command,int y){const CompanionGuideCopy*c;if(!command||command>128||!creatures_ability(command))return;c=&companion_guide_commands[command];companion_guide_center(c->combat[0],y,CREAM);companion_guide_center(c->combat[1],y+14,CREAM);}
static void number(unsigned value,int x,int y){
 static const unsigned char digits[10][5]={{7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},{5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},{7,5,7,5,7},{7,5,7,1,7}};
 unsigned values[3]={0,0,0},i,row,col,started=0;if(value>999)value=999;while(value>=100){value-=100;values[0]++;}while(value>=10){value-=10;values[1]++;}values[2]=value;
 for(i=0;i<3;i++)if(values[i]||started||i==2){for(row=0;row<5;row++)for(col=0;col<3;col++)if(digits[values[i]][row]&(4u>>col))rect(x+(int)col*2,y+(int)row*2,2,2,CREAM);x+=8;started=1;}
}
void companion_guide_draw(const CreatureInstance*c,unsigned command,unsigned destination){
 const CompanionGuideCopy*copy;unsigned action;box(8,31,224,123);
 if(!c||!creatures_form(c->form_id)||!command||command>128||!creatures_ability(command)){centered(TX_E_NO_MEMBER,87,CREAM);centered(TX_PF_BACK_CLOSE,138,TEAL);return;}
 copy=&companion_guide_commands[command];party_title(c,progression_name_id(c->form_id),destination);companion_guide_axes(c->form_id,c->polarity,49);
 if(companion_guide_page){centered(progression_command_name_id(command),65,GOLD);companion_guide_center(copy->field,81,CREAM);companion_guide_center(CG_FIELD_CONTEXT,95,TEAL);companion_guide_center(CG_FIELD_WAIT,109,TEAL);}
 else{centered(progression_command_name_id(command),65,GOLD);companion_guide_combat(command,81);companion_guide_text(CG_COMBAT_WAIT,38,109,TEAL);number(companion_guide_recovery(command),132,111);companion_guide_text(CG_FRAMES,160,109,CREAM);}
 companion_guide_center(companion_guide_page?CG_BROWSE_FIELD:CG_BROWSE_COMBAT,123,TEAL);
 if(destination<4){unsigned slot=adventure_save.roster.party[destination];int assigned=slot<CREATURE_ROSTER_CAPACITY&&c==&adventure_save.roster.instances[slot];action=(assigned?CG_ASSIGNED_0:CG_ASSIGN_0)+destination*2;}
 else action=c->selected_command<2&&c->equipped[c->selected_command]==command?CG_EQUIPPED:CG_EQUIP;
 companion_guide_center(action,138,CREAM);
}
