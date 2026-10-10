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
#include "south_game.h"
#include "magma_quests.h"
#include "magma_game.h"
#include "underwater_quests.h"
#include "underwater_game.h"
#include "underwater_powers.h"
#include "northern_creature_art.h"
#include "southern_creature_art.h"
#include "magma_creature_art.h"
#include "underwater_creature_art.h"
#include "return_creature_art.h"
#include "return_quests.h"
#include "return_game.h"
#include "return_powers.h"
#include "return_legacy_powers.h"
#include "horizons_creature_art.h"
#include "horizons_game.h"
#include "horizons_quests.h"
#include "horizons_powers.h"
#include "covenants_powers.h"
#include "covenants_game.h"
#include "covenants_creature_art.h"
#include "companion_guide.h"
#include "companion_guide_text.h"
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
/* Explicit target and participant survive only this frozen confirmation. */
unsigned progression_evolution_target,progression_evolution_choice,progression_evolution_count;
unsigned progression_evolution_reason,progression_evolution_slot;
static unsigned progression_evolution_source_form;
static CreatureU32 progression_evolution_instance;
#define INK 1
#define CREAM PAL_GOLD4
#define GOLD PAL_GOLD3
#define TEAL PAL_TEAL2
#define PLAY 1
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
    case 34:return 19;case 35:return 20;
    case 11:return 21;case 12:return 22;case 13:return 23;case 14:return 24;
    case 15:return 25;case 16:return 26;case 36:return 27;case 37:return 28;case 38:return 29;
    case 17:return 30;case 18:return 31;case 19:return 32;case 20:return 33;
    case 21:return 34;case 22:return 35;case 23:return 36;case 24:return 37;
    case 39:return 38;case 40:return 39;
    case 41:return 40;case 42:return 41;case 43:return 42;case 44:return 43;case 45:return 44;case 46:return 45;case 47:return 46;case 48:return 47;case 49:return 48;case 50:return 49;case 51:return 50;case 52:return 51;
    case 53:return 52;case 54:return 53;case 55:return 54;case 56:return 55;case 57:return 56;case 58:return 57;case 59:return 58;case 60:return 59;
    default:return CREATURE_EMPTY_SLOT;
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
/* Small exact selector signature, not a roster validity cache. This catches
 * away-and-back edits during frozen menus before any power/world tick resumes. */
