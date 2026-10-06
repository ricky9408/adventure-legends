/* Projected practice fixtures unfold only after an explicit lectern A. They
 * are material-neutral drawings, never new walls. The player's actual walks,
 * exact command shapes and chosen geometry make each receipt. */
static const unsigned char trial_area[16]={50,52,51,49,48,48,50,51,49,48,48,51,51,52,49,52};
static const int tnames[16]={TX_UW_TRIAL0,TX_UW_TRIAL1,TX_UW_TRIAL2,TX_UW_TRIAL3,TX_UW_TRIAL4,TX_UW_TRIAL5,TX_UW_TRIAL6,TX_UW_TRIAL7,TX_UW_TRIAL8,TX_UW_TRIAL9,TX_UW_TRIAL10,TX_UW_TRIAL11,TX_UW_TRIAL12,TX_UW_TRIAL13,TX_UW_TRIAL14,TX_UW_TRIAL15};
static const int tclues[16][2]={{TX_UW_TRIAL0A,TX_UW_TRIAL0B},{TX_UW_TRIAL1A,TX_UW_TRIAL1B},{TX_UW_TRIAL2A,TX_UW_TRIAL2B},{TX_UW_TRIAL3A,TX_UW_TRIAL3B},{TX_UW_TRIAL4A,TX_UW_TRIAL4B},{TX_UW_TRIAL5A,TX_UW_TRIAL5B},{TX_UW_TRIAL6A,TX_UW_TRIAL6B},{TX_UW_TRIAL7A,TX_UW_TRIAL7B},{TX_UW_TRIAL8A,TX_UW_TRIAL8B},{TX_UW_TRIAL9A,TX_UW_TRIAL9B},{TX_UW_TRIAL10A,TX_UW_TRIAL10B},{TX_UW_TRIAL11A,TX_UW_TRIAL11B},{TX_UW_TRIAL12A,TX_UW_TRIAL12B},{TX_UW_TRIAL13A,TX_UW_TRIAL13B},{TX_UW_TRIAL14A,TX_UW_TRIAL14B},{TX_UW_TRIAL15A,TX_UW_TRIAL15B}};
static void trial_center(int*x,int*y){*x=(room==48||room==51)?240:120;*y=(room==48||room==51)?160:80;}
static void trial_point(unsigned p,int*x,int*y){static const short off[6][2]={{-48,-20},{48,-20},{-48,20},{48,20},{0,-24},{0,28}};int ox,oy;trial_center(&ox,&oy);if(underwater_game_trial.index==9){*x=ox-36+(int)(p%3)*36;*y=oy-18+(int)(p/3)*36;}else if(underwater_game_trial.index==15){static const short corners[6][2]={{-48,-24},{48,-24},{0,32},{64,32},{0,-24},{0,28}};*x=ox+corners[p][0];*y=oy+corners[p][1];}else{*x=ox+off[p][0];*y=oy+off[p][1];}}
static int participant(void){CreatureInstance*c=active();UnderwaterTrialProof*t=&underwater_game_trial;return t->index<16&&t->generation==room_generation&&t->slot<160&&t->party_signature==party_signature()&&t->selected_party==adventure_save.roster.selected_party&&c==&adventure_save.roster.instances[t->slot]&&c->instance_id==t->instance_id&&c->form_id==t->form&&room==trial_area[t->index];}
static COLD int begin_trial(unsigned key){CreatureInstance*c=active();const CreatureForm*f=c?creatures_form(c->form_id):0;unsigned idx,slot;if(!f||f->family<17||f->family>24||key<1||key>2){toast(TX_UW_TRIAL_PICK);return 1;}idx=(f->family-17)*2+key-1;if(room!=trial_area[idx]){say(TX_UW_TRIAL_ROOM,room_text(trial_area[idx]));return 1;}slot=adventure_save.roster.party[adventure_save.roster.selected_party];queue(UW_REQUEST_TRIAL_STATUS,0,0,0,f->family-16,slot,f->family,key,c->instance_id);return 1;}
static COLD void start_trial_proof(const WorldIntent*e){CreatureInstance*c=active();unsigned idx=(e->family-17)*2+e->key-1;if(!c||c->instance_id!=e->instance_id||c!=&adventure_save.roster.instances[e->slot]||room!=trial_area[idx]){toast(TX_UW_SAME);return;}clear_trial();projection=1;underwater_powers_geometry_changed();invalidate_actions();room_generation++;if(!room_generation)room_generation=1;underwater_game_trial.index=(unsigned char)idx;underwater_game_trial.slot=e->slot;underwater_game_trial.instance_id=c->instance_id;underwater_game_trial.generation=room_generation;underwater_game_trial.party_signature=party_signature();underwater_game_trial.selected_party=adventure_save.roster.selected_party;underwater_game_trial.form=(unsigned char)c->form_id;underwater_game_trial.family=e->family;underwater_game_trial.key=e->key;underwater_game_trial.source=e->source;underwater_game_trial.command=(unsigned char)(67+(e->family-17)*3);reset_pending=0;changed();toast(tclues[idx][0]);}
static int trial_geometry_ok(const UnderwaterTrialProof*t){const unsigned char*s=t->setting;switch(t->index){case 0:return s[0]==1&&s[1]==1;case 1:return s[0]==1&&!s[1];case 4:return s[0]==1&&!t->failed;case 5:return s[0]==1&&s[1]==1&&!s[2];case 6:return s[0]==1&&s[1]==1;case 7:return s[0]==1&&s[1]==2&&!s[2];case 11:return s[0]==1&&s[1]==3&&s[2]==1;case 12:return(s[0]==1&&s[1]==3)||(s[0]==3&&s[1]==1);case 13:return s[0]==2;case 14:return s[0]==1&&s[1]==3;case 15:return s[0]==7;default:return 1;}}
static int trial_solved(const UnderwaterTrialProof*t){if(!trial_geometry_ok(t))return 0;switch(t->index){case 0:case 1:case 11:case 12:case 14:return t->casts==3;case 2:return !t->setting[0]&&t->casts==3&&t->walk==1;case 3:return(t->setting[0]!=t->setting[1])&&t->casts==3&&t->walk==3;case 4:return t->casts==3;case 5:return t->casts==1&&t->walk==3;case 6:return t->casts==1&&t->order==1;case 7:return t->casts==1;case 8:return t->order==3;case 9:return t->order==4&&(t->casts==39||t->casts==51);case 10:return t->casts==1&&t->setting[0]==3;case 13:return t->casts==1&&t->walk==3&&t->order==6;case 15:return t->casts==7;default:return 0;}}
static COLD void trial_finish(void){UnderwaterTrialProof*t=&underwater_game_trial;if(participant()&&trial_solved(t))queue(UW_REQUEST_TRIAL_COMPLETE,0,0,0,t->source,t->slot,t->family,t->key,t->instance_id);}
static COLD void trial_changed(void){changed();trial_finish();}
static COLD int trial_manual(unsigned n){UnderwaterTrialProof*t=&underwater_game_trial;unsigned char*s=t->setting;if(!participant()){clear_trial();toast(TX_UW_SAME);return 1;}switch(t->index){
 case 0:if(n==0)s[0]=(s[0]+1)&3;else if(n==1)s[1]^=1;else return 0;t->casts=0;break;
 case 1:if(n>1)return 0;s[n]^=1;t->casts=0;break;
 case 2:case 3:toast(TX_UW_USE_COMMAND);return 1;
 case 4:if(n!=4)return 0;s[0]^=1;if(!s[0])t->casts=0;break;
 case 5:if(n>2)return 0;s[n]^=1;t->casts=t->walk=0;break;
 case 6:if(n<2){s[n]=(s[n]+1)&3;t->casts=t->order=0;}else if(n==2){if(trial_geometry_ok(t))t->order=1;else toast(TX_UW_FIT);}else return 0;break;
 case 7:if(n==0||n==2)s[n]^=1;else if(n==1)s[n]=(s[n]+1)%3;else return 0;t->casts=0;break;
 case 8:if(n==0){s[0]^=1;if(t->order==1&&s[0])t->order=2;else t->order=0;}else if(n==1){if(t->order==2&&s[0])t->order=3;else toast(TX_UW_HEAT_ORDER);}else return 0;break;
 case 9:toast(TX_UW_USE_COMMAND);return 1;
 case 10:if(n!=4)return 0;s[0]=(s[0]+1)%5;break;
 case 11:case 12:if(n>(t->index==11?2u:1u))return 0;s[n]=(s[n]+1)&3;t->casts=0;break;
 case 13:if(n!=4)return 0;s[0]=(s[0]+1)%3;t->casts=t->walk=t->order=0;break;
 case 14:if(n>1)return 0;s[n]=(s[n]+1)&3;t->casts=0;break;
 case 15:if(n>3)return 0;s[0]^=(unsigned char)(1u<<n);t->casts=0;break;
 default:return 0;}
 toast(TX_UW_ADJUSTED);trial_changed();return 1;}
