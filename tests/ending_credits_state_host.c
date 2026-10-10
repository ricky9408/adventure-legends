#include <assert.h>
#include <stdio.h>
#include "ending_credits.c"
int keys,pressed,arrival_input_mask;
unsigned short *screen;
void rect(int a,int b,int c,int d,unsigned char e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void text_spans(const UiText*a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
static unsigned checks;
static void step(unsigned held,unsigned edge){keys=(int)held;pressed=(int)edge;assert(!ending_credits_update());checks++;}
int main(void){
 for(unsigned held=1;held<1024;held++)if(held&BUTTONS){
  ending_credits_begin();for(unsigned i=0;i<200;i++)step(held,i?0:held);
  assert(!ending_credits_armed&&!ending_credits_phase&&!ending_credits_scroll);
  step(0,0);assert(ending_credits_armed);step(1,1);assert(ending_credits_phase==1&&!ending_credits_armed);
  for(unsigned i=0;i<20;i++)step(1,0);assert(!ending_credits_scroll);
 }
 ending_credits_begin();step(0,0);
 for(unsigned i=0;i<179;i++){step(0,0);assert(!ending_credits_phase);}
 step(0,0);assert(ending_credits_phase==1);step(0,0);
 unsigned full_steps=0;while(ending_credits_phase==1){step(0,0);assert(++full_steps<4000);}
 assert(ending_credits_phase==2&&!ending_credits_armed);
 unsigned end=ending_credits_scroll;step(0,0);unsigned revision=ending_credits_revision;
 for(unsigned i=0;i<1000;i++)step(0,0);
 assert(ending_credits_scroll==end&&ending_credits_revision==revision);
 step(1,1);assert(ending_credits_phase==1&&!ending_credits_scroll&&!ending_credits_armed);
 for(unsigned phase=0;phase<3;phase++)for(unsigned button=2;button<=8;button+=6){
  ending_credits_begin();ending_credits_phase=phase;step(button,button);assert(!ending_credits_armed);
  step(0,0);keys=(int)button;pressed=(int)button;arrival_input_mask=0;
  assert(ending_credits_update()==1);assert(!pressed&&arrival_input_mask==(int)button);checks++;
 }
 printf("PASS %u state/input updates, all held-button combinations, automatic/full roll, stable end, replay and B/Start exits; full scroll %u updates\n",checks,full_steps);
 return 0;
}
