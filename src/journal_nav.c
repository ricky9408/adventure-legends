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
#include "collection_journal.h"
#include "growth_goals.h"
#include "growth_journal_text.h"
#include "assets.h"
#include "ui.h"
extern int journal_tab;
extern volatile int save_failed;
extern void save_game(void);
extern unsigned journal_page_count(void);
extern void box(int,int,int,int),rect(int,int,int,int,unsigned char),text(int,int,int,int),centered(int,int,int);
extern void text_spans(const UiText *text,int x,int y,int color);
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
static const unsigned char destinations[9]={JOURNAL_ITEMS,JOURNAL_GEAR,JOURNAL_PARTY,JOURNAL_GROWTH,JOURNAL_MAP,JOURNAL_QUESTS,JOURNAL_CONTROLS,255,JOURNAL_COLLECTION};
#include "journal_quest_list.inc"
static unsigned quest_count(void){unsigned pages=journal_page_count();if(pages<5)return 1;if(pages>13)pages=13;return pages-4;}
static void changed(void){journal_nav_revision++;}
static void enter(int page){journal_tab=page;journal_nav_detail=0;repeat_direction=repeat_delay=0;if(page==JOURNAL_GEAR)gear_menu_reset();else if(page==JOURNAL_PARTY)quickparty_menu_reset();else if(page==JOURNAL_GROWTH)progression_menu_reset();else if(page==JOURNAL_COLLECTION)collection_journal_open();else if(page==JOURNAL_MAP&&journey_map_open)journey_map_open();changed();}
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
  if(journal_tab==JOURNAL_COLLECTION&&collection_journal_back()){changed();return JOURNAL_CONSUMED;}
  if(journal_tab==JOURNAL_MAP&&journey_map_input&&journey_map_input(input)){changed();return JOURNAL_CONSUMED;}
  if(journal_tab==JOURNAL_HUB)return JOURNAL_CLOSE;
  if(journal_nav_detail&&journal_tab>=JOURNAL_REGION_FIRST&&journal_tab<=JOURNAL_REGION_LAST){journal_nav_detail=0;changed();return JOURNAL_CONSUMED;}
  enter(journal_tab==JOURNAL_GOAL||(journal_tab>=JOURNAL_REGION_FIRST&&journal_tab<=JOURNAL_REGION_LAST)?JOURNAL_QUESTS:JOURNAL_HUB);return JOURNAL_CONSUMED;
 }
 if(input&SELECT)return JOURNAL_CONSUMED;
 if(journal_tab==JOURNAL_HUB){
  if(direction){int row=journal_nav_category>>1,column=journal_nav_category&1;
   if(direction==RIGHT||direction==LEFT){if(row<4)column^=1;}
   else if(direction==UP){row=row?row-1:4;if(row==4&&column)row=3;}
   else if(direction==DOWN){row=row<4?row+1:0;if(row==4&&column)row=0;}
   else return JOURNAL_CONSUMED;
   journal_nav_category=row*2+column;changed();return JOURNAL_CONSUMED;
  }
  if(input&A){unsigned page=destinations[journal_nav_category];if(page==255)return JOURNAL_CLOSE;enter((int)page);}return JOURNAL_CONSUMED;
 }
 if(journal_tab==JOURNAL_COLLECTION){int result=collection_journal_input(input);if(result==COLLECTION_OPEN_PARTY){unsigned member=collection_journal_instance();enter(JOURNAL_PARTY);if(member<CREATURE_ROSTER_CAPACITY)quickparty_menu_candidate=(int)member;}changed();return JOURNAL_CONSUMED;}
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
/* SELECT shows the journey goal. A short L tap while one direction is held steps.
 * Line: SELECT 目的  L＋方向で一歩 */
