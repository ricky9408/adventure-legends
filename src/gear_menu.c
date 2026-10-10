#include "gear_menu.h"
#include "gear_runtime.h"
#include "gear_preview.h"
#include "gear_preview_text.h"
#include "economy.h"
#include "progression.h"
#include "assets.h"
#include "ui.h"
typedef unsigned char u8;
#if defined(__arm__)
#define MENU_HOT __attribute__((section(".iwram.text.gear_menu"),long_call,noinline))
#define MENU_COLD __attribute__((section(".text.rom"),long_call,noinline))
#else
#define MENU_HOT
#define MENU_COLD
#endif
extern int journal_tab;
extern void rect(int,int,int,int,u8),box(int,int,int,int),text(int,int,int,int),centered(int,int,int);
extern void save_game(void),toast(int),sfx(int);
#define GOLD PAL_GOLD3
#define CREAM PAL_GOLD4
#define TEAL PAL_TEAL2
unsigned gear_menu_revision;
int gear_menu_slot,gear_menu_candidate;
static int notice;
/* Display only. Every A commit still validates the live equipment separately.
 * Full byte equality catches ownership/history changes outside this menu. */
typedef unsigned GearCacheWord __attribute__((__may_alias__));
static struct {
 EquipmentState equipment;
 EquipmentComparison comparison;
 unsigned valid,result,slot,candidate,base_hp,current_hp,relics,upgrade;
} preview_cache;
typedef char GearCacheAligned[(__builtin_offsetof(Save5State,equipment)%4==0&&sizeof(EquipmentState)%4==0)?1:-1];
static int preview_equipment_same(void){unsigned i;const GearCacheWord*a=(const GearCacheWord*)&adventure_save.equipment,*b=(const GearCacheWord*)&preview_cache.equipment;
 for(i=0;i<sizeof(EquipmentState)/sizeof(GearCacheWord);i++)if(a[i]!=b[i])return 0;
 return 1;
}
static void preview_copy(void*destination,const void*source,unsigned length){u8*d=(u8*)destination;const u8*s=(const u8*)source;while(length--)*d++=*s++;}
static void preview_remember(unsigned base,unsigned current){unsigned i;const GearCacheWord*source=(const GearCacheWord*)&adventure_save.equipment;GearCacheWord*dest=(GearCacheWord*)&preview_cache.equipment;
 for(i=0;i<sizeof(EquipmentState)/sizeof(GearCacheWord);i++)dest[i]=source[i];
 preview_cache.slot=(unsigned)gear_menu_slot;preview_cache.candidate=(unsigned)gear_menu_candidate;
 preview_cache.base_hp=base;preview_cache.current_hp=current;preview_cache.relics=adventure_save.economy.relics;preview_cache.upgrade=adventure_save.economy.upgrade;preview_cache.valid=1;
}
static MENU_COLD unsigned preview_display(EquipmentComparison*out){unsigned base=game_gear_base_hp(),current=game_gear_hp();
 if(!preview_cache.valid||preview_cache.slot!=(unsigned)gear_menu_slot||preview_cache.candidate!=(unsigned)gear_menu_candidate||preview_cache.base_hp!=base||preview_cache.current_hp!=current||preview_cache.relics!=adventure_save.economy.relics||preview_cache.upgrade!=adventure_save.economy.upgrade||!preview_equipment_same()){
  preview_cache.result=equipment_preview(&adventure_save.equipment,(unsigned)gear_menu_slot,(unsigned)gear_menu_candidate,base,current,0,&preview_cache.comparison);preview_remember(base,current);
 }
 if(preview_cache.result==EQUIPMENT_OK){preview_copy(out,&preview_cache.comparison,sizeof *out);game_gear_bonus_stats(&out->before);game_gear_bonus_stats(&out->after);}return preview_cache.result;
}
static void preview_committed(const EquipmentComparison*fresh){
 preview_copy(&preview_cache.comparison,fresh,sizeof *fresh);preview_copy(&preview_cache.comparison.before,&fresh->after,sizeof fresh->after);
 preview_cache.comparison.hp_before_q4=preview_cache.comparison.hp_after_q4=(EquipmentU16)game_gear_hp();
 preview_cache.comparison.old_ref=preview_cache.comparison.new_ref;
 preview_cache.result=EQUIPMENT_OK;preview_remember(game_gear_base_hp(),game_gear_hp());
}
extern unsigned short *screen;
/* Four-pixel, seven-row glyphs deliberately separate1 from7 and6 from5.
 * Entry10 is an explicit unknown-value marker for out-of-cell synthetic data. */
