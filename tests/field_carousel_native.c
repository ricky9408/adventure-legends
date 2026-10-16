/* Synthetic host fixtures, NOT controller acquisition or cartridge evidence.
 * Exercise production quickparty/creatures/progression/notice code. Engine
 * save/reseat and regional authority revocation boundaries are counted bridges;
 * the real progression selection signature invokes those revocation hooks. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "progression.h"
static void counted_selection_changed(void);
static int counted_instance_validate(const CreatureInstance*);
#define progression_selection_changed counted_selection_changed
#define creatures_instance_validate counted_instance_validate
#include "quickparty.c"
#undef creatures_instance_validate
#undef progression_selection_changed
#define field_arming (quickparty_open&&!quickparty_visible)

volatile int spirit,game_state,room;
int journal_tab,gfx_companion_frame;
static unsigned saves,ordinary_saves,changes,reseats,sounds,journals;
static unsigned before_progression_revision;
static unsigned validation_calls,draw_calls;
static unsigned revoked[11],assertions,draw_sprites;
static unsigned short framebuffer[240*160/2];
unsigned short *screen=framebuffer;
static int physical_previous,filtered_held,filtered_pressed;
static int checking_field;
static int counted_instance_validate(const CreatureInstance*c){validation_calls++;return creatures_instance_validate(c);}
static void counted_selection_changed(void){changes++;progression_selection_changed();}
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
void toast(int t){(void)t;}
void sfx(int n){(void)n;sounds++;}
unsigned game_power_cooldown(unsigned base){return base;}
static void bounds(int x,int y,int w,int h){
 draw_calls++;
 assert(x>=0&&y>=0&&w>=0&&h>=0&&x+w<=240&&y+h<=160);
 if(checking_field)assert(x>=26&&y>=29&&x+w<=214);
}
void rect(int x,int y,int w,int h,u8 color){(void)color;bounds(x,y,w,h);}
void box(int x,int y,int w,int h){bounds(x,y,w,h);}
void text(int t,int x,int y,int color){(void)color;bounds(x,y,ui_texts[t].width,ui_texts[t].height);}
void centered(int t,int y,int color){text(t,(240-ui_texts[t].width)/2,y,color);}
void text_spans(const UiText*t,int x,int y,int color){
 const UiRun*r=t->runs[x&1];unsigned i,j;bounds(x,y,t->width,t->height);
 for(i=0;i<t->count[x&1];i++)for(j=0;j<r[i].count;j++){
  unsigned p=(unsigned)(y*120+(x>>1))+r[i].offset+j;assert(p<240*160/2);
  if(r[i].mask&1)screen[p]=(unsigned short)((screen[p]&0xff00)|(unsigned)color);
  if(r[i].mask&2)screen[p]=(unsigned short)((screen[p]&255)|((unsigned)color<<8));
 }
}
void sprite(const u8*p,int x,int y,int w,int h,int flip){(void)p;(void)flip;bounds(x,y,w,h);draw_sprites++;}
const u8 *companion_form_pixels(unsigned f,unsigned d,unsigned tick){static const u8 pixels[256]={1};(void)f;(void)d;(void)tick;return pixels;}

static int physical_step(int physical){int owned;filtered_held=physical;filtered_pressed=physical&~physical_previous;physical_previous=physical;quickparty_filter_input(&filtered_held,&filtered_pressed);owned=quickparty_update(filtered_held,filtered_pressed);assertions++;return owned;}
/* Transaction tests start at a complete carousel. Boundary tests below drive
 * every physical update themselves, including the entire hidden interval. */
