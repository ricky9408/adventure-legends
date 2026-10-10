/* Original optional discovery trials. Engine hooks, no hidden persistence. */
#include "trials.h"
#include "trial_art.h"
#include "progression.h"
#include "assets.h"
typedef unsigned char u8;
extern void rect(int,int,int,int,u8),line(int,int,int,int,int);
extern void obj_upload(const u8*,int,int,int),obj_add(int,int,int,int,int,int,int,int);
extern volatile int px,py,game_state;
#define OBJ_PROP 12352
#define OBJ_HINT 10496
#define PLAY_STATE 1
#define RESET_X 32
#define RESET_Y 120
const TrialAid trial_grove_aids[6]={{184,280,0,0},{296,208,0,1},{320,72,0,2},{80,136,1,3},{400,136,1,4},{304,280,1,5}};
const short trial_vane_centers[3][2]={{88,64},{88,112},{168,112}};
const short trial_plate_centers[2][2]={{88,56},{152,104}};
unsigned trials_revision;
unsigned char trial_vanes[3];
short trial_parcels[2][2];
static int loaded_room=-1;
static unsigned loaded_revision=~0u;
static int ab(int x){return x<0?-x:x;}
static int close(int x,int y,int a,int b,int d){return ab(x-a)+ab(y-b)<d;}
static void changed(void){trials_revision++;progression_revision++;}
static CreatureInstance *family_instance(unsigned family){unsigned i;if(family>=4)return 0;for(i=0;i<CREATURE_ROSTER_CAPACITY;i++){CreatureInstance*c=&adventure_save.roster.instances[i];if((c->flags&(CREATURE_OCCUPIED|CREATURE_STORY_LOCKED))==(CREATURE_OCCUPIED|CREATURE_STORY_LOCKED)&&creatures_legacy_spirit(c->form_id)==family)return c;}return 0;}
int trials_done(unsigned family){CreatureInstance*c=family_instance(family);return c&&(c->trial_flags&(1u<<family))!=0;}
int trials_complete(unsigned family){CreatureInstance*c=family_instance(family);unsigned gain;if(!c||family>=4)return TRIAL_NONE;if(c->trial_flags&(1u<<family))return TRIAL_ALREADY_DONE;
 /* Explicit personal-quest exception: +10 bond to this story companion even
  * when ordinary expedition participation is capped. Trial bit guards BOTH
  * awards, independently of repeatable expedition event bits. */
 if(!creatures_mark_trial(c,1u<<family))return TRIAL_NONE;
 gain=CREATURE_MAX_BOND-c->bond;if(gain>10)gain=10;c->bond+=(u8)gain;creatures_add_xp(c,180);changed();return TRIAL_COMPLETE_HOMURA+(int)family;
}
int trials_is_room(unsigned room){return room==TRIAL_ROOM_WIND||room==TRIAL_ROOM_STONE;}
void trials_enter(unsigned room){int i;loaded_room=-1;if(room==TRIAL_ROOM_WIND){trial_vanes[0]=trials_done(2)?2:0;trial_vanes[1]=trials_done(2)?1:0;trial_vanes[2]=0;}if(room==TRIAL_ROOM_STONE){for(i=0;i<2;i++){trial_parcels[i][0]=trials_done(3)?trial_plate_centers[i][0]:(i?136:88);trial_parcels[i][1]=trials_done(3)?trial_plate_centers[i][1]:88;}}changed();}
int trials_solid(unsigned room,int x,int y){int i;if(!trials_is_room(room))return 0;if(x<12||x>=228||y<44||y>=148)return 1;if(room==TRIAL_ROOM_STONE)for(i=0;i<2;i++)if(ab(x-trial_parcels[i][0])<11&&ab(y-trial_parcels[i][1])<11)return 1;return 0;}
int trials_wind_solved(void){return trial_vanes[0]==2&&trial_vanes[1]==1&&trial_vanes[2]==0;}
unsigned trials_plate_mask(void){unsigned i,j,mask=0;for(i=0;i<2;i++)for(j=0;j<2;j++)if(trial_parcels[j][0]==trial_plate_centers[i][0]&&trial_parcels[j][1]==trial_plate_centers[i][1])mask|=1u<<i;return mask;}
int trials_try_push(int x,int y,unsigned face){static const signed char dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};int i;if(face>=4)return 0;for(i=0;i<2;i++){int a=trial_parcels[i][0]-x,b=trial_parcels[i][1]-y,forward=a*dx[face]+b*dy[face],side=a*dy[face]-b*dx[face];if(forward>=10&&forward<=21&&ab(side)<=5){int nx=trial_parcels[i][0]+dx[face]*16,ny=trial_parcels[i][1]+dy[face]*16;
 if(nx<72||nx>168||ny<56||ny>104||(nx==trial_parcels[1-i][0]&&ny==trial_parcels[1-i][1]))return -1;
 trial_parcels[i][0]=(short)nx;trial_parcels[i][1]=(short)ny;changed();return 1;}}return 0;}
