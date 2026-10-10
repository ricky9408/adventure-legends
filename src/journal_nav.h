#ifndef EMBER_JOURNAL_NAV_H
#define EMBER_JOURNAL_NAV_H
enum { JOURNAL_GOAL=0,JOURNAL_MAP=1,JOURNAL_PARTY=2,JOURNAL_GROWTH=3,JOURNAL_GEAR=4,JOURNAL_REGION_FIRST=5,JOURNAL_REGION_LAST=12,JOURNAL_HUB=13,JOURNAL_QUESTS=14,JOURNAL_ITEMS=15,JOURNAL_CONTROLS=16 };
enum { JOURNAL_DISPATCH=0,JOURNAL_CONSUMED=1,JOURNAL_CLOSE=2 };
extern unsigned journal_nav_revision;
extern int journal_nav_category,journal_nav_quest,journal_nav_detail;
void journal_nav_open(void);
int journal_nav_keys(int held_keys,int pressed_keys);
int journal_nav_input(int input);
int journal_nav_draw(void);
#endif