static COLD int trial_cast(unsigned n){UnderwaterTrialProof*t=&underwater_game_trial;unsigned char*s=t->setting;int ok=1;if(!participant())return 0;
 switch(t->index){
 case 0:case 1:case 11:case 12:case 14:if(n>1||!trial_geometry_ok(t))ok=0;else t->casts|=(unsigned char)(1u<<n);break;
 case 2:if(n==0&&!s[0]&&!t->casts){s[0]=1;t->casts=1;}else if(n==1&&s[0]&&t->walk){s[0]=0;t->casts|=2;}else ok=0;break;
 case 3:if(n>1)ok=0;else{s[n]^=1;t->casts|=(unsigned char)(1u<<n);t->walk=0;}break;
 case 4:if(n<2){t->casts|=(unsigned char)(1u<<n);}else if(n==4){t->failed=1;t->casts=0;}else ok=0;break;
 case 5:if(n==4&&trial_geometry_ok(t)&&t->walk==3)t->casts=1;else ok=0;break;
 case 6:if(n==4&&trial_geometry_ok(t)&&t->order)t->casts=1;else ok=0;break;
 case 7:if(n==4&&trial_geometry_ok(t))t->casts=1;else ok=0;break;
 case 8:if(n==0&&!s[0]&&!t->order)t->order=1;else ok=0;break;
 case 9:if(n>=6||n==3||(t->casts&(1u<<n))||(!t->order&&n!=0)||
  (t->order&& !((n/3==s[0]/3&&ab((int)n-(int)s[0])==1)||(n%3==s[0]%3&&ab((int)n-(int)s[0])==3)))){t->casts=t->order=0;ok=0;}else{t->casts|=(unsigned char)(1u<<n);t->order++;s[0]=(unsigned char)n;}break;
 case 10:if(n==2)t->casts=1;else ok=0;break;
 case 13:if(n==4&&trial_geometry_ok(t)){t->casts=1;t->walk=t->order=0;}else ok=0;break;
 case 15:if(n<3&&trial_geometry_ok(t))t->casts|=(unsigned char)(1u<<n);else ok=0;break;
 default:ok=0;break;}
 if(!ok){toast(TX_UW_FIT);changed();return 2;}toast(TX_UW_TRACE);trial_changed();return 1;}
