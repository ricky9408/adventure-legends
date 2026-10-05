/* Emberbond: original GBA homebrew vertical slice, 2026. */
#include "assets.h"
#include "ui.h"
#include "asset_collisions.h"
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define REG16(a) (*(volatile u16*)(a))
#define REG32(a) (*(volatile u32*)(a))
#define KEY_A 1
#define KEY_B 2
#define KEY_SELECT 4
#define KEY_START 8
#define KEY_RIGHT 16
#define KEY_LEFT 32
#define KEY_UP 64
#define KEY_DOWN 128
#define KEY_R 256
#define KEY_L 512
#define TITLE 0
#define PLAY 1
#define DIALOG 2
#define PAUSE 3
#define DEAD 4
#define WIN 5
/* These UI palette slots are reconciled with the art manifest at build time. */
#define INK 1
#define CREAM PAL_GOLD4
#define GOLD PAL_GOLD3
#define GREEN PAL_PINE4
#define TEAL PAL_TEAL2
#define RED PAL_HEART
#define BLUE PAL_BLUE2
#define WHITE PAL_WHITE
#define UI_BG 1
#define UI_BORDER PAL_GOLD2
#define SRAM ((volatile u8*)0x0E000000)
__attribute__((used)) const char save_type[]="SRAM_V113";

typedef struct { int x,y,hp,flash,kind; } Enemy;
typedef struct { int x,y,dx,dy,life,owner; } Shot;
/* Stable named symbols intentionally retained for emulator QA inspection. */
volatile int game_state, room, px, py, hp, spirit, summoned, bridge_open, torches, boss_hp;
volatile int boss_armor, boss_x, boss_y, has_save, quest_started, ticks, deaths, kills;
int face, walk, invuln, swing, sword_cd, ability_cd, heal_cd, cx,cy, toast_id,toast_ticks;
volatile unsigned int render_cycles, worst_render_cycles;
int frame, page, keys, pressed, prev_keys, dpage,dcount,dafter,dialog_lines[12],music_tick,music_step;
int saved_room, seen_temple, seen_boss, boss_time, boss_flash, slash_id, completed;
typedef struct {int x,y,life;} Impact;
Impact impacts[6];
Enemy enemies[4]; Shot shots[12];
u16 *screen;
int ab(int n){return n<0?-n:n;} int sign(int n){return(n>0)-(n<0);} int near(int x,int y,int xx,int yy,int d){return ab(x-xx)+ab(y-yy)<d;}
void zero(void *p,int n){u8 *b=p;while(n--)*b++=0;}
void *memset(void *p,int v,unsigned int n){u8*b=p;while(n--)*b++=v;return p;}
void *memcpy(void *d,const void*s,unsigned int n){u8*a=d;const u8*b=s;while(n--)*a++=*b++;return d;}
void pix(int x,int y,u8 c){if((unsigned)x>=240||(unsigned)y>=160)return;u16 *p=screen+y*120+(x>>1);u16 v=*p;*p=(x&1)?((v&255)|(c<<8)):((v&0xFF00)|c);}
void rect(int x,int y,int w,int h,u8 c){int yy,xx;if(x<0){w+=x;x=0;}if(y<0){h+=y;y=0;}if(x+w>240)w=240-x;if(y+h>160)h=160-y;if(w<1||h<1)return;
 for(yy=y;yy<y+h;yy++){int left=x,right=x+w;if(left&1){pix(left++,yy,c);}if(right&1)pix(--right,yy,c);u16 *p=screen+yy*120+(left>>1);for(xx=left;xx<right;xx+=2)*p++=c|(c<<8);}}
void box(int x,int y,int w,int h){rect(x,y,w,h,UI_BG);rect(x,y,w,1,UI_BORDER);rect(x,y+h-1,w,1,UI_BORDER);rect(x,y,1,h,UI_BORDER);rect(x+w-1,y,1,h,UI_BORDER);}
void text(int id,int x,int y,int col){const UiText *t=&ui_texts[id];int yy,xx;u16 color=col|(col<<8);
 /* Text is laid out inside the screen. Draw aligned pairs without per-pixel
  * calls, clipping checks, or repeated row-address multiplication. */
 for(yy=0;yy<t->height;yy++){const u8 *row=t->data+yy*t->stride;u16 *dst=screen+(y+yy)*120+(x>>1);int source=0;
  if(x&1){if(row[0]&1)*dst=(*dst&255)|(col<<8);dst++;source=1;}
  for(xx=source;xx+1<t->width;xx+=2){int a=(row[xx>>3]>>(xx&7))&1;int b=(row[(xx+1)>>3]>>((xx+1)&7))&1;
   if(a&&b)*dst=color;else if(a)*dst=(*dst&0xFF00)|col;else if(b)*dst=(*dst&255)|(col<<8);dst++;}
  if(xx<t->width&&((row[xx>>3]>>(xx&7))&1))*dst=(*dst&0xFF00)|col;
 }
}
void centered(int id,int y,int col){text(id,(240-ui_texts[id].width)/2,y,col);}
void sprite(const u8 *data,int x,int y,int w,int h,int flash){int xx,yy;for(yy=0;yy<h;yy++)for(xx=0;xx<w;xx++){u8 v=data[yy*w+xx];if(v)pix(x+xx,y+yy,flash?WHITE:v);}}
void spr(int id,int x,int y){sprite(sprite_data[id],x-8,y-8,16,16,0);}
void line(int x,int y,int x2,int y2,int col){int dx=ab(x2-x),sx=sign(x2-x),dy=-ab(y2-y),sy=sign(y2-y),e=dx+dy,e2;while(1){pix(x,y,col);if(x==x2&&y==y2)break;e2=2*e;if(e2>=dy){e+=dy;x+=sx;}if(e2<=dx){e+=dx;y+=sy;}}}
void copy_bg(int id){REG32(0x040000D4)=(u32)backgrounds[id];REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;}
/* Hardware OBJ compositor: pixels live in cartridge tile memory once; OAM
 * controls per-frame motion. Bitmap modes reserve the first 512 OBJ tiles. */
