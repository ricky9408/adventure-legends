#include "save_feedback.h"
#include "save_snapshot_copy.h"
/* One exact EWRAM copy is reused for active and last verified snapshots. */
static Save5State snapshot;
typedef unsigned SnapshotWord __attribute__((__may_alias__));
typedef char save_feedback_word_aligned[(sizeof(Save5State)%sizeof(SnapshotWord)==0)?1:-1];
static unsigned verified,saved_ticks;
unsigned save_feedback_revision,save_feedback_background,save_feedback_ordinary;
unsigned save_feedback_requests,save_feedback_started,save_feedback_skipped,save_feedback_preemptions,save_feedback_background_frames,save_feedback_blocked_frames;
void save_feedback_reset(void){verified=saved_ticks=save_feedback_background=save_feedback_ordinary=0;save_feedback_requests=save_feedback_started=save_feedback_skipped=save_feedback_preemptions=save_feedback_background_frames=save_feedback_blocked_frames=0;save_feedback_revision++;}
void save_feedback_capture(const Save5State*s){save_snapshot_copy(&snapshot,s);verified=0;saved_ticks=0;save_feedback_started++;save_feedback_revision++;}
int save_feedback_same(const Save5State*s){const SnapshotWord*a=(const SnapshotWord*)&snapshot,*b=(const SnapshotWord*)s;unsigned i;if(!verified)return 0;for(i=0;i<sizeof snapshot/sizeof(SnapshotWord);i++)if(a[i]!=b[i])return 0;return 1;}
void save_feedback_complete(int success){verified=success!=0;saved_ticks=success?80:0;save_feedback_revision++;}
void save_feedback_invalidate(void){verified=0;save_feedback_revision++;}
void save_feedback_tick(void){if(saved_ticks&&!--saved_ticks)save_feedback_revision++;}
unsigned save_feedback_badge(void){return save_feedback_background?1:saved_ticks?2:0;}
