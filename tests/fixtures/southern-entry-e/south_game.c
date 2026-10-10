/* Original Sunlace chapter. Volatile optics and field demonstrations never
* masquerade as durable rewards. Every mutation goes through typed policy. */
#include "south_game.h"
#include "south_art.h"
#include "southern_quests.h"
#include "progression.h"
#include "assets.h"
#ifdef SOUTH_GAME_HOST_TEST
#include "south_game_test_ui.h"
#else
#include "ui.h"
#endif
#if defined(__arm__)
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
#else
#define COLD
#endif
#define PLAY 1
#define UP 64
#define DOWN 128
#define JOURNAL_TAB 7
extern volatile int room,px,py,game_state,summoned,transition_lock,checkpoint_spawn,camera_x,camera_y;
extern volatile unsigned chapter_flags;
extern int face,keys,journal_tab;
extern void enter_room(int,int),save_game(void),dialogue(int,int,int),toast(int),text(int,int,int,int),centered(int,int,int),box(int,int,int,int);
extern void rect(int,int,int,int,unsigned char),line(int,int,int,int,int),game_region_warp(int,int);
unsigned south_game_revision,south_game_journal_selection;
SouthPuzzle south_game_puzzle;
unsigned char south_game_machine_stage,south_game_machine_ticks,south_game_machine_hp;
static unsigned char demo,hood,quiet,roots,drain,panels,ripple,runnel,pins,sun,loft,moisture,alignment,overflow,door_notice,machine_hit;
static short machine_x=88;
static unsigned dirty;
typedef struct { unsigned char family,capability;
unsigned char area[3];
short xy[3][2];
} Trial;
static const Trial trials[10]={
{9,12,{31,31,32},{{128,192},{176,144},{56,104}}},
{10,19,{33,33,33},{{56,80},{112,80},{168,80}}},
{28,26,{30,30,30},{{160,192},{208,192},{256,192}}},
{29,23,{33,33,33},{{56,112},{112,112},{168,112}}},
{30,15,{31,31,31},{{368,176},{400,176},{432,176}}},
{31,17,{35,35,35},{{48,112},{112,128},{176,128}}},
{32,22,{32,32,32},{{48,80},{120,80},{192,80}}},
{33,16,{31,31,31},{{224,112},{272,176},{320,112}}},
{34,13,{32,32,32},{{48,32},{120,32},{192,32}}},
{35,3,{33,33,33},{{56,48},{112,48},{168,48}}}
};
/* One explicitly chosen individual participates. Identity, not just family,
* binds every transient proof; swapping active members cannot merge copies. */
static unsigned char trial_index=255,trial_slot=255,trial_bits,trial_revealed;
static CreatureU32 trial_id;
static const short spawns[8][5][2]={{{240,284},{304,32},{112,224},{80,148},{400,224}},{{240,284},{400,72},{80,264},{80,104}},{{120,132}},{{120,132}},{{120,132}},{{120,132}},{{120,132}},{{120,132}}};
static const unsigned char counts[8]={5,4,1,1,1,1,1,1};
static int ab(int n){return n<0?-n:n;
}
static int near(int x,int y,int xx,int yy,int r){return ab(x-xx)+ab(y-yy)<r;
}
static int close(int x,int y){if((face==1&&y>py+8)||(face==0&&y<py-8)||(face==2&&x>px+8)||(face==3&&x<px-8))return 0;
return near(px,py,x,y,18);
}
/* An NPC beside or behind a marked fixture must not steal its A press.
 * Use the facing cone only for conversations; side-mounted manual controls
 * retain their existing reachable approaches and interaction radius. */
