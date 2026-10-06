#include "progression_events.h"
#include "creatures.h"
typedef struct EncounterCreditRow { unsigned char area,first,count; } EncounterCreditRow;
static const EncounterCreditRow southern_encounters[]={{31,180,6},{33,186,6}};
unsigned progression_encounter_event(unsigned area,unsigned slot){
 unsigned i;
 if(slot>=6)return CREATURE_EVENT_CAPACITY;
 if(area<=29)return area*6+slot;
 for(i=0;i<sizeof southern_encounters/sizeof southern_encounters[0];i++){
  const EncounterCreditRow*r=&southern_encounters[i];
  if(area==r->area&&slot<r->count)return r->first+slot;
 }
 return CREATURE_EVENT_CAPACITY;
}
