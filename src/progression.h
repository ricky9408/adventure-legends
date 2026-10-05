#ifndef EMBER_PROGRESSION_H
#define EMBER_PROGRESSION_H
#include "save5.h"
enum { PROGRESSION_SPIRIT_COUNT=6, PROGRESSION_WATER=4, PROGRESSION_METAL=5 };
extern Save5State adventure_save;
/* Best owned form per engine adapter; regional entries are zero until owned.
 * Selected HUD/body/menu art must use the actual instance, not this cache. */
extern unsigned progression_forms[PROGRESSION_SPIRIT_COUNT], progression_revision;
extern int save_requested, save_resume_state;
/* Enabled identity -> legacy 0..3, Water4, Metal5; 255 if unsupported. */
unsigned progression_form_spirit(unsigned form_id);
unsigned progression_current_spirit(void); /* selected instance, safe0 if absent */
unsigned progression_current_form(void);   /* selected actual form, 0 if absent */
int progression_name_id(unsigned form_id); /* raster UI ID, unknown if disabled */
unsigned progression_evolution_context(void);
int progression_load(void);
void progression_new(void);
void progression_refresh(void);
/* Explicit family selection accepts adapters0..5. Keeps exact selected
 * instance if it already matches. Save/load never call this to infer selection. */
void progression_select(unsigned engine_spirit);
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
