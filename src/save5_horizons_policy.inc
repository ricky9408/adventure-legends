/* Numeric content8 source policy. Every listed receipt owns retained identities;
 * nonauthoritative credit/history never authorizes an invitation or trial. */
static const Save4U8 horizons_base_forms[12]={105,107,109,111,113,114,115,116,117,118,119,120};
static const Save4U8 horizons_source_rooms[12]={62,63,66,68,63,64,65,67,69,66,62,68};
static const Save4U8 horizons_quest_masks[6]={7,15,15,15,7,15};
static const Save4U8 horizons_priors[6][2]={{52,0},{55,0},{55,0},{56,57},{55,0},{55,0}};
/* quest,bit,predecessors,area. Ordered invitation bits are included here, but
 * only the typed initial-source transaction can create those four bits. */
static const Save4U8 horizons_objectives[][4]={
 {54,1,0,60},{54,2,1,62},{54,4,3,62},
 {55,1,0,63},{55,2,1,63},{55,4,3,64},{55,8,7,63},
 {56,1,0,65},{56,2,1,65},{56,4,3,66},{56,8,7,66},
 {57,1,0,67},{57,2,1,67},{57,4,3,68},{57,8,7,68},
 {58,1,0,64},{58,2,0,69},{58,4,3,65},
 {59,1,0,63},{59,2,0,66},{59,4,0,69},{59,8,7,60}
};
static int horizons_visit(const Save5Quests*q,unsigned room){
 return room==60?!!(q->region_flags[5]&64u):room==61?!!(q->region_flags[5]&128u):
  room>=62&&room<=69?!!(q->region_flags[6]&(1u<<(room-62))):0;
}
static int horizons_done(const Save5Quests*q,unsigned id){return save5_quest_state(q,id)==3;}
static unsigned horizons_receipt(const Save5Quests*q,unsigned index,unsigned repeat){
 return (q->region_flags[(repeat?14:12)+(index>>3)]>>(index&7))&1u;
}
static int horizons_objective_validate(const Save5Quests*q,unsigned id){
 unsigned state,mask,bits,i;if(id<54||id>59)return 0;
 state=save5_quest_state(q,id);mask=horizons_quest_masks[id-54];bits=q->objectives[id];
 if(bits&~mask||(!state&&bits)||(state==1&&bits==mask)||(state>=2&&bits!=mask))return 0;
 for(i=0;i<sizeof horizons_objectives/sizeof horizons_objectives[0];++i){
  const Save4U8*p=horizons_objectives[i];
  if(p[0]==id&&(bits&p[1])&&(bits&p[2])!=p[2])return 0;
 }
 return 1;
}
static int horizons_quest_campaign_validate(const Save5Quests*q){
 unsigned i,j,v=q->region_flags[6];
 for(i=54;i<60;++i)if(save5_quest_state(q,i)){
  for(j=0;j<2;++j)if(horizons_priors[i-54][j]&&!horizons_done(q,horizons_priors[i-54][j]-1u))return 0;
 }
 if(v||q->anchors[6]||q->region_flags[12]||q->region_flags[13]||q->region_flags[14]||q->region_flags[15]){
  if(!horizons_done(q,51)||!(v&1u))return 0;
 }
 if((v&254u)&&!horizons_done(q,54))return 0;
 if((v&96u)&&(!horizons_done(q,55)||!horizons_done(q,56)))return 0;
 if((q->anchors[6]&1u)&&!(v&1u))return 0;
 if((q->anchors[6]&2u)&&(!(v&8u)||!horizons_done(q,54)))return 0;
 for(i=0;i<sizeof horizons_objectives/sizeof horizons_objectives[0];++i){
  const Save4U8*p=horizons_objectives[i];
  if((q->objectives[p[0]]&p[1])&&!horizons_visit(q,p[3]))return 0;
 }
 for(i=0;i<12;++i){
  unsigned initial=horizons_receipt(q,i,0);
  if(i<4&&initial!=!!(q->objectives[54+i]&(i?8u:4u)))return 0;
  if(initial&&(!horizons_visit(q,horizons_source_rooms[i])||(i>=4&&!horizons_done(q,54))))return 0;
  if(horizons_receipt(q,i,1)&&(!initial||!horizons_done(q,i<4?54+i:54)))return 0;
 }
 return 1;
}
static int horizons_campaign_validate(const CampaignSave*c,const Save5Quests*q){
 static const Save4U8 counts[8]={5,4,2,4,3,4,1,2};
 static const Save4U8 inbound[8][5]={{61,63,66,64,62},{62,65,64,67,0},{63,62,0,0,0},
  {63,66,67,65,0},{65,62,69,0,0},{63,65,68,69,0},{67,0,0,0,0},{66,67,0,0,0}};
 unsigned r=c->room,s=c->spawn;if(r<62||r>69||s>=counts[r-62]||!horizons_visit(q,r)||!horizons_visit(q,inbound[r-62][s]))return 0;
 if(!horizons_done(q,51))return 0;
 if((r!=62||(s>=1&&s<=3))&&!horizons_done(q,54))return 0;
 if((r==67||r==68||(r==63&&s==3)||(r==65&&s==2)||(r==69&&s==1))&&
  (!horizons_done(q,55)||!horizons_done(q,56)))return 0;
 if(((r==67&&s==3)||(r==69&&s==1))&&!horizons_done(q,57))return 0;
 if(r==62&&s==4&&!(q->anchors[6]&1u))return 0;
 if(r==65&&s==3&&!(q->anchors[6]&2u))return 0;
 return 1;
}
static void horizons_instance_evidence(HorizonsEvidence*e,const CreatureInstance*c){
 unsigned family=creatures_family_revision(c->form_id,8),i;
 if(family<41||family>52)return;
 i=family-41;
 if(e->count[i]<2)++e->count[i];
 if(c->trial_flags){e->trained=1;if(family>44||c->trial_flags!=1024||c->level<34||c->bond<60)e->invalid=1;}
}
static int horizons_sources_validate(const Save5Quests*q,const Save4U8*obtained,const HorizonsEvidence*e){
 unsigned i;if(e->invalid||(e->trained&&!horizons_done(q,54)))return 0;
 for(i=0;i<12;++i){
  unsigned base=horizons_base_forms[i]-1u,initial=horizons_receipt(q,i,0),repeat=horizons_receipt(q,i,1);
  if(initial!=!!e->count[i]||repeat!=(e->count[i]>=2))return 0;
  if(initial&&!(obtained[base>>3]&(1u<<(base&7))))return 0;
  /* New families have no release path: acquired history cannot exist without
   * their first real invitation. Seen-only encounter history remains legal. */
  if(!initial&&((obtained[base>>3]&(1u<<(base&7)))||
    (i<4&&(obtained[(base+1)>>3]&(1u<<((base+1)&7))))))return 0;
 }
 return 1;
}
static int horizons_roster_sources_validate(const Save5Quests*q,const CreatureRoster*r){
 HorizonsEvidence e;unsigned i;clear_bytes(&e,sizeof e);
 for(i=0;i<160;++i)horizons_instance_evidence(&e,&r->instances[i]);
 return horizons_sources_validate(q,r->obtained,&e);
}