static CreatureU32 selected_signature_ids[4];
static unsigned char selected_signature_party[4],selected_signature_slot;
static unsigned char selected_signature_form,selected_signature_commands[3],selected_signature_valid;
void progression_selection_changed(void){
 CreatureRoster*r=&adventure_save.roster;CreatureInstance*c=progression_selected();unsigned i,changed=0;
 for(i=0;i<4;i++){
  unsigned slot=r->party[i];CreatureU32 id=slot<CREATURE_ROSTER_CAPACITY?r->instances[slot].instance_id:0;
  if(selected_signature_party[i]!=slot||selected_signature_ids[i]!=id)changed=1;
  selected_signature_party[i]=(unsigned char)slot;selected_signature_ids[i]=id;
 }
 if(selected_signature_slot!=r->selected_party||selected_signature_form!=(c?c->form_id:0)||
    selected_signature_commands[0]!=(c?c->equipped[0]:0)||selected_signature_commands[1]!=(c?c->equipped[1]:0)||
    selected_signature_commands[2]!=(c?c->selected_command:0))changed=1;
 selected_signature_slot=r->selected_party;selected_signature_form=c?c->form_id:0;
 selected_signature_commands[0]=c?c->equipped[0]:0;selected_signature_commands[1]=c?c->equipped[1]:0;
 selected_signature_commands[2]=c?c->selected_command:0;
 if(changed&&selected_signature_valid){south_game_cancel_rest();magma_game_cancel_return();progression_evolution_cancel();underwater_powers_selection_changed();underwater_game_selection_changed();return_powers_selection_changed();return_legacy_cancel();return_game_selection_changed();horizons_powers_selection_changed();horizons_game_selection_changed();covenants_powers_selection_changed();covenants_game_selection_changed();}
 selected_signature_valid=1;
}
static void synchronize_selection(void){
    spirit=(int)progression_current_spirit();
    adventure_save.campaign.spirit=(unsigned)spirit<CREATURE_LEGACY_COUNT?(unsigned)spirit:0;
    gfx_companion_frame=-1;
    progression_selection_changed();
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
    progression_evolution_cancel();
    selected_signature_valid=0;
    for(i=0;i<sizeof adventure_save;i++)p[i]=0;
    equipment_init(&adventure_save.equipment);
    creatures_migrate_legacy(&adventure_save.roster,0,0);
    progression_refresh();save_requested=0;
}
int progression_load(void){progression_evolution_cancel();if(!save5_load(&adventure_save))return 0;progression_refresh();save_requested=0;return 1;}
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
int progression_save_begin(void){progression_evolution_cancel();synchronize_selection();return save5_begin(&adventure_save);}
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
    return context|magma_context(&adventure_save)|underwater_context(&adventure_save)|return_context(&adventure_save)|horizons_context(&adventure_save);
}
int progression_is_sanctuary(void){
    unsigned i;
    if(return_game_is_sanctuary()||horizons_game_is_sanctuary()||covenants_game_is_sanctuary())return 1;
    if(room==0||room==16||room==22||room==30||room==38||room==46)return 1;
    if(room==47&&close_to(80,280,30))return 1;
    if(room==39&&close_to(80,280,30))return 1;
    if(room==31&&close_to(80,264,30))return 1;
    if(room==23&&close_to(80,264,30))return 1;
    if(room==17&&close_to(120,232,30))return 1;
    if(room==1&&close_to(WORLD_CAMP_X,WORLD_CAMP_Y,30))return 1;
    if(room>=4&&room<14){const CampaignRoom*r=&campaign_rooms[room-4];for(i=0;i<r->object_count;i++)if(r->objects[i].kind==9&&close_to(r->objects[i].x,r->objects[i].y,30))return 1;}
    return 0;
}
/* Compact decimal font for dynamic values; story text remains rasterized. */
static const u8 digits[10][5]={{7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},{5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},{7,5,7,5,7},{7,5,7,1,7}};
/* Exact transparent6x10 doubled glyphs; ordinary level/bond values avoid division. */
extern unsigned short *screen;
static void growth_digit_blit(unsigned digit,int x,int y){
 unsigned row;unsigned short ink=(unsigned short)(CREAM|((unsigned)CREAM<<8));
 if((unsigned)x>234||(unsigned)y>150){int xx,yy;for(yy=0;yy<5;yy++)for(xx=0;xx<3;xx++)if(digits[digit][yy]&(4>>xx))rect(x+xx*2,y+yy*2,2,2,CREAM);return;}
 for(row=0;row<5;row++){unsigned bits=digits[digit][row],copy;unsigned short*p=screen+(y+(int)row*2)*120+(x>>1);
  if(!(x&1)){for(copy=0;copy<2;copy++,p+=120){if(bits&4)p[0]=ink;if(bits&2)p[1]=ink;if(bits&1)p[2]=ink;}}
  else{unsigned short mask[4];unsigned col;mask[0]=(bits&4)?65280:0;mask[1]=(unsigned short)(((bits&4)?255:0)|((bits&2)?65280:0));mask[2]=(unsigned short)(((bits&2)?255:0)|((bits&1)?65280:0));mask[3]=(bits&1)?255:0;
   for(copy=0;copy<2;copy++,p+=120)for(col=0;col<4;col++)if(mask[col])p[col]=(unsigned short)((p[col]&~mask[col])|(ink&mask[col]));}
 }
}
static void number(unsigned n,int x,int y){unsigned value[3]={0,0,0},i;int started=0;
 /* Real level/bond callers are <=100. Rare host probes retain the original
  * low-three-digit behavior; valid menu values take no division path. */
 if(n>=1000)n%=1000;while(n>=100){n-=100;value[0]++;}while(n>=10){n-=10;value[1]++;}value[2]=n;
 for(i=0;i<3;i++)if(value[i]||started||i==2){growth_digit_blit(value[i],x,y);x+=8;started=1;}
}

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
    case 25:return TX_E_TANGLEAPER;case 26:return TX_E_BOUGHVAULT;case 28:return TX_E_DUNEROLL;case 29:return TX_E_DUNESCOOP;case 79:return TX_E_SKIMKIP;case 80:return TX_E_SAILSKIP;case 81:return TX_E_WARMCROAK;case 82:return TX_E_BELLOWSWELL;case 83:return TX_E_SHELLWADDLE;case 84:return TX_E_VAULTBACK;case 85:return TX_E_CLIPMANTIS;case 86:return TX_E_FOILSCYTHE;case 87:return TX_E_SWAYLEMUR;case 88:return TX_E_CANOPETAIL;case 89:return TX_E_RILLNEWT;case 90:return TX_E_VEILCREST;case 91:return TX_E_GLIMMERBAT;case 92:return TX_E_FLAREFAN;case 93:return TX_E_NEEDLETROT;case 94:return TX_E_QUILLSTRIDE;
    case 31:return TX_E_MG_NAME_31;case 32:return TX_E_MG_NAME_32;case 33:return TX_E_MG_NAME_33;case 34:return TX_E_MG_NAME_34;case 35:return TX_E_MG_NAME_35;case 36:return TX_E_MG_NAME_36;case 37:return TX_E_MG_NAME_37;case 38:return TX_E_MG_NAME_38;case 39:return TX_E_MG_NAME_39;case 40:return TX_E_MG_NAME_40;case 41:return TX_E_MG_NAME_41;case 42:return TX_E_MG_NAME_42;case 43:return TX_E_MG_NAME_43;case 44:return TX_E_MG_NAME_44;case 45:return TX_E_MG_NAME_45;case 46:return TX_E_MG_NAME_46;case 47:return TX_E_MG_NAME_47;case 48:return TX_E_MG_NAME_48;case 95:return TX_E_MG_NAME_95;case 96:return TX_E_MG_NAME_96;case 97:return TX_E_MG_NAME_97;case 98:return TX_E_MG_NAME_98;case 99:return TX_E_MG_NAME_99;case 100:return TX_E_MG_NAME_100;
    case 49:return TX_E_UW_NAME_49;case 50:return TX_E_UW_NAME_50;case 51:return TX_E_UW_NAME_51;case 52:return TX_E_UW_NAME_52;case 53:return TX_E_UW_NAME_53;case 54:return TX_E_UW_NAME_54;case 55:return TX_E_UW_NAME_55;case 56:return TX_E_UW_NAME_56;case 57:return TX_E_UW_NAME_57;case 58:return TX_E_UW_NAME_58;case 59:return TX_E_UW_NAME_59;case 60:return TX_E_UW_NAME_60;case 61:return TX_E_UW_NAME_61;case 62:return TX_E_UW_NAME_62;case 63:return TX_E_UW_NAME_63;case 64:return TX_E_UW_NAME_64;case 65:return TX_E_UW_NAME_65;case 66:return TX_E_UW_NAME_66;case 67:return TX_E_UW_NAME_67;case 68:return TX_E_UW_NAME_68;case 69:return TX_E_UW_NAME_69;case 70:return TX_E_UW_NAME_70;case 71:return TX_E_UW_NAME_71;case 72:return TX_E_UW_NAME_72;
    case 3:return TX_E_RT_NAME_3;
    case 6:return TX_E_RT_NAME_6;
    case 9:return TX_E_RT_NAME_9;
    case 12:return TX_E_RT_NAME_12;
    case 15:return TX_E_RT_NAME_15;
    case 17:return TX_E_RT_NAME_17;
    case 18:return TX_E_RT_NAME_18;
    case 21:return TX_E_RT_NAME_21;
    case 24:return TX_E_RT_NAME_24;
    case 27:return TX_E_RT_NAME_27;
    case 30:return TX_E_RT_NAME_30;
    case 101:return TX_E_RT_NAME_101;
    case 102:return TX_E_RT_NAME_102;
    case 103:return TX_E_RT_NAME_103;
    case 104:return TX_E_RT_NAME_104;
    case 105:return TX_E_HZ_NAME_105;case 106:return TX_E_HZ_NAME_106;case 107:return TX_E_HZ_NAME_107;case 108:return TX_E_HZ_NAME_108;case 109:return TX_E_HZ_NAME_109;case 110:return TX_E_HZ_NAME_110;case 111:return TX_E_HZ_NAME_111;case 112:return TX_E_HZ_NAME_112;case 113:return TX_E_HZ_NAME_113;case 114:return TX_E_HZ_NAME_114;case 115:return TX_E_HZ_NAME_115;case 116:return TX_E_HZ_NAME_116;case 117:return TX_E_HZ_NAME_117;case 118:return TX_E_HZ_NAME_118;case 119:return TX_E_HZ_NAME_119;case 120:return TX_E_HZ_NAME_120;
    case 121:return TX_E_CV_STILLTIDE;case 122:return TX_E_CV_VOWBOUGH;case 123:return TX_E_CV_KILNWHORL;case 124:return TX_E_CV_CAIRNWARD;case 125:return TX_E_CV_BELLMANTLE;case 126:return TX_E_CV_SHADEWEAVER;case 127:return TX_E_CV_TIDEPLUME;case 128:return TX_E_CV_HEARTHMOTH;
    default:return TX_C_UNKNOWN;
    }
}
static int return_wish_index(unsigned form){
    static const u8 predecessor[13]={2,5,8,11,14,16,17,20,23,26,29,101,103};
    unsigned i;for(i=0;i<13;++i)if(predecessor[i]==form)return (int)i;return -1;
}
static int reason_id(unsigned reason,unsigned form){
    switch(reason){
    case CREATURE_EVOLVE_READY:return TX_E_READY;
    case CREATURE_EVOLVE_LEVEL:return TX_E_LEVEL_MORE;
    case CREATURE_EVOLVE_BOND:return TX_E_BOND_MORE;
    case CREATURE_EVOLVE_STORY:if(form>=105&&form<=112)return TX_E_HZ_NEED_STORY;if(return_wish_index(form)>=0)return TX_E_RT_MORE;
        return progression_form_spirit(form)>=PROGRESSION_UNDERWATER_FIRST?((progression_evolution_context()&CREATURE_UNDERWATER_READY)?TX_E_UW_LATER:TX_E_UW_MORE):progression_form_spirit(form)>=PROGRESSION_MAGMA_FIRST?(creatures_form(form)->tier>=2?TX_E_MG_LATER:TX_E_MG_MORE):form==13?TX_E_REED_MORE:progression_form_spirit(form)>=PROGRESSION_SOUTH_FIRST?TX_E_SOUTH_MORE:progression_form_spirit(form)>=PROGRESSION_NORTH_WOOD?TX_E_NORTH_MORE:TX_E_STORY_MORE;
    case CREATURE_EVOLVE_TRIAL:return TX_E_TRIAL_MORE;
    case CREATURE_EVOLVE_SANCTUARY:return TX_E_SANCTUARY;
    case CREATURE_EVOLVE_AMBIGUOUS:return TX_E_CHOOSE_BRANCH;
    case CREATURE_EVOLVE_COLLECTION_RESERVED:return TX_E_SPACE_RESERVED;
    case CREATURE_EVOLVE_NO_EDGE:return form==16||(form>=121&&form<=128)?TX_E_FIXED_FORM:TX_E_GROWN;
    default:return TX_E_NO_MEMBER;
    }
}
static int wish_id(unsigned form){
    static const int wishes[PROGRESSION_SPIRIT_COUNT]={TX_E_WISH_FIRE,TX_E_WISH_ROOT,TX_E_WISH_WIND,TX_E_WISH_STONE,TX_E_WISH_WATER,TX_E_FIXED_FORM,TX_E_WISH_NORTH_WOOD,TX_E_WISH_NORTH_FIRE,TX_E_WISH_NORTH_WATER,TX_E_WISH_NORTH_EARTH,TX_E_WISH_NORTH_METAL,TX_E_WISH_SOUTH_0,TX_E_WISH_SOUTH_1,TX_E_WISH_SOUTH_2,TX_E_WISH_SOUTH_3,TX_E_WISH_SOUTH_4,TX_E_WISH_SOUTH_5,TX_E_WISH_SOUTH_6,TX_E_WISH_SOUTH_7,TX_E_WISH_SOUTH_8,TX_E_WISH_SOUTH_9,TX_E_MG_WISH_0,TX_E_MG_WISH_1,TX_E_MG_WISH_2,TX_E_MG_WISH_3,TX_E_MG_WISH_4,TX_E_MG_WISH_5,TX_E_MG_WISH_6,TX_E_MG_WISH_7,TX_E_MG_WISH_8,TX_E_UW_WISH_0,TX_E_UW_WISH_1,TX_E_UW_WISH_2,TX_E_UW_WISH_3,TX_E_UW_WISH_4,TX_E_UW_WISH_5,TX_E_UW_WISH_6,TX_E_UW_WISH_7,TX_E_RT_WISH_11,TX_E_RT_WISH_12};
    static const int returning[13]={TX_E_RT_WISH_0,TX_E_RT_WISH_1,TX_E_RT_WISH_2,TX_E_RT_WISH_3,TX_E_RT_WISH_4,TX_E_RT_WISH_5,TX_E_RT_WISH_6,TX_E_RT_WISH_7,TX_E_RT_WISH_8,TX_E_RT_WISH_9,TX_E_RT_WISH_10,TX_E_RT_WISH_11,TX_E_RT_WISH_12};
    unsigned family=progression_form_spirit(form);int index=return_wish_index(form);
    if(form>=121&&form<=128)return TX_E_FIXED_FORM;
    if(index>=0)return returning[index];
    if(form>=105&&form<=112&&((form-105)&1u)==0){static const int wishes_hz[4]={TX_E_HZ_WISH_0,TX_E_HZ_WISH_1,TX_E_HZ_WISH_2,TX_E_HZ_WISH_3};return wishes_hz[(form-105)/2];}
    if(creatures_form(form)&&!creatures_evolution_count(form))return TX_E_GROWN;
    if(form==32)return TX_E_MG_WISH_32;
    if(form==35)return TX_E_MG_WISH_35;
    return family<PROGRESSION_SPIRIT_COUNT?wishes[family]:TX_E_NO_MEMBER;
}
int progression_command_name_id(unsigned command){
    static const int names[]={TX_E_COMMAND_OLD,TX_E_MOVE_FIRE,TX_E_MOVE_HEAL,TX_E_MOVE_WIND,TX_E_MOVE_STONE,TX_E_MOVE_HEARTH,TX_E_MOVE_CANOPY,TX_E_MOVE_REFLECT,TX_E_MOVE_ARCH,TX_E_MOVE_DEW,TX_E_MOVE_TIDE,TX_E_MOVE_CHIME,TX_E_CV_CMD_12,TX_E_MOVE_THREADHOLD,TX_E_MOVE_SHUTTLE_SPAN,TX_E_MOVE_HEAT_POCKET,TX_E_MOVE_FIRING_DRAWER,TX_E_MOVE_WASHBACK,TX_E_MOVE_WAKE_TURN,TX_E_MOVE_COUNTERDROP,TX_E_MOVE_COUNTERPOISE,TX_E_MOVE_QUARTERTURN,TX_E_MOVE_GIMBAL_SCREEN,TX_E_MOVE_LEAFBOUND,TX_E_MOVE_CANOPY_ARC,TX_E_MOVE_RIDGEKICK,TX_E_MOVE_RAMPART_TURN,TX_E_MOVE_LENS_DART,TX_E_MOVE_PRISM_WAKE,TX_E_MOVE_EMBER_HUSH,TX_E_MOVE_BELLOWS_RING,TX_E_MOVE_SIDEGUARD,TX_E_MOVE_VAULT_STEP,TX_E_MOVE_PINCH_WINDOW,TX_E_MOVE_SHEAR_GATE,TX_E_MOVE_SAPLING_FEINT,TX_E_MOVE_CANOPY_EXCHANGE,TX_E_MOVE_RILL_FORK,TX_E_MOVE_VEIL_CURL,TX_E_MOVE_WARM_ECHO,TX_E_MOVE_PAIRED_ECHO,TX_E_MOVE_NEEDLE_BANK,TX_E_MOVE_QUILL_RETURN,TX_E_MG_CMD_43,TX_E_MG_CMD_44,TX_E_MG_CMD_45,TX_E_MG_CMD_46,TX_E_MG_CMD_47,TX_E_MG_CMD_48,TX_E_MG_CMD_49,TX_E_MG_CMD_50,TX_E_MG_CMD_51,TX_E_MG_CMD_52,TX_E_MG_CMD_53,TX_E_MG_CMD_54,TX_E_MG_CMD_55,TX_E_MG_CMD_56,TX_E_MG_CMD_57,TX_E_MG_CMD_58,TX_E_MG_CMD_59,TX_E_MG_CMD_60,TX_E_MG_CMD_61,TX_E_MG_CMD_62,TX_E_MG_CMD_63,TX_E_MG_CMD_64,TX_E_MG_CMD_65,TX_E_MG_CMD_66,TX_E_UW_CMD_67,TX_E_UW_CMD_68,TX_E_UW_CMD_69,TX_E_UW_CMD_70,TX_E_UW_CMD_71,TX_E_UW_CMD_72,TX_E_UW_CMD_73,TX_E_UW_CMD_74,TX_E_UW_CMD_75,TX_E_UW_CMD_76,TX_E_UW_CMD_77,TX_E_UW_CMD_78,TX_E_UW_CMD_79,TX_E_UW_CMD_80,TX_E_UW_CMD_81,TX_E_UW_CMD_82,TX_E_UW_CMD_83,TX_E_UW_CMD_84,TX_E_UW_CMD_85,TX_E_UW_CMD_86,TX_E_UW_CMD_87,TX_E_UW_CMD_88,TX_E_UW_CMD_89,TX_E_UW_CMD_90,TX_E_RT_CMD_91,TX_E_RT_CMD_92,TX_E_RT_CMD_93,TX_E_RT_CMD_94,TX_E_RT_CMD_95,TX_E_RT_CMD_96,TX_E_RT_CMD_97,TX_E_RT_CMD_98,TX_E_RT_CMD_99,TX_E_RT_CMD_100,TX_E_RT_CMD_101,TX_E_RT_CMD_102,TX_E_RT_CMD_103,TX_E_RT_CMD_104,TX_E_RT_CMD_105,TX_E_HZ_CMD_106,TX_E_HZ_CMD_107,TX_E_HZ_CMD_108,TX_E_HZ_CMD_109,TX_E_HZ_CMD_110,TX_E_HZ_CMD_111,TX_E_HZ_CMD_112,TX_E_HZ_CMD_113,TX_E_HZ_CMD_114,TX_E_HZ_CMD_115,TX_E_HZ_CMD_116,TX_E_HZ_CMD_117,TX_E_HZ_CMD_118,TX_E_HZ_CMD_119,TX_E_HZ_CMD_120,TX_E_HZ_CMD_121,TX_E_CV_CMD_122,TX_E_CV_CMD_123,TX_E_CV_CMD_124,TX_E_CV_CMD_125,TX_E_CV_CMD_126,TX_E_CV_CMD_127,TX_E_CV_CMD_128};
    return command<sizeof names/sizeof names[0]&&creatures_ability(command)?names[command]:TX_E_COMMAND_OLD;
}
static const u8 *portrait(unsigned form){const u8*p;if(form>=121&&form<=128)return covenants_creature_art_portrait(form);if(form>=105&&form<=120)return horizons_creature_art_portrait(form);p=return_creature_art_portrait(form);if(p)return p;p=underwater_creature_art_portrait(form);if(p)return p;p=magma_creature_art_portrait(form);if(p)return p;p=southern_creature_art_portrait(form);if(p)return p;p=northern_creature_art_portrait(form);if(p)return p;p=evolution_art_portrait(form);return p?p:regional_creature_art_portrait(form);}
static void draw_form(unsigned form,int x,int y){
    const u8*p=portrait(form);
    /* Original indexed anatomy stays intact, including ink-colored pixels.
     * Only the eight new portraits need a light matte against this dark card. */
    if(p){if(form>=121&&form<=128)rect(x,y,32,32,PAL_GOLD4);sprite(p,x,y,32,32,0);}
    else{p=companion_form_pixels(form,0,0);if(p)sprite(p,x+8,y+8,16,16,0);}
}
/* Browse is a preview. Only A commits the visible command or evolution. */
int progression_menu_row,progression_menu_detail;
unsigned progression_menu_command;
void progression_menu_reset(void){progression_menu_row=progression_menu_detail=0;companion_guide_page=0;progression_menu_command=progression_command();progression_revision++;}
int progression_menu_back(void){if(!progression_menu_detail)return 0;progression_menu_detail=0;progression_revision++;return 1;}
static void command_candidate(CreatureInstance*c,int delta){
 const CreatureForm*f=creatures_form(c->form_id);unsigned index=0,i;
 if(!f||!f->learnset_count||f->learnset_offset+f->learnset_count>CREATURE_LEARNSET_COUNT)return;
 for(i=0;i<f->learnset_count;i++)if(creature_learnsets[f->learnset_offset+i].ability_id==progression_menu_command){index=i;break;}
 for(i=0;i<f->learnset_count;i++){unsigned next;index=delta>0?(index+1==f->learnset_count?0:index+1):(index?index-1:(unsigned)f->learnset_count-1);next=creature_learnsets[f->learnset_offset+index].ability_id;if(creatures_command_learned(c->form_id,c->level,next)){progression_menu_command=next;progression_revision++;return;}}
}
static int choose_command(CreatureInstance*c){unsigned next=progression_menu_command;
 if(next==progression_command()||!creatures_command_learned(c->form_id,c->level,next)||c->selected_command>1)return 0;
 if(c->equipped[c->selected_command^1]==next)return creatures_select_command(c,c->selected_command^1);
 return creatures_equip(c,c->selected_command,next);
}
void progression_draw_tab(void){CreatureInstance*c=progression_selected();unsigned reason;
 if(progression_menu_detail){companion_guide_draw(c,progression_menu_command,COMPANION_GUIDE_GROWTH);return;}
 box(8,31,224,123);centered(TX_E_GROWTH,33,GOLD);
 if(!c){centered(TX_E_NO_MEMBER,87,CREAM);centered(TX_PF_BACK_CLOSE,138,TEAL);return;}
 centered(progression_name_id(c->form_id),51,CREAM);
 text(TX_E_LEVEL,59,69,CREAM);number(c->level,101,71);text(TX_E_BOND,135,69,CREAM);number(c->bond,177,71);
 reason=creatures_can_evolve(c,progression_evolution_context(),progression_is_sanctuary());
 rect(14,progression_menu_row?105:87,212,17,PAL_STONE2);centered(progression_command_name_id(progression_menu_command),88,progression_menu_row?CREAM:GOLD);
 if(progression_menu_command==progression_command())rect(216,94,3,3,TEAL);
 text(TX_PF_EVOLVE,21,105,reason==CREATURE_EVOLVE_READY?GOLD:PAL_SLATE);
 centered(reason==CREATURE_EVOLVE_TRIAL?wish_id(c->form_id):reason_id(reason,c->form_id),121,CREAM);companion_guide_center(CG_GROWTH_KEYS,138,TEAL);
}
#include "progression_evolution_job.inc"
int progression_menu_input(int pressed){
    CreatureInstance*c;int direction=pressed&240;
    if(journal_tab!=3)return 0;if(pressed&(2|8))return 0;c=progression_selected();if(!c)return 1;
    if(pressed&4)return 0;
    if(progression_menu_detail){
        if(direction==16||direction==32){command_candidate(c,direction==16?1:-1);return 1;}
        if(direction==64||direction==128){companion_guide_page^=1;progression_revision++;return 1;}
        if(direction)return 1;
        if(pressed&1){if(choose_command(c)){progression_selection_changed();save_game();}progression_menu_detail=0;progression_revision++;return 1;}
        return 0;
    }
    if(direction==64||direction==128){progression_menu_row^=1;progression_revision++;return 1;}
    if(direction){if(!progression_menu_row&&(direction==16||direction==32))command_candidate(c,direction==16?1:-1);return 1;}
    if(!(pressed&1))return 0;
    if(!progression_menu_row){progression_menu_detail=1;companion_guide_page=0;progression_revision++;return 1;}
    {
        unsigned count=creatures_evolution_count(c->form_id),i;
        if(!count||count>2){toast(reason_id(count?CREATURE_EVOLVE_INVALID:CREATURE_EVOLVE_NO_EDGE,c->form_id));return 1;}
        progression_evolution_cancel();
        progression_evolution_source_form=c->form_id;progression_evolution_instance=c->instance_id;
        progression_evolution_slot=adventure_save.roster.party[adventure_save.roster.selected_party];
        evolution_job.selected_party=adventure_save.roster.selected_party;
        evolution_job.commands[0]=c->equipped[0];evolution_job.commands[1]=c->equipped[1];
        evolution_job.commands[2]=c->selected_command;evolution_job.manual_choice=0;
        progression_evolution_count=count;progression_evolution_choice=0;
        for(i=0;i<count;i++){
            const CreatureEvolution*e=creatures_evolution_at(c->form_id,i);
            evolution_job.reasons[i]=e?creatures_can_evolve_to(c,e->to,
              progression_evolution_context(),progression_is_sanctuary()):CREATURE_EVOLVE_INVALID;
        }
        evolution_choice_refresh();
        if(count<2&&progression_evolution_reason!=CREATURE_EVOLVE_READY){toast(reason_id(progression_evolution_reason,c->form_id));return 1;}
        game_state=EVOLVE_CONFIRM;
        evolution_job.a_latched=1;
        if(evolution_job.reasons[0]==CREATURE_EVOLVE_READY||(count==2&&evolution_job.reasons[1]==CREATURE_EVOLVE_READY))evolution_prepare(0);
        else progression_revision++;
        return 1;
    }
    return 0;
}
void progression_draw_confirm(void){
    const CreatureForm*f=creatures_form(progression_evolution_target);
    box(8,31,224,123);
    if(!f){centered(TX_E_NO_MEMBER,87,CREAM);centered(TX_E_CONFIRM_KEYS,138,TEAL);return;}
    /* One full-width candidate avoids truncating either irreversible branch.
     * Only drawing changes: the existing frozen transaction owns every input. */
    centered(progression_name_id(f->id),33,GOLD);
    companion_guide_axes(f->id,f->polarity,49);
    centered(progression_command_name_id(f->signature_ability),65,GOLD);
    companion_guide_combat(f->signature_ability,81);
    companion_guide_center(CG_EVOLVE,109,TEAL);
    centered(progression_evolution_busy()?TX_UW_PREPARING:reason_id(progression_evolution_reason,progression_evolution_source_form),123,CREAM);
    companion_guide_center(progression_evolution_count>1?CG_EVOLVE_KEYS:CG_EVOLVE_SINGLE_KEYS,138,TEAL);
}
void progression_confirm_input(int pressed){
    unsigned fresh_a;
    if(game_state!=EVOLVE_CONFIRM){progression_evolution_cancel();return;}
    /* The previous update committed the exact individual. Cancellation is
     * no longer an option; publish once on this cheaper update. */
    if(progression_evolution_handoff()){
        evolution_release();progression_refresh();evolution_tick=0;game_state=EVOLVE_ANIM;sfx(2);return;
    }
    if(pressed&(2|8)){progression_evolution_cancel();game_state=(pressed&8)?PLAY:PAUSE;progression_revision++;return;}
    if(pressed&4)return;
    if(!evolution_participant_matches()||!evolution_request_matches()){evolution_source_changed();return;}
    fresh_a=(pressed&1)&&!evolution_job.a_latched;
    evolution_job.a_latched=(unsigned char)((pressed&1)!=0);
    if(pressed&240){
        /* Every direction revokes a pending confirmation and consumes A.
         * Only an exact single left/right direction changes a branch. */
        if(evolution_job.confirm)evolution_release();
        if(progression_evolution_count==2&&((pressed&240)==16||(pressed&240)==32)){
            progression_evolution_choice^=1;evolution_job.manual_choice=1;
            evolution_choice_refresh();progression_revision++;
        }
        return;
    }
    if(progression_evolution_busy()){
        unsigned slice;
        /* Warm both cold pages first. Exact compare/commit+refresh always owns
         * its own update, never the tail of a preparation batch. */
        if(evolution_job.phase==EVOLUTION_JOB_WARM||evolution_job.phase==EVOLUTION_JOB_FINISH){
            evolution_prepare_step();return;
        }
        for(slice=0;slice<EVOLUTION_JOB_SLICES_PER_UPDATE;slice++){
            evolution_prepare_step();
            if(game_state!=EVOLVE_CONFIRM||evolution_job.phase==EVOLUTION_JOB_IDLE||
               evolution_job.phase==EVOLUTION_JOB_FINISH||evolution_job.phase==EVOLUTION_JOB_WARM)break;
        }
        return;
    }
    if(fresh_a){
        unsigned status=creatures_can_evolve_to(progression_selected(),progression_evolution_target,
          progression_evolution_context(),progression_is_sanctuary());
        if(status!=CREATURE_EVOLVE_READY){evolution_denied(status);return;}
        /* A never authorizes from a cached display reason or a previous proof. */
        evolution_prepare(1);
    }
}
void progression_draw_evolution(void){
    CreatureInstance*c=progression_selected();unsigned form;
    if(!c)return;
    form=evolution_tick<36?evolution_before:c->form_id;box(20,38,200,114);
    centered(TX_E_BOND_LIGHT,44,GOLD);draw_form(form,104,72);
    centered(evolution_tick<36?TX_E_BOND_LIGHT:progression_name_id(form),113,CREAM);
}
void progression_evolution_tick(void){evolution_tick++;if(evolution_tick==36)sfx(4);progression_revision++;if(evolution_tick>=80){game_state=PAUSE;progression_menu_reset();save_game();}}
