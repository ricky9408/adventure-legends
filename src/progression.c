/* Creature progression stays ROM-resident; game.c only orchestrates hooks. */
#include "progression.h"
#include "ui.h"
#include "assets.h"
#include "world.h"
#include "campaign_rules.h"
#include "evolution_art.h"
typedef unsigned char u8;
extern volatile int room,px,py,spirit,game_state,has_save,save_failed;
extern volatile unsigned chapter_flags;
extern int journal_tab,frame,ability_cd,heal_cd,gfx_companion_frame,checkpoint_spawn;
extern void text(int,int,int,int),centered(int,int,int),rect(int,int,int,int,u8),box(int,int,int,int);
extern void sprite(const u8*,int,int,int,int,int),toast(int),save_game(void),sfx(int);
extern const u8 *companion_pixels(int,int,int);
Save5State adventure_save;
unsigned progression_forms[4],progression_revision;
int save_requested,save_resume_state;
static unsigned evolution_tick,evolution_before;
#define INK 1
#define CREAM PAL_GOLD4
#define GOLD PAL_GOLD3
#define TEAL PAL_TEAL2
#define PAUSE 3
#define EVOLVE_CONFIRM 7
#define EVOLVE_ANIM 8

static int abs_i(int n){return n<0?-n:n;}
static int close_to(int x,int y,int d){return abs_i(px-x)+abs_i(py-y)<d;}
static unsigned story_slot(unsigned which){unsigned i;for(i=0;i<CREATURE_ROSTER_CAPACITY;i++)if((adventure_save.roster.instances[i].flags&CREATURE_STORY_LOCKED)&&creatures_legacy_spirit(adventure_save.roster.instances[i].form_id)==which)return i;return 255;}
CreatureInstance *progression_selected(void){unsigned i=story_slot((unsigned)spirit);return i<CREATURE_ROSTER_CAPACITY?&adventure_save.roster.instances[i]:0;}
void progression_refresh(void){unsigned i;for(i=0;i<4;i++){unsigned slot=story_slot(i);progression_forms[i]=slot<CREATURE_ROSTER_CAPACITY?adventure_save.roster.instances[slot].form_id:creature_legacy_forms[i];}progression_revision++;gfx_companion_frame=-1;}
void progression_select(unsigned which){unsigned i;for(i=0;i<4;i++){unsigned slot=adventure_save.roster.party[i];if(slot<160&&creatures_legacy_spirit(adventure_save.roster.instances[slot].form_id)==which){adventure_save.roster.selected_party=i;break;}}progression_revision++;}
void progression_new(void){unsigned i;u8*p=(u8*)&adventure_save;for(i=0;i<sizeof adventure_save;i++)p[i]=0;creatures_migrate_legacy(&adventure_save.roster,0,0);progression_refresh();save_requested=0;}
int progression_load(void){if(!save5_load(&adventure_save))return 0;progression_refresh();save_requested=0;return 1;}
void progression_story(void){unsigned i;for(i=0;i<4;i++)creatures_grant_story(&adventure_save.roster,i,chapter_flags);creatures_apply_story_floors(&adventure_save.roster,chapter_flags);progression_select((unsigned)spirit);progression_refresh();}
void progression_encounter(unsigned area,unsigned enemy){if(area<14&&enemy<6){creatures_credit_event(&adventure_save.roster,area*6+enemy,60,CREATURE_CREDIT_ENCOUNTER);progression_revision++;}}
int progression_field(unsigned event){int result=creatures_credit_event(&adventure_save.roster,CREATURE_FIELD_EVENT_BASE+event,100,CREATURE_CREDIT_FIELD_AID);if(result>0)progression_revision++;return result;}
unsigned progression_command(void){CreatureInstance*c=progression_selected();return c?c->equipped[c->selected_command]:0;}
int progression_save_begin(void){progression_select((unsigned)spirit);return save5_begin(&adventure_save);}
int progression_save_step(void){return (int)save5_step(SAVE5_RECOMMENDED_BUDGET*3);}
int progression_is_sanctuary(void){unsigned i;if(room==0)return 1;if(room==1&&close_to(WORLD_CAMP_X,WORLD_CAMP_Y,30))return 1;if(room>=4&&room<14){const CampaignRoom*r=&campaign_rooms[room-4];for(i=0;i<r->object_count;i++)if(r->objects[i].kind==9&&close_to(r->objects[i].x,r->objects[i].y,30))return 1;}return 0;}
/* Compact decimal font for dynamic values; all story text remains rasterized. */
static const u8 digits[10][5]={{7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},{5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},{7,5,7,5,7},{7,5,7,1,7}};
static void number(unsigned n,int x,int y){unsigned divisor=100;int started=0;for(;divisor;divisor/=10){unsigned d=n/divisor%10;if(d||started||divisor==1){int xx,yy;for(yy=0;yy<5;yy++)for(xx=0;xx<3;xx++)if(digits[d][yy]&(4>>xx))rect(x+xx*2,y+yy*2,2,2,CREAM);x+=8;started=1;}}}
static int name_id(unsigned form){switch(form){case 2:return TX_E_HOMURA;case 5:return TX_E_MIDORI;case 8:return TX_E_FUURI;case 11:return TX_E_KOHAKU;default:return form==1?TX_FOX:form==4?TX_LEAF:form==7?TX_C_WIND:TX_C_STONE;}}
static int reason_id(unsigned reason){switch(reason){case CREATURE_EVOLVE_READY:return TX_E_READY;case CREATURE_EVOLVE_LEVEL:return TX_E_LEVEL_MORE;case CREATURE_EVOLVE_BOND:return TX_E_BOND_MORE;case CREATURE_EVOLVE_STORY:return TX_E_STORY_MORE;case CREATURE_EVOLVE_TRIAL:return TX_E_TRIAL_MORE;case CREATURE_EVOLVE_SANCTUARY:return TX_E_SANCTUARY;default:return TX_E_GROWN;}}
void progression_draw_tab(void){CreatureInstance*c=progression_selected();const CreatureForm*f;const u8*portrait;int phase_names[]={TX_E_WOOD,TX_E_FIRE,TX_E_EARTH,TX_E_METAL,TX_E_WATER};unsigned reason;if(!c)return;f=creatures_form(c->form_id);box(8,31,224,122);centered(TX_E_GROWTH,34,GOLD);portrait=evolution_art_portrait(c->form_id);if(portrait)sprite(portrait,18,56,32,32,0);else sprite(companion_pixels(spirit,0,0),26,63,16,16,0);text(name_id(c->form_id),59,53,CREAM);text(phase_names[f->phase],59,70,TEAL);text(f->polarity==CREATURE_YIN?TX_E_YIN:TX_E_YANG,95,70,GOLD);text(TX_E_LEVEL,131,70,CREAM);number(c->level,190,72);text(TX_E_BOND,18,92,CREAM);number(c->bond,60,94);rect(90,97,112,4,INK);rect(90,97,c->bond,4,TEAL);reason=creatures_can_evolve(c,chapter_flags,progression_is_sanctuary());if(reason==CREATURE_EVOLVE_TRIAL){const int wishes[]={TX_E_WISH_FIRE,TX_E_WISH_ROOT,TX_E_WISH_WIND,TX_E_WISH_STONE};centered(wishes[spirit],107,GOLD);}else centered(reason_id(reason),107,GOLD);{const int command_names[]={TX_E_COMMAND_OLD,TX_E_MOVE_FIRE,TX_E_MOVE_HEAL,TX_E_MOVE_WIND,TX_E_MOVE_STONE,TX_E_MOVE_HEARTH,TX_E_MOVE_CANOPY,TX_E_MOVE_REFLECT,TX_E_MOVE_ARCH};unsigned command=progression_command();centered(command_names[command<=8?command:0],123,CREAM);}centered(TX_E_KEYS,138,TEAL);}
int progression_menu_input(int pressed){CreatureInstance*c;if(journal_tab!=3)return 0;c=progression_selected();if(!c)return 0;if(pressed&256){const CreatureForm*f=creatures_form(c->form_id);if(f&&f->tier>1){unsigned id=progression_command()>4?(unsigned)spirit+1:f->signature_ability;creatures_equip(c,0,id);creatures_select_command(c,0);progression_revision++;save_game();}return 1;}if(pressed&4){unsigned status=creatures_can_evolve(c,chapter_flags,progression_is_sanctuary());if(status==CREATURE_EVOLVE_READY)game_state=EVOLVE_CONFIRM;else toast(reason_id(status));return 1;}return 0;}
void progression_draw_confirm(void){box(12,42,216,105);centered(TX_E_CONFIRM,51,GOLD);centered(TX_E_KEEP_POWER,73,CREAM);centered(TX_E_CHOICE,95,CREAM);centered(TX_E_CONFIRM_KEYS,124,TEAL);}
void progression_confirm_input(int pressed){if(pressed&2){game_state=PAUSE;return;}if(pressed&1){unsigned slot=story_slot((unsigned)spirit);CreatureInstance*c=progression_selected();if(!c){game_state=PAUSE;return;}evolution_before=c->form_id;if(creatures_evolve(&adventure_save.roster,slot,chapter_flags,progression_is_sanctuary(),1)==CREATURE_EVOLVE_READY){progression_refresh();evolution_tick=0;game_state=EVOLVE_ANIM;sfx(2);}else game_state=PAUSE;}}
void progression_draw_evolution(void){CreatureInstance*c=progression_selected();const u8*p;unsigned form=evolution_tick<36?evolution_before:c->form_id;box(20,38,200,114);centered(TX_E_BOND_LIGHT,44,GOLD);p=evolution_art_portrait(form);if(p)sprite(p,104,72,32,32,0);else{unsigned old=progression_forms[spirit];progression_forms[spirit]=form;sprite(companion_pixels(spirit,0,0),112,80,16,16,0);progression_forms[spirit]=old;}centered(evolution_tick<36?TX_E_BOND_LIGHT:name_id(form),113,CREAM);}
void progression_evolution_tick(void){evolution_tick++;if(evolution_tick==36)sfx(4);progression_revision++;if(evolution_tick>=80){game_state=PAUSE;save_game();}}
