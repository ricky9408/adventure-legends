#ifndef EMBER_COLLECTION_JOURNAL_H
#define EMBER_COLLECTION_JOURNAL_H
#include "creatures.h"
enum { COLLECTION_CONSUMED=1,COLLECTION_OPEN_PARTY=2 };
/* All inspection is read-only. History counts forms, never current instances. */
void collection_journal_open(void);
int collection_journal_back(void);
int collection_journal_input(int);
void collection_journal_draw(void);
unsigned collection_journal_instance(void);
void collection_journal_counts(unsigned*forms,unsigned*families,unsigned*known);
extern unsigned collection_journal_family,collection_journal_form,collection_journal_filter,collection_journal_detail;
#endif