typedef struct { u16 a0,a1,a2,pad; } ObjEntry;
ObjEntry obj_entries[128]; int obj_depth[128],obj_count;
u16 obj_tiles[512]; u8 slash_pixels[1024];
int gfx_hero_frame=-1,gfx_companion_frame=-1,gfx_slash_frame=-1;
int px_q8,py_q8,cx_q8,cy_q8,walk_phase,hitstop,transition;
int cached_armor[2]={-1,-1};
u32 cache_key[2]={0xFFFFFFFF,0xFFFFFFFF},cache_dialog[2]={0xFFFFFFFF,0xFFFFFFFF};
#define OBJ_HERO 6144
#define OBJ_COMPANION 6400
#define OBJ_SHADOW 6656
#define OBJ_BOSS_SHADOW 6912
#define OBJ_SLASH 7424
#define OBJ_CANOPY 8448
#define OBJ_HINT 10496
#define OBJ_SPARK 10560
#define OBJ_ARMOR 10624
void obj_upload(const u8 *data,int w,int h,int offset){int tx,ty,x,y,k=0;u16 *dst=(u16*)(0x06014000+offset);
 for(ty=0;ty<h;ty+=8)for(tx=0;tx<w;tx+=8)for(y=0;y<8;y++)for(x=0;x<8;x+=2){int p=(ty+y)*w+tx+x;obj_tiles[k++]=data[p]|(data[p+1]<<8);}
 REG32(0x040000D4)=(u32)obj_tiles;REG32(0x040000D8)=(u32)dst;REG32(0x040000DC)=0x84000000|(k/2);
}
void obj_init(void){int i;u8 shadow[512];for(i=0;i<256;i++)((volatile u16*)0x05000200)[i]=game_palette[i];
 for(i=0;i<SPR_COUNT;i++)obj_upload(sprite_data[i],16,16,i*256);
 obj_upload(boss_data,32,32,5120);
 for(i=0;i<256;i++){int x=i%16-8,y=i/16-11;shadow[i]=(x*x*2+y*y*9<81)?PAL_SHADOW:0;}
#ifdef EMBERBOND_POLISHED_ART
 obj_upload(hero_shadow,16,16,OBJ_SHADOW);obj_upload(boss_shadow,32,16,OBJ_BOSS_SHADOW);
#else
 obj_upload(shadow,16,16,OBJ_SHADOW);for(i=0;i<512;i++){int x=i%32-16,y=i/32-9;shadow[i]=(x*x+y*y*8<190)?PAL_SHADOW:0;}obj_upload(shadow,32,16,OBJ_BOSS_SHADOW);
#endif
 zero(shadow,64);for(i=0;i<64;i++){int x=i&7,y=i>>3;if((x==3||y==3)&&x>0&&x<7&&y>0&&y<7)shadow[i]=PAL_GOLD3;if(x==3&&y==3)shadow[i]=PAL_WHITE;}obj_upload(shadow,8,8,OBJ_SPARK);
 zero(shadow,64);{const u8 rows[8]={0,60,66,90,102,126,66,60};for(i=0;i<64;i++){int x=i&7,y=i>>3;if(rows[y]&(128>>x))shadow[i]=y==1||y==7?PAL_GOLD3:PAL_WHITE;}}obj_upload(shadow,8,8,OBJ_HINT);
 zero(shadow,64);for(i=0;i<64;i++){int x=(i&7)-3,y=(i>>3)-3;if(ab(x)+ab(y)<5)shadow[i]=(x+y<0)?PAL_MOSS3:PAL_PINE2;if(x==y&&x>-3&&x<3)shadow[i]=PAL_GOLD2;}obj_upload(shadow,8,8,OBJ_ARMOR);

}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip){int shape=0,size=0;ObjEntry o;
 if(obj_count>=120||x<=-w||x>=240||y<=-h||y>=160)return;
 /* Menus are background pixels: hide actors where a panel covers them. */
 if(priority==1||priority==2){if(game_state==PAUSE||game_state==DEAD)return;if(game_state==DIALOG&&y+h>99)return;}
 if(w==16&&h==16)size=1;else if(w==32&&h==32)size=2;else if(w==32&&h==16){shape=1;size=2;}
 o.a0=(y&255)|0x2000|(shape<<14);o.a1=(x&511)|(size<<14)|(flip?0x1000:0);o.a2=(512+off/32)|(priority<<10);o.pad=0;
 obj_entries[obj_count]=o;obj_depth[obj_count]=depth;obj_count++;
}
void obj_sprite(int id,int x,int y,int depth){obj_add(id*256,x-8,y-8,16,16,1,depth,0);}
void obj_commit(void){int i,j;for(i=1;i<obj_count;i++){ObjEntry o=obj_entries[i];int d=obj_depth[i];j=i;while(j&&obj_depth[j-1]<d){obj_entries[j]=obj_entries[j-1];obj_depth[j]=obj_depth[j-1];j--;}obj_entries[j]=o;obj_depth[j]=d;}
 for(i=obj_count;i<128;i++)obj_entries[i]=(ObjEntry){0x0200,0,0,0};
 REG32(0x040000D4)=(u32)obj_entries;REG32(0x040000D8)=0x07000000;REG32(0x040000DC)=0x84000000|256;
}
void sword_art(int phase){int x,y;zero(slash_pixels,sizeof slash_pixels);
 /* A changing crescent: high-contrast edge, warm inner trail, no solid box. */
 for(y=0;y<32;y++)for(x=0;x<32;x++){int dx=x-16,dy=y-16,d=dx*dx+dy*dy;int fx=face==2?-dx:face==3?dx:face==1?-dy:dy;int side=face<2?dx:dy;
 if(d>115&&d<231&&fx>1&&side<phase*5-4&&side>phase*5-19)slash_pixels[y*32+x]=d>192?PAL_WHITE:PAL_GOLD3;
 if(d>80&&d<=115&&fx>5&&side<phase*5-3&&side>phase*5-14)slash_pixels[y*32+x]=PAL_FIRE1;
 }
 obj_upload(slash_pixels,32,32,OBJ_SLASH);
}
void draw_actors(void){int i,anim=swing?1:walk?(walk_phase/6)&3:0,code=face*4+anim;const u8 *hero;obj_count=0;
 if(game_state==TITLE)return;
 if(game_state==WIN){obj_sprite(SPR_HERO_DOWN_0,101,106,106);obj_sprite(SPR_FOX_0,121,108,108);obj_sprite(SPR_LEAF_0,141,108,108);return;}
 for(i=0;i<6;i++)obj_add((i<hp?SPR_HEART_FULL:SPR_HEART_EMPTY)*256,3+i*11,3,16,16,0,9999,0);
#ifdef EMBERBOND_POLISHED_ART
 hero=hero_frames[face][anim];
#else
 hero=sprite_data[SPR_HERO_DOWN_0+face*2+(anim&1)];
#endif
 if(code!=gfx_hero_frame){obj_upload(hero,16,16,OBJ_HERO);gfx_hero_frame=code;}
 if(room==0){obj_sprite(SPR_ELDER,120,92,92);if(game_state==PLAY&&near(px,py,120,94,29))obj_add(OBJ_HINT,116,75,8,8,1,999,0);}
 if(room==2){if(torches&1)obj_sprite(SPR_FLAME_0+(frame/7&1),64,57,70);if(torches&2)obj_sprite(SPR_FLAME_0+(frame/7&1),176,57,70);}
 for(i=0;i<4;i++)if(enemies[i].hp){Enemy *e=&enemies[i];obj_add(OBJ_SHADOW,e->x-8,e->y-6,16,16,2,e->y-1,0);if(!e->flash||(frame&2))obj_sprite(SPR_SLIME_0+(frame/10&1),e->x,e->y,e->y);}
 if(room==3){obj_add(OBJ_BOSS_SHADOW,boss_x-16,boss_y+1,32,16,2,boss_y,0);if(!boss_flash||(frame&2))obj_add(5120,boss_x-16,boss_y-20,32,32,1,boss_y,0);if(!boss_armor){for(i=0;i<4;i++)obj_add(OBJ_ARMOR,boss_x+(i&1?17:-17)-4,boss_y+(i&2?9:-9)-4,8,8,1,boss_y+1,0);}}
 if(summoned){int d=ab(px-cx)>ab(py-cy)?(px<cx?2:3):(py<cy?1:0);int ca=(frame/7)&3;code=spirit*16+d*4+ca;
  if(code!=gfx_companion_frame){
#ifdef EMBERBOND_POLISHED_ART
   obj_upload(companion_direction_frames[spirit][d][ca],16,16,OBJ_COMPANION);
#else
   obj_upload(sprite_data[(spirit?SPR_LEAF_0:SPR_FOX_0)+(ca&1)],16,16,OBJ_COMPANION);
#endif
   gfx_companion_frame=code;
  }
  obj_add(OBJ_SHADOW,cx-8,cy-6,16,16,2,cy-1,0);obj_add(OBJ_COMPANION,cx-8,cy-9-(spirit?((frame/10)&1):0),16,16,1,cy,0);
 }
 obj_add(OBJ_SHADOW,px-8,py-6,16,16,2,py-1,0);if(!invuln||(frame&4))obj_add(OBJ_HERO,px-8,py-11,16,16,1,py,0);
 if(swing){int phase=(13-swing)/2;code=face*8+phase;if(code!=gfx_slash_frame){sword_art(phase);gfx_slash_frame=code;}obj_add(OBJ_SLASH,px-16,py-17,32,32,1,py+1,0);}
 for(i=0;i<12;i++)if(shots[i].life)obj_sprite(shots[i].owner?SPR_PROJECTILE:SPR_FLAME_0,shots[i].x,shots[i].y,shots[i].y+2);
 for(i=0;i<6;i++)if(impacts[i].life){int j,r=(20-impacts[i].life)/2+3;for(j=0;j<4;j++)obj_add(OBJ_SPARK,impacts[i].x+(j==0?-r:j==1?r:0)-4,impacts[i].y+(j==2?-r:j==3?r:0)-4,8,8,1,impacts[i].y+2,0);}
 if(summoned&&ability_cd>60&&spirit){int r=(75-ability_cd)*2;for(i=0;i<4;i++)obj_sprite(SPR_LEAF_0,px+(i==0?-r:i==1?r:0),py+(i==2?-r:i==3?r:0),py+1);}
#ifdef EMBERBOND_POLISHED_ART
 {int n=0;for(i=0;i<FOREGROUND_CANOPY_COUNT;i++)if(game_state==PLAY&&foreground_canopies[i].room==room){/* Two fixed masks per room; upload only after room changes below. */
  obj_add(OBJ_CANOPY+n*1024,foreground_canopies[i].x,foreground_canopies[i].y,32,32,0,foreground_canopies[i].y+32,0);n++;}}
#endif
}

