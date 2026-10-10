/* Current Return causal policy. Never called for revisions1..6. */
static int return_quest_campaign_validate(const Save5Quests *q) {
 static const Save4U8 prerequisites[8][2]={{41,0},{47,0},{48,0},{47,0},{50,0},{49,51},{47,0},{48,50}};
 static const Save4U8 objective_visits[][3]={
  {47,2,2},
  {48,1,8},
  {48,2,8},
  {49,1,16},
  {49,2,16},
  {50,1,32},
  {50,2,4},
  {51,1,64},
  {51,2,64},
  {51,4,128},
  {52,2,8},
  {53,1,1},
  {53,2,4},
  {53,4,8},
  {53,8,16},
 };
 unsigned i,j;
 for(i=46;i<54;++i)if(save5_quest_state(q,i)){
  for(j=0;j<2;++j)if(prerequisites[i-46][j]&&save5_quest_state(q,prerequisites[i-46][j]-1u)!=SAVE5_QUEST_CLAIMED)return 0;
 }
 if(q->region_flags[5]||q->region_flags[11]||q->anchors[5]){
  if(save5_quest_state(q,46)!=SAVE5_QUEST_CLAIMED||!(q->region_flags[5]&1u))return 0;
 }
 if((q->region_flags[5]&36u)&&save5_quest_state(q,49)!=SAVE5_QUEST_CLAIMED)return 0;
 if((q->region_flags[5]&8u)&&save5_quest_state(q,47)!=SAVE5_QUEST_CLAIMED)return 0;
 if((q->region_flags[5]&192u)&&(save5_quest_state(q,48)!=SAVE5_QUEST_CLAIMED||save5_quest_state(q,50)!=SAVE5_QUEST_CLAIMED))return 0;
 for(i=0;i<sizeof objective_visits/sizeof objective_visits[0];++i)
  if((q->objectives[objective_visits[i][0]]&objective_visits[i][1])&&!(q->region_flags[5]&objective_visits[i][2]))return 0;
 return 1;
}
static void return_instance_evidence(ReturnEvidence *e,const CreatureInstance *c) {
 unsigned family=creatures_family_revision(c->form_id,7),level=32,bond=60;
 if(family==39||family==40){
  unsigned i=family-39;
  if(e->count[i]<2)++e->count[i];
 }
 if((family>=1&&family<=10)||(family==39||family==40)){
  unsigned mask=c->trial_flags&3072u;
  if(!mask)return;
  e->trained=1;
  if((family==6&&!(mask&2048u))||family>=39){level=28;bond=45;}
  if(c->level<level||c->bond<bond)e->invalid=1;
 }
}
static int return_sources_validate(const Save5Quests *q,const Save4U8 *obtained,const ReturnEvidence *e) {
 unsigned i;
 if(e->invalid||(e->trained&&save5_quest_state(q,46)!=SAVE5_QUEST_CLAIMED))return 0;
 for(i=0;i<2;++i){
  unsigned claimed=save5_quest_state(q,47+2*i)==SAVE5_QUEST_CLAIMED;
  unsigned base=100+2*i;
  unsigned history=((obtained[base>>3]>>(base&7))|(obtained[(base+1)>>3]>>((base+1)&7)))&1u;
  if(!!e->count[i]!=!!claimed||(claimed&&!history))return 0;
  /* The initial quest authorizes one real copy; additional retained copies
   * have exactly the repeat provenance. Counts never use history bits. */
  if(!!(q->region_flags[11]&(1u<<i))!=(e->count[i]>=2))return 0;
 }
 return 1;
}
static int return_roster_sources_validate(const Save5Quests *q,const CreatureRoster *r) {
 ReturnEvidence e;unsigned i;clear_bytes(&e,sizeof e);
 for(i=0;i<CREATURE_ROSTER_CAPACITY;++i)return_instance_evidence(&e,&r->instances[i]);
 return return_sources_validate(q,r->obtained,&e);
}