#define GEAR_DIGIT_ROWS(M) \
 {M(6),M(9),M(9),M(9),M(9),M(9),M(6)}, \
 {M(2),M(6),M(2),M(2),M(2),M(2),M(7)}, \
 {M(6),M(9),M(1),M(2),M(4),M(8),M(15)}, \
 {M(14),M(1),M(1),M(6),M(1),M(1),M(14)}, \
 {M(2),M(6),M(10),M(10),M(15),M(2),M(2)}, \
 {M(15),M(8),M(8),M(14),M(1),M(1),M(14)}, \
 {M(6),M(8),M(8),M(14),M(9),M(9),M(6)}, \
 {M(15),M(1),M(1),M(2),M(2),M(4),M(4)}, \
 {M(6),M(9),M(9),M(6),M(9),M(9),M(6)}, \
 {M(6),M(9),M(9),M(7),M(1),M(1),M(6)}, \
 {M(6),M(9),M(1),M(2),M(2),M(0),M(2)}
#define GEAR_BITS(n) (n)
#define GEAR_PAIR(a,b) (((a)?255u:0u)|((b)?65280u:0u))
#define GEAR_EVEN(n) {GEAR_PAIR((n)&8,(n)&4),GEAR_PAIR((n)&2,(n)&1)}
#define GEAR_ODD(n) {GEAR_PAIR(0,(n)&8),GEAR_PAIR((n)&4,(n)&2),GEAR_PAIR((n)&1,0)}
static const u8 digits[11][7]={GEAR_DIGIT_ROWS(GEAR_BITS)};
/* The same authored glyphs precompiled for both halfword alignments. Keep
 * bit decoding/branches out of every digit row; zero masks preserve pixels. */
static const unsigned short digit_even_masks[11][7][2]={GEAR_DIGIT_ROWS(GEAR_EVEN)};
static const unsigned short digit_odd_masks[11][7][3]={GEAR_DIGIT_ROWS(GEAR_ODD)};
#undef GEAR_ODD
#undef GEAR_EVEN
#undef GEAR_PAIR
#undef GEAR_BITS
#undef GEAR_DIGIT_ROWS
static MENU_HOT void digit_blit(unsigned digit,int x,int y,u8 color){
 unsigned row;unsigned short ink=(unsigned short)(color|((unsigned)color<<8)),*p;const unsigned short*m;
 if((unsigned)x>236||(unsigned)y>153){int xx,yy;for(yy=0;yy<7;yy++)for(xx=0;xx<4;xx++)if(digits[digit][yy]&(8>>xx))rect(x+xx,y+yy,1,1,color);return;}
 p=screen+y*120+(x>>1);
 if(x&1){m=&digit_odd_masks[digit][0][0];for(row=0;row<7;row++){unsigned short a=*m++,b=*m++,c=*m++;p[0]=(unsigned short)((p[0]&~a)|(ink&a));p[1]=(unsigned short)((p[1]&~b)|(ink&b));p[2]=(unsigned short)((p[2]&~c)|(ink&c));p+=120;}}
 else{m=&digit_even_masks[digit][0][0];for(row=0;row<7;row++){unsigned short a=*m++,b=*m++;p[0]=(unsigned short)((p[0]&~a)|(ink&a));p[1]=(unsigned short)((p[1]&~b)|(ink&b));p+=120;}}
}

/* All displayed stat values are <=999. Decimal extraction deliberately avoids
 * Thumb software division on the cold menu draw path. */
static MENU_HOT void number(unsigned n,int x,int y,int color){
 unsigned values[3]={0,0,0},i;int started=0;
 if(n>999){digit_blit(10,x,y,(u8)color);return;}
 while(n>=100){n-=100;values[0]++;}
 while(n>=10){n-=10;values[1]++;}
 values[2]=n;
 for(i=0;i<3;i++){unsigned digit=values[i];if(digit||started||i==2){
  digit_blit(digit,x,y,(u8)color);
  x+=5;started=1;
 }}
}