static int npc_close(int x,int y){int forward,side;
if(!close(x,y))return 0;
if(face==1){forward=py-y;side=ab(px-x);}
else if(face==0){forward=y-py;side=ab(px-x);}
else if(face==2){forward=px-x;side=ab(py-y);}
else if(face==3){forward=x-px;side=ab(py-y);}
else return 0;
return side<=forward+4;
}
static unsigned state(unsigned q){return save5_quest_state(&adventure_save.quests,q);
}
static int done(unsigned q){return state(q)==3;
}
static int ready(unsigned q){return state(q)>=2;
}
static void changed(void){south_game_revision++;
progression_revision++;
}
static void sync(void){adventure_save.campaign.chapter_flags=(Save4U8)chapter_flags;
}
static COLD void persist(void){if(dirty){sync();
if(south_game_is_room((unsigned)room)){adventure_save.campaign.room=(Save4U8)room;
adventure_save.campaign.spawn=(Save4U8)checkpoint_spawn;
}changed();
save_game();
dirty=0;
}}
static COLD void say(int a,int b){persist();
dialogue(a,b,PLAY);
}
#include "south_rest_job.inc"
static COLD int offer(unsigned q){int r=southern_quest_offer(&adventure_save,q);
if(r==SOUTH_CHANGED)dirty=1;
return r!=SOUTH_LOCKED&&r!=SOUTH_INVALID;
}
static COLD void objective(unsigned q,unsigned bit){int r=southern_quest_objective(&adventure_save,q,bit);
if(r==SOUTH_CHANGED||r==SOUTH_NOW_READY){dirty=1;
changed();
}}
static COLD void claim(unsigned q){int r=southern_quest_claim(&adventure_save,q);
if(r==SOUTH_REWARDED){dirty=1;
progression_refresh();
say(q==24?TX_ST_RETURN_A:TX_ST_RECEIVED_A,q==24?TX_ST_RETURN_B:TX_ST_RECEIVED_B);
}
else if(r==SOUTH_RESERVED)say(TX_MG_RESERVED,TX_MG_RESERVEDB);else if(r==SOUTH_FULL)say(TX_ST_FULL_A,TX_ST_FULL_B);
else if(r==SOUTH_UNCHANGED)say(q==24?TX_ST_RETURN_A:TX_ST_DONE_A,q==24?TX_ST_RETURN_B:TX_ST_DONE_B);
else say(TX_ST_LOCKED_A,TX_ST_LOCKED_B);
}
static const int qnames[8]={TX_ST_Q22,TX_ST_Q23,TX_ST_Q24,TX_ST_Q25,TX_ST_Q26,TX_ST_Q27,TX_ST_Q28,TX_ST_Q29};
static const int clues[8][2]={{TX_ST_CLUE22A,TX_ST_CLUE22B},{TX_ST_CLUE23A,TX_ST_CLUE23B},{TX_ST_CLUE24A,TX_ST_CLUE24B},{TX_ST_CLUE25A,TX_ST_CLUE25B},{TX_ST_CLUE26A,TX_ST_CLUE26B},{TX_ST_CLUE27A,TX_ST_CLUE27B},{TX_ST_CLUE28A,TX_ST_CLUE28B},{TX_ST_CLUE29A,TX_ST_CLUE29B}};
static const int tnames[10]={TX_ST_TRIAL0,TX_ST_TRIAL1,TX_ST_TRIAL2,TX_ST_TRIAL3,TX_ST_TRIAL4,TX_ST_TRIAL5,TX_ST_TRIAL6,TX_ST_TRIAL7,TX_ST_TRIAL8,TX_ST_TRIAL9};
static const int tclues[10][2]={{TX_ST_TRIAL0A,TX_ST_TRIAL0B},{TX_ST_TRIAL1A,TX_ST_TRIAL1B},{TX_ST_TRIAL2A,TX_ST_TRIAL2B},{TX_ST_TRIAL3A,TX_ST_TRIAL3B},{TX_ST_TRIAL4A,TX_ST_TRIAL4B},{TX_ST_TRIAL5A,TX_ST_TRIAL5B},{TX_ST_TRIAL6A,TX_ST_TRIAL6B},{TX_ST_TRIAL7A,TX_ST_TRIAL7B},{TX_ST_TRIAL8A,TX_ST_TRIAL8B},{TX_ST_TRIAL9A,TX_ST_TRIAL9B}};
static COLD void talk(unsigned q){if(ready(q)){claim(q);
return;
}if(offer(q))say(clues[q-22][0],clues[q-22][1]);
else say(TX_ST_LOCKED_A,TX_ST_LOCKED_B);
}
unsigned south_game_enemy_spawns(unsigned area,const SouthEnemySpawn **out){
static const SouthEnemySpawn field_enemies[5]={{208,264,5,0,0},{320,272,5,0,1},{432,128,6,2,3},{208,64,5,0,4},{336,64,6,2,2}};
static const SouthEnemySpawn hollow_enemies[2]={{80,120,5,0,3},{184,136,5,0,1}};
if(out){*out=area==31?field_enemies:area==33?hollow_enemies:0;
}return area==31?5:area==33?2:0;
}
int south_game_is_room(unsigned a){return a>=30&&a<=37;
}
static int puzzle_valid(const SouthPuzzle*p,unsigned a){return p&&a>=34&&a<=36&&p->mirror[0]<2&&p->mirror[1]<2&&p->shade<2;
}
int south_puzzle_step(SouthPuzzle*p,unsigned a,unsigned act){if(!puzzle_valid(p,a))return -1;
if(act==SOUTH_ACTION_RESET){p->mirror[0]=p->mirror[1]=(unsigned char)(a==36);
p->shade=1;
return 1;
}
if(act==SOUTH_ACTION_MIRROR0){p->mirror[0]^=1;
return 1;
}
if(act==SOUTH_ACTION_MIRROR1&&a!=34){p->mirror[1]^=1;
return 1;
}
if(act==SOUTH_ACTION_SHADE&&a!=34){p->shade^=1;
return 1;
}return -1;
}
/* Pixel-stepped rays are bounded by authored room size. First blocker wins;
* no recursion, loops or dynamic allocation. Every ray uses cardinal lines. */
static int optical_wall(unsigned area,int x,int y){const SouthArtRoom*r=&south_art_rooms[area-30];
unsigned i;
if((unsigned)x>=r->width||(unsigned)y>=r->height)return 1;
for(i=0;i<r->solid_count;i++){const SouthArtRect*b=&r->solids[i];
if(x>=b->x&&x<b->x+b->w&&y>=b->y&&y<b->y+b->h)return 1;
}return 0;
}
unsigned south_puzzle_beam(const SouthPuzzle*p,unsigned a,SouthBeam out[4]){static const int dx[4]={1,0,-1,0},dy[4]={0,1,0,-1};
int mx[2],my[2],rx,ry,x,y,d=0,nx,ny,k,kind,hit;
unsigned n=0,seen=0,bit;
if(!out||!puzzle_valid(p,a))return 0;
mx[0]=a==36?80:112;
my[0]=a==36?104:56;
mx[1]=a==36?80:112;
my[1]=a==36?48:104;
rx=a==34?112:192;
ry=a==36?48:104;
x=32;
y=a==36?104:56;
while(n<4){nx=x;
ny=y;
hit=-1;
kind=SOUTH_BEAM_WALL;
for(k=0;k<240;k++){nx+=dx[d];
ny+=dy[d];
if(optical_wall(a,nx,ny))break;
if(a!=34&&nx==152&&ny==(p->shade?(a==35?104:48):(a==35?56:104))){kind=SOUTH_BEAM_SHADE;
break;
}
if(nx==rx&&ny==ry){kind=SOUTH_BEAM_RECEIVER;
break;
}
if(nx==mx[0]&&ny==my[0]){hit=0;
kind=SOUTH_BEAM_MIRROR;
break;
}
if(a!=34&&nx==mx[1]&&ny==my[1]){hit=1;
kind=SOUTH_BEAM_MIRROR;
break;
}
}
out[n].x1=(short)x;
out[n].y1=(short)y;
out[n].x2=(short)nx;
out[n].y2=(short)ny;
out[n].end_kind=(unsigned char)kind;
n++;
if(hit<0){break;
}bit=1u<<((unsigned)hit*4+(unsigned)d);
if(seen&bit){out[n-1].end_kind=SOUTH_BEAM_LOOP;
break;
}seen|=bit;
d=p->mirror[hit]?(d^1):3-d;
x=nx;
y=ny;
}return n;
}
static int contains(const SouthBeam*b,int x,int y){return b->x1==b->x2?x==b->x1&&y>=(b->y1<b->y2?b->y1:b->y2)&&y<=(b->y1>b->y2?b->y1:b->y2):y==b->y1&&x>=(b->x1<b->x2?b->x1:b->x2)&&x<=(b->x1>b->x2?b->x1:b->x2);
}
unsigned south_puzzle_receivers(const SouthPuzzle*p,unsigned a){SouthBeam b[4];
unsigned n=south_puzzle_beam(p,a,b),i,v=0;
for(i=0;i<n;i++){if(a==35&&contains(&b[i],80,56))v|=1;
if(b[i].end_kind==SOUTH_BEAM_RECEIVER)v|=a==35?2u:1u;
}return v;
}
int south_puzzle_solved(const SouthPuzzle*p,unsigned a){return puzzle_valid(p,a)&&south_puzzle_receivers(p,a)==(a==35?3u:1u);
}
static void clear_trial(void){trial_index=trial_slot=255;
trial_bits=trial_revealed=0;
trial_id=0;
}
static COLD void reset_scene(void){south_game_puzzle.mirror[0]=south_game_puzzle.mirror[1]=(unsigned char)(room==36);
south_game_puzzle.shade=1;
if(room>=34&&room<=36&&(adventure_save.quests.objectives[24]&(1u<<(room-34)))){south_game_puzzle.mirror[0]=south_game_puzzle.mirror[1]=(unsigned char)(room!=36);
south_game_puzzle.shade=0;
}
demo=hood=quiet=roots=drain=panels=ripple=runnel=pins=sun=loft=moisture=alignment=overflow=machine_hit=0;
if(room==32)loft=(unsigned char)(adventure_save.quests.objectives[29]&3);
south_game_machine_stage=(unsigned char)((adventure_save.quests.objectives[24]&8)?5:0);
south_game_machine_ticks=0;
south_game_machine_hp=(unsigned char)(south_game_machine_stage==5?0:144);
machine_x=88;
changed();
}
COLD void south_game_reset(void){south_game_cancel_rest();clear_trial();
reset_scene();
}
COLD int south_game_enter(unsigned area,unsigned spawn){int r;
south_game_cancel_rest();sync();
if(!south_game_is_room(area)||spawn>=counts[area-30]||!southern_can_enter(&adventure_save,area))return 0;
r=southern_visit(&adventure_save,area);
if(r==SOUTH_INVALID||r==SOUTH_LOCKED)return 0;
if(r==SOUTH_CHANGED){dirty=1;
}room=(int)area;
checkpoint_spawn=(int)spawn;
px=spawns[area-30][spawn][0];
py=spawns[area-30][spawn][1];
reset_scene();
door_notice=0;
if(area>=34){offer(24);
}adventure_save.campaign.room=(Save4U8)area;
adventure_save.campaign.spawn=(Save4U8)spawn;
dirty=1;
persist();
return 1;
}
int south_game_solid(int x,int y){const SouthArtRoom*r;
const unsigned short*b;
unsigned n;
if(!south_game_is_room((unsigned)room))return 0;
r=&south_art_rooms[room-30];
if((unsigned)x>=r->width||(unsigned)y>=r->height)return 1;
b=r->collision_bands+r->collision_rows[y];
n=*b++;
while(n--){if((unsigned)x<b[0])return 0;
if((unsigned)x<b[1])return 1;
b+=2;
}return 0;
}
static COLD int door(unsigned dest,unsigned spawn){if(!southern_can_enter(&adventure_save,dest)){if(!door_notice){say(TX_ST_LOCKED_A,TX_ST_LOCKED_B);
door_notice=45;
}return 1;
}persist();
enter_room((int)dest,(int)spawn);
return 1;
}
static COLD void mechanism(unsigned action){int r=south_puzzle_step(&south_game_puzzle,(unsigned)room,action);
if(r<0){toast(TX_ST_ARRANGE);
return;
}changed();
toast(action==SOUTH_ACTION_SHADE?(south_game_puzzle.shade?TX_ST_SHADE_CLOSED:TX_ST_SHADE_OPEN):south_game_puzzle.mirror[action-1]?TX_ST_MIRROR1:TX_ST_MIRROR0);
if(room==36&&south_puzzle_solved(&south_game_puzzle,36)){objective(24,4);
persist();
toast(TX_ST_SHORTCUT);
}}
static int line_clear(int x,int y){int ox=px,oy=py,dx=x-ox,dy=y-oy,n=ab(dx)>ab(dy)?ab(dx):ab(dy),i;
if(n>24)return 0;
for(i=1;i<n;i++)if(south_game_solid(ox+dx*i/n,oy+dy*i/n))return 0;
return 1;
}
static CreatureInstance*active(void){CreatureInstance*c=progression_selected();
unsigned p=adventure_save.roster.selected_party,s;
if(!summoned||p>=4)return 0;
s=adventure_save.roster.party[p];
if(s>=160||c!=&adventure_save.roster.instances[s]||!creatures_instance_validate(c))return 0;
return c;
}
static int field(unsigned cap,int x,int y){CreatureInstance*c=active();
return c&&close(x,y)&&line_clear(x,y)&&creatures_supports_capability(c->form_id,cap);
}
static COLD int wrong(int id){toast(id);
return 2;
}
static COLD void discovery(unsigned d){int r=southern_discover(&adventure_save,d);
if(r==SOUTH_CHANGED){dirty=1;
changed();
toast(TX_ST_DISCOVERED);
}}
static COLD int recruit(unsigned token,int valid,int clue){int r;
if(southern_source_claimed(&adventure_save,token)){toast(TX_ST_KNOWN);
return 1;
}if(!valid){toast(clue);
return 1;
}r=southern_field_recruit(&adventure_save,token);
if(r==SOUTH_REWARDED){dirty=1;
progression_refresh();
persist();
toast(TX_ST_RECRUITED);
}else if(r==SOUTH_RESERVED)say(TX_MG_RESERVED,TX_MG_RESERVEDB);else if(r==SOUTH_FULL)say(TX_ST_FULL_A,TX_ST_FULL_B);
else toast(TX_ST_ARRANGE);
return 1;
}
static int participant(void){CreatureInstance*c=active();
return trial_index<10&&trial_slot<160&&c==&adventure_save.roster.instances[trial_slot]&&c->instance_id==trial_id;
}
static COLD int begin_trial(void){CreatureInstance*c=active();
const CreatureForm*f=c?creatures_form(c->form_id):0;
unsigned i;
if(!f||!done(22)||!done(23)){toast(TX_ST_TRIAL_PICK);
return 1;
}for(i=0;i<10;i++)if(trials[i].family==f->family)break;
if(i==10||!southern_source_claimed(&adventure_save,southern_source_token_for_family(f->family))){toast(TX_ST_TRIAL_PICK);
return 1;
}
if(creatures_has_trial_qualified(c,f->family,1)){toast(TX_ST_TRIAL_ALREADY);
return 1;
}trial_index=(unsigned char)i;
trial_slot=adventure_save.roster.party[adventure_save.roster.selected_party];
trial_id=c->instance_id;
trial_bits=trial_revealed=0;
changed();
say(TX_ST_TRIAL_START,tclues[i][0]);
return 1;
}
static COLD int trial_mark(unsigned which){int r;
if(!participant())return wrong(TX_ST_TRIAL_SAME);
if(trial_bits&(1u<<which)){toast(TX_ST_PROGRESS);
return 1;
}trial_bits=(unsigned char)(trial_bits|(1u<<which));
changed();
if(trial_bits!=7){toast(TX_ST_PROGRESS);
return 1;
}r=southern_trial_complete(&adventure_save,trial_slot,trial_id,trials[trial_index].family,1,southern_source_token_for_family(trials[trial_index].family));
if(r==SOUTH_REWARDED){dirty=1;
progression_refresh();
persist();
toast(TX_ST_TRIAL_DONE);
}else if(r==SOUTH_UNCHANGED)toast(TX_ST_TRIAL_ALREADY);
else{trial_bits=0;
toast(TX_ST_TRIAL_RESET);
}return 1;
}
static int trial_near(unsigned i){return trial_index<10&&room==trials[trial_index].area[i]&&close(trials[trial_index].xy[i][0],trials[trial_index].xy[i][1]);
}
static int trial_setting(unsigned i){static const unsigned char patterns[3]={1,3,2};
switch(trial_index){case 1:return !overflow&&trial_bits==((1u<<i)-1u);
case 2:return demo==(i!=1);
case 3:return moisture==1;
case 4:return panels==patterns[i];
case 5:return !south_game_puzzle.shade;
case 6:return loft==(i==0?1:i==1?2:3);
case 8:return loft==patterns[i];
case 9:return alignment==i;
default:return 1;
}}
static COLD int trial_power(void){unsigned i;
if(trial_index>=10)return 0;
for(i=0;i<3;i++)if(trial_near(i)){if(!participant())return wrong(TX_ST_TRIAL_SAME);
if(!field(trials[trial_index].capability,trials[trial_index].xy[i][0],trials[trial_index].xy[i][1]))return wrong(TX_ST_WRONG);
if(trial_bits&(1u<<i))return wrong(TX_ST_TRIAL_ALREADY);
if(!trial_setting(i)){trial_bits=trial_revealed=0;
changed();
return wrong(TX_ST_TRIAL_RESET);
}
if(trial_index==7){trial_revealed=(unsigned char)(trial_revealed|(1u<<i));
changed();
toast(TX_ST_CURRENT);
return 1;
}return trial_mark(i);
}return 0;
}
COLD int south_game_interact(void){unsigned i;
if(game_state!=PLAY||!south_game_is_room((unsigned)room))return 0;
/* Rest must enqueue before the ordinary interaction path synchronizes or
 * mutates any live campaign/checkpoint fields. */
if((room==30&&close(112,208))||(room==31&&close(80,248))){
 if(!south_game_request_rest())toast(TX_ST_LOCKED_A);
 return 1;
}
dirty=0;
sync();
if(trial_index==7)for(i=0;i<3;i++)if(trial_near(i)){if(!participant()){toast(TX_ST_TRIAL_SAME);
return 1;
}if(trial_revealed&(1u<<i))return trial_mark(i);
toast(TX_ST_CURRENT);
return 1;
}
if((room==30&&close(432,208))||(room==31&&close(240,240))||(room==32&&close(208,132))||(room==33&&close(32,104))||(room==35&&close(208,132)))return begin_trial();
if(room>=32){if(close(32,132)){south_game_reset();
toast(TX_ST_RESET);
return 1;
}if(close(120,148)){unsigned dest=room==32?30:room==33||room==34?31:(unsigned)room-1,spawn=room==32?3:room==33?3:room==34?1:0;
return door(dest,spawn);
}}
if(room==30){
if(face==1&&near(px,py,80,136,18))return door(32,0);
if(close(240,264)){persist();
enter_room(22,0);
game_region_warp(208,224);
return 1;
}
if(npc_close(144,160)){talk(22);
return 1;
}if(npc_close(112,160)){talk(28);
return 1;
}if(npc_close(312,176)){talk(25);
return 1;
}if(npc_close(64,208)){talk(26);
return 1;
}if(npc_close(352,224)){talk(27);
return 1;
}if(npc_close(48,160)){talk(29);
return 1;
}if(npc_close(400,192)){talk(24);
return 1;
}
if(close(192,176)){demo^=1;
changed();
if(demo&&offer(22))objective(22,1);
persist();
toast(demo?TX_ST_MIRROR1:TX_ST_MIRROR0);
return 1;
}
if(close(192,240)){if(!offer(22)){toast(TX_ST_FIRST);
return 1;
}hood=1;
changed();
persist();
toast(TX_ST_HOOD);
return 1;
}
if(close(192,208)){if(hood&&offer(22)){objective(22,2);
hood=0;
persist();
toast(TX_ST_REPAIRED);
}else toast(TX_ST_HOOD);
return 1;
}
if(close(240,176)){quiet^=1;
changed();
if(quiet&&ready(28))discovery(1);
persist();
toast(quiet?TX_ST_QUIET:TX_ST_BRIGHT);
return 1;
}
for(i=0;i<3;i++)if(close(280+(int)i*32,208)){if(offer(25))objective(25,1u<<i);
persist();
toast(TX_ST_SHADE_OPEN);
return 1;
}
if(close(144,128)||close(320,128)){if(offer(26))objective(26,close(144,128)?1:2);
persist();
toast(TX_ST_REPAIRED);
return 1;
}
if(close(128,248)||close(384,248)){if(offer(27))objective(27,close(128,248)?1:2);
persist();
toast(TX_ST_REPAIRED);
return 1;
}
}else if(room==31){
if(face==1&&near(px,py,400,65,18))return door(34,0);
if(face==1&&near(px,py,80,96,18))return door(33,0);
if(npc_close(352,160)){talk(23);
return 1;
}
if(close(304,192)){if(offer(23))objective(23,1);
persist();
toast(TX_ST_REPAIRED);
return 1;
}
if(close(352,192)){if((adventure_save.quests.objectives[23]&1)&&offer(23)){objective(23,2);
persist();
toast(TX_ST_REPAIRED);
}else toast(TX_ST_CLUE23A);
return 1;
}
if(close(128,224)||close(160,224)){roots=(unsigned char)(roots|(close(128,224)?1:2));
changed();
toast(TX_ST_REPAIRED);
return 1;
}
if(close(128,80)){drain^=1;
changed();
toast(TX_ST_REPAIRED);
return 1;
}
if(close(384,240)||close(416,240)){panels^=(unsigned char)(close(384,240)?1:2);
changed();
toast(TX_ST_CHANGED);
return 1;
}
if(close(256,144)){ripple=1;
changed();
toast(TX_ST_RILL_CLUE);
return 1;
}
if(close(224,144)){runnel^=1;
changed();
toast(TX_ST_REPAIRED);
return 1;
}
if(close(144,208))return recruit(16,roots==3,TX_ST_ROOT_CLUE);
if(close(160,80))return recruit(17,drain,TX_ST_DRAIN_CLUE);
if(close(400,208))return recruit(19,panels==3,TX_ST_CRAB_CLUE);
if(close(288,96))return recruit(20,(adventure_save.quests.region_flags[18]&1)!=0,TX_ST_TAIL_CLUE);
if(close(256,112))return recruit(21,ripple&&runnel,TX_ST_RILL_CLUE);
}else if(room==32){
if(close(208,64)){if(ready(29))return door(30,4);
say(TX_ST_CLUE29A,TX_ST_CLUE29B);
return 1;
}
if(close(48,48)){if(offer(28))objective(28,1);
persist();
toast(TX_ST_CLUE28B);
return 1;
}
if(close(176,48)){if((adventure_save.quests.objectives[28]&1)&&offer(28)){objective(28,2);
persist();
toast(TX_ST_BAT_CLUE);
}else toast(TX_ST_CLUE28A);
return 1;
}
if(close(72,80)||close(168,80)){unsigned b=close(72,80)?1:2,was=(unsigned)ready(29);
loft^=(unsigned char)b;
changed();
if(offer(29)&&loft==3){objective(29,1);
objective(29,2);
discovery(0);
}persist();
if(loft==3&&!was)say(TX_ST_DISCOVERED,TX_ST_SHORTCUT);else toast(TX_ST_CHANGED);
return 1;
}
if(npc_close(208,112)){say(TX_ST_TAIL_CLUE,TX_ST_BAT_CLUE);
return 1;
}
if(close(120,112))return recruit(22,(adventure_save.quests.region_flags[18]&2)!=0,TX_ST_BAT_CLUE);
}else if(room==33){
if(close(208,48)){sun^=1;
changed();
toast(sun?TX_ST_SHADE_OPEN:TX_ST_SHADE_CLOSED);
return 1;
}
if(close(208,80)){static const int labels[3]={TX_ST_ALIGN0,TX_ST_ALIGN1,TX_ST_ALIGN2};
alignment=(unsigned char)((alignment+1)%3);
changed();
toast(labels[alignment]);
return 1;
}
if(close(208,104)){overflow^=1;
if(trial_index==1)trial_bits=0;
changed();
toast(TX_ST_TRIAL_RESET);
return 1;
}
if(close(208,128)){static const int labels[3]={TX_ST_MOIST0,TX_ST_MOIST1,TX_ST_MOIST2};
moisture=(unsigned char)((moisture+1)%3);
changed();
toast(labels[moisture]);
return 1;
}
for(i=0;i<3;i++)if(close(56+(int)i*56,48)){pins=(unsigned char)(pins|(1u<<i));
changed();
toast(TX_ST_REPAIRED);
return 1;
}
if(close(40,72))return recruit(18,sun,TX_ST_FROG_CLUE);
if(close(176,96))return recruit(23,pins==7,TX_ST_PIN_CLUE);
}else if(room<=36){
if(room==36&&close(208,112)){if(adventure_save.quests.objectives[24]&4)return door(31,1);
toast(TX_ST_ARRANGE);
return 1;
}
if(close(208,56)){unsigned bit=1u<<(room-34);
if(adventure_save.quests.objectives[24]&bit)return door((unsigned)room+1,0);
say(room==34?TX_ST_WATER_A:room==35?TX_ST_METAL_A:TX_ST_ARRANGE,TX_ST_EXIT_A);
return 1;
}
if(close(room==36?80:112,room==36?104:56)){mechanism(SOUTH_ACTION_MIRROR0);
return 1;
}
if(room!=34&&close(room==36?80:112,room==36?48:104)){mechanism(SOUTH_ACTION_MIRROR1);
return 1;
}
if(room!=34&&close(176,room==35?80:104)){mechanism(SOUTH_ACTION_SHADE);
return 1;
}
if(room==34&&(close(112,104)||close(192,128))){say(TX_ST_WATER_A,TX_ST_WATER_B);
return 1;
}
if(room==35&&close(192,104)){say(TX_ST_METAL_A,TX_ST_METAL_B);
return 1;
}
}else{
if(close(192,112)){south_game_puzzle.shade^=1;
changed();
toast(south_game_puzzle.shade?TX_ST_SHADE_CLOSED:TX_ST_SHADE_OPEN);
return 1;
}
if(close(120,112)){
if(south_game_machine_stage>=1&&south_game_machine_stage<=4)return 0;
if(south_game_machine_stage==5){if(done(24)){persist();
enter_room(30,4);
}else claim(24);
return 1;
}
south_game_machine_stage=1;
south_game_machine_ticks=60;
changed();
say(TX_ST_CROWN_A,TX_ST_CROWN_B);
return 1;
}
}
return 0;
}
COLD int south_game_power(unsigned command){int r;
(void)command;
if(game_state!=PLAY||!south_game_is_room((unsigned)room))return 0;
/* Rest must enqueue before the ordinary interaction path synchronizes or
 * mutates any live campaign/checkpoint fields. */
if((room==30&&close(112,208))||(room==31&&close(80,248))){
 if(!south_game_request_rest())toast(TX_ST_LOCKED_A);
 return 1;
}
dirty=0;
sync();
/* Mandatory tagged targets get priority over optional trial fixtures. */
if(room==34&&close(112,104)){if(!field(26,112,104))return wrong(TX_ST_WRONG);
if(!south_puzzle_solved(&south_game_puzzle,34))return wrong(TX_ST_ARRANGE);
objective(24,1);
persist();
toast(TX_ST_SOLVED);
return 1;
}
if(room==35&&close(192,104)){if(!field(17,192,104))return wrong(TX_ST_WRONG);
if(!south_puzzle_solved(&south_game_puzzle,35))return wrong(TX_ST_ARRANGE);
objective(24,2);
persist();
toast(TX_ST_SOLVED);
return 1;
}
r=trial_power();
if(r)return r;
return 0;
}
COLD int south_game_target(int*x,int*y,int*r){if(room!=37||south_game_machine_stage!=3||!south_game_machine_hp||south_game_puzzle.shade)return 0;
if(x)*x=machine_x;
if(y)*y=64;
if(r)*r=13;
return 1;
}
COLD int south_game_weapon_hit(unsigned cls,int x,int y,unsigned damage){if(game_state!=PLAY||!south_game_target(0,0,0)||cls<1||cls>3||cls!=game_weapon_class()||!damage||!near(x,y,machine_x,64,27))return 0;
if(damage>south_game_machine_hp){damage=south_game_machine_hp;
}south_game_machine_hp=(unsigned char)(south_game_machine_hp-damage);
changed();
if(!south_game_machine_hp){south_game_machine_stage=5;
south_game_machine_ticks=0;
objective(24,8);
persist();
toast(TX_ST_MACHINE_DONE);
}return 1;
}
COLD void south_game_tick(void){if(game_state!=PLAY)return;
if(door_notice)door_notice--;
if(!south_game_is_room((unsigned)room))return;
if(room==37&&south_game_machine_stage>=1&&south_game_machine_stage<=4){
if(south_game_machine_ticks)south_game_machine_ticks--;
if(south_game_machine_stage==2){machine_x=(short)(88+(40-south_game_machine_ticks)*64/40);
changed();
if(!machine_hit&&py>=76&&py<=100&&ab(px-machine_x)<20){machine_hit=1;
game_north_hurt(16);
}}
if(!south_game_machine_ticks){if(south_game_machine_stage==1){south_game_machine_stage=2;
south_game_machine_ticks=40;
machine_hit=0;
}
else if(south_game_machine_stage==2){south_game_machine_stage=3;
south_game_machine_ticks=100;
toast(south_game_puzzle.shade?TX_ST_CROWN_B:TX_ST_OPEN);
}
else if(south_game_machine_stage==3){south_game_machine_stage=4;
south_game_machine_ticks=30;
}
else{south_game_machine_stage=1;
south_game_machine_ticks=60;
machine_x=88;
toast(TX_ST_WARN);
}changed();
}
}
if(transition_lock)return;
if(room==30){if((keys&UP)&&px>=288&&px<=320&&py<=18){door(31,0);
return;
}}
else if(room==31){if((keys&DOWN)&&px>=224&&px<=255&&py>=298){door(30,1);
return;
}}
else if((keys&DOWN)&&px>=108&&px<=132&&py>=143){unsigned dest=room==32?30:room==33||room==34?31:(unsigned)room-1,spawn=room==32?3:room==33?3:room==34?1:0;
door(dest,spawn);
}
}
COLD int south_game_name(void){static const int n[8]={TX_ST_ROOM30,TX_ST_ROOM31,TX_ST_ROOM32,TX_ST_ROOM33,TX_ST_ROOM34,TX_ST_ROOM35,TX_ST_ROOM36,TX_ST_ROOM37};
return south_game_is_room((unsigned)room)?n[room-30]:0;
}
COLD int south_game_quest_text(void){unsigned q;
for(q=22;q<=29;q++)if(state(q)==2)return qnames[q-22];
if(!done(22))return TX_ST_Q22;
if(!done(23))return TX_ST_Q23;
if(!done(24))return TX_ST_Q24;
return TX_ST_JOURNAL;
}
COLD void south_game_draw_journal(void){static const int s[4]={TX_ST_UNSEEN,TX_ST_ACTIVE,TX_ST_READY,TX_ST_CLAIMED};
unsigned sel=south_game_journal_selection%18,q,b,x=88;
CreatureInstance*c=progression_selected();
box(8,31,224,122);
centered(TX_ST_JOURNAL,34,PAL_GOLD3);
if(sel<8){q=22+sel;
text(qnames[sel],18,54,PAL_GOLD4);
text(s[state(q)],173,54,PAL_TEAL2);
text(clues[sel][0],14,76,PAL_GOLD4);
text(clues[sel][1],14,94,PAL_GOLD4);
text(TX_ST_OBJECTIVES,18,115,PAL_TEAL2);
for(b=1;b<=8;b<<=1)if(southern_quest_mask(q)&b){rect((int)x,118,8,8,(adventure_save.quests.objectives[q]&b)?PAL_GOLD3:PAL_STONE1);
x+=13;
}}
else{sel-=8;
text(tnames[sel],18,54,PAL_GOLD4);
text(tclues[sel][0],14,76,PAL_GOLD4);
text(tclues[sel][1],14,94,PAL_GOLD4);
q=c&&creatures_has_trial_qualified(c,trials[sel].family,1)?7:trial_index==sel?trial_bits:0;
for(b=1;b<=4;b<<=1){rect((int)x,118,8,8,(q&b)?PAL_GOLD3:PAL_STONE1);
x+=13;
}}
centered(TX_ST_KEYS,138,PAL_TEAL2);
}
COLD int south_game_menu_input(int k){if(journal_tab!=JOURNAL_TAB)return 0;
if(k&UP){south_game_journal_selection=(south_game_journal_selection+17)%18;
changed();
return 1;
}if(k&DOWN){south_game_journal_selection=(south_game_journal_selection+1)%18;
changed();
return 1;
}return 0;
}
#include "south_game_draw.inc"