static int step(int physical){int owned=physical_step(physical);while(field_arming&&(physical&L)&&!(physical&(B|START)))assert(physical_step(physical));return owned;}
static void clear_counts(void){saves=ordinary_saves=changes=reseats=sounds=journals=validation_calls=draw_calls=0;memset(revoked,0,sizeof revoked);before_progression_revision=progression_revision;}
static void active_invariants(void){CreatureRoster*r=&adventure_save.roster;unsigned i,j,legends=0;assert(creatures_roster_validate(r));assert(creatures_party_validate(r));for(i=0;i<4;i++)if(r->party[i]!=EMPTY){for(j=0;j<i;j++)assert(r->party[i]!=r->party[j]);legends+=creatures_form(r->instances[r->party[i]].form_id)->rarity!=0;}assert(legends<=1);if(r->selected_party<4){assert((unsigned)spirit==progression_current_spirit());assert(adventure_save.campaign.spirit==((unsigned)spirit<4?(unsigned)spirit:0));}}
static void fixture(unsigned count){unsigned i;quickparty_reset(0);step(0);memset(&adventure_save,0,sizeof adventure_save);creatures_roster_init(&adventure_save.roster);for(i=0;i<count;i++)assert(creatures_grant(&adventure_save.roster,1,36,60,0,0)==i);spirit=(int)progression_current_spirit();adventure_save.campaign.spirit=(unsigned)spirit<4?(unsigned)spirit:0;gfx_companion_frame=17;game_state=1;progression_selection_changed();clear_counts();}
static void assert_no_effect(const Save5State*before,int before_spirit){assert(!memcmp(before,&adventure_save,sizeof *before));assert(spirit==before_spirit);assert(progression_revision==before_progression_revision);assert(!changes&&!reseats&&!saves&&!ordinary_saves);}
static void assert_one_sync(unsigned ordinary){unsigned i;assert(changes==1&&reseats==1&&!saves&&ordinary_saves==ordinary);assert(progression_revision==before_progression_revision+1);for(i=0;i<11;i++)assert(revoked[i]==1);assert(gfx_companion_frame==-1);active_invariants();}
static void draw(unsigned expected){checking_field=1;draw_sprites=0;quickparty_draw();assert(draw_sprites==expected);checking_field=0;}
static void edge(int direction){assert(step(L));assert(step(L|direction));}
static void browse_to(unsigned instance){unsigned i;assert(step(L));for(i=0;i<160&&quickparty_candidate!=(int)instance;i++)edge(RIGHT);assert(quickparty_candidate==(int)instance);}

