/* Exact pre-optimization production numeric function, captured after baseline restoration. */
static void legacy_growth_number(unsigned n,int x,int y){unsigned divisor=100;int started=0;for(;divisor;divisor/=10){unsigned d=n/divisor%10;if(d||started||divisor==1){int xx,yy;for(yy=0;yy<5;yy++)for(xx=0;xx<3;xx++)if(digits[d][yy]&(4>>xx))rect(x+xx*2,y+yy*2,2,2,CREAM);x+=8;started=1;}}}
