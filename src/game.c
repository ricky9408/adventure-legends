/* Emberbond: original GBA homebrew vertical slice, 2026. */
#include "assets.h"
#include "ui.h"
#include "asset_collisions.h"
#include "world.h"
#include "campaign_art.h"
#include "campaign_rules.h"
#include "save4.h"
#include "progression.h"
#include "evolution_art.h"
#include "advanced_powers.h"
#include "trials.h"
#include "quickparty.h"
#include "gear_runtime.h"
#include "regional_powers.h"
#include "region_game.h"
#include "north_art.h"
#include "north_game.h"
#include "south_art.h"
#include "south_game.h"
#include "southern_quests.h"
#include "northern_quests.h"
#include "northern_creature_art.h"
#include "southern_creature_art.h"
#include "northern_powers.h"
#include "southern_powers.h"
#include "magma_game.h"
#include "magma_art.h"
#include "magma_quests.h"
#include "magma_creature_art.h"
#include "magma_powers.h"
#include "region_art.h"
#include "regional_quests.h"
#include "obj_layout.h"
#include "gear_menu.h"
#include "combat_rules.h"
#include "regional_creature_art.h"
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
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
#define SAVE_PENDING 6
#define EVOLVE_CONFIRM 7
#define EVOLVE_ANIM 8
#define NEW_GAME_CONFIRM 9
#define SAVE_NOTICE_Y 8
#define SAVE_NOTICE_H 19
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
int face, walk, invuln, swing, sword_cd, ability_cd, ability_max, heal_cd, cx,cy, toast_id,toast_ticks;
volatile unsigned int render_cycles, worst_render_cycles;
int frame, page, keys, pressed, prev_keys, dpage,dcount,dafter,dialog_lines[12],music_tick,music_step;
int restoring_checkpoint;
/* Freeze gameplay and paint the notice before copying the save snapshot. The
 * requesting action can itself validate a large roster; charging both costs
 * to that cold-overlay frame would miss a hardware presentation deadline. */
int save_begin_pending;
int saved_room, seen_temple, seen_boss, boss_time, boss_flash, slash_id, completed;
typedef struct {int x,y,life;} Impact;
Impact impacts[6];
#define MAX_ENEMIES 6
Enemy enemies[MAX_ENEMIES]; Shot shots[12];
unsigned char ordinary_hostile_shots[12];
volatile int camera_x,camera_y,max_hp,relic_found,camp_unlocked,roll_ticks,roll_cd,combo_step,loaded_save_version;
int camera_fx,camera_fy;
int enemy_clocks[MAX_ENEMIES],enemy_windups[MAX_ENEMIES],enemy_aimx[MAX_ENEMIES],enemy_aimy[MAX_ENEMIES];
int roll_dx,roll_dy,combo_timer,swing_damage,attack_buffer,journal_tab;
volatile unsigned int chapter_flags,room_flags,optional_flags,story_seen;
volatile int boss_state,boss_phase,boss_state_ticks,boss_hp_max,stone_guard,guard_invuln,transition_lock,save_failed,checkpoint_spawn;
int boss_aimx,boss_aimy,boss_dx,boss_dy,boss_pattern,hazard_mode,power_effect;
int dialogue_action,dialogue_seen,dialog_speakers[6];
/* Acknowledgement does not turn a failed write into a successful one. */
int save_failure_notice;
int save_notice_visible(void){return save_failure_notice&&game_state!=PLAY&&game_state!=TITLE&&game_state!=SAVE_PENDING;}
int save_notice_left(void){return (240-ui_texts[TX_C_SAVE_FAILED].width-10)/2;}

int gfx_props_room=-1;u32 gfx_props_progress=0xFFFFFFFF;
COLD void enter_room(int,int);
COLD void save_game(void);
COLD void game_geometry_sync(void);
COLD void show_scene(int,int,unsigned);
COLD void append_scene(int);
void toast(int);
void impact(int,int);
int fire_shot(int,int,int,int,int);
int solid(int,int);
int quest_id(void);
unsigned progress_bits(void){return room_flags|(chapter_flags<<16);}
int boss_active(void){return (room==3&&!(chapter_flags&SAVE4_GROVE_CLEAR))||(room==8&&!(chapter_flags&SAVE4_SKY_CLEAR))||(room==13&&!(chapter_flags&SAVE4_CORE_CLEAR));}
const u8 *companion_form_pixels(unsigned form,unsigned d,unsigned f){const u8*p;unsigned legacy;if(d>=4||f>=4)return 0;p=magma_creature_art_frame(form,d,f);if(p)return p;p=southern_creature_art_frame(form,d,f);if(p)return p;p=northern_creature_art_frame(form,d,f);if(p)return p;p=regional_creature_art_frame(form,d,f);if(p)return p;p=evolution_art_frame(form,d,f);if(p)return p;legacy=creatures_legacy_spirit(form);if(legacy>=4)return 0;return legacy<2?companion_direction_frames[legacy][d][f]:campaign_companion_direction_frames[legacy-2][d][f];}
const u8 *companion_pixels(int c,int d,int f){return (unsigned)c<PROGRESSION_SPIRIT_COUNT?companion_form_pixels(progression_forms[c],(unsigned)d,(unsigned)f):0;}
int scrolling_room(void){return room==1||room==16||room==17||room==22||room==23||room==30||room==31||room==38||room==39;}
int world_width(void){return scrolling_room()?480:240;}
int world_height(void){return scrolling_room()?320:160;}
COLD int room_name(void){if(((unsigned)(room-38)<8u))return magma_game_name();if(south_game_is_room((unsigned)room))return south_game_name();if(north_game_is_room((unsigned)room))return north_game_name();if(region_game_is_room((unsigned)room))return region_game_name();if(room==14)return TX_T_ROOM_WIND;if(room==15)return TX_T_ROOM_STONE;return room<4?TX_VILLAGE+room:campaign_rooms[room-4].name;}


u16 *screen;
int ab(int n){return n<0?-n:n;} int sign(int n){return(n>0)-(n<0);} int near(int x,int y,int xx,int yy,int d){return ab(x-xx)+ab(y-yy)<d;}
void zero(void *p,int n){u8 *b=p;while(n--)*b++=0;}
void *memset(void *p,int v,unsigned int n){u8*b=p;while(n--)*b++=v;return p;}
void *memcpy(void *d,const void*s,unsigned int n){u8*a=d;const u8*b=s;while(n--)*a++=*b++;return d;}
void pix(int x,int y,u8 c){if((unsigned)x>=240||(unsigned)y>=160)return;u16 *p=screen+y*120+(x>>1);u16 v=*p;*p=(x&1)?((v&255)|(c<<8)):((v&0xFF00)|c);}
void rect(int x,int y,int w,int h,u8 c){int yy,xx;u32 fill=(u32)c*0x01010101u;if(x<0){w+=x;x=0;}if(y<0){h+=y;y=0;}if(x+w>240)w=240-x;if(y+h>160)h=160-y;if(w<1||h<1)return;
 for(yy=y;yy<y+h;yy++){int left=x,right=x+w;if(left&1)pix(left++,yy,c);if(right&1)pix(--right,yy,c);u16 *p=screen+yy*120+(left>>1);
  /* Host pixel tests use the same CPU fill without accessing DMA registers. */
#ifndef GAME_HOST_TEST
  if(right-left>=32){if(left&2){*p++=(u16)fill;left+=2;}if((right-left)&2){screen[yy*120+(right>>1)-1]=(u16)fill;right-=2;}REG32(0x040000D4)=(u32)&fill;REG32(0x040000D8)=(u32)p;REG32(0x040000DC)=0x85000000|((right-left)>>2);}
  else
#endif
  for(xx=left;xx<right;xx+=2)*p++=(u16)fill;
 }}
void box(int x,int y,int w,int h){rect(x,y,w,h,UI_BG);rect(x,y,w,1,UI_BORDER);rect(x,y+h-1,w,1,UI_BORDER);rect(x,y,1,h,UI_BORDER);rect(x+w-1,y,1,h,UI_BORDER);}
void text(int id,int x,int y,int col){const UiText *t=&ui_texts[id];const UiRun*r=t->runs[x&1];int n=t->count[x&1];u16 *base=screen+y*120+(x>>1),color=col|(col<<8);
 while(n--){u16 *dst=base+r->offset;int count=r->count;u16 mask=r->mask;r++;
  if(mask==3)while(count--)*dst++=color;
  else if(mask==1)while(count--){*dst=(*dst&0xFF00)|col;dst++;}
  else while(count--){*dst=(*dst&255)|(col<<8);dst++;}
 }
}
void centered(int id,int y,int col){text(id,(240-ui_texts[id].width)/2,y,col);}
void sprite(const u8 *data,int x,int y,int w,int h,int flash){int xx,yy;
 if(x<0||y<0||x+w>240||y+h>160){for(yy=0;yy<h;yy++)for(xx=0;xx<w;xx++){u8 v=data[yy*w+xx];if(v)pix(x+xx,y+yy,flash?WHITE:v);}return;}
 for(yy=0;yy<h;yy++){const u8*src=data+yy*w;u16*dst=screen+(y+yy)*120+(x>>1);xx=0;
  if(x&1){u8 a=src[xx++];if(a)*dst=(*dst&255)|((flash?WHITE:a)<<8);dst++;}
  for(;xx+1<w;xx+=2){u8 a=src[xx],b=src[xx+1];if(flash){if(a)a=WHITE;if(b)b=WHITE;}if(a&&b)*dst=a|(b<<8);else if(a)*dst=(*dst&0xFF00)|a;else if(b)*dst=(*dst&255)|(b<<8);dst++;}
  if(xx<w&&src[xx])*dst=(*dst&0xFF00)|(flash?WHITE:src[xx]);
 }
}
void spr(int id,int x,int y){sprite(sprite_data[id],x-8,y-8,16,16,0);}
void line(int x,int y,int x2,int y2,int col){int dx=ab(x2-x),sx=sign(x2-x),dy=-ab(y2-y),sy=sign(y2-y),e=dx+dy,e2;while(1){pix(x,y,col);if(x==x2&&y==y2)break;e2=2*e;if(e2>=dy){e+=dy;x+=sx;}if(e2<=dx){e+=dx;y+=sy;}}}
void copy_bg(int id){REG32(0x040000D4)=(u32)backgrounds[id];REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;}
/* Hardware OBJ compositor: pixels live in cartridge tile memory once; OAM
 * controls per-frame motion. Bitmap modes reserve the first 512 OBJ tiles. */
typedef struct { u16 a0,a1,a2,pad; } ObjEntry;
ObjEntry obj_entries[128]; int obj_depth[128],obj_count;
u16 obj_tiles[512]; u8 slash_pixels[1024];
u16 sword_tile_frames[4][7][512];

