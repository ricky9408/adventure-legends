#ifndef EMBERBOND_FIELD_WORLD_H
#define EMBERBOND_FIELD_WORLD_H
/* Read-only geometry and typed action routing for inherited companion powers.
 * Each chapter owns its exact scene/token backend. Numeric room bounds are
 * checked before weak calls; a missing current backend grants no authority.
 * Weak new hooks keep historical focused host harnesses linkable. Absence of
 * a backend can never authorize a hit. No saved state or cooldown lives here. */
#include "return_game.h"
extern volatile int room;
extern int return_game_clear_box(int,int,int,int) __attribute__((weak));
extern int return_game_supercover(int,int,int,int) __attribute__((weak));
extern unsigned return_game_action_begin(unsigned) __attribute__((weak));
extern int return_game_field_target(unsigned,int*,int*,int*) __attribute__((weak));
extern int return_game_field_hit(unsigned,unsigned,unsigned,unsigned,unsigned) __attribute__((weak));
extern int horizons_game_is_room(unsigned) __attribute__((weak));
extern int horizons_game_clear_box(int,int,int,int) __attribute__((weak));
extern int horizons_game_supercover(int,int,int,int) __attribute__((weak));
extern unsigned horizons_game_action_begin(unsigned) __attribute__((weak));
extern int horizons_game_field_target(unsigned,int*,int*,int*) __attribute__((weak));
extern int horizons_game_field_hit(unsigned,unsigned,unsigned,unsigned,unsigned) __attribute__((weak));
extern void horizons_game_revoke_cast(unsigned) __attribute__((weak));
extern int covenants_game_is_room(unsigned) __attribute__((weak));
extern int covenants_game_clear_box(int,int,int,int) __attribute__((weak));
extern int covenants_game_supercover(int,int,int,int) __attribute__((weak));
extern unsigned covenants_game_action_begin(unsigned) __attribute__((weak));
extern int covenants_game_field_target(unsigned,int*,int*,int*) __attribute__((weak));
extern int covenants_game_field_hit(unsigned,unsigned,unsigned,unsigned,unsigned) __attribute__((weak));
extern void covenants_game_revoke_cast(unsigned) __attribute__((weak));
static inline int field_world_is_room(unsigned area){
 if(area-54u<8u)return 1;
 if(area-62u<8u)return horizons_game_is_room&&horizons_game_is_room(area);
 return area-70u<8u&&covenants_game_is_room&&covenants_game_is_room(area);
}
static inline int field_world_clear_box(int x0,int y0,int x1,int y1){
 if((unsigned)room-54u<8u&&return_game_clear_box)return return_game_clear_box(x0,y0,x1,y1);
 if((unsigned)room-62u<8u&&horizons_game_clear_box)return horizons_game_clear_box(x0,y0,x1,y1);
 if((unsigned)room-70u<8u&&covenants_game_clear_box)return covenants_game_clear_box(x0,y0,x1,y1);
 return 0;
}
static inline int field_world_supercover(int x,int y,int tx,int ty){
 if((unsigned)room-54u<8u&&return_game_supercover)return return_game_supercover(x,y,tx,ty);
 if((unsigned)room-62u<8u&&horizons_game_supercover)return horizons_game_supercover(x,y,tx,ty);
 if((unsigned)room-70u<8u&&covenants_game_supercover)return covenants_game_supercover(x,y,tx,ty);
 return (unsigned)room-54u<24u?0:-1;
}
static inline unsigned field_world_action_begin(unsigned channel){
 if((unsigned)room-54u<8u&&return_game_action_begin)return return_game_action_begin(channel);
 if((unsigned)room-62u<8u&&horizons_game_action_begin)return horizons_game_action_begin(channel);
 if((unsigned)room-70u<8u&&covenants_game_action_begin)return covenants_game_action_begin(channel);
 return 0;
}
static inline int field_world_target(unsigned index,int*x,int*y,int*radius){
 if((unsigned)room-54u<8u&&return_game_field_target)return return_game_field_target(index,x,y,radius);
 if((unsigned)room-62u<8u&&horizons_game_field_target)return horizons_game_field_target(index,x,y,radius);
 if((unsigned)room-70u<8u&&covenants_game_field_target)return covenants_game_field_target(index,x,y,radius);
 return 0;
}
static inline int field_world_hit(unsigned index,unsigned command,unsigned caster,unsigned form,unsigned token){
 if((unsigned)room-54u<8u&&return_game_field_hit)return return_game_field_hit(index,command,caster,form,token);
 if((unsigned)room-62u<8u&&horizons_game_field_hit)return horizons_game_field_hit(index,command,caster,form,token);
 if((unsigned)room-70u<8u&&covenants_game_field_hit)return covenants_game_field_hit(index,command,caster,form,token);
 return 0;
}
static inline void field_world_revoke_cast(unsigned token){
 if((unsigned)room-62u<8u&&horizons_game_revoke_cast)horizons_game_revoke_cast(token);
 else if((unsigned)room-70u<8u&&covenants_game_revoke_cast)covenants_game_revoke_cast(token);
}
#endif
