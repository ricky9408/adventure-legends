/* A held L owns input until release, including its opening and closing update.
 * The engine `spirit` remains an adapter0..5, NEVER a quick-party slot.
 * CampaignSave.spirit uses only legacy0..3; the roster owns actual selection. */
#include "quickparty.h"
#include "progression.h"
#include "journal_nav.h"
#include "assets.h"
#include "ui.h"
#include "companion_guide.h"
#include "companion_guide_text.h"
typedef unsigned char u8;
extern volatile int spirit,game_state,room;
extern int journal_tab,gfx_companion_frame;
extern void rect(int,int,int,int,u8),box(int,int,int,int),text(int,int,int,int),centered(int,int,int),sprite(const u8*,int,int,int,int,int),save_game(void),toast(int),sfx(int);
extern const u8 *companion_form_pixels(unsigned,unsigned,unsigned);
extern void game_companion_reseat(void) __attribute__((weak));
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
int quickparty_menu_detail;
unsigned quickparty_menu_command;
static int blocked,had_direction,menu_notice;

static CreatureInstance *member(unsigned slot){CreatureRoster*r=&adventure_save.roster;unsigned i;if(slot>=4)return 0;i=r->party[slot];if(i>=CREATURE_ROSTER_CAPACITY||!(r->instances[i].flags&CREATURE_OCCUPIED))return 0;return progression_form_spirit(r->instances[i].form_id)<PROGRESSION_SPIRIT_COUNT?&r->instances[i]:0;}

static void changed(void){quickparty_revision++;}
static void synchronize(void){CreatureRoster*r=&adventure_save.roster;CreatureInstance*c=member(r->selected_party);if(c){spirit=(int)progression_current_spirit();adventure_save.campaign.spirit=(unsigned)spirit<CREATURE_LEGACY_COUNT?(unsigned)spirit:0;gfx_companion_frame=-1;progression_selection_changed();if(game_companion_reseat)game_companion_reseat();progression_revision++;changed();}}
int quickparty_select(unsigned slot){CreatureRoster*r=&adventure_save.roster;if(!member(slot))return 0;if(r->selected_party==slot)return 0;r->selected_party=slot;synchronize();sfx(2);return 1;}
int quickparty_cycle(void){CreatureRoster*r=&adventure_save.roster;unsigned i;for(i=1;i<=4;i++){unsigned next=(r->selected_party+i)&3;if(member(next))return quickparty_select(next);}return 0;}
void quickparty_reset(int held){if(quickparty_open){quickparty_open=0;changed();}quickparty_candidate=EMPTY;quickparty_hold_updates=0;had_direction=0;blocked=(held&L)!=0;}
int quickparty_update(int held,int pressed){unsigned dir=held&DIRECTIONS;int candidate=EMPTY;
 if(blocked){if(!(held&L))blocked=0;return 1;}
 if(!quickparty_open){if(!(pressed&L))return 0;quickparty_open=1;quickparty_candidate=EMPTY;quickparty_hold_updates=0;had_direction=0;changed();}
 if(pressed&(B|START)){quickparty_reset(held);if(pressed&START){journal_nav_open();game_state=3;}return 1;}
 if(!(held&L)){int choice=quickparty_candidate;int tap=!had_direction&&quickparty_hold_updates<=12;quickparty_reset(0);if(choice!=EMPTY)quickparty_select((unsigned)choice);else if(tap)quickparty_cycle();return 1;}
 if(quickparty_hold_updates<13)quickparty_hold_updates++;
 if(dir){had_direction=1;if(dir==64)candidate=0;else if(dir==16)candidate=1;else if(dir==128)candidate=2;else if(dir==32)candidate=3;if(candidate!=EMPTY&&!member((unsigned)candidate))candidate=EMPTY;if(candidate!=quickparty_candidate){quickparty_candidate=candidate;changed();}}
 return 1;
}
int quickparty_assign(unsigned target,unsigned instance){CreatureRoster*r=&adventure_save.roster;CreatureU8 party[4];unsigned i,count=0,legendary=0;if(target>=4)return 0;if(instance!=EMPTY&&(instance>=CREATURE_ROSTER_CAPACITY||!(r->instances[instance].flags&CREATURE_OCCUPIED)||progression_form_spirit(r->instances[instance].form_id)>=PROGRESSION_SPIRIT_COUNT))return 0;if(r->party[target]==instance)return 0;
 for(i=0;i<4;i++)party[i]=r->party[i];
 /* Assignment of an already active INSTANCE is a swap, never a duplicate. */
 if(instance!=EMPTY)for(i=0;i<4;i++)if(i!=target&&party[i]==instance){party[i]=party[target];break;}
 party[target]=(CreatureU8)instance;for(i=0;i<4;i++)count+=party[i]!=EMPTY;if(!count){menu_notice=1;changed();return 0;}
 /* Explain this exact proposed-party constraint without changing selection,
  * active cast authority, recovery or persistence. Other errors keep their
  * own validator behavior; they must not receive a misleading notice. */
 for(i=0;i<4;i++)if(party[i]<CREATURE_ROSTER_CAPACITY){const CreatureForm*f=creatures_form(r->instances[party[i]].form_id);if(f&&f->rarity)legendary++;}
 if(legendary>1){menu_notice=2;changed();return 0;}
 /* Missing field capabilities stay recoverable from owned collection at any
  * point via this journal. No release/delete path exists, including stories. */
 if(!creatures_party_set(r,party,0))return 0;
 menu_notice=0;synchronize();save_game();return 1;
}
/* Only +/-1 steps enter here. Explicit wrap avoids a software integer divide
 * for every empty storage slot on ARM7TDMI (up to160 checks per key press). */
