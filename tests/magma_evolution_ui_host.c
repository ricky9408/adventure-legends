/* Explicit synthetic host bridge for production progression.c.
 * Core, catalog, quests, save reader, generated text and portraits are real.
 * Engine globals, sound/save requests and framebuffer writes are host stubs.
 * This is not a controller, emulator, native acquisition or timing test. */
#include <string.h>
#include <stdint.h>
#include "progression.h"
#include "ui.h"
#include "assets.h"
#include "magma_creature_art.h"

volatile int room,px,py,spirit,game_state,has_save,save_failed;
volatile unsigned chapter_flags;
int journal_tab,frame,ability_cd,heal_cd,gfx_companion_frame,checkpoint_spawn;
unsigned host_saves,host_toast,host_sounds,host_fallbacks,host_bad_bounds;
unsigned host_roster_checks,host_catalog_checks,host_admission_checks,host_commits;
unsigned char host_pixels[240*160];
typedef struct {int kind,id,x,y,w,h,color;} HostDraw;
HostDraw host_draws[128];
unsigned host_draw_count;
static Save5State snapshot;
static const unsigned char fallback[256]={1};

/* Only creatures.c is built with instrumentation. Counts include internal
 * calls, so an accidentally introduced full validation cannot hide in a helper. */
void __attribute__((no_instrument_function)) __cyg_profile_func_enter(void *fn,void *caller){
 (void)caller;
 if(fn==(void*)(uintptr_t)creatures_roster_validate)host_roster_checks++;
 if(fn==(void*)(uintptr_t)creatures_catalog_validate)host_catalog_checks++;
 if(fn==(void*)(uintptr_t)creatures_can_evolve_roster_to)host_admission_checks++;
 if(fn==(void*)(uintptr_t)creatures_evolve_to)host_commits++;
}
void __attribute__((no_instrument_function)) __cyg_profile_func_exit(void *fn,void *caller){(void)fn;(void)caller;}
static void draw(int kind,int id,int x,int y,int w,int h,int col){
 if(x<0||y<0||w<0||h<0||x+w>240||y+h>160)host_bad_bounds++;
 if(host_draw_count<128)host_draws[host_draw_count++]=(HostDraw){kind,id,x,y,w,h,col};
}
static void pixel(int x,int y,unsigned char c){if((unsigned)x<240&&(unsigned)y<160)host_pixels[y*240+x]=c;else host_bad_bounds++;}
void rect(int x,int y,int w,int h,unsigned char c){int xx,yy;draw(0,0,x,y,w,h,c);for(yy=0;yy<h;yy++)for(xx=0;xx<w;xx++)pixel(x+xx,y+yy,c);}
void box(int x,int y,int w,int h){rect(x,y,w,h,1);rect(x,y,w,1,PAL_GOLD2);rect(x,y+h-1,w,1,PAL_GOLD2);rect(x,y,1,h,PAL_GOLD2);rect(x+w-1,y,1,h,PAL_GOLD2);}
void text(int id,int x,int y,int col){
 const UiText*t;const UiRun*r;unsigned i,j;
 if(id<0||id>=TX_COUNT){host_bad_bounds++;return;}
 t=&ui_texts[id];draw(1,id,x,y,t->width,t->height,col);r=t->runs[x&1];
 /* The engine's text offsets address pixel pairs on a120-pair scanline. */
 for(i=0;i<t->count[x&1];i++)for(j=0;j<r[i].count;j++){
  int pair=y*120+(x>>1)+r[i].offset+(int)j;
  if(r[i].mask&1)pixel((pair%120)*2,pair/120,(unsigned char)col);
  if(r[i].mask&2)pixel((pair%120)*2+1,pair/120,(unsigned char)col);
 }
}
void centered(int id,int y,int col){if(id<0||id>=TX_COUNT){host_bad_bounds++;return;}text(id,(240-ui_texts[id].width)/2,y,col);}
void sprite(const unsigned char*p,int x,int y,int w,int h,int flash){
 unsigned i;int xx,yy,form=0;(void)flash;
 for(i=0;i<MAGMA_CREATURE_ART_COUNT;i++)if(p==magma_creature_portraits[i])form=magma_creature_form_ids[i];
 draw(2,form,x,y,w,h,0);
 if(!p){host_bad_bounds++;return;}
 for(yy=0;yy<h;yy++)for(xx=0;xx<w;xx++)if(p[yy*w+xx])pixel(x+xx,y+yy,p[yy*w+xx]);
}
const unsigned char*companion_form_pixels(unsigned form,unsigned direction,unsigned frame_id){(void)form;(void)direction;(void)frame_id;host_fallbacks++;return fallback;}
void toast(int id){host_toast=(unsigned)id;}
void save_game(void){host_saves++;}
void sfx(int id){host_sounds|=1u<<(unsigned)id;}