int gfx_hero_frame=-1,gfx_companion_frame=-1,gfx_slash_frame=-1;
int px_q8,py_q8,cx_q8,cy_q8,walk_phase,hitstop,transition;
int cached_armor[2]={-1,-1};
int gfx_hud_code=-1,gfx_hud_bar=-1,gfx_ending_revision=-1,area_ticks;
/* Exact cache fields avoid packed-key collisions as rooms/text/catalog grow. */
#define CACHE_FIELDS 30
int cache_valid[2];u32 cache_fields[2][CACHE_FIELDS];
#define OBJ_HERO 6144
#define OBJ_COMPANION 6400
#define OBJ_SHADOW 6656
#define OBJ_BOSS_SHADOW 6912
#define OBJ_SLASH 7424
#define OBJ_CANOPY 8448
#define OBJ_HINT 10496
#define OBJ_SPARK 10560
#define OBJ_ARMOR 10624
#define OBJ_WORLD 10816
#define OBJ_PROP 12352
#define OBJ_WARN 13888
#define OBJ_HAZARD 14144
#define OBJ_HUD_COMPANION 14400
#define OBJ_HUD_ACTION 14656
#define OBJ_HUD_COOLDOWN 14720
void obj_upload(const u8 *data,int w,int h,int offset){int tx,ty,x,y,k=0;u16 *dst=(u16*)(0x06014000+offset);
 for(ty=0;ty<h;ty+=8)for(tx=0;tx<w;tx+=8)for(y=0;y<8;y++)for(x=0;x<8;x+=2){int p=(ty+y)*w+tx+x;obj_tiles[k++]=data[p]|(data[p+1]<<8);}
 REG32(0x040000D4)=(u32)obj_tiles;REG32(0x040000D8)=(u32)dst;REG32(0x040000DC)=0x84000000|(k/2);
}
COLD void init_sword_tiles(void);
COLD void obj_init(void){int i;u8 shadow[512];for(i=0;i<256;i++)((volatile u16*)0x05000200)[i]=game_palette[i];
 for(i=0;i<SPR_COUNT;i++)obj_upload(sprite_data[i],16,16,i*256);
 obj_upload(boss_data,32,32,5120);
 for(i=0;i<6;i++)obj_upload(world_sprites[i],16,16,OBJ_WORLD+i*256);
 for(i=0;i<256;i++){int x=i%16-8,y=i/16-11;shadow[i]=(x*x*2+y*y*9<81)?PAL_SHADOW:0;}
#ifdef EMBERBOND_POLISHED_ART
 obj_upload(hero_shadow,16,16,OBJ_SHADOW);obj_upload(boss_shadow,32,16,OBJ_BOSS_SHADOW);
#else
 obj_upload(shadow,16,16,OBJ_SHADOW);for(i=0;i<512;i++){int x=i%32-16,y=i/32-9;shadow[i]=(x*x+y*y*8<190)?PAL_SHADOW:0;}obj_upload(shadow,32,16,OBJ_BOSS_SHADOW);
#endif
 zero(shadow,64);for(i=0;i<64;i++){int x=i&7,y=i>>3;if((x==3||y==3)&&x>0&&x<7&&y>0&&y<7)shadow[i]=PAL_GOLD3;if(x==3&&y==3)shadow[i]=PAL_WHITE;}obj_upload(shadow,8,8,OBJ_SPARK);
 zero(shadow,64);{const u8 rows[8]={0,60,66,90,102,126,66,60};for(i=0;i<64;i++){int x=i&7,y=i>>3;if(rows[y]&(128>>x))shadow[i]=y==1||y==7?PAL_GOLD3:PAL_WHITE;}}obj_upload(shadow,8,8,OBJ_HINT);
 zero(shadow,64);for(i=0;i<64;i++){int x=(i&7)-3,y=(i>>3)-3;if(ab(x)+ab(y)<5)shadow[i]=(x+y<0)?PAL_MOSS3:PAL_PINE2;if(x==y&&x>-3&&x<3)shadow[i]=PAL_GOLD2;}obj_upload(shadow,8,8,OBJ_ARMOR);
 {int j;u8 band[256];for(j=0;j<256;j++){int x=j&31,y=j>>5;band[j]=((x+y)&7)<2?PAL_GOLD3:0;}obj_upload(band,32,8,OBJ_WARN);for(j=0;j<256;j++){int x=j&31,y=j>>5;band[j]=(y==0||y==7)?PAL_WHITE:((x+y)&3)?PAL_FIRE2:PAL_FIRE0;}obj_upload(band,32,8,OBJ_HAZARD);}
 init_sword_tiles();

}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip){int shape=0,size=0;ObjEntry o;
 if(scrolling_room()&&(priority==1||priority==2)){x-=camera_x;y-=camera_y;}

 if(obj_count>=120||x<=-w||x>=240||y<=-h||y>=160)return;
 /* Even corner HUD OBJ must not obscure the exceptional modal notice. */
 if(save_notice_visible()){int left=save_notice_left();if(x+w>left&&x<240-left&&y+h>SAVE_NOTICE_Y&&y<SAVE_NOTICE_Y+SAVE_NOTICE_H)return;}
 /* Menus are background pixels: hide actors where a panel covers them. */
 if(priority==1||priority==2){if(quickparty_open&&x+w>26&&x<214&&y+h>29&&y<160)return;if(game_state==PAUSE||game_state==DEAD||game_state==EVOLVE_CONFIRM||game_state==EVOLVE_ANIM)return;if(game_state==DIALOG&&y+h>99)return;if(game_state==SAVE_PENDING&&x+w>37&&x<203&&y+h>77&&y<111)return;}
 if(w==16&&h==16)size=1;else if(w==32&&h==32)size=2;else if(w==32&&h==16){shape=1;size=2;}else if(w==32&&h==8){shape=1;size=1;}else if(w==16&&h==8){shape=1;size=0;}
 o.a0=(y&255)|0x2000|(shape<<14);o.a1=(x&511)|(size<<14)|(flip?0x1000:0);o.a2=(512+off/32)|(priority<<10);o.pad=0;
 obj_entries[obj_count]=o;obj_depth[obj_count]=depth;obj_count++;
}
void obj_sprite(int id,int x,int y,int depth){obj_add(id*256,x-8,y-8,16,16,1,depth,0);}
void obj_commit(void){int i,j;for(i=1;i<obj_count;i++){ObjEntry o=obj_entries[i];int d=obj_depth[i];j=i;while(j&&obj_depth[j-1]<d){obj_entries[j]=obj_entries[j-1];obj_depth[j]=obj_depth[j-1];j--;}obj_entries[j]=o;obj_depth[j]=d;}
 for(i=obj_count;i<128;i++)obj_entries[i]=(ObjEntry){0x0200,0,0,0};
 REG32(0x040000D4)=(u32)obj_entries;REG32(0x040000D8)=0x07000000;REG32(0x040000DC)=0x84000000|256;
}
COLD void init_sword_tiles(void){int dir,phase,x,y,tx,ty,k;for(dir=0;dir<4;dir++)for(phase=0;phase<7;phase++){zero(slash_pixels,sizeof slash_pixels);
 for(y=0;y<32;y++)for(x=0;x<32;x++){int dx=x-16,dy=y-16,d=dx*dx+dy*dy;int fx=dir==2?-dx:dir==3?dx:dir==1?-dy:dy;int side=dir<2?dx:dy;if(d>115&&d<231&&fx>1&&side<phase*5-4&&side>phase*5-19)slash_pixels[y*32+x]=d>192?PAL_WHITE:PAL_GOLD3;if(d>80&&d<=115&&fx>5&&side<phase*5-3&&side>phase*5-14)slash_pixels[y*32+x]=PAL_FIRE1;}
 k=0;for(ty=0;ty<32;ty+=8)for(tx=0;tx<32;tx+=8)for(y=0;y<8;y++)for(x=0;x<8;x+=2){int z=(ty+y)*32+tx+x;sword_tile_frames[dir][phase][k++]=slash_pixels[z]|(slash_pixels[z+1]<<8);}
}}
void sword_art(int phase){if(phase<0)phase=0;if(phase>6)phase=6;REG32(0x040000D4)=(u32)sword_tile_frames[weapon_action.direction][phase];REG32(0x040000D8)=0x06014000+OBJ_SLASH;REG32(0x040000DC)=0x84000000|256;}
void camera_update(int);
static int region_actor_cursor,region_cache_room=-1;
static unsigned region_actor_keys[20];
COLD void region_pixels_actor(unsigned key,const u8*p,int x,int y){int slot,off;if(!p||x-camera_x<=-8||x-camera_x>=248||y-camera_y<=-8||y-camera_y>=168)return;if(region_actor_cursor>=20)return;slot=region_actor_cursor++;off=slot<8?GFX_OBJ_REGION_A+slot*256:GFX_OBJ_REGION_B+(slot-8)*256;if(region_actor_keys[slot]!=key){obj_upload(p,16,16,off);region_actor_keys[slot]=key;}obj_add(off,x-8,y-8,16,16,1,y,0);}
COLD void region_actor(unsigned id,int x,int y){if(id<REGION_SPR_COUNT)region_pixels_actor(id+1,region_sprites[id],x,y);}
COLD void north_actor(unsigned id,int x,int y){if(id<NORTH_SPR_COUNT)region_pixels_actor(512+id,north_sprites[id],x,y);}
COLD void south_actor(unsigned id,int x,int y){if(id<SOUTH_SPR_COUNT)region_pixels_actor(4096+id,south_sprites[id],x,y);}
COLD void magma_actor(unsigned id,int x,int y){if(id<MAGMA_SPR_COUNT)region_pixels_actor(6144+id,magma_sprites[id],x,y);}
COLD int game_magma_actor_overlap(int x,int y,int radius){unsigned i;for(i=0;i<MAX_ENEMIES;i++)if(enemies[i].hp&&ab(x-enemies[i].x)<radius+5&&ab(y-enemies[i].y)<radius+5)return 1;return 0;}
COLD void region_form_actor(unsigned form,int x,int y){unsigned pose=(frame/7)&3;region_pixels_actor(1024+form*16+pose,companion_form_pixels(form,0,pose),x,y);}
COLD int game_region_entry_safe(void){int i;for(i=0;i<6;i++)if(enemies[i].hp&&near(px,py,enemies[i].x,enemies[i].y,24))return 0;return 1;}
COLD void game_region_warp(int x,int y){if(solid(x,y))return;px=x;py=y;px_q8=x*256;py_q8=y*256;cx=x+14;cy=y+3;cx_q8=cx*256;cy_q8=cy*256;game_attacks_suspend();camera_update(1);cache_valid[0]=cache_valid[1]=0;}
void draw_campaign_actors(void);
void draw_floating_hud(void){int code=(int)progression_current_form()*2+summoned;int width=ability_cd?(ability_max-ability_cd)*16/ability_max:16;
 if(code!=gfx_hud_code){u8 pixels[64];int x,y;const u8 rr[7]={30,17,17,30,20,18,17},bb[7]={30,17,17,30,17,17,30};const u8*rows=summoned?rr:bb;obj_upload(companion_form_pixels(progression_current_form(),0,0),16,16,OBJ_HUD_COMPANION);for(y=0;y<8;y++)for(x=0;x<8;x++)pixels[y*8+x]=(x>=1&&x<=5&&y<7&&(rows[y]&(1<<(5-x))))?WHITE:INK;obj_upload(pixels,8,8,OBJ_HUD_ACTION);gfx_hud_code=code;}
 if(width!=gfx_hud_bar){u8 pixels[256];int x,y;for(y=0;y<8;y++)for(x=0;x<32;x++)pixels[y*32+x]=(x<18&&y>=2&&y<=5)?((x>0&&x<=width&&y==3)?TEAL:INK):0;obj_upload(pixels,32,8,OBJ_HUD_COOLDOWN);gfx_hud_bar=width;}
 obj_add(OBJ_HUD_COMPANION,216,3,16,16,0,9999,0);obj_add(OBJ_HUD_ACTION,204,8,8,8,0,9999,0);obj_add(OBJ_HUD_COOLDOWN,215,18,32,8,0,9999,0);
}
void draw_actors(void){int i,anim=roll_ticks?(roll_ticks/3)&3:(swing||weapon_action.phase==WEAPON_CHARGING||weapon_action.phase==WEAPON_WINDUP||weapon_action.phase==WEAPON_ACTIVE)?1:walk?(walk_phase/6)&3:0,code=face*4+anim;const u8 *hero;obj_count=0;region_actor_cursor=0;if(region_cache_room!=room){int k;for(k=0;k<20;k++)region_actor_keys[k]=0;region_cache_room=room;}
 if(game_state==TITLE||game_state==NEW_GAME_CONFIRM)return;
 if(game_state!=WIN)gfx_ending_revision=-1;
 if(game_state==WIN){if(gfx_ending_revision!=(int)progression_revision){for(i=0;i<4;i++)obj_upload(companion_pixels(i,0,0),16,16,OBJ_PROP+i*256);gfx_ending_revision=progression_revision;}obj_sprite(SPR_HERO_DOWN_0,79,106,106);for(i=0;i<4;i++)obj_add(OBJ_PROP+i*256,91+i*20,100,16,16,1,108,0);return;}
 game_draw_health();
 draw_floating_hud();
 /* obj_add rejects every world-priority actor in these modal states. Avoid
  * walking/uploading invisible actors too; leave their tile keys unchanged
  * so the first visible frame refreshes any pose/room/progression changes. */
 if(game_state==PAUSE||game_state==DEAD||game_state==EVOLVE_CONFIRM||game_state==EVOLVE_ANIM)return;
 region_game_draw_actors();north_game_draw_actors();south_game_draw_actors();magma_game_draw_actors();
 if(room==22)south_actor(SOUTH_SPR_FERRY,208,208);
 if(room==30)magma_actor(MAGMA_SPR_LIFT,288,248);
#ifdef EMBERBOND_POLISHED_ART
 hero=hero_frames[face][anim];
#else
 hero=sprite_data[SPR_HERO_DOWN_0+face*2+(anim&1)];
#endif
 if(code!=gfx_hero_frame){obj_upload(hero,16,16,OBJ_HERO);gfx_hero_frame=code;}
 if(room==0){obj_sprite(SPR_ELDER,120,92,92);if(game_state==PLAY&&near(px,py,120,94,29))obj_add(OBJ_HINT,116,75,8,8,1,999,0);}
 draw_campaign_actors();trials_draw_actors(room,camera_x,camera_y);
 if(room==2){if(torches&1)obj_sprite(SPR_FLAME_0+(frame/7&1),64,57,70);if(torches&2)obj_sprite(SPR_FLAME_0+(frame/7&1),176,57,70);}
 for(i=0;i<MAX_ENEMIES;i++)if(enemies[i].hp){Enemy *e=&enemies[i];obj_add(OBJ_SHADOW,e->x-8,e->y-6,16,16,2,e->y-1,0);if(!e->flash||(frame&2)){if(e->kind==2){int f=enemy_windups[i]?WORLD_SPR_RANGER_WINDUP:WORLD_SPR_RANGER_IDLE;if(room>=16)region_pixels_actor(200+(unsigned)f,world_sprites[f],e->x,e->y);else obj_add(OBJ_WORLD+f*256,e->x-8,e->y-8,16,16,1,e->y,0);}else obj_sprite(SPR_SLIME_0+(frame/10&1),e->x,e->y,e->y);}if(enemy_windups[i])obj_add(OBJ_SPARK,e->x-4,e->y-29,8,8,1,e->y+1,0);game_draw_enemy_phase((unsigned)i,e->x,e->y);}
 if(room==1){obj_add(OBJ_WORLD+(camp_unlocked?WORLD_SPR_CAMP_LIT:WORLD_SPR_CAMP_IDLE)*256,WORLD_CAMP_X-8,WORLD_CAMP_Y-8,16,16,1,WORLD_CAMP_Y,0);obj_add(OBJ_WORLD+(relic_found?WORLD_SPR_CHEST_OPEN:WORLD_SPR_CHEST_CLOSED)*256,WORLD_CHEST_X-8,WORLD_CHEST_Y-8,16,16,1,WORLD_CHEST_Y,0);if(game_state==PLAY&&near(px,py,WORLD_CAMP_X,WORLD_CAMP_Y,26))obj_add(OBJ_HINT,WORLD_CAMP_X-4,WORLD_CAMP_Y-21,8,8,1,999,0);if(game_state==PLAY&&!relic_found&&near(px,py,WORLD_CHEST_X,WORLD_CHEST_Y,26))obj_add(OBJ_HINT,WORLD_CHEST_X-4,WORLD_CHEST_Y-21,8,8,1,999,0);}

 if(room==3||room==8||room==13){obj_add(OBJ_BOSS_SHADOW,boss_x-16,boss_y+1,32,16,2,boss_y,0);if(!boss_flash||(frame&2))obj_add(5120,boss_x-16,boss_y-20,32,32,1,boss_y,0);if(room==3&&boss_active()&&!boss_armor){for(i=0;i<4;i++)obj_add(OBJ_ARMOR,boss_x+(i&1?17:-17)-4,boss_y+(i&2?9:-9)-4,8,8,1,boss_y+1,0);}}
 if(summoned){int d=ab(px-cx)>ab(py-cy)?(px<cx?2:3):(py<cy?1:0);int ca=(frame/7)&3,mcasting=magma_power_cast_time>0&&magma_powers_cast_matches_selected(),scasting=southern_power_cast_time>0&&southern_powers_cast_matches_selected(),ncasting=northern_power_cast_time>0&&northern_power_form==(int)progression_current_form(),casting=regional_power_time>0&&regional_power_time>(regional_power_kind==11?16:40)&&regional_power_form==(int)progression_current_form();if(ncasting)d=northern_power_direction;if(scasting)d=southern_power_direction;if(mcasting)d=magma_power_direction;code=spirit*16+d*4+ca+(casting?2048+((regional_power_time/6)&1)*4096:0)+(ncasting?8192+((northern_power_cast_time/6)&1)*16384:0)+(scasting?32768+((southern_power_cast_time/6)&1)*65536:0)+(mcasting?131072+((magma_power_cast_time/6)&1)*262144:0);
  if(code!=gfx_companion_frame){
#ifdef EMBERBOND_POLISHED_ART
   {const u8*p=mcasting?magma_creature_art_ability_frame(progression_current_form(),(unsigned)d,(unsigned)((magma_power_cast_time/6)&1)):scasting?southern_creature_art_ability_frame(progression_current_form(),(unsigned)d,(unsigned)((southern_power_cast_time/6)&1)):ncasting?northern_creature_art_ability_frame(progression_current_form(),(unsigned)d,(unsigned)((northern_power_cast_time/6)&1)):casting?regional_creature_art_ability_frame(progression_current_form(),(unsigned)d,(unsigned)((regional_power_time/6)&1)):0;obj_upload(p?p:companion_form_pixels(progression_current_form(),(unsigned)d,(unsigned)ca),16,16,OBJ_COMPANION);}
#else
   obj_upload(sprite_data[(spirit?SPR_LEAF_0:SPR_FOX_0)+(ca&1)],16,16,OBJ_COMPANION);
#endif
   gfx_companion_frame=code;
  }
  {int draw_x=cx,draw_y=cy;southern_powers_companion_pose(&draw_x,&draw_y);obj_add(OBJ_SHADOW,draw_x-8,draw_y-6,16,16,2,draw_y-1,0);obj_add(OBJ_COMPANION,draw_x-8,draw_y-9-((spirit==1||spirit==2)?((frame/10)&1):0),16,16,1,draw_y,0);}
 }
 obj_add(OBJ_SHADOW,px-8,py-6,16,16,2,py-1,0);if(!invuln||(frame&4))obj_add(OBJ_HERO,px-8,py-11+(roll_ticks?2:0),16,16,1,py,0);
 if(roll_ticks){obj_add(OBJ_SPARK,px-sign(roll_dx)*12-4,py-sign(roll_dy)*12,8,8,1,py-1,0);}
 game_draw_weapon();
 if(swing){int phase=(13-swing)/2;code=weapon_action.direction*8+phase;if(code!=gfx_slash_frame){sword_art(phase);gfx_slash_frame=code;}obj_add(OBJ_SLASH,px-16,py-17,32,32,1,py+1,0);}
 for(i=0;i<12;i++)if(shots[i].life){if(northern_powers_shot_is_reflected((unsigned)i))obj_add(GFX_OBJ_PHASE_ICONS+CREATURE_METAL*GFX_OBJ_PHASE_STRIDE,shots[i].x-4,shots[i].y-4,8,8,1,shots[i].y+2,0);else if(!shots[i].owner&&shot_effects[i]==SHOT_EFFECT_WIND)obj_add(OBJ_SPARK,shots[i].x-4,shots[i].y-4,8,8,1,shots[i].y+2,0);else obj_sprite(shots[i].owner?SPR_PROJECTILE:SPR_FLAME_0,shots[i].x,shots[i].y,shots[i].y+2);}
 if(game_state==PLAY){advanced_draw();regional_powers_draw();northern_powers_draw();southern_powers_draw();magma_powers_draw();}
 for(i=0;i<6;i++)if(impacts[i].life){int j,r=(20-impacts[i].life)/2+3;for(j=0;j<4;j++)obj_add(OBJ_SPARK,impacts[i].x+(j==0?-r:j==1?r:0)-4,impacts[i].y+(j==2?-r:j==3?r:0)-4,8,8,1,impacts[i].y+2,0);}
 if(summoned&&ability_cd>60&&ability_cd<=75&&spirit==1&&progression_command()<=4){int r=(75-ability_cd)*2;for(i=0;i<4;i++)obj_sprite(SPR_LEAF_0,px+(i==0?-r:i==1?r:0),py+(i==2?-r:i==3?r:0),py+1);}
#ifdef EMBERBOND_POLISHED_ART
 {int n=0;for(i=0;i<FOREGROUND_CANOPY_COUNT;i++)if(game_state==PLAY&&room<4&&room!=1&&foreground_canopies[i].room==room){/* Two fixed masks per room; upload only after room changes below. */
  obj_add(OBJ_CANOPY+n*1024,foreground_canopies[i].x,foreground_canopies[i].y,32,32,0,foreground_canopies[i].y+32,0);n++;}}
#endif
}

