/* Synthetic actual-C short-L/long-picker regression. Real roster, selection
 * signatures and notice policies; counted engine save/reseat/revocation hooks.
 * This does not prove controller acquisition, rendered pixels or GBA timing. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "progression.h"
static void counted_selection_changed(void);
static int counted_instance_validate(const CreatureInstance *c);
#define progression_selection_changed counted_selection_changed
#define creatures_instance_validate counted_instance_validate
#include "quickparty.c"
#undef progression_selection_changed
#undef creatures_instance_validate

volatile int spirit,game_state,room;
int journal_tab,gfx_companion_frame;
static unsigned saves,ordinary_saves,changes,reseats,sounds,journals;
static unsigned revoked[11],checks,updates,validations;
static unsigned before_progression,before_picker;
static int physical_previous,filtered_held,filtered_pressed;
static unsigned short pixels[240*160/2];
unsigned short *screen=pixels;
#define CHECK(condition) do{checks++;assert(condition);}while(0)
static void counted_selection_changed(void){changes++;progression_selection_changed();}
static int counted_instance_validate(const CreatureInstance*c){validations++;return creatures_instance_validate(c);}
void south_game_cancel_rest(void){revoked[0]++;}
void magma_game_cancel_return(void){revoked[1]++;}
void underwater_powers_selection_changed(void){revoked[2]++;}
void underwater_game_selection_changed(void){revoked[3]++;}
void return_powers_selection_changed(void){revoked[4]++;}
void return_legacy_cancel(void){revoked[5]++;}
void return_game_selection_changed(void){revoked[6]++;}
void horizons_powers_selection_changed(void){revoked[7]++;}
void horizons_game_selection_changed(void){revoked[8]++;}
void covenants_powers_selection_changed(void){revoked[9]++;}
void covenants_game_selection_changed(void){revoked[10]++;}
unsigned save5_preflight_status(Save4U32 token){(void)token;return SAVE5_FAILED;}
void save5_preflight_cancel(void){}
int save5_preflight_active(void){return 0;}
void save_game(void){saves++;}
void save_game_ordinary(void){ordinary_saves++;}
void game_companion_reseat(void){reseats++;}
void journal_nav_open(void){journals++;}
void toast(int text_id){(void)text_id;}
void sfx(int id){CHECK(id==2);sounds++;}
unsigned game_power_cooldown(unsigned base){return base;}
void rect(int x,int y,int w,int h,u8 color){(void)x;(void)y;(void)w;(void)h;(void)color;}
void box(int x,int y,int w,int h){(void)x;(void)y;(void)w;(void)h;}
void text(int id,int x,int y,int color){(void)id;(void)x;(void)y;(void)color;}
void centered(int id,int y,int color){(void)id;(void)y;(void)color;}
void text_spans(const UiText*t,int x,int y,int color){(void)t;(void)x;(void)y;(void)color;}
void sprite(const u8*p,int x,int y,int w,int h,int flip){(void)p;(void)x;(void)y;(void)w;(void)h;(void)flip;}
const u8 *companion_form_pixels(unsigned form,unsigned direction,unsigned tick){static const u8 p[256]={1};(void)form;(void)direction;(void)tick;return p;}

static int step(int physical){
 int owned;filtered_held=physical;filtered_pressed=physical&~physical_previous;
 physical_previous=physical;validations=0;
 quickparty_filter_input(&filtered_held,&filtered_pressed);
 owned=quickparty_update(filtered_held,filtered_pressed);updates++;return owned;
}
static void counts(void){
 saves=ordinary_saves=changes=reseats=sounds=journals=0;
 memset(revoked,0,sizeof(revoked));before_progression=progression_revision;
 before_picker=quickparty_revision;
}
static void fixture(unsigned count){
 unsigned i;game_state=3;quickparty_reset(0);game_state=1;
 physical_previous=0;CHECK(!step(0));
 memset(&adventure_save,0,sizeof(adventure_save));
 creatures_roster_init(&adventure_save.roster);
 for(i=0;i<count;i++)CHECK(creatures_grant(&adventure_save.roster,1,36,60,0,0)==i);
 spirit=(int)progression_current_spirit();
 adventure_save.campaign.spirit=(unsigned)spirit<4?(unsigned)spirit:0;
 gfx_companion_frame=19;progression_selection_changed();counts();
}
static void mapping(unsigned a,unsigned b,unsigned c,unsigned d,unsigned selected){
 CreatureRoster*r=&adventure_save.roster;
 r->party[0]=(CreatureU8)a;r->party[1]=(CreatureU8)b;
 r->party[2]=(CreatureU8)c;r->party[3]=(CreatureU8)d;
 r->selected_party=(CreatureU8)selected;spirit=(int)progression_current_spirit();
 adventure_save.campaign.spirit=(unsigned)spirit<4?(unsigned)spirit:0;
 progression_selection_changed();counts();CHECK(creatures_party_validate(r));
}
static void unchanged(const Save5State*before){
 unsigned i;CHECK(!memcmp(before,&adventure_save,sizeof(*before)));
 CHECK(!changes&&!reseats&&!saves&&!ordinary_saves&&!sounds);
 CHECK(progression_revision==before_progression);
 for(i=0;i<11;i++)CHECK(!revoked[i]);
}
static void selected(const Save5State*before,unsigned slot,unsigned change,
                     unsigned ordinary,unsigned picker_delta){
 Save5State expected=*before;unsigned i;
 expected.roster.selected_party=(CreatureU8)slot;
 expected.campaign.spirit=(unsigned)progression_current_spirit()<4?progression_current_spirit():0;
 CHECK(!memcmp(&expected,&adventure_save,sizeof(expected)));
 CHECK(changes==change&&reseats==change&&sounds==change);
 CHECK(!saves&&ordinary_saves==ordinary);
 CHECK(progression_revision==before_progression+change);
 CHECK(quickparty_revision==before_picker+picker_delta);
 for(i=0;i<11;i++)CHECK(revoked[i]==change);
 CHECK((unsigned)spirit==progression_current_spirit());
}
static void hold(unsigned duration,int direction){
 unsigned i;
 for(i=1;i<=duration;i++){
  CHECK(step(L|direction));CHECK(quickparty_open);
  CHECK(quickparty_visible==(i>=13));
  CHECK(validations<=13);
  if(i<=12){CHECK(quickparty_candidate==EMPTY);CHECK(quickparty_revision==before_picker);}
  CHECK(progression_revision==before_progression);
  CHECK(!changes&&!reseats&&!ordinary_saves&&!saves);
 }
}
static void neutral_durations(void){
 static const unsigned durations[]={0,1,11,12,13,14};
 static const unsigned populations[]={0,1,5,160};
 unsigned n,h;
 CHECK(QUICKPARTY_TAP_UPDATES==12&&QUICKPARTY_HOLD_UPDATES==13);
 CHECK(QUICKPARTY_PREPARE_RECORDS==13);
 for(n=0;n<4;n++)for(h=0;h<6;h++){
  Save5State before;unsigned duration=durations[h],count=populations[n];
  unsigned initial,target,change,picker_delta;
  fixture(count);before=adventure_save;initial=before.roster.selected_party;
  hold(duration,0);
  target=duration&&duration<=12&&count>1?1:initial;
  change=target!=initial;picker_delta=duration>=13?2:change;
  CHECK(step(0)==(duration!=0));CHECK(!quickparty_open&&!quickparty_visible);
  selected(&before,target,change,0,picker_delta);
  CHECK(!step(0));selected(&before,target,change,0,picker_delta);
 }
 /* No sampled L press is no tap. This separate zero-hold synthetic API
  * edge preserves the original release-before-count behavior as well. */
 fixture(5);{Save5State before=adventure_save;
  CHECK(quickparty_update(0,L));CHECK(!quickparty_open&&!quickparty_visible);
  selected(&before,1,1,0,1);CHECK(!step(0));selected(&before,1,1,0,1);
 }
}
static void party_order_holes_wrap_and_reserve(void){
 Save5State before;unsigned i;static const unsigned expected[]={1,2,3,0};
 fixture(8);mapping(6,2,7,4,0);
 for(i=0;i<4;i++){
  counts();before=adventure_save;hold(1,0);CHECK(step(0));
  selected(&before,expected[i],1,0,1);
 }
 fixture(8);mapping(6,EMPTY,4,EMPTY,0);before=adventure_save;
 hold(12,0);CHECK(step(0));selected(&before,2,1,0,1);
 counts();before=adventure_save;hold(1,0);CHECK(step(0));selected(&before,0,1,0,1);
 fixture(8);mapping(EMPTY,EMPTY,6,EMPTY,2);before=adventure_save;
 hold(1,0);CHECK(step(0));unchanged(&before);CHECK(quickparty_revision==before_picker);
 /* A reserve previously selected into a party position cycles to the next
  * party position, never to the next physical owned-record index. */
 fixture(8);mapping(6,2,7,4,3);before=adventure_save;
 hold(1,0);CHECK(step(0));selected(&before,0,1,0,1);
 CHECK(adventure_save.roster.party[adventure_save.roster.selected_party]==6);
 /* Two complete presses cycle twice; repeated released updates do nothing. */
 fixture(5);before=adventure_save;hold(1,0);CHECK(step(0));
 CHECK(!step(0));CHECK(!step(0));CHECK(adventure_save.roster.selected_party==1);
 counts();before=adventure_save;hold(1,0);CHECK(step(0));selected(&before,2,1,0,1);
}
static void every_party_order_and_hole_mask(void){
 static const unsigned records[]={6,2,7,4};unsigned a,b,c,d,slot,mask,next;
 Save5State before;
 for(a=0;a<4;a++)for(b=0;b<4;b++)for(c=0;c<4;c++)for(d=0;d<4;d++){
  if(a==b||a==c||a==d||b==c||b==d||c==d)continue;
  for(slot=0;slot<4;slot++){
   fixture(8);mapping(records[a],records[b],records[c],records[d],slot);
   before=adventure_save;hold(1,0);CHECK(step(0));
   selected(&before,(slot+1u)&3u,1,0,1);
  }
 }
 for(mask=1;mask<16;mask++)for(slot=0;slot<4;slot++)if(mask&(1u<<slot)){
  fixture(8);mapping(mask&1?6:EMPTY,mask&2?2:EMPTY,
                     mask&4?7:EMPTY,mask&8?4:EMPTY,slot);
  next=(slot+1u)&3u;while(!(mask&(1u<<next)))next=(next+1u)&3u;
  before=adventure_save;hold(12,0);CHECK(step(0));
  selected(&before,next,next!=slot,0,next!=slot);
 }
 /* Synthetic broken mappings must still retain the original safe member
  * lookup: unowned/unknown records and out-of-range party refs are skipped. */
 fixture(8);mapping(6,2,7,4,0);
 adventure_save.roster.instances[2].flags=0;
 adventure_save.roster.instances[7].form_id=129;
 before=adventure_save;hold(1,0);CHECK(step(0));selected(&before,3,1,0,1);
 fixture(8);mapping(6,2,7,4,0);
 adventure_save.roster.party[1]=200;adventure_save.roster.party[2]=EMPTY;
 before=adventure_save;hold(1,0);CHECK(step(0));selected(&before,3,1,0,1);
}
static void directional_short_and_release_edge(void){
 static const int dirs[]={16,32,64,128,16|32,16|64,DIRECTIONS};
 static const unsigned durations[]={1,11,12};unsigned d,h;
 for(d=0;d<sizeof(dirs)/sizeof(dirs[0]);d++)for(h=0;h<3;h++){
  Save5State before;fixture(5);before=adventure_save;
  hold(durations[h],dirs[d]);CHECK(step(0));unchanged(&before);
  CHECK(!quickparty_open&&!quickparty_visible&&quickparty_revision==before_picker);
 }
 for(d=0;d<sizeof(dirs)/sizeof(dirs[0]);d++){
  Save5State before;unsigned i;
  fixture(5);before=adventure_save;CHECK(step(L|dirs[d]));
  for(i=1;i<12;i++)CHECK(step(L));CHECK(step(0));
  unchanged(&before);CHECK(quickparty_revision==before_picker);
  /* Exact4005 ordering: a first direction on release is too late to
   * disqualify the tap. It is latched out of subsequent field input. */
  fixture(5);before=adventure_save;hold(12,0);CHECK(step(dirs[d]));
  selected(&before,1,1,0,1);CHECK(!step(dirs[d]));
  CHECK(!filtered_held&&!filtered_pressed);CHECK(!step(0));
  CHECK(!step(dirs[d]));CHECK(filtered_held==dirs[d]&&filtered_pressed==dirs[d]);
 }
}
static void bounded_publish_and_long_repeats(void){
 Save5State before;unsigned i;
 fixture(160);before=adventure_save;
 for(i=1;i<=13;i++){
  CHECK(step(L));CHECK(quickparty_open);CHECK(quickparty_visible==(i==13));
  CHECK(validations==(i<=12?13u:4u));
  CHECK(quickparty_candidate==(i<13?EMPTY:0));unchanged(&before);
  CHECK(quickparty_revision==before_picker+(i==13));
 }
 CHECK(step(L|LEFT));CHECK(quickparty_candidate==159); /* Every reserve, wrap. */
 CHECK(step(L|RIGHT));CHECK(quickparty_candidate==0);CHECK(step(L));
 CHECK(step(L|RIGHT));CHECK(quickparty_candidate==1);
 for(i=1;i<QUICKPARTY_REPEAT_DELAY;i++){
  CHECK(step(L|RIGHT));CHECK(quickparty_candidate==1);
 }
 CHECK(step(L|RIGHT));CHECK(quickparty_candidate==2);
 for(i=1;i<QUICKPARTY_REPEAT_INTERVAL;i++){
  CHECK(step(L|RIGHT));CHECK(quickparty_candidate==2);
 }
 CHECK(step(L|RIGHT));CHECK(quickparty_candidate==3);
 CHECK(step(L|LEFT));CHECK(quickparty_candidate==2); /* Immediate reversal. */
 CHECK(step(0));CHECK(adventure_save.roster.selected_party==2);
 CHECK(changes==1&&reseats==1&&!saves&&ordinary_saves==1);
 CHECK(!step(0));CHECK(changes==1&&ordinary_saves==1);
 /* A horizontal hold starts one visible step after arming, with no repeat
  * delay accrued invisibly. Reserve selection updates exactly one slot. */
 fixture(5);before=adventure_save;hold(13,LEFT);CHECK(quickparty_candidate==4);
 CHECK(step(0));CHECK(adventure_save.roster.party[0]==4);
 CHECK(adventure_save.roster.selected_party==0&&ordinary_saves==1&&!saves);
 CHECK(changes==1&&reseats==1&&progression_revision==before_progression+1);
 CHECK(!memcmp(adventure_save.roster.instances,before.roster.instances,sizeof(before.roster.instances)));
 /* A continuously held direction starts its repeat clock only when visible,
  * even though logical input ownership began twelve updates earlier. */
 fixture(5);before=adventure_save;hold(13,RIGHT);CHECK(quickparty_candidate==1);
 for(i=1;i<QUICKPARTY_REPEAT_DELAY;i++){
  CHECK(step(L|RIGHT));CHECK(quickparty_candidate==1);
 }
 CHECK(step(L|RIGHT));CHECK(quickparty_candidate==2);
 CHECK(step(L|B));unchanged(&before);CHECK(!step(0));
 fixture(8);mapping(6,2,7,4,0);before=adventure_save;
 hold(13,0);CHECK(quickparty_candidate==6);CHECK(step(0));
 unchanged(&before);CHECK(quickparty_revision==before_picker+2);
}
static void cancel_reset_and_modal(void){
 static const unsigned counts_to_cancel[]={0,1,11,12,13,14};
 unsigned h,button,release;
 for(h=0;h<6;h++)for(button=0;button<2;button++)for(release=0;release<2;release++){
  Save5State before;int cancel=button?START:B;unsigned duration=counts_to_cancel[h];
  /* Without any L observation there is no picker context to cancel. The
   * ordinary engine owns standalone B/START; opening+cancel is tested below. */
  if(!duration&&release)continue;
  fixture(5);before=adventure_save;hold(duration,0);
  /* duration0 combines opening/cancel; otherwise B/START wins at both the
   * 12->13 threshold and L release, without accidental short tap. */
  CHECK(step((release?0:L)|cancel));unchanged(&before);
  CHECK(!quickparty_open&&!quickparty_visible);
  CHECK(quickparty_revision==before_picker+(duration>=13?2u:0u));
  CHECK(game_state==(button?3:1));CHECK(journals==(button?1u:0u));
  if(!release){CHECK(!step(L|cancel));unchanged(&before);CHECK(!quickparty_open);}
 }
 for(h=0;h<6;h++){
  Save5State before;unsigned duration=counts_to_cancel[h];
  fixture(5);before=adventure_save;hold(duration,0);
  quickparty_reset(L);CHECK(!quickparty_open&&!quickparty_visible);unchanged(&before);
  CHECK(!step(L));CHECK(!step(0));unchanged(&before);
  CHECK(quickparty_revision==before_picker+(duration>=13?2u:0u));
 }
 /* Physical L held over a modal cannot reopen/cycle after returning PLAY. */
 fixture(5);{Save5State before=adventure_save;unsigned i;
  game_state=3;physical_previous=L;
  for(i=0;i<14;i++)quickparty_reset(L);
  game_state=1;for(i=0;i<14;i++)CHECK(!step(L));
  CHECK(!quickparty_open&&!quickparty_visible);unchanged(&before);
  CHECK(!step(0));hold(1,0);CHECK(step(0));selected(&before,1,1,0,1);
 }
}
static void notice_once_without_extra_save(void){
 CreatureRoster*r=&adventure_save.roster;Save5State before,expected;unsigned i;
 fixture(0);CHECK(creatures_migrate_legacy(r,7,0));
 for(i=0;i<4;i++)r->party[i]=EMPTY;
 r->party[2]=2;r->selected_party=2;
 spirit=(int)progression_current_spirit();adventure_save.campaign.spirit=2;
 progression_selection_changed();counts();before=adventure_save;
 hold(1,0);CHECK(step(0));expected=before;expected.economy.reserved[1]|=1;
 CHECK(!memcmp(&expected,&adventure_save,sizeof(expected)));
 CHECK(!changes&&!reseats&&!sounds&&!saves&&ordinary_saves==1);
 CHECK(progression_revision==before_progression+1&&quickparty_revision==before_picker+1);
 counts();before=adventure_save;hold(12,0);CHECK(step(0));unchanged(&before);
 CHECK(quickparty_revision==before_picker);
}
int main(void){
 CHECK(creatures_catalog_validate());neutral_durations();party_order_holes_wrap_and_reserve();
 every_party_order_and_hole_mask();
 directional_short_and_release_edge();bounded_publish_and_long_repeats();
 cancel_reset_and_modal();notice_once_without_extra_save();
 printf("%u synthetic short-L assertions, %u input updates passed; 0/1/11/12/13/14 holds, party order/holes/reserves, arming13-record bound, repeat/cancel/modal/handoff and exact save/revision counts\n",checks,updates);
 return 0;
}
