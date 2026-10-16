/* Synthetic capacity input through the production creatures/Save5 APIs.
 * Never gameplay acquisition, emulator RAM injection, or a personal save. */
#include "save5.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static Save5State state,loaded,before_rekey;
static CreatureInstance initial[160];
int main(int argc,char **argv){
 FILE *f;unsigned i,before,after,stride;CreatureU8 party[4];CreatureU32 next;
 assert(argc==3||argc==4);stride=argc==4?256u:1u;
 if(argc==4)assert(!strcmp(argv[3],"stride256"));
 f=fopen(argv[1],"rb");assert(f);assert(fread(save5_test_sram,1,32768,f)==32768);assert(fgetc(f)==EOF);assert(!fclose(f));
 save5_test_reset_writer();save5_test_fail_after(-1);
 assert(save5_load(&state)&&save5_validate(&state)&&creatures_roster_validate(&state.roster));
 before=creatures_roster_count(&state.roster);assert(before==72);
 memcpy(initial,state.roster.instances,sizeof initial);memcpy(party,state.roster.party,4);next=state.roster.next_instance_id;
 for(i=before;i<160;i++)assert(creatures_grant(&state.roster,1,36,60,0,0)==i);
 after=creatures_roster_count(&state.roster);
 assert(after==160&&state.roster.next_instance_id==next+88);
 assert(!memcmp(initial,state.roster.instances,72*sizeof(CreatureInstance))&&!memcmp(party,state.roster.party,4));
 assert(creatures_grant(&state.roster,1,36,60,0,0)==CREATURE_EMPTY_SLOT);
 if(stride==256){
  /* First publish the ordinary160 input, then rekey that decoded state. This
   * also matches the independent two-stage factory's transport sequence. */
  assert(save5_store(&state)&&save5_load(&state)&&save5_validate(&state));
  before_rekey=state;
  for(i=0;i<160;i++)state.roster.instances[i].instance_id=1u+256u*i;
  state.roster.next_instance_id=40706;
  for(i=0;i<160;i++)before_rekey.roster.instances[i].instance_id=state.roster.instances[i].instance_id;
  before_rekey.roster.next_instance_id=state.roster.next_instance_id;
  assert(!memcmp(&before_rekey,&state,sizeof state));
 }
 assert(creatures_roster_validate(&state.roster)&&save5_validate(&state));
 assert(save5_store(&state)&&save5_load(&loaded)&&save5_validate(&loaded));
 assert(!memcmp(&state.roster,&loaded.roster,sizeof state.roster));
 assert(!memcmp(&state.quests,&loaded.quests,sizeof state.quests));
 assert(!memcmp(&state.equipment,&loaded.equipment,sizeof state.equipment));
 assert(!memcmp(&state.economy,&loaded.economy,sizeof state.economy));
 f=fopen(argv[2],"wb");assert(f);assert(fwrite(save5_test_sram,1,32768,f)==32768);assert(!fclose(f));
 printf("{\"synthetic\":true,\"before_count\":%u,\"after_count\":%u,\"appended_real_creatures_grants\":88,\"identity_stride\":%u,\"original72_records_preserved_before_optional_rekey\":true,\"rekey_changes_only_ids_and_next_id\":true,\"real_save5_validate_and_roundtrip\":true,\"content_revision\":%u,\"state_bytes\":%lu}\n",before,after,stride,SAVE5_CONTENT_REVISION,(unsigned long)sizeof state);
 return 0;
}