static int name_id(unsigned item){switch(item){
 case 1:return TX_G_ITEM1;case 2:return TX_G_ITEM2;case 9:return TX_G_ITEM9;case 10:return TX_G_ITEM10;
 case 17:return TX_G_ITEM17;case 18:return TX_G_ITEM18;case 33:return TX_G_ITEM33;case 34:return TX_G_ITEM34;
 case 49:return TX_G_ITEM49;case 50:return TX_G_ITEM50;case 65:return TX_G_ITEM65;case 81:return TX_G_ITEM81;case 82:return TX_G_ITEM82;case 3:return TX_G_ITEM3;case 11:return TX_G_ITEM11;case 19:return TX_G_ITEM19;case 35:return TX_G_ITEM35;case 51:return TX_G_ITEM51;case 83:return TX_G_ITEM83;case 4:return TX_G_ITEM4;case 12:return TX_G_ITEM12;case 36:return TX_G_ITEM36;case 52:return TX_G_ITEM52;case 66:return TX_G_ITEM66;case 84:return TX_G_ITEM84;case 20:return TX_G_ITEM20;case 37:return TX_G_ITEM37;case 53:return TX_G_ITEM53;case 67:return TX_G_ITEM67;case 85:return TX_G_ITEM85;case 5:return TX_G_ITEM5;case 6:return TX_G_ITEM6;case 13:return TX_G_ITEM13;case 38:return TX_G_ITEM38;case 54:return TX_G_ITEM54;case 68:return TX_G_ITEM68;case 86:return TX_G_ITEM86;case 7:return TX_HZ_GEAR7;case 14:return TX_HZ_GEAR14;case 56:return TX_HZ_GEAR56;case 88:return TX_HZ_GEAR88;case 21:return TX_PF_G_ITEM21;case 39:return TX_PF_G_ITEM39;case 55:return TX_PF_G_ITEM55;case 69:return TX_PF_G_ITEM69;case 87:return TX_PF_G_ITEM87;case 40:return TX_PF_G_ITEM40;case 89:return TX_PF_G_ITEM89;default:return TX_G_EMPTY;}}
void gear_menu_reset(void){gear_menu_slot=0;gear_menu_candidate=adventure_save.equipment.equipped[0];notice=0;preview_cache.valid=0;gear_menu_revision++;}
static void change_candidate(int delta){EquipmentState*e=&adventure_save.equipment;int i=gear_menu_candidate==255?48:gear_menu_candidate;unsigned n;
 for(n=0;n<49;n++){const EquipmentDefinition*d;i=(i+delta+49)%49;if(i==48){gear_menu_candidate=255;break;}d=equipment_definition(e->bag[i].item_id);if(d&&d->slot==gear_menu_slot){gear_menu_candidate=i;break;}}
 notice=0;gear_menu_revision++;
}
int gear_menu_input(int pressed){EquipmentU16 hp;EquipmentComparison cmp;unsigned result;int directions=pressed&240;if(journal_tab!=4)return 0;
 if(pressed&(2|8))return 0;
 if(directions==16||directions==32){gear_menu_slot=(gear_menu_slot+(directions==16?1:4))%5;gear_menu_candidate=adventure_save.equipment.equipped[gear_menu_slot];notice=0;gear_menu_revision++;return 1;}
 if(directions==64||directions==128){change_candidate(directions==128?1:-1);return 1;}
 if(directions)return 1;
 if(!(pressed&1))return 0;
 hp=(EquipmentU16)game_gear_hp();
 result=equipment_equip(&adventure_save.equipment,(unsigned)gear_menu_slot,(unsigned)gear_menu_candidate,game_gear_base_hp(),&hp,game_gear_busy(),&cmp);
 if(result==EQUIPMENT_OK){game_gear_apply_stats(hp,&cmp.after);gear_menu_candidate=adventure_save.equipment.equipped[gear_menu_slot];preview_committed(&cmp);notice=0;save_game();sfx(2);}
 else notice=1;
 gear_menu_revision++;return 1;
}
static unsigned number_width(unsigned n){return n>999?4u:n>=100?14u:n>=10?9u:4u;}
/* Exact Q4 decimals. Every reachable equipment capacity is a quarter heart.
 * 11.25/12.25 are22px. Wider synthetic sixteenths use an explicit ? in cells,
 * never rounding or truncating real values to fit. */