/* Original 16-note ambient phrase, square wave 2. Sound effects use channel 1. */
void sound_init(void){REG16(0x04000084)=0x80;REG16(0x04000080)=0x3377;REG16(0x04000082)=2;}
void sfx(int id){REG16(0x04000060)=id==1?0x21:0;REG16(0x04000062)=id==3?0xA180:0x8180;REG16(0x04000064)=0x8000|(id==1?1850:id==2?1700:id==3?1200:1950);}
void music(void){static const u16 notes[]={1547,1750,1840,1750,1602,1750,1820,1750,1673,1800,1874,1800,1602,1700,1750,1602};if(++music_tick>=24){music_tick=0;REG16(0x04000068)=0x2080;REG16(0x0400006C)=0x8000|notes[music_step++&15];}}
void toast(int id){toast_id=id;toast_ticks=110;}
void dialogue(int a,int b,int next){dialog_lines[0]=a;dialog_lines[1]=b;dpage=0;dcount=1;dafter=next;game_state=DIALOG;}
void addpage(int a,int b){dialog_lines[dcount*2]=a;dialog_lines[dcount*2+1]=b;dcount++;}
void save_game(void){u8 vals[8];int i,sum=0;vals[0]=0x45;vals[1]=0x42;vals[2]=2;vals[3]=room;vals[4]=bridge_open;vals[5]=torches;vals[6]=completed;vals[7]=quest_started;for(i=0;i<8;i++){SRAM[i]=vals[i];sum+=vals[i];}SRAM[8]=(u8)sum;has_save=1;saved_room=room;}
int check_save(void){int i,sum=0;for(i=0;i<8;i++)sum+=SRAM[i];return SRAM[0]==0x45&&SRAM[1]==0x42&&SRAM[2]==2&&SRAM[3]<4&&SRAM[4]<2&&SRAM[5]<4&&SRAM[6]<2&&SRAM[7]<2&&((u8)sum)==SRAM[8];}
void spawn_enemies(void){zero(enemies,sizeof enemies);zero(shots,sizeof shots);zero(impacts,sizeof impacts);if(room==1){enemies[0]=(Enemy){77,120,2,0,0};enemies[1]=(Enemy){174,118,2,0,0};enemies[2]=(Enemy){167,65,2,0,0};}if(room==2){enemies[0]=(Enemy){55,113,2,0,1};enemies[1]=(Enemy){184,110,2,0,1};}}
void enter_room(int r,int fromnorth){room=r;px=120;py=fromnorth?40:139;cx=px+14;cy=py+3;invuln=75;boss_time=0;spawn_enemies();if(r==0){py=122;hp=6;}if(r==3){boss_x=120;boss_y=65;boss_hp=12;boss_armor=0;boss_flash=0;}px_q8=px*256;py_q8=py*256;cx_q8=cx*256;cy_q8=cy*256;transition=10;
#ifdef EMBERBOND_POLISHED_ART
 {int i,n=0;for(i=0;i<FOREGROUND_CANOPY_COUNT;i++)if(foreground_canopies[i].room==r)obj_upload(foreground_canopy_data[i],32,32,OBJ_CANOPY+(n++)*1024);}
#endif
 save_game();if(r==2&&!seen_temple){seen_temple=1;dialogue(TX_TEMPLE1,TX_TEMPLE2,PLAY);}if(r==3&&!seen_boss){seen_boss=1;dialogue(TX_BOSS1,TX_BOSS2,PLAY);}}
