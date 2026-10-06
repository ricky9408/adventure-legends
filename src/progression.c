/* Creature progression stays ROM-resident; game.c only orchestrates hooks. */
#include "progression.h"
#include "progression_events.h"
#include "ui.h"
#include "assets.h"
#include "world.h"
#include "campaign_rules.h"
#include "evolution_art.h"
#include "regional_creature_art.h"
#include "regional_quests.h"
#include "northern_quests.h"
#include "southern_quests.h"
#include "northern_creature_art.h"
#include "southern_creature_art.h"
typedef unsigned char u8;
extern volatile int room,px,py,spirit,game_state,has_save,save_failed;
extern volatile unsigned chapter_flags;
extern int journal_tab,frame,ability_cd,heal_cd,gfx_companion_frame,checkpoint_spawn;
extern void text(int,int,int,int),centered(int,int,int),rect(int,int,int,int,u8),box(int,int,int,int);
extern void sprite(const u8*,int,int,int,int,int),toast(int),save_game(void),sfx(int);
extern const u8 *companion_form_pixels(unsigned,unsigned,unsigned);
Save5State adventure_save;
unsigned progression_forms[PROGRESSION_SPIRIT_COUNT],progression_revision;
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
unsigned progression_form_spirit(unsigned form){
    const CreatureForm*f=creatures_form(form);
    if(!f)return CREATURE_EMPTY_SLOT;
    /* Only this compatibility cache is compact. Persistent family IDs and
     * selected roster references retain their actual authored identities. */
    switch(f->family){
    case 1:return 0;case 2:return 1;case 3:return 2;case 4:return 3;
    case 5:return PROGRESSION_WATER;case 6:return PROGRESSION_METAL;
    case 7:return PROGRESSION_NORTH_WOOD;case 8:return PROGRESSION_NORTH_FIRE;
    case 25:return PROGRESSION_NORTH_WATER;case 26:return PROGRESSION_NORTH_EARTH;
    case 27:return PROGRESSION_NORTH_METAL;
    case 9:return 11;case 10:return 12;case 28:return 13;case 29:return 14;
    case 30:return 15;case 31:return 16;case 32:return 17;case 33:return 18;
    case 34:return 19;case 35:return 20;default:return CREATURE_EMPTY_SLOT;
    }
}
CreatureInstance *progression_selected(void){
    CreatureRoster*r=&adventure_save.roster;
    unsigned i=r->selected_party<CREATURE_PARTY_CAPACITY?r->party[r->selected_party]:CREATURE_EMPTY_SLOT;
    if(i>=CREATURE_ROSTER_CAPACITY||!(r->instances[i].flags&CREATURE_OCCUPIED)||
       progression_form_spirit(r->instances[i].form_id)>=PROGRESSION_SPIRIT_COUNT)return 0;
    return &r->instances[i];
}
unsigned progression_current_form(void){CreatureInstance*c=progression_selected();return c?c->form_id:0;}
unsigned progression_current_spirit(void){CreatureInstance*c=progression_selected();return c?progression_form_spirit(c->form_id):0;}
/* CampaignSave keeps its four-family wire contract. The roster reference is
 * authoritative for every regional family and multiple instances in a family. */