static unsigned heart_width(unsigned n){unsigned width=number_width(n/16),r=n%16;if(r){width+=3;do{width+=5;r=(r*10)%16;}while(r);}return width;}
static void decimal_dot(int x,int y,int color){rect(x,y+5,2,2,(u8)color);}
static void heart_number(unsigned n,int x,int y,int color){unsigned r=n%16,w=number_width(n/16);number(n/16,x,y,color);if(r){decimal_dot(x+(int)w+1,y,color);x+=(int)w+4;do{r*=10;digit_blit(r/16,x,y,(u8)color);x+=5;r%=16;}while(r);}}
/* floor(n/10), exact for0..65535. Actual fixed values are0..1100. */
static unsigned decimal_tens(unsigned n){return (n*52429u)>>19;}
static unsigned fixed_width(unsigned n,unsigned places){unsigned unit=places==1?10u:100u;return (n>=100u*unit?14u:n>=10u*unit?9u:4u)+3u+places*5u;}
static void fixed_number(unsigned n,unsigned places,int x,int y,int color){
 unsigned tens=decimal_tens(n),ones=n-tens*10u;
 unsigned integral=places==1?tens:decimal_tens(tens),w=number_width(integral);
 number(integral,x,y,color);decimal_dot(x+(int)w+1,y,color);x+=(int)w+4;
 if(places==2){digit_blit(tens-integral*10u,x,y,(u8)color);x+=5;}
 digit_blit(ones,x,y,(u8)color);
}
extern void text_spans(const UiText*,int,int,int);
static void label(unsigned id,int x,int y,int color){text_spans(&gear_preview_texts[id],x,y,color);}
static void label_center(unsigned id,int y,int color){label(id,(240-gear_preview_texts[id].width)/2,y,color);}
static unsigned value_width(unsigned n,unsigned format){return format==1?heart_width(n):format>=2?fixed_width(n,format-1):number_width(n);}
static MENU_HOT void value_number(unsigned n,unsigned format,int x,int y,int color){if(format==1)heart_number(n,x,y,color);else if(format>=2)fixed_number(n,format-1,x,y,color);else number(n,x,y,color);}
static int cell_supported(unsigned n,unsigned format,unsigned limit){static const unsigned maxima[4]={999u,15999u,9999u,65535u};return format<=3u&&n<=maxima[format]&&value_width(n,format)<=limit;}
static unsigned cell_width(unsigned n,unsigned format,unsigned limit){return cell_supported(n,format,limit)?value_width(n,format):4u;}
static void cell_number(unsigned n,unsigned format,int x,int y,int color,unsigned limit){if(!cell_supported(n,format,limit))digit_blit(10,x,y,CREAM);else value_number(n,format,x,y,color);}
/* Seven-pixel shaft and a five-row head, centered on the7px numerals. */
static void arrow(int x,int y){rect(x,y+3,7,1,TEAL);rect(x+5,y+2,1,3,TEAL);rect(x+4,y+1,1,5,TEAL);}
/* Labels sit above each54px pair.22px + gap1 + arrow7 + gap1 +22px fits. */
static MENU_COLD void stat(unsigned before,unsigned after,int id,int x,unsigned format){
 int color=after>before?GOLD:after<before?PAL_HEART:CREAM;
 label((unsigned)id,x+(54-gear_preview_texts[id].width)/2,80,CREAM);
 cell_number(before,format,x+23-(int)cell_width(before,format,22),93,CREAM,22);arrow(x+24,93);cell_number(after,format,x+32,93,color,22);
}
/* Three72px columns leave31px per value, comfortably wider than seconds. */
static void detail_stat(unsigned before,unsigned after,unsigned id,int x,unsigned format,int lower,int missing){
 int color=after==before?CREAM:((after>before)!=lower?GOLD:PAL_HEART);
 label(id,x+(72-gear_preview_texts[id].width)/2,102,CREAM);arrow(x+33,115);
 if(missing){rect(x+26,118,6,2,CREAM);rect(x+41,118,6,2,CREAM);return;}
 cell_number(before,format,x+32-(int)cell_width(before,format,31),115,CREAM,31);cell_number(after,format,x+41,115,color,31);
}
static unsigned context_label(const EquipmentComparison*c,const GearPreview*before,const GearPreview*after,unsigned command){
 unsigned equal;
 if(!command)return GP_NO_COMMAND;
 /* Compare final values, never nominal item descriptions. Include class:
  * numerically similar sword/bow openings still behave differently. */
 equal=before->attack==after->attack&&before->defense==after->defense&&before->hearts==after->hearts&&before->walk_tenths==after->walk_tenths&&before->recovery_updates==after->recovery_updates&&before->distance==after->distance&&before->stagger==after->stagger&&before->weapon_class==after->weapon_class&&c->before.phase==c->after.phase;
 if(equal)return GP_SAME;
 /* Weapon browsing always explains which attack the distance describes. */
 if(gear_menu_slot==EQUIPMENT_WEAPON)return after->weapon_class==EQUIPMENT_BOW?GP_BOW:after->weapon_class==EQUIPMENT_LANCE?GP_LANCE:GP_SWORD;
 if(before->recovery_updates==after->recovery_updates&&
    (unsigned)EQUIPMENT_BASE_POWER_COOLDOWN-c->after.power_cooldown>=8u+economy_power_reduction(&adventure_save))return GP_RECOVERY_CAP;
 if(before->stagger==3&&after->stagger==3)return GP_STAGGER_CAP;
 return after->weapon_class==EQUIPMENT_BOW?GP_BOW:after->weapon_class==EQUIPMENT_LANCE?GP_LANCE:GP_SWORD;
}
MENU_COLD void gear_menu_draw(void){
 EquipmentState*e=&adventure_save.equipment;EquipmentComparison cmp;GearPreview before,after;
 unsigned item=gear_menu_candidate<48?e->bag[gear_menu_candidate].item_id:0,i,result,command=progression_command();
 const int labels[]={TX_G_TAB_WEAPON,TX_G_TAB_BODY,TX_G_TAB_BOOTS,TX_G_TAB_BELT,TX_G_TAB_RING};
 if(!item&&gear_menu_slot==EQUIPMENT_WEAPON)item=EQUIPMENT_STARTER_ID;
 box(8,31,224,123);
 if(notice)centered(TX_G_BUSY,33,GOLD);
 else{label(GP_TITLE,14,33,GOLD);label(gear_menu_candidate==e->equipped[gear_menu_slot]?GP_EQUIPPED:GP_PREVIEW,185,33,TEAL);}
 label(GP_LEFT,12,49,TEAL);label(GP_RIGHT,216,49,TEAL);
 for(i=0;i<5;i++){int x=30+i*38;if((int)i==gear_menu_slot)rect(x-3,49,33,15,PAL_STONE2);text(labels[i],x,49,(int)i==gear_menu_slot?GOLD:CREAM);}
 label(GP_UP,12,65,TEAL);label(GP_DOWN,216,65,TEAL);
 centered(gear_menu_candidate==EQUIPMENT_EMPTY_REF?(gear_menu_slot==EQUIPMENT_WEAPON?TX_PF_STARTER:TX_PF_UNEQUIP):name_id(item),65,GOLD);
 result=preview_display(&cmp);
 if(result==EQUIPMENT_OK){
  gear_preview_project(&cmp.before,command,&before);gear_preview_project(&cmp.after,command,&after);
  stat(before.attack,after.attack,GP_ATTACK,12,0);stat(before.defense,after.defense,GP_DEFENSE,66,0);
  stat(before.hearts,after.hearts,GP_HEART,120,1);stat(before.walk_tenths,after.walk_tenths,GP_WALK,174,2);
  detail_stat(before.recovery_hundredths,after.recovery_hundredths,GP_RECOVERY,12,3,1,!command);
  detail_stat(before.distance,after.distance,GP_DISTANCE,84,0,0,0);detail_stat(before.stagger,after.stagger,GP_STAGGER,156,0,0,0);
  label_center(context_label(&cmp,&before,&after,command),124,TEAL);
 }
 label_center(GP_FOOTER,138,TEAL);
}
