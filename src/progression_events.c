#include "progression_events.h"
#include "creatures.h"
typedef struct EncounterCreditRow { unsigned char area,first,count; } EncounterCreditRow;
static const EncounterCreditRow chapter_encounters[]={
 {31,180,6},{33,186,6},
 /* Stable explicit IDs: ordinary pools and regulator each have one credit. */
 {39,220,5},{41,225,2},{42,227,1},{43,228,1},{44,229,2},{45,231,1}
};
unsigned progression_encounter_event(unsigned area,unsigned slot){
 unsigned i;
 if(slot>=6)return CREATURE_EVENT_CAPACITY;
 if(area<=29)return area*6+slot;
 for(i=0;i<sizeof chapter_encounters/sizeof chapter_encounters[0];i++){
  const EncounterCreditRow*r=&chapter_encounters[i];
  if(area==r->area&&slot<r->count)return r->first+slot;
 }
 return CREATURE_EVENT_CAPACITY;
}