/* Original 16-note ambient phrase, square wave 2. Sound effects use channel 1. */
void sound_init(void){REG16(0x04000084)=0x80;REG16(0x04000080)=0x3377;REG16(0x04000082)=2;}
void sfx(int id){REG16(0x04000060)=id==1?0x21:0;REG16(0x04000062)=id==3?0xA180:0x8180;REG16(0x04000064)=0x8000|(id==1?1850:id==2?1700:id==3?1200:1950);}
void music(void){static const u16 notes[]={1547,1750,1840,1750,1602,1750,1820,1750,1673,1800,1874,1800,1602,1700,1750,1602};if(++music_tick>=24){music_tick=0;REG16(0x04000068)=0x2080;REG16(0x0400006C)=0x8000|(notes[music_step++&15]+(room>=9?-60:room>=4?70:0));}}
void toast(int id){toast_id=id;toast_ticks=110;}
void acknowledge_save_failure(void){save_failure_notice=0;if(toast_id==TX_C_SAVE_FAILED)toast_ticks=0;}
void dialogue(int a,int b,int next){dialog_lines[0]=a;dialog_lines[1]=b;dialog_speakers[0]=room==0?TX_ELDER:room==3?TX_BOSS:TX_SUBTITLE;dpage=0;dcount=1;dafter=next;dialogue_action=dialogue_seen=0;game_state=DIALOG;}
void addpage(int a,int b){if(dcount>=6)return;dialog_lines[dcount*2]=a;dialog_lines[dcount*2+1]=b;dialog_speakers[dcount]=dialog_speakers[0];dcount++;}
COLD void make_save(CampaignSave *v,int r,int spawn){zero(v,sizeof *v);v->room=r;v->spawn=spawn;v->chapter_flags=chapter_flags;v->bridge=bridge_open;v->torches=torches;v->relic=relic_found;v->camp=camp_unlocked;v->room_flags=room_flags;v->optional_flags=optional_flags;v->story_seen=story_seen;v->spirit=spirit<4?spirit:0;}
COLD void save_at(int r,int spawn){if(r==14||r==15){r=0;spawn=3;}make_save(&adventure_save.campaign,r,spawn);acknowledge_save_failure();save_failed=0;save_requested=1;saved_room=r;}
COLD void save_game(void){save_at(room,checkpoint_spawn);}
COLD int check_save(void){return save5_has_valid();}
COLD void save_frame(void){if(save_requested&&game_state!=SAVE_PENDING){save_requested=0;save_resume_state=game_state;game_attacks_suspend();save_begin_pending=magma_game_save_prepare_pending()?3:1;game_state=SAVE_PENDING;}}
COLD void show_scene(int id,int action,unsigned seen){const CampaignDialogue*d=&campaign_dialogues[id];int i;dpage=0;dcount=d->pages;dafter=PLAY;dialogue_action=action;dialogue_seen=seen;for(i=0;i<dcount;i++){dialog_lines[i*2]=d->lines[i*2];dialog_lines[i*2+1]=d->lines[i*2+1];dialog_speakers[i]=d->speaker;}game_state=DIALOG;}
COLD void append_scene(int id){const CampaignDialogue*d=&campaign_dialogues[id];int i;for(i=0;i<d->pages&&dcount<6;i++){dialog_lines[dcount*2]=d->lines[i*2];dialog_lines[dcount*2+1]=d->lines[i*2+1];dialog_speakers[dcount++]=d->speaker;}}
COLD void finish_dialogue(void){story_seen|=dialogue_seen;game_state=dafter;if(dialogue_action==1)enter_room(0,3);else if(dialogue_action==2){chapter_flags|=SAVE4_ENDING_SEEN;completed=1;save_at(0,3);game_state=WIN;}else if(dialogue_seen)save_game();if(game_state==PLAY)acknowledge_save_failure();dialogue_action=dialogue_seen=0;}
void camera_update(int snap){int tx,ty;if(!scrolling_room()){camera_x=camera_y=camera_fx=camera_fy=0;return;}
 tx=px-120;ty=py-80;if(tx<0)tx=0;if(tx>WORLD_W-240)tx=WORLD_W-240;if(ty<0)ty=0;if(ty>WORLD_H-160)ty=WORLD_H-160;
 if(snap){camera_fx=tx*256;camera_fy=ty*256;}else{if(ab(tx*256-camera_fx)<4)camera_fx=tx*256;else camera_fx+=(tx*256-camera_fx)/4;if(ab(ty*256-camera_fy)<4)camera_fy=ty*256;else camera_fy+=(ty*256-camera_fy)/4;}
 camera_x=camera_fx>>8;camera_y=camera_fy>>8;
}
COLD void spawn_enemies(void){zero(enemies,sizeof enemies);zero(shots,sizeof shots);zero(ordinary_hostile_shots,sizeof ordinary_hostile_shots);zero(impacts,sizeof impacts);zero(enemy_clocks,sizeof enemy_clocks);zero(enemy_windups,sizeof enemy_windups);
 if(room==1){enemies[0]=(Enemy){184,232,2,0,0};enemies[1]=(Enemy){326,238,4,0,2};enemies[2]=(Enemy){290,102,2,0,0};enemies[3]=(Enemy){412,92,4,0,2};enemies[4]=(Enemy){108,91,2,0,0};}
 if(room==17){enemies[0]=(Enemy){184,264,4,0,0};enemies[1]=(Enemy){312,248,4,0,0};enemies[2]=(Enemy){400,240,6,0,2};enemies[3]=(Enemy){152,112,4,0,0};enemies[4]=(Enemy){296,88,6,0,2};}
 if(room==2){enemies[0]=(Enemy){55,113,2,0,1};enemies[1]=(Enemy){184,110,2,0,1};}
 if(room>=4&&room<14){const CampaignRoom*d=&campaign_rooms[room-4];int i;if(room==6&&(room_flags&CF_SKY_PATROL_CLEAR))return;for(i=0;i<d->enemy_count;i++)enemies[i]=(Enemy){d->enemies[i].x,d->enemies[i].y,d->enemies[i].hp,0,d->enemies[i].kind};}}

COLD void enter_room(int r,int fromnorth){int oldroom=room;quickparty_reset(keys);if((unsigned)r>45)return;adventure_save.campaign.chapter_flags=chapter_flags;if(r>=38){if(!magma_game_can_enter((unsigned)r)||(unsigned)fromnorth>=magma_game_spawn_count((unsigned)r))return;}else if(r>=30){if(!southern_can_enter(&adventure_save,(unsigned)r)||(unsigned)fromnorth>=(r==30?5u:r==31?4u:1u))return;}else if(r>=22){if(!northern_can_enter(&adventure_save,(unsigned)r)||(unsigned)fromnorth>=(r==22?5u:r==23?3u:1u))return;}else if(r>=16&&(!regional_can_enter(&adventure_save,(unsigned)r)||(unsigned)fromnorth>=(r==16?6u:r==17?3u:1u)))return;if((room==0||room==16||room==22||room==30||room==38)&&r!=room&&!restoring_checkpoint)creatures_begin_expedition(&adventure_save.roster);room=r;trials_enter(r);checkpoint_spawn=fromnorth;px=120;py=fromnorth==1?40:139;invuln=90;boss_time=0;roll_ticks=roll_cd=attack_buffer=combo_timer=combo_step=0;swing=sword_cd=hitstop=0;game_attacks_reset();spawn_enemies();game_enemy_health_reset();if(r==17){enemy_phases[0]=CREATURE_WOOD;enemy_phases[1]=CREATURE_FIRE;enemy_phases[2]=CREATURE_METAL;enemy_phases[3]=CREATURE_WATER;enemy_phases[4]=CREATURE_EARTH;}if(r==23){static const short ex[5]={272,144,272,416,320},ey[5]={256,176,48,176,96};int e;for(e=0;e<5;e++){enemies[e]=(Enemy){ex[e],ey[e],e==2||e==4?6:4,0,e==2||e==4?2:0};enemy_hp_q4[e]=enemies[e].hp*16;enemy_phases[e]=(unsigned char)e;}}
 if(r==31||r==33){const SouthEnemySpawn*rows=0;unsigned count=south_game_enemy_spawns((unsigned)r,&rows),e;
  for(e=0;e<count&&e<MAX_ENEMIES;e++){enemies[e]=(Enemy){rows[e].x,rows[e].y,rows[e].hp,0,rows[e].kind};enemy_hp_q4[e]=rows[e].hp*16;enemy_phases[e]=rows[e].phase;}}
 if(r>=38){const MagmaEnemySpawn*rows=0;unsigned count=magma_game_enemy_spawns((unsigned)r,&rows),e;for(e=0;e<count&&e<MAX_ENEMIES;e++){enemies[e]=(Enemy){rows[e].x,rows[e].y,rows[e].hp,0,rows[e].kind};enemy_hp_q4[e]=rows[e].hp*16;enemy_phases[e]=rows[e].phase;}}
 if(r==0){px=fromnorth==4?180:fromnorth==5?76:120;py=fromnorth==3?118:128;game_health_fill();if(fromnorth==1||fromnorth==2)checkpoint_spawn=0;}
 if(r>=2&&fromnorth==2)checkpoint_spawn=0;
 if(r>=4){px=120;py=fromnorth==1?52:132;}
 if(r==4&&oldroom==14){px=204;py=86;checkpoint_spawn=0;}
 if(r==9&&oldroom==15){px=208;py=140;checkpoint_spawn=0;}
 if(r==1&&fromnorth==2&&!camp_unlocked)checkpoint_spawn=0;
 if(r==2&&fromnorth==1)py=torches==3?52:139;
 if(r==1){px=fromnorth==1?WORLD_TEMPLE_X:(fromnorth==2&&camp_unlocked)?WORLD_CAMP_X:WORLD_SPAWN_X;py=fromnorth==1?43:(fromnorth==2&&camp_unlocked)?WORLD_CAMP_Y+16:WORLD_SPAWN_Y;}
 if(r==1&&fromnorth==3){px=168;py=264;checkpoint_spawn=0;}
 if(r>=38)magma_game_enter((unsigned)r,(unsigned)fromnorth);else if(r>=30)south_game_enter((unsigned)r,(unsigned)fromnorth);else if(r>=22)north_game_enter((unsigned)r,(unsigned)fromnorth);else if(r>=16)region_game_enter((unsigned)r,(unsigned)fromnorth);
 if(r==3||r==8||r==13){boss_x=120;boss_y=r==3?65:68;boss_hp_max=r==3?12:r==8?20:24;game_boss_health_set((unsigned)boss_hp_max);boss_armor=0;boss_flash=0;boss_state=boss_state_ticks=boss_phase=boss_pattern=hazard_mode=0;obj_upload(r==3?boss_data:campaign_boss_data[r==8?0:1],32,32,5120);if(!boss_active())game_boss_health_set(0);}
 if(r<16&&oldroom>=16){int w;for(w=0;w<WORLD_SPR_COUNT;w++)obj_upload(world_sprites[w],16,16,OBJ_WORLD+w*256);}
 area_ticks=100;transition_lock=20;stone_guard=guard_invuln=power_effect=0;advanced_reset();regional_powers_reset();northern_powers_reset();southern_powers_reset();magma_powers_reset();{unsigned e;for(e=0;e<MAX_ENEMIES;e++){southern_powers_enemy_spawn(e);magma_powers_enemy_spawn(e);}}gfx_props_room=-1;
 cx=px+14;cy=py+3;px_q8=px*256;py_q8=py*256;cx_q8=cx*256;cy_q8=cy*256;transition=10;camera_update(1);cache_valid[0]=cache_valid[1]=0;
#ifdef EMBERBOND_POLISHED_ART
 {int i,n=0;for(i=0;i<FOREGROUND_CANOPY_COUNT;i++)if(foreground_canopies[i].room==r)obj_upload(foreground_canopy_data[i],32,32,OBJ_CANOPY+(n++)*1024);}
#endif
 save_game();if(r==5&&!(story_seen&SAVE4_SEEN_SKY_INTRO)){show_scene(CD_SKY_INTRO,0,SAVE4_SEEN_SKY_INTRO);}
 if(r==9&&!(story_seen&SAVE4_SEEN_CORE_INTRO)){show_scene(CD_CORE_INTRO,0,SAVE4_SEEN_CORE_INTRO);}
 if(r==8&&boss_active()){show_scene(CD_SKY_BOSS_INTRO,0,0);}
 if(r==13&&boss_active()){show_scene(CD_CORE_STONE_HINT,0,0);}
 if(r==2&&!seen_temple){seen_temple=1;dialogue(TX_TEMPLE1,TX_TEMPLE2,PLAY);}if(r==3&&!seen_boss){seen_boss=1;dialogue(TX_BOSS1,TX_BOSS2,PLAY);}}
