/* Synthetic host bridge; real runtime, quest, catalog and save modules. */

#include <string.h>
#include <limits.h>
#include "magma_game.h"
#include "assets.h"
#include "magma_art.h"
#include "magma_quests.h"
#include "progression.h"
Save5State adventure_save;
unsigned progression_revision,progression_forms[PROGRESSION_SPIRIT_COUNT];
volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
volatile unsigned chapter_flags;
int face,keys,journal_tab;
static unsigned saved,invalid,hurt_calls,actors,last_toast,weapon_class=1;
static int overlay_sweep_x=-1,overlay_sweep_y=-1;
static unsigned host_save_queued,host_auto_settle=1,anchor_prepare_calls,host_save_writes,health_fills;
static int host_finish_save(void);
unsigned camera_maxima[8];
static Save5State snapshot;
CreatureInstance *progression_selected(void){unsigned p=adventure_save.roster.selected_party,s;if(p>=4)return 0;s=adventure_save.roster.party[p];return s<160?&adventure_save.roster.instances[s]:0;}
unsigned progression_command(void){CreatureInstance*c=progression_selected();return c?c->equipped[c->selected_command]:0;}
void progression_refresh(void){progression_revision++;}
/* Synthetic scheduler: queue first, let rest restore its staged spawn byte,
 * then finish from a later helper boundary in frozen SAVE_PENDING mode. */
