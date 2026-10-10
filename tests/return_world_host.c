/* Host-only orchestration/geometry bridge. No claim of native cast or input QA. */
#include <string.h>
#include <limits.h>
#include "return_game.h"
#include "return_art.h"
#include "return_quests.h"
#include "progression.h"
Save5State adventure_save;
unsigned progression_revision;
volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
int face,keys,journal_tab;
static unsigned last_toast,actors,health_fills,saved,geometry_changes;
static Save5State snapshot;
CreatureInstance*progression_selected(void){unsigned p=adventure_save.roster.selected_party,s;if(p>=4)return 0;s=adventure_save.roster.party[p];return s<160?&adventure_save.roster.instances[s]:0;}
unsigned progression_command(void){CreatureInstance*c=progression_selected();return c?c->equipped[c->selected_command]:0;}
void progression_refresh(void){progression_revision++;}
void save_game(void){saved++;}
void dialogue(int a,int b,int c){(void)a;(void)b;(void)c;game_state=2;}
void toast(int a){last_toast=(unsigned)a;}
void text(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void centered(int a,int b,int c){(void)a;(void)b;(void)c;}
void box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void rect(int a,int b,int c,int d,unsigned char e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void line(int a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void return_actor(unsigned a,int x,int y){(void)a;if(x-camera_x>=-8&&x-camera_x<248&&y-camera_y>=-8&&y-camera_y<168)actors++;}
void region_form_actor(unsigned a,int x,int y){return_actor(a,x,y);}
void game_health_fill(void){health_fills++;}
void return_powers_geometry_changed(void){geometry_changes++;}
void game_region_warp(int x,int y){if(!return_game_solid(x,y)){px=x;py=y;}}
void enter_room(int r,int s){if(r>=54){int q=return_game_request_enter(r,s);if(q==1)return_game_enter(r,s);}else{return_game_reset();room=r;checkpoint_spawn=s;adventure_save.campaign.room=r;adventure_save.campaign.spawn=s;}}
#include "../src/return_game.c"
int settle(void){unsigned n=0,a,s;while(return_game_event_pending()&&n++<1000)if(return_game_prepare_event()==SAVE5_FAILED)return 0;if(n>=1000)return 0;if(return_game_take_transition(&a,&s))enter_room(a,s);game_state=1;return save5_validate(&adventure_save);}
int fresh(void){return_game_reset();save5_test_reset_writer();save5_test_fail_after(-1);memset(&adventure_save,0,sizeof adventure_save);if(!save5_load(&adventure_save))return 0;room=adventure_save.campaign.room;checkpoint_spawn=adventure_save.campaign.spawn;game_state=summoned=1;face=1;keys=transition_lock=camera_x=camera_y=0;last_toast=actors=health_fills=saved=geometry_changes=0;return save5_validate(&adventure_save);}
void at(int x,int y,int f){px=x;py=y;face=f;game_state=1;keys=0;}
void old_room(unsigned r,unsigned spawn){return_game_reset();room=r;checkpoint_spawn=spawn;adventure_save.campaign.room=r;adventure_save.campaign.spawn=spawn;game_state=1;}
int entry(unsigned r,unsigned s){game_state=1;int q=return_game_request_enter(r,s);if(q==1)return return_game_enter(r,s);if(q==2)return settle();return 0;}
unsigned qs(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
unsigned qo(unsigned q){return adventure_save.quests.objectives[q];}
unsigned get_toast(void){return last_toast;}
int valid(void){return save5_validate(&adventure_save);}
unsigned select_form(unsigned f,unsigned command){unsigned i,j;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==f){for(j=0;j<4;j++)if(adventure_save.roster.party[j]==i)break;if(j<4){unsigned tmp=adventure_save.roster.party[0];adventure_save.roster.party[0]=i;adventure_save.roster.party[j]=tmp;}else adventure_save.roster.party[0]=i;adventure_save.roster.selected_party=0;CreatureInstance*c=&adventure_save.roster.instances[i];if(!creatures_equip(c,0,command))return 254;c->selected_command=0;return_game_selection_changed();return i;}return 255;}
int synthetic_field(unsigned index){int x,y;CreatureInstance*c=active();if(!c||!return_game_field_target(index,&x,&y,0))return 0;return return_game_field_hit(index,progression_command(),c->instance_id,c->form_id,return_game_action_begin(3));}
unsigned count(void){return creatures_roster_count(&adventure_save.roster);}
unsigned trial_mask(unsigned slot){return adventure_save.roster.instances[slot].trial_flags;}
unsigned level(unsigned slot){return adventure_save.roster.instances[slot].level;}
unsigned bond(unsigned slot){return adventure_save.roster.instances[slot].bond;}
void snapshot_state(void){snapshot=adventure_save;}
int unchanged(void){return !memcmp(&snapshot,&adventure_save,sizeof snapshot);}
void tick(void){return_game_tick();}
int evolve(unsigned slot,unsigned to){return creatures_evolve_to(&adventure_save.roster,slot,to,return_context(&adventure_save),1,1);}
unsigned mask_setting(unsigned value){setting[0]=value&1;setting[1]=(value>>1)&1;setting[2]=(value>>2)&1;return value;}
int set_one(unsigned index,unsigned value){return set_mechanism(index,value);}
int collision_equivalence(void){unsigned a,i,v;int x,y,old=room;for(a=54;a<=61;a++){const ReturnArtRoom*r=&return_art_rooms[a-54];room=a;for(v=0;v<8;v++){mask_setting(v);short dr[2][4];unsigned n=dynamic_rects(a,setting,dr);for(y=-6;y<r->height+6;y++)for(x=-6;x<r->width+6;x++){int expected=x<5||y<5||x>r->width-6||y>r->height-6;for(i=0;i<r->solid_count;i++){const ReturnArtRect*s=&r->solids[i];if(x+5>=s->x&&x-5<s->x+s->w&&y+5>=s->y&&y-5<s->y+s->h)expected=1;}for(i=0;i<n;i++)if(rect_hit(x,y,dr[i]))expected=1;if(return_game_solid(x,y)!=expected){room=old;return a;}}}}room=old;return 0;}
int reference_ray(int x,int y,int tx,int ty){int dx=ab(tx-x),dy=-ab(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,e=dx+dy;if(return_game_solid(x,y)||return_game_solid(tx,ty)||dx-dy>160)return 0;while(x!=tx||y!=ty){int twice=e*2,nx=x,ny=y;if(twice>=dy){e+=dy;nx+=sx;}if(twice<=dx){e+=dx;ny+=sy;}if(return_game_solid(nx,y)||return_game_solid(x,ny)||return_game_solid(nx,ny))return 0;x=nx;y=ny;}return 1;}
unsigned draw(unsigned a,int cx,int cy){room=a;camera_x=cx;camera_y=cy;actors=0;return_game_draw_actors();return_game_draw_overlay();return actors;}
unsigned trial_index(void){return return_game_trial.index;}
unsigned trial_stage(void){return return_game_trial.stage;}
unsigned repeat_status(void){return repeat_stage;}
unsigned phase(void){return phase_step;}

unsigned confirmation(void){return invite_confirm;}
unsigned attempt_id(void){return attempt;}
unsigned room_scene(void){return scene;}
unsigned repeat_source(void){return repeat_active;}
unsigned trial_casts(void){return return_game_trial.casts;}
/* Emulate the engine's normal modal freeze: no simulation while viewing.
 * No actual selection notification is delivered unless an edit occurs. */
void view_roundtrip(unsigned mode){int old=game_state;if(mode==0){game_state=3;return_game_input(0,0);return_game_tick();game_state=old;}else{ /* Picker leaves PLAY but skips all simulation. */ return_game_input(0,0); } }