COLD void start_game(int resume){int oldsave=has_save;south_game_reset();southern_powers_reset();magma_game_reset();magma_powers_reset();quickparty_reset(keys);quickparty_menu_slot=quickparty_menu_candidate=0;restoring_checkpoint=0;progression_new();zero(enemies,sizeof enemies);zero(shots,sizeof shots);zero(impacts,sizeof impacts);frame=0;room=0;px=120;py=126;max_hp=6;game_health_refresh(1);game_attacks_reset();gear_menu_reset();relic_found=camp_unlocked=0;roll_ticks=roll_cd=combo_step=combo_timer=attack_buffer=0;loaded_save_version=0;journal_tab=0;chapter_flags=room_flags=optional_flags=story_seen=0;checkpoint_spawn=0;stone_guard=guard_invuln=transition_lock=0;spirit=0;summoned=0;bridge_open=0;torches=0;boss_hp=12;quest_started=0;completed=0;face=0;walk=0;invuln=0;swing=0;sword_cd=0;ability_cd=0;ability_max=75;heal_cd=0;toast_ticks=0;seen_temple=0;seen_boss=0;deaths=0;kills=0;ticks=0;cx=136;cy=126;px_q8=px*256;py_q8=py*256;cx_q8=cx*256;cy_q8=cy*256;walk_phase=0;hitstop=0;transition=0;game_state=PLAY;camera_update(1);
#ifdef EMBERBOND_POLISHED_ART
 {int i,n=0;for(i=0;i<FOREGROUND_CANOPY_COUNT;i++)if(foreground_canopies[i].room==0)obj_upload(foreground_canopy_data[i],32,32,OBJ_CANOPY+(n++)*1024);}
#endif
 if(resume&&oldsave){CampaignSave v;if(!progression_load()){has_save=0;game_state=TITLE;return;}v=adventure_save.campaign;loaded_save_version=v.loaded_version;chapter_flags=v.chapter_flags;room_flags=v.room_flags;optional_flags=v.optional_flags;story_seen=v.story_seen;bridge_open=v.bridge;torches=v.torches;relic_found=v.relic;camp_unlocked=v.camp;max_hp=relic_found?8:6;game_health_refresh(1);spirit=(int)progression_current_spirit();quest_started=1;completed=(chapter_flags&SAVE4_ENDING_SEEN)!=0;seen_temple=v.room>=2;seen_boss=v.room==3;restoring_checkpoint=1;enter_room(v.room,v.spawn);restoring_checkpoint=0;
 if(!(chapter_flags&SAVE4_ENDING_SEEN)){
  if((chapter_flags&SAVE4_CORE_CLEAR)&&!(story_seen&SAVE4_SEEN_CORE_RELEASE))show_scene(CD_CORE_RELEASE,1,SAVE4_SEEN_CORE_RELEASE);
  else if((chapter_flags&SAVE4_SKY_CLEAR)&&!(story_seen&SAVE4_SEEN_STONE_JOIN))show_scene(CD_STONE_JOIN,1,SAVE4_SEEN_STONE_JOIN|SAVE4_SEEN_WIND_JOIN);
  else if((chapter_flags&SAVE4_GROVE_CLEAR)&&!(story_seen&SAVE4_SEEN_WIND_JOIN)){show_scene(loaded_save_version<4?CD_LEGACY_RECAP:CD_WIND_JOIN,1,SAVE4_SEEN_WIND_JOIN|(loaded_save_version<4?SAVE4_SEEN_LEGACY_RECAP:0));}
 }else game_state=PLAY;
 if(game_state==PLAY&&!save_failed)toast(TX_SAVED);
 }
 else {quest_started=1;dialogue(TX_INTRO1A,TX_INTRO1B,PLAY);addpage(TX_INTRO2A,TX_INTRO2B);addpage(TX_INTRO3A,TX_INTRO3B);addpage(TX_INTRO4A,TX_INTRO4B);addpage(TX_EXPLORE1,TX_EXPLORE2);addpage(TX_CAMP_GUIDE1,TX_CAMP_GUIDE2);save_game();}}

/* Fresh A edge is required after opening this confirmation. Cancel wins when
 * buttons conflict, and entering/cancelling never touches either SRAM bank. */
COLD void update_title(void){
 if(game_state==NEW_GAME_CONFIRM){
  if(pressed&(KEY_B|KEY_START|KEY_SELECT)){game_state=TITLE;return;}
  if(pressed&KEY_A)start_game(0);
  return;
 }
 if(pressed&KEY_START)start_game(has_save);
 else if(pressed&KEY_SELECT){if(has_save)game_state=NEW_GAME_CONFIRM;else start_game(0);}
}

int solid(int x,int y){
 int i;if(((unsigned)(room-38)<8u))return magma_game_solid(x,y);if(south_game_is_room((unsigned)room))return south_game_solid(x,y);if(north_game_is_room((unsigned)room))return north_game_solid(x,y);if(region_game_is_room((unsigned)room))return region_game_solid(x,y);if(trials_is_room(room))return trials_solid(room,x,y);
 if(room>=4&&room<14){const CampaignRoom*d=&campaign_rooms[room-4];int k;unsigned pr=progress_bits();if(x<12||x>=228||y<32||y>=148)return 1;for(k=0;k<5;k++){int xx=x+(k?(k&1?-4:4):0),yy=y+(k?(k&2?-4:4):0);for(i=0;i<d->solid_count;i++){const CampaignBlock*b=&d->solids[i];if(xx>=b->x&&xx<b->x+b->w&&yy>=b->y&&yy<b->y+b->h)return 1;}for(i=0;i<d->block_count;i++){const CampaignBlock*b=&d->blocks[i];if((pr&b->flags)!=b->flags&&xx>=b->x&&xx<b->x+b->w&&yy>=b->y&&yy<b->y+b->h)return 1;}}return 0;}
 if(room==1){if(x<12||x>=WORLD_W-12||y<24||y>=WORLD_H-12)return 1;for(i=0;i<OVERWORLD_SOLID_COUNT;i++){const WorldRect*r=&overworld_solids[i];if(x>=r->x&&x<r->x+r->w&&y>=r->y&&y<r->y+r->h)return 1;}if(y>=WORLD_RIVER_Y&&y<WORLD_RIVER_Y+WORLD_RIVER_H&&(!bridge_open||x<WORLD_BRIDGE_X||x>=WORLD_BRIDGE_X+WORLD_BRIDGE_W))return 1;return 0;}
 if(x<12||x>227||y<28||y>152)return 1;
 for(i=0;i<asset_solids_count[room];i++) {const AssetRect *r=&asset_solids[room][i];if(x>=r->x&&x<r->x+r->w&&y>=r->y&&y<r->y+r->h)return 1;}

 if(room==2){if(y<44&&x>88&&x<152&&torches!=3)return 1;if((ab(x-64)<13||ab(x-176)<13)&&ab(y-64)<10)return 1;}
 if(room==3&&y<39)return 1;
 return 0;
}
void move_player(int dx,int dy){while(dx||dy){int sx=dx>256?256:dx<-256?-256:dx,sy=dy>256?256:dy<-256?-256:dy;int nx=px_q8+sx,ny=py_q8+sy;if(!solid(nx>>8,py))px_q8=nx;if(!solid(px,ny>>8))py_q8=ny;px=px_q8>>8;py=py_q8>>8;dx-=sx;dy-=sy;}}
COLD void damage_amount(unsigned base,unsigned attack_phase){if(!base||base>255)return;if(invuln||guard_invuln||roll_ticks||game_state!=PLAY)return;if(stone_guard){if(advanced_guard_charges>1)advanced_guard_charges--;else{stone_guard=0;advanced_guard_charges=0;}guard_invuln=24;impact(px,py);toast(TX_C_STONE_GUARD);return;}game_health_hurt(base,attack_phase);invuln=80;sfx(3);if(hp<=0){game_state=DEAD;deaths++;summoned=0;zero(shots,sizeof shots);game_attacks_reset();regional_powers_reset();northern_powers_reset();southern_powers_reset();south_game_reset();magma_powers_reset();magma_game_reset();}}
void damage_phase(unsigned attack_phase){damage_amount(16,attack_phase);}
COLD void game_north_hurt(unsigned base){damage_amount(base,COMBAT_NEUTRAL_PHASE);}
void damage(void){damage_phase(COMBAT_NEUTRAL_PHASE);}
int fire_shot(int x,int y,int dx,int dy,int owner){int i;for(i=0;i<12;i++)if(!shots[i].life){shots[i]=(Shot){x,y,dx,dy,90,owner};northern_powers_shot_spawn((unsigned)i);ordinary_hostile_shots[i]=0;shot_effects[i]=owner?SHOT_EFFECT_NONE:SHOT_EFFECT_FIRE;shot_phases[i]=owner?COMBAT_NEUTRAL_PHASE:game_companion_phase();return i;}return -1;}
COLD int trial_event(int event){int i;if(!event)return 0;
 if(event==TRIAL_ENTER_WIND){enter_room(14,0);dialogue(TX_T_WIND_HINT1,TX_T_WIND_HINT2,PLAY);return 1;}
 if(event==TRIAL_ENTER_STONE){enter_room(15,0);dialogue(TX_T_STONE_HINT1,TX_T_STONE_HINT2,PLAY);return 1;}
 if(event==TRIAL_EXIT){int r=trials_exit(room,px,py);if(r>=0)enter_room(r,0);return 1;}
 if((event==TRIAL_INSPECT||event==TRIAL_ALREADY_DONE)&&room==1)for(i=0;i<MAX_ENEMIES;i++)if(enemies[i].hp&&near(px,py,enemies[i].x,enemies[i].y,44))return 0;
 if(trials_event_needs_save(event))save_game();
 if(event>=TRIAL_COMPLETE_HOMURA&&event<=TRIAL_COMPLETE_KOHAKU){progression_refresh();dialogue(TX_T_COMPLETE1,TX_T_COMPLETE2,PLAY);sfx(4);return 1;}
 if(event==TRIAL_INSPECT){if(room==14)dialogue(TX_T_WIND_HINT1,TX_T_WIND_HINT2,PLAY);else if(room==15)dialogue(TX_T_STONE_HINT1,TX_T_STONE_HINT2,PLAY);else{int which=0,best=999;for(i=0;i<6;i++){int d=ab(px-trial_grove_aids[i].x)+ab(py-trial_grove_aids[i].y);if(d<best){best=d;which=trial_grove_aids[i].family;}}dialogue(which?TX_T_ROOT_HINT1:TX_T_FIRE_HINT1,which?TX_T_ROOT_HINT2:TX_T_FIRE_HINT2,PLAY);}return 1;}
 if(event==TRIAL_RESTORED)toast(TX_T_RESTORED);else if(event==TRIAL_WRONG_POWER)toast(TX_C_POWER_MISMATCH);else if(event==TRIAL_NEED_PLATES)toast(TX_T_NEED_PLATES);else if(event==TRIAL_ALREADY_DONE)toast(TX_T_ALREADY);else if(event==TRIAL_RESET)toast(TX_T_RESET);else if(event==TRIAL_BLOCKED)toast(TX_T_BLOCKED);sfx(event==TRIAL_PUSHED?1:2);return 1;
}
int campaign_power(void);
int campaign_interact(void);
COLD void ability(void){int i;unsigned command=progression_command();game_geometry_sync();if(!summoned){toast(TX_NEEDSUMMON);return;}if(ability_cd){if(magma_powers_can_aim()){if(!magma_powers_aim())toast(TX_SP_AIM_CLEAR);}else if(southern_powers_can_aim()){if(!southern_powers_aim())toast(TX_SP_AIM_CLEAR);}else toast(TX_COOLDOWN);return;}
 {int field=magma_game_power(command);if(field){if(field==1){ability_max=ability_cd=game_power_cooldown(75);power_effect=20;if(command>=43&&command<=66)magma_powers_feedback(command);else if(command>=23&&command<=42)southern_powers_feedback(command);else if(command>=13&&command<=22)northern_powers_feedback(command);sfx(2);}return;}}
 if(command>=43&&command<=66){if(!magma_power(command))toast(TX_SP_AIM_CLEAR);return;}
 {int field=south_game_power(command);if(field){if(field==1){ability_max=ability_cd=game_power_cooldown(75);power_effect=20;if(command>=23&&command<=42)southern_powers_feedback(command);else if(command>=13&&command<=22)northern_powers_feedback(command);sfx(2);}return;}}
 if(command>=23&&command<=42){if(!southern_power(command))toast(TX_SP_AIM_CLEAR);return;}
 if(command>=13&&command<=22){if(north_game_power(command)){ability_max=ability_cd=game_power_cooldown(creatures_ability(command)->cooldown_updates);northern_powers_feedback(command);sfx(2);}else if(!northern_power(command))toast(TX_COOLDOWN);return;}
 ability_max=ability_cd=game_power_cooldown(75);sfx(2);if(north_game_power(command))return;if(region_game_power(command))return;if(trial_event(trials_power(room,px,py,spirit)))return;if(campaign_power())return;if(command>=9&&command<=11){regional_power(command);return;}

 if(spirit==1){if(room==1&&!bridge_open&&near(px,py,WORLD_BRIDGE_CENTER_X,WORLD_BRIDGE_Y,55)){bridge_open=1;save_game();dialogue(TX_BRIDGE1,TX_BRIDGE2,PLAY);return;}if(progression_command()>4&&advanced_power(progression_command()))return;if(!heal_cd&&hero_hp_q4<gear_stats.max_hp_q4){game_health_heal(16);heal_cd=360;toast(TX_HEALED);}for(i=0;i<MAX_ENEMIES;i++)if(enemies[i].hp&&near(px,py,enemies[i].x,enemies[i].y,47)){enemies[i].flash=35;enemies[i].x+=sign(enemies[i].x-px)*6;enemies[i].y+=sign(enemies[i].y-py)*6;}return;}
 if(room==2){int before=torches;if(near(px,py,64,64,42))torches|=1;if(near(px,py,176,64,42))torches|=2;if(before!=torches){save_game();if(torches==3)dialogue(TX_GATE1,TX_GATE2,PLAY);return;}}
 if(room==3&&boss_active()&&!boss_armor&&near(px,py,boss_x,boss_y,84)){boss_armor=210;boss_flash=12;toast(TX_EXPOSED);fire_shot(cx,cy,sign(boss_x-cx)*2,sign(boss_y-cy)*2,0);return;}
 if(progression_command()>4&&advanced_power(progression_command()))return;
 if(spirit==0)fire_shot(px,py,face==2?-2:face==3?2:0,face==1?-2:face==0?2:0,0);}
