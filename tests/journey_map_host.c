/* Host contract checks; actual map, journal, quest and spawn predicates. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "journey_map.h"
#include "journey_map_text.h"
#include "journal_nav.h"
#include "connected_roads.h"
#include "travel_feedback.h"
#include "progression.h"
#include "assets.h"
Save5State adventure_save;
volatile int room,bridge_open,torches,save_failed;
volatile unsigned chapter_flags,room_flags,story_seen;
int seen_temple,seen_boss,journal_tab;
unsigned region_game_journal_selection,north_game_journal_selection,south_game_journal_selection;
unsigned magma_game_journal_selection,underwater_game_journal_selection,return_game_journal_selection;
static unsigned short pixels[19200];
unsigned short *screen=pixels;
static unsigned captures,draws;
static unsigned drawn_text[TX_COUNT];
typedef struct { int x,y,w,h; } TextBox;
static TextBox text_boxes[32];
static unsigned text_box_count;
void text_spans(const UiText*t,int x,int y,int col){
 const UiRun*r=t->runs[x&1];unsigned i,j;
 assert(x>=8&&x+t->width<=232&&y>=31&&y+t->height<=154);
 for(i=0;i<text_box_count;i++){
  const TextBox*b=&text_boxes[i];
  if(x<b->x+b->w&&x+t->width>b->x&&y<b->y+b->h&&y+t->height>b->y){
   fprintf(stderr,"map text overlap (%d,%d,%u,%u) against (%d,%d,%d,%d)\n",x,y,t->width,t->height,b->x,b->y,b->w,b->h);abort();
  }
 }
 assert(text_box_count<32);text_boxes[text_box_count++]=(TextBox){x,y,t->width,t->height};
 for(i=0;i<t->count[x&1];i++)for(j=0;j<r[i].count;j++){unsigned at=(unsigned)(y*120+(x>>1))+r[i].offset+j;
  if(r[i].mask&1)((unsigned char*)pixels)[at*2]=(unsigned char)col;
  if(r[i].mask&2)((unsigned char*)pixels)[at*2+1]=(unsigned char)col;
 }
}
void gear_menu_reset(void){}
void quickparty_menu_reset(void){}
void progression_menu_reset(void){}
int quickparty_menu_back(void){return 0;}
int progression_menu_back(void){return 0;}
unsigned journal_page_count(void){return 13;}
void save_game(void){assert(!"Map inspection attempted a save");}
void rect(int x,int y,int w,int h,unsigned char c){int xx,yy;assert(x>=8&&y>=31&&x+w<=232&&y+h<=154);for(yy=y;yy<y+h;yy++)for(xx=x;xx<x+w;xx++)((unsigned char*)pixels)[yy*240+xx]=c;}
void box(int x,int y,int w,int h){rect(x,y,w,h,1);rect(x,y,w,1,PAL_GOLD2);rect(x,y+h-1,w,1,PAL_GOLD2);rect(x,y,1,h,PAL_GOLD2);rect(x+w-1,y,1,h,PAL_GOLD2);}
void text(int id,int x,int y,int col){
 assert(id>=0&&id<TX_COUNT);drawn_text[id]++;text_spans(&ui_texts[id],x,y,col);
}
void centered(int id,int y,int col){text(id,(240-ui_texts[id].width)/2,y,col);}
static void draw(void){unsigned x,y;memset(pixels,0x77,sizeof pixels);memset(drawn_text,0,sizeof drawn_text);text_box_count=0;journey_map_draw();draws++;
 for(y=0;y<160;y++)for(x=0;x<240;x++)if(x<8||x>=232||y<31||y>=154)assert(((unsigned char*)pixels)[y*240+x]==0x77);
}
static void capture(const char*label){const char*dir=getenv("JOURNEY_MAP_CAPTURE_DIR");FILE*f;char path[1024];unsigned i;if(!dir)return;
 snprintf(path,sizeof path,"%s/%s.ppm",dir,label);f=fopen(path,"wb");assert(f);fprintf(f,"P6\n240 160\n255\n");
 for(i=0;i<38400;i++){unsigned c=game_palette[((unsigned char*)pixels)[i]];fputc((c&31)*255/31,f);fputc(((c>>5)&31)*255/31,f);fputc(((c>>10)&31)*255/31,f);}assert(!fclose(f));captures++;
}
static void fresh(void){memset(&adventure_save,0,sizeof adventure_save);chapter_flags=room_flags=story_seen=0;seen_temple=seen_boss=bridge_open=torches=0;room=0;}
static void full(void){unsigned i;fresh();chapter_flags=15;room_flags=65535;story_seen=127;seen_temple=seen_boss=bridge_open=1;torches=3;adventure_save.campaign.chapter_flags=15;
 memset(adventure_save.quests.states,255,16);memset(adventure_save.quests.region_flags,255,32);memset(adventure_save.quests.anchors,255,16);
 for(i=0;i<64;i++)adventure_save.quests.objectives[i]=65535;
 adventure_save.roster.lifetime_field_aid[0]=255;
}
static int find(unsigned from,unsigned to,unsigned kind,JourneyMapExit*out){JourneyMapExit e;unsigned n;for(n=0;journey_map_exit(from,n,&e);n++)if(e.target==to&&e.kind==kind){if(out)*out=e;return 1;}return 0;}
static void topology(void){JourneyMapExit e;unsigned i,a,n;full();
 for(i=0;i<connected_road_count;i++){const ConnectedRoad*r=&connected_roads[i];assert(find(r->room,r->target,JOURNEY_ROAD,&e)==!(r->reserved&ROAD_ARRIVAL_ONLY));
  if(!(r->reserved&ROAD_ARRIVAL_ONLY)){assert(e.open);assert(e.direction==r->edge||(r->edge==0&&(e.direction==9||e.direction==10))||(r->edge==1&&(e.direction==11||e.direction==12))||(r->edge==2&&(e.direction==13||e.direction==14))||(r->edge==3&&(e.direction==15||e.direction==16)));}
 }
 assert(find(63,65,JOURNEY_ROAD,&e)&&e.direction==JOURNEY_N_LEFT);
 assert(find(63,67,JOURNEY_ROAD,&e)&&e.direction==JOURNEY_N_RIGHT);
 assert(find(16,55,JOURNEY_STAIRS,&e)&&e.direction==JOURNEY_E);
 assert(find(55,16,JOURNEY_STAIRS,&e)&&e.direction==JOURNEY_S);
 assert(find(0,60,JOURNEY_DOOR,&e)&&e.direction==JOURNEY_E);
 assert(find(22,30,JOURNEY_FERRY,&e));assert(find(30,22,JOURNEY_FERRY,&e));
 assert(find(30,38,JOURNEY_LIFT,&e));assert(find(38,30,JOURNEY_LIFT,&e));
 assert(find(38,46,JOURNEY_DIVE,&e));assert(find(46,38,JOURNEY_LIFT,&e));
 for(a=0;a<78;a++){assert(journey_map_exit(a,0,&e));for(n=0;journey_map_exit(a,n,&e);n++){assert(n<12&&e.target<78&&e.kind<=6&&e.direction<=16);assert(!(a==45&&e.target==38));assert(!(a==53&&e.target==46));assert(!(a==8&&e.target==0));assert(!(a==13&&e.target==0));}}
 assert(!journey_map_exit(78,0,&e));assert(!journey_map_exit(0,0,0));
 puts("PASS all78 areas have authored exits;92 directed roads match live topology, transports and stairs are typed, retired shortcuts absent");
}
static void gates_and_secrets(void){JourneyMapExit e;Save5State before;fresh();before=adventure_save;
 assert(find(0,4,JOURNEY_ROAD,&e)&&!e.open);assert(find(0,9,JOURNEY_ROAD,&e)&&!e.open);
 assert(find(0,54,JOURNEY_ROAD,&e)&&!e.open);assert(find(0,60,JOURNEY_DOOR,&e)&&!e.open);
 assert(find(2,3,JOURNEY_DOOR,&e)&&!e.open);torches=3;assert(find(2,3,JOURNEY_DOOR,&e)&&e.open);
 assert(find(9,10,JOURNEY_DOOR,&e)&&!e.open);room_flags=SAVE4_CORE_PATH_OPEN;assert(find(9,10,JOURNEY_DOOR,&e)&&e.open);
 assert(find(4,14,JOURNEY_DOOR,&e)&&!e.named);assert(find(9,15,JOURNEY_DOOR,&e)&&!e.named);
 assert(!find(32,30,JOURNEY_PASSAGE,&e));assert(!find(39,40,JOURNEY_PASSAGE,&e));assert(!find(40,39,JOURNEY_PASSAGE,&e));assert(!find(44,39,JOURNEY_PASSAGE,&e));assert(!memcmp(&before,&adventure_save,sizeof before));
 chapter_flags=1;assert(find(0,4,JOURNEY_ROAD,&e)&&e.open);assert(find(0,9,JOURNEY_ROAD,&e)&&!e.open);
 full();assert(find(32,30,JOURNEY_PASSAGE,&e)&&e.open);assert(find(39,40,JOURNEY_PASSAGE,&e)&&e.open);assert(find(44,39,JOURNEY_PASSAGE,&e)&&e.open);
 save5_quest_set_state(&adventure_save.quests,57,SAVE5_QUEST_READY);assert(find(67,69,JOURNEY_ROAD,&e)&&!e.open);assert(find(69,67,JOURNEY_ROAD,&e)&&!e.open);
 puts("PASS closed chapter/spawn gates, original torch gate, and concealed shortcut/trial knowledge");
}
static void knowledge_bitset_equivalence(void){unsigned stage,a,source,i,n;JourneyMapExit e;
 for(stage=0;stage<2;stage++)for(a=0;a<78;a++){
  unsigned char expected[78]={0};fresh();room=(int)a;
  if(stage){adventure_save.quests.objectives[35]=2;adventure_save.quests.objectives[24]=4;adventure_save.quests.objectives[32]=4;save5_quest_set_state(&adventure_save.quests,29,SAVE5_QUEST_READY);}
  expected[0]=expected[1]=expected[a]=1;
  for(i=0;i<3;i++){source=i<2?i:a;for(n=0;journey_map_exit(source,n,&e);n++)if(e.named)expected[e.target]=1;}
  journey_map_reset();for(i=0;i<78;i++)assert(journey_map_is_known(i)==expected[i]);
 }
 full();journal_nav_open();journal_nav_category=4;journal_nav_input(1);assert(journey_map_is_known(77));
 fresh();journal_nav_open();journal_nav_category=4;journal_nav_input(1);assert(!journey_map_is_known(77));
 puts("PASS generated knowledge bitsets match actual exits for156 source/discovery states; a new pause invalidates old knowledge");
}
static void layouts_and_purity(void){Save5State before;unsigned stage,a,n;char label[64];for(stage=0;stage<3;stage++){
  if(stage==2)full();else fresh();if(stage==1){chapter_flags=7;adventure_save.campaign.chapter_flags=7;adventure_save.quests.region_flags[0]=1;}
  for(a=0;a<78;a++){room=(int)a;before=adventure_save;journey_map_reset();assert(journey_map_selected_place()==a&&journey_map_is_known(a));
   for(n=0;n<12;n++){draw();if(stage==2&&n==0){snprintf(label,sizeof label,"room-%02u-map",a);capture(label);}journey_map_input(128);}
   journey_map_input(1);assert(journey_map_overview());for(n=0;n<20;n++){draw();journey_map_input(128);}if(stage==2&&(a==0||a==46||a==70)){snprintf(label,sizeof label,"room-%02u-places",a);capture(label);}
   for(n=0;n<9;n++){journey_map_input(16);draw();}assert(!memcmp(&before,&adventure_save,sizeof before));
  }
 }
 printf("PASS %u pixel-boundary and text-overlap checked host renders across78 areas/3 progress states; all save bytes unchanged\n",draws);
}
static void navigation(void){Save5State before;unsigned revision;fresh();before=adventure_save;journal_nav_open();journal_nav_category=4;
 assert(journal_nav_input(1)==JOURNAL_CONSUMED&&journal_tab==JOURNAL_MAP);assert(journey_map_selected_place()==0&&!journey_map_overview());
 revision=journal_nav_revision;journal_nav_input(0);journal_nav_input(4);assert(journal_nav_revision==revision);journal_nav_input(128);assert(journal_nav_revision>revision&&journey_map_selected_exit()==1);
 journal_nav_input(4);assert(!journey_map_overview());journal_nav_input(1);assert(journey_map_overview());journal_nav_input(128);journal_nav_input(1);assert(!journey_map_overview());
 journal_nav_input(2);assert(journey_map_overview()&&journal_tab==JOURNAL_MAP);journal_nav_input(2);assert(!journey_map_overview()&&journey_map_selected_place()==0);
 journal_nav_input(2);assert(journal_tab==JOURNAL_HUB);journal_nav_category=4;journal_nav_input(1);assert(journal_nav_input(8)==JOURNAL_CLOSE);
 journal_nav_open();journal_nav_category=4;journal_nav_input(1);assert(!journey_map_overview()&&journey_map_selected_exit()==0);assert(!memcmp(&before,&adventure_save,sizeof before));
 fresh();journey_map_reset();assert(!journey_map_is_known(14)&&!journey_map_is_known(15)&&!journey_map_is_known(77));
 journey_map_input(1);journey_map_input(16);journey_map_input(16);journey_map_input(128);journey_map_input(1);
 assert(journey_map_selected_place()==60&&!journey_map_is_known(61));draw();assert(!drawn_text[TX_RT_ROOM61]);capture("fresh-known-maproom-hides-onward-name");
 puts("PASS A choose, B nested back, Start close, Select unused, reopening resets, no travel/save mutation");
}
int main(void){topology();gates_and_secrets();knowledge_bitset_equivalence();layouts_and_purity();navigation();printf("Host map captures: %u\n",captures);return 0;}
