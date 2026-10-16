#!/usr/bin/env python3
"""Extracted context-input regressions; synthetic host ownership evidence only.

The actual Underwater and Return input functions, region predicates, and Return
repeat-prompt cleanup are compiled unchanged. Reach checks and toast delivery
are explicit stubs: these tests prove input ownership, not reach geometry,
controller-earned progress, native timing, or on-screen feedback.
"""
from pathlib import Path
import os
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def extract(source, signature):
    """Keep the actual complete function body, including its declarations."""
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


DRIVER = r'''
#include <stdio.h>
#include <stdlib.h>

#define COLD
enum { PLAY=1, KEY_B=2, B=2, R=256, TX_RT_WAIT=1001 };
static int room,game_state,reset_pending,reset_confirm,invite_confirm,repeat_active;
static int reach_x,reach_y,reach_allowed,prompt_x,prompt_y,prompt_allowed;
static unsigned close_calls,prompt_calls,toast_calls,assertions,cases;
static int last_toast;
#define CHECK(condition) do { assertions++; if(!(condition)) { \
 fprintf(stderr,"context assertion failed at line %d: %s\n",__LINE__,#condition); \
 exit(1); } } while(0)

/* Deliberately controlled reach outcomes. Actual facing/reach geometry is not
 * substituted with a synthetic distance model or claimed as tested here. */
static int close(int x,int y) {
 close_calls++;return reach_allowed&&x==reach_x&&y==reach_y;
}
static int prompt_close(int x,int y) {
 prompt_calls++;return prompt_allowed&&x==prompt_x&&y==prompt_y;
}
static void toast(int id) {toast_calls++;last_toast=id;}

#include "field_context_actual.inc"

static void setup(int area) {
 room=area;game_state=PLAY;reset_pending=reset_confirm=invite_confirm=repeat_active=0;
 reach_x=reach_y=prompt_x=prompt_y=0;reach_allowed=prompt_allowed=0;
 close_calls=prompt_calls=toast_calls=0;last_toast=0;
}
static void expect_underwater(unsigned pressed,unsigned held,int consumed,int pending) {
 cases++;CHECK(underwater_game_input(pressed,held)==consumed);
 CHECK(reset_pending==pending);CHECK(!toast_calls&&!close_calls&&!prompt_calls);
}
static void expect_return(unsigned pressed,unsigned held,int consumed,int reset,
                          int invite,unsigned toasts) {
 cases++;CHECK(return_game_input(pressed,held)==consumed);
 CHECK(reset_confirm==reset);CHECK(invite_confirm==invite);
 CHECK(toast_calls==toasts);CHECK(last_toast==(toasts?TX_RT_WAIT:0));
}

static void reset_ownership(void) {
 unsigned pressed,extra,pending;int area;
 const unsigned held_extra[]={0,B,R|B};
 /* Every physical-key mask, including B+R and B+A, is owned by a pending
  * reset. R, held B without an edge, and all unrelated buttons never cancel.
  * Each call begins with independent synthetic state, not a personal save. */
 for(area=46;area<=53;area++)for(pending=0;pending<=1;pending++)
  for(pressed=0;pressed<1024;pressed++)for(extra=0;extra<3;extra++) {
   int consumed=(pending&&(pressed&B))!=0;
   setup(area);reset_pending=(int)pending;
   expect_underwater(pressed,pressed|held_extra[extra],consumed,
                     consumed?0:(int)pending);
  }
 for(area=54;area<=61;area++)for(pending=0;pending<=1;pending++)
  for(pressed=0;pressed<1024;pressed++)for(extra=0;extra<3;extra++) {
   int consumed=(pending&&(pressed&B))!=0;
   setup(area);reset_confirm=(int)pending;
   expect_return(pressed,pressed|held_extra[extra],consumed,
                 consumed?0:(int)pending,0,0);
  }
 /* A cancellation consumes exactly the confirming edge. A later B is free
  * for the field ability, and continuing to hold B is not another edge. */
 for(area=46;area<=53;area++) {
  setup(area);reset_pending=1;
  expect_underwater(B,B,1,0);expect_underwater(0,B,0,0);
  expect_underwater(B,B,0,0);
 }
 for(area=54;area<=61;area++) {
  setup(area);reset_confirm=1;
  expect_return(B,B,1,0,0,0);expect_return(0,B,0,0,0,0);
  expect_return(B,B,0,0,0,0);
 }
}

static void state_and_room_boundaries(void) {
 unsigned i,j;const int other_states[]={0,2,3,9};
 const int underwater_outside[]={-1,0,16,30,45,54,61,77};
 const int return_outside[]={-1,0,16,30,46,53,62,77};
 for(i=0;i<sizeof(other_states)/sizeof(other_states[0]);i++) {
  setup(46);game_state=other_states[i];reset_pending=1;
  expect_underwater(B|R,B|R,0,1);
  /* Even a departed or old-room invitation must remain untouched while a
   * modal state owns the controller. No reach or notification is evaluated. */
  for(j=0;j<3;j++) {
   setup(j==0?54:j==1?16:30);game_state=other_states[i];
   reset_confirm=1;invite_confirm=j==0?1:j==1?47:49;
   expect_return(B|R,B|R,0,1,invite_confirm,0);
   CHECK(!close_calls&&!prompt_calls);
  }
 }
 for(i=0;i<sizeof(underwater_outside)/sizeof(underwater_outside[0]);i++) {
  setup(underwater_outside[i]);reset_pending=1;
  expect_underwater(B,B,0,1);
 }
 for(i=0;i<sizeof(return_outside)/sizeof(return_outside[0]);i++) {
  setup(return_outside[i]);reset_confirm=1;
  expect_return(B,B,0,1,0,0);CHECK(!close_calls&&!prompt_calls);
 }
}

static void invitation_priority(void) {
 unsigned i,pending,button;const unsigned buttons[]={0,R,B,B|R};
 const int areas[]={55,58},sources[]={17,18},xs[]={208,400},ys[]={80,240};
 for(i=0;i<2;i++)for(pending=0;pending<=1;pending++)
  for(button=0;button<sizeof(buttons)/sizeof(buttons[0]);button++) {
   unsigned pressed=buttons[button];int consumed=(pressed&B)!=0;
   setup(areas[i]);reset_confirm=(int)pending;invite_confirm=1;
   repeat_active=sources[i];prompt_allowed=1;prompt_x=xs[i];prompt_y=ys[i];
   expect_return(pressed,pressed|B,consumed,consumed?0:(int)pending,
                 consumed?0:1,(unsigned)consumed);
   CHECK(prompt_calls==1&&!close_calls);
   if(consumed) {
    /* Cancellation of the invitation takes priority over reset-only feedback.
     * Neither prompt reopens itself on the next press. */
    toast_calls=0;last_toast=0;
    expect_return(B,B,0,0,0,0);
   }
  }
 /* Walking out of the active invitation reach discards just the prompt.
  * The physical B is unconsumed unless a separate reset was pending. */
 for(i=0;i<2;i++)for(pending=0;pending<=1;pending++) {
  setup(areas[i]);reset_confirm=(int)pending;invite_confirm=1;
  repeat_active=sources[i];prompt_x=xs[i];prompt_y=ys[i];
  expect_return(B,B,(int)pending,0,0,0);CHECK(prompt_calls==1);
  setup(areas[i]);invite_confirm=1;repeat_active=sources[i];
  expect_return(0,0,0,0,0,0);CHECK(prompt_calls==1);
  /* A prompt from the other encounter is stale even at the current reach. */
  setup(areas[i]);invite_confirm=1;repeat_active=sources[1-i];
  prompt_allowed=1;prompt_x=xs[i];prompt_y=ys[i];
  expect_return(B,B,0,0,0,0);CHECK(!prompt_calls&&!close_calls);
 }
}

static void old_room_invitations(void) {
 unsigned i,pending,button;const unsigned buttons[]={0,R,B,B|R};
 const int areas[]={16,30},invites[]={47,49},xs[]={368,448},ys[]={152,192};
 for(i=0;i<2;i++)for(pending=0;pending<=1;pending++)
  for(button=0;button<sizeof(buttons)/sizeof(buttons[0]);button++) {
   unsigned pressed=buttons[button];int consumed=(pressed&B)!=0;
   setup(areas[i]);invite_confirm=invites[i];reset_confirm=(int)pending;
   reach_allowed=1;reach_x=xs[i];reach_y=ys[i];
   /* These explicitly supported old-room invitations precede Return's room
    * filter. The unrelated region reset flag remains untouched here. */
   expect_return(pressed,pressed|B,consumed,(int)pending,
                 consumed?0:invites[i],(unsigned)consumed);
   CHECK(close_calls==1&&!prompt_calls);
   if(consumed) {
    toast_calls=0;last_toast=0;
    expect_return(B,B,0,(int)pending,0,0);
   }
  }
 for(i=0;i<2;i++) {
  /* Leaving the reach, entering the other old room, or leaving both old
   * rooms clears the invitation without stealing the field ability edge. */
  setup(areas[i]);invite_confirm=invites[i];reset_confirm=1;
  reach_x=xs[i];reach_y=ys[i];
  expect_return(B,B,0,1,0,0);CHECK(close_calls==1);
  setup(areas[1-i]);invite_confirm=invites[i];reset_confirm=1;
  reach_allowed=1;reach_x=xs[i];reach_y=ys[i];
  expect_return(B,B,0,1,0,0);CHECK(!close_calls);
  setup(0);invite_confirm=invites[i];reset_confirm=1;
  expect_return(B,B,0,1,0,0);CHECK(!close_calls);
 }
}

int main(void) {
 reset_ownership();state_and_room_boundaries();invitation_priority();
 old_room_invitations();
 printf("%u synthetic context transitions, %u assertions passed\n",cases,assertions);
 return 0;
}
'''


