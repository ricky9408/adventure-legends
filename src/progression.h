#ifndef EMBER_PROGRESSION_H
#define EMBER_PROGRESSION_H
#include "save5.h"
extern Save5State adventure_save;
extern unsigned progression_forms[4], progression_revision;
extern int save_requested, save_resume_state;
int progression_load(void);
void progression_new(void);
void progression_refresh(void);
void progression_select(unsigned legacy_spirit);
void progression_story(void);
void progression_encounter(unsigned room, unsigned enemy);
int progression_field(unsigned event);
int progression_save_begin(void);
int progression_save_step(void);
CreatureInstance *progression_selected(void);
unsigned progression_command(void);
void progression_draw_tab(void);
int progression_menu_input(int pressed);
void progression_draw_confirm(void);
void progression_confirm_input(int pressed);
void progression_draw_evolution(void);
void progression_evolution_tick(void);
int progression_is_sanctuary(void);
#endif
