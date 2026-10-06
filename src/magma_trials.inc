/* Fifteen named trials. Each explicit step is tied to one selected immutable
 * instance ID; floor/bit transaction is committed only after real object proof.
 * Transient heat never crosses rooms. Form32 uses the same workshop practice
 * brick for all three outputs, then inspects the gallery return in person. */
typedef struct {unsigned char area,cap,action,face;short x,y;} MagmaTrialStep;
typedef struct {unsigned char family,key,from,count;MagmaTrialStep step[6];} MagmaTrial;
/* action0 field,1 manual,2 observe,3 custom brick. face255 accepts any facing. */
static const MagmaTrial trials[15]={
 {11,1,31,3,{{38,23,3,255,144,232},{40,23,3,255,48,86},{42,23,3,255,48,68}}},
 {11,2,32,4,{{40,23,3,255,48,86},{40,23,3,255,144,86},{40,23,3,255,192,86},{44,0,1,255,72,112}}},
 {12,1,34,3,{{39,15,0,255,176,128},{39,15,0,255,272,128},{43,15,0,255,168,104}}},
 {12,2,35,3,{{39,15,0,1,320,112},{39,15,0,0,320,264},{44,15,0,255,48,104}}},
 {13,1,37,2,{{39,12,0,255,72,176},{39,12,0,255,104,176}}},
 {13,2,37,5,{{39,0,1,255,392,208},{39,12,0,255,328,128},{39,12,0,255,360,128},{39,0,1,255,336,240},{40,0,1,255,168,64}}},
 {14,1,40,5,{{41,16,0,255,48,64},{41,9,0,255,112,64},{41,0,1,255,80,96},{41,0,1,255,144,96},{41,0,1,255,176,96}}},
 {14,2,40,4,{{39,16,0,255,272,128},{41,16,0,255,48,64},{39,9,0,255,304,128},{41,9,0,255,112,64}}},
 {15,1,43,4,{{40,0,1,255,128,64},{40,3,0,2,144,96},{40,3,0,2,176,96},{41,3,0,2,176,96}}},
 {15,2,43,3,{{40,3,0,2,80,96},{40,3,0,3,112,96},{40,0,1,255,48,96}}},
 {16,1,46,3,{{39,18,0,255,392,208},{39,18,0,255,424,240},{44,18,0,255,72,112}}},
 {16,2,46,3,{{39,18,0,255,392,208},{39,0,1,255,424,240},{40,18,0,255,128,64}}},
 {36,1,95,6,{{39,0,2,255,272,96},{39,19,0,255,304,96},{39,0,2,255,128,112},{39,19,0,255,160,112},{41,0,2,255,48,64},{41,19,0,255,80,64}}},
 {37,1,97,4,{{40,0,1,255,128,64},{40,22,0,255,56,112},{40,22,0,255,88,112},{44,22,0,255,48,104}}},
 {38,1,99,5,{{41,0,1,255,80,96},{41,0,1,255,144,96},{38,17,0,255,288,248},{41,17,0,255,112,64},{41,17,0,255,176,96}}}
};
static const int tnames[15]={TX_MG_TRIAL0,TX_MG_TRIAL1,TX_MG_TRIAL2,TX_MG_TRIAL3,TX_MG_TRIAL4,TX_MG_TRIAL5,TX_MG_TRIAL6,TX_MG_TRIAL7,TX_MG_TRIAL8,TX_MG_TRIAL9,TX_MG_TRIAL10,TX_MG_TRIAL11,TX_MG_TRIAL12,TX_MG_TRIAL13,TX_MG_TRIAL14};
static const int tclues[15][2]={{TX_MG_TRIAL0A,TX_MG_TRIAL0B},{TX_MG_TRIAL1A,TX_MG_TRIAL1B},{TX_MG_TRIAL2A,TX_MG_TRIAL2B},{TX_MG_TRIAL3A,TX_MG_TRIAL3B},{TX_MG_TRIAL4A,TX_MG_TRIAL4B},{TX_MG_TRIAL5A,TX_MG_TRIAL5B},{TX_MG_TRIAL6A,TX_MG_TRIAL6B},{TX_MG_TRIAL7A,TX_MG_TRIAL7B},{TX_MG_TRIAL8A,TX_MG_TRIAL8B},{TX_MG_TRIAL9A,TX_MG_TRIAL9B},{TX_MG_TRIAL10A,TX_MG_TRIAL10B},{TX_MG_TRIAL11A,TX_MG_TRIAL11B},{TX_MG_TRIAL12A,TX_MG_TRIAL12B},{TX_MG_TRIAL13A,TX_MG_TRIAL13B},{TX_MG_TRIAL14A,TX_MG_TRIAL14B}};
static COLD int begin_trial(unsigned key){CreatureInstance*c=active();const CreatureForm*f=c?creatures_form(c->form_id):0;unsigned i,slot;int r;if(!f){toast(TX_MG_TRIAL_PICK);return 1;}for(i=0;i<15;i++)if(trials[i].family==f->family&&trials[i].key==key)break;if(i==15){toast(TX_MG_TRIAL_PICK);return 1;}slot=adventure_save.roster.party[adventure_save.roster.selected_party];r=magma_trial_status(&adventure_save,slot,c->instance_id,f->family,key,magma_source_token_for_family(f->family));if(r==MAGMA_UNCHANGED){toast(TX_MG_TRIAL_ALREADY);return 1;}if(r!=MAGMA_REWARDED&&r!=MAGMA_CHANGED&&r!=MAGMA_NOW_READY){toast(TX_MG_TIER_LOCK);return 1;}clear_trial();trial_index=(unsigned char)i;trial_slot=(unsigned char)slot;trial_id=c->instance_id;grab=255;if(room==40&&(i==0||i==1))magma_puzzle_reset(&magma_game_puzzle,40);changed();say(TX_MG_TRIAL_START,tclues[i][0]);return 1;}
static COLD int trial_mark(unsigned bit){const MagmaTrial*t;unsigned mask,aid;int r;if(trial_index>=15||!participant())return wrong(TX_MG_SAME);t=&trials[trial_index];mask=(1u<<t->count)-1;if(trial_bits&bit){toast(TX_MG_PROGRESS);return 1;}trial_bits|=(unsigned char)bit;changed();if(trial_bits==mask){r=magma_trial_complete(&adventure_save,trial_slot,trial_id,t->family,t->key,magma_source_token_for_family(t->family));if(r==MAGMA_REWARDED||r==MAGMA_CHANGED){aid=magma_trial_aid(t->family,t->key);if(aid<128)creatures_credit_event(&adventure_save.roster,384+aid,160,CREATURE_CREDIT_FIELD_AID);dirty=1;progression_refresh();persist();toast(TX_MG_TRIAL_DONE);}else if(r==MAGMA_UNCHANGED)toast(TX_MG_TRIAL_ALREADY);else{trial_bits&=(unsigned char)~bit;toast(TX_MG_TIER_LOCK);}}else toast(TX_MG_PROGRESS);return 1;}
static int trial_prefix(unsigned i){return (trial_bits&((1u<<i)-1))==((1u<<i)-1);}
static COLD void trial_slide(void){if(!participant())return;
 if(trial_index==0&&magma_game_puzzle.heat&&magma_game_puzzle.cell[0]==23)trial_mark(2);
 if(trial_index==1&&magma_game_puzzle.heat){unsigned goal=trial_order==0?23:trial_order==2?26:trial_order==4?27:255;if(magma_game_puzzle.cell[0]==goal){unsigned bit=trial_order==0?1:trial_order==2?2:4;trial_mark(bit);trial_order++;}}
}
static COLD int trial_interact(void){const MagmaTrial*t;unsigned i;int x,y;if(trial_index>=15)return 0;
t=&trials[trial_index];
 /* Inspect/cool the same practice brick at the actual marked sink resting
  * place. No inventory heat, teleport, copied participant or menu-only move. */
 if(trial_index==1&&room==40&&close(144,112)){if(!participant())return wrong(TX_MG_SAME);if((trial_order==1||trial_order==3)&&magma_game_puzzle.cell[0]==25){magma_game_puzzle.heat=0;trial_order++;changed();toast(TX_MG_COOLED);}else toast(TX_MG_ORDER);return 1;}
 if(trial_index==0&&room==38&&close(192,232)&&lesson_x!=192){toast(TX_MG_GRAB_HELP);return 1;}
 if(trial_index==4&&room==39&&close(88,144)){toast(TX_MG_TRIAL4B);return 1;}
 for(i=0;i<t->count;i++){const MagmaTrialStep*s=&t->step[i];if(s->area!=room||s->action==0||s->action==3||!close(s->x,s->y))continue;if(!participant())return wrong(TX_MG_SAME);if(!trial_prefix(i))return wrong(TX_MG_ORDER);
  if(trial_index==1&&i==3&&trial_order!=5)return wrong(TX_MG_ORDER);
  if(trial_index==5&&i==0)wind=1;
  if(trial_index==5&&i==3)trial_aux|=1;
  if(trial_index==5&&i==4&&!(trial_aux&1))return wrong(TX_MG_ORDER);
  if(trial_index==8||trial_index==13)pot_hood=1;
  if(trial_index==14&&i<2)sound|=(unsigned char)(1u<<i);
  return trial_mark(1u<<i);
 }
 /* The native target is always the current physical position of the brick;
  * the sign/source marker is not an invisible shortcut to the shelf. */
 if(trial_brick()&&magma_puzzle_position(&magma_game_puzzle,40,0,&x,&y)&&close(x,y))return 0;
 return 0;}