static COLD void trial_walk(void){UnderwaterTrialProof*t=&underwater_game_trial;int x,y,l,r,c;if(!participant()){clear_trial();invalidate_actions();changed();return;}trial_center(&x,&y);l=near(px,py,x-64,y+28,10);r=near(px,py,x+64,y+28,10);c=near(px,py,x,y+28,10);
 if(t->index==2&&t->setting[0]&&r&&!(t->walk&1)){t->walk=1;trial_changed();}
 else if((t->index==3&&t->casts==3&&t->setting[0]!=t->setting[1])||(t->index==5&&trial_geometry_ok(t))){unsigned b=l?1:r?2:0;if(b&&!(t->walk&b)){t->walk|=(unsigned char)b;trial_changed();}}
 else if(t->index==13&&t->casts){unsigned point=near(px,py,x-48,y-12,9)?1:near(px,py,x-48,y+28,9)?2:near(px,py,x+48,y-12,9)?3:near(px,py,x+48,y+28,9)?4:0;unsigned phase=t->order%3,side=point<=2?1:2;c=near(px,py,x,y+8,9);if(point&&phase==0){if(t->walk&side){t->walk=t->order=0;toast(TX_UW_LOOP_AGAIN);}else{t->setting[1]=(unsigned char)point;t->order++;changed();}}else if(point&&phase==1&&point!=t->setting[1]&&side==(t->setting[1]<=2?1u:2u)){t->order++;changed();}else if(c&&phase==2){t->walk|=(unsigned char)(t->setting[1]<=2?1:2);t->order++;trial_changed();}}
}
static COLD int trial_interact(void){unsigned i;int x,y;if(underwater_game_trial.index>=16)return 0;for(i=0;i<6;i++){trial_point(i,&x,&y);if(close(x,y))return trial_manual(i);}return 0;}
