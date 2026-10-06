/* Pixel-equivalence oracle for cold-menu decimal rendering; no GBA RAM writes. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../src/gear_menu.c"
static union {unsigned short words[19200];unsigned char pixels[160][240];} actual,expected;
#define got actual.pixels
#define want expected.pixels
unsigned short *screen=actual.words;
void rect(int x,int y,int w,int h,unsigned char c){int a,b;for(b=0;b<h;b++)for(a=0;a<w;a++){assert(x+a>=0&&x+a<240&&y+b>=0&&y+b<160);got[y+b][x+a]=c;}}
int main(void){unsigned n,parity,background;static const unsigned char glyphs[10][5]={{7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},{5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},{7,5,7,5,7},{7,5,7,1,7}};
 for(background=0;background<2;background++)for(parity=0;parity<2;parity++)for(n=0;n<1000;n++){char text[8];unsigned d,x,y;memset(got,background?0x5a:0,sizeof got);memset(want,background?0x5a:0,sizeof want);number(n,10+(int)parity,10,4);snprintf(text,sizeof text,"%u",n);
  for(d=0;text[d];d++)for(y=0;y<5;y++)for(x=0;x<3;x++)if(glyphs[(unsigned)(text[d]-'0')][y]&(4u>>x))want[10+y][10+parity+d*4+x]=4;
  assert(!memcmp(got,want,sizeof got));
 }
 for(n=288;n<=352;n++)assert((n*100+160)/320==((n*5+8)>>4));
 puts("PASS all1000 decimal masks at both pixel parities and65 speed-index values, exact pixels/rounding");return 0;
}
