#include "gear_menu.h"
#include "progression.h"
#include "assets.h"
#include "ui.h"
typedef unsigned char u8;
extern int journal_tab;
extern void rect(int,int,int,int,u8),box(int,int,int,int),text(int,int,int,int),centered(int,int,int);
extern void save_game(void),toast(int),sfx(int);
#define GOLD PAL_GOLD3
#define CREAM PAL_GOLD4
#define TEAL PAL_TEAL2
unsigned gear_menu_revision;
int gear_menu_slot,gear_menu_candidate;
static int notice;
static const u8 digits[10][5]={{7,5,5,5,7},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},{5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7},{7,1,1,1,1},{7,5,7,5,7},{7,5,7,1,7}};
static void number(unsigned n,int x,int y,int color){unsigned d=100;int started=0;for(;d;d/=10){unsigned digit=n/d%10;if(digit||started||d==1){int xx,yy;for(yy=0;yy<5;yy++)for(xx=0;xx<3;xx++)if(digits[digit][yy]&(4>>xx))rect(x+xx,y+yy,1,1,(u8)color);x+=4;started=1;}}}
static int name_id(unsigned item){switch(item){
 case 1:return TX_G_ITEM1;case 2:return TX_G_ITEM2;case 9:return TX_G_ITEM9;case 10:return TX_G_ITEM10;
 case 17:return TX_G_ITEM17;case 18:return TX_G_ITEM18;case 33:return TX_G_ITEM33;case 34:return TX_G_ITEM34;
 case 49:return TX_G_ITEM49;case 50:return TX_G_ITEM50;case 65:return TX_G_ITEM65;case 81:return TX_G_ITEM81;case 82:return TX_G_ITEM82;default:return TX_G_EMPTY;}}
static int description_id(unsigned item){switch(item){
 case 1:return TX_G_DESC1;case 2:return TX_G_DESC2;case 9:return TX_G_DESC9;case 10:return TX_G_DESC10;
 case 17:return TX_G_DESC17;case 18:return TX_G_DESC18;case 33:return TX_G_DESC33;case 34:return TX_G_DESC34;
 case 49:return TX_G_DESC49;case 50:return TX_G_DESC50;case 65:return TX_G_DESC65;case 81:return TX_G_DESC81;case 82:return TX_G_DESC82;default:return TX_G_EMPTY;}}
void gear_menu_reset(void){gear_menu_slot=0;gear_menu_candidate=adventure_save.equipment.equipped[0];notice=0;gear_menu_revision++;}
static void change_candidate(int delta){EquipmentState*e=&adventure_save.equipment;int i=gear_menu_candidate==255?48:gear_menu_candidate;unsigned n;
 for(n=0;n<49;n++){const EquipmentDefinition*d;i=(i+delta+49)%49;if(i==48){gear_menu_candidate=255;break;}d=equipment_definition(e->bag[i].item_id);if(d&&d->slot==gear_menu_slot){gear_menu_candidate=i;break;}}
 notice=0;gear_menu_revision++;
}
int gear_menu_input(int pressed){EquipmentU16 hp;EquipmentComparison cmp;unsigned result;int directions=pressed&240;if(journal_tab!=4)return 0;
 if(directions==64||directions==128){gear_menu_slot=(gear_menu_slot+(directions==128?1:4))%5;gear_menu_candidate=adventure_save.equipment.equipped[gear_menu_slot];notice=0;gear_menu_revision++;return 1;}
 if(directions==16||directions==32){change_candidate(directions==16?1:-1);return 1;}
 if(!(pressed&(256|4)))return 0;
 hp=(EquipmentU16)game_gear_hp();
 result=equipment_equip(&adventure_save.equipment,(unsigned)gear_menu_slot,(pressed&4)?255:(unsigned)gear_menu_candidate,game_gear_base_hp(),&hp,game_gear_busy(),&cmp);
 if(result==EQUIPMENT_OK){game_gear_apply(hp);gear_menu_candidate=adventure_save.equipment.equipped[gear_menu_slot];notice=0;save_game();sfx(2);}
 else notice=1;
 gear_menu_revision++;return 1;
}
static void heart_number(unsigned n,int x,int y,int color){number(n/16,x,y,color);if(n%16){rect(x+5,y+4,1,1,(u8)color);number((n%16)*10/16,x+7,y,color);}}
static void stat(unsigned before,unsigned after,int label,int x,int hearts){int col=after>before?GOLD:after<before?PAL_HEART:CREAM;text(label,x,98,CREAM);if(hearts)heart_number(before,x+15,104,CREAM);else number(before,x+15,104,CREAM);rect(x+28,105,5,1,TEAL);rect(x+31,104,1,3,TEAL);if(hearts)heart_number(after,x+35,104,col);else number(after,x+35,104,col);}
void gear_menu_draw(void){EquipmentState*e=&adventure_save.equipment;EquipmentComparison cmp;unsigned item=gear_menu_candidate<48?e->bag[gear_menu_candidate].item_id:0,i,result;const int labels[]={TX_G_TAB_WEAPON,TX_G_TAB_BODY,TX_G_TAB_BOOTS,TX_G_TAB_BELT,TX_G_TAB_RING};
 if(!item&&gear_menu_slot==EQUIPMENT_WEAPON)item=EQUIPMENT_STARTER_ID;
 box(8,31,224,123);centered(notice?TX_G_BUSY:TX_G_TITLE,33,GOLD);
 for(i=0;i<5;i++){int x=23+i*43;if((int)i==gear_menu_slot)rect(x-6,51,36,17,PAL_STONE2);text(labels[i],x,51,(int)i==gear_menu_slot?GOLD:CREAM);}
 centered(name_id(item),70,GOLD);centered(description_id(item),84,CREAM);
 result=equipment_preview(e,(unsigned)gear_menu_slot,(unsigned)gear_menu_candidate,game_gear_base_hp(),game_gear_hp(),0,&cmp);
 if(result==EQUIPMENT_OK){stat(equipment_weapons[cmp.before.weapon_class].moves[0].damage_q4+cmp.before.attack_q4,equipment_weapons[cmp.after.weapon_class].moves[0].damage_q4+cmp.after.attack_q4,TX_G_STAT_ATTACK,14,0);stat(cmp.before.defense_q4,cmp.after.defense_q4,TX_G_STAT_DEFENSE,68,0);stat(cmp.before.max_hp_q4,cmp.after.max_hp_q4,TX_G_STAT_HP,122,1);stat((cmp.before.speed_q8*100+160)/320,(cmp.after.speed_q8*100+160)/320,TX_G_STAT_SPEED,176,0);}
 centered(TX_G_CANDIDATES,112,TEAL);centered(TX_G_COMMIT,126,CREAM);centered(TX_G_NEXT_TAB,140,TEAL);
}