static void field_step_control_line(int x,int y,int color){
 static const UiRun even[]={{30,1,1},{50,1,2},{57,1,1},{74,1,2},{142,4,3},{147,1,2},{150,1,1},{170,1,2},{176,1,2},{194,1,2},{240,1,2},{241,1,3},{243,2,3},{245,2,1},{249,2,3},{251,1,1},{252,2,3},{254,1,1},{255,2,3},{257,1,1},{262,1,1},{265,1,2},{267,1,2},{270,2,3},{272,1,1},{279,1,1},{284,1,2},{288,5,3},{293,1,1},{296,1,1},{313,1,1},{314,1,2},{315,2,3},{360,1,1},{362,2,1},{366,1,1},{369,1,1},{372,1,1},{376,1,1},{382,1,1},{385,1,2},{387,2,3},{389,1,2},{392,1,1},{399,1,1},{404,1,2},{410,1,1},{414,5,3},{419,1,1},{422,3,3},{433,1,1},{434,1,2},{480,1,1},{483,1,1},{486,1,1},{489,1,1},{492,1,1},{496,1,1},{502,4,3},{507,1,1},{508,2,2},{512,1,1},{519,1,1},{524,1,2},{530,1,1},{534,1,1},{539,1,1},{540,2,3},{543,1,1},{551,1,1},{553,1,1},{554,1,2},{600,1,1},{603,1,1},{606,1,1},{609,1,1},{612,1,1},{616,1,1},{622,1,1},{625,1,2},{627,1,1},{628,1,2},{632,1,1},{639,1,1},{644,1,2},{650,3,3},{654,1,1},{659,1,1},{662,1,2},{664,1,2},{666,5,3},{671,1,1},{672,5,3},{677,1,1},{720,1,2},{721,1,3},{723,2,3},{726,1,1},{729,2,3},{732,1,1},{736,1,1},{742,1,1},{745,1,2},{747,2,3},{750,1,1},{752,1,1},{759,1,1},{762,1,2},{763,4,3},{770,1,1},{772,1,2},{774,1,1},{775,1,2},{776,2,3},{779,1,1},{782,1,1},{783,1,2},{785,1,1},{793,1,1},{794,1,2},{796,1,1},{842,2,1},{846,1,1},{849,1,1},{852,1,1},{856,1,1},{862,4,3},{867,1,1},{868,1,2},{870,1,2},{872,1,1},{879,1,1},{884,1,2},{889,1,2},{892,1,2},{894,1,1},{895,1,2},{897,1,2},{899,1,1},{902,1,1},{904,1,1},{912,1,2},{914,1,2},{916,1,2},{962,2,1},{966,1,1},{969,1,1},{972,1,1},{976,1,1},{982,1,1},{985,1,2},{987,1,1},{988,1,2},{992,1,1},{999,1,1},{1004,1,2},{1009,1,2},{1012,1,2},{1014,1,1},{1015,1,2},{1017,1,2},{1019,1,1},{1022,1,1},{1034,1,3},{1080,1,1},{1082,2,1},{1086,1,1},{1089,1,1},{1092,1,1},{1094,1,1},{1096,1,1},{1102,1,1},{1105,1,2},{1107,1,1},{1108,1,2},{1112,1,1},{1119,1,1},{1124,1,2},{1129,1,1},{1132,1,2},{1134,1,1},{1135,1,2},{1136,2,3},{1139,1,1},{1142,1,1},{1156,1,3},{1200,1,2},{1201,1,3},{1203,2,3},{1205,1,1},{1206,2,3},{1208,1,1},{1209,2,3},{1211,1,1},{1212,1,2},{1213,1,3},{1216,1,1},{1222,1,1},{1225,1,2},{1227,2,3},{1231,1,2},{1239,2,3},{1241,1,1},{1244,1,2},{1249,1,1},{1252,1,1},{1254,1,1},{1259,1,1},{1262,1,2},{1274,1,2},{1275,1,3},{1342,4,3},{1350,1,2},{1351,1,1},{1370,1,2},{1371,1,3},{1374,1,1},{1378,1,3},{1379,1,1},{1383,1,3},{1384,1,1},{1392,1,2},{1393,1,3},{1394,1,1}};
 static const UiRun odd[]={{30,1,2},{51,1,1},{57,1,2},{75,1,1},{142,1,2},{143,3,3},{146,1,1},{148,1,1},{150,1,2},{171,1,1},{177,1,1},{195,1,1},{241,1,3},{242,1,1},{243,1,2},{244,2,3},{246,1,2},{249,1,2},{250,2,3},{252,1,2},{253,2,3},{255,1,2},{256,2,3},{262,1,2},{266,1,1},{268,1,1},{270,1,2},{271,2,3},{279,1,2},{285,1,1},{288,1,2},{289,5,3},{296,1,2},{313,1,2},{315,2,3},{317,1,1},{360,1,2},{362,2,2},{366,1,2},{369,1,2},{372,1,2},{376,1,2},{382,1,2},{386,1,1},{387,1,2},{388,1,3},{389,2,1},{392,1,2},{399,1,2},{405,1,1},{410,1,2},{414,1,2},{415,5,3},{422,1,2},{423,2,3},{425,1,1},{433,1,2},{435,1,1},{480,1,2},{483,1,2},{486,1,2},{489,1,2},{492,1,2},{496,1,2},{502,1,2},{503,3,3},{506,1,1},{507,1,2},{509,2,1},{512,1,2},{519,1,2},{525,1,1},{530,1,2},{534,1,2},{539,2,2},{541,1,3},{542,1,1},{543,1,2},{551,1,2},{553,1,2},{555,1,1},{600,1,2},{603,1,2},{606,1,2},{609,1,2},{612,1,2},{616,1,2},{622,1,2},{626,1,1},{627,1,2},{629,1,1},{632,1,2},{639,1,2},{645,1,1},{650,1,2},{651,2,3},{653,1,1},{654,1,2},{659,1,2},{663,1,1},{665,1,1},{666,1,2},{667,5,3},{672,1,2},{673,5,3},{721,1,3},{722,1,1},{723,1,2},{724,1,3},{725,1,1},{726,1,2},{729,1,2},{730,1,3},{731,1,1},{732,1,2},{736,1,2},{742,1,2},{746,1,1},{747,1,2},{748,1,3},{749,1,1},{750,1,2},{752,1,2},{759,1,2},{763,4,3},{767,1,1},{770,1,2},{773,1,1},{774,1,2},{776,2,3},{778,1,1},{779,1,2},{782,1,2},{784,1,1},{785,1,2},{793,1,2},{795,1,1},{796,1,2},{842,2,2},{846,1,2},{849,1,2},{852,1,2},{856,1,2},{862,1,2},{863,3,3},{866,1,1},{867,1,2},{869,1,1},{871,1,1},{872,1,2},{879,1,2},{885,1,1},{890,1,1},{893,1,1},{894,1,2},{896,1,1},{898,1,1},{899,1,2},{902,1,2},{904,1,2},{913,1,1},{915,1,1},{917,1,1},{962,2,2},{966,1,2},{969,1,2},{972,1,2},{976,1,2},{982,1,2},{986,1,1},{987,1,2},{989,1,1},{992,1,2},{999,1,2},{1005,1,1},{1010,1,1},{1013,1,1},{1014,1,2},{1016,1,1},{1018,1,1},{1019,1,2},{1022,1,2},{1034,1,2},{1035,1,1},{1080,1,2},{1082,2,2},{1086,1,2},{1089,1,2},{1092,1,2},{1094,1,2},{1096,1,2},{1102,1,2},{1106,1,1},{1107,1,2},{1109,1,1},{1112,1,2},{1119,1,2},{1125,1,1},{1129,1,2},{1133,1,1},{1134,1,2},{1136,2,3},{1138,1,1},{1139,1,2},{1142,1,2},{1156,1,2},{1157,1,1},{1201,1,3},{1202,1,1},{1203,1,2},{1204,2,3},{1206,1,2},{1207,2,3},{1209,1,2},{1210,2,3},{1213,1,3},{1214,1,1},{1216,1,2},{1222,1,2},{1226,1,1},{1227,1,2},{1228,1,3},{1229,1,1},{1232,1,1},{1239,1,2},{1240,2,3},{1245,1,1},{1249,1,2},{1252,1,2},{1254,1,2},{1259,1,2},{1263,1,1},{1275,1,3},{1276,1,1},{1342,1,2},{1343,3,3},{1346,1,1},{1351,1,3},{1371,1,3},{1372,1,1},{1374,1,2},{1378,1,2},{1379,1,3},{1383,1,2},{1384,1,3},{1393,2,3}};
 static const UiText line={157,15,0,{even,odd},{224,246}};
 text_spans(&line,x,y,color);
}
int journal_nav_draw(void){unsigned i;
 if(journal_tab==JOURNAL_COLLECTION){collection_journal_draw();return 1;}
 if(journal_tab==JOURNAL_MAP&&journey_map_draw){journey_map_draw();return 1;}
 if(journal_tab>=JOURNAL_REGION_FIRST&&journal_tab<=JOURNAL_REGION_LAST&&!journal_nav_detail){const struct QuestList*list=&quest_lists[journal_tab-JOURNAL_REGION_FIRST];unsigned selection=*list->selection<list->count?*list->selection:0,first=selection>4?selection-4:0;
  box(8,31,224,123);centered(list->title,33,GOLD);
  for(i=first;i<list->count&&i<first+5;i++){int y=52+(int)(i-first)*16;if(i==selection)rect(13,y,214,16,PAL_STONE2);text(list->names[i],14,y,i==selection?GOLD:CREAM);}
  if(first)rect(224,49,3,2,GOLD);if(first+5<list->count)rect(224,132,3,2,GOLD);centered(TX_PF_QUEST_KEYS,137,TEAL);return 1;
 }
 if(journal_tab==JOURNAL_HUB){static const int labels[8]={TX_PF_ITEMS,TX_PF_GEAR,TX_PF_PARTY,TX_PF_GROWTH,TX_PF_MAP,TX_PF_QUESTS,TX_PF_CONTROLS,TX_PF_RESUME};box(8,31,224,123);centered(TX_PF_HUB,33,GOLD);
  for(i=0;i<9;i++){int x=17+(int)(i&1)*108,y=51+(int)(i>>1)*16;if((int)i==journal_nav_category)rect(x-3,y-1,102,16,PAL_STONE2);if(i<8)text(labels[i],x,y,(int)i==journal_nav_category?GOLD:CREAM);else growth_goals_text(GJ_COLLECTION,x,y,(int)i==journal_nav_category?GOLD:CREAM);}centered(TX_PF_HUB_KEYS,136,TEAL);return 1;
 }
 if(journal_tab==JOURNAL_QUESTS){static const int labels[9]={TX_PF_CURRENT_QUEST,TX_PF_REGION_0,TX_PF_REGION_1,TX_PF_REGION_2,TX_PF_REGION_3,TX_PF_REGION_4,TX_PF_REGION_5,TX_PF_REGION_6,TX_PF_REGION_7};unsigned count=quest_count(),first=journal_nav_quest>4?(unsigned)journal_nav_quest-4:0;box(8,31,224,123);centered(TX_PF_QUESTS,33,GOLD);
  for(i=first;i<count&&i<first+5;i++){int y=52+(int)(i-first)*16;if((int)i==journal_nav_quest)rect(18,y,204,16,PAL_STONE2);text(labels[i],28,y,(int)i==journal_nav_quest?GOLD:CREAM);}if(first)rect(213,49,4,2,GOLD);if(first+5<count)rect(213,132,4,2,GOLD);centered(TX_PF_QUEST_KEYS,137,TEAL);return 1;
 }
 if(journal_tab==JOURNAL_CONTROLS){static const int labels[5]={TX_PF_CONTROLS_0,TX_PF_CONTROLS_1,TX_PF_CONTROLS_2,TX_PF_CONTROLS_3,TX_PF_CONTROLS_4};box(8,31,224,123);centered(TX_PF_CONTROLS,33,GOLD);
  for(i=0;i<5;i++){int y=47+(int)i*13,retry=i==4&&save_failed;if(retry)rect(14,y-1,212,16,PAL_STONE2);text(retry?TX_PF_RETRY_SAVE:labels[i],18,y,retry?GOLD:CREAM);}field_step_control_line(18,112,CREAM);centered(TX_PF_BACK_CLOSE,138,TEAL);return 1;
 }return 0;
}
