#ifndef EMBER_QUICKPARTY_H
#define EMBER_QUICKPARTY_H
/* Field selector and owned-instance journal. ROM-resident, no save schema change.
 * Supports every enabled engine adapter through actual owned-instance refs. */
extern int quickparty_open,quickparty_candidate,quickparty_hold_updates;
extern unsigned quickparty_revision;
extern int quickparty_menu_slot,quickparty_menu_candidate;
void quickparty_reset(int held_keys);
int quickparty_update(int held_keys,int pressed_keys);
int quickparty_cycle(void);
int quickparty_select(unsigned party_slot);
int quickparty_assign(unsigned party_slot,unsigned roster_slot);
int quickparty_menu_input(int pressed_keys);
void quickparty_draw(void);
void quickparty_draw_journal(void);
#endif
