#include "gear_runtime.h"
#include "gear_menu.h"
#include "combat_rules.h"
#include "progression.h"
#include "assets.h"
#include "obj_layout.h"
#include "regional_powers.h"
#include "northern_powers.h"
#include "southern_powers.h"
#include "north_game.h"
#include "south_game.h"
#include "magma_game.h"
#include "magma_powers.h"
typedef unsigned char u8;
typedef struct {int x,y,hp,flash,kind;} Enemy;
typedef struct {int x,y,dx,dy,life,owner;} Shot;
extern Shot shots[12];
extern Enemy enemies[6];
extern volatile int hp,max_hp,px,py,boss_hp,boss_x,boss_y,room;
extern int keys,gfx_slash_frame,face,roll_ticks,swing,sword_cd,combo_step,combo_timer,attack_buffer,swing_damage,slash_id,hitstop,boss_flash,boss_armor;
extern int solid(int,int),near(int,int,int,int,int),boss_active(void),try_interaction(void);
extern void move_player(int,int),sfx(int),impact(int,int),kill_enemy(Enemy*);
extern void obj_upload(const u8*,int,int,int),obj_add(int,int,int,int,int,int,int,int);
extern int region_game_practice_hit(unsigned,int,int);
EquipmentStats gear_stats;
WeaponAttack weapon_action;
WeaponArrow player_arrows[2];
int hero_hp_q4,enemy_hp_q4[6],boss_hp_q4;
unsigned char enemy_phases[6],enemy_stagger_ticks[6];
static int health_code=-1,partial_code=-1,cap_code=-1,weapon_code=-1,arrow_direction[2]={-1,-1},phase_icons_ready;
static void init_phase_icons(void);
static u8 weapon_pixels[1024];
#define OBJ_PARTIAL_HEART GFX_OBJ_HEART_PARTIAL
#define OBJ_CAP_HEART GFX_OBJ_HEART_CAP
#define OBJ_PLAYER_ARROW GFX_OBJ_PLAYER_ARROW
#define OBJ_WEAPON 7424
#define OBJ_PHASE_ICONS GFX_OBJ_PHASE_ICONS
static unsigned magma_melee_token,magma_arrow_tokens[2];
static unsigned live_arrows(void){return !!player_arrows[0].active+!!player_arrows[1].active;}
unsigned game_weapon_class(void){return gear_stats.weapon_class;}
unsigned game_power_cooldown(unsigned base){unsigned reduction=EQUIPMENT_BASE_POWER_COOLDOWN-gear_stats.power_cooldown;return base>reduction?base-reduction:1;}
unsigned game_gear_base_hp(void){return (unsigned)max_hp*16u;}
unsigned game_gear_hp(void){return (unsigned)hero_hp_q4;}
unsigned game_gear_busy(void){unsigned i,busy=weapon_action_busy(&weapon_action,live_arrows())|(roll_ticks?EQUIPMENT_BUSY_ROLLING:0);for(i=0;i<12;i++)if(shots[i].life&&!shots[i].owner)busy|=EQUIPMENT_BUSY_PLAYER_PROJECTILE;if((regional_power_kind==11&&regional_power_time)||northern_powers_busy()||southern_powers_busy()||magma_powers_busy())busy|=EQUIPMENT_BUSY_PLAYER_PROJECTILE;return busy;}
void game_health_refresh(int fill){
    if(!equipment_derive(&adventure_save.equipment,game_gear_base_hp(),&gear_stats))return;
    if(fill||hero_hp_q4>gear_stats.max_hp_q4)hero_hp_q4=gear_stats.max_hp_q4;
    if(hero_hp_q4<0)hero_hp_q4=0;
    hp=(hero_hp_q4+15)/16;health_code=-1;
}
void game_gear_apply(unsigned clamped){hero_hp_q4=(int)clamped;game_health_refresh(0);gfx_slash_frame=-1;weapon_code=-1;}
void game_health_fill(void){if(!gear_stats.max_hp_q4){game_health_refresh(1);return;}hero_hp_q4=gear_stats.max_hp_q4;hp=(hero_hp_q4+15)/16;}
void game_health_heal(unsigned amount){
    if(amount>(unsigned)(gear_stats.max_hp_q4-hero_hp_q4))amount=(unsigned)(gear_stats.max_hp_q4-hero_hp_q4);
    hero_hp_q4+=(int)amount;hp=(hero_hp_q4+15)/16;
}
void game_health_hurt(unsigned base,unsigned phase){
    unsigned n=combat_damage_q4(base,0,gear_stats.defense_q4,phase,COMBAT_NEUTRAL_PHASE,0);
    hero_hp_q4=hero_hp_q4>(int)n?hero_hp_q4-(int)n:0;hp=(hero_hp_q4+15)/16;
}
void game_enemy_health_reset(void){unsigned i;for(i=0;i<6;i++){enemy_hp_q4[i]=enemies[i].hp*16;enemy_phases[i]=COMBAT_NEUTRAL_PHASE;enemy_stagger_ticks[i]=0;}}
void game_combat_tick(void){unsigned i;for(i=0;i<6;i++)if(enemy_stagger_ticks[i])enemy_stagger_ticks[i]--;}
void game_enemy_stagger(unsigned i,unsigned bonus){if(i<6&&bonus&&bonus<=3){unsigned duration=16+bonus*8;if(enemy_stagger_ticks[i]<duration)enemy_stagger_ticks[i]=(unsigned char)duration;}}
void game_enemy_hurt(unsigned i,unsigned base,unsigned attack,unsigned phase){
    unsigned n;if(i>=6||!enemies[i].hp)return;
    n=combat_damage_q4(base,attack,0,phase,enemy_phases[i],0);
    enemy_hp_q4[i]=enemy_hp_q4[i]>(int)n?enemy_hp_q4[i]-(int)n:0;
    enemies[i].hp=(enemy_hp_q4[i]+15)/16;
}
void game_boss_health_set(unsigned hearts){boss_hp_q4=(int)hearts*16;boss_hp=(int)hearts;}
void game_boss_hurt(unsigned base,unsigned attack,unsigned phase){
    unsigned n=combat_damage_q4(base,attack,0,phase,COMBAT_NEUTRAL_PHASE,0);
    boss_hp_q4=boss_hp_q4>(int)n?boss_hp_q4-(int)n:0;boss_hp=(boss_hp_q4+15)/16;
}
unsigned game_companion_phase(void){CreatureInstance*c=progression_selected();const CreatureForm*f=c?creatures_form(c->form_id):0;return f?f->phase:COMBAT_NEUTRAL_PHASE;}
void game_attacks_reset(void){unsigned i;weapon_action_init(&weapon_action);for(i=0;i<2;i++){player_arrows[i].active=0;magma_arrow_tokens[i]=0;}magma_melee_token=0;weapon_code=-1;if(!phase_icons_ready){init_phase_icons();phase_icons_ready=1;}swing=sword_cd=attack_buffer=combo_step=combo_timer=0;}
void game_attacks_suspend(void){weapon_action_suspend(&weapon_action);if(!(keys&1))weapon_action.suppress_until_release=0;attack_buffer=0;}
static int clear_path(int x,int y,int tx,int ty){int dx=tx-x,dy=ty-y,sx=dx<0?-1:1,sy=dy<0?-1:1,err,e2;if(dx<0)dx=-dx;if(dy<0)dy=-dy;err=dx-dy;while(x!=tx||y!=ty){e2=err*2;if(e2>-dy){err-=dy;x+=sx;}if(e2<dx){err+=dx;y+=sy;}if(solid(x,y))return 0;}return 1;}
static int chapter_target(int*x,int*y,int*r){return north_game_target(x,y,r)||south_game_target(x,y,r)||magma_game_target(x,y,r);}
static int chapter_hit(unsigned c,int x,int y,unsigned d,unsigned channel,unsigned token){return north_game_weapon_hit(c,x,y,d)||south_game_weapon_hit(c,x,y,d)||magma_game_weapon_hit(c,x,y,d,channel,token);}
void game_attack_update(int held,int pressed){
    unsigned event,i;const EquipmentWeapon*w;
    if(roll_ticks)return;
    if((pressed&1)&&!weapon_action.suppress_until_release&&weapon_action.phase==WEAPON_IDLE&&try_interaction()){game_attacks_suspend();return;}
    event=weapon_action_tick(&weapon_action,&gear_stats,(unsigned)face,!!(held&1),!!(pressed&1),live_arrows());
    w=&equipment_weapons[weapon_action.weapon_class];
    if(event&WEAPON_EVENT_START){slash_id++;if(weapon_action.weapon_class!=EQUIPMENT_BOW)magma_melee_token=magma_game_action_begin(0);if(weapon_action.weapon_class!=EQUIPMENT_BOW){int d=weapon_action.direction;move_player(d==2?-(int)w->lunge_q8:d==3?(int)w->lunge_q8:0,d==1?-(int)w->lunge_q8:d==0?(int)w->lunge_q8:0);sfx(1);}}
    if(event&WEAPON_EVENT_ARROW)for(i=0;i<2;i++)if(!player_arrows[i].active&&weapon_arrow_spawn(&player_arrows[i],&weapon_action,px,py)){magma_arrow_tokens[i]=magma_game_action_begin(i+1);sfx(1);break;}
    if(event&WEAPON_EVENT_ACTIVE){int tx=440,ty=280;if(room==16&&weapon_action_contains(&weapon_action,px,py,tx,ty)&&clear_path(px,py,tx,ty)&&weapon_action_mark_hit(&weapon_action,7))region_game_practice_hit(weapon_action.weapon_class,tx,ty);}
    if(event&WEAPON_EVENT_ACTIVE){int tx,ty,radius;if(chapter_target(&tx,&ty,&radius)&&game_melee_hit(8,tx,ty,1)){
        unsigned damage=combat_damage_q4(weapon_action.damage_q4,weapon_action.attack_q4,0,weapon_action.element,COMBAT_NEUTRAL_PHASE,0);
        if(chapter_hit(weapon_action.weapon_class,tx,ty,damage,0,magma_melee_token)){hitstop=3;impact(tx,ty);sfx(4);}
    }}
    combo_step=weapon_action.combo;combo_timer=weapon_action.combo_clock;attack_buffer=weapon_action.buffer;swing_damage=weapon_action.damage_q4/16;
    swing=weapon_action.phase&&weapon_action.weapon_class==EQUIPMENT_SWORD&&weapon_action.age<13?13-weapon_action.age:0;
    sword_cd=weapon_action.phase?1:0;
}
int game_melee_hit(unsigned target,int x,int y,int boss){
    int inside;if(!weapon_action_can_hit(&weapon_action,target))return 0;
    inside=weapon_action_contains(&weapon_action,px,py,x,y);
    if(boss&&weapon_action.weapon_class==EQUIPMENT_SWORD){int dx=x-px,dy=y-py,f=weapon_action.direction==0?dy:weapon_action.direction==1?-dy:weapon_action.direction==2?-dx:dx;if(dx<0)dx=-dx;if(dy<0)dy=-dy;inside=dx+dy<=38+gear_stats.reach_px&&f>=-6;}
    if(!inside||!clear_path(px,py,x,y))return 0;
    return weapon_action_mark_hit(&weapon_action,target);
}
static int arrow_solid(void*context,int x,int y){(void)context;return solid(x,y);}
static int arrow_target(void*context,int x,int y){
    WeaponArrow*a=(WeaponArrow*)context;unsigned i;
    if(room==16&&near(x,y,440,280,9)){region_game_practice_hit(EQUIPMENT_BOW,440,280);return 1;}
    for(i=0;i<6;i++)if(enemies[i].hp&&near(x,y,enemies[i].x,enemies[i].y,10)&&clear_path(x,y,enemies[i].x,enemies[i].y)){
        game_enemy_hurt(i,a->damage_q4,a->attack_q4,a->element);southern_powers_weapon_hit(i);game_enemy_stagger(i,a->stagger);enemies[i].flash=16;impact(x,y);sfx(4);
        if(!enemies[i].hp)kill_enemy(&enemies[i]);
        return 1;
    }
    {int tx,ty,radius;if(chapter_target(&tx,&ty,&radius)&&near(x,y,tx,ty,radius)&&clear_path(x,y,tx,ty)){
        unsigned damage=combat_damage_q4(a->damage_q4,a->attack_q4,0,a->element,COMBAT_NEUTRAL_PHASE,0);
        if(chapter_hit(EQUIPMENT_BOW,tx,ty,damage,(unsigned)(a-player_arrows)+1,magma_arrow_tokens[a-player_arrows])){impact(tx,ty);sfx(4);}return 1;
    }}
    if(boss_active()&&near(x,y,boss_x,boss_y,20)&&clear_path(x,y,boss_x,boss_y)){
        if(boss_armor&&!boss_flash){game_boss_hurt(a->damage_q4==48?32:16,a->attack_q4,a->element);boss_flash=16;impact(x,y);sfx(4);}return 1;
    }
    return 0;
}
void game_arrows_update(void){unsigned i;for(i=0;i<2;i++)if(player_arrows[i].active)weapon_arrow_tick(&player_arrows[i],arrow_solid,arrow_target,&player_arrows[i]);}
static void partial_heart(unsigned amount,unsigned capacity,u8*out){unsigned x,y;for(y=0;y<16;y++)for(x=0;x<16;x++){
    unsigned i=y*16+x;u8 full=sprite_data[SPR_HEART_FULL][i],empty=sprite_data[SPR_HEART_EMPTY][i];
    /* Original heart is x2..12. Keep its outline for available capacity only. */
    unsigned column=x>1?x-1:0;
    out[i]=column>=capacity?0:column<amount?full:empty;
}}
void game_draw_health(void){
    unsigned i,cap=gear_stats.max_hp_q4,full=(unsigned)hero_hp_q4/16,rem=(unsigned)hero_hp_q4&15,last=cap/16,caprem=cap&15;
    int code=hero_hp_q4+(int)cap*256;
    if(code!=health_code){u8 pixels[256];int capfill=full==last?(int)rem:0,capkey=(int)caprem*32+capfill;
     if(rem&&(full!=last||!caprem)&&partial_code!=(int)rem){partial_heart(rem,16,pixels);obj_upload(pixels,16,16,OBJ_PARTIAL_HEART);partial_code=(int)rem;}
     if(caprem&&cap_code!=capkey){partial_heart((unsigned)capfill,caprem,pixels);obj_upload(pixels,16,16,OBJ_CAP_HEART);cap_code=capkey;}
     health_code=code;
    }
    for(i=0;i<(cap+15)/16;i++){int off=i<full?SPR_HEART_FULL*256:i==full&&rem?OBJ_PARTIAL_HEART:SPR_HEART_EMPTY*256;if(i==last&&caprem)off=OBJ_CAP_HEART;obj_add(off,3+(int)i*9,3,16,16,0,9999,0);}
}
static void wpixel(int x,int y,u8 c){if((unsigned)x<32&&(unsigned)y<32)weapon_pixels[y*32+x]=c;}
static void axis_pixel(int forward,int side,unsigned dir,u8 c){int x=16,y=16;if(dir==0){x+=side;y+=forward;}else if(dir==1){x-=side;y-=forward;}else if(dir==2){x-=forward;y+=side;}else{x+=forward;y-=side;}wpixel(x,y,c);}
void game_draw_weapon(void){
    unsigned i;int code=(int)weapon_action.weapon_class*1024+weapon_action.direction*128+weapon_action.phase*16+(weapon_action.charge/4);
    if(weapon_action.weapon_class!=EQUIPMENT_SWORD&&weapon_action.phase&&weapon_action.phase!=WEAPON_RECOVERY){
        if(code!=weapon_code){for(i=0;i<1024;i++)weapon_pixels[i]=0;
            if(weapon_action.weapon_class==EQUIPMENT_LANCE){int k;for(k=-10;k<15;k++){axis_pixel(k,0,weapon_action.direction,PAL_WOOD1);axis_pixel(k,1,weapon_action.direction,PAL_WOOD3);}for(k=10;k<16;k++){axis_pixel(k,-1,weapon_action.direction,PAL_WHITE);axis_pixel(k,0,weapon_action.direction,PAL_STONE4);}}
            else {int k;for(k=-7;k<=7;k++){axis_pixel(8-(k*k)/12,k,weapon_action.direction,PAL_GOLD3);axis_pixel(2,k,weapon_action.direction,PAL_GOLD4);}for(k=0;k<13;k++)axis_pixel(k,0,weapon_action.direction,weapon_action.charge>=24?PAL_TEAL2:PAL_WHITE);}
            obj_upload(weapon_pixels,32,32,OBJ_WEAPON);weapon_code=code;gfx_slash_frame=-1;
        }
        {int offset=weapon_action.weapon_class==EQUIPMENT_LANCE?(weapon_action.phase==WEAPON_ACTIVE?24:6):0;unsigned d=weapon_action.direction;obj_add(OBJ_WEAPON,px-16+(d==2?-offset:d==3?offset:0),py-17+(d==1?-offset:d==0?offset:0),32,32,1,py+1,0);}
    }
    for(i=0;i<2;i++)if(player_arrows[i].active){u8 pixels[64];unsigned x,y,d=player_arrows[i].direction;if(arrow_direction[i]!=(int)d){for(y=0;y<8;y++)for(x=0;x<8;x++){int f=d==0?(int)y-4:d==1?4-(int)y:d==2?4-(int)x:(int)x-4,side=d<2?(int)x-4:(int)y-4;pixels[y*8+x]=(side==0&&f>=-3&&f<=2)?PAL_WOOD3:(f==2&&(side==1||side==-1))?PAL_WHITE:0;}obj_upload(pixels,8,8,OBJ_PLAYER_ARROW+(int)i*64);arrow_direction[i]=(int)d;}obj_add(OBJ_PLAYER_ARROW+(int)i*64,(player_arrows[i].x_q8>>8)-4,(player_arrows[i].y_q8>>8)-4,8,8,1,(player_arrows[i].y_q8>>8)+1,0);}
}
void game_draw_enemy_phase(unsigned i,int x,int y){if(i<6&&enemy_phases[i]<5)obj_add(OBJ_PHASE_ICONS+enemy_phases[i]*64,x-4,y-21,8,8,1,y+2,0);}
static void init_phase_icons(void){static const unsigned char shape[5][8]={{0,12,30,62,30,12,8,0},{0,8,12,30,62,30,12,0},{0,8,28,62,62,28,8,0},{0,28,34,34,34,34,28,0},{0,8,8,28,62,62,28,0}};static const unsigned char colors[5]={PAL_MOSS3,PAL_FIRE2,PAL_STONE3,PAL_GOLD3,PAL_WATER4};unsigned p,x,y;unsigned char pixels[64];for(p=0;p<5;p++){for(y=0;y<8;y++)for(x=0;x<8;x++)pixels[y*8+x]=(shape[p][y]&(1u<<x))?colors[p]:0;obj_upload(pixels,8,8,OBJ_PHASE_ICONS+(int)p*64);}}