static void menu_move(int delta){CreatureRoster*r=&adventure_save.roster;int i=(unsigned)quickparty_menu_candidate<CREATURE_ROSTER_CAPACITY?quickparty_menu_candidate:CREATURE_ROSTER_CAPACITY;unsigned n;for(n=0;n<161;n++){i+=delta;if(i<0)i=160;else if(i>160)i=0;if(i==160||((r->instances[i].flags&CREATURE_OCCUPIED)&&progression_form_spirit(r->instances[i].form_id)<PROGRESSION_SPIRIT_COUNT)){quickparty_menu_candidate=i==160?EMPTY:i;menu_notice=0;changed();return;}}}
static CreatureInstance *menu_member(void){CreatureRoster*r=&adventure_save.roster;unsigned i=(unsigned)quickparty_menu_candidate;return i<CREATURE_ROSTER_CAPACITY&&(r->instances[i].flags&CREATURE_OCCUPIED)&&progression_form_spirit(r->instances[i].form_id)<PROGRESSION_SPIRIT_COUNT?&r->instances[i]:0;}
void quickparty_menu_reset(void){CreatureRoster*r=&adventure_save.roster;quickparty_menu_slot=r->selected_party<CREATURE_PARTY_CAPACITY?r->selected_party:0;quickparty_menu_candidate=r->party[quickparty_menu_slot];quickparty_menu_detail=0;quickparty_menu_command=0;companion_guide_page=0;menu_notice=0;changed();}
int quickparty_menu_back(void){if(!quickparty_menu_detail)return 0;quickparty_menu_detail=0;changed();return 1;}
int quickparty_menu_input(int pressed){CreatureRoster*r=&adventure_save.roster;int dir=pressed&DIRECTIONS;if(journal_tab!=2)return 0;
 if(pressed&(B|START))return 0;
 if(pressed&4)return 0;
 if((unsigned)quickparty_menu_slot>=CREATURE_PARTY_CAPACITY)quickparty_menu_slot=r->selected_party<CREATURE_PARTY_CAPACITY?r->selected_party:0;
 if(quickparty_menu_detail){CreatureInstance*c=menu_member();
  if(dir==16||dir==32){quickparty_menu_command=companion_guide_command_next(c,quickparty_menu_command,dir==16?1:-1);changed();return 1;}
  if(dir==64||dir==128){companion_guide_page^=1;changed();return 1;}
  if(dir)return 1;
  if(pressed&1){quickparty_assign((unsigned)quickparty_menu_slot,(unsigned)quickparty_menu_candidate);quickparty_menu_detail=0;changed();return 1;}
  return 0;
 }
 if(dir==16||dir==32){quickparty_menu_slot=(quickparty_menu_slot+(dir==16?1:3))&3;quickparty_menu_candidate=r->party[quickparty_menu_slot];menu_notice=0;changed();return 1;}
 if(dir==64||dir==128){menu_move(dir==128?1:-1);return 1;}
 if(dir)return 1;
 if(pressed&1){CreatureInstance*c=menu_member();if(c&&c->selected_command<2){quickparty_menu_detail=1;quickparty_menu_command=c->equipped[c->selected_command];companion_guide_page=0;changed();}else quickparty_assign((unsigned)quickparty_menu_slot,(unsigned)quickparty_menu_candidate);return 1;}
 return 0;
}
static void arrow(unsigned slot,int x,int y,int col){int j;for(j=0;j<4;j++){if(slot==0||slot==2)rect(x+3-j,y+(slot==0?j:3-j),j*2+1,1,col);else rect(x+(slot==3?j:3-j),y+3-j,1,j*2+1,col);}}
static void card(unsigned slot,int x,int y,int w,int chosen){CreatureInstance*c=member(slot);/* Both callers already paint one enclosing UI_BG panel. */rect(x,y,w,1,PAL_GOLD2);rect(x,y+27,w,1,PAL_GOLD2);rect(x,y,1,28,PAL_GOLD2);rect(x+w-1,y,1,28,PAL_GOLD2);if(chosen){rect(x,y,w,2,GOLD);rect(x,y+26,w,2,GOLD);rect(x,y,2,28,GOLD);rect(x+w-2,y,2,28,GOLD);}arrow(slot,x+4,y+10,c?TEAL:PAL_SLATE);if(c){const u8*p=companion_form_pixels(c->form_id,0,0);if(p)sprite(p,x+w/2-5,y+5,16,16,0);}else{rect(x+w/2-2,y+13,9,2,PAL_SLATE);}if(slot==adventure_save.roster.selected_party)rect(x+w-5,y+4,2,2,CREAM);}
void quickparty_draw(void){CreatureInstance*c=quickparty_candidate==EMPTY?0:member((unsigned)quickparty_candidate);box(26,29,188,131);centered(c?progression_name_id(c->form_id):TX_Q_CHOOSE,31,GOLD);card(0,96,50,48,quickparty_candidate==0);card(1,150,77,48,quickparty_candidate==1);card(2,96,103,48,quickparty_candidate==2);card(3,42,77,48,quickparty_candidate==3);centered(TX_Q_RELEASE,130,CREAM);centered(TX_Q_CANCEL,144,TEAL);}
/* Journal slots alone have fixed even x/width and remain inside the screen.
 * Write each border once; preserve the adjacent interior byte of thin edges.
 * The field picker above retains its established general card renderer. */
