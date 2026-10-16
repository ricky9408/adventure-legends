/* The field picker owns its opening, preview and closing update.
 * The engine `spirit` remains an adapter0..59, NEVER a quick-party slot.
 * CampaignSave.spirit uses only legacy0..3; the roster owns actual selection. */
#include "quickparty.h"
#include "progression.h"
#include "journal_nav.h"
#include "assets.h"
#include "ui.h"
#include "companion_guide.h"
#include "companion_guide_text.h"
#include "recruit_notice.h"
typedef unsigned char u8;
extern volatile int spirit,game_state,room;
extern int journal_tab,gfx_companion_frame;
extern void rect(int,int,int,int,u8),box(int,int,int,int),text(int,int,int,int),centered(int,int,int),sprite(const u8*,int,int,int,int,int),save_game(void),toast(int),sfx(int);
extern const u8 *companion_form_pixels(unsigned,unsigned,unsigned);
extern void game_companion_reseat(void) __attribute__((weak));
extern void save_game_ordinary(void) __attribute__((weak));
#define L 512
#define B 2
#define START 8
#define DIRECTIONS 240
#define RIGHT 16
#define LEFT 32
#define HANDOFF (1|B|4|START|DIRECTIONS|256)
#define EMPTY CREATURE_EMPTY_SLOT
#define INK 1
#define GOLD PAL_GOLD3
#define CREAM PAL_GOLD4
#define TEAL PAL_TEAL2
int quickparty_open,quickparty_visible,quickparty_candidate=EMPTY,quickparty_hold_updates;
unsigned quickparty_revision;
int quickparty_menu_slot,quickparty_menu_candidate;
int quickparty_menu_detail;
unsigned quickparty_menu_command;
static int blocked,menu_notice,handoff_mask,repeat_direction,repeat_updates;
static int had_direction;
/* A preview is an index of occupied, valid physical roster records. Neither
 * discovery/obtained history nor form identity stands in for an individual. */
static CreatureU8 field_slots[CREATURE_ROSTER_CAPACITY];
static unsigned field_count,field_cursor,field_scan,field_current;

static CreatureInstance *member(unsigned slot){CreatureRoster*r=&adventure_save.roster;unsigned i;if(slot>=4)return 0;i=r->party[slot];if(i>=CREATURE_ROSTER_CAPACITY||!(r->instances[i].flags&CREATURE_OCCUPIED))return 0;return progression_form_spirit(r->instances[i].form_id)<PROGRESSION_SPIRIT_COUNT?&r->instances[i]:0;}

static void changed(void){quickparty_revision++;}
static void synchronize(void){CreatureRoster*r=&adventure_save.roster;CreatureInstance*c=member(r->selected_party);if(c){spirit=(int)progression_current_spirit();adventure_save.campaign.spirit=(unsigned)spirit<CREATURE_LEGACY_COUNT?(unsigned)spirit:0;gfx_companion_frame=-1;progression_selection_changed();if(game_companion_reseat)game_companion_reseat();progression_revision++;changed();}}
static void acknowledge(CreatureInstance*c){if(recruit_notice_acknowledge(c)){progression_revision++;changed();if(save_game_ordinary)save_game_ordinary();}}
int quickparty_select(unsigned slot){CreatureRoster*r=&adventure_save.roster;CreatureInstance*c=member(slot);if(!c)return 0;if(r->selected_party==slot){acknowledge(c);return 0;}r->selected_party=slot;synchronize();acknowledge(c);sfx(2);return 1;}
int quickparty_cycle(void){CreatureRoster*r=&adventure_save.roster;unsigned i;for(i=1;i<=4;i++){unsigned next=(r->selected_party+i)&3;if(member(next))return quickparty_select(next);}return 0;}
static CreatureInstance *field_member(unsigned i){CreatureRoster*r=&adventure_save.roster;CreatureInstance*c;if(i>=CREATURE_ROSTER_CAPACITY)return 0;c=&r->instances[i];return (c->flags&CREATURE_OCCUPIED)&&progression_form_spirit(c->form_id)<PROGRESSION_SPIRIT_COUNT&&creatures_instance_validate(c)?c:0;}
/* Draw only the frozen preview references admitted by field_prepare. The
 * roster cannot change while the selector owns input; rendering still guards
 * physical bounds, ownership and enabled form without repeating XP/bond rules.
 * Opening and commit continue to use the complete instance validator. */
