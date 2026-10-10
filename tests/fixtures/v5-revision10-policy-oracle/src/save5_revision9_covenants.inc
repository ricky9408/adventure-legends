/* Frozen accepted E content9 covenant rights and receipts. */
/* Unique covenant rights and invitation receipts are separate causal facts.
 * Seen-only discovery is legal; obtained always has exactly one retained owner. */
static int history9_covenant_done(const Save5Quests*q,unsigned quest){return save5_quest_state(q,quest)==3;}
static int history9_covenant_visit(const Save5Quests*q,unsigned room){
 return room==0?1:room==62?!!(q->region_flags[6]&1u):room>=70&&room<=77?!!(q->region_flags[7]&(1u<<(room-70))):0;
}
static int history9_covenant_entry(const CampaignSave*c,const Save5Quests*q){
 return (c->chapter_flags&SAVE4_ENDING_SEEN)&&history9_covenant_done(q,57)&&(q->objectives[60]&3u)==3u;
}
static int history9_covenants_objective_validate(const Save5Quests*q,unsigned quest){
 unsigned state,mask,bits;if(quest<60||quest>63)return 0;
 state=save5_quest_state(q,quest);bits=q->objectives[quest];mask=(quest==60||quest==63)?7u:15u;
 if(bits&~mask||(!state&&bits)||(state==1&&bits==mask)||(state>=2&&bits!=mask))return 0;
 return (quest==61||quest==62)||!(bits&(bits+1u));
}
static int history9_covenants_quest_campaign_validate(const CampaignSave*c,const Save5Quests*q){
 unsigned i,v=q->region_flags[7],rights=q->region_flags[22],receipts=q->region_flags[23];
 if(save5_quest_state(q,60)&&(!(c->chapter_flags&SAVE4_ENDING_SEEN)||!history9_covenant_done(q,57)))return 0;
 if((q->objectives[60]&2u)&&!history9_covenant_visit(q,62))return 0;
 if((q->objectives[60]&4u)&&!(v&1u))return 0;
 if((v||q->anchors[7]||rights||receipts)&&(!(v&1u)||!history9_covenant_entry(c,q)))return 0;
 if((v&14u)&&!history9_covenant_done(q,60))return 0;
 if((v&240u)&&(!(v&16u)||!history9_covenant_done(q,61)))return 0;
 if((q->anchors[7]&1u)&&!(v&1u))return 0;
 if((q->anchors[7]&2u)&&(!(v&16u)||!history9_covenant_done(q,61)))return 0;
 if(save5_quest_state(q,61)&&(!history9_covenant_done(q,60)||!(v&1u)))return 0;
 if(save5_quest_state(q,62)&&(!history9_covenant_done(q,61)||!(v&16u)))return 0;
 if(save5_quest_state(q,63)&&(!history9_covenant_done(q,61)||!history9_covenant_done(q,62)||!(v&1u)))return 0;
 if((q->objectives[63]&2u)&&!history9_covenant_visit(q,62))return 0;
 if(rights!=((unsigned)q->objectives[61]|((unsigned)q->objectives[62]<<4))||(receipts&~rights))return 0;
 for(i=0;i<8;++i)if((rights&(1u<<i))&&(!(v&(1u<<i))||!history9_covenant_done(q,i<4?60:61)))return 0;
 return 1;
}
static int history9_covenants_campaign_validate(const CampaignSave*c,const Save5Quests*q){
 static const Save4U8 counts[8]={5,2,2,2,4,2,2,2};
 static const Save4U8 inbound[8][5]={{62,71,73,74,70},{70,72,0,0,0},{71,73,0,0,0},{72,70,0,0,0},
  {70,75,77,74,0},{74,76,0,0,0},{75,77,0,0,0},{76,74,0,0,0}};
 unsigned r=c->room,s=c->spawn;
 if(r==62&&s==5)return history9_covenant_entry(c,q)&&history9_covenant_visit(q,62)&&history9_covenant_visit(q,70);
 if(r<70||r>77||s>=counts[r-70]||!history9_covenant_entry(c,q)||!history9_covenant_visit(q,r)||!history9_covenant_visit(q,inbound[r-70][s]))return 0;
 if(r>=71&&r<=73&&!history9_covenant_done(q,60))return 0;
 if((r>=74||(r==70&&s==3))&&!history9_covenant_done(q,61))return 0;
 if(r==70&&s==4&&!(q->anchors[7]&1u))return 0;
 if(r==74&&s==3&&!(q->anchors[7]&2u))return 0;
 return 1;
}
static void history9_covenants_instance_evidence(CovenantsEvidence*e,const CreatureInstance*c){
 unsigned i;if(c->form_id<121||c->form_id>128)return;i=c->form_id-121;
 if(e->count[i]<2)++e->count[i];
}
static int history9_covenants_sources_validate(const Save5Quests*q,const Save4U8*obtained,const CovenantsEvidence*e){
 unsigned i;for(i=0;i<8;++i){unsigned receipt=(q->region_flags[23]>>i)&1u;
  if(e->count[i]!=receipt||!!(obtained[15]&(1u<<i))!=receipt)return 0;
 }return 1;
}
static int history9_covenants_roster_sources_validate(const Save5Quests*q,const CreatureRoster*r){
 CovenantsEvidence e;unsigned i;clear_bytes(&e,sizeof e);
 for(i=0;i<160;++i)history9_covenants_instance_evidence(&e,&r->instances[i]);
 return history9_covenants_sources_validate(q,r->obtained,&e);
}