static void population_and_preview(void){
 static const unsigned counts[]={0,1,4,5,160};unsigned k,i;Save5State before;
 /* Authored native names, not a mocked font metric, fit the established panel. */
 for(i=1;i<=CREATURE_FORM_CAPACITY;i++)if(creatures_form(i))assert(ui_texts[progression_name_id(i)].width<=188);
 for(k=0;k<sizeof counts/sizeof counts[0];k++){
  unsigned n=counts[k];fixture(n);before=adventure_save;assert(step(L));assert(quickparty_open&&field_count==n);assert(quickparty_candidate==(n?0:EMPTY));draw(n<5?n:5);
  for(i=0;i<(n?n*2:10);i++){
   edge(RIGHT);assert(quickparty_candidate==(n?(int)((i+1)%n):EMPTY));draw(n<5?n:5);assert_no_effect(&before,0);
  }
  assert(step(0));assert_no_effect(&before,0);assert(!quickparty_open);active_invariants();
 }
 /* A completed neutral hold keeps the current instance on release. */
 for(k=0;k<2;k++){fixture(5);before=adventure_save;for(i=0;i<(k?80u:1u);i++)assert(step(L));assert(step(0));assert_no_effect(&before,0);}
}
static void preparation_and_tap_boundaries(void){
 unsigned count,i,j,revision;Save5State before;CreatureRoster*r=&adventure_save.roster;
 for(count=1;count<=QUICKPARTY_TAP_UPDATES;count++){
  fixture(5);before=adventure_save;revision=quickparty_revision;
  for(i=1;i<=count;i++){assert(physical_step(L));assert(field_arming&&quickparty_candidate==EMPTY);assert(field_scan==i*QUICKPARTY_PREPARE_RECORDS);assert(quickparty_revision==revision);assert_no_effect(&before,0);}
  assert(physical_step(0));assert(!quickparty_open&&!field_arming&&!field_scan);assert(r->selected_party==1);assert(!memcmp(r->party,before.roster.party,4));assert(!memcmp(r->instances,before.roster.instances,sizeof r->instances));assert_one_sync(0);
 }
 fixture(160);before=adventure_save;revision=quickparty_revision;
 for(i=1;i<=QUICKPARTY_HOLD_UPDATES;i++){assert(physical_step(L));assert(field_scan==(i<13?i*13:160));assert(validation_calls==field_scan);assert(quickparty_open&&quickparty_visible==(i==QUICKPARTY_HOLD_UPDATES));if(i<QUICKPARTY_HOLD_UPDATES){assert(field_arming&&quickparty_candidate==EMPTY&&quickparty_revision==revision);quickparty_draw();assert(!draw_calls);}assert_no_effect(&before,0);}
 assert(field_count==160&&quickparty_candidate==0&&!field_arming);assert(physical_step(0));assert_no_effect(&before,0);
 /* Every kind of held direction suppresses a short tap. A direction released
  * before readiness never becomes a queued carousel movement. */
 {static const int dirs[]={RIGHT,LEFT,64,128,RIGHT|LEFT,RIGHT|64,DIRECTIONS};
  for(j=0;j<sizeof dirs/sizeof dirs[0];j++)for(count=1;count<=QUICKPARTY_TAP_UPDATES;count++){
   fixture(5);before=adventure_save;assert(physical_step(L|dirs[j]));for(i=1;i<count;i++)assert(physical_step(L));assert(physical_step(0));assert_no_effect(&before,0);
  }
 }
 fixture(5);before=adventure_save;assert(physical_step(L|RIGHT));for(i=1;i<QUICKPARTY_HOLD_UPDATES;i++)assert(physical_step(L));assert(quickparty_open&&quickparty_candidate==0);assert(physical_step(0));assert_no_effect(&before,0);
 /* The first still-held horizontal choice starts only once the full list is
  * ready, then receives the ordinary24/6 repeat cadence. */
 fixture(160);before=adventure_save;for(i=0;i<QUICKPARTY_HOLD_UPDATES;i++)assert(physical_step(L|RIGHT));assert(quickparty_open&&quickparty_candidate==1);for(i=1;i<QUICKPARTY_REPEAT_DELAY;i++){assert(physical_step(L|RIGHT));assert(quickparty_candidate==1);}assert(physical_step(L|RIGHT));assert(quickparty_candidate==2);assert(physical_step(L|B));assert_no_effect(&before,0);physical_step(0);
 /* Hidden ownership has the same cancellation, modal latch and held-input
  * handoff guarantees as the visible selector, without a revision redraw. */
 fixture(5);before=adventure_save;revision=quickparty_revision;assert(physical_step(L|RIGHT));assert(physical_step(L|RIGHT|B));assert(!quickparty_open&&!field_arming&&blocked&&!field_scan&&quickparty_revision==revision);assert_no_effect(&before,0);assert(!physical_step(L|RIGHT|B)&&filtered_held==L);physical_step(0);
 fixture(5);before=adventure_save;assert(physical_step(L));assert(physical_step(L|START));assert(game_state==3&&journals==1&&!field_arming&&!quickparty_open);assert_no_effect(&before,0);game_state=1;assert(!physical_step(L));physical_step(0);
 fixture(5);before=adventure_save;assert(physical_step(L|RIGHT));quickparty_reset(L|RIGHT);assert(!field_arming&&!quickparty_open&&!field_scan);assert(!physical_step(L|RIGHT)&&filtered_held==L);assert_no_effect(&before,0);physical_step(0);
}
static void gaps_validity_and_instances(void){
 CreatureRoster*r=&adventure_save.roster;Save5State before;unsigned i;fixture(5);
 r->instances[159]=r->instances[4];memset(&r->instances[4],0,sizeof r->instances[4]);
 r->instances[70]=r->instances[3];memset(&r->instances[3],0,sizeof r->instances[3]);r->party[3]=70;
 /* Invalid owned form, unowned record, and malformed owned instance must be
  * skipped; discovery bits deliberately claim unrelated forms as well. */
 r->instances[20]=r->instances[159];r->instances[20].form_id=129;
 r->instances[30]=r->instances[159];r->instances[30].flags=0;
 r->instances[90]=r->instances[159];r->instances[90].level=0;
 memset(r->seen,255,sizeof r->seen);memset(r->obtained,255,sizeof r->obtained);
 before=adventure_save;assert(step(L));assert(field_count==5);edge(LEFT);assert(quickparty_candidate==159);edge(LEFT);assert(quickparty_candidate==70);edge(RIGHT);assert(quickparty_candidate==159);assert_no_effect(&before,0);assert(step(L|B));assert_no_effect(&before,0);step(0);
 /* Every physical instance is separately reachable, despite identical forms.
  * Valid story protection is never used as a selection lock. */
 fixture(0);assert(creatures_migrate_legacy(r,7,0));spirit=(int)progression_current_spirit();progression_selection_changed();clear_counts();before=adventure_save;
 assert(step(L));assert(field_count==4);for(i=0;i<4;i++){assert(r->instances[quickparty_candidate].flags&CREATURE_STORY_LOCKED);edge(RIGHT);}assert_no_effect(&before,0);assert(step(0));
 fixture(5);assert(r->instances[0].instance_id!=r->instances[4].instance_id);before=adventure_save;browse_to(4);assert_no_effect(&before,0);assert(step(0));assert(r->party[0]==4&&r->selected_party==0);assert(!memcmp(r->instances,before.roster.instances,sizeof r->instances));assert_one_sync(1);
}
static void cadence_and_invalid_directions(void){
 unsigned i;Save5State before;fixture(160);before=adventure_save;assert(step(L|RIGHT));assert(quickparty_candidate==1);
 for(i=1;i<QUICKPARTY_REPEAT_DELAY;i++){assert(step(L|RIGHT));assert(quickparty_candidate==1);}
 assert(step(L|RIGHT));assert(quickparty_candidate==2);
 for(i=1;i<QUICKPARTY_REPEAT_INTERVAL;i++){assert(step(L|RIGHT));assert(quickparty_candidate==2);}
 assert(step(L|RIGHT));assert(quickparty_candidate==3);
 assert(step(L|LEFT));assert(quickparty_candidate==2); /* immediate reversal */
 for(i=0;i<60;i++)assert(step(L|LEFT|RIGHT));assert(quickparty_candidate==2);
 assert(step(L|LEFT));assert(quickparty_candidate==1);
 for(i=0;i<60;i++)assert(step(L|RIGHT|64));assert(quickparty_candidate==1);
 assert(step(L|RIGHT));assert(quickparty_candidate==2);
 for(i=0;i<60;i++)assert(step(L|128));assert(quickparty_candidate==2);
 for(i=0;i<60;i++)assert(step(L|64));assert(quickparty_candidate==2);
 for(i=0;i<60;i++)assert(step(L|DIRECTIONS));assert(quickparty_candidate==2);
 edge(LEFT);assert(quickparty_candidate==1);edge(LEFT);assert(quickparty_candidate==0);edge(LEFT);assert(quickparty_candidate==159);edge(RIGHT);assert(quickparty_candidate==0);assert_no_effect(&before,0);
 assert(step(L|B));assert_no_effect(&before,0);step(0);
}
static void commit_destinations_and_save(void){
 CreatureRoster*r=&adventure_save.roster;Save5State before;unsigned i,a,b;
 fixture(5);r->selected_party=3;progression_selection_changed();clear_counts();before=adventure_save;assert(step(L));assert(quickparty_candidate==3);edge(LEFT);assert(quickparty_candidate==2);assert_no_effect(&before,0);assert(step(0));assert(r->selected_party==2);assert(!memcmp(r->party,before.roster.party,4));assert_one_sync(1);
 fixture(4);a=creatures_grant(r,121,36,60,0,0);b=creatures_grant(r,122,36,60,0,0);assert(a==4&&b==5);assert(quickparty_assign(2,a));r->selected_party=0;spirit=0;adventure_save.campaign.spirit=0;progression_selection_changed();clear_counts();before=adventure_save;
 browse_to(b);assert_no_effect(&before,0);assert(step(0));assert(r->party[2]==b&&r->selected_party==2&&r->party[0]==0);assert(!memcmp(r->instances,before.roster.instances,sizeof r->instances));assert(!memcmp(r->seen,before.roster.seen,48));assert_one_sync(1);
 /* Selecting a non-legendary reserve replaces precisely the selected slot. */
 clear_counts();before=adventure_save;browse_to(2);assert(step(0));assert(r->party[2]==2&&r->selected_party==2);assert_one_sync(1);
 /* Acknowledgement plus selection share exactly one ordinary save. */
 fixture(0);assert(creatures_migrate_legacy(r,7,0));spirit=0;progression_selection_changed();clear_counts();before=adventure_save;browse_to(2);assert_no_effect(&before,0);assert(step(0));assert(r->selected_party==2);assert_one_sync(1);assert(adventure_save.economy.reserved[1]&1);
 /* A same-member open/release may acknowledge once, without cast sync. */
 clear_counts();adventure_save.economy.reserved[1]=0;assert(step(L));assert(step(0));assert(ordinary_saves==1&&!saves&&!changes&&!reseats);clear_counts();assert(step(L));assert(step(0));assert(!ordinary_saves&&!changes);
 /* Every valid reserve remains reachable with a legendary already active. */
 for(i=121;i<=128;i++){clear_counts();assert(creatures_grant(r,i,36,60,0,0)<160);}
 active_invariants();
}
static void every_instance_and_legendary_destination(void){
 CreatureRoster*r=&adventure_save.roster;CreatureInstance records[160];unsigned target,first,second,i;CreatureU8 party[4];Save5State before;
 fixture(160);memcpy(records,r->instances,sizeof records);
 for(target=0;target<160;target++){
  clear_counts();browse_to(target);assert(step(0));assert(r->party[r->selected_party]==target);assert(!memcmp(records,r->instances,sizeof records));
  if(target)assert_one_sync(1);else{assert(!changes&&!reseats&&!ordinary_saves&&!saves);active_invariants();}
 }
 /* All ordered distinct legendary pairs: an inactive legendary always
  * replaces the existing legendary position, even with another selection. */
 for(first=121;first<=128;first++)for(second=121;second<=128;second++)if(first!=second){
  fixture(4);for(i=121;i<=128;i++)assert(creatures_grant(r,i,36,60,0,0)==i-117);
  for(i=0;i<4;i++)party[i]=r->party[i];party[2]=(CreatureU8)(first-117);assert(creatures_party_set(r,party,0));r->selected_party=0;spirit=0;adventure_save.campaign.spirit=0;progression_selection_changed();clear_counts();before=adventure_save;
  browse_to(second-117);assert_no_effect(&before,0);assert(step(0));assert(r->selected_party==2&&r->party[2]==second-117&&r->party[0]==0);assert(!memcmp(r->instances,before.roster.instances,sizeof r->instances));assert_one_sync(1);
 }
 /* A synthetic corrupt live mapping cannot bypass creatures_party_set. */
 fixture(5);assert(step(L|RIGHT));r->party[2]=r->party[1];before=adventure_save;assert(step(0));assert_no_effect(&before,0);
}
static void cancel_modal_reset_and_handoff(void){
 Save5State before;unsigned i;fixture(5);before=adventure_save;assert(step(L|RIGHT));assert(quickparty_candidate==1);
 assert(step(L|RIGHT|1|256|4));assert_no_effect(&before,0);assert(step(L|RIGHT|B|1|256|4));assert(!quickparty_open&&blocked);assert_no_effect(&before,0);
 assert(!step(L|RIGHT|B|1|256|4));assert(filtered_held==L&&filtered_pressed==0);assert(!quickparty_open);assert_no_effect(&before,0);
 /* World owns this update while each held input stays suppressed. Releasing
  * A permits a fresh A press even while cancelled L remains held. */
 assert(!step(L|RIGHT|B|256|4));assert(!step(L|RIGHT|B|1|256|4));assert((filtered_held&1)&&(filtered_pressed&1));assert(!quickparty_open);
 assert(!step(RIGHT|B|1|256|4));assert(!(filtered_held&(RIGHT|B|256|4)));assert(!blocked);assert(!step(0));assert(!step(RIGHT|B|1|256|4));assert(filtered_held==(RIGHT|B|1|256|4));assert(filtered_pressed==filtered_held);step(0);
 /* Release commits own the closing frame; stale directions and actions are
  * suppressed afterwards, while unrelated fresh directions remain usable. */
 fixture(5);assert(step(L|RIGHT|1|256|4));assert(step(RIGHT|1|256|4));assert(!quickparty_open);assert_one_sync(1);assert(!step(RIGHT|1|256|4));assert(filtered_held==0);assert(!step(RIGHT|128|1|256|4));assert(filtered_held==128);step(0);
 fixture(5);before=adventure_save;assert(step(L|RIGHT));assert(step(L|START|RIGHT));assert(game_state==3&&journals==1&&!quickparty_open);assert_no_effect(&before,0);
 for(i=0;i<8;i++)quickparty_reset(L|RIGHT);game_state=1;assert(!step(L|RIGHT));assert(!quickparty_open&&filtered_held==L);assert(!step(0));assert(step(L));assert(quickparty_candidate==0);assert(step(L|B));step(0);
 /* Physical release inside a modal ends that button's handoff even if it is
  * pressed again before PLAY. L still cannot reopen until its own release. */
 fixture(5);assert(step(L|RIGHT));assert(step(L|RIGHT|START));quickparty_reset(L);quickparty_reset(L|RIGHT);physical_previous=L|RIGHT;game_state=1;assert(!step(L|RIGHT));assert(filtered_held==(L|RIGHT)&&!quickparty_open);step(0);
 /* A room reset sees filtered PLAY input; it must preserve suppression of a
  * still-held button rather than confusing that mask with physical release. */
 fixture(5);assert(step(L|RIGHT));assert(step(RIGHT));assert(!step(RIGHT));assert(filtered_held==0);quickparty_reset(filtered_held);assert(!step(RIGHT));assert(filtered_held==0);step(0);
 /* Room/reset interruption discards preview and repeat state, retaining the
  * held-L block. It never commits a previously previewed reserve. */
 fixture(5);before=adventure_save;assert(step(L|RIGHT));quickparty_reset(L|RIGHT);assert(quickparty_candidate==EMPTY&&!quickparty_open&&!field_count&&!repeat_updates&&!repeat_direction);assert_no_effect(&before,0);assert(!step(L|RIGHT));step(0);assert(step(L));assert(quickparty_candidate==0);assert(step(L|B));step(0);
 quickparty_menu_detail=1;quickparty_menu_command=7;companion_guide_page=1;quickparty_reset(0);assert(!quickparty_menu_detail&&!quickparty_menu_command&&!companion_guide_page);
 game_state=3;quickparty_menu_detail=1;quickparty_menu_command=7;companion_guide_page=1;quickparty_reset(0);assert(quickparty_menu_detail&&quickparty_menu_command==7&&companion_guide_page==1);game_state=1;quickparty_reset(0);
 /* Same-frame B/START overrides opening and directions. */
 fixture(5);before=adventure_save;assert(step(L|RIGHT|B));assert(!quickparty_open);assert_no_effect(&before,0);step(0);assert(step(L|RIGHT|START));assert(game_state==3&&!quickparty_open&&journals==1);assert_no_effect(&before,0);step(0);
 fixture(5);before=adventure_save;assert(step(L|RIGHT));assert(step(RIGHT|B));assert_no_effect(&before,0);assert(!quickparty_open);step(0);
 fixture(5);before=adventure_save;assert(step(L|RIGHT));assert(step(RIGHT|START));assert_no_effect(&before,0);assert(!quickparty_open&&game_state==3&&journals==1);step(0);
}
int main(void){
 assert(creatures_catalog_validate());preparation_and_tap_boundaries();population_and_preview();gaps_validity_and_instances();cadence_and_invalid_directions();commit_destinations_and_save();every_instance_and_legendary_destination();cancel_modal_reset_and_handoff();
 printf("PASS synthetic field carousel: %u native C input updates; real creature validator, progression signature and notice; 0/1/4/5/160 owners, gaps, repeats, preview, commit, save and per-button handoff\n",assertions);return 0;
}