void save_game(void){saved++;adventure_save.campaign.room=(Save4U8)room;adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;host_save_queued=1;}
static int host_finish_save(void){int oldstate=game_state;if(!host_save_queued)return 1;game_state=6;
 if(magma_game_save_prepare_pending()&&!magma_game_prepare_save()){host_save_queued=0;invalid++;game_state=oldstate;return 0;}
 if(!save5_validate(&adventure_save)||!save5_store(&adventure_save)){host_save_queued=0;invalid++;game_state=oldstate;return 0;}
 host_save_queued=0;host_save_writes++;game_state=oldstate;return 1;
}
void dialogue(int a,int b,int c){(void)a;(void)b;(void)c;game_state=2;}
void toast(int a){last_toast=(unsigned)a;}
void text(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void centered(int a,int b,int c){(void)a;(void)b;(void)c;}
void box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;}
void rect(int a,int b,int c,int d,unsigned char e){if(c==12&&d==18&&e==PAL_ROSE4){overlay_sweep_x=a;overlay_sweep_y=b;}}
void line(int a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;}
void magma_actor(unsigned a,int x,int y){(void)a;if(x-camera_x>-8&&x-camera_x<248&&y-camera_y>-8&&y-camera_y<168)actors++;}
void region_form_actor(unsigned a,int x,int y){magma_actor(a,x,y);}
void game_health_fill(void){health_fills++;}
void game_region_warp(int x,int y){px=x;py=y;}
unsigned game_weapon_class(void){return weapon_class;}
void game_north_hurt(unsigned d){hurt_calls+=d;}
void enter_room(int r,int s){if(r>=38)magma_game_enter((unsigned)r,(unsigned)s);else{room=r;checkpoint_spawn=s;}}
int fresh(void){magma_game_reset();host_save_queued=anchor_prepare_calls=host_save_writes=health_fills=0;host_auto_settle=1;save5_test_reset_writer();save5_test_fail_after(-1);memset(&adventure_save,0,sizeof adventure_save);if(!save5_load(&adventure_save))return 0;chapter_flags=adventure_save.campaign.chapter_flags;room=adventure_save.campaign.room;checkpoint_spawn=adventure_save.campaign.spawn;game_state=summoned=1;face=keys=transition_lock=camera_x=camera_y=0;saved=invalid=hurt_calls=actors=0;weapon_class=1;magma_game_reset();return save5_validate(&adventure_save);}
void at(int x,int y){if(host_auto_settle)host_finish_save();px=x;py=y;game_state=1;face=1;keys=0;}
int entry(unsigned r,unsigned s){if(host_auto_settle&&!host_finish_save())return 0;game_state=1;return magma_game_enter(r,s);}
unsigned select_form(unsigned form){unsigned i,j;for(i=0;i<160;i++)if(adventure_save.roster.instances[i].form_id==form){for(j=0;j<4;j++)if(adventure_save.roster.party[j]==i)break;if(j<4){unsigned t=adventure_save.roster.party[0];adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.party[j]=(CreatureU8)t;}else adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.selected_party=0;return i;}return 255;}
void select_slot(unsigned i){unsigned j;for(j=0;j<4;j++)if(adventure_save.roster.party[j]==i)break;if(j<4){unsigned t=adventure_save.roster.party[0];adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.party[j]=(CreatureU8)t;}else adventure_save.roster.party[0]=(CreatureU8)i;adventure_save.roster.selected_party=0;}
unsigned duplicate(unsigned form){return creatures_grant(&adventure_save.roster,form,18,20,0,0);}
unsigned qs(unsigned q){return save5_quest_state(&adventure_save.quests,q);}
unsigned qo(unsigned q){return adventure_save.quests.objectives[q];}
unsigned source(unsigned t){return magma_source_claimed(&adventure_save,t);}
unsigned flags(unsigned b){return adventure_save.quests.region_flags[b];}
unsigned roster_count(void){return creatures_roster_count(&adventure_save.roster);}
unsigned invalid_saves(void){return invalid;}
int valid(void){return save5_validate(&adventure_save);}
void snapshot_state(void){snapshot=adventure_save;}
int unchanged(void){return !memcmp(&snapshot,&adventure_save,sizeof snapshot);}
int roundtrip(void){Save5State r;if(!host_finish_save())return 0;if(!save5_store(&adventure_save)||!save5_load(&r))return 0;return !memcmp(&adventure_save.quests,&r.quests,sizeof r.quests)&&!memcmp(&adventure_save.roster,&r.roster,sizeof r.roster)&&!memcmp(&adventure_save.equipment,&r.equipment,sizeof r.equipment);}
void tick(unsigned n){while(n--)magma_game_tick();}
void modal(unsigned m){game_state=(int)m;}
void summon(unsigned m){summoned=(int)m;}
void weapon(unsigned w){weapon_class=w;}
unsigned hurt(void){return hurt_calls;}
unsigned draw(int x,int y){actors=0;camera_x=x;camera_y=y;magma_game_draw_actors();magma_game_draw_overlay();magma_game_draw_journal();return actors;}
void direction(int k){keys=k;game_state=1;}
unsigned trial(unsigned slot){return slot<160?adventure_save.roster.instances[slot].trial_flags:0;}
unsigned level(unsigned slot){return slot<160?adventure_save.roster.instances[slot].level:0;}
unsigned bond(unsigned slot){return slot<160?adventure_save.roster.instances[slot].bond:0;}
unsigned encounter_spawns(unsigned area){const MagmaEnemySpawn*e;unsigned n=magma_game_enemy_spawns(area,&e),i;int oldroom=room;room=(int)area;for(i=0;i<n;i++)if(magma_game_solid(e[i].x,e[i].y)||e[i].phase>=5||(e[i].kind!=0&&e[i].kind!=2)||!e[i].hp){room=oldroom;return 255;}room=oldroom;return n;}
unsigned max_camera_actors(void){const MagmaEnemySpawn*e;unsigned n=magma_game_enemy_spawns((unsigned)room,&e),i,max=0;int x,y,mx=room<40?240:0,my=room<40?160:0;for(y=0;y<=my;y++)for(x=0;x<=mx;x++){unsigned count=draw(x,y);for(i=0;i<n;i++)if(e[i].kind==2&&e[i].x-x>-8&&e[i].x-x<248&&e[i].y-y>-8&&e[i].y-y<168)count++;if(count>max)max=count;}if(room>=38&&room<=45&&max>camera_maxima[room-38])camera_maxima[room-38]=max;return max;}
int collision_equivalence(void){unsigned a,i;int x,y,old=room;for(a=38;a<=45;a++){const MagmaArtRoom*r=&magma_art_rooms[a-38];room=(int)a;for(y=-6;y<r->height+6;y++)for(x=-6;x<r->width+6;x++){int expected=x<5||y<5||x>r->width-6||y>r->height-6;for(i=0;i<r->solid_count;i++){const MagmaArtRect*s=&r->solids[i];if(x+5>=s->x&&x-5<s->x+s->w&&y+5>=s->y&&y-5<s->y+s->h)expected=1;}if(magma_game_geometry_solid(a,x,y)!=expected){room=old;return (int)a;}}if(!magma_game_solid(INT_MIN,INT_MAX)||!magma_game_solid(INT_MAX,INT_MIN)){room=old;return -1;}}room=old;return 0;}

