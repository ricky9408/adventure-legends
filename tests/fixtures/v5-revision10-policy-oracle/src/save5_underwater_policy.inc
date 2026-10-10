/* Revision6 causal rules are deliberately isolated from immutable r1..5.
 * None of these functions are used to reinterpret old bank fields. */
static int underwater_quest_campaign_validate(const Save5Quests *q) {
 static const Save4U8 visits[6]={4,2,8,4,32,8};
 unsigned i;
 if(q->region_flags[4]||q->region_flags[10]||q->region_flags[17]||
    q->region_flags[20]||q->region_flags[21]){
  if(save5_quest_state(q,32)!=SAVE5_QUEST_CLAIMED||!(q->region_flags[4]&1u))return 0;
 }
 for(i=38;i<46;++i)if(save5_quest_state(q,i)&&
  (!(q->region_flags[4]&1u)||save5_quest_state(q,32)!=SAVE5_QUEST_CLAIMED))return 0;
 if(save5_quest_state(q,41)&&save5_quest_state(q,38)!=SAVE5_QUEST_CLAIMED)return 0;
 if(save5_quest_state(q,42)&&save5_quest_state(q,39)!=SAVE5_QUEST_CLAIMED)return 0;
 if(save5_quest_state(q,45)&&save5_quest_state(q,40)!=SAVE5_QUEST_CLAIMED)return 0;
 if(save5_quest_state(q,40)||(q->region_flags[4]&240u)){
  if(save5_quest_state(q,38)!=SAVE5_QUEST_CLAIMED||save5_quest_state(q,39)!=SAVE5_QUEST_CLAIMED)return 0;
 }
 for(i=5;i<8;++i)if((q->region_flags[4]&(1u<<i))&&
  !has_all(q->objectives[40],(1u<<(i-4))-1u))return 0;
 for(i=0;i<6;++i)if((q->region_flags[10]&(1u<<i))&&!(q->region_flags[4]&visits[i]))return 0;
 if(q->region_flags[20]&&!(q->region_flags[4]&32u))return 0;
 if(q->region_flags[21]&&!(q->region_flags[4]&8u))return 0;
 if((q->region_flags[10]&16u)&&q->region_flags[20]!=3)return 0;
 if((q->region_flags[10]&32u)&&q->region_flags[21]!=7)return 0;
 return 1;
}
static void underwater_instance_evidence(UnderwaterEvidence *e,const CreatureInstance *c) {
 unsigned i,delta;
 if(c->form_id<49||c->form_id>72)return;
 i=(c->form_id-49)/3;delta=(c->form_id-49)%3;
 if(e->count[i]<2)++e->count[i];
 if(delta)e->terminals|=(Save4U8)(1u<<i);
 if(c->trial_flags||delta){
  e->trained=1;
  if(c->level<28||c->bond<45||(c->trial_flags&~3u)||
   (delta&&!(c->trial_flags&(1u<<(delta-1)))))e->invalid=1;
 }
}
static int underwater_sources_validate(const Save5Quests *q,const Save4U8 *obtained,
 const UnderwaterEvidence *e) {
 unsigned sources=(unsigned)q->region_flags[10]<<2,i,j;
 if(e->invalid)return 0;
 if(save5_quest_state(q,38)==SAVE5_QUEST_CLAIMED)sources|=1u;
 if(save5_quest_state(q,39)==SAVE5_QUEST_CLAIMED)sources|=2u;
 if(e->trained&&(sources&3u)!=3u)return 0;
 for(i=0;i<8;++i){
  unsigned history=0,terminal_history=0;
  if(!!e->count[i]!=!!(sources&(1u<<i)))return 0;
  for(j=0;j<3;++j){unsigned f=48+3*i+j,seen=(obtained[f>>3]>>(f&7))&1u;
   history|=seen;if(j)terminal_history|=seen;}
  if((sources&(1u<<i))&&!history)return 0;
  if(q->region_flags[17]&(1u<<i)){
   if(e->count[i]<2||!(e->terminals&(1u<<i))||!terminal_history)return 0;
  }
 }
 return 1;
}
static int underwater_roster_sources_validate(const Save5Quests *q,const CreatureRoster *r) {
 UnderwaterEvidence e;unsigned i;clear_bytes(&e,sizeof e);
 for(i=0;i<CREATURE_ROSTER_CAPACITY;++i)underwater_instance_evidence(&e,&r->instances[i]);
 return underwater_sources_validate(q,r->obtained,&e);
}
