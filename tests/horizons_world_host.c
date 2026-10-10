/* Synthetic host input and tagged field callbacks; NOT native acquisition evidence. */
#include <string.h>
#include "horizons_game.h"
#include "horizons_art.h"
#include "horizons_creature_art.h"
#include "horizons_quests.h"
#include "progression.h"
Save5State adventure_save;
unsigned progression_revision;
volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
int face,keys,journal_tab;
int horizons_power_kind,horizons_power_time,horizons_power_form,horizons_power_direction,horizons_power_origin_x,horizons_power_origin_y,horizons_power_age,horizons_power_cooldown,horizons_power_cast_time,horizons_power_phase;
static unsigned last_toast,actors,saved,geometry_changes,power_beat=1,power_release,mock_token,mock_id;
int return_power_kind,return_power_time,return_power_form,return_power_direction,return_power_origin_x,return_power_origin_y;
static Save5State snapshot;
static int actor_x[32],actor_y[32];static unsigned actor_calls;
unsigned char world_bitmap[240*160] __attribute__((aligned(4)));static unsigned bitmap_active;
unsigned short*screen=(unsigned short*)world_bitmap;
#define HZ_COPY_HALFWORDS(source,destination,count) memcpy((destination),(source),(count)*2u)
static void pixel(int x,int y,unsigned char c){if(bitmap_active&&(unsigned)x<240u&&(unsigned)y<160u)world_bitmap[y*240+x]=c;}
static void sprite_pixels(const unsigned char*p,int x,int y){if(!bitmap_active||!p)return;for(int yy=0;yy<16;yy++)for(int xx=0;xx<16;xx++)if(p[yy*16+xx])pixel(x-camera_x-8+xx,y-camera_y-8+yy,p[yy*16+xx]);}
CreatureInstance*progression_selected(void){unsigned p=adventure_save.roster.selected_party,s;if(p>=4)return 0;s=adventure_save.roster.party[p];return s<160?&adventure_save.roster.instances[s]:0;}
unsigned progression_command(void){CreatureInstance*c=progression_selected();return c?c->equipped[c->selected_command]:0;}
void progression_refresh(void){progression_revision++;}
void save_game(void){saved++;}
void dialogue(int a,int b,int c){(void)a;(void)b;(void)c;game_state=2;}
void toast(int a){last_toast=(unsigned)a;}
void text(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void centered(int a,int b,int c){(void)a;(void)b;(void)c;}
void box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void rect(int a,int b,int c,int d,unsigned char e){if(bitmap_active)for(int y=b;y<b+d;y++)for(int x=a;x<a+c;x++)pixel(x,y,e);}
void sprite(const unsigned char*p,int x,int y,int w,int h,int flip){if(bitmap_active)for(int yy=0;yy<h;yy++)for(int xx=0;xx<w;xx++){unsigned char c=p[yy*w+(flip?w-1-xx:xx)];if(c)pixel(x+xx,y+yy,c);}}
void line(int x,int y,int tx,int ty,int color){if(bitmap_active){int ax=x<tx?tx-x:x-tx,ay=-(y<ty?ty-y:y-ty),sx=x<tx?1:-1,sy=y<ty?1:-1,e=ax+ay;for(;;){int q;pixel(x,y,color);if(x==tx&&y==ty)break;q=e*2;if(q>=ay){e+=ay;x+=sx;}if(q<=ax){e+=ax;y+=sy;}}}}
void horizons_actor(unsigned a,int x,int y){if(a<20)sprite_pixels(horizons_sprites[a],x,y);if(actor_calls<32){actor_x[actor_calls]=x;actor_y[actor_calls++]=y;}if(x-camera_x>=-8&&x-camera_x<248&&y-camera_y>=-8&&y-camera_y<168)actors++;}
void region_form_actor(unsigned a,int x,int y){horizons_actor(a,x,y);sprite_pixels(horizons_creature_art_frame(a,0,0),x,y);}
void game_health_fill(void){}
void horizons_audio_tick(void){}
void game_horizons_performance_start(void){}
void game_horizons_performance_stop(void){}
void return_powers_geometry_changed(void){geometry_changes++;}
void horizons_powers_geometry_changed(void){geometry_changes++;}
unsigned horizons_powers_beat(void){return power_beat;}
unsigned horizons_powers_release_phase(void){return power_release;}
int horizons_powers_busy(void){return horizons_power_kind!=0;}
unsigned horizons_powers_cast_token(void){return mock_token;}
unsigned horizons_powers_caster_id(void){return mock_id;}
int return_powers_busy(void){return return_power_kind!=0;}
unsigned return_powers_cast_token(void){return mock_token;}
unsigned return_powers_caster_id(void){return mock_id;}
int game_region_actor_overlap(int x0,int y0,int x1,int y1){return px+6>=x0&&px-6<=x1&&py+6>=y0&&py-6<=y1;}
void game_region_warp(int x,int y){if(!horizons_game_solid(x,y)){px=x;py=y;}}
void enter_room(int r,int s){if(r>=62){int q=horizons_game_request_enter(r,s);if(q==1)horizons_game_enter(r,s);}else{horizons_game_reset();room=r;checkpoint_spawn=s;adventure_save.campaign.room=r;adventure_save.campaign.spawn=s;}}
#include "../src/horizons_game.c"
int settle(void){unsigned n=0,a,s;while(horizons_game_event_pending()&&n++<2000)if(horizons_game_prepare_event()==SAVE5_FAILED)return 0;if(n>=2000)return 0;if(horizons_game_take_transition(&a,&s))enter_room(a,s);game_state=1;return save5_validate(&adventure_save);}
int fresh(void){room=0;horizons_game_reset();save5_test_reset_writer();save5_test_fail_after(-1);memset(&adventure_save,0,sizeof adventure_save);if(!save5_load(&adventure_save))return 0;room=adventure_save.campaign.room;checkpoint_spawn=adventure_save.campaign.spawn;game_state=summoned=1;face=1;keys=transition_lock=camera_x=camera_y=0;last_toast=actors=saved=geometry_changes=0;power_beat=1;power_release=0;return save5_validate(&adventure_save);}
void at(int x,int y,int f){px=x;py=y;face=f;game_state=1;keys=0;}
void old_room(unsigned r,unsigned spawn){room=r;horizons_game_reset();checkpoint_spawn=spawn;adventure_save.campaign.room=r;adventure_save.campaign.spawn=spawn;game_state=1;}
int entry(unsigned r,unsigned s){game_state=1;int q=horizons_game_request_enter(r,s);if(q==1)return horizons_game_enter(r,s);if(q==2)return settle();return 0;}
unsigned qs(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
unsigned qo(unsigned q){return adventure_save.quests.objectives[q];}
unsigned get_toast(void){return last_toast;}
int valid(void){return save5_validate(&adventure_save);}
unsigned select_form(unsigned f,unsigned command){unsigned i,j;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==f){for(j=0;j<4;j++)if(adventure_save.roster.party[j]==i)break;if(j<4){unsigned tmp=adventure_save.roster.party[0];adventure_save.roster.party[0]=i;adventure_save.roster.party[j]=tmp;}else adventure_save.roster.party[0]=i;adventure_save.roster.selected_party=0;CreatureInstance*c=&adventure_save.roster.instances[i];if(!creatures_equip(c,0,command))return 254;c->selected_command=0;horizons_game_selection_changed();return i;}return 255;}
unsigned action(void){CreatureInstance*c=active();power_beat=1;power_release=0;mock_id=c?c->instance_id:0;horizons_power_kind=return_power_kind=progression_command();horizons_power_form=return_power_form=c?c->form_id:0;horizons_power_direction=return_power_direction=face;horizons_power_origin_x=return_power_origin_x=px;horizons_power_origin_y=return_power_origin_y=py;mock_token=horizons_game_action_begin(3);return mock_token;}
int hit(unsigned i,unsigned token,unsigned beat,unsigned release){CreatureInstance*c=active();power_beat=beat;power_release=release;horizons_power_kind=progression_command();return c?horizons_game_field_hit(i,progression_command(),c->instance_id,c->form_id,token):0;}
int synthetic_field(unsigned i){return hit(i,action(),1,0);}
unsigned count(void){return creatures_roster_count(&adventure_save.roster);}
unsigned trial_mask(unsigned slot){return adventure_save.roster.instances[slot].trial_flags;}
unsigned level(unsigned slot){return adventure_save.roster.instances[slot].level;}
unsigned bond(unsigned slot){return adventure_save.roster.instances[slot].bond;}
void snapshot_state(void){snapshot=adventure_save;}
int unchanged(void){return !memcmp(&snapshot,&adventure_save,sizeof snapshot);}
void tick(void){horizons_game_tick();}
int evolve(unsigned slot,unsigned to){return creatures_evolve_to(&adventure_save.roster,slot,to,horizons_context(&adventure_save),1,1);}
unsigned get_setting(unsigned i){return i<16?setting[i]:255;}
unsigned get_mode(void){return proof.mode;}
unsigned get_stage(void){return proof.stage;}
unsigned get_walk(void){return proof.walk;}
unsigned confirmation(void){return invite_confirm;}
unsigned attempt_id(void){return attempt;}
unsigned cast_id(void){return cast.token;}
unsigned draw(unsigned a,int cx,int cy){room=a;camera_x=cx;camera_y=cy;actors=actor_calls=0;horizons_game_draw_actors();horizons_game_draw_overlay();return actors;}
int collision_equivalence(void){unsigned a,i,v;int x,y,old=room;for(a=62;a<=69;a++){const HorizonsArtRoom*r=&horizons_art_rooms[a-62];room=a;for(v=0;v<(a==63?4:1);v++){carriage_x=192+v*32;for(y=-6;y<r->height+6;y++)for(x=-6;x<r->width+6;x++){int expected=x<5||y<5||x>r->width-6||y>r->height-6;for(i=0;i<r->solid_count;i++){const HorizonsArtRect*s=&r->solids[i];if(x+5>=s->x&&x-5<s->x+s->w&&y+5>=s->y&&y-5<s->y+s->h)expected=1;}if(dynamic_solid(x,y))expected=1;if(horizons_game_solid(x,y)!=expected){room=old;return a;}}}}room=old;return 0;}

int actor_at(int x,int y){unsigned i;for(i=0;i<actor_calls;i++)if(actor_x[i]==x&&actor_y[i]==y)return 1;return 0;}

void render_bitmap(int cx,int cy){const HorizonsArtRoom*r=&horizons_art_rooms[room-62];camera_x=cx;camera_y=cy;for(int y=0;y<160;y++)for(int x=0;x<240;x++)world_bitmap[y*240+x]=r->bitmap[(cy+y)*r->width+cx+x];bitmap_active=1;horizons_game_draw_overlay();horizons_game_draw_actors();bitmap_active=0;}

void aim_effect(unsigned dir){horizons_power_direction=return_power_direction=dir;}
void corrupt_effect_origin(void){horizons_power_origin_x++;return_power_origin_x++;}