void start_game(int resume){int oldsave=has_save;zero(enemies,sizeof enemies);zero(shots,sizeof shots);zero(impacts,sizeof impacts);frame=0;room=0;px=120;py=126;hp=6;spirit=0;summoned=0;bridge_open=0;torches=0;boss_hp=12;quest_started=0;completed=0;face=0;walk=0;invuln=0;swing=0;sword_cd=0;ability_cd=0;heal_cd=0;toast_ticks=0;seen_temple=0;seen_boss=0;deaths=0;kills=0;ticks=0;cx=136;cy=126;px_q8=px*256;py_q8=py*256;cx_q8=cx*256;cy_q8=cy*256;walk_phase=0;hitstop=0;transition=0;game_state=PLAY;
#ifdef EMBERBOND_POLISHED_ART
 {int i,n=0;for(i=0;i<FOREGROUND_CANOPY_COUNT;i++)if(foreground_canopies[i].room==0)obj_upload(foreground_canopy_data[i],32,32,OBJ_CANOPY+(n++)*1024);}
#endif

 if(resume&&oldsave){int r=SRAM[3];bridge_open=SRAM[4];torches=SRAM[5];completed=SRAM[6];quest_started=SRAM[7];seen_temple=r>=2;seen_boss=r==3;enter_room(r,0);if(completed)game_state=WIN;else toast(TX_SAVED);}
 else {quest_started=1;dialogue(TX_INTRO1A,TX_INTRO1B,PLAY);addpage(TX_INTRO2A,TX_INTRO2B);addpage(TX_INTRO3A,TX_INTRO3B);addpage(TX_INTRO4A,TX_INTRO4B);save_game();}}