extern unsigned short*screen;
static void journal_card(unsigned slot,int chosen){
 static const u8 arrows[4][7]={{8,28,62,127,0,0,0},{1,3,7,15,7,3,1},{127,62,28,8,0,0,0},{8,12,14,15,14,12,8}};
 CreatureInstance*c=member(slot);unsigned row,column,thickness=chosen?2u:1u;
 int x=16+(int)slot*54;unsigned short ink=(unsigned short)((chosen?GOLD:PAL_GOLD2)*257u),*top=screen+52*120+(x>>1);
 for(row=0;row<thickness;row++)for(column=0;column<23;column++){top[row*120+column]=ink;top[(27-row)*120+column]=ink;}
 for(row=thickness;row<28-thickness;row++){unsigned short*p=top+row*120;
  if(chosen){p[0]=ink;p[22]=ink;}else{p[0]=(unsigned short)((p[0]&65280)|(ink&255));p[22]=(unsigned short)((p[22]&255)|(ink&65280));}
 }
 ink=(unsigned short)((c?TEAL:PAL_SLATE)*257u);
 for(row=0;row<7;row++){unsigned bits=arrows[slot][row];unsigned short*p=top+(10+row)*120+2;
  for(column=0;column<4;column++){unsigned mask=bits&3u;if(mask==3)p[column]=ink;else if(mask==1)p[column]=(unsigned short)((p[column]&65280)|(ink&255));else if(mask==2)p[column]=(unsigned short)((p[column]&255)|(ink&65280));bits>>=2;}
 }
 if(c){const u8*p=companion_form_pixels(c->form_id,0,0);if(p)sprite(p,x+18,57,16,16,0);}else rect(x+21,65,9,2,PAL_SLATE);
 if(slot==adventure_save.roster.selected_party)rect(x+41,56,2,2,CREAM);
}
/* Count only browsable owned individuals, never obtained-form history or holes.
 * Empty is a separate action (position 000), not an additional companion. */
