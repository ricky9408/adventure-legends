#include "travel_feedback.h"
/* Feet rectangles, shared by artwork and gameplay. Never an A-only portal. */
const TravelEntry travel_entries[]={
#include "travel_feedback_entries.inc"
};
const unsigned travel_entry_count=sizeof travel_entries/sizeof travel_entries[0];
static unsigned latched[2];
/* Canonical checkpoints may stand twelve pixels beyond a return dock. Keep
 * that saved spawn safe while walking off it. Arrival and re-arming share
 * one outer band so held movement cannot release the latch too early. */
enum { TRAVEL_CLEARANCE=16 };
typedef char travel_entries_fit_latch[(sizeof travel_entries/sizeof travel_entries[0]<=64)?1:-1];
static int contains(const TravelEntry*e,unsigned room,int x,int y,int margin){return e->room==room&&x>=e->x-margin&&x<e->x+e->w+margin&&y>=e->y-margin&&y<e->y+e->h+margin;}
void travel_feedback_reset(void){latched[0]=latched[1]=0;}
void travel_feedback_release(unsigned entry){if(entry<travel_entry_count)latched[entry>>5]&=~(1u<<(entry&31));}
void travel_feedback_arrive(unsigned room,int x,int y){unsigned i;latched[0]=latched[1]=0;for(i=0;i<travel_entry_count;i++)if(contains(&travel_entries[i],room,x,y,TRAVEL_CLEARANCE))latched[i>>5]|=1u<<(i&31);}
int travel_feedback_step(unsigned room,int x,int y,unsigned held,unsigned locked){unsigned i;
 for(i=0;i<travel_entry_count;i++)if(!contains(&travel_entries[i],room,x,y,TRAVEL_CLEARANCE))latched[i>>5]&=~(1u<<(i&31));
 if(locked||!(held&240u))return -1;
 for(i=0;i<travel_entry_count;i++)if(contains(&travel_entries[i],room,x,y,0)){if(latched[i>>5]&(1u<<(i&31)))return -1;latched[i>>5]|=1u<<(i&31);return (int)i;}
 return -1;
}
