#include "recruit_notice.h"
#include "progression.h"
#include "assets.h"
extern void rect(int,int,int,int,unsigned char);

static unsigned story_bit(const CreatureInstance*c){
 unsigned legacy;
 if(!c||!(c->flags&CREATURE_OCCUPIED)||!(c->flags&CREATURE_STORY_LOCKED))return 0;
 legacy=creatures_legacy_spirit(c->form_id);
 return legacy==2?1u:legacy==3?2u:0u;
}
int recruit_notice_pending(const CreatureInstance*c){
 unsigned bit=story_bit(c);
 return bit&&!(adventure_save.economy.reserved[1]&bit);
}
int recruit_notice_acknowledge(const CreatureInstance*c){
 unsigned bit=story_bit(c);
 /* A live transaction owns its immutable snapshot; retry inspection later. */
 if(!bit||(adventure_save.economy.reserved[1]&bit)||save5_preflight_active())return 0;
 adventure_save.economy.reserved[1]|=(unsigned char)bit;
 return 1;
}
int recruit_notice_world(unsigned form){
 return form&&form<=CREATURE_FORM_CAPACITY&&
   !(adventure_save.roster.obtained[(form-1u)>>3]&(1u<<((form-1u)&7u)));
}
void recruit_notice_badge(int x,int y){
 /* Compact stable NEW tag; this is text, never an animated attention flash.
  * It occupies the card's unused top-left corner, above its direction glyph. */
 static const unsigned char glyphs[3][5]={{5,7,7,7,5},{7,4,6,4,7},{5,5,7,7,5}};
 unsigned letter,row,column;
 rect(x,y,13,7,PAL_INK);
 for(letter=0;letter<3;letter++)for(row=0;row<5;row++)
  for(column=0;column<3;column++)if(glyphs[letter][row]&(4u>>column))
   rect(x+1+(int)letter*4+(int)column,y+1+(int)row,1,1,PAL_GOLD3);
}