COLD int southern_ferry_interact(void){
 if(room!=22||!near(px,py,208,224,22)||!game_region_entry_safe())return 0;
 if(!southern_can_enter(&adventure_save,30)){dialogue(TX_ST_FERRY_WAIT_A,TX_ST_FERRY_WAIT_B,PLAY);return 1;}
 enter_room(30,0);return 1;
}
COLD int magma_lift_interact(void){if(room!=30||!near(px,py,288,248,23)||!game_region_entry_safe())return 0;if(!magma_game_can_enter(38)){dialogue(TX_MG_LIFT_WAIT_A,TX_MG_LIFT_WAIT_B,PLAY);return 1;}enter_room(38,0);return 1;}
int try_interaction(void){if(magma_lift_interact())return 1;if(magma_game_interact())return 1;if(southern_ferry_interact())return 1;if(south_game_interact())return 1;if(north_game_interact())return 1;if(region_game_interact())return 1;
 if(trial_event(trials_interact(room,px,py,face)))return 1;
 if(campaign_interact())return 1;
 if(room==1&&near(px,py,WORLD_CAMP_X,WORLD_CAMP_Y,26)){camp_unlocked=1;checkpoint_spawn=SAVE4_SPAWN_CAMP;game_health_fill();save_game();dialogue(TX_CAMP1,TX_CAMP2,PLAY);return 1;}
 if(room==1&&!relic_found&&near(px,py,WORLD_CHEST_X,WORLD_CHEST_Y,26)){relic_found=1;max_hp=8;game_health_refresh(1);save_game();dialogue(TX_RELIC1,TX_RELIC2,PLAY);return 1;}
 return 0;}
void sword(void){game_attack_update(keys,KEY_A);}
int sword_hits(int x,int y,int radius){int dx=x-px,dy=y-py;if(ab(dx)+ab(dy)>radius)return 0;if(face==0&&dy>=-6)return 1;if(face==1&&dy<=6)return 1;if(face==2&&dx<=6)return 1;if(face==3&&dx>=-6)return 1;return 0;}
void impact(int x,int y){int i;for(i=0;i<6;i++)if(!impacts[i].life){impacts[i]=(Impact){x,y,20};return;}impacts[0]=(Impact){x,y,20};}
void kill_enemy(Enemy*e){impact(e->x,e->y);e->hp=0;kills++;progression_encounter(room,(unsigned)(e-enemies));if(hero_hp_q4<gear_stats.max_hp_q4&&kills%3==0)game_health_heal(16);}
void update_enemies(void){int i,j;for(i=0;i<MAX_ENEMIES;i++){Enemy*e=&enemies[i];if(!e->hp)continue;if(e->flash)e->flash--;if(!e->flash&&game_melee_hit((unsigned)i,e->x,e->y,0)){game_enemy_hurt((unsigned)i,weapon_action.damage_q4,weapon_action.attack_q4,weapon_action.element);southern_powers_weapon_hit((unsigned)i);game_enemy_stagger((unsigned)i,weapon_action.stagger);e->flash=16;hitstop=3;sfx(4);if(e->hp<=0)kill_enemy(e);else{int nx=e->x+sign(e->x-px)*5,ny=e->y+sign(e->y-py)*5;if(!solid(nx,ny)){e->x=nx;e->y=ny;}}}if(!e->hp)continue;
 if(e->kind==2&&!rooted_enemies[i]){if(e->flash||enemy_stagger_ticks[i])enemy_windups[i]=0;else if(enemy_windups[i]){if(--enemy_windups[i]==0){{int shot=fire_shot(e->x,e->y,enemy_aimx[i],enemy_aimy[i],1);if(shot>=0){shot_phases[shot]=enemy_phases[i];ordinary_hostile_shots[shot]=1;}}enemy_clocks[i]=100;}}else if(enemy_clocks[i])enemy_clocks[i]--;else if(near(px,py,e->x,e->y,145)){int dx=px-e->x,dy=py-e->y,m=ab(dx)>ab(dy)?ab(dx):ab(dy);if(!m)m=1;enemy_aimx[i]=dx*2/m;enemy_aimy[i]=dy*2/m;enemy_windups[i]=(int)southern_powers_windup((unsigned)i,30);}}
 else if(!rooted_enemies[i]&&!enemy_stagger_ticks[i]&&!e->flash&&frame%3==0&&(!slowed_enemies[i]||frame%2==0)&&near(px,py,e->x,e->y,70)){int tx=px,ty=py,dx,dy;southern_powers_approach((unsigned)i,&tx,&ty);dx=sign(tx-e->x);dy=sign(ty-e->y);if((frame+i)&1){if(!solid(e->x+dx,e->y))e->x+=dx;}else if(!solid(e->x,e->y+dy))e->y+=dy;}
 if(ab(px-e->x)<11&&ab(py-e->y)<11){int blocked=0;if(e->kind!=2&&!invuln&&!guard_invuln&&!roll_ticks&&game_state==PLAY)blocked=southern_powers_melee_guard((unsigned)i,e->x,e->y)||magma_powers_melee_guard((unsigned)i,e->x,e->y);if(!blocked)damage_phase(enemy_phases[i]);}
 for(j=0;j<12;j++)if(shots[j].life&&!shots[j].owner&&near(e->x,e->y,shots[j].x,shots[j].y,14)){shots[j].life=0;game_enemy_hurt((unsigned)i,32,0,shot_phases[j]);e->flash=16;enemy_windups[i]=0;if(e->hp<=0)kill_enemy(e);break;}}
}
void campaign_boss_update(void);
void boss_reward(void);
void update_boss(void){int i;if(!boss_active())return;if(boss_hp<=0){game_boss_health_set(0);boss_reward();return;}if(room>=4&&room<14){campaign_boss_update();return;}boss_time++;if(boss_armor)boss_armor--;if(boss_flash)boss_flash--;if(boss_armor&&!boss_flash&&game_melee_hit(6,boss_x,boss_y,1)){game_boss_hurt(weapon_action.damage_q4==48?32:16,weapon_action.attack_q4,weapon_action.element);boss_flash=16;hitstop=3;impact(boss_x,boss_y);sfx(4);if(boss_hp<=0){boss_hp=0;boss_reward();return;}}
 if(!boss_armor){if(boss_time%120==0){for(i=0;i<8;i++){static const int vx[]={2,2,0,-2,-2,-2,0,2};static const int vy[]={0,2,2,2,0,-2,-2,-2};fire_shot(boss_x,boss_y,vx[i],vy[i],1);}}if(boss_time%240>175&&boss_time%3==0){boss_x+=sign(px-boss_x);boss_y+=sign(py-boss_y);}}else if(boss_time%10==0){boss_x+=sign(120-boss_x);boss_y+=sign(65-boss_y);}
 if(boss_x<30)boss_x=30;
 if(boss_x>210)boss_x=210;
 if(boss_y<48)boss_y=48;
 if(boss_y>130)boss_y=130;
 if(ab(px-boss_x)<20&&ab(py-boss_y)<20)damage();}