static void synchronize_selection(void){
    spirit=(int)progression_current_spirit();
    adventure_save.campaign.spirit=(unsigned)spirit<CREATURE_LEGACY_COUNT?(unsigned)spirit:0;
    gfx_companion_frame=-1;
}
void progression_refresh(void){
    unsigned i;
    for(i=0;i<PROGRESSION_SPIRIT_COUNT;i++)progression_forms[i]=i<CREATURE_LEGACY_COUNT?creature_legacy_forms[i]:0;
    for(i=0;i<CREATURE_ROSTER_CAPACITY;i++){
        const CreatureInstance*c=&adventure_save.roster.instances[i];
        const CreatureForm*f,*old;unsigned family;
        if(!(c->flags&CREATURE_OCCUPIED))continue;
        family=progression_form_spirit(c->form_id);
        if(family>=PROGRESSION_SPIRIT_COUNT)continue;
        f=creatures_form(c->form_id);old=creatures_form(progression_forms[family]);
        if(!old||f->tier>old->tier)progression_forms[family]=c->form_id;
    }
    synchronize_selection();progression_revision++;
}
void progression_select(unsigned which){
    CreatureRoster*r=&adventure_save.roster;CreatureInstance*c;unsigned i;
    if(which>=PROGRESSION_SPIRIT_COUNT)return;
    c=progression_selected();
    if(c&&progression_form_spirit(c->form_id)==which){synchronize_selection();return;}
    for(i=0;i<CREATURE_PARTY_CAPACITY;i++){
        unsigned slot=r->party[i];
        if(slot<CREATURE_ROSTER_CAPACITY&&(r->instances[slot].flags&CREATURE_OCCUPIED)&&
           progression_form_spirit(r->instances[slot].form_id)==which){
            r->selected_party=(CreatureU8)i;synchronize_selection();progression_revision++;return;
        }
    }
}
void progression_new(void){
    unsigned i;u8*p=(u8*)&adventure_save;
    for(i=0;i<sizeof adventure_save;i++)p[i]=0;
    equipment_init(&adventure_save.equipment);
    creatures_migrate_legacy(&adventure_save.roster,0,0);
    progression_refresh();save_requested=0;
}
int progression_load(void){if(!save5_load(&adventure_save))return 0;progression_refresh();save_requested=0;return 1;}
void progression_story(void){
    unsigned i;
    for(i=0;i<CREATURE_LEGACY_COUNT;i++)creatures_grant_story(&adventure_save.roster,i,chapter_flags);
    creatures_apply_story_floors(&adventure_save.roster,chapter_flags);
    /* A story reward must not evict/reselect an already active stored recruit. */
    progression_refresh();
}
void progression_encounter(unsigned area,unsigned enemy){
    unsigned event=progression_encounter_event(area,enemy);
    if(event<CREATURE_FIELD_EVENT_BASE){creatures_credit_event(&adventure_save.roster,event,60,CREATURE_CREDIT_ENCOUNTER);progression_revision++;}
}
int progression_field(unsigned event){int result=creatures_credit_event(&adventure_save.roster,CREATURE_FIELD_EVENT_BASE+event,100,CREATURE_CREDIT_FIELD_AID);if(result>0)progression_revision++;return result;}
unsigned progression_command(void){CreatureInstance*c=progression_selected();return c&&c->selected_command<2?c->equipped[c->selected_command]:0;}
int progression_save_begin(void){synchronize_selection();return save5_begin(&adventure_save);}
int progression_save_step(void){return (int)save5_step(SAVE5_RECOMMENDED_BUDGET*3);}
unsigned progression_evolution_context(void){
    unsigned context=chapter_flags&CREATURE_EVOLUTION_CHAPTER_MASK;
    if(save5_quest_state(&adventure_save.quests,REGION_QUEST_WATER_BOND)==SAVE5_QUEST_CLAIMED)
        context|=CREATURE_REED_RESTORED;
    if(save5_quest_state(&adventure_save.quests,NORTH_Q_LINES)==SAVE5_QUEST_CLAIMED&&
       save5_quest_state(&adventure_save.quests,NORTH_Q_BEARING)==SAVE5_QUEST_CLAIMED)
        context|=CREATURE_NORTH_HARBOR_READY;
    if(save5_quest_state(&adventure_save.quests,NORTH_Q_BEACON)==SAVE5_QUEST_CLAIMED)
        context|=CREATURE_COUNTERWORKS_STABLE;
    if(save5_quest_state(&adventure_save.quests,SOUTH_Q_WINDOW)==SAVE5_QUEST_CLAIMED&&
       save5_quest_state(&adventure_save.quests,SOUTH_Q_HINGE)==SAVE5_QUEST_CLAIMED)
        context|=CREATURE_SOUTH_READY;
    if(save5_quest_state(&adventure_save.quests,SOUTH_Q_SUNWELL)==SAVE5_QUEST_CLAIMED)
        context|=CREATURE_SUNWELL_OPEN;
    return context;
}
int progression_is_sanctuary(void){
    unsigned i;
    if(room==0||room==16||room==22||room==30)return 1;
    if(room==31&&close_to(80,264,30))return 1;
    if(room==23&&close_to(80,264,30))return 1;
    if(room==17&&close_to(120,232,30))return 1;
    if(room==1&&close_to(WORLD_CAMP_X,WORLD_CAMP_Y,30))return 1;
    if(room>=4&&room<14){const CampaignRoom*r=&campaign_rooms[room-4];for(i=0;i<r->object_count;i++)if(r->objects[i].kind==9&&close_to(r->objects[i].x,r->objects[i].y,30))return 1;}
    return 0;
}
/* Compact decimal font for dynamic values; story text remains rasterized. */
static const u8 digits[10][5]={{7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},{5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},{7,5,7,5,7},{7,5,7,1,7}};
static void number(unsigned n,int x,int y){unsigned divisor=100;int started=0;for(;divisor;divisor/=10){unsigned d=n/divisor%10;if(d||started||divisor==1){int xx,yy;for(yy=0;yy<5;yy++)for(xx=0;xx<3;xx++)if(digits[d][yy]&(4>>xx))rect(x+xx*2,y+yy*2,2,2,CREAM);x+=8;started=1;}}}
int progression_name_id(unsigned form){
    if(!creatures_form(form))return TX_C_UNKNOWN;
    switch(form){
    case 1:return TX_FOX;case 2:return TX_E_HOMURA;
    case 4:return TX_LEAF;case 5:return TX_E_MIDORI;
    case 7:return TX_C_WIND;case 8:return TX_E_FUURI;
    case 10:return TX_C_STONE;case 11:return TX_E_KOHAKU;
    case 13:return TX_E_DEWSPINDLE;case 14:return TX_E_TIDEWHEEL;
    case 16:return TX_E_CHIMECLASP;
    case 19:return TX_E_SPOOLBUD;case 20:return TX_E_LOOMCROWN;
    case 22:return TX_E_CINDERTRAY;case 23:return TX_E_KILNBARROW;
    case 73:return TX_E_KEELKIP;case 74:return TX_E_WAKECRADLE;
    case 75:return TX_E_CAIRNCRICKET;case 76:return TX_E_ARCHSPRING;
    case 77:return TX_E_RIVETFOIL;case 78:return TX_E_GIMBALCLOAK;
    case 25:return TX_E_TANGLEAPER;case 26:return TX_E_BOUGHVAULT;case 28:return TX_E_DUNEROLL;case 29:return TX_E_DUNESCOOP;case 79:return TX_E_SKIMKIP;case 80:return TX_E_SAILSKIP;case 81:return TX_E_WARMCROAK;case 82:return TX_E_BELLOWSWELL;case 83:return TX_E_SHELLWADDLE;case 84:return TX_E_VAULTBACK;case 85:return TX_E_CLIPMANTIS;case 86:return TX_E_FOILSCYTHE;case 87:return TX_E_SWAYLEMUR;case 88:return TX_E_CANOPETAIL;case 89:return TX_E_RILLNEWT;case 90:return TX_E_VEILCREST;case 91:return TX_E_GLIMMERBAT;case 92:return TX_E_FLAREFAN;case 93:return TX_E_NEEDLETROT;case 94:return TX_E_QUILLSTRIDE;default:return TX_C_UNKNOWN;
    }
}
static int reason_id(unsigned reason,unsigned form){
    switch(reason){
    case CREATURE_EVOLVE_READY:return TX_E_READY;
    case CREATURE_EVOLVE_LEVEL:return TX_E_LEVEL_MORE;
    case CREATURE_EVOLVE_BOND:return TX_E_BOND_MORE;
    case CREATURE_EVOLVE_STORY:return form==13?TX_E_REED_MORE:progression_form_spirit(form)>=PROGRESSION_SOUTH_FIRST?TX_E_SOUTH_MORE:progression_form_spirit(form)>=PROGRESSION_NORTH_WOOD?TX_E_NORTH_MORE:TX_E_STORY_MORE;
    case CREATURE_EVOLVE_TRIAL:return TX_E_TRIAL_MORE;
    case CREATURE_EVOLVE_SANCTUARY:return TX_E_SANCTUARY;
    case CREATURE_EVOLVE_NO_EDGE:return form==16?TX_E_FIXED_FORM:TX_E_GROWN;
    default:return TX_E_NO_MEMBER;
    }
}
static int wish_id(unsigned form){
    static const int wishes[PROGRESSION_SPIRIT_COUNT]={TX_E_WISH_FIRE,TX_E_WISH_ROOT,TX_E_WISH_WIND,TX_E_WISH_STONE,TX_E_WISH_WATER,TX_E_FIXED_FORM,TX_E_WISH_NORTH_WOOD,TX_E_WISH_NORTH_FIRE,TX_E_WISH_NORTH_WATER,TX_E_WISH_NORTH_EARTH,TX_E_WISH_NORTH_METAL,TX_E_WISH_SOUTH_0,TX_E_WISH_SOUTH_1,TX_E_WISH_SOUTH_2,TX_E_WISH_SOUTH_3,TX_E_WISH_SOUTH_4,TX_E_WISH_SOUTH_5,TX_E_WISH_SOUTH_6,TX_E_WISH_SOUTH_7,TX_E_WISH_SOUTH_8,TX_E_WISH_SOUTH_9};
    unsigned family=progression_form_spirit(form);
    return family<PROGRESSION_SPIRIT_COUNT?wishes[family]:TX_E_NO_MEMBER;
}
static int command_id(unsigned command){
    static const int names[]={TX_E_COMMAND_OLD,TX_E_MOVE_FIRE,TX_E_MOVE_HEAL,TX_E_MOVE_WIND,TX_E_MOVE_STONE,TX_E_MOVE_HEARTH,TX_E_MOVE_CANOPY,TX_E_MOVE_REFLECT,TX_E_MOVE_ARCH,TX_E_MOVE_DEW,TX_E_MOVE_TIDE,TX_E_MOVE_CHIME,TX_E_COMMAND_OLD,TX_E_MOVE_THREADHOLD,TX_E_MOVE_SHUTTLE_SPAN,TX_E_MOVE_HEAT_POCKET,TX_E_MOVE_FIRING_DRAWER,TX_E_MOVE_WASHBACK,TX_E_MOVE_WAKE_TURN,TX_E_MOVE_COUNTERDROP,TX_E_MOVE_COUNTERPOISE,TX_E_MOVE_QUARTERTURN,TX_E_MOVE_GIMBAL_SCREEN,TX_E_MOVE_LEAFBOUND,TX_E_MOVE_CANOPY_ARC,TX_E_MOVE_RIDGEKICK,TX_E_MOVE_RAMPART_TURN,TX_E_MOVE_LENS_DART,TX_E_MOVE_PRISM_WAKE,TX_E_MOVE_EMBER_HUSH,TX_E_MOVE_BELLOWS_RING,TX_E_MOVE_SIDEGUARD,TX_E_MOVE_VAULT_STEP,TX_E_MOVE_PINCH_WINDOW,TX_E_MOVE_SHEAR_GATE,TX_E_MOVE_SAPLING_FEINT,TX_E_MOVE_CANOPY_EXCHANGE,TX_E_MOVE_RILL_FORK,TX_E_MOVE_VEIL_CURL,TX_E_MOVE_WARM_ECHO,TX_E_MOVE_PAIRED_ECHO,TX_E_MOVE_NEEDLE_BANK,TX_E_MOVE_QUILL_RETURN};
    return command<sizeof names/sizeof names[0]&&creatures_ability(command)?names[command]:TX_E_COMMAND_OLD;
}
static const u8 *portrait(unsigned form){const u8*p=southern_creature_art_portrait(form);if(p)return p;p=northern_creature_art_portrait(form);if(p)return p;p=evolution_art_portrait(form);return p?p:regional_creature_art_portrait(form);}
static void draw_form(unsigned form,int x,int y){
    const u8*p=portrait(form);
    if(p)sprite(p,x,y,32,32,0);
    else{p=companion_form_pixels(form,0,0);if(p)sprite(p,x+8,y+8,16,16,0);}
}
void progression_draw_tab(void){
    CreatureInstance*c=progression_selected();const CreatureForm*f;
    static const int phases[]={TX_E_WOOD,TX_E_FIRE,TX_E_EARTH,TX_E_METAL,TX_E_WATER};
    unsigned reason;
    box(8,31,224,122);centered(TX_E_GROWTH,34,GOLD);
    if(!c){centered(TX_E_NO_MEMBER,87,CREAM);return;}
    f=creatures_form(c->form_id);draw_form(c->form_id,18,56);
    text(progression_name_id(c->form_id),59,53,CREAM);
    if(f->phase<CREATURE_PHASE_COUNT)text(phases[f->phase],59,70,TEAL);
    text(f->polarity==CREATURE_YIN?TX_E_YIN:TX_E_YANG,95,70,GOLD);
    text(TX_E_LEVEL,131,70,CREAM);number(c->level,190,72);
    text(TX_E_BOND,18,92,CREAM);number(c->bond,60,94);
    rect(90,97,112,4,INK);rect(90,97,c->bond,4,TEAL);
    reason=creatures_can_evolve(c,progression_evolution_context(),progression_is_sanctuary());
    centered(reason==CREATURE_EVOLVE_TRIAL?wish_id(c->form_id):reason_id(reason,c->form_id),107,GOLD);
    centered(command_id(progression_command()),123,CREAM);centered(TX_E_KEYS,138,TEAL);
}
/* Cycle actual learned commands. If the next command is already equipped in
 * the other slot, select it rather than creating an invalid duplicate. */
