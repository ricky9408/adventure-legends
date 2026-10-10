#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "ending_credits.c"
int keys,pressed,arrival_input_mask;
unsigned short *screen;
void rect(int a,int b,int c,int d,unsigned char e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void text_spans(const UiText*a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
static unsigned short actual[19264],expected[19264];
int main(void){unsigned checks=0;for(unsigned id=0;id<EC_COUNT;id++)for(int y=-20;y<=160;y++)for(int color=0;color<256;color+=127){
 for(unsigned i=0;i<19264;i++)actual[i]=expected[i]=(unsigned short)(i*73+0x34ab);screen=actual+32;
 const UiText*t=&ending_credits_texts[id];int x=(240-t->width)/2;
 for(unsigned i=0;i<t->count[x&1];i++){UiRun r=t->runs[x&1][i];int yy=y+r.offset/120;if(yy<TOP||yy>=BOTTOM)continue;
  for(unsigned j=0;j<r.count;j++)for(unsigned bit=0;bit<2;bit++)if(r.mask&(1u<<bit)){
   int xx=(x/2+(r.offset%120)+j)*2+bit;assert(xx>=0&&xx<240);((unsigned char*)(expected+32))[yy*240+xx]=(unsigned char)color;
  }
 }
 clipped(id,y,color);assert(!memcmp(actual,expected,sizeof actual));checks++;
 }printf("PASS %u independent clipped full-frame/canary comparisons\n",checks);return 0;}