def source_order_contract():
    """Source inspection only: this is not an executed update-loop proof."""
    source = (ROOT / 'src/game.c').read_text()
    update = extract(source, 'void update(void)')
    order = (
        'context_owned=game_field_context_input();',
        'if(context_owned)game_power_preview_cancel();',
        'controls=field_controls_read(',
        'aim_holding=game_power_aim_hold(',
        'underwater_powers_tick();',
        'if(context_owned){walk=0;game_attacks_suspend();goto movement_done;}',
        'underwater_powers_input(controls.power_pressed',
        'game_field_ability();',
    )
    positions = [update.index(fragment) for fragment in order]
    assert positions == sorted(positions), 'Context must own B before power dispatch'
    return len(order) - 1


def main():
    underwater = (ROOT / 'src/underwater_game.c').read_text()
    returning = (ROOT / 'src/return_game.c').read_text()
    interaction = (ROOT / 'src/return_interact.inc').read_text()
    actual = '\n'.join((
        extract(underwater, 'int underwater_game_is_room(unsigned a)'),
        extract(returning, 'int return_game_is_room(unsigned a)'),
        extract(interaction, 'static void clear_departed_repeat_prompt(void)'),
        extract(underwater, 'COLD int underwater_game_input(unsigned pressed,unsigned held)'),
        extract(interaction, 'int return_game_input(unsigned pressed,unsigned held)'),
    ))
    with tempfile.TemporaryDirectory(prefix='field-context-') as temporary:
        temporary = Path(temporary)
        (temporary / 'field_context_actual.inc').write_text(actual)
        driver = temporary / 'field_context_driver.c'
        driver.write_text(DRIVER)
        for label, flags in [('strict', []), ('sanitized', [
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
            target = temporary / label
            subprocess.run([os.environ.get('HOST_CC', 'cc'), '-std=c99', '-O2',
                            '-Wall', '-Wextra', '-Werror', '-pedantic', *flags,
                            str(driver), '-o', str(target)], check=True, cwd=ROOT)
            result = subprocess.run([str(target)], check=True, cwd=ROOT,
                                    capture_output=True, text=True, env={**os.environ,
                                        'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
                                        'UBSAN_OPTIONS': 'halt_on_error=1'})
            print(label + ': ' + result.stdout.strip())
    checks = source_order_contract()
    print(f'source-only: {checks} context-before-power ordering checks passed')


if __name__ == '__main__':
    main()