static int cycle_command(CreatureInstance*c){
    const CreatureForm*f=creatures_form(c->form_id);unsigned current=progression_command(),index=0,i;
    if(!f||f->learnset_offset+f->learnset_count>CREATURE_LEARNSET_COUNT||c->selected_command>1)return 0;
    for(i=0;i<f->learnset_count;i++)if(creature_learnsets[f->learnset_offset+i].ability_id==current){index=i;break;}
    for(i=1;i<=f->learnset_count;i++){
        unsigned next=creature_learnsets[f->learnset_offset+(index+i)%f->learnset_count].ability_id;
        if(next==current||!creatures_command_learned(c->form_id,c->level,next))continue;
        if(c->equipped[c->selected_command^1]==next)return creatures_select_command(c,c->selected_command^1);
        return creatures_equip(c,c->selected_command,next);
    }
    return 0;
}
int progression_menu_input(int pressed){
    CreatureInstance*c;if(journal_tab!=3)return 0;c=progression_selected();if(!c)return 0;
    if(pressed&256){if(cycle_command(c)){progression_revision++;save_game();}return 1;}
    if(pressed&4){unsigned status=creatures_can_evolve(c,progression_evolution_context(),progression_is_sanctuary());if(status==CREATURE_EVOLVE_READY)game_state=EVOLVE_CONFIRM;else toast(reason_id(status,c->form_id));return 1;}
    return 0;
}
void progression_draw_confirm(void){box(12,42,216,105);centered(TX_E_CONFIRM,51,GOLD);centered(TX_E_KEEP_POWER,73,CREAM);centered(TX_E_CHOICE,95,CREAM);centered(TX_E_CONFIRM_KEYS,124,TEAL);}
void progression_confirm_input(int pressed){
    if(pressed&2){game_state=PAUSE;return;}
    if(pressed&1){
        CreatureInstance*c=progression_selected();unsigned slot;
        if(!c){game_state=PAUSE;return;}
        slot=adventure_save.roster.party[adventure_save.roster.selected_party];evolution_before=c->form_id;
        if(creatures_evolve(&adventure_save.roster,slot,progression_evolution_context(),progression_is_sanctuary(),1)==CREATURE_EVOLVE_READY){progression_refresh();evolution_tick=0;game_state=EVOLVE_ANIM;sfx(2);}
        else game_state=PAUSE;
    }
}
void progression_draw_evolution(void){
    CreatureInstance*c=progression_selected();unsigned form;
    if(!c)return;
    form=evolution_tick<36?evolution_before:c->form_id;box(20,38,200,114);
    centered(TX_E_BOND_LIGHT,44,GOLD);draw_form(form,104,72);
    centered(evolution_tick<36?TX_E_BOND_LIGHT:progression_name_id(form),113,CREAM);
}
void progression_evolution_tick(void){evolution_tick++;if(evolution_tick==36)sfx(4);progression_revision++;if(evolution_tick>=80){game_state=PAUSE;save_game();}}
