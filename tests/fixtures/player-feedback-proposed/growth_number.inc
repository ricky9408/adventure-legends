/* Proposed only until approved: transparent6x10 doubled glyphs. */
extern unsigned short *screen;
static void growth_digit_blit(unsigned digit,int x,int y){
 unsigned row;unsigned short ink=(unsigned short)(CREAM|((unsigned)CREAM<<8));
 if((unsigned)x>234||(unsigned)y>150){int xx,yy;for(yy=0;yy<5;yy++)for(xx=0;xx<3;xx++)if(digits[digit][yy]&(4>>xx))rect(x+xx*2,y+yy*2,2,2,CREAM);return;}
 for(row=0;row<5;row++){unsigned bits=digits[digit][row],copy;unsigned short*p=screen+(y+(int)row*2)*120+(x>>1);
  if(!(x&1)){for(copy=0;copy<2;copy++,p+=120){if(bits&4)p[0]=ink;if(bits&2)p[1]=ink;if(bits&1)p[2]=ink;}}
  else{unsigned short mask[4];unsigned col;mask[0]=(bits&4)?65280:0;mask[1]=(unsigned short)(((bits&4)?255:0)|((bits&2)?65280:0));mask[2]=(unsigned short)(((bits&2)?255:0)|((bits&1)?65280:0));mask[3]=(bits&1)?255:0;
   for(copy=0;copy<2;copy++,p+=120)for(col=0;col<4;col++)if(mask[col])p[col]=(unsigned short)((p[col]&~mask[col])|(ink&mask[col]));}
 }
}
static void number(unsigned n,int x,int y){unsigned value[3]={0,0,0},i;int started=0;
 /* Real level/bond callers are <=100. Rare host probes retain the original
  * low-three-digit behavior; valid menu values take no division path. */
 if(n>=1000)n%=1000;while(n>=100){n-=100;value[0]++;}while(n>=10){n-=10;value[1]++;}value[2]=n;
 for(i=0;i<3;i++)if(value[i]||started||i==2){growth_digit_blit(value[i],x,y);x+=8;started=1;}
}
