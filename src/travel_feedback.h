#ifndef ADVENTURE_TRAVEL_FEEDBACK_H
#define ADVENTURE_TRAVEL_FEEDBACK_H
typedef struct { unsigned char room,action,target,spawn; short x,y; unsigned char w,h; } TravelEntry;
enum { TRAVEL_CAMPAIGN=1,TRAVEL_REGION,TRAVEL_NORTH,TRAVEL_SOUTH,TRAVEL_MAGMA,TRAVEL_UNDERWATER,TRAVEL_RETURN,TRAVEL_HORIZONS,TRAVEL_FERRY,TRAVEL_LIFT,TRAVEL_DIVE,TRAVEL_TRIAL };
extern const TravelEntry travel_entries[];
extern const unsigned travel_entry_count;
void travel_feedback_reset(void);
void travel_feedback_release(unsigned entry);
void travel_feedback_arrive(unsigned room,int x,int y);
int travel_feedback_step(unsigned room,int x,int y,unsigned held,unsigned locked);
#endif
