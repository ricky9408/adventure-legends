/* Synthetic controller positions/effect certificates; real world and save jobs.
 * These tests establish host contracts, never native acquisition or pacing. */
#include <string.h>
#include "covenants_game.h"
#include "covenants_art.h"
#include "covenants_quests.h"
#include "covenants_powers.h"
#include "progression.h"
Save5State adventure_save;
unsigned progression_revision;
static unsigned short display[240*160/2];
unsigned short*screen=display;
int progression_name_id(unsigned form){return (int)form;}
volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
int face,keys,journal_tab;
int horizons_power_kind,horizons_power_form,horizons_power_direction,horizons_power_origin_x,horizons_power_origin_y;
int return_power_kind,return_power_form,return_power_direction,return_power_origin_x,return_power_origin_y;
static unsigned last_toast,toast_count,saved,geometry_changes,power_beat=1,power_release,mock_token,mock_id,overlap=1,enemy_count;
static CovenantsPowerProof power_proof;
CreatureInstance*progression_selected(void){unsigned p=adventure_save.roster.selected_party,s;if(p>=4)return 0;s=adventure_save.roster.party[p];return s<160?&adventure_save.roster.instances[s]:0;}
unsigned progression_command(void){CreatureInstance*c=progression_selected();return c&&c->selected_command<2?c->equipped[c->selected_command]:0;}
void progression_refresh(void){progression_revision++;}
void save_game(void){saved++;}
void dialogue(int a,int b,int c){(void)a;(void)b;(void)c;game_state=2;}
void toast(int a){last_toast=(unsigned)a;toast_count++;}
void text(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void centered(int a,int b,int c){(void)a;(void)b;(void)c;}
void box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void rect(int a,int b,int c,int d,unsigned char e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void sprite(const unsigned char*a,int b,int c,int d,int e,int f){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;}
void line(int a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void covenants_actor(unsigned a,int x,int y){(void)a;(void)x;(void)y;}
void region_form_actor(unsigned a,int x,int y){(void)a;(void)x;(void)y;}
void game_health_fill(void){}
void return_powers_geometry_changed(void){geometry_changes++;}
void horizons_powers_geometry_changed(void){geometry_changes++;}
void covenants_powers_geometry_changed(void){geometry_changes++;}
unsigned horizons_powers_beat(void){return power_beat;}
unsigned horizons_powers_release_phase(void){return power_release;}
int horizons_powers_busy(void){return horizons_power_kind!=0;}
unsigned horizons_powers_cast_token(void){return mock_token;}
unsigned horizons_powers_caster_id(void){return mock_id;}
int return_powers_busy(void){return return_power_kind!=0;}
unsigned return_powers_cast_token(void){return mock_token;}
unsigned return_powers_caster_id(void){return mock_id;}
unsigned covenants_powers_beat(void){return power_beat;}
unsigned covenants_powers_release_phase(void){return power_release;}
const CovenantsPowerProof*covenants_powers_proof(void){return mock_token?&power_proof:0;}
int horizons_powers_overlap(int x,int y,int r){(void)x;(void)y;(void)r;return (int)overlap;}
int return_powers_overlap(int x,int y,int r){(void)x;(void)y;(void)r;return (int)overlap;}
int covenants_powers_overlap(int x,int y,int r){(void)x;(void)y;(void)r;return overlap!=0;}
int game_region_actor_overlap(int x0,int y0,int x1,int y1){return px+6>=x0&&px-6<=x1&&py+6>=y0&&py-6<=y1;}
void game_region_warp(int x,int y){if(!covenants_game_solid(x,y)){px=x;py=y;}}
int game_covenants_spawn_wave(unsigned wave){enemy_count=wave?wave+1:0;return 1;}
unsigned game_covenants_enemies_alive(void){return enemy_count;}
int solid(int x,int y){(void)x;(void)y;return 0;}
void enter_room(int r,int s){if(r>=70){int q=covenants_game_request_enter(r,s);if(q==1)covenants_game_enter(r,s);}else{covenants_game_reset();room=r;checkpoint_spawn=s;adventure_save.campaign.room=r;adventure_save.campaign.spawn=s;}}
#include "covenants_world_source.inc"
int settle(void){unsigned n=0,a,s;while(covenants_game_event_pending()&&n++<2000)if(covenants_game_prepare_event()==SAVE5_FAILED)return 0;if(n>=2000)return 0;if(covenants_game_take_transition(&a,&s))enter_room(a,s);game_state=1;return save5_validate(&adventure_save);}
void fresh_world(void){room=adventure_save.campaign.room;checkpoint_spawn=adventure_save.campaign.spawn;covenants_game_reset();game_state=summoned=1;face=1;keys=transition_lock=camera_x=camera_y=0;last_toast=toast_count=saved=geometry_changes=0;power_beat=1;power_release=0;overlap=1;}
void at(int x,int y,int f){px=x;py=y;face=f;game_state=1;keys=0;}
int entry(unsigned r,unsigned s){game_state=1;int q=covenants_game_request_enter(r,s);if(q==1)return covenants_game_enter(r,s);if(q==2)return settle();return 0;}
unsigned get_toast(void){return last_toast;}
unsigned get_toast_count(void){return toast_count;}
unsigned get_blocked_ticks(void){return npc_blocked_ticks;}
unsigned select_form(unsigned f,unsigned command){unsigned i,j;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==f){for(j=0;j<4;j++)if(adventure_save.roster.party[j]==i)break;if(j<4){unsigned tmp=adventure_save.roster.party[0];adventure_save.roster.party[0]=i;adventure_save.roster.party[j]=tmp;}else adventure_save.roster.party[0]=i;adventure_save.roster.selected_party=0;CreatureInstance*c=&adventure_save.roster.instances[i];if(!creatures_equip(c,0,command))return 254;c->selected_command=0;covenants_game_selection_changed();return i;}return 255;}
unsigned action(void){CreatureInstance*c=active();power_beat=1;power_release=0;mock_id=c?c->instance_id:0;horizons_power_kind=return_power_kind=progression_command();horizons_power_form=return_power_form=c?c->form_id:0;horizons_power_direction=return_power_direction=face;horizons_power_origin_x=return_power_origin_x=px;horizons_power_origin_y=return_power_origin_y=py;mock_token=covenants_game_action_begin(3);memset(&power_proof,0,sizeof power_proof);power_proof.token=mock_token;power_proof.caster=mock_id;power_proof.form=c?c->form_id:0;power_proof.command=progression_command();power_proof.origin_x=px;power_proof.origin_y=py;power_proof.direction=face;power_proof.scene=scene;power_proof.attempt=attempt;power_proof.geometry=geometry;return mock_token;}
int hit(unsigned i,unsigned token,unsigned beat,unsigned release){CreatureInstance*c=active();power_beat=beat;power_release=release;return c?covenants_game_field_hit(i,progression_command(),c->instance_id,c->form_id,token):0;}
void tick(unsigned n){while(n--)covenants_game_tick();}
unsigned get_setting(unsigned i){return i<24?setting[i]:255;}
unsigned get_mode(void){return practice_mode;}
unsigned get_stage(void){return npc_stage;}
int get_npc_x(void){return npc_x;}
int get_npc_y(void){return npc_y;}
int get_moving_x(void){return moving_x;}
unsigned get_moving_state(void){return moving_state;}
unsigned get_practice_ticks(void){return practice_ticks;}
unsigned confirmation(unsigned which){return which==0?reset_confirm:which==1?invite_confirm:porch_confirm;}
unsigned cast_id(void){return cast.token;}
unsigned world_bytes(void){return sizeof setting+sizeof reset_confirm+sizeof invite_confirm+sizeof porch_confirm+sizeof dirty+sizeof transition_area+sizeof transition_spawn+sizeof transition_ready+sizeof moving_x+sizeof npc_x+sizeof npc_y+sizeof movement_ticks+sizeof practice_ticks+sizeof moving_state+sizeof npc_stage+sizeof practice_mode+sizeof escort_stage+sizeof npc_walk_recent+sizeof npc_walk_phase+sizeof npc_blocked_ticks+sizeof heat_token+sizeof work_area+sizeof cast+sizeof events+sizeof event_handle+sizeof event_scene+sizeof event_attempt+sizeof event_count+sizeof event_index+7*sizeof(unsigned);}
/* Negative controls deliberately mutate owner/proof independently of world. */
void fault(unsigned k){switch(k){case 0:mock_token++;power_proof.token++;break;case 1:mock_id++;power_proof.caster++;break;case 2:horizons_power_origin_x++;return_power_origin_x++;power_proof.origin_x++;break;case 3:geometry_changed();break;case 4:next_generation(&scene);break;case 5:next_generation(&attempt);break;case 6:overlap=0;break;case 7:horizons_power_kind=return_power_kind=0;mock_token=0;break;case 8:horizons_power_direction=return_power_direction=4;power_proof.direction=4;break;}}
void enemies_clear(void){enemy_count=0;}

void adopt_fixture(unsigned source_scene){scene=source_scene;fresh_world();}