static CreatureInstance *field_draw_member(unsigned i){CreatureRoster*r=&adventure_save.roster;CreatureInstance*c;if(i>=CREATURE_ROSTER_CAPACITY)return 0;c=&r->instances[i];return (c->flags&CREATURE_OCCUPIED)&&progression_form_spirit(c->form_id)<PROGRESSION_SPIRIT_COUNT?c:0;}
static void field_begin(void){CreatureRoster*r=&adventure_save.roster;field_current=r->selected_party<CREATURE_PARTY_CAPACITY?r->party[r->selected_party]:EMPTY;field_count=field_cursor=field_scan=0;quickparty_candidate=EMPTY;}
/* The preserved short-L interval also bounds roster preparation. Input stays
 * owned, so the roster is frozen while at most13 physical records receive the
 * complete validator per update. No partial list is shown or selected. */
static int field_prepare(void){unsigned n;for(n=0;n<QUICKPARTY_PREPARE_RECORDS&&field_scan<CREATURE_ROSTER_CAPACITY;n++,field_scan++)if(field_member(field_scan)){if(field_scan==field_current)field_cursor=field_count;field_slots[field_count++]=(CreatureU8)field_scan;}if(field_scan<CREATURE_ROSTER_CAPACITY)return 0;quickparty_candidate=field_count?field_slots[field_cursor]:EMPTY;return 1;}
static void field_move(int delta){if(field_count>1){if(delta>0)field_cursor=field_cursor+1==field_count?0:field_cursor+1;else field_cursor=field_cursor?field_cursor-1:field_count-1;quickparty_candidate=field_slots[field_cursor];changed();}}
/* The journal keeps its explicit assign/swap behavior below. A field choice
 * instead selects an existing party position, or replaces one position while
 * leaving the displaced record in storage. Every proposed mapping passes the
 * real validator before selected_party and cast authority are synchronized. */