COLD int shot_segment_clear(int x,int y,int tx,int ty){int dx=ab(tx-x),dy=-ab(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,err=dx+dy;while(x!=tx||y!=ty){int twice=err*2;if(twice>=dy){err+=dy;x+=sx;}if(twice<=dx){err+=dx;y+=sy;}if(solid(x,y))return 0;}return 1;}
void update_shots(void){int i;for(i=0;i<12;i++){Shot*s=&shots[i];if(!s->life)continue;s->life--;if(magma_powers_intercept_shot((unsigned)i,s->x,s->y,s->x+s->dx,s->y+s->dy,s->owner&&ordinary_hostile_shots[i]))continue;if(southern_powers_intercept_shot((unsigned)i,s->x,s->y,s->x+s->dx,s->y+s->dy,s->owner&&ordinary_hostile_shots[i]))continue;if(northern_powers_shot_is_reflected((unsigned)i)&&!shot_segment_clear(s->x,s->y,s->x+s->dx,s->y+s->dy)){s->life=0;continue;}s->x+=s->dx;s->y+=s->dy;if(s->x<8||s->x>world_width()-8||s->y<(scrolling_room()?8:26)||s->y>(scrolling_room()?world_height()-8:151)||((room==1||room>=4)&&solid(s->x,s->y))){s->life=0;continue;}if(s->owner&&near(px,py,s->x,s->y,11)){damage_phase(shot_phases[i]);s->life=0;}if(!s->owner&&shot_effects[i]==SHOT_EFFECT_FIRE&&room==3&&boss_active()&&!boss_armor&&near(s->x,s->y,boss_x,boss_y,25)){boss_armor=210;boss_flash=10;s->life=0;}
 if(!s->owner&&shot_effects[i]==SHOT_EFFECT_FIRE&&room==2){int old=torches;if(near(s->x,s->y,64,64,14)){torches|=1;s->life=0;}if(near(s->x,s->y,176,64,14)){torches|=2;s->life=0;}if(torches!=old){save_game();if(torches==3)dialogue(TX_GATE1,TX_GATE2,PLAY);}}}}
/* Exact inputs of solid(), separate from UI revisions and actor positions.
 * Synchronize before cached combat geometry and again before drawing because
 * A/field actions, shots or rewards may change collision later in the update.
 * New dynamic-collision systems must extend this explicit fingerprint. */
static u32 collision_fingerprint[4];
COLD void game_geometry_sync(void){
 u32 values[4]={(u32)room,0,0,0};int i,changed=0;
 if(room==1)values[1]=(u32)bridge_open;
 else if(room==2)values[1]=(u32)torches;
 else if(room>=4&&room<14)values[1]=progress_bits();
 else if(room==17)values[1]=adventure_save.quests.objectives[REGION_QUEST_DRY_ROAD]&2u;
 if(room==15||room==20){short(*points)[2]=room==15?trial_parcels:region_game_crates;
  values[2]=(u16)points[0][0]|((u32)(u16)points[0][1]<<16);
  values[3]=(u16)points[1][0]|((u32)(u16)points[1][1]<<16);
 }
 if(((unsigned)(room-38)<8u))magma_game_collision_inputs(values+1);
 for(i=0;i<4;i++)if(collision_fingerprint[i]!=values[i]){changed=1;collision_fingerprint[i]=values[i];}
 if(changed){southern_powers_geometry_changed();magma_powers_geometry_changed();}
}
COLD unsigned journal_page_count(void){return (adventure_save.quests.region_flags[3]&1)?9:(adventure_save.quests.region_flags[2]&1)?8:7;}
void update(void){int dx=0,dy=0;frame++;music();if(game_state!=PLAY||quickparty_open||(pressed&KEY_L))game_attacks_suspend();if(game_state!=PLAY)quickparty_reset(keys);else if(quickparty_update(keys,pressed))return;if(transition)transition--;if(toast_ticks)toast_ticks--;if(game_state==TITLE||game_state==NEW_GAME_CONFIRM){update_title();return;}
 if(game_state==SAVE_PENDING){int status;
 /* Deferred chapter proofs need both bitmap pages warm before their bounded
  * validation frame. No snapshot starts until the exact proof has succeeded. */
 if(save_begin_pending>1){
  if(save_begin_pending==2&&!magma_game_prepare_save()){save_begin_pending=0;save_failed=save_failure_notice=1;game_state=save_resume_state;toast(TX_C_SAVE_FAILED);}
  else save_begin_pending--;
  return;
 }
 if(save_begin_pending){save_begin_pending=0;if(!progression_save_begin()){save_failed=save_failure_notice=1;game_state=save_resume_state;toast(TX_C_SAVE_FAILED);}return;}status=progression_save_step();if(status==SAVE5_DONE){save_failed=0;acknowledge_save_failure();has_save=1;game_state=save_resume_state;}else if(status==SAVE5_FAILED){save_failed=save_failure_notice=1;game_state=save_resume_state;toast(TX_C_SAVE_FAILED);}return;}
 if(game_state==EVOLVE_CONFIRM){progression_confirm_input(pressed);return;}
 if(game_state==EVOLVE_ANIM){progression_evolution_tick();return;}
 if(game_state==DIALOG){if(pressed&KEY_A){sfx(4);if(++dpage>=dcount)finish_dialogue();}return;}
 if(game_state==PAUSE){if(quickparty_menu_input(pressed)||progression_menu_input(pressed)||gear_menu_input(pressed)||region_game_menu_input(pressed)||north_game_menu_input(pressed)||south_game_menu_input(pressed)||magma_game_menu_input(pressed))return;if((pressed&KEY_R)&&journal_tab==0&&(chapter_flags&SAVE4_ENDING_SEEN)){show_scene(CD_ELDER_FINAL,2,0);append_scene(CD_ENDING_FRIENDS);return;}if(pressed&KEY_A)journal_tab=(journal_tab+1)%journal_page_count();if(pressed&KEY_L)quickparty_cycle();if(pressed&(KEY_START|KEY_SELECT|KEY_B)){acknowledge_save_failure();game_state=PLAY;}return;}
 if(game_state==DEAD){if(pressed&KEY_A){game_health_fill();ability_cd=0;heal_cd=0;game_state=PLAY;enter_room(room,room>=16?checkpoint_spawn:2);}return;}
 if(game_state==WIN){if(pressed&KEY_START){game_state=PLAY;enter_room(0,3);}return;}
 ticks++;{int i;for(i=0;i<6;i++)if(impacts[i].life)impacts[i].life--;}if(hitstop){hitstop--;return;}if(pressed&KEY_START){journal_tab=room==1?1:0;game_state=PAUSE;return;}if(area_ticks)area_ticks--;if(invuln)invuln--;if(ability_cd)ability_cd--;if(heal_cd)heal_cd--;if(stone_guard)stone_guard--;advanced_tick();regional_powers_tick();northern_powers_tick();game_geometry_sync();southern_powers_tick();magma_powers_tick();game_combat_tick();if(guard_invuln)guard_invuln--;if(power_effect)power_effect--;if(transition_lock)transition_lock--;if(roll_cd)roll_cd--;
 {int grabbing=magma_game_input((unsigned)pressed,(unsigned)keys);if(grabbing){walk=0;game_attacks_suspend();goto movement_done;}}
 if(pressed&KEY_B){summoned=!summoned;cx=px+14;cy=py;cx_q8=cx*256;cy_q8=cy*256;sfx(2);if(summoned)toast(TX_SUMMONED);}
 if(keys&KEY_LEFT){dx=-1;face=2;}if(keys&KEY_RIGHT){dx=1;face=3;}if(keys&KEY_UP){dy=-1;face=1;}if(keys&KEY_DOWN){dy=1;face=0;}if(swing||weapon_action.phase==WEAPON_WINDUP||weapon_action.phase==WEAPON_ACTIVE)face=weapon_action.direction;walk=dx||dy;if(walk)walk_phase++;
 if((pressed&KEY_SELECT)&&!roll_cd&&(weapon_action.phase==WEAPON_IDLE||weapon_action.phase==WEAPON_CHARGING||(weapon_action.weapon_class==EQUIPMENT_BOW&&weapon_action.phase==WEAPON_WINDUP))){game_attacks_suspend();roll_ticks=12;roll_cd=gear_stats.roll_cooldown;if(advanced_guard_charges){advanced_guard_charges=0;stone_guard=0;}roll_dx=dx;roll_dy=dy;if(!dx&&!dy){roll_dx=face==2?-1:face==3?1:0;roll_dy=face==1?-1:face==0?1:0;}sfx(2);}
 if(roll_ticks){move_player(roll_dx*(roll_dx&&roll_dy?543:768),roll_dy*(roll_dx&&roll_dy?543:768));}else {int speed=advanced_guard_charges?224:gear_stats.speed_q8,diag=advanced_guard_charges?158:gear_stats.diagonal_q8;if(weapon_action.phase==WEAPON_CHARGING){speed=speed*3/4;diag=diag*3/4;}move_player(dx*(dx&&dy?diag:speed),dy*(dx&&dy?diag:speed));}
 game_attack_update(keys,pressed);
 /* A deferred rest must freeze before another hostile simulation update.
  * SaveFrame paints the notice now; proof and snapshot occur on later frames. */
 if(save_requested&&(room==38||room==39)&&magma_game_save_prepare_pending()){save_frame();return;}
 /* An A interaction may have opened dialogue. Do not let a simultaneous R
  * start a cast after the action state has already changed. */
 if(game_state!=PLAY)return;
 if((pressed&KEY_R)&&!roll_ticks)ability();
 if(game_state!=PLAY)return;
 movement_done:
 /* Only these rooms can move physical props after the opening tick.
  * Keep both unconditional pre-tick and pre-draw checks for every area. */
 if(room==15||room==20||(unsigned)(room-38)<8u)game_geometry_sync();
 if(summoned){int tx=(px+(face==2?17:-17))*256,ty=(py+8)*256;cx_q8+=(tx-cx_q8)/6;cy_q8+=(ty-cy_q8)/6;cx=cx_q8>>8;cy=cy_q8>>8;}

 update_shots();game_arrows_update();update_enemies();if(room==3||room==8||room==13)update_boss();region_game_tick();north_game_tick();south_game_tick();magma_game_tick();if(roll_ticks)roll_ticks--;if(game_state!=PLAY)return;
 if(room==6&&!(room_flags&CF_SKY_PATROL_CLEAR)){int i,alive=0;for(i=0;i<MAX_ENEMIES;i++)alive+=enemies[i].hp>0;if(!alive){room_flags|=CF_SKY_PATROL_CLEAR;save_game();show_scene(CD_PATROL_CLEAR,0,0);return;}}
 if(region_game_is_room((unsigned)room)||north_game_is_room((unsigned)room)||south_game_is_room((unsigned)room)||((unsigned)(room-38)<8u)){}
 else if(trials_is_room(room)){int dest=trials_exit(room,px,py);if(!transition_lock&&(keys&KEY_DOWN)&&dest>=0)enter_room(dest,0);}
 else if(room>=4&&room<14){const CampaignRoom*d=&campaign_rooms[room-4];if(!transition_lock&&px>=108&&px<=132){if(py<=39&&(keys&KEY_UP)&&(progress_bits()&d->north_flags)==d->north_flags)enter_room(d->north_room,d->north_spawn);else if(py>=140&&(keys&KEY_DOWN))enter_room(d->south_room,d->south_spawn);}}
 else if(room==1){if(py<=31&&px>=WORLD_TEMPLE_GATE_X&&px<WORLD_TEMPLE_GATE_X+WORLD_TEMPLE_GATE_W)enter_room(2,0);else if(py>=WORLD_VILLAGE_EXIT_Y&&ab(px-WORLD_VILLAGE_EXIT_X)<18)enter_room(0,1);}
 else if(py<=31&&px>100&&px<140){if(room<3)enter_room(room+1,0);else if(room==3&&!boss_active())enter_room(0,3);}else if(py>=149&&px>100&&px<140&&room>0&&room<=3)enter_room(room-1,1);
 camera_update(0);
}
COLD void draw_sword(void){int d=face,phase=13-swing,ox=d==2?-15:d==3?15:0,oy=d==1?-15:d==0?15:0;int x=px+ox,y=py+oy;line(px,py-2,x,y,WHITE);if(d<2){line(x-12+phase,y-3,x+8,y+2,GOLD);line(x-11+phase,y-2,x+8,y+3,CREAM);}else{line(x-3,y-12+phase,x+2,y+8,GOLD);line(x-2,y-11+phase,x+3,y+8,CREAM);} }
/* The world occupies all160 rows. HUD pixels are small transparent OBJ. */
void copy_overworld(void){int y;const u8 *atlas=(camera_x&1)?overworld_bitmap_odd:overworld_bitmap;int sx=camera_x&~1;for(y=0;y<160;y++){REG32(0x040000D4)=(u32)(atlas+(camera_y+y)*WORLD_W+sx);REG32(0x040000D8)=(u32)(screen+y*120);REG32(0x040000DC)=0x80000000|120;}}
void draw_campaign_background(void);
COLD void copy_region(void){const RegionArtRoom*r=&region_art_rooms[room-16];int y;if(r->width==240){REG32(0x040000D4)=(u32)r->bitmap;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}for(y=0;y<160;y++){const u8*src=((camera_x&1)?r->bitmap_odd:r->bitmap)+(camera_y+y)*r->width+camera_x-(camera_x&1);REG32(0x040000D4)=(u32)src;REG32(0x040000D8)=(u32)(screen+y*120);REG32(0x040000DC)=0x80000000|120;}}
COLD void copy_south(void){const SouthArtRoom*r=&south_art_rooms[room-30];int y;if(r->width==240){REG32(0x040000D4)=(u32)r->bitmap;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}for(y=0;y<160;y++){const u8*src=((camera_x&1)?r->bitmap_odd:r->bitmap)+(camera_y+y)*r->width+camera_x-(camera_x&1);REG32(0x040000D4)=(u32)src;REG32(0x040000D8)=(u32)(screen+y*120);REG32(0x040000DC)=0x80000000|120;}}
COLD void copy_magma(void){const MagmaArtRoom*r=&magma_art_rooms[room-38];int y;if(r->width==240){REG32(0x040000D4)=(u32)r->bitmap;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}for(y=0;y<160;y++){const u8*src=((camera_x&1)?r->bitmap_odd:r->bitmap)+(camera_y+y)*r->width+camera_x-(camera_x&1);REG32(0x040000D4)=(u32)src;REG32(0x040000D8)=(u32)(screen+y*120);REG32(0x040000DC)=0x80000000|120;}}
COLD void copy_north(void){const NorthArtRoom*r=&north_art_rooms[room-22];int y;if(r->width==240){REG32(0x040000D4)=(u32)r->bitmap;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}for(y=0;y<160;y++){const u8*src=((camera_x&1)?r->bitmap_odd:r->bitmap)+(camera_y+y)*r->width+camera_x-(camera_x&1);REG32(0x040000D4)=(u32)src;REG32(0x040000D8)=(u32)(screen+y*120);REG32(0x040000DC)=0x80000000|120;}}
COLD void draw_south_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(south_game_name(),35,GOLD);rect(mx,my,120,80,PAL_GOLD2);rect(mx,my+58,120,22,PAL_WATER3);for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;rect(x,y,10,10,(adventure_save.quests.region_flags[2]&(1u<<i))?GOLD:PAL_STONE2);if(room==30+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
COLD void draw_magma_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(magma_game_name(),35,GOLD);rect(mx,my,120,80,PAL_GOLD2);rect(mx,my+58,120,22,PAL_STONE3);for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;rect(x,y,10,10,(adventure_save.quests.region_flags[3]&(1u<<i))?GOLD:PAL_STONE2);if(room==38+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
COLD void draw_north_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(north_game_name(),35,GOLD);rect(mx,my,120,80,PAL_PINE3);rect(mx,my+58,120,22,PAL_WATER3);for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;rect(x,y,10,10,(adventure_save.quests.region_flags[1]&(1u<<i))?GOLD:PAL_STONE2);if(room==22+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
COLD void draw_region_map(void){int i,mx=20,my=62;box(8,31,224,123);centered(region_game_name(),35,GOLD);rect(mx,my,120,80,PAL_PINE3);rect(mx,my+36,120,8,PAL_WATER3);for(i=0;i<6;i++){int x=170+(i&1)*30,y=67+(i/2)*24;rect(x,y,10,10,(adventure_save.quests.region_flags[0]&(1u<<i))?GOLD:PAL_STONE2);if(room==16+i)rect(x-2,y-2,14,2,TEAL);}if(scrolling_room())rect(mx+px/4-1,my+py/4-1,3,3,PAL_HEART);centered(TX_G_NEXT_TAB,140,TEAL);}
void draw_world(void){int i;if(((unsigned)(room-38)<8u)){copy_magma();magma_game_draw_overlay();}
 else if(south_game_is_room((unsigned)room)){copy_south();south_game_draw_overlay();}
 else if(north_game_is_room((unsigned)room)){copy_north();north_game_draw_overlay();}
 else if(region_game_is_room((unsigned)room)){copy_region();region_game_draw_overlay();}
 else if(room==1){copy_overworld();if(bridge_open){int x=WORLD_BRIDGE_X-camera_x,y=WORLD_RIVER_Y-camera_y;rect(x-2,y-2,28,24,PAL_PINE3);for(i=0;i<6;i++){rect(x-1,y-2+i*4,26,3,PAL_WOOD3);rect(x+2,y-2+i*4,20,1,GOLD);}line(x-2,y-4,x-2,y+23,GREEN);line(x+26,y-4,x+26,y+23,GREEN);}}
 else if(trials_is_room(room)){REG32(0x040000D4)=(u32)trials_background(room);REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;}
 else if(room>=4&&room<14){REG32(0x040000D4)=(u32)campaign_backgrounds[room-4];REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;}else copy_bg(room);
 if(room==2){if(torches!=3){rect(99,27,42,13,INK);for(i=101;i<141;i+=6)rect(i,27,2,15,GOLD);}else{rect(108,25,24,9,INK);line(108,33,132,33,GOLD);}}
 if(room>=4&&room<14)draw_campaign_background();
 trials_draw_background(room,camera_x,camera_y);
 if(game_state==PLAY&&area_ticks){int x=(240-ui_texts[room_name()].width)/2;text(room_name(),x+1,23,INK);text(room_name(),x,22,CREAM);}
 if(toast_ticks&&game_state==PLAY){const UiText*t=&ui_texts[toast_id];box((240-t->width-10)/2,143,t->width+10,17);centered(toast_id,143,CREAM);}
}
COLD void draw_map(void){int mx=48,my=56,mw=144,mh=76;box(8,31,224,122);centered(TX_MAP,35,GOLD);rect(mx,my,mw,mh,PAL_PINE3);rect(mx,my+WORLD_RIVER_Y*mh/WORLD_H,mw,6,PAL_WATER3);line(mx+WORLD_SPAWN_X*mw/WORLD_W,my+mh-2,mx+WORLD_BRIDGE_CENTER_X*mw/WORLD_W,my+22,CREAM);line(mx+27,my+22,mx+110,my+22,CREAM);line(mx+110,my+22,mx+110,my+4,CREAM);if(bridge_open)rect(mx+68,my+35,8,10,GOLD);rect(mx+WORLD_CAMP_X*mw/WORLD_W-2,my+WORLD_CAMP_Y*mh/WORLD_H-2,5,5,PAL_FIRE2);rect(mx+WORLD_CHEST_X*mw/WORLD_W-2,my+WORLD_CHEST_Y*mh/WORLD_H-2,5,5,relic_found?PAL_STONE2:GOLD);rect(mx+WORLD_TEMPLE_X*mw/WORLD_W-3,my+WORLD_TEMPLE_Y*mh/WORLD_H-3,7,7,CREAM);rect(mx+px*mw/WORLD_W-2,my+py*mh/WORLD_H-2,5,5,PAL_HEART);centered(TX_MAP_KEYS,136,CREAM);}
/* 5x7 letterforms for an exact-pixel wordmark. */
const u8 alphabet[26][7]={{14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{14,17,16,16,16,17,14},{30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},{14,17,16,23,17,17,15},{17,17,17,31,17,17,17},{31,4,4,4,4,4,31},{7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},{17,27,21,21,17,17,17},{17,25,25,21,19,19,17},{14,17,17,17,17,17,14},{30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},{15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},{17,17,17,17,17,10,4},{17,17,17,21,21,27,17},{17,17,10,4,10,17,17},{17,17,10,4,4,4,4},{31,1,2,4,8,16,31}};
COLD void wordmark(void){const char*s="EMBERBOND";int i,x,y;for(i=0;i<9;i++)for(y=0;y<7;y++)for(x=0;x<5;x++)if(alphabet[s[i]-'A'][y]&(16>>x)){rect(43+i*18+x*3,35+y*3+2,3,3,INK);rect(42+i*18+x*3,35+y*3,3,3,y<3?CREAM:GOLD);}}
COLD void draw_route_map(void){int i;const int names[]={TX_C_MAP_GROVE,TX_C_MAP_SKY,TX_C_MAP_CORE};int selected=room==14?1:room>=9?2:room>=4?1:0;box(8,31,224,122);centered(TX_C_MAP_ROUTE,35,GOLD);line(48,78,192,78,PAL_GOLD2);for(i=0;i<3;i++){int x=48+i*72;rect(x-9,66,18,22,(chapter_flags&(1u<<i))?PAL_GOLD3:PAL_STONE1);rect(x-5,70,10,14,(chapter_flags&(1u<<i))?PAL_FIRE2:PAL_STONE3);if(selected==i){rect(x-12,62,24,2,TEAL);rect(x-12,92,24,2,TEAL);}text(names[i],x-ui_texts[names[i]].width/2,100,CREAM);}centered(TX_C_MAP_RETURN,120,CREAM);centered(TX_C_MAP_NEXT,136,TEAL);}
COLD void draw_companion_journal(void){quickparty_draw_journal();}
COLD int quest_id(void){if(((unsigned)(room-38)<8u))return magma_game_quest_text();if(south_game_is_room((unsigned)room))return south_game_quest_text();if(north_game_is_room((unsigned)room))return north_game_quest_text();if(region_game_is_room((unsigned)room))return region_game_quest_text();if(room==14)return TX_T_WIND_HINT1;if(room==15)return TX_T_STONE_HINT1;if(room<4&&(chapter_flags&SAVE4_CORE_CLEAR))return chapter_flags&SAVE4_ENDING_SEEN?TX_C_QUEST_COMPLETE:TX_C_QUEST_RETURN;if(room<4&&(chapter_flags&SAVE4_SKY_CLEAR))return TX_C_QUEST_ACT3;if(room<4&&(chapter_flags&SAVE4_GROVE_CLEAR))return TX_C_QUEST_ACT2;if(room==0)return TX_QUEST0;if(room==1)return bridge_open?TX_QUEST2:TX_QUEST1;if(room==2)return torches==3?TX_QUEST4:TX_QUEST3;if(room==3)return TX_QUEST5;{const int q[]={TX_C_QUEST_ACT2,TX_C_QUEST_SKY_VANE,TX_C_QUEST_SKY_PATROL,TX_C_QUEST_SKY_RELAY,TX_C_QUEST_SKY_BOSS,TX_C_QUEST_ACT3,TX_C_QUEST_CORE_WEIGHTS,TX_C_QUEST_CORE_ROOTS,TX_C_QUEST_CORE_LAMPS,TX_C_QUEST_CORE_BOSS};return q[room-4];}}
COLD void draw_save_failure_notice(void){if(save_notice_visible()){int left=save_notice_left();box(left,SAVE_NOTICE_Y,240-left*2,SAVE_NOTICE_H);centered(TX_C_SAVE_FAILED,SAVE_NOTICE_Y+2,CREAM);}}
COLD int southern_hint_text(void){unsigned h=southern_powers_hint();return h==SOUTHERN_HINT_OTHER_SIDE?TX_SP_OTHER_SIDE:h==SOUTHERN_HINT_SECOND_TARGET?TX_SP_SECOND_TARGET:0;}
COLD void render_static(void){screen=(u16*)(page?0x0600A000:0x06000000);if(game_state==TITLE||game_state==NEW_GAME_CONFIRM){copy_bg(BACK_TITLE);if(game_state==NEW_GAME_CONFIRM){box(8,50,224,76);centered(TX_NEW_CONFIRM,57,GOLD);centered(TX_NEW_WARNING,80,CREAM);centered(TX_NEW_CHOICE,104,TEAL);}else{wordmark();centered(TX_SUBTITLE,60,CREAM);centered(TX_TAGLINE,84,CREAM);box(43,112,154,36);centered(has_save?TX_CONTINUE:TX_START,114,GOLD);if(has_save)centered(TX_NEW,130,CREAM);else centered(TX_BUILD,132,CREAM);}return;}
 draw_world();if(game_state==PLAY){int hint=magma_powers_hint()==MAGMA_HINT_LANDING?TX_MP_LANDING:southern_hint_text();if(hint){int w=ui_texts[hint].width+12;box((240-w)/2,138,w,19);centered(hint,140,TEAL);}}if(game_state==DIALOG){box(5,99,230,56);text(dialog_speakers[dpage],13,103,GOLD);text(dialog_lines[dpage*2],13,120,CREAM);text(dialog_lines[dpage*2+1],13,136,CREAM);text(TX_NEXT,207,102,GOLD);}
 if(game_state==PAUSE&&journal_tab==1){if(room==1)draw_map();else if(((unsigned)(room-38)<8u))draw_magma_map();else if(south_game_is_room((unsigned)room))draw_south_map();else if(north_game_is_room((unsigned)room))draw_north_map();else if(region_game_is_room((unsigned)room))draw_region_map();else draw_route_map();}
 else if(game_state==PAUSE&&journal_tab==2){draw_companion_journal();}
 else if(game_state==PAUSE&&journal_tab==3){progression_draw_tab();}
 else if(game_state==PAUSE&&journal_tab==4){gear_menu_draw();}
 else if(game_state==PAUSE&&journal_tab==5){region_game_draw_journal();}
 else if(game_state==PAUSE&&journal_tab==6){north_game_draw_journal();}
 else if(game_state==PAUSE&&journal_tab==7){south_game_draw_journal();}
 else if(game_state==PAUSE&&journal_tab==8){magma_game_draw_journal();}
 else if(game_state==PAUSE){box(8,31,224,119);centered(room_name(),35,GOLD);text(quest_id(),16,54,CREAM);text(TX_CONTROL1,16,73,CREAM);text(TX_CONTROL2,16,89,CREAM);text(TX_CONTROL3,16,105,CREAM);centered((chapter_flags&SAVE4_ENDING_SEEN)?TX_C_ENDING_REPLAY:TX_ROLL_CONTROL,127,TEAL);}
 if(quickparty_open)quickparty_draw();
 if(game_state==SAVE_PENDING){box(37,77,166,34);centered(TX_E_SAVING,85,GOLD);}
 if(game_state==EVOLVE_CONFIRM)progression_draw_confirm();
 if(game_state==EVOLVE_ANIM)progression_draw_evolution();
 if(game_state==DEAD){box(22,60,196,57);centered(TX_DEAD,69,GOLD);centered(TX_RETRY,94,CREAM);}
 if(game_state==WIN){copy_bg(BACK_TITLE);box(17,40,206,103);centered(TX_COMPLETE,49,GOLD);centered(TX_THANKS,75,CREAM);centered(TX_C_POSTGAME,122,CREAM);centered(TX_C_FINAL_SMALL,149,GOLD);}
 draw_save_failure_notice();}
int boss_banner(void){if(room==3)return boss_armor?TX_EXPOSED:TX_ARMORED;if(boss_state==5)return TX_C_BOSS_EXPOSED;if(room==8)return boss_state==4?TX_C_WIND_WINDOW:TX_C_BOSS_WARN;if(boss_state==6)return TX_C_PHASE_CHANGE;if(boss_state!=4)return TX_C_BOSS_WARN;return boss_phase==0?TX_C_NEED_STONE:boss_phase==1?TX_C_NEED_WIND:TX_C_NEED_FIRE;}
void render(void){game_geometry_sync();u32 key[CACHE_FIELDS]={room,game_state,spirit,summoned,bridge_open,torches,dpage,game_state==PLAY&&toast_ticks>0,game_state==PLAY?toast_id:0,has_save,journal_tab,room_flags,chapter_flags,optional_flags,game_state==DIALOG?dialog_lines[dpage*2]:-1,game_state==DIALOG?dialog_lines[dpage*2+1]:-1,game_state==DIALOG?dialog_speakers[dpage]:-1,scrolling_room()?camera_x:0,scrolling_room()?camera_y:0,progression_revision,area_ticks>0,quickparty_revision,save_notice_visible(),gear_menu_revision,region_game_revision,north_game_revision,south_game_revision,game_state==PLAY?southern_powers_hint():0,magma_game_revision,game_state==PLAY?magma_powers_hint():0};int i,changed=!cache_valid[page],world_changed=!cache_valid[page],other=page^1,reusable=quickparty_open&&cache_valid[page^1];
 screen=(u16*)(page?0x0600A000:0x06000000);for(i=0;i<CACHE_FIELDS;i++){if(cache_fields[page][i]!=key[i]){changed=1;if(i!=21)world_changed=1;}if(i!=21&&cache_fields[other][i]!=key[i])reusable=0;}
 /* Picker-only changes cannot alter the frozen world. A moving camera may
  * leave this back page stale; reuse the other bitmap ONLY when every world
  * key matches. The opaque picker repaints any prior picker pixels. */
 if(changed){if(quickparty_open&&(!world_changed||reusable)){if(world_changed){REG32(0x040000D4)=other?0x0600A000:0x06000000;REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;}quickparty_draw();}else render_static();cached_armor[page]=-1;cache_valid[page]=1;for(i=0;i<CACHE_FIELDS;i++)cache_fields[page][i]=key[i];}
 if(game_state==PLAY&&!quickparty_open&&boss_active()){rect(57,153,126,5,INK);rect(59,154,boss_hp_q4*120/(boss_hp_max*16),3,boss_armor?GOLD:GREEN);}
 draw_actors();
}
/* Campaign content: monotonic puzzles, explicit power dispatch and boss FSMs. */
int campaign_interact(void){int i;if(room==0){
 if(!transition_lock&&(chapter_flags&SAVE4_GROVE_CLEAR)&&near(px,py,196,128,24)){enter_room(4,0);return 1;}
 if(!transition_lock&&(chapter_flags&SAVE4_SKY_CLEAR)&&near(px,py,80,128,24)){enter_room(9,0);return 1;}
 if(near(px,py,120,94,29)){game_health_fill();save_game();
  if((chapter_flags&SAVE4_CORE_CLEAR)&&!(chapter_flags&SAVE4_ENDING_SEEN)){show_scene(CD_ELDER_FINAL,2,0);append_scene(CD_ENDING_FRIENDS);}
  else {show_scene(chapter_flags&SAVE4_ENDING_SEEN?CD_ELDER_POSTGAME:chapter_flags&SAVE4_SKY_CLEAR?CD_ELDER_ACT3:chapter_flags&SAVE4_GROVE_CLEAR?CD_ELDER_ACT2:CD_ELDER_ACT1,0,0);if((optional_flags&SAVE4_RIDGE_CHIME)&&!(story_seen&SAVE4_SEEN_CHIME)){append_scene(CD_ELDER_CHIME);dialogue_seen|=SAVE4_SEEN_CHIME;}}
  return 1;}
 }
 if(room==3&&!boss_active()&&near(px,py,boss_x,boss_y,34)){show_scene(CD_GROVE_POSTCLEAR,0,0);return 1;}
 if(room>=4&&room<14){const CampaignRoom*d=&campaign_rooms[room-4];for(i=0;i<d->object_count;i++){const CampaignObject*o=&d->objects[i];if(o->input!=1||!near(px,py,o->x,o->y,o->range))continue;if(o->kind==CAM_PROP_SIGN){int j,close=0;for(j=0;j<MAX_ENEMIES;j++)if(enemies[j].hp&&near(px,py,enemies[j].x,enemies[j].y,44))close=1;if(close)continue;}if(o->kind==CAM_PROP_REST){game_health_fill();save_game();}if(o->dialogue>=0)show_scene(o->dialogue,0,0);else toast(TX_HEALED);return 1;}}
 return 0;
}
void boss_set_state(int state){boss_state=state;boss_state_ticks=0;if(state!=5)boss_armor=0;if(state==0||state==2){boss_aimx=px;boss_aimy=py;}hazard_mode=0;}
void boss_expose(void){boss_set_state(5);boss_armor=180;boss_flash=10;zero(shots,sizeof shots);toast(TX_C_BOSS_EXPOSED);}
int campaign_power(void){int i,nearest=-1,dist=999,wrong=0;unsigned pr=progress_bits();
 if(room>=4&&room<14){const CampaignRoom*d=&campaign_rooms[room-4];for(i=0;i<d->object_count;i++){const CampaignObject*o=&d->objects[i];int q=ab(px-o->x)+ab(py-o->y);if(o->input!=2||q>o->range)continue;if(o->set&&(pr&o->set)==o->set)continue;if(o->optional&&(optional_flags&o->optional))continue;if(o->power==spirit&&q<dist){nearest=i;dist=q;}else wrong=1;}
  if(nearest>=0){const CampaignObject*o=&d->objects[nearest];if((pr&o->requires)!=o->requires){toast(TX_C_NEED_WELL);return 1;}room_flags|=o->set;optional_flags|=o->optional;save_game();gfx_props_room=-1;
   if(room==7&&(room_flags&(CF_RELAY_LEFT|CF_RELAY_RIGHT|CF_RELAY_FIRE))==(CF_RELAY_LEFT|CF_RELAY_RIGHT|CF_RELAY_FIRE))show_scene(CD_RELAY_COMPLETE,0,0);
   else if(room==12&&(room_flags&0xF000)==0xF000)show_scene(CD_FOUR_LIGHTS,0,0);
   else if(o->dialogue>=0)show_scene(o->dialogue,0,0);else if(!save_failed)toast(TX_SAVED);
   return 1;}
  if(wrong){toast(TX_C_POWER_MISMATCH);return 1;}
 }
 if((room==8||room==13)&&boss_active()&&boss_state==4&&near(px,py,boss_x,boss_y,64)){
  int required=room==8?2:boss_phase==0?3:boss_phase==1?2:0;
  if(spirit==required){boss_expose();return 1;}toast(TX_C_POWER_MISMATCH);
 }
 if(progression_command()>4&&(spirit==2||spirit==3)&&advanced_power(progression_command()))return 1;
 if(spirit==2){power_effect=14;for(i=0;i<12;i++)if(shots[i].life&&shots[i].owner){int dx=shots[i].x-px,dy=shots[i].y-py,f=face==2?-dx:face==3?dx:face==1?-dy:dy,side=face<2?dx:dy;if(f>=-8&&f<=56&&ab(side)<=24)shots[i].life=0;}
  for(i=0;i<MAX_ENEMIES;i++)if(enemies[i].hp){Enemy*e=&enemies[i];int dx=e->x-px,dy=e->y-py,f=face==2?-dx:face==3?dx:face==1?-dy:dy,side=face<2?dx:dy;if(f>=-8&&f<=56&&ab(side)<=24){int nx=e->x+(face==2?-6:face==3?6:0),ny=e->y+(face==1?-6:face==0?6:0);e->flash=45;enemy_windups[i]=0;if(!solid(nx,ny)){e->x=nx;e->y=ny;}}}
  return 1;}
 if(spirit==3){advanced_guard_charges=0;stone_guard=36;power_effect=14;for(i=0;i<MAX_ENEMIES;i++)if(enemies[i].hp&&near(px,py,enemies[i].x,enemies[i].y,32)){game_enemy_hurt((unsigned)i,16,0,CREATURE_EARTH);enemies[i].flash=30;enemy_windups[i]=0;if(enemies[i].hp<=0)kill_enemy(&enemies[i]);}return 1;}
 return 0;
}
COLD void boss_reward(void){zero(shots,sizeof shots);zero(impacts,sizeof impacts);hazard_mode=0;game_health_fill();game_boss_health_set(0);
 if(room==3){chapter_flags|=SAVE4_GROVE_CLEAR;progression_story();save_at(0,3);show_scene(CD_GROVE_CLEAR,1,SAVE4_SEEN_WIND_JOIN);append_scene(CD_WIND_JOIN);}
 else if(room==8){chapter_flags|=SAVE4_SKY_CLEAR;progression_story();save_at(0,3);show_scene(CD_SKY_BOSS_CLEAR,1,SAVE4_SEEN_STONE_JOIN|SAVE4_SEEN_WIND_JOIN);append_scene(CD_STONE_JOIN);}
 else {chapter_flags|=SAVE4_CORE_CLEAR;progression_story();save_at(0,3);show_scene(CD_CORE_RELEASE,1,SAVE4_SEEN_CORE_RELEASE);}
}
void fire_fan(int count){static const int vx[8]={2,2,0,-2,-2,-2,0,2},vy[8]={0,2,2,2,0,-2,-2,-2};int dx=boss_aimx-boss_x,dy=boss_aimy-boss_y,dir,i;if(ab(dx)>ab(dy)*2)dir=dx>=0?0:4;else if(ab(dy)>ab(dx)*2)dir=dy>=0?2:6;else dir=dy>=0?(dx>=0?1:3):(dx>=0?7:5);for(i=-count/2;i<=count/2;i++){int a=(dir+i+8)&7;fire_shot(boss_x,boss_y,vx[a],vy[a],1);}}
int in_rect(int x,int y,int w,int h){return px>=x&&px<x+w&&py>=y&&py<y+h;}
void campaign_boss_update(void){int t;if(room==13&&boss_state==5&&boss_phase<2&&boss_hp_q4<=(16-boss_phase*8)*16){game_boss_health_set((unsigned)(16-boss_phase*8));boss_phase++;boss_pattern=0;boss_set_state(6);zero(shots,sizeof shots);ability_cd=0;return;}boss_time++;boss_state_ticks++;t=boss_state_ticks;if(boss_flash)boss_flash--;
 if(boss_state==5){boss_armor=180-t;if(!boss_flash&&game_melee_hit(6,boss_x,boss_y,1)){game_boss_hurt(weapon_action.damage_q4==48?32:16,weapon_action.attack_q4,weapon_action.element);boss_flash=16;hitstop=3;impact(boss_x,boss_y);sfx(4);
   if(boss_hp<=0){boss_hp=0;boss_reward();return;}
   if(room==13&&boss_phase<2&&boss_hp<=16-boss_phase*8){game_boss_health_set((unsigned)(16-boss_phase*8));boss_phase++;boss_pattern=0;boss_set_state(6);zero(shots,sizeof shots);ability_cd=0;return;}}
  if(t>=30&&ab(px-boss_x)<20&&ab(py-boss_y)<20)damage();
  if(t>=180){boss_pattern++;boss_set_state(0);}return;}
 boss_armor=0;
 if(boss_state==6){if(t>=45)boss_set_state(0);return;}
 if(room==8){
  if(boss_state==0){if(t==1){boss_aimx=px;boss_aimy=py;}if(t>=36)boss_set_state(1);}
  else if(boss_state==1){if(t==1||(boss_hp<=10&&t==18))fire_fan(3);if(t>=36)boss_set_state(2);}
  else if(boss_state==2){if(t>=45){int dx=boss_aimx-boss_x,dy=boss_aimy-boss_y,m=(ab(dx)>ab(dy)?ab(dx)+ab(dy)/2:ab(dy)+ab(dx)/2);if(!m)m=1;boss_dx=dx*512/m;boss_dy=dy*512/m;boss_set_state(3);}}
  else if(boss_state==3){int nx=boss_x+boss_dx/256,ny=boss_y+boss_dy/256;if(nx<40)nx=40;if(nx>200)nx=200;if(ny<52)ny=52;if(ny>124)ny=124;boss_x=nx;boss_y=ny;if(t>=32||near(boss_x,boss_y,boss_aimx,boss_aimy,5))boss_set_state(4);}
  else if(boss_state==4&&t>=90)boss_set_state(0);
 }else {
  if(boss_state==0){
   if(boss_phase==0||(boss_phase==2&&(boss_pattern&1))){if(t<36)hazard_mode=1;else if(t<44){hazard_mode=2;if(in_rect(16,96,208,12))damage();}else if(t<68)hazard_mode=0;else if(t<104)hazard_mode=3;else if(t<112){hazard_mode=4;if(in_rect(16,120,208,12))damage();}else boss_set_state(4);}
   else if(boss_phase==1){if(t==1){boss_aimx=px;boss_aimy=py;}hazard_mode=t<36?5:0;if(t==36)fire_fan(5);if(t>=72)boss_set_state(4);}
   else {if(t<36)hazard_mode=6;else if(t<46){hazard_mode=7;if(in_rect(56,44,16,92)||in_rect(168,44,16,92))damage();}else boss_set_state(4);}
  }else if(boss_state==4&&t>=120){boss_pattern++;boss_set_state(0);}
 }
 if(ab(px-boss_x)<20&&ab(py-boss_y)<20)damage();
}
void refresh_campaign_props(void){unsigned pr=progress_bits()|(optional_flags<<24)|((unsigned)boss_phase<<20)|((unsigned)(boss_state==4)<<22);int i;if(gfx_props_room==room&&gfx_props_progress==pr)return;gfx_props_room=room;gfx_props_progress=pr;
 if(room==0){obj_upload(campaign_prop_data[CAM_PROP_SIGN][1],16,16,OBJ_PROP);obj_upload(campaign_prop_data[CAM_PROP_STONE][1],16,16,OBJ_PROP+256);return;}
 if(room==8)obj_upload(campaign_prop_data[CAM_PROP_WIND][boss_state==4],16,16,OBJ_PROP+5*256);
 if(room==13)obj_upload(campaign_prop_data[boss_phase==0?CAM_PROP_STONE:boss_phase==1?CAM_PROP_WIND:CAM_PROP_FIRE][boss_state==4],16,16,OBJ_PROP+5*256);
 if(room>=4&&room<14){const CampaignRoom*d=&campaign_rooms[room-4];for(i=0;i<d->object_count;i++){const CampaignObject*o=&d->objects[i];int lit=o->lit?((progress_bits()&o->lit)==o->lit):o->optional?(optional_flags&o->optional)!=0:o->kind==CAM_PROP_REST;obj_upload(campaign_prop_data[o->kind][lit],16,16,OBJ_PROP+i*256);}}
}
void draw_campaign_actors(void){int i;unsigned pr=progress_bits();refresh_campaign_props();
 if(room==0){if(chapter_flags&SAVE4_GROVE_CLEAR){obj_add(OBJ_PROP,188,120,16,16,1,128,0);if(game_state==PLAY&&near(px,py,196,128,24))obj_add(OBJ_HINT,192,107,8,8,1,999,0);}if(chapter_flags&SAVE4_SKY_CLEAR){obj_add(OBJ_PROP+256,72,120,16,16,1,128,0);if(game_state==PLAY&&near(px,py,80,128,24))obj_add(OBJ_HINT,76,107,8,8,1,999,0);}if(optional_flags&SAVE4_RIDGE_CHIME){obj_add(OBJ_SPARK,98,68,8,8,1,90,0);obj_add(OBJ_SPARK,137,68,8,8,1,90,0);}}
 if(room>=4&&room<14){const CampaignRoom*d=&campaign_rooms[room-4];for(i=0;i<d->object_count;i++){const CampaignObject*o=&d->objects[i];if(o->visible&&(pr&o->visible)!=o->visible)continue;if(o->hide_done&&o->set&&(pr&o->set)==o->set)continue;obj_add(OBJ_PROP+i*256,o->x-8,o->y-8,16,16,1,o->y,0);if(game_state==PLAY&&o->input==1&&near(px,py,o->x,o->y,o->range))obj_add(OBJ_HINT,o->x-4,o->y-21,8,8,1,999,0);}}
 if(game_state!=PLAY)return;
 if(stone_guard){for(i=0;i<4;i++)obj_add(OBJ_ARMOR,px+(i&1?11:-15),py+(i&2?8:-12),8,8,1,py+1,0);}
 if(power_effect&&spirit==2){for(i=1;i<5;i++)obj_add(OBJ_SPARK,px+(face==2?-i*10:face==3?i*10:0)-4,py+(face==1?-i*10:face==0?i*10:0)-4,8,8,1,py+1,0);}
 if(room==8&&boss_active()){if(boss_state==0||boss_state==2){for(i=1;i<5;i++)obj_add(OBJ_SPARK,boss_x+(boss_aimx-boss_x)*i/5-4,boss_y+(boss_aimy-boss_y)*i/5-4,8,8,1,150,0);}if(boss_state!=5)obj_add(OBJ_PROP+5*256,boss_x-8,boss_y-31,16,16,1,150,0);}
 if(room==13&&boss_active()){
  if(hazard_mode>=1&&hazard_mode<=4){int y=hazard_mode<=2?96:120,off=(hazard_mode&1)?OBJ_WARN:OBJ_HAZARD;for(i=0;i<7;i++)obj_add(off,16+(i==6?176:i*29),y,32,8,1,160,0);}
  else if(hazard_mode==5){for(i=1;i<5;i++)obj_add(OBJ_SPARK,boss_x+(boss_aimx-boss_x)*i/5-4,boss_y+(boss_aimy-boss_y)*i/5-4,8,8,1,150,0);}
  else if(hazard_mode==6||hazard_mode==7){for(i=0;i<12;i++){int y=44+(i==11?84:i*8);obj_add(hazard_mode==6?OBJ_WARN:OBJ_HAZARD,56,y,16,8,1,160,0);obj_add(hazard_mode==6?OBJ_WARN:OBJ_HAZARD,168,y,16,8,1,160,0);}}
  if(boss_state!=5)obj_add(OBJ_PROP+5*256,boss_x-8,boss_y-31,16,16,1,150,0);
 }
}
void draw_campaign_background(void){const CampaignRoom*d=&campaign_rooms[room-4];unsigned pr=progress_bits();int i,j;for(i=0;i<d->block_count;i++){const CampaignBlock*b=&d->blocks[i];int open=(pr&b->flags)==b->flags;if(!open){if((room==5&&i==0)||(room==11&&b->y==84))continue;rect(b->x,b->y,b->w,b->h,PAL_STONE0);for(j=b->x+2;j<b->x+b->w;j+=6)rect(j,b->y,2,b->h,GOLD);}
 else if((room==5&&i==0)||(room==11&&b->y==84)){rect(b->x,b->y,b->w,b->h,PAL_WOOD3);for(j=b->y;j<b->y+b->h;j+=4)rect(b->x,j,b->w,2,CREAM);}}
}

unsigned int cycle_now(void){u16 hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return ((u32)hi<<16)|lo;}
int main(void){int i;REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;for(i=0;i<256;i++)((volatile u16*)0x05000000)[i]=game_palette[i];REG16(0x04000020)=256;REG16(0x04000026)=256;REG16(0x04000022)=0;REG16(0x04000024)=0;REG32(0x04000028)=0;REG32(0x0400002C)=0;page=0;has_save=check_save();game_state=TITLE;sound_init();obj_init();REG16(0x0400000C)=3;REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;while(1){u32 started=cycle_now();keys=(~REG16(0x04000130))&1023;pressed=keys&~prev_keys;prev_keys=keys;update();save_frame();render();render_cycles=cycle_now()-started;if(render_cycles>worst_render_cycles)worst_render_cycles=render_cycles;while(REG16(0x04000006)>=160){}while(REG16(0x04000006)<160){}obj_commit();REG16(0x04000050)=0x00FF;REG16(0x04000054)=transition;REG16(0x04000000)=0x1444|(page?0x10:0);page^=1;}return 0;}