int solid(int x,int y){
 int i;
 if(x<12||x>227||y<28||y>152)return 1;
 for(i=0;i<asset_solids_count[room];i++) {const AssetRect *r=&asset_solids[room][i];if(x>=r->x&&x<r->x+r->w&&y>=r->y&&y<r->y+r->h)return 1;}
 if(room==1&&y>75&&y<94&&(!bridge_open||x<106||x>134))return 1;
 if(room==2){if(y<44&&x>88&&x<152&&torches!=3)return 1;if((ab(x-64)<13||ab(x-176)<13)&&ab(y-64)<10)return 1;}
 if(room==3&&y<39)return 1;
 return 0;
}
void move_player(int dx,int dy){int nx=px_q8+dx,ny=py_q8+dy;if(!solid(nx>>8,py))px_q8=nx;if(!solid(px,ny>>8))py_q8=ny;px=px_q8>>8;py=py_q8>>8;}
void damage(void){if(invuln||game_state!=PLAY)return;hp--;invuln=80;sfx(3);if(hp<=0){game_state=DEAD;deaths++;summoned=0;zero(shots,sizeof shots);}}
void fire_shot(int x,int y,int dx,int dy,int owner){int i;for(i=0;i<12;i++)if(!shots[i].life){shots[i]=(Shot){x,y,dx,dy,90,owner};break;}}
void ability(void){int i;if(!summoned){toast(TX_NEEDSUMMON);return;}if(ability_cd){toast(TX_COOLDOWN);return;}ability_cd=75;sfx(2);
 if(spirit==1){if(room==1&&!bridge_open&&near(px,py,120,95,55)){bridge_open=1;save_game();dialogue(TX_BRIDGE1,TX_BRIDGE2,PLAY);return;}if(!heal_cd&&hp<6){hp++;heal_cd=360;toast(TX_HEALED);}for(i=0;i<4;i++)if(enemies[i].hp&&near(px,py,enemies[i].x,enemies[i].y,47)){enemies[i].flash=35;enemies[i].x+=sign(enemies[i].x-px)*6;enemies[i].y+=sign(enemies[i].y-py)*6;}return;}
 if(room==2){int before=torches;if(near(px,py,64,64,42))torches|=1;if(near(px,py,176,64,42))torches|=2;if(before!=torches){save_game();if(torches==3)dialogue(TX_GATE1,TX_GATE2,PLAY);return;}}
 if(room==3&&near(px,py,boss_x,boss_y,84)){boss_armor=210;boss_flash=12;toast(TX_EXPOSED);fire_shot(cx,cy,sign(boss_x-cx)*2,sign(boss_y-cy)*2,0);return;}
 fire_shot(px,py,face==2?-2:face==3?2:0,face==1?-2:face==0?2:0,0);}
