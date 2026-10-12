/* Cold loading never writes SRAM and shares the existing scratch allocation.
 * Bank authenticity and decoded-state acceptance remain separate checks. The
 * latter uses the same revision-qualified record/evidence evaluators as the
 * blocking validator, without its repeated whole-roster walks. */
enum {
 LOAD_SCAN_A, LOAD_SCAN_B, LOAD_CHOOSE, LOAD_CLEAR, LOAD_META,
 LOAD_INSTANCES, LOAD_EQUIPMENT, LOAD_VALIDATE, LOAD_COLLECTION,
 LOAD_ROSTER, LOAD_PARTY, LOAD_OBJECTIVES, LOAD_FIELDS, LOAD_REWARDS,
 LOAD_CAMPAIGN, LOAD_CREATURES, LOAD_SOUTH, LOAD_MAGMA, LOAD_WATER,
 LOAD_RETURN, LOAD_HORIZONS, LOAD_COVENANTS, LOAD_GEAR_RECORDS,
 LOAD_GEAR_REFS, LOAD_GEAR_SEEN, LOAD_GEAR_CLAIMS, LOAD_ECONOMY,
 LOAD_PUBLISH
};
static struct {
 Save5State *out;
 unsigned status, phase, index, offset, revision, progress;
 Save4U32 sequence;
} loader;
unsigned save5_load_status(void){return loader.status;}
unsigned save5_load_progress(void){return loader.progress;}
unsigned save5_load_progress_total(void){return 2u*SAVE5_BANK_SIZE+28u*256u;}
void save5_load_cancel(void){loader.status=SAVE5_IDLE;loader.out=0;loader.progress=0;}
int save5_load_begin(Save5State *out){
 if(writer_status==SAVE5_BUSY||save5_preflight_active()||loader.status==SAVE5_BUSY)return 0;
 loader.out=out;loader.status=SAVE5_BUSY;loader.phase=LOAD_SCAN_A;
 loader.index=loader.progress=0;
 bank_valid[0]=bank_valid[1]=0;bank_sequence[0]=bank_sequence[1]=0;
 scan_start(SAVE5_BANK_A,0);return 1;
}
static int load_campaign_valid(const Save5State*s,unsigned r){
 return r==11?save5_campaign_validate(&s->campaign):r==10?history10_save5_campaign_validate(&s->campaign):
  r==9?history9_save5_campaign_validate(&s->campaign):r==8?history8_save5_campaign_validate(&s->campaign):
  r==7?history7_save5_campaign_validate(&s->campaign):history_campaign_validate(&s->campaign,r);
}
static int load_objective_valid(const Save5Quests*q,unsigned i,unsigned r){
 return r==11?quest_objective_validate(q,i):r==10?history10_quest_objective_validate(q,i):
  r==9?history9_quest_objective_validate(q,i):r==8?history8_quest_objective_validate(q,i):
  r==7?history7_quest_objective_validate(q,i):history_objective_validate(q,i,r);
}
static int load_fields_valid(const Save5Quests*q,unsigned r){
 return r==11?quest_fields_validate(q):r==10?history10_quest_fields_validate(q):
  r==9?history9_quest_fields_validate(q):r==8?history8_quest_fields_validate(q):
  r==7?history7_quest_fields_validate(q):history_quest_fields_validate(q,r);
}
static int load_quest_campaign_valid(const Save5State*s,unsigned r){
 return r==11?quest_campaign_validate(&s->campaign,&s->quests):r==10?history10_quest_campaign_validate(&s->campaign,&s->quests):
  r==9?history9_quest_campaign_validate(&s->campaign,&s->quests):r==8?history8_quest_campaign_validate(&s->campaign,&s->quests):
  r==7?history7_quest_campaign_validate(&s->campaign,&s->quests):history_quest_campaign_validate(&s->campaign,&s->quests,r);
}
static int load_creatures_valid(const Save5State*s,unsigned r){
 const Save5Quests*q=&s->quests;const CreatureRoster*c=&s->roster;
 return r<7?history_creatures_validate(q,c->obtained,c->rewards,scan.retained_creatures,scan.southern_evidence):
  r==7?history7_quest_creatures_validate(q,c->obtained,c->rewards,scan.retained_creatures):
  r==8?history8_quest_creatures_validate(q,c->obtained,c->rewards,scan.retained_creatures):
  r==9?history9_quest_creatures_validate(q,c->obtained,c->rewards,scan.retained_creatures):
  r==10?history10_quest_creatures_validate(q,c->obtained,c->rewards,scan.retained_creatures):
  quest_creatures_validate(q,c->obtained,c->rewards,scan.retained_creatures);
}
unsigned save5_load_step(unsigned budget){
 Save5State*s=&scratch.state;unsigned i,n,ok=1,r=loader.revision;
 Save4U8 b[32];
 if(loader.status!=SAVE5_BUSY||!budget)return loader.status;
 if(budget>1024)budget=1024;
#ifdef SAVE5_HOST_TEST
 test_step_work=budget;
#endif
 /* At most one phase per call, including cold bank and semantic boundaries. */
 switch(loader.phase){
 case LOAD_SCAN_A:case LOAD_SCAN_B:{
  unsigned bank=loader.phase==LOAD_SCAN_B,before=scan.position;
  (void)scan_run(budget);loader.progress+=scan.position-before;
  if(scan.valid&&scan.position<SAVE5_BANK_SIZE)return SAVE5_BUSY;
  bank_valid[bank]=scan.valid;bank_sequence[bank]=scan.sequence;
  if(!bank){loader.phase=LOAD_SCAN_B;scan_start(SAVE5_BANK_B,0);}
  else loader.phase=LOAD_CHOOSE;
  return SAVE5_BUSY;
 }
 case LOAD_CHOOSE:{
  int active=newest_bank();
  if(active>=0){
   loader.offset=active?SAVE5_BANK_B:SAVE5_BANK_A;loader.sequence=bank_sequence[active];
   read_bytes(b,loader.offset+12,2);loader.revision=get16(b);
  }else{
   CampaignSave legacy;
#ifdef SAVE5_HOST_TEST
   read_bytes(save4_test_sram,0,256);
#endif
   if(!save4_load(&legacy)){ok=0;break;}
   clear_bytes(s,sizeof *s);encode_campaign(b,&legacy);decode_campaign(&s->campaign,b);
   s->campaign.sequence=legacy.sequence;s->campaign.loaded_version=legacy.loaded_version;
   equipment_init(&s->equipment);
   if(!creatures_migrate_legacy(&s->roster,legacy.chapter_flags,legacy.spirit)){ok=0;break;}
   /* Legacy migration receives the full current decoded-state check too. */
   loader.revision=11;loader.phase=LOAD_VALIDATE;return SAVE5_BUSY;
  }
  break;
 }
 case LOAD_CLEAR:clear_bytes(s,sizeof *s);break;
 case LOAD_META:{
  unsigned o=loader.offset;
  read_bytes(b,o+32,15);decode_campaign(&s->campaign,b);s->campaign.sequence=loader.sequence;
  read_bytes(s->roster.seen,o+96,16);read_bytes(s->roster.obtained,o+112,16);read_bytes(s->roster.rewards,o+128,16);
  read_bytes(b,o+4000,12);copy_bytes(s->roster.party,b,4);s->roster.selected_party=b[4];s->roster.next_instance_id=get32(b+8);
  read_bytes(s->roster.expedition_bond,o+4296,160);read_bytes(s->roster.expedition_events,o+4456,64);read_bytes(s->roster.lifetime_field_aid,o+4520,16);
  if(r==1)history_starter_init(&s->equipment);
  else{
   read_bytes(s->quests.states,o+4032,16);
   for(i=0;i<64;++i){read_bytes(b,o+4048+i*2,2);s->quests.objectives[i]=get16(b);}
   read_bytes(s->quests.rewards,o+4176,8);read_bytes(s->quests.variables,o+4184,64);
   read_bytes(s->quests.region_flags,o+4248,32);read_bytes(s->quests.anchors,o+4280,16);
   read_bytes(s->equipment.equipped,o+4928,5);read_bytes(s->equipment.seen,o+4944,64);read_bytes(s->equipment.reward_claims,o+5024,8);
  }
  if(r==10||r==11){read_bytes(b,o+SAVE5_ECONOMY_OFFSET,32);decode_economy(&s->economy,b);}
  normalize_resume(&s->campaign,r);loader.index=0;break;
 }
 case LOAD_INSTANCES:
  for(i=0;i<8&&loader.index<160;++i,++loader.index){read_bytes(b,loader.offset+160+loader.index*24,24);decode_instance(&s->roster.instances[loader.index],b);}
  if(loader.index<160)return SAVE5_BUSY;
  loader.index=0;break;
 case LOAD_EQUIPMENT:
  if(r!=1)for(i=0;i<8&&loader.index<48;++i,++loader.index){read_bytes(b,loader.offset+4544+loader.index*8,8);decode_equipment_record(&s->equipment.bag[loader.index],b);}
  if(r!=1&&loader.index<48)return SAVE5_BUSY;
  loader.index=0;break;
 case LOAD_VALIDATE:
  clear_bytes(&scan,sizeof scan);scan.revision=r;
  clear_bytes(scratch.bytes+SAVE5_RESERVED_OFFSET,640);
  copy_bytes(scan.collection,s->roster.seen,16);copy_bytes(scan.collection+16,s->roster.obtained,16);copy_bytes(scan.collection+32,s->roster.rewards,16);
  ok=load_campaign_valid(s,r);break;
 case LOAD_COLLECTION:ok=scan_collection()&&s->roster.next_instance_id!=0;loader.index=0;break;
 case LOAD_ROSTER:
  n=budget/160;if(!n)n=1;if(n>8)n=8;
  for(i=0;i<n&&loader.index<160;++i,++loader.index){
   const CreatureInstance*c=&s->roster.instances[loader.index];
   encode_instance(scan.block,c);
   if(!scan_instance(loader.index)||s->roster.expedition_bond[loader.index]>10||
      (!c->form_id&&s->roster.expedition_bond[loader.index])||
      (c->form_id&&c->instance_id>=s->roster.next_instance_id)){ok=0;break;}
  }
  if(ok&&loader.index<160)return SAVE5_BUSY;
  loader.index=0;break;
 case LOAD_PARTY:
  clear_bytes(scan.block,32);copy_bytes(scan.block,s->roster.party,4);scan.block[4]=s->roster.selected_party;put32(scan.block+8,s->roster.next_instance_id);
  ok=scan_party();break;
 case LOAD_OBJECTIVES:
  for(i=0;i<16&&loader.index<64;++i,++loader.index)if(!load_objective_valid(&s->quests,loader.index,r)){ok=0;break;}
  if(ok&&loader.index<64)return SAVE5_BUSY;
  loader.index=0;break;
 case LOAD_FIELDS:ok=load_fields_valid(&s->quests,r);break;
 case LOAD_REWARDS:
  for(i=0;i<8&&ok;++i)ok=history_reward_validate(&s->quests,i)&&(r<7||(r==10?history10_quest_reward_validate(&s->quests,i):quest_reward_validate(&s->quests,i)));
  break;
 case LOAD_CAMPAIGN:ok=load_quest_campaign_valid(s,r);break;
 case LOAD_CREATURES:ok=load_creatures_valid(s,r);break;
 case LOAD_SOUTH:ok=r<7?1:r==10?history10_southern_sources_validate(&s->quests,s->roster.obtained,scan.southern_evidence):southern_sources_validate(&s->quests,s->roster.obtained,scan.southern_evidence);break;
 case LOAD_MAGMA:ok=r<5?1:r==10?history10_magma_sources_validate(&s->quests,s->roster.obtained,&scan.magma):magma_sources_validate(&s->quests,s->roster.obtained,&scan.magma);break;
 case LOAD_WATER:ok=r<6?1:r==10?history10_underwater_sources_validate(&s->quests,s->roster.obtained,&scan.underwater):underwater_sources_validate(&s->quests,s->roster.obtained,&scan.underwater);break;
 case LOAD_RETURN:ok=r<7?1:r==10?history10_return_sources_validate(&s->quests,s->roster.obtained,&scan.returning):return_sources_validate(&s->quests,s->roster.obtained,&scan.returning);break;
 case LOAD_HORIZONS:ok=r<8?1:r==8?history8_horizons_sources_validate(&s->quests,s->roster.obtained,&scan.horizons):r==9?history9_horizons_sources_validate(&s->quests,s->roster.obtained,&scan.horizons):r==10?history10_horizons_sources_validate(&s->quests,s->roster.obtained,&scan.horizons):horizons_sources_validate(&s->quests,s->roster.obtained,&scan.horizons);break;
 case LOAD_COVENANTS:ok=r<9?1:r==9?history9_covenants_sources_validate(&s->quests,s->roster.obtained,&scan.covenants):r==10?history10_covenants_sources_validate(&s->quests,s->roster.obtained,&scan.covenants):covenants_sources_validate(&s->quests,s->roster.obtained,&scan.covenants);loader.index=0;break;
 case LOAD_GEAR_RECORDS:
  if(r==1){ok=history_starter_validate(&s->equipment);break;}
  for(i=0;i<8&&loader.index<48;++i,++loader.index){encode_equipment_record(scan.block,&s->equipment.bag[loader.index]);if(!scan_equipment_record(loader.index)){ok=0;break;}}
  if(ok&&loader.index<48)return SAVE5_BUSY;
  loader.index=0;break;
 case LOAD_GEAR_REFS:ok=r==1?1:r==11?equipment_refs_validate(&s->equipment):history_equipment_refs_validate(&s->equipment,r);break;
 case LOAD_GEAR_SEEN:
  if(r==1)break;
  for(i=0;i<8&&loader.index<64;++i,++loader.index)if(!equipment_seen_byte(loader.index,s->equipment.seen[loader.index])){ok=0;break;}
  if(ok&&loader.index<64)return SAVE5_BUSY;
  loader.index=0;break;
 case LOAD_GEAR_CLAIMS:
  ok=r==1?1:(zero_bytes(s->equipment.settings_reserved,11)&&zero_bytes(s->equipment.wallet_key_reserved,16)&&zero_bytes(s->equipment.reserved,24)&&
   (r==11?quest_equipment_validate(&s->quests,&s->equipment):history_equipment_claims_validate(&s->quests,&s->equipment,r)));break;
 case LOAD_ECONOMY:
  ok=r<10?zero_bytes((const Save4U8*)&s->economy,32):r==10?history10_economy_validate(&s->economy,s->campaign.chapter_flags):
   economy_state_validate(&s->economy,s->campaign.chapter_flags)&&save5_later_claims_validate(&s->quests,&s->economy);break;
 case LOAD_PUBLISH:
  if(loader.out)copy_state(loader.out,s);
  loader.out=0;loader.status=SAVE5_DONE;loader.progress=save5_load_progress_total();return SAVE5_DONE;
 default:ok=0;break;
 }
 if(!ok){loader.out=0;loader.status=SAVE5_FAILED;return SAVE5_FAILED;}
 loader.progress+=256;++loader.phase;return SAVE5_BUSY;
}