static int field_commit(unsigned instance){CreatureRoster*r=&adventure_save.roster;CreatureInstance*c=field_member(instance);const CreatureForm*f;CreatureU8 party[CREATURE_PARTY_CAPACITY];unsigned i,target=r->selected_party;int mapping_changed,selection_changed,ack;if(!c)return 0;
 for(i=0;i<CREATURE_PARTY_CAPACITY;i++)if(r->party[i]==instance){target=i;break;}
 if(i==CREATURE_PARTY_CAPACITY){if(target>=CREATURE_PARTY_CAPACITY)target=0;f=creatures_form(c->form_id);if(f&&f->rarity)for(i=0;i<CREATURE_PARTY_CAPACITY;i++){CreatureInstance*existing=member(i);const CreatureForm*active=existing?creatures_form(existing->form_id):0;if(active&&active->rarity){target=i;break;}}}
 for(i=0;i<CREATURE_PARTY_CAPACITY;i++)party[i]=r->party[i];
 mapping_changed=party[target]!=instance;selection_changed=r->selected_party!=target;party[target]=(CreatureU8)instance;
 if(!creatures_party_set(r,party,0))return 0;
 r->selected_party=(CreatureU8)target;
 if(mapping_changed||selection_changed)synchronize();
 /* Selection and acknowledgement are one field transaction/revision. */
 ack=recruit_notice_acknowledge(c);if(ack&&!mapping_changed&&!selection_changed){progression_revision++;changed();}
 if((mapping_changed||selection_changed||ack)&&save_game_ordinary)save_game_ordinary();
 if(mapping_changed||selection_changed)sfx(2);
 return mapping_changed||selection_changed;
}
void quickparty_filter_input(int*held,int*pressed){handoff_mask&=*held;*held&=~handoff_mask;*pressed&=~handoff_mask;}
void quickparty_reset(int held){
 /* Non-PLAY resets receive unfiltered modal keys every update. Observe their
  * physical releases too. PLAY/room resets may receive already filtered keys,
  * so they must not clear another still-held button's handoff mask. */
 if(game_state!=1)handoff_mask&=held;
 /* The engine also resets this module every journal update. Keep its live
  * detail page there, but discard stale detail on field/room/start resets. */
 if(game_state!=3||quickparty_open){quickparty_menu_detail=0;quickparty_menu_command=0;companion_guide_page=0;}
 if(quickparty_open)handoff_mask|=held&HANDOFF;
 if(quickparty_visible)changed();
 quickparty_open=quickparty_visible=had_direction=0;quickparty_candidate=EMPTY;quickparty_hold_updates=0;field_count=field_cursor=field_scan=0;field_current=EMPTY;repeat_direction=repeat_updates=0;blocked=(held&L)!=0;
}
int quickparty_update(int held,int pressed){unsigned dir=held&DIRECTIONS;
 /* L is deliberately never filtered: modal resets must see physical release.
  * After a cancellation, the world can resume with only held inputs masked. */
 if(blocked){if(!(held&L))blocked=0;return 0;}
 if(!quickparty_open){if(!(pressed&L))return 0;quickparty_open=1;quickparty_visible=0;field_begin();quickparty_hold_updates=0;had_direction=0;repeat_direction=repeat_updates=0;}
 if(pressed&(B|START)){quickparty_reset(held);if(pressed&START){journal_nav_open();game_state=3;}return 1;}
 if(!(held&L)){int choice=quickparty_candidate,tap=!had_direction&&quickparty_hold_updates<=QUICKPARTY_TAP_UPDATES;quickparty_reset(held);if(choice!=EMPTY)field_commit((unsigned)choice);else if(tap)quickparty_cycle();return 1;}
 if(quickparty_hold_updates<32767)quickparty_hold_updates++;
 /* Preserve the user's exact original short-L party cycle: any held
  * direction disqualifies the <=12-update tap, including ambiguous axes. */
 if(dir)had_direction=1;
 if(!quickparty_visible){if(!field_prepare()||quickparty_hold_updates<QUICKPARTY_HOLD_UPDATES)return 1;quickparty_visible=1;changed();}
 /* Only an unambiguous horizontal direction is a choice. A reversal is an
  * immediate edge; all neutral, vertical and multi-axis states reset repeat. */
 if(dir==LEFT||dir==RIGHT){int delta=dir==RIGHT?1:-1;if(repeat_direction!=delta){repeat_direction=delta;repeat_updates=0;field_move(delta);}else if(++repeat_updates>=QUICKPARTY_REPEAT_DELAY){field_move(delta);repeat_updates=QUICKPARTY_REPEAT_DELAY-QUICKPARTY_REPEAT_INTERVAL;}}
 else repeat_direction=repeat_updates=0;
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
 if(pressed&1){CreatureInstance*c=menu_member();if(c&&c->selected_command<2){acknowledge(c);quickparty_menu_detail=1;quickparty_menu_command=c->equipped[c->selected_command];companion_guide_page=0;changed();}else quickparty_assign((unsigned)quickparty_menu_slot,(unsigned)quickparty_menu_candidate);return 1;}
 return 0;
}
extern unsigned short*screen;
/* The five field cards have fixed even x, width32 and height34. Paint each
 * border halfword once, preserving its interior neighbour for thin edges. */
