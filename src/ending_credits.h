#ifndef EMBER_ENDING_CREDITS_H
#define EMBER_ENDING_CREDITS_H
#if defined(__arm__)
#define ENDING_CODE __attribute__((section(".text.rom"),long_call,noinline))
#else
#define ENDING_CODE
#endif
extern unsigned ending_credits_phase,ending_credits_scroll,ending_credits_revision,ending_credits_armed;
ENDING_CODE void ending_credits_begin(void);
ENDING_CODE int ending_credits_update(void);
ENDING_CODE int ending_credits_draw(void);
ENDING_CODE void ending_credits_card_hint(void);
#endif
