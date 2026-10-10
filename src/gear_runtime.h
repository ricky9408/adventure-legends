#ifndef EMBERBOND_GEAR_RUNTIME_H
#define EMBERBOND_GEAR_RUNTIME_H
#include "equipment.h"
#include "weapon_actions.h"
/* Gear8 plus earned Sky Feather8 and Caldera Bell4. */
#define GAME_MAX_POWER_RECOVERY 20u
extern EquipmentStats gear_stats;
extern WeaponAttack weapon_action;
extern WeaponArrow player_arrows[2];
/* Authoritative q4 health. Legacy hp/Enemy.hp/boss_hp symbols are ceiling-heart
 * observation caches for old route tools, never fractional-damage storage. */
extern int hero_hp_q4,enemy_hp_q4[6],boss_hp_q4;
extern unsigned char enemy_phases[6],enemy_stagger_ticks[6];
void game_combat_tick(void);
void game_enemy_stagger(unsigned index,unsigned bonus);
void game_gear_bonus_stats(EquipmentStats *stats);
/* Only for the raw after-stats returned by a successful live equipment_equip.
 * The caller owns validation; current passive bonuses are applied once here. */
void game_gear_apply_stats(unsigned clamped_hp_q4,const EquipmentStats *fresh);
void game_health_refresh(int fill);
void game_health_fill(void);
void game_health_heal(unsigned amount_q4);
void game_health_hurt(unsigned base_q4,unsigned attacker_phase);
void game_enemy_health_reset(void);
void game_enemy_hurt(unsigned index,unsigned base_q4,unsigned attack_q4,unsigned phase);
void game_boss_health_set(unsigned hearts);
void game_boss_hurt(unsigned base_q4,unsigned attack_q4,unsigned phase);
unsigned game_weapon_class(void);
unsigned game_power_cooldown(unsigned base_updates);
unsigned game_companion_phase(void);
void game_attacks_reset(void);
void game_attacks_suspend(void);
void game_attack_update(int held,int pressed);
int game_melee_hit(unsigned target,int x,int y,int boss);
void game_arrows_update(void);
void game_draw_health(void);
void game_draw_weapon(void);
void game_draw_enemy_phase(unsigned index,int x,int y);
#endif
