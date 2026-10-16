#ifndef EMBER_QUICKPARTY_H
#define EMBER_QUICKPARTY_H
/* Field selector and owned-instance journal. ROM-resident, no save schema change.
 * Supports every enabled engine adapter through actual owned-instance refs. */
/* Field candidate is a physical roster index0..159, or CREATURE_EMPTY_SLOT;
 * selected_party remains a four-position party index. */
/* open owns/pauses field input from the L press. visible draws the complete
 * carousel after its hidden preparation interval; never draw a partial list. */
extern int quickparty_open,quickparty_visible,quickparty_candidate,quickparty_hold_updates;
extern unsigned quickparty_revision;
extern int quickparty_menu_slot,quickparty_menu_candidate;
extern int quickparty_menu_detail;
extern unsigned quickparty_menu_command;
/* A neutral L release within12 held updates preserves the original party
 * cycle. Holding13 updates prepares all160 records and displays the picker.
 * Native browse cadence: step on a horizontal edge, wait24 held updates,
 * then step every6 updates. Neutral/ambiguous input resets the delay. */
enum { QUICKPARTY_TAP_UPDATES=12, QUICKPARTY_HOLD_UPDATES=13,
       QUICKPARTY_PREPARE_RECORDS=13,
       QUICKPARTY_REPEAT_DELAY=24, QUICKPARTY_REPEAT_INTERVAL=6 };
void quickparty_reset(int held_keys);
/* PLAY calls once before update. Only buttons held when the picker closes
 * stay masked until their individual physical release; L has its own latch. */
void quickparty_filter_input(int *held_keys,int *pressed_keys);
int quickparty_update(int held_keys,int pressed_keys);
int quickparty_cycle(void);
int quickparty_select(unsigned party_slot);
int quickparty_assign(unsigned party_slot,unsigned roster_slot);
void quickparty_menu_reset(void);
int quickparty_menu_input(int pressed_keys);
int quickparty_menu_back(void);
void quickparty_draw(void);
void quickparty_draw_journal(void);
#endif
