/* Exhaustive retained Return-form policy under content8. New forms105..120
 * have their independent exhaustive mask proof in test_horizons_history.py. */
#include "creatures.h"
#include <stdio.h>
#include <string.h>
static unsigned expected_mask(unsigned form){
 switch(form){
 case 2:case 3:case 26:case 27:case 29:case 30:return 1025;
 case 5:case 6:return 1026;case 8:case 9:return 1028;
 case 11:case 12:return 1032;case 14:case 15:return 1040;
 case 16:case 101:case 102:case 103:case 104:return 1024;
 case 17:case 18:return 3072;
 case 20:case 21:return 1056;case 23:case 24:return 1088;
 default:return creatures_trial_allowed_mask(form,6);
 }
}
static unsigned required(unsigned form){
 switch(form){
 case 3:case 27:case 30:return 1025;case 6:return 1026;
 case 9:return 1028;case 12:return 1032;case 15:return 1040;
 case 17:case 102:case 104:return 1024;case 18:return 3072;
 case 21:return 1056;case 24:return 1088;
 default:return form>=49&&form<=72&&(form-49)%3?1u<<((form-49)%3-1):0;
 }
}
static unsigned prerequisite(unsigned family){
 static const unsigned old[11]={0,1,2,4,8,16,0,32,64,1,1};
 return family<=10?old[family]:0;
}
int main(void){
 unsigned form,mask,count=0,checks=0;CreatureInstance c;
 if(!creatures_catalog_validate()||CREATURE_CONTENT_REVISION!=8||CREATURE_TRIAL_MASK!=1023)return 1;
 for(form=1;form<=104;++form){
  const CreatureForm*f=creatures_form(form);unsigned allowed,req,prior;
  if(!f)continue;
  ++count;allowed=expected_mask(form);req=required(form);prior=prerequisite(f->family);
  if(creatures_trial_allowed_mask(form,7)!=allowed){fprintf(stderr,"mask policy form%u\n",form);return 2;}
  memset(&c,0,sizeof c);c.form_id=(CreatureU8)form;c.flags=CREATURE_OCCUPIED;c.level=50;c.bond=100;c.xp=470596;c.instance_id=1;c.polarity=f->polarity;c.equipped[0]=f->signature_ability;
  for(mask=0;mask<65536;++mask){
   unsigned expected=!(mask&~allowed)&&(mask&req)==req;
   if((mask&1024u)&&prior&&(mask&prior)!=prior)expected=0;
   if(f->family==6&&(mask&2048u)&&!(mask&1024u))expected=0;
   if((f->family==11||f->family==12)&&(mask&2u)&&!(mask&1u))expected=0;
   c.trial_flags=(CreatureU16)mask;
   if(creatures_instance_validate(&c)!=(int)expected){fprintf(stderr,"form%u mask%u expected%u\n",form,mask,expected);return 3;}
   ++checks;
  }
 }
 if(count!=104||checks!=6815744)return 4;
 puts("Retained r7 forms under current8:6,815,744 exact per-stage mask cases passed across104 forms; old scalar mask unchanged");return 0;
}