static void menu_summary(unsigned *position,unsigned *total,unsigned *party_slot){
 CreatureRoster*r=&adventure_save.roster;unsigned i;*position=*total=0;*party_slot=EMPTY;
 for(i=0;i<CREATURE_ROSTER_CAPACITY;i++)if((r->instances[i].flags&CREATURE_OCCUPIED)&&progression_form_spirit(r->instances[i].form_id)<PROGRESSION_SPIRIT_COUNT){
  ++*total;if((int)i==quickparty_menu_candidate)*position=*total;
 }
 if(menu_member())for(i=0;i<CREATURE_PARTY_CAPACITY;i++)if((int)r->party[i]==quickparty_menu_candidate){*party_slot=i;break;}
}
static void menu_identity(const CreatureInstance*c){
 unsigned position,total,slot;int x;menu_summary(&position,&total,&slot);
 x=companion_guide_number(position,3,18,99,CREAM);companion_guide_text(CG_PARTY_SLASH,x,99,TEAL);
 companion_guide_number(total,3,x+companion_guide_texts[CG_PARTY_SLASH].width+1,99,CREAM);
 if(!c)return;
 companion_guide_text(CG_PARTY_INSTANCE,83,99,TEAL);companion_guide_number((unsigned)quickparty_menu_candidate+1,3,83+companion_guide_texts[CG_PARTY_INSTANCE].width,99,CREAM);
 companion_guide_text(CG_PARTY_LEVEL,133,99,TEAL);companion_guide_number(c->level,2,133+companion_guide_texts[CG_PARTY_LEVEL].width,99,CREAM);
 if(slot<CREATURE_PARTY_CAPACITY){companion_guide_text(CG_PARTY_SLOT,190,99,TEAL);companion_guide_number(slot+1,1,190+companion_guide_texts[CG_PARTY_SLOT].width,99,CREAM);}
 else companion_guide_text(CG_PARTY_RESERVE,190,99,TEAL);
}
void quickparty_draw_journal(void){unsigned i;CreatureInstance*c=menu_member();if(quickparty_menu_detail){companion_guide_draw(c,quickparty_menu_command,(unsigned)quickparty_menu_slot);return;}box(8,31,224,123);centered(menu_notice==1?TX_Q_LAST_MEMBER:menu_notice==2?TX_CV_PARTY_ONE:TX_Q_PARTY,32,GOLD);for(i=0;i<4;i++)journal_card(i,(int)i==quickparty_menu_slot);centered(c?progression_name_id(c->form_id):TX_Q_EMPTY,83,CREAM);menu_identity(c);centered(TX_Q_MENU_MOVE,116,TEAL);if(c)companion_guide_center(CG_PARTY_FOOTER,138,CREAM);else companion_guide_center(CG_PARTY_EMPTY_FOOTER,138,CREAM);}