static void field_card_border(int x,int chosen){unsigned row,column,thickness=chosen?2u:1u;unsigned short ink=(unsigned short)((chosen?GOLD:PAL_GOLD2)*257u),*top=screen+65*120+(x>>1);
 for(row=0;row<thickness;row++)for(column=0;column<16;column++){top[row*120+column]=ink;top[(33-row)*120+column]=ink;}
 for(row=thickness;row<34-thickness;row++){unsigned short*p=top+row*120;if(chosen){p[0]=ink;p[15]=ink;}else{p[0]=(unsigned short)((p[0]&65280)|(ink&255));p[15]=(unsigned short)((p[15]&255)|(ink&65280));}}
}
static void field_card(unsigned instance,int column,int chosen){CreatureRoster*r=&adventure_save.roster;CreatureInstance*c=field_draw_member(instance);int x=32+column*36,y=65;const u8*p=c?companion_form_pixels(c->form_id,0,0):0;
 field_card_border(x,chosen);
 if(p)sprite(p,x+8,y+10,16,16,0);else rect(x+12,y+17,8,2,PAL_SLATE);
 /* The small cream marker identifies the active individual, even when a
  * different form-identical reserve is centered for preview. */
 if(c&&r->selected_party<CREATURE_PARTY_CAPACITY&&r->party[r->selected_party]==instance)rect(x+25,y+4,3,3,CREAM);
 if(recruit_notice_pending(c))recruit_notice_badge(x+3,y+3);
}
static void field_identity(const CreatureInstance*c){int x=companion_guide_number(c?field_cursor+1:0,3,34,108,CREAM);companion_guide_text(CG_PARTY_SLASH,x,108,TEAL);companion_guide_number(field_count,3,x+companion_guide_texts[CG_PARTY_SLASH].width+1,108,CREAM);if(!c)return;
 companion_guide_text(CG_PARTY_INSTANCE,92,108,TEAL);companion_guide_number((unsigned)quickparty_candidate+1,3,92+companion_guide_texts[CG_PARTY_INSTANCE].width,108,CREAM);
 companion_guide_text(CG_PARTY_LEVEL,151,108,TEAL);companion_guide_number(c->level,2,151+companion_guide_texts[CG_PARTY_LEVEL].width,108,CREAM);
}
void quickparty_draw(void){CreatureInstance*c;int offset,limit;if(!quickparty_visible)return;c=field_draw_member((unsigned)quickparty_candidate);limit=field_count<5?(int)field_count:5;box(26,29,188,131);centered(c?progression_name_id(c->form_id):TX_Q_EMPTY,31,GOLD);centered(TX_Q_CHOOSE,47,TEAL);
 /* Five fixed card positions keep the center stable. Small collections show
  * each owned instance once instead of repeating one sprite around the row. */
 if(!limit)field_card(EMPTY,2,1);
 for(offset=-(limit/2);offset<(limit+1)/2;offset++){int index=(int)field_cursor+offset;if(index<0)index+=(int)field_count;else if(index>=(int)field_count)index-=(int)field_count;field_card(field_slots[index],offset+2,offset==0);}
 field_identity(c);centered(TX_Q_RELEASE,129,CREAM);centered(TX_Q_CANCEL,144,TEAL);
}
/* Journal slots alone have fixed even x/width and remain inside the screen.
 * Write each border once; preserve the adjacent interior byte of thin edges.
 * The field picker above has its own horizontal instance cards. */
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
 if(recruit_notice_pending(c))recruit_notice_badge(x+4,54);
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
void quickparty_draw_journal(void){unsigned i;CreatureInstance*c=menu_member();if(quickparty_menu_detail){companion_guide_draw(c,quickparty_menu_command,(unsigned)quickparty_menu_slot);return;}box(8,31,224,123);centered(menu_notice==1?TX_Q_LAST_MEMBER:menu_notice==2?TX_CV_PARTY_ONE:TX_Q_PARTY,32,GOLD);for(i=0;i<4;i++)journal_card(i,(int)i==quickparty_menu_slot);centered(c?progression_name_id(c->form_id):TX_Q_EMPTY,83,CREAM);if(recruit_notice_pending(c))recruit_notice_badge(18,86);menu_identity(c);centered(TX_Q_MENU_MOVE,116,TEAL);if(c)companion_guide_center(CG_PARTY_FOOTER,138,CREAM);else companion_guide_center(CG_PARTY_EMPTY_FOOTER,138,CREAM);}
