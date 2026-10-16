/* Synthetic pixel/provenance oracle only. No GBA timing or earned play claim.
 * Actual baseline and prototype functions are linked from separate extracted
 * translation units. All drawing/reach/save/hardware behavior is explicit. */
#include "play_strip_ranges_host.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

StripState candidate,reference;
static unsigned checks,frames,handoffs,rejections,reuses,invalid_ranges,arming_cases;
static u32 rng=0x5fa61c39u,world_serial=1;
static u16 before_frame[FRAME_WORDS],before_strip[STRIP_WORDS];
#define CHECK(condition) do {checks++;if(!(condition)){ \
 fprintf(stderr,"FAIL line %d: %s (frames=%u handoffs=%u seed=%08x)\n", \
 __LINE__,#condition,frames,handoffs,rng);exit(1);}}while(0)

static u32 random_word(void) {
 rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;
}
static u32 mixed(u32 n) {
 n^=n>>16;n*=0x7feb352du;n^=n>>15;n*=0x846ca68bu;return n^(n>>16);
}
static void draw_pattern(StripState *s,int top,int bottom,int left,int right,u32 salt) {
 int x,y;
 /* Nonopaque, asymmetric odd-byte boundaries exercise neighbor preservation.
  * Top/bottom/left/right border pixels are always written. */
 unsigned char *bytes=(unsigned char *)s->screen;
 for(y=top;y<bottom;y++)for(x=left;x<right;x++)
  if(y==top||y==bottom-1||x==left||x==right-1||((x+3*y)&3)!=0)
   bytes[y*240+x]=(unsigned char)mixed(salt+s->overlay_serial*97u+(u32)(x+y*240));
}
void oracle_draw_notices(StripState *s,int cached) {
 unsigned i,hint=0;(void)cached;
 for(i=0;i<6;i++)hint|=s->hints[i];
 if(hint)draw_pattern(s,138,157,31,212,0x100000u+hint);
 else if(s->toast_ticks)draw_pattern(s,143,160,43,196,0x200000u);
}
void oracle_draw_reward(StripState *s) {
 /* Deliberately fill to y160: this is a conservative superset of current
  * reward pixels and catches any incorrect assumption about old toast rows. */
 if(s->reward)draw_pattern(s,122,160,5,121,0x300000u);
}
static void draw_boss(StripState *s) {
 if(s->boss)draw_pattern(s,153,158,57,183,0x400000u);
}
void oracle_copy_previous_bitmap(StripState *s) {
 s->screen=s->bitmap[s->page];
 memcpy(s->screen,s->bitmap[s->page^1],sizeof(s->bitmap[0]));
 s->cache_valid[s->page]=0;
}
void oracle_save_frame(StripState *s) {s->save_calls++;}

static void canaries(void) {
 unsigned i;
 for(i=0;i<8;i++) {
  CHECK(candidate.guard_pre[i]==0x8a8a0000u+i);
  CHECK(candidate.guard_post[i]==0x5b5b0000u+i);
  CHECK(reference.guard_pre[i]==0x8a8a0000u+i);
  CHECK(reference.guard_post[i]==0x5b5b0000u+i);
 }
}
static void compare(void) {
 int p;unsigned n;
 for(p=0;p<2;p++) {
  CHECK(memcmp(candidate.bitmap[p],reference.bitmap[p],sizeof(candidate.bitmap[p]))==0);
  CHECK(candidate.cache_valid[p]==reference.cache_valid[p]);
  CHECK(memcmp(candidate.cache_fields[p],reference.cache_fields[p],sizeof(candidate.cache_fields[p]))==0);
  CHECK(candidate.play_strip_valid[p]==reference.play_strip_valid[p]);
  CHECK(candidate.play_strip_clean[p]==reference.play_strip_clean[p]);
  CHECK(candidate.cached_armor[p]==reference.cached_armor[p]);
  CHECK(memcmp(candidate.modal_world_row[p],reference.modal_world_row[p],sizeof(candidate.modal_world_row[p]))==0);
  if(candidate.play_strip_valid[p]) {
   CHECK(candidate.play_strip_top[p]==122||candidate.play_strip_top[p]==138);
   for(n=(unsigned)(candidate.play_strip_top[p]-122)*120;n<STRIP_WORDS;n++)
    CHECK(candidate.play_world_strip[p][n]==reference.play_world_strip[p][n]);
  }
 }
 CHECK(candidate.play_strip_reuses==reference.play_strip_reuses);
 CHECK(candidate.scene_present_phase==reference.scene_present_phase);
 CHECK(candidate.save_ordinary_defer==reference.save_ordinary_defer);
 CHECK(candidate.save_calls==reference.save_calls);
 canaries();
}
static void reset(void) {
 int p;unsigned n;
 memset(&candidate,0,sizeof(candidate));memset(&reference,0,sizeof(reference));
 candidate.game_state=reference.game_state=PLAY;
 candidate.room=reference.room=63;
 for(n=0;n<8;n++) {
  candidate.guard_pre[n]=reference.guard_pre[n]=0x8a8a0000u+n;
  candidate.guard_post[n]=reference.guard_post[n]=0x5b5b0000u+n;
 }
 for(p=0;p<2;p++)for(n=0;n<STRIP_WORDS;n++)
  candidate.play_world_strip[p][n]=reference.play_world_strip[p][n]=(u16)random_word();
}
static void select_page(int p) {
 candidate.page=reference.page=p;
 candidate.screen=candidate.bitmap[p];reference.screen=reference.bitmap[p];
}
/* mask: toast, six distinct hint providers, boss, reward. */
static void overlays(unsigned mask) {
 unsigned i;
 candidate.toast_ticks=reference.toast_ticks=(mask&1u)!=0;
 for(i=0;i<6;i++)candidate.hints[i]=reference.hints[i]=(mask>>(i+1))&1u;
 candidate.boss=reference.boss=(mask>>7)&1u;
 candidate.reward=reference.reward=(mask>>8)&1u;
 candidate.overlay_serial=reference.overlay_serial=random_word();
}
static void make_key(u32 key[CACHE_FIELDS]) {
 unsigned i;
 for(i=0;i<CACHE_FIELDS;i++)key[i]=mixed(world_serial*197u+i);
 key[0]=(u32)candidate.room;key[1]=PLAY;
 key[7]=(u32)candidate.toast_ticks;key[8]=candidate.overlay_serial;
 for(i=0;i<6;i++)key[27+i*2]=candidate.hints[i];
 key[40]=candidate.overlay_serial;key[42]=candidate.reward;
}
static void world(StripState *s) {
 unsigned i;
 for(i=0;i<FRAME_WORDS;i++)s->screen[i]=(u16)mixed(world_serial*65537u+i);
}
static void full_frame(const u32 key[CACHE_FIELDS]) {
 int p=candidate.page;
 world(&candidate);world(&reference);
 memcpy(before_strip,candidate.play_world_strip[p],sizeof(before_strip));
 candidate_capture();reference_capture();
 if(candidate.play_strip_valid[p]&&candidate.play_strip_top[p]==138)
  CHECK(memcmp(before_strip,candidate.play_world_strip[p],16*120*sizeof(u16))==0);
 oracle_draw_notices(&candidate,0);oracle_draw_notices(&reference,0);
 oracle_draw_reward(&candidate);oracle_draw_reward(&reference);
 draw_boss(&candidate);draw_boss(&reference);
 candidate.cache_valid[p]=reference.cache_valid[p]=1;
 memcpy(candidate.cache_fields[p],key,sizeof(candidate.cache_fields[p]));
 memcpy(reference.cache_fields[p],key,sizeof(reference.cache_fields[p]));
 frames++;compare();
}
static void step(unsigned mask,int p,int change_world) {
 u32 key[CACHE_FIELDS];int a,b,old_top,old_raw;unsigned n;
 if(change_world)world_serial++;
 select_page(p);overlays(mask);make_key(key);
 memcpy(before_frame,candidate.screen,sizeof(before_frame));
 memcpy(before_strip,candidate.play_world_strip[p],sizeof(before_strip));
 old_raw=candidate.play_strip_valid[p];old_top=candidate.play_strip_top[p];
 a=candidate_reuse(key);b=reference_reuse(key);CHECK(a==b);
 if(!a) {
  rejections++;
  CHECK(memcmp(before_frame,candidate.screen,sizeof(before_frame))==0);
  CHECK(memcmp(before_strip,candidate.play_world_strip[p],sizeof(before_strip))==0);
  full_frame(key);return;
 }
 reuses++;
 /* Capture/restore/overlay must leave all rows above its union untouched.
  * For a widened old strip, only the new prefix may change the raw buffer. */
 n=(unsigned)((candidate.reward||(old_raw&&old_top==122))?122:138)*120;
 CHECK(memcmp(before_frame,candidate.screen,n*sizeof(u16))==0);
 if(old_raw&&old_top==138&&candidate.reward) {
  CHECK(candidate.play_strip_top[p]==122);
  CHECK(memcmp(candidate.play_world_strip[p],before_frame+122*120,16*120*sizeof(u16))==0);
  CHECK(memcmp(candidate.play_world_strip[p]+16*120,before_strip+16*120,22*120*sizeof(u16))==0);
 }
 draw_boss(&candidate);draw_boss(&reference);
 memcpy(candidate.cache_fields[p],key,sizeof(candidate.cache_fields[p]));
 memcpy(reference.cache_fields[p],key,sizeof(reference.cache_fields[p]));
 frames++;compare();
}
static void explicit_transitions(void) {
 unsigned first,next;int p;
 const unsigned modes[]={0,1,2,4,8,16,32,64,128,256,257,258,384,511};
 /* Every clean/notice/boss/reward predecessor to every successor, each page.
  * Narrow->reward->narrow->clear explicitly exercises prefix provenance. */
 for(p=0;p<2;p++)for(first=0;first<sizeof(modes)/sizeof(modes[0]);first++)
  for(next=0;next<sizeof(modes)/sizeof(modes[0]);next++) {
   u32 key[CACHE_FIELDS];reset();select_page(p);overlays(modes[first]);make_key(key);
   full_frame(key);step(modes[next],p,0);step(256,p,0);step(2,p,0);step(0,p,0);
  }
}
/* Logical input ownership starts on L press, before a panel is visible.
 * It must not invalidate underlay provenance or suppress normal strip redraw. */
static void selector_arming(void) {
 unsigned mode;int p;
 const unsigned modes[]={0,1,2,4,8,16,32,64,128,256,257,258,384,511};
 for(p=0;p<2;p++)for(mode=0;mode<sizeof(modes)/sizeof(modes[0]);mode++) {
  u32 key[CACHE_FIELDS];reset();select_page(p);overlays(modes[mode]);make_key(key);
  candidate.quickparty_open=reference.quickparty_open=1;
  CHECK(!candidate.quickparty_visible&&!reference.quickparty_visible);
  full_frame(key);CHECK(candidate.play_strip_valid[p]||candidate.play_strip_clean[p]);
  step(256,p,0);step(2,p,0);step(0,p,0);arming_cases++;
  candidate.quickparty_visible=reference.quickparty_visible=1;
  memcpy(before_frame,candidate.screen,sizeof(before_frame));
  memcpy(before_strip,candidate.play_world_strip[p],sizeof(before_strip));
  CHECK(!candidate_reuse(key));CHECK(!reference_reuse(key));
  CHECK(memcmp(before_frame,candidate.screen,sizeof(before_frame))==0);
  candidate_capture();reference_capture();
  CHECK(!candidate.play_strip_valid[p]&&!candidate.play_strip_clean[p]);
  CHECK(memcmp(before_strip,candidate.play_world_strip[p],sizeof(before_strip))==0);
  compare();
  candidate.quickparty_open=reference.quickparty_open=0;
  candidate.quickparty_visible=reference.quickparty_visible=0;
  overlays(modes[mode]);make_key(key);full_frame(key);step(256,p,0);arming_cases++;
 }
}
static int mutable_key(unsigned i,int area) {
 return i==7||i==8||i==27||i==29||i==31||i==33||i==35||i==37||i==40||i==42||
        (i==19&&area>=4&&area<14);
}
static void key_guards(void) {
 unsigned i,area;int p;
 for(area=0;area<2;area++)for(p=0;p<2;p++)for(i=0;i<CACHE_FIELDS;i++) {
  u32 key[CACHE_FIELDS];int a,b;reset();select_page(p);
  candidate.room=reference.room=area?4:63;
  overlays(2);make_key(key);full_frame(key);key[i]^=0x10000u;
  memcpy(before_frame,candidate.screen,sizeof(before_frame));
  a=candidate_reuse(key);b=reference_reuse(key);CHECK(a==b);
  CHECK(a==mutable_key(i,candidate.room));
  if(!a) {
   rejections++;CHECK(memcmp(before_frame,candidate.screen,sizeof(before_frame))==0);
  } else reuses++;
  compare();
 }
 /* Independent fail-closed entry guards; no capture or pixel writes. */
 for(p=0;p<2;p++)for(i=0;i<7;i++) {
  u32 key[CACHE_FIELDS];reset();select_page(p);overlays(2);make_key(key);full_frame(key);
  switch(i) {
   case 0:candidate.play_strip_disabled=reference.play_strip_disabled=1;break;
   case 1:candidate.game_state=reference.game_state=2;break;
   case 2:candidate.quickparty_open=reference.quickparty_open=1;
          candidate.quickparty_visible=reference.quickparty_visible=1;break;
   case 3:candidate.cache_valid[p]=reference.cache_valid[p]=0;break;
   case 4:candidate.play_strip_valid[p]=reference.play_strip_valid[p]=0;
          candidate.play_strip_clean[p]=reference.play_strip_clean[p]=0;break;
   case 5:candidate.cache_fields[p][1]=reference.cache_fields[p][1]=2;break;
   default:candidate.play_strip_valid[p]=reference.play_strip_valid[p]=0;
           candidate.play_strip_clean[p]=reference.play_strip_clean[p]=1;
           candidate.boss=reference.boss=1;break;
  }
  memcpy(before_frame,candidate.screen,sizeof(before_frame));
  CHECK(!candidate_reuse(key));CHECK(!reference_reuse(key));rejections++;
  CHECK(memcmp(before_frame,candidate.screen,sizeof(before_frame))==0);compare();
 }
}
static void handoff(unsigned mask,int destination,unsigned save_case) {
 u32 key[CACHE_FIELDS];int source=destination^1;unsigned i;int top;
 reset();select_page(source);overlays(mask);make_key(key);full_frame(key);
 for(i=0;i<112;i++)candidate.modal_world_row[source][i]=reference.modal_world_row[source][i]=(u16)random_word();
 candidate.cached_armor[source]=reference.cached_armor[source]=73;
 select_page(destination);
 for(i=0;i<FRAME_WORDS;i++)candidate.screen[i]=reference.screen[i]=(u16)random_word();
 memcpy(before_strip,candidate.play_world_strip[destination],sizeof(before_strip));
 candidate.scene_present_phase=reference.scene_present_phase=3;
 candidate.save_ordinary_defer=reference.save_ordinary_defer=4;
 candidate.save_requested=reference.save_requested=(save_case>>0)&1u;
 candidate.save_feedback_ordinary=reference.save_feedback_ordinary=(save_case>>1)&1u;
 candidate.save_feedback_background=reference.save_feedback_background=(save_case>>2)&1u;
 candidate_finish();reference_finish();handoffs++;compare();
 if(candidate.play_strip_valid[destination]) {
  top=candidate.play_strip_top[destination];
  CHECK(top==candidate.play_strip_top[source]);
  CHECK(memcmp(candidate.play_world_strip[destination]+(top-122)*120,
               candidate.play_world_strip[source]+(top-122)*120,(160-top)*120*sizeof(u16))==0);
  CHECK(memcmp(candidate.play_world_strip[destination],before_strip,(top-122)*120*sizeof(u16))==0);
 }
 step(256,destination,0);step(1,destination,0);step(0,destination,0);
}
static void scene_handoffs(void) {
 unsigned mode,save_case;int p;
 const unsigned modes[]={0,1,2,128,256,258,511};
 for(p=0;p<2;p++)for(mode=0;mode<sizeof(modes)/sizeof(modes[0]);mode++)
  for(save_case=0;save_case<8;save_case++)handoff(modes[mode],p,save_case);
}
static void randomized(void) {
 unsigned i;reset();
 for(i=0;i<16000;i++) {
  unsigned r=random_word(),mask=(r>>2)&511u;
  if((i%31)==0)mask=0;
  step(mask,(int)(r&1u),(r%53u)==0);
 }
}
static void invalid_range_guards(void) {
 unsigned i;int p;
 const int invalid[]={0,121,123,137,139,160,-1,(-2147483647-1),2147483647};
 for(p=0;p<2;p++)for(i=0;i<sizeof(invalid)/sizeof(invalid[0]);i++) {
  u32 key[CACHE_FIELDS];int source=p^1;
  reset();select_page(p);overlays(2);make_key(key);full_frame(key);
  candidate.play_strip_top[p]=invalid[i];
  memcpy(before_frame,candidate.screen,sizeof(before_frame));
  memcpy(before_strip,candidate.play_world_strip[p],sizeof(before_strip));
  CHECK(!candidate_reuse(key));invalid_ranges++;
  CHECK(memcmp(before_frame,candidate.screen,sizeof(before_frame))==0);
  CHECK(memcmp(before_strip,candidate.play_world_strip[p],sizeof(before_strip))==0);
  /* Unlike the historical full-strip reference, partial metadata can be
   * malformed. Its new guard must fail closed before forming an offset. */
  reset();select_page(source);overlays(2);make_key(key);full_frame(key);
  candidate.play_strip_top[source]=invalid[i];select_page(p);
  memcpy(before_strip,candidate.play_world_strip[p],sizeof(before_strip));
  candidate.scene_present_phase=3;candidate_finish();invalid_ranges++;
  CHECK(memcmp(candidate.bitmap[p],candidate.bitmap[source],sizeof(candidate.bitmap[p]))==0);
  CHECK(!candidate.play_strip_valid[p]&&!candidate.play_strip_clean[p]);
  CHECK(memcmp(before_strip,candidate.play_world_strip[p],sizeof(before_strip))==0);
  CHECK(!candidate.scene_present_phase);canaries();
 }
}
int main(void) {
 explicit_transitions();selector_arming();key_guards();scene_handoffs();randomized();invalid_range_guards();
 printf("%u full-frame comparisons; %u scene handoffs; %u accepted reuses; "
        "%u refused reuses; %u invalid-range checks; %u arming/resume cases; %u assertions passed\n",
        frames,handoffs,reuses,rejections,invalid_ranges,arming_cases,checks);
 return 0;
}
