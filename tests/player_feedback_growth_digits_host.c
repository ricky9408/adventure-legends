#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>
#include "../src/progression.c"
#include "fixtures/player-feedback-proposed/original_growth_number.inc"
#ifndef TEST_APPLIED
#define number proposed_number
#define growth_digit_blit proposed_growth_digit_blit
#include "fixtures/player-feedback-proposed/growth_number.inc"
#undef growth_digit_blit
#undef number
#define candidate_number proposed_number
#else
#define candidate_number number
#endif
static union{unsigned short words[19200];unsigned char pixels[38400];}actual;
static unsigned char expected[38400];unsigned short*screen=actual.words;
void rect(int x,int y,int w,int h,unsigned char color){int xx,yy;for(yy=0;yy<h;yy++)for(xx=0;xx<w;xx++)if((unsigned)(x+xx)<240&&(unsigned)(y+yy)<160)actual.pixels[(y+yy)*240+x+xx]=color;}
static void compare(unsigned n,int x,int y,unsigned char background){memset(actual.pixels,background,sizeof actual.pixels);legacy_growth_number(n,x,y);memcpy(expected,actual.pixels,sizeof expected);memset(actual.pixels,background,sizeof actual.pixels);candidate_number(n,x,y);assert(!memcmp(expected,actual.pixels,sizeof expected));}
int main(void){unsigned n,p,b,cases=0;static const unsigned extras[]={1000,1001,12345,UINT_MAX};static const int clips[][2]={{-3,5},{232,5},{235,149},{10,154},{-1,-2}};for(n=0;n<1000;n++)for(p=0;p<2;p++)for(b=0;b<2;b++){compare(n,100+(int)p,70,b?0x5a:0);cases++;}for(n=0;n<4;n++){compare(extras[n],101,71,0x6b);cases++;}for(n=0;n<5;n++){compare(123,clips[n][0],clips[n][1],0x5a);cases++;}printf("PASS Growth glyph equivalence: %u full-frame pixel comparisons, parity/background/clipping/out-of-range semantics\n",cases);return 0;}
