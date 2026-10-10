/* Independent exact-decimal and54px-column pixel oracle. No game RAM writes. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/gear_menu.c"
static union {unsigned short words[19200];unsigned char pixels[160][240];} actual,expected;
static unsigned char canvas[160][240];
#define got actual.pixels
#define want expected.pixels
unsigned short *screen=actual.words;
void rect(int x,int y,int w,int h,unsigned char color){int a,b;for(b=0;b<h;b++)for(a=0;a<w;a++){assert(x+a>=0&&x+a<240&&y+b>=0&&y+b<160);got[y+b][x+a]=color;}}
/* Same public UiRun semantics as the real paired-pixel renderer. */
void text_spans(const UiText*t,int x,int y,int color){const UiRun*r=t->runs[x&1];unsigned n=t->count[x&1];while(n--){unsigned a;for(a=0;a<r->count;a++){unsigned off=(unsigned)y*240+(unsigned)(x&~1)+(r->offset+a)*2;assert(off+1<sizeof got);if(r->mask&1)((unsigned char*)got)[off]=(unsigned char)color;if(r->mask&2)((unsigned char*)got)[off+1]=(unsigned char)color;}r++;}}
static const unsigned char glyphs[10][7]={{6,9,9,9,9,9,6},{2,6,2,2,2,2,7},{6,9,1,2,4,8,15},{14,1,1,6,1,1,14},{2,6,10,10,15,2,2},{15,8,8,14,1,1,14},{6,8,8,14,9,9,6},{15,1,1,2,2,4,4},{6,9,9,6,9,9,6},{6,9,9,7,1,1,6}};
static void oracle_decimal(unsigned n,char*s){char tail[8];unsigned r=n%16;snprintf(s,16,"%u",n/16);if(r){/* 1/16=.0625; a fully independent integer-to-string oracle. */snprintf(tail,sizeof tail,"%04u",r*625);while(tail[strlen(tail)-1]=='0')tail[strlen(tail)-1]=0;strcat(s,".");strcat(s,tail);}}
static unsigned oracle_width(const char*s){unsigned width=0;for(;*s;s++)width+=*s=='.'?3u:5u;return width-1;}
static void oracle_paint(const char*s,int x,int y,unsigned char color){unsigned a,b;for(;*s;s++){if(*s=='.'){want[y+5][x]=want[y+5][x+1]=want[y+6][x]=want[y+6][x+1]=color;x+=3;}else{for(b=0;b<7;b++)for(a=0;a<4;a++)if(glyphs[(unsigned)(*s-'0')][b]&(8u>>a))want[y+b][x+a]=color;x+=5;}}}
int main(int argc,char**argv){unsigned n,parity,bg,before,after,pairs=0;char s[16],t[16];
 /* Every Q4 value in the supported96..192 range, including quarter examples. */
 for(bg=0;bg<2;++bg)for(parity=0;parity<2;++parity)for(n=96;n<=192;++n){memset(got,bg?0x5a:0,sizeof got);memset(want,bg?0x5a:0,sizeof want);oracle_decimal(n,s);heart_number(n,10+(int)parity,10,4);oracle_paint(s,10+(int)parity,10,4);assert(heart_width(n)==oracle_width(s));assert(!memcmp(got,want,sizeof got));}
 assert(gear_preview_texts[GP_HEART].width<=54);
 /* All625 quarter-heart comparisons at both pixel parities, two backgrounds. */
 for(bg=0;bg<2;++bg)for(parity=0;parity<2;++parity)for(before=96;before<=192;before+=4)for(after=96;after<=192;after+=4){unsigned width;int x=120+(int)parity,col=after>before?GOLD:after<before?PAL_HEART:CREAM;memset(got,bg?0x5a:0,sizeof got);label(GP_HEART,x+(54-gear_preview_texts[GP_HEART].width)/2,80,CREAM);memcpy(want,got,sizeof want);oracle_decimal(before,s);oracle_decimal(after,t);width=oracle_width(s);assert(width<=22&&oracle_width(t)<=22);oracle_paint(s,x+23-(int)width,93,CREAM);oracle_paint(t,x+32,93,(unsigned char)col);{unsigned k;for(k=0;k<7;k++)want[96][x+24+k]=TEAL;for(k=0;k<3;k++)want[95+k][x+29]=TEAL;for(k=0;k<5;k++)want[94+k][x+28]=TEAL;}stat(before,after,GP_HEART,x,1);assert(!memcmp(got,want,sizeof got));pairs++;}
 /* A240x160 native-size canvas for visual inspection. Each row uses four
  * real54px columns, real generated Japanese labels, and actual color roles. */
 if(argc>1){static const unsigned cases[3][4][2]={{{96,100},{100,104},{104,108},{108,96}},{{160,164},{164,168},{172,192},{192,192}},{{188,192},{192,188},{180,188},{188,180}}};unsigned row,column,y;FILE*f;memset(got,0,sizeof got);
  for(row=0;row<3;++row){memset(got,0,sizeof got);for(column=0;column<4;++column)stat(cases[row][column][0],cases[row][column][1],GP_HEART,12+(int)column*54,1);for(y=80;y<100;++y)memcpy(canvas[22+row*42+y-80],got[y],240);}
  f=fopen(argv[1],"wb");assert(f);assert(fwrite(canvas,1,sizeof canvas,f)==sizeof canvas);fclose(f);
 }
 printf("PASS exact97 Q4 values x4 canvas conditions; %u quarter comparisons;54px columns and adjacent pixels preserved\n",pairs);return 0;}
