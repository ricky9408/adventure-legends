#include "journal_nav.h"
#include "journey_map.h"
/* Standalone historical host probes may omit the optional map module. */
extern void journey_map_open(void) __attribute__((weak));
extern void journey_map_begin(void) __attribute__((weak));
extern int journey_map_input(int) __attribute__((weak));
extern void journey_map_draw(void) __attribute__((weak));
#include "gear_menu.h"
#include "quickparty.h"
#include "progression.h"
#include "assets.h"
#include "ui.h"
extern int journal_tab;
extern volatile int save_failed;
extern void save_game(void);
extern unsigned journal_page_count(void);
extern void box(int,int,int,int),rect(int,int,int,int,unsigned char),text(int,int,int,int),centered(int,int,int);
unsigned journal_nav_revision;
int journal_nav_category,journal_nav_quest,journal_nav_detail;
static unsigned repeat_direction,repeat_delay;
#define A 1
#define B 2
#define SELECT 4
#define START 8
#define RIGHT 16
#define LEFT 32
#define UP 64
#define DOWN 128
#define DIRECTIONS 240
#define GOLD PAL_GOLD3
#define CREAM PAL_GOLD4
#define TEAL PAL_TEAL2
static const unsigned char destinations[8]={JOURNAL_ITEMS,JOURNAL_GEAR,JOURNAL_PARTY,JOURNAL_GROWTH,JOURNAL_MAP,JOURNAL_QUESTS,JOURNAL_CONTROLS,255};
#include "journal_quest_list.inc"
static unsigned quest_count(void){unsigned pages=journal_page_count();if(pages<5)return 1;if(pages>13)pages=13;return pages-4;}
static void changed(void){journal_nav_revision++;}
static void enter(int page){journal_tab=page;journal_nav_detail=0;repeat_direction=repeat_delay=0;if(page==JOURNAL_GEAR)gear_menu_reset();else if(page==JOURNAL_PARTY)quickparty_menu_reset();else if(page==JOURNAL_GROWTH)progression_menu_reset();else if(page==JOURNAL_MAP&&journey_map_open)journey_map_open();changed();}
void journal_nav_open(void){if(journey_map_begin)journey_map_begin();journal_nav_category=0;journal_nav_quest=0;enter(JOURNAL_HUB);}
int journal_nav_keys(int held,int pressed){unsigned direction=(unsigned)held&DIRECTIONS;int input=pressed&~DIRECTIONS;
 if(direction!=RIGHT&&direction!=LEFT&&direction!=UP&&direction!=DOWN){repeat_direction=repeat_delay=0;return input|(pressed&DIRECTIONS);}
 if(direction!=repeat_direction){repeat_direction=direction;repeat_delay=18;return input|(int)direction;}
 if(pressed&(B|START)){repeat_direction=repeat_delay=0;return input;}
 if(repeat_delay&&!--repeat_delay){repeat_delay=6;return input|(int)direction;}
 return input;
}
int journal_nav_input(int input){int direction=input&DIRECTIONS;
 if(input&START){repeat_direction=repeat_delay=0;return JOURNAL_CLOSE;}
 if(input&B){
  if((journal_tab==JOURNAL_PARTY&&quickparty_menu_back())||(journal_tab==JOURNAL_GROWTH&&progression_menu_back()))return JOURNAL_CONSUMED;
  if(journal_tab==JOURNAL_MAP&&journey_map_input&&journey_map_input(input)){changed();return JOURNAL_CONSUMED;}
  if(journal_tab==JOURNAL_HUB)return JOURNAL_CLOSE;
  if(journal_nav_detail&&journal_tab>=JOURNAL_REGION_FIRST&&journal_tab<=JOURNAL_REGION_LAST){journal_nav_detail=0;changed();return JOURNAL_CONSUMED;}
  enter(journal_tab==JOURNAL_GOAL||(journal_tab>=JOURNAL_REGION_FIRST&&journal_tab<=JOURNAL_REGION_LAST)?JOURNAL_QUESTS:JOURNAL_HUB);return JOURNAL_CONSUMED;
 }
 if(input&SELECT)return JOURNAL_CONSUMED;
 if(journal_tab==JOURNAL_HUB){
  if(direction){int row=journal_nav_category>>1,column=journal_nav_category&1;
   if(direction==RIGHT||direction==LEFT)column^=1;else if(direction==UP)row=(row+3)&3;else if(direction==DOWN)row=(row+1)&3;else return JOURNAL_CONSUMED;
   journal_nav_category=row*2+column;changed();return JOURNAL_CONSUMED;
  }
  if(input&A){unsigned page=destinations[journal_nav_category];if(page==255)return JOURNAL_CLOSE;enter((int)page);}return JOURNAL_CONSUMED;
 }
 if(journal_tab==JOURNAL_QUESTS){unsigned count=quest_count();if((unsigned)journal_nav_quest>=count)journal_nav_quest=0;
  if(direction){if(direction==UP)journal_nav_quest=journal_nav_quest?journal_nav_quest-1:(int)count-1;else if(direction==DOWN)journal_nav_quest=(unsigned)(journal_nav_quest+1)<count?journal_nav_quest+1:0;else return JOURNAL_CONSUMED;changed();return JOURNAL_CONSUMED;}
  if(input&A)enter(journal_nav_quest?journal_nav_quest+4:JOURNAL_GOAL);return JOURNAL_CONSUMED;
 }
 if(journal_tab>=JOURNAL_REGION_FIRST&&journal_tab<=JOURNAL_REGION_LAST){const struct QuestList*list=&quest_lists[journal_tab-JOURNAL_REGION_FIRST];
  if(journal_nav_detail)return JOURNAL_CONSUMED;if(*list->selection>=list->count)*list->selection=0;
  if(direction){if(direction==UP)*list->selection=*list->selection?*list->selection-1:list->count-1;else if(direction==DOWN)*list->selection=*list->selection+1<list->count?*list->selection+1:0;else return JOURNAL_CONSUMED;changed();return JOURNAL_CONSUMED;}
  if(input&A){journal_nav_detail=1;changed();}return JOURNAL_CONSUMED;
 }
 if(journal_tab==JOURNAL_GOAL)return !direction&&(input&A)?JOURNAL_DISPATCH:JOURNAL_CONSUMED;
 if(journal_tab==JOURNAL_CONTROLS){if(!direction&&(input&A)&&save_failed)save_game();return JOURNAL_CONSUMED;}
 if(journal_tab==JOURNAL_MAP){if(journey_map_input&&(input&(A|DIRECTIONS))){journey_map_input(input);changed();}return JOURNAL_CONSUMED;}
 if(direction&&(direction!=RIGHT&&direction!=LEFT&&direction!=UP&&direction!=DOWN))return JOURNAL_CONSUMED;return JOURNAL_DISPATCH;
}
int journal_nav_draw(void){unsigned i;
 if(journal_tab==JOURNAL_MAP&&journey_map_draw){journey_map_draw();return 1;}
 if(journal_tab>=JOURNAL_REGION_FIRST&&journal_tab<=JOURNAL_REGION_LAST&&!journal_nav_detail){const struct QuestList*list=&quest_lists[journal_tab-JOURNAL_REGION_FIRST];unsigned selection=*list->selection<list->count?*list->selection:0,first=selection>4?selection-4:0;
  box(8,31,224,123);centered(list->title,33,GOLD);
  for(i=first;i<list->count&&i<first+5;i++){int y=52+(int)(i-first)*16;if(i==selection)rect(13,y,214,16,PAL_STONE2);text(list->names[i],14,y,i==selection?GOLD:CREAM);}
  if(first)rect(224,49,3,2,GOLD);if(first+5<list->count)rect(224,132,3,2,GOLD);centered(TX_PF_QUEST_KEYS,137,TEAL);return 1;
 }
 if(journal_tab==JOURNAL_HUB){static const int labels[8]={TX_PF_ITEMS,TX_PF_GEAR,TX_PF_PARTY,TX_PF_GROWTH,TX_PF_MAP,TX_PF_QUESTS,TX_PF_CONTROLS,TX_PF_RESUME};box(8,31,224,123);centered(TX_PF_HUB,33,GOLD);
  for(i=0;i<8;i++){int x=17+(int)(i&1)*108,y=54+(int)(i>>1)*19;if((int)i==journal_nav_category)rect(x-3,y-1,102,18,PAL_STONE2);text(labels[i],x,y,(int)i==journal_nav_category?GOLD:CREAM);}centered(TX_PF_HUB_KEYS,136,TEAL);return 1;
 }
 if(journal_tab==JOURNAL_QUESTS){static const int labels[9]={TX_PF_CURRENT_QUEST,TX_PF_REGION_0,TX_PF_REGION_1,TX_PF_REGION_2,TX_PF_REGION_3,TX_PF_REGION_4,TX_PF_REGION_5,TX_PF_REGION_6,TX_PF_REGION_7};unsigned count=quest_count(),first=journal_nav_quest>4?(unsigned)journal_nav_quest-4:0;box(8,31,224,123);centered(TX_PF_QUESTS,33,GOLD);
  for(i=first;i<count&&i<first+5;i++){int y=52+(int)(i-first)*16;if((int)i==journal_nav_quest)rect(18,y,204,16,PAL_STONE2);text(labels[i],28,y,(int)i==journal_nav_quest?GOLD:CREAM);}if(first)rect(213,49,4,2,GOLD);if(first+5<count)rect(213,132,4,2,GOLD);centered(TX_PF_QUEST_KEYS,137,TEAL);return 1;
 }
 if(journal_tab==JOURNAL_CONTROLS){static const int labels[5]={TX_PF_CONTROLS_0,TX_PF_CONTROLS_1,TX_PF_CONTROLS_2,TX_PF_CONTROLS_3,TX_PF_CONTROLS_4};box(8,31,224,123);centered(TX_PF_CONTROLS,33,GOLD);
  for(i=0;i<5;i++){int retry=i==4&&save_failed;if(retry)rect(14,115,212,18,PAL_STONE2);text(retry?TX_PF_RETRY_SAVE:labels[i],18,52+(int)i*16,retry?GOLD:CREAM);}centered(TX_PF_BACK_CLOSE,138,TEAL);return 1;
 }return 0;
}