static unsigned blocked_actor;
int game_magma_actor_overlap(int x,int y,int r){(void)x;(void)y;(void)r;return blocked_actor;}
void set_actor_overlap(unsigned x){blocked_actor=x;}
void progression_encounter(unsigned r,unsigned e){(void)r;(void)e;}
unsigned evolve(unsigned slot,unsigned target){return creatures_evolve_to(&adventure_save.roster,slot,target,magma_context(&adventure_save),1,1);}
void facing(unsigned x){face=(int)x;}
unsigned get_toast(void){return last_toast;}
/* Synthetic extreme rosters test real gameplay wrapper failure atomicity. */
unsigned fill_reserved(void){unsigned slot,n=0;while(creatures_admission_allowed(creatures_grant_admitted(&adventure_save.roster,1,30,20,0,0,&slot)))n++;return n;}
unsigned excess(void){CreatureCoverage c;if(!creatures_collection_coverage(&adventure_save.roster,&c))return 999;return c.excess;}
unsigned fill_historical_full(void){unsigned n=0;while(creatures_grant(&adventure_save.roster,1,30,20,0,0)<160)n++;return n;}
unsigned roster_event_digest(void){unsigned i,h=0;for(i=0;i<64;i++)h=h*33u+adventure_save.roster.expedition_events[i];for(i=0;i<16;i++)h=h*33u+adventure_save.roster.lifetime_field_aid[i];return h;}

int sample_overlay_sweep(void){overlay_sweep_x=overlay_sweep_y=-1;magma_game_draw_overlay();return overlay_sweep_x;}
int sample_overlay_sweep_y(void){return overlay_sweep_y;}

/* Link-time observation wraps the real typed transaction, never stubs it. */
int __real_magma_anchor(Save5State*,unsigned);
int __wrap_magma_anchor(Save5State*s,unsigned area){anchor_prepare_calls++;return __real_magma_anchor(s,area);}
void host_set_auto_settle(unsigned n){host_auto_settle=n;}
int host_settle_save(void){return host_finish_save();}
unsigned host_anchor_calls(void){return anchor_prepare_calls;}
unsigned host_writes(void){return host_save_writes;}
unsigned host_health_fills(void){return health_fills;}
unsigned host_anchor_bits(void){return adventure_save.quests.anchors[3];}
unsigned host_campaign_spawn(void){return adventure_save.campaign.spawn;}
void host_corrupt_roster_level(void){adventure_save.roster.instances[0].level=0;}
void host_stamp_campaign(unsigned area,unsigned spawn){adventure_save.campaign.room=(Save4U8)area;adventure_save.campaign.spawn=(Save4U8)spawn;}

/* Explicit synthetic EVENT_PENDING scheduler for retained world tests.
 * Two warmup updates do no transaction work; then one actual bounded prepare
 * call runs per host update. This proves module sequencing, not native frames. */
int host_settle_event(void){unsigned step,status;
 if(!magma_game_event_pending())return 1;
 game_state=10;
 for(step=0;step<502;step++){
  if(step<2)continue;
  status=magma_game_prepare_event();
  if(status==SAVE5_BUSY)continue;
  game_state=1;
  if(status!=SAVE5_DONE)return 0;
  return magma_game_commit_event()&&!magma_game_event_pending();
 }
 magma_game_cancel_event();game_state=1;return 0;
}
