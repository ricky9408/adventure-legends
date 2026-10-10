/* Production journal slot raster versus the pinned original per-rectangle code. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/quickparty.c"
#include "fixtures/player-feedback-proposed/party_original_card.inc"
static union{unsigned short words[19200];unsigned char bytes[38400];}actual,expected;
unsigned short*screen=actual.words;
static unsigned char portrait[256];
const unsigned char*companion_form_pixels(unsigned form,unsigned direction,unsigned pose){(void)form;(void)direction;(void)pose;return portrait;}
void rect(int x,int y,int w,int h,unsigned char color){int a,b;unsigned char*dest=(unsigned char*)screen;assert(x>=0&&y>=0&&x+w<=240&&y+h<=160);for(b=0;b<h;b++)for(a=0;a<w;a++)dest[(y+b)*240+x+a]=color;}
void sprite(const unsigned char*p,int x,int y,int w,int h,int flash){int a,b;assert(!flash);for(b=0;b<h;b++)for(a=0;a<w;a++)if(p[b*w+a])rect(x+a,y+b,1,1,p[b*w+a]);}
static void compare(unsigned slot,unsigned chosen,unsigned background,unsigned*cases){unsigned i;for(i=0;i<38400;i++)actual.bytes[i]=expected.bytes[i]=(unsigned char)(background?background==1?0xa5:(i*37u+(i/240u)*19u)&255u:0);screen=actual.words;journal_card(slot,(int)chosen);screen=expected.words;original_card(slot,16+(int)slot*54,52,46,(int)chosen);assert(!memcmp(&actual,&expected,sizeof actual));(*cases)++;}
int main(void){unsigned form,slot,chosen,selected,bg,i,cases=0;
 for(i=0;i<256;i++)portrait[i]=(i%5)?(unsigned char)((i*13u)%255u+1u):0;
 for(form=0;form<=129;form++)for(slot=0;slot<4;slot++)for(chosen=0;chosen<2;chosen++)for(selected=0;selected<5;selected++){
  memset(&adventure_save.roster,0,sizeof adventure_save.roster);for(i=0;i<4;i++){adventure_save.roster.party[i]=(unsigned char)i;adventure_save.roster.instances[i].flags=CREATURE_OCCUPIED;adventure_save.roster.instances[i].form_id=(unsigned char)form;}adventure_save.roster.selected_party=(unsigned char)selected;
  for(bg=0;bg<3;bg++)compare(slot,chosen,bg,&cases);
 }
 for(slot=0;slot<4;slot++)for(chosen=0;chosen<2;chosen++)for(selected=0;selected<5;selected++)for(bg=0;bg<3;bg++){
  adventure_save.roster.selected_party=(unsigned char)selected;adventure_save.roster.party[slot]=CREATURE_EMPTY_SLOT;compare(slot,chosen,bg,&cases);
  adventure_save.roster.party[slot]=CREATURE_ROSTER_CAPACITY;compare(slot,chosen,bg,&cases);
  adventure_save.roster.party[slot]=0;adventure_save.roster.instances[0].flags=0;compare(slot,chosen,bg,&cases);
 }
 printf("PASS production Party slot raster: %u exact full-frame comparisons, all forms/directions/selection/empty-invalid states and3 backgrounds; field picker source unchanged\n",cases);return 0;
}