void sword(void){if(sword_cd)return;if(room==0&&near(px,py,120,94,29)){hp=6;save_game();dialogue(TX_VILLAGETALK1,TX_VILLAGETALK2,PLAY);return;}swing=13;sword_cd=20;slash_id++;move_player(face==2?-384:face==3?384:0,face==1?-384:face==0?384:0);sfx(1);}
int sword_hits(int x,int y,int radius){int dx=x-px,dy=y-py;if(ab(dx)+ab(dy)>radius)return 0;if(face==0&&dy>=-6)return 1;if(face==1&&dy<=6)return 1;if(face==2&&dx<=6)return 1;if(face==3&&dx>=-6)return 1;return 0;}
void impact(int x,int y){int i;for(i=0;i<6;i++)if(!impacts[i].life){impacts[i]=(Impact){x,y,20};return;}impacts[0]=(Impact){x,y,20};}
void kill_enemy(Enemy*e){impact(e->x,e->y);e->hp=0;kills++;if(hp<6&&kills%3==0)hp++;}
void update_enemies(void){int i,j;for(i=0;i<4;i++){Enemy*e=&enemies[i];if(!e->hp)continue;if(e->flash)e->flash--;if(swing==11&&!e->flash&&sword_hits(e->x,e->y,29)){e->hp-=2;e->flash=16;hitstop=3;sfx(4);if(e->hp<=0)kill_enemy(e);}if(!e->hp)continue;if(!e->flash&&frame%3==0&&near(px,py,e->x,e->y,70)){int dx=sign(px-e->x),dy=sign(py-e->y);if((frame+i)&1){if(!solid(e->x+dx,e->y))e->x+=dx;}else if(!solid(e->x,e->y+dy))e->y+=dy;}
 if(ab(px-e->x)<11&&ab(py-e->y)<11)damage();
 for(j=0;j<12;j++)if(shots[j].life&&!shots[j].owner&&near(e->x,e->y,shots[j].x,shots[j].y,14)){shots[j].life=0;kill_enemy(e);break;}}
}
void update_boss(void){int i;boss_time++;if(boss_armor)boss_armor--;if(boss_flash)boss_flash--;if(swing==11&&boss_armor&&!boss_flash&&sword_hits(boss_x,boss_y,38)){boss_hp--;boss_flash=18;hitstop=3;impact(boss_x,boss_y);sfx(4);if(boss_hp<=0){completed=1;save_game();dialogue(TX_WIN1,TX_WIN2,WIN);addpage(TX_WIN3,TX_WIN4);zero(shots,sizeof shots);return;}}
 if(!boss_armor){if(boss_time%120==0){for(i=0;i<8;i++){static const int vx[]={2,2,0,-2,-2,-2,0,2};static const int vy[]={0,2,2,2,0,-2,-2,-2};fire_shot(boss_x,boss_y,vx[i],vy[i],1);}}if(boss_time%240>175&&boss_time%3==0){boss_x+=sign(px-boss_x);boss_y+=sign(py-boss_y);}}else if(boss_time%10==0){boss_x+=sign(120-boss_x);boss_y+=sign(65-boss_y);}
 if(boss_x<30)boss_x=30;
 if(boss_x>210)boss_x=210;
 if(boss_y<48)boss_y=48;
 if(boss_y>130)boss_y=130;
 if(ab(px-boss_x)<20&&ab(py-boss_y)<20)damage();}
void update_shots(void){int i;for(i=0;i<12;i++){Shot*s=&shots[i];if(!s->life)continue;s->life--;s->x+=s->dx;s->y+=s->dy;if(s->x<8||s->x>232||s->y<26||s->y>151){s->life=0;continue;}if(s->owner&&near(px,py,s->x,s->y,11)){damage();s->life=0;}if(!s->owner&&room==3&&near(s->x,s->y,boss_x,boss_y,25)){boss_armor=210;boss_flash=10;s->life=0;}
 if(!s->owner&&room==2){int old=torches;if(near(s->x,s->y,64,64,14)){torches|=1;s->life=0;}if(near(s->x,s->y,176,64,14)){torches|=2;s->life=0;}if(torches!=old){save_game();if(torches==3)dialogue(TX_GATE1,TX_GATE2,PLAY);}}}}
