#ifndef ADVENTURE_GAME_SHOP_H
#define ADVENTURE_GAME_SHOP_H
extern unsigned game_shop_revision,game_shop_reward_xp,game_shop_reward_gold;
extern int game_shop_selection,game_shop_confirm;
void game_shop_reset(void);
int game_shop_scene_change(void);
int game_shop_later_interact(void);
void game_shop_tick(void);
void game_shop_cancel_items(void);
int game_shop_in_range(void);
int game_shop_interact(void);
int game_shop_update(void);
int game_shop_draw(void);
int game_shop_display_state(void);
void game_shop_draw_items(void);
int game_shop_items_input(int input);
int game_shop_begin_boss(unsigned boss);
void game_shop_reward(unsigned xp,unsigned gold);
unsigned game_shop_reward_visible(void);
void game_shop_draw_reward(void);
#endif
