/* Actual input-boundary and extracted engine helpers; synthetic unit inputs. */
#include <assert.h>
#include <stdio.h>
#include "field_controls.h"
#include "power_aim_hold.h"

static unsigned assertions;
#define CHECK(x) do { assert(x); assertions++; } while (0)
static FieldControlState state;
static FieldControlInput read_input(unsigned held,unsigned pressed) {
 return field_controls_read(&state,held,pressed);
}
static void input_contract(void) {
 FieldControlInput in;unsigned held,pressed;
 field_controls_reset(&state,0);
 in=read_input(2,2);CHECK(in.power_pressed==256&&in.power_held==256&&!in.companion_pressed);
 in=read_input(2,0);CHECK(!in.power_pressed&&in.power_held==256);
 in=read_input(0,0);CHECK(!in.power_held);
 in=read_input(256,256);CHECK(in.companion_pressed==256&&!in.power_pressed&&!in.power_held);
 in=read_input(2,2);CHECK(in.power_pressed==256); /* R up, fresh B down. */
 /* Simultaneous presses and either chord order belong to presence control. */
 field_controls_reset(&state,0);in=read_input(258,258);
 CHECK(in.companion_pressed==256&&!in.power_pressed&&!in.power_held);
 in=read_input(2,0);CHECK(!in.power_held); /* R release cannot cast held B. */
 in=read_input(0,0);in=read_input(2,2);CHECK(in.power_pressed==256);
 in=read_input(258,256);CHECK(in.companion_pressed==256&&!in.power_held);
 in=read_input(256,0);in=read_input(258,2);CHECK(!in.power_pressed&&!in.power_held);
 in=read_input(0,0);in=read_input(2,2);CHECK(in.power_pressed==256);
 /* A B held across a modal exit must first be physically released. */
 field_controls_reset(&state,2);in=read_input(2,0);CHECK(!in.power_held);
 in=read_input(0,0);in=read_input(2,2);CHECK(in.power_pressed==256);
 /* Every valid physical key subset preserves independent A/directions/etc.
  * R is removed from the power channel, including while B is absent. */
 for(held=0;held<1024;held++)for(pressed=held;;pressed=(pressed-1)&held) {
  field_controls_reset(&state,0);in=read_input(held,pressed);
  CHECK((in.power_held&~256u)==(held&~258u));
  CHECK((in.power_pressed&~256u)==(pressed&~258u));
  CHECK(in.companion_pressed==(pressed&256u));
  CHECK((in.power_held&256u)==((held&2u)&&!(held&256u)?256u:0u));
  CHECK((in.power_pressed&256u)==((pressed&2u)&&!(held&256u)?256u:0u));
  if(!pressed)break;
 }
}
static void aim_contract(void) {
 PowerAimHold hold={0,0};FieldControlInput in;unsigned n;
 field_controls_reset(&state,0);
 for(n=0;n<90;n++) {
  in=read_input(2,n?0:2);CHECK(power_aim_hold_input(&hold,in.power_held,1));
  CHECK(power_aim_hold_tick(&hold));
 }
 in=read_input(2,0);CHECK(!power_aim_hold_input(&hold,in.power_held,1));
 CHECK(!power_aim_hold_tick(&hold)&&hold.updates==90);
 power_aim_hold_reset(&hold);CHECK(!hold.held&&!hold.updates);
 in=read_input(258,256);CHECK(!power_aim_hold_input(&hold,in.power_held,1));
 in=read_input(2,0);CHECK(!power_aim_hold_input(&hold,in.power_held,1));
 read_input(0,0);in=read_input(2,2);CHECK(power_aim_hold_input(&hold,in.power_held,1));
 CHECK(!power_aim_hold_input(&hold,in.power_held,0));
}

/* Engine helper bodies below come directly from game.c, not test copies. */
#define COLD
#define TX_E_NO_MEMBER 1
#define TX_SUMMONED 2
static int summoned,px=50,py=60,selected=1,ability_cd=77;
static int casts,reanchors,previews,legacy,covenants,selection,sounds,notices;
static int keys,pressed,context_owner,context_calls;
static int progression_selected(void) { return selected; }
static void toast(int id) { notices=id; }
static void ability(void) { CHECK(summoned);CHECK(ability_cd==77);casts++; }
static void game_companion_reanchor(int x,int y) {CHECK(x==px+14&&y==py);reanchors++;}
static void game_power_preview_cancel(void) {previews++;}
static void return_legacy_cancel(void) {legacy++;}
static void covenants_powers_selection_changed(void) {covenants++;}
static void covenants_game_selection_changed(void) {selection++;}
static void sfx(int id) {CHECK(id==2);sounds++;}
static int contextual(unsigned p,unsigned h,int id) {
 CHECK(p==(unsigned)pressed&&h==(unsigned)keys);context_calls++;
 return context_owner==id;
}
#define CONTEXT(chapter,id) static int chapter##_game_input(unsigned p,unsigned h){return contextual(p,h,id);}
CONTEXT(covenants,1) CONTEXT(horizons,2) CONTEXT(return,3)
CONTEXT(underwater,4) CONTEXT(magma,5)
#include "field_controls_engine.inc"
static void engine_contract(void) {
 unsigned owner;
 selected=0;game_field_ability();CHECK(!casts&&!summoned&&!reanchors&&notices==TX_E_NO_MEMBER);
 selected=1;game_field_ability();CHECK(casts==1&&summoned&&reanchors==1);
 game_field_ability();CHECK(casts==2&&reanchors==1);
 game_field_companion_toggle();CHECK(!summoned&&previews==1&&legacy==1&&covenants==1&&selection==1);
 CHECK(sounds==1&&reanchors==2&&ability_cd==77);
 game_field_companion_toggle();CHECK(summoned&&previews==1&&legacy==1&&sounds==2&&notices==TX_SUMMONED);
 for(owner=0;owner<=5;owner++) {
  context_owner=(int)owner;context_calls=0;pressed=2;keys=258;
  CHECK(game_field_context_input()==(owner!=0));
  CHECK(context_calls==(owner?(int)owner:5));
 }
}
int main(void) {
 input_contract();aim_contract();engine_contract();
 printf("%u field input/engine assertions passed\n",assertions);return 0;
}