void host_reset_draw(void){memset(host_pixels,0,sizeof host_pixels);host_draw_count=host_bad_bounds=host_fallbacks=0;}
void host_reset_counts(void){host_roster_checks=host_catalog_checks=host_admission_checks=host_commits=0;}
void host_context(unsigned bits){
 save5_quest_set_state(&adventure_save.quests,30,bits&256?3:0);
 save5_quest_set_state(&adventure_save.quests,31,bits&256?3:0);
 save5_quest_set_state(&adventure_save.quests,32,bits&512?3:0);
}
unsigned host_add(unsigned form,unsigned trial){
 unsigned slot=creatures_grant(&adventure_save.roster,form,50,100,0,0);
 if(slot<160)adventure_save.roster.instances[slot].trial_flags=(CreatureU16)trial;
 return slot;
}
int host_fresh(unsigned form,unsigned trial,unsigned context){
 memset(&adventure_save,0,sizeof adventure_save);creatures_roster_init(&adventure_save.roster);
 room=38;px=120;py=120;spirit=0;game_state=3;chapter_flags=0;journal_tab=3;
 host_saves=host_sounds=0;host_toast=0xffffffffu;
 if(host_add(form,trial)!=0)return 0;
 host_context(context);progression_refresh();host_reset_draw();host_reset_counts();
 return creatures_roster_validate(&adventure_save.roster);
}
int host_load_fixture(void){
 save5_test_reset_writer();save5_test_fail_after(-1);
 if(!progression_load())return 0;
 room=(int)adventure_save.campaign.room;chapter_flags=adventure_save.campaign.chapter_flags;
 journal_tab=3;game_state=3;host_reset_draw();host_reset_counts();return save5_validate(&adventure_save);
}
unsigned host_form(unsigned slot){return slot<160?adventure_save.roster.instances[slot].form_id:0;}
unsigned host_identity(unsigned slot){return slot<160?adventure_save.roster.instances[slot].instance_id:0;}
unsigned host_trial(unsigned slot){return slot<160?adventure_save.roster.instances[slot].trial_flags:0;}
unsigned host_count(void){return creatures_roster_count(&adventure_save.roster);}
unsigned host_excess(void){CreatureCoverage c;return creatures_collection_coverage(&adventure_save.roster,&c)?c.excess:999;}
int host_valid(void){return creatures_roster_validate(&adventure_save.roster);}
void host_snapshot(void){snapshot=adventure_save;}
int host_unchanged(void){return !memcmp(&snapshot,&adventure_save,sizeof snapshot);}
int host_instance_unchanged(unsigned slot){return slot<160&&!memcmp(&snapshot.roster.instances[slot],&adventure_save.roster.instances[slot],sizeof(CreatureInstance));}
void host_select(unsigned slot){unsigned i;for(i=0;i<4;i++)if(adventure_save.roster.party[i]==slot){adventure_save.roster.selected_party=(CreatureU8)i;return;}adventure_save.roster.party[0]=(CreatureU8)slot;adventure_save.roster.selected_party=0;}
void host_mutate(unsigned kind,unsigned slot,unsigned value){
 CreatureInstance*c=slot<160?&adventure_save.roster.instances[slot]:0;
 if(kind==0&&c)c->instance_id=value;
 if(kind==1&&c){const CreatureForm*f=creatures_form(value);c->form_id=(CreatureU8)value;if(f)c->polarity=f->polarity;}
 if(kind==2)adventure_save.roster.selected_party=(CreatureU8)value;
 if(kind==3&&c)c->flags=(CreatureU8)value;
 if(kind==4&&c){c->level=(CreatureU8)value;c->xp=creatures_xp_threshold(value);}
 if(kind==5&&c)c->bond=(CreatureU8)value;
 if(kind==6&&c)c->trial_flags=(CreatureU16)value;
 if(kind==7&&c)c->selected_command=(CreatureU8)value;
}
unsigned host_status(unsigned slot,unsigned target){return creatures_can_evolve_roster_to(&adventure_save.roster,slot,target,progression_evolution_context(),progression_is_sanctuary());}
unsigned host_evolve(unsigned slot,unsigned target){return creatures_evolve_to(&adventure_save.roster,slot,target,progression_evolution_context(),progression_is_sanctuary(),1);}
unsigned host_name(unsigned form){return (unsigned)progression_name_id(form);}
unsigned host_reason_name(unsigned reason){static const unsigned ids[]={TX_E_READY,TX_E_NO_MEMBER,TX_E_GROWN,TX_E_LEVEL_MORE,TX_E_BOND_MORE,TX_E_MG_MORE,TX_E_TRIAL_MORE,TX_E_SANCTUARY,TX_E_NO_MEMBER,TX_E_CHOOSE_BRANCH,TX_E_SPACE_RESERVED};return reason<sizeof ids/sizeof ids[0]?ids[reason]:TX_E_NO_MEMBER;}
unsigned host_source_changed_name(void){return TX_E_SOURCE_CHANGED;}