int trials_exit(unsigned room,int x,int y){if(x<108||x>132||y<140||y>=148)return -1;return room==TRIAL_ROOM_WIND?4:room==TRIAL_ROOM_STONE?9:-1;}
int trials_interact(unsigned room,int x,int y,unsigned face){int i,result;if(room==4&&close(x,y,204,64,19))return TRIAL_ENTER_WIND;if(room==9&&close(x,y,208,120,19))return TRIAL_ENTER_STONE;
 if(room==1){for(i=0;i<6;i++)if(close(x,y,trial_grove_aids[i].x,trial_grove_aids[i].y,23))return (adventure_save.roster.lifetime_field_aid[0]&(1u<<i))?TRIAL_ALREADY_DONE:TRIAL_INSPECT;return TRIAL_NONE;}
 if(!trials_is_room(room))return TRIAL_NONE;
 if(close(x,y,RESET_X,RESET_Y,21)){if(trials_done(room==TRIAL_ROOM_WIND?2:3))return TRIAL_ALREADY_DONE;trials_enter(room);return TRIAL_RESET;}
 if(trials_exit(room,x,y)>=0)return TRIAL_EXIT;
 if(room==TRIAL_ROOM_STONE){if(trials_done(3)){for(i=0;i<2;i++)if(close(x,y,trial_parcels[i][0],trial_parcels[i][1],27))return TRIAL_ALREADY_DONE;}else{result=trials_try_push(x,y,face);if(result)return result>0?TRIAL_PUSHED:TRIAL_BLOCKED;}if(close(x,y,200,64,25))return trials_done(3)?TRIAL_ALREADY_DONE:TRIAL_INSPECT;}
 if(room==TRIAL_ROOM_WIND)for(i=0;i<3;i++)if(close(x,y,trial_vane_centers[i][0],trial_vane_centers[i][1],25))return trials_done(2)?TRIAL_ALREADY_DONE:TRIAL_INSPECT;
 return TRIAL_NONE;
}
int trials_power(unsigned room,int x,int y,unsigned spirit){int i,event,result;if(room==1){int best=-1,dist=999;for(i=0;i<6;i++){int d=ab(x-trial_grove_aids[i].x)+ab(y-trial_grove_aids[i].y);if(d<28&&d<dist){best=i;dist=d;}}if(best<0)return TRIAL_NONE;i=best;if(spirit!=trial_grove_aids[i].family)return TRIAL_WRONG_POWER;if(adventure_save.roster.lifetime_field_aid[0]&(1u<<i))return TRIAL_NONE;
 event=trial_grove_aids[i].event;if(progression_field((unsigned)event)<=0)return TRIAL_NONE;changed();if((adventure_save.roster.lifetime_field_aid[0]&(spirit?56:7))==(spirit?56:7)){result=trials_complete(spirit);if(result>=TRIAL_COMPLETE_HOMURA&&result<=TRIAL_COMPLETE_KOHAKU)return result;}return TRIAL_RESTORED;}
 if(room==TRIAL_ROOM_WIND){int best=-1,dist=999;for(i=0;i<3;i++){int d=ab(x-trial_vane_centers[i][0])+ab(y-trial_vane_centers[i][1]);if(d<27&&d<dist){best=i;dist=d;}}if(best<0)return TRIAL_NONE;if(spirit!=2)return TRIAL_WRONG_POWER;if(trials_done(2))return TRIAL_ALREADY_DONE;trial_vanes[best]=(u8)((trial_vanes[best]+1)&3);changed();if(trials_wind_solved()){if(!(adventure_save.roster.lifetime_field_aid[0]&64))progression_field(6);return trials_complete(2);}return TRIAL_ROTATED;}
 if(room==TRIAL_ROOM_STONE&&close(x,y,200,64,28)){if(spirit!=3)return TRIAL_WRONG_POWER;if(trials_done(3))return TRIAL_ALREADY_DONE;if(trials_plate_mask()!=3)return TRIAL_NEED_PLATES;if(!(adventure_save.roster.lifetime_field_aid[0]&128))progression_field(7);return trials_complete(3);}
 return TRIAL_NONE;
}
int trials_event_needs_save(int event){return event==TRIAL_RESTORED||(event>=TRIAL_COMPLETE_HOMURA&&event<=TRIAL_COMPLETE_KOHAKU);}
const unsigned char *trials_background(unsigned room){return room==TRIAL_ROOM_WIND?trial_background_wind:room==TRIAL_ROOM_STONE?trial_background_stone:0;}
const char *trials_room_name(unsigned room){return room==TRIAL_ROOM_WIND?"Wind-loom courtyard":room==TRIAL_ROOM_STONE?"Amber workshop":"";}
static void beam(int x,int y,int xx,int yy,int lit){line(x,y,xx,yy,lit?PAL_TEAL0:PAL_STONE3);if(x==xx)line(x+1,y,xx+1,yy,lit?PAL_GOLD4:PAL_STONE3);else line(x,y+1,xx,yy+1,lit?PAL_GOLD4:PAL_STONE3);}
void trials_draw_background(unsigned room,int cam_x,int cam_y){int i;if(room==1){for(i=0;i<6;i++){int x=trial_grove_aids[i].x-cam_x,y=trial_grove_aids[i].y-cam_y;if(y<-16||y>175||x<-16||x>255)continue;/* A weathered mosaic points at the abandoned craft, never blocks movement. */
 rect(x-13,y+5,27,4,i<3?PAL_BG_SUNLIT_DIRT1:PAL_BG_SUNLIT_MOSS1);line(x-11,y+9,x+11,y+9,PAL_BG_SUNLIT_STONE4);if(i<3){line(x-12,y+3,x-13,y-5,PAL_BG_SUNLIT_WOOD2);line(x+12,y+3,x+13,y-5,PAL_BG_SUNLIT_WOOD2);}else{line(x-11,y+3,x-14,y-2,PAL_BG_SUNLIT_MOSS2);line(x+11,y+3,x+14,y-2,PAL_BG_SUNLIT_MOSS2);}}return;}
 if(room==TRIAL_ROOM_WIND){int active=1;beam(40,64,88,64,1);for(i=0;i<3&&active;i++){int x=trial_vane_centers[i][0],y=trial_vane_centers[i][1],xx=x,yy=y;unsigned d=trial_vanes[i];int good=(i==0?d==2:i==1?d==1:d==0);if(good){xx=i==0?88:168;yy=i==0?112:i==1?112:48;}else{if(d==0)yy=48;else if(d==1)xx=216;else if(d==2)yy=136;else xx=24;}beam(x,y,xx,yy,1);active=good;}
 if(trials_done(2)){rect(156,44,25,3,PAL_GOLD3);rect(159,47,19,2,PAL_GOLD4);}}
 if(room==TRIAL_ROOM_STONE){unsigned m=trials_plate_mask();for(i=0;i<2;i++){int x=trial_plate_centers[i][0],y=trial_plate_centers[i][1];rect(x-7,y-7,15,15,(m&(1u<<i))?PAL_GOLD2:PAL_STONE2);rect(x-5,y-5,11,11,(m&(1u<<i))?PAL_GOLD4:PAL_GOLD0);line(x-3,y,x+3,y,PAL_WOOD1);line(x,y-3,x,y+3,PAL_WOOD1);}if(trials_done(3)){beam(184,64,200,64,1);rect(194,49,13,2,PAL_GOLD4);}}
}
static void load_slot(unsigned slot,const u8*p){obj_upload(p,16,16,OBJ_PROP+(int)slot*256);}
static void actor(unsigned slot,int x,int y){obj_add(OBJ_PROP+(int)slot*256,x-8,y-8,16,16,1,y,0);}
static void hint(int x,int y,int range){if(game_state==PLAY_STATE&&close(px,py,x,y,range))obj_add(OBJ_HINT,x-4,y-21,8,8,1,999,0);}
void trials_draw_actors(unsigned room,int cam_x,int cam_y){unsigned i;int reload=loaded_room!=(int)room||loaded_revision!=trials_revision;(void)cam_x;(void)cam_y;
 if(room!=1&&room!=4&&room!=9&&!trials_is_room(room))return;
 if(reload){if(room==1)for(i=0;i<6;i++)load_slot(i,trial_aid_sprites[i][(adventure_save.roster.lifetime_field_aid[0]>>i)&1]);
 else if(room==4||room==9)load_slot(5,trial_misc_sprites[room==4?TRIAL_SPR_WIND_SIGN:TRIAL_SPR_STONE_SIGN]);
 else if(room==TRIAL_ROOM_WIND){for(i=0;i<3;i++)load_slot(i,trial_vane_sprites[trial_vanes[i]&3]);load_slot(3,trial_misc_sprites[TRIAL_SPR_RESET]);load_slot(4,trial_misc_sprites[trials_done(2)?TRIAL_SPR_LOOM_LIT:TRIAL_SPR_LOOM]);}
 else{load_slot(0,trial_misc_sprites[TRIAL_SPR_PARCEL]);load_slot(1,trial_misc_sprites[TRIAL_SPR_PARCEL]);load_slot(2,trial_misc_sprites[TRIAL_SPR_RESET]);load_slot(3,trial_misc_sprites[trials_done(3)?TRIAL_SPR_ARCH_LIT:TRIAL_SPR_ARCH]);}
 loaded_room=(int)room;loaded_revision=trials_revision;}
 if(room==1){for(i=0;i<6;i++){actor(i,trial_grove_aids[i].x,trial_grove_aids[i].y);hint(trial_grove_aids[i].x,trial_grove_aids[i].y,23);}}
 else if(room==4||room==9){int x=room==4?204:208,y=room==4?64:120;actor(5,x,y);hint(x,y,22);}
 else if(room==TRIAL_ROOM_WIND){for(i=0;i<3;i++)actor(i,trial_vane_centers[i][0],trial_vane_centers[i][1]);actor(3,RESET_X,RESET_Y);actor(4,168,48);hint(RESET_X,RESET_Y,24);}
 else{for(i=0;i<2;i++)actor(i,trial_parcels[i][0],trial_parcels[i][1]);actor(2,RESET_X,RESET_Y);actor(3,200,64);hint(RESET_X,RESET_Y,24);}
}