static COLD int trial_power(void){const MagmaTrial*t;unsigned i;int x,y;
 if(trial_index>=15)return 0;
t=&trials[trial_index];
 if(trial_index==0&&room==38&&close(lesson_x,232)){if(!participant())return wrong(TX_MG_SAME);if(lesson_x!=144)return wrong(TX_MG_COLD);if(!field(23,lesson_x,232))return wrong(TX_MG_WRONG);trial_aux|=1;changed();toast(TX_MG_CHARGED);return 1;}
 if(trial_brick()){if(!magma_puzzle_position(&magma_game_puzzle,40,0,&x,&y))return wrong(TX_MG_ARRANGE);if(close(x,y)){if(!participant())return wrong(TX_MG_SAME);if(!field(23,x,y))return wrong(TX_MG_WRONG);if(trial_index==1&&(trial_order==1||trial_order==3||trial_order>=5))return wrong(TX_MG_ORDER);if(!magma_puzzle_charge(&magma_game_puzzle,40))return wrong(TX_MG_COLD);changed();toast(TX_MG_CHARGED);return 1;}}
 if((trial_index==4&&room==39&&close(88,144))||(trial_index==7&&room==41&&close(144,64))||(trial_index==10&&room==39&&close(336,240))||(trial_index==12&&room==41&&close(144,64)))return wrong(TX_MG_ARRANGE);
 for(i=0;i<t->count;i++){const MagmaTrialStep*s=&t->step[i];if(s->area!=room||s->action!=0||!close(s->x,s->y))continue;if(!participant())return wrong(TX_MG_SAME);if(!field(s->cap,s->x,s->y))return wrong(TX_MG_WRONG);if(s->face!=255&&face!=s->face)return wrong(TX_MG_ARRANGE);if(!trial_prefix(i))return wrong(TX_MG_ORDER);
  if(trial_index==3&&i==2&&!((trial_aux&4)&&magma_game_puzzle.cell[1]==4&&magma_game_puzzle.cell[0]==20))return wrong(TX_MG_ARRANGE);
  if(trial_index==4&&i>0&&!(trial_bits&1))return wrong(TX_MG_ORDER);
  if(trial_index==8&&!(trial_bits&1))return wrong(TX_MG_ARRANGE);
  if(trial_index==13&&!(trial_bits&1))return wrong(TX_MG_ARRANGE);
  return trial_mark(1u<<i);
 }
 return 0;}
