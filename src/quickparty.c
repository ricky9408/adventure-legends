/* A held L owns input until release, including its opening and closing update.
 * The legacy `spirit` remains a family/power ID, NEVER a quick-party slot. */
#include "quickparty.h"
#include "progression.h"
#include "assets.h"
#include "ui.h"
#include "evolution_art.h"
typedef unsigned char u8;
extern volatile int spirit,game_state,room;
extern int journal_tab,gfx_companion_frame;
extern void rect(int,int,int,int,u8),box(int,int,int,int),text(int,int,int,int),centered(int,int,int),sprite(const u8*,int,int,int,int,int),save_game(void),toast(int),sfx(int);
extern const u8 *companion_pixels(int,int,int);
#define L 512
#define B 2
#define START 8
#define DIRECTIONS 240
#define EMPTY CREATURE_EMPTY_SLOT
#define INK 1
#define GOLD PAL_GOLD3
#define CREAM PAL_GOLD4
#define TEAL PAL_TEAL2
int quickparty_open,quickparty_candidate=EMPTY,quickparty_hold_updates;
unsigned quickparty_revision;
int quickparty_menu_slot,quickparty_menu_candidate;
static int blocked,had_direction,menu_notice;

static CreatureInstance *member(unsigned slot){CreatureRoster*r=&adventure_save.roster;unsigned i;if(slot>=4)return 0;i=r->party[slot];if(i>=CREATURE_ROSTER_CAPACITY||!(r->instances[i].flags&CREATURE_OCCUPIED))return 0;return creatures_legacy_spirit(r->instances[i].form_id)<4?&r->instances[i]:0;}
static int name_id(unsigned form){switch(form){case 2:return TX_E_HOMURA;case 5:return TX_E_MIDORI;case 8:return TX_E_FUURI;case 11:return TX_E_KOHAKU;default:return form==1?TX_FOX:form==4?TX_LEAF:form==7?TX_C_WIND:TX_C_STONE;}}
static void changed(void){quickparty_revision++;}
static void synchronize(void){CreatureRoster*r=&adventure_save.roster;CreatureInstance*c=member(r->selected_party);if(c){spirit=creatures_legacy_spirit(c->form_id);adventure_save.campaign.spirit=spirit;gfx_companion_frame=-1;progression_revision++;changed();}}
int quickparty_select(unsigned slot){CreatureRoster*r=&adventure_save.roster;if(!member(slot))return 0;if(r->selected_party==slot)return 0;r->selected_party=slot;synchronize();sfx(2);return 1;}
int quickparty_cycle(void){CreatureRoster*r=&adventure_save.roster;unsigned i;for(i=1;i<=4;i++){unsigned next=(r->selected_party+i)&3;if(member(next))return quickparty_select(next);}return 0;}
void quickparty_reset(int held){if(quickparty_open){quickparty_open=0;changed();}quickparty_candidate=EMPTY;quickparty_hold_updates=0;had_direction=0;blocked=(held&L)!=0;}
int quickparty_update(int held,int pressed){unsigned dir=held&DIRECTIONS;int candidate=EMPTY;
 if(blocked){if(!(held&L))blocked=0;return 1;}
 if(!quickparty_open){if(!(pressed&L))return 0;quickparty_open=1;quickparty_candidate=EMPTY;quickparty_hold_updates=0;had_direction=0;changed();}
 if(pressed&(B|START)){quickparty_reset(held);if(pressed&START){journal_tab=room==1?1:0;game_state=3;}return 1;}
 if(!(held&L)){int choice=quickparty_candidate;int tap=!had_direction&&quickparty_hold_updates<=12;quickparty_reset(0);if(choice!=EMPTY)quickparty_select((unsigned)choice);else if(tap)quickparty_cycle();return 1;}
 if(quickparty_hold_updates<13)quickparty_hold_updates++;
 if(dir){had_direction=1;if(dir==64)candidate=0;else if(dir==16)candidate=1;else if(dir==128)candidate=2;else if(dir==32)candidate=3;if(candidate!=EMPTY&&!member((unsigned)candidate))candidate=EMPTY;if(candidate!=quickparty_candidate){quickparty_candidate=candidate;changed();}}
 return 1;
}
int quickparty_assign(unsigned target,unsigned instance){CreatureRoster*r=&adventure_save.roster;CreatureU8 party[4];unsigned i,count=0;if(target>=4)return 0;if(instance!=EMPTY&&(instance>=CREATURE_ROSTER_CAPACITY||!(r->instances[instance].flags&CREATURE_OCCUPIED)||creatures_legacy_spirit(r->instances[instance].form_id)>=4))return 0;if(r->party[target]==instance)return 0;
 for(i=0;i<4;i++)party[i]=r->party[i];
 /* Assignment of an already active INSTANCE is a swap, never a duplicate. */
 if(instance!=EMPTY)for(i=0;i<4;i++)if(i!=target&&party[i]==instance){party[i]=party[target];break;}
 party[target]=(CreatureU8)instance;for(i=0;i<4;i++)count+=party[i]!=EMPTY;if(!count){menu_notice=1;changed();return 0;}
 /* Missing field capabilities stay recoverable from owned collection at any
  * point via this journal. No release/delete path exists, including stories. */
 if(!creatures_party_set(r,party,0))return 0;
 menu_notice=0;synchronize();save_game();return 1;
}
static void menu_move(int delta){CreatureRoster*r=&adventure_save.roster;int i=quickparty_menu_candidate==EMPTY?160:quickparty_menu_candidate;unsigned n;for(n=0;n<161;n++){i=(i+delta+161)%161;if(i==160||(r->instances[i].flags&CREATURE_OCCUPIED)){quickparty_menu_candidate=i==160?EMPTY:i;menu_notice=0;changed();return;}}}
int quickparty_menu_input(int pressed){CreatureRoster*r=&adventure_save.roster;int dir=pressed&DIRECTIONS;if(journal_tab!=2)return 0;
 if(dir==16||dir==32){quickparty_menu_slot=(quickparty_menu_slot+(dir==16?1:3))&3;quickparty_menu_candidate=r->party[quickparty_menu_slot];menu_notice=0;changed();return 1;}
 if(dir==64||dir==128){menu_move(dir==128?1:-1);return 1;}
 if(pressed&256){quickparty_assign((unsigned)quickparty_menu_slot,(unsigned)quickparty_menu_candidate);return 1;}
 if(pressed&4){quickparty_assign((unsigned)quickparty_menu_slot,EMPTY);quickparty_menu_candidate=r->party[quickparty_menu_slot];changed();return 1;}
 return 0;
}
static void arrow(unsigned slot,int x,int y,int col){int j;for(j=0;j<4;j++){if(slot==0||slot==2)rect(x+3-j,y+(slot==0?j:3-j),j*2+1,1,col);else rect(x+(slot==3?j:3-j),y+3-j,1,j*2+1,col);}}
static void card(unsigned slot,int x,int y,int w,int chosen){CreatureInstance*c=member(slot);box(x,y,w,28);if(chosen){rect(x,y,w,2,GOLD);rect(x,y+26,w,2,GOLD);rect(x,y,2,28,GOLD);rect(x+w-2,y,2,28,GOLD);}arrow(slot,x+4,y+10,c?TEAL:PAL_SLATE);if(c)sprite(companion_pixels(creatures_legacy_spirit(c->form_id),0,0),x+w/2-5,y+5,16,16,0);else{rect(x+w/2-2,y+13,9,2,PAL_SLATE);}if(slot==adventure_save.roster.selected_party)rect(x+w-5,y+4,2,2,CREAM);}
void quickparty_draw(void){CreatureInstance*c=quickparty_candidate==EMPTY?0:member((unsigned)quickparty_candidate);box(26,29,188,131);centered(c?name_id(c->form_id):TX_Q_CHOOSE,31,GOLD);card(0,96,50,48,quickparty_candidate==0);card(1,150,77,48,quickparty_candidate==1);card(2,96,103,48,quickparty_candidate==2);card(3,42,77,48,quickparty_candidate==3);centered(TX_Q_RELEASE,130,CREAM);centered(TX_Q_CANCEL,144,TEAL);}
void quickparty_draw_journal(void){CreatureRoster*r=&adventure_save.roster;unsigned i,candidate=(unsigned)quickparty_menu_candidate;CreatureInstance*c=candidate<160&&r->instances[candidate].flags&CREATURE_OCCUPIED?&r->instances[candidate]:0;box(8,31,224,123);centered(menu_notice?TX_Q_LAST_MEMBER:TX_Q_PARTY,32,GOLD);for(i=0;i<4;i++)card(i,16+i*54,52,46,(int)i==quickparty_menu_slot);if(c){unsigned family=creatures_legacy_spirit(c->form_id);sprite(companion_pixels(family,0,0),20,89,16,16,0);text(name_id(c->form_id),43,87,CREAM);}else text(TX_Q_EMPTY,43,87,CREAM);centered(TX_Q_MENU_MOVE,105,TEAL);centered(TX_Q_MENU_ASSIGN,121,CREAM);centered(TX_E_NEXT_GROWTH,138,TEAL);}
