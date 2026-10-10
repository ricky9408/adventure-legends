#ifndef ADVENTURE_SAVE_FEEDBACK_H
#define ADVENTURE_SAVE_FEEDBACK_H
#include "save5.h"
extern unsigned save_feedback_revision,save_feedback_background,save_feedback_ordinary;
extern unsigned save_feedback_requests,save_feedback_started,save_feedback_skipped,save_feedback_preemptions,save_feedback_background_frames,save_feedback_blocked_frames;
void save_feedback_reset(void);
void save_feedback_capture(const Save5State*state);
int save_feedback_same(const Save5State*state);
void save_feedback_complete(int success);
void save_feedback_invalidate(void);
void save_feedback_tick(void);
unsigned save_feedback_badge(void);
#endif