void update(void){int dx=0,dy=0;frame++;music();if(transition)transition--;if(toast_ticks)toast_ticks--;if(game_state==TITLE){if(pressed&KEY_START)start_game(has_save);else if(pressed&KEY_SELECT)start_game(0);return;}
 if(game_state==DIALOG){if(pressed&KEY_A){sfx(4);if(++dpage>=dcount)game_state=dafter;}return;}
 if(game_state==PAUSE){if(pressed&(KEY_START|KEY_SELECT|KEY_B))game_state=PLAY;return;}
 if(game_state==DEAD){if(pressed&KEY_A){hp=6;ability_cd=0;heal_cd=0;game_state=PLAY;enter_room(room,0);}return;}
 if(game_state==WIN){if(pressed&KEY_START){game_state=TITLE;has_save=check_save();}return;}
 ticks++;{int i;for(i=0;i<6;i++)if(impacts[i].life)impacts[i].life--;}if(hitstop){hitstop--;return;}if(pressed&(KEY_START|KEY_SELECT)){game_state=PAUSE;return;}if(invuln)invuln--;if(swing)swing--;if(sword_cd)sword_cd--;if(ability_cd)ability_cd--;if(heal_cd)heal_cd--;
 if(pressed&KEY_B){summoned=!summoned;cx=px+14;cy=py;cx_q8=cx*256;cy_q8=cy*256;sfx(2);if(summoned)toast(TX_SUMMONED);}if(pressed&KEY_L){spirit=1-spirit;sfx(2);}
 if(keys&KEY_LEFT){dx=-1;face=2;}if(keys&KEY_RIGHT){dx=1;face=3;}if(keys&KEY_UP){dy=-1;face=1;}if(keys&KEY_DOWN){dy=1;face=0;}walk=dx||dy;if(walk)walk_phase++;move_player(dx*(dx&&dy?226:320),dy*(dx&&dy?226:320));
 if(pressed&KEY_A)sword();
 if(pressed&KEY_R)ability();
 if(game_state!=PLAY)return;
 if(summoned){int tx=(px+(face==2?17:-17))*256,ty=(py+8)*256;cx_q8+=(tx-cx_q8)/6;cy_q8+=(ty-cy_q8)/6;cx=cx_q8>>8;cy=cy_q8>>8;}

 update_shots();update_enemies();if(room==3)update_boss();if(game_state!=PLAY)return;
 if(py<=31&&px>100&&px<140){if(room<3)enter_room(room+1,0);}else if(py>=149&&px>100&&px<140&&room>0&&room<3)enter_room(room-1,1);
}
void draw_sword(void){int d=face,phase=13-swing,ox=d==2?-15:d==3?15:0,oy=d==1?-15:d==0?15:0;int x=px+ox,y=py+oy;line(px,py-2,x,y,WHITE);if(d<2){line(x-12+phase,y-3,x+8,y+2,GOLD);line(x-11+phase,y-2,x+8,y+3,CREAM);}else{line(x-3,y-12+phase,x+2,y+8,GOLD);line(x-2,y-11+phase,x+3,y+8,CREAM);} }
void draw_hud(void){rect(0,0,240,24,INK);rect(0,23,240,1,GOLD);text(TX_VILLAGE+room,104,4,CREAM);spr(spirit?SPR_LEAF_0:SPR_FOX_0,83,11);if(summoned){rect(74,20,18,1,GOLD);}if(ability_cd)rect(74,21,(75-ability_cd)*18/75,1,TEAL);else rect(74,21,18,1,TEAL);}
void draw_world(void){int i;copy_bg(room);if(room==1&&bridge_open){rect(106,75,28,20,PAL_PINE3);for(i=0;i<5;i++){rect(107,75+i*4,26,3,PAL_WOOD3);rect(110,75+i*4,20,1,GOLD);}line(106,72,106,97,GREEN);line(134,72,134,97,GREEN);}
 if(room==2){if(torches!=3){rect(99,27,42,13,INK);for(i=101;i<141;i+=6)rect(i,27,2,15,GOLD);}else{rect(108,25,24,9,INK);line(108,33,132,33,GOLD);}}
 draw_hud();
 if(toast_ticks&&game_state==PLAY){const UiText*t=&ui_texts[toast_id];box((240-t->width-10)/2,143,t->width+10,17);centered(toast_id,143,CREAM);}else if(game_state==PLAY)rect(0,153,240,7,INK);
}
/* 5x7 letterforms for an exact-pixel wordmark. */
const u8 alphabet[26][7]={{14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{14,17,16,16,16,17,14},{30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},{14,17,16,23,17,17,15},{17,17,17,31,17,17,17},{31,4,4,4,4,4,31},{7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},{17,27,21,21,17,17,17},{17,25,25,21,19,19,17},{14,17,17,17,17,17,14},{30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},{15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},{17,17,17,17,17,10,4},{17,17,17,21,21,27,17},{17,17,10,4,10,17,17},{17,17,10,4,4,4,4},{31,1,2,4,8,16,31}};
void wordmark(void){const char*s="EMBERBOND";int i,x,y;for(i=0;i<9;i++)for(y=0;y<7;y++)for(x=0;x<5;x++)if(alphabet[s[i]-'A'][y]&(16>>x)){rect(43+i*18+x*3,35+y*3+2,3,3,INK);rect(42+i*18+x*3,35+y*3,3,3,y<3?CREAM:GOLD);}}
int quest_id(void){if(room==0)return TX_QUEST0;if(room==1)return bridge_open?TX_QUEST2:TX_QUEST1;if(room==2)return torches==3?TX_QUEST4:TX_QUEST3;return TX_QUEST5;}
void render_static(void){screen=(u16*)(page?0x0600A000:0x06000000);if(game_state==TITLE){copy_bg(BACK_TITLE);wordmark();centered(TX_SUBTITLE,60,CREAM);centered(TX_TAGLINE,84,CREAM);box(43,112,154,36);centered(has_save?TX_CONTINUE:TX_START,114,GOLD);if(has_save)centered(TX_NEW,130,CREAM);else centered(TX_BUILD,132,CREAM);return;}
 draw_world();if(game_state==DIALOG){box(5,99,230,56);text(room==0?TX_ELDER:room==3?TX_BOSS:TX_SUBTITLE,13,103,GOLD);text(dialog_lines[dpage*2],13,120,CREAM);text(dialog_lines[dpage*2+1],13,136,CREAM);text(TX_NEXT,207,102,GOLD);}
 if(game_state==PAUSE){box(8,31,224,119);centered(TX_PAUSE,35,GOLD);text(quest_id(),16,54,CREAM);text(TX_CONTROL1,16,73,CREAM);text(TX_CONTROL2,16,89,CREAM);text(TX_CONTROL3,16,105,CREAM);centered(spirit?TX_CONTROL4:TX_CONTROL5,127,TEAL);}
 if(game_state==DEAD){box(22,60,196,57);centered(TX_DEAD,69,GOLD);centered(TX_RETRY,94,CREAM);}
 if(game_state==WIN){copy_bg(BACK_TITLE);box(17,40,206,103);centered(TX_COMPLETE,49,GOLD);centered(TX_THANKS,75,CREAM);centered(TX_RESTART,122,CREAM);centered(TX_ENDINGSMALL,149,GOLD);}}
void render(void){u32 key=(u32)room|((u32)game_state<<2)|((u32)spirit<<8)|((u32)summoned<<9)|((u32)bridge_open<<10)|((u32)torches<<11)|((u32)dpage<<13)|((u32)(game_state==PLAY&&toast_ticks>0)<<16)|((u32)(game_state==PLAY?toast_id:0)<<17)|((u32)has_save<<25);u32 dk=game_state==DIALOG?(u32)dialog_lines[dpage*2]|((u32)dialog_lines[dpage*2+1]<<8):0;
 screen=(u16*)(page?0x0600A000:0x06000000);if(cache_key[page]!=key||cache_dialog[page]!=dk){render_static();cached_armor[page]=-1;cache_key[page]=key;cache_dialog[page]=dk;}
 if(game_state==PLAY){rect(74,20,18,2,INK);rect(74,21,ability_cd?(75-ability_cd)*18/75:18,1,TEAL);if(room==3){if(cached_armor[page]!=(boss_armor>0)){rect(0,24,240,16,INK);text(boss_armor?TX_EXPOSED:TX_ARMORED,8,25,CREAM);cached_armor[page]=boss_armor>0;}rect(57,140,126,5,INK);rect(59,141,boss_hp*10,3,boss_armor?GOLD:GREEN);}}
 draw_actors();
}
unsigned int cycle_now(void){u16 hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return ((u32)hi<<16)|lo;}
int main(void){int i;REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;for(i=0;i<256;i++)((volatile u16*)0x05000000)[i]=game_palette[i];REG16(0x04000020)=256;REG16(0x04000026)=256;REG16(0x04000022)=0;REG16(0x04000024)=0;REG32(0x04000028)=0;REG32(0x0400002C)=0;page=0;has_save=check_save();game_state=TITLE;sound_init();obj_init();REG16(0x0400000C)=3;REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;while(1){u32 started=cycle_now();keys=(~REG16(0x04000130))&1023;pressed=keys&~prev_keys;prev_keys=keys;update();render();render_cycles=cycle_now()-started;if(render_cycles>worst_render_cycles)worst_render_cycles=render_cycles;while(REG16(0x04000006)>=160){}while(REG16(0x04000006)<160){}obj_commit();REG16(0x04000050)=0x00FF;REG16(0x04000054)=transition;REG16(0x04000000)=0x1444|(page?0x10:0);page^=1;}return 0;}
