#ifndef EMBER_PROGRESSION_H
#define EMBER_PROGRESSION_H
#include "save5.h"
enum { PROGRESSION_SPIRIT_COUNT=60, PROGRESSION_WATER=4, PROGRESSION_METAL=5,
       PROGRESSION_NORTH_WOOD=6, PROGRESSION_NORTH_FIRE=7,
       PROGRESSION_NORTH_WATER=8, PROGRESSION_NORTH_EARTH=9, PROGRESSION_NORTH_METAL=10, PROGRESSION_SOUTH_FIRST=11, PROGRESSION_MAGMA_FIRST=21, PROGRESSION_UNDERWATER_FIRST=30, PROGRESSION_RETURN_FIRST=38, PROGRESSION_HORIZONS_FIRST=40, PROGRESSION_COVENANTS_FIRST=52 };
extern Save5State adventure_save;
/* Best owned form per engine adapter; regional entries are zero until owned.
 * Selected HUD/body/menu art must use the actual instance, not this cache. */
extern unsigned progression_forms[PROGRESSION_SPIRIT_COUNT], progression_revision;
extern int save_requested, save_resume_state;
/* Enabled identity -> compact explicit family adapter0..59; 255 if unsupported.
 * Persistent family IDs are sparse and must never be used as array indices. */
unsigned progression_form_spirit(unsigned form_id);
unsigned progression_current_spirit(void); /* selected instance, safe0 if absent */
unsigned progression_current_form(void);   /* selected actual form, 0 if absent */
int progression_name_id(unsigned form_id); /* raster UI ID, unknown if disabled */
int progression_command_name_id(unsigned command);
unsigned progression_evolution_context(void);
int progression_load(void);
void progression_new(void);
void progression_refresh(void);
/* Notify only actual selected identity/form/command or four-slot mapping edits. */
void progression_selection_changed(void);
/* Explicit family selection accepts adapters0..59. Keeps exact selected
 * instance if it already matches. Save/load never call this to infer selection. */
void progression_select(unsigned engine_spirit);
void progression_story(void);
void progression_encounter(unsigned room, unsigned enemy);
int progression_field(unsigned event);
int progression_save_begin(void);
int progression_save_step(void);
CreatureInstance *progression_selected(void);
unsigned progression_command(void);
extern int progression_menu_row;
extern int progression_menu_detail;
extern unsigned progression_menu_command;
void progression_menu_reset(void);
void progression_draw_tab(void);
int progression_menu_input(int pressed);
int progression_menu_back(void);
void progression_draw_confirm(void);
void progression_confirm_input(int pressed);
/* Cancel on scene/death/menu abandonment. New/load/save also revoke ownership. */
void progression_evolution_cancel(void);
int progression_evolution_busy(void);
/* One committed, input-inert frame before derived refresh and animation. */
int progression_evolution_handoff(void);
void progression_draw_evolution(void);
void progression_evolution_tick(void);
int progression_is_sanctuary(void);
#endif
