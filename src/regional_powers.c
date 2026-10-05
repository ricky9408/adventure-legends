#include "regional_powers.h"
#include "gear_runtime.h"
#include "assets.h"
#include "obj_layout.h"
#include "creatures.h"
#include "progression.h"
typedef struct {int x,y,hp,flash,kind;} Enemy;
extern Enemy enemies[6];
extern volatile int px,py;
extern int face,ability_cd,ability_max,enemy_windups[6],enemy_clocks[6];
extern int solid(int,int),near(int,int,int,int,int);
extern unsigned game_power_cooldown(unsigned);
extern void sfx(int),impact(int,int),kill_enemy(Enemy*),obj_upload(const unsigned char*,int,int,int),obj_add(int,int,int,int,int,int,int,int);
unsigned char slowed_enemies[6];
int regional_power_kind,regional_power_time,regional_power_form;
static int origin_x,origin_y,pin_x,pin_y,pin_direction,pin_return,pin_hit;
#define OBJ_POWER_PIN GFX_OBJ_POWER_PIN
static int absolute(int n){return n<0?-n:n;}
static int sign(int n){return(n>0)-(n<0);}
static int clear(int x,int y,int tx,int ty){int dx=absolute(tx-x),dy=-absolute(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,err=dx+dy;while(x!=tx||y!=ty){int twice=err*2;if(twice>=dy){err+=dy;x+=sx;}if(twice<=dx){err+=dx;y+=sy;}if(solid(x,y))return 0;}return 1;}
void regional_powers_reset(void){unsigned i;regional_power_kind=regional_power_time=regional_power_form=pin_hit=pin_return=0;for(i=0;i<6;i++)slowed_enemies[i]=0;}
int regional_power(unsigned command){unsigned i;if(command<9||command>11)return 0;{CreatureInstance*c=progression_selected();regional_power_form=c?c->form_id:0;}regional_power_kind=(int)command;regional_power_time=command==11?36:60;origin_x=pin_x=px;origin_y=pin_y=py;pin_direction=face;pin_return=pin_hit=0;
 ability_max=ability_cd=(int)game_power_cooldown(creatures_ability(command)->cooldown_updates);sfx(2);
 if(command==11){unsigned char pixels[256];unsigned x,y;for(y=0;y<16;y++)for(x=0;x<16;x++){int f=face==0?(int)y-7:face==1?7-(int)y:face==2?7-(int)x:(int)x-7,side=face<2?(int)x-7:(int)y-7;if(side<0)side=-side;pixels[y*16+x]=(f>=4&&f<=6&&side<=2)?PAL_WHITE:(side==0&&f>=-5&&f<=6)?PAL_GOLD3:0;}obj_upload(pixels,16,16,OBJ_POWER_PIN);}
 else {unsigned char water[64];unsigned x,y;for(y=0;y<8;y++)for(x=0;x<8;x++){int side=(int)x-3;if(side<0)side=-side;water[y*8+x]=(y>=1&&y<=6&&(unsigned)side<=(y<4?y/2:2))?(side==0&&y<5?PAL_WHITE:PAL_WATER4):0;}obj_upload(water,8,8,GFX_OBJ_WATER_DROP);}
 if(command!=11)for(i=0;i<6;i++)if(enemies[i].hp&&near(px,py,enemies[i].x,enemies[i].y,command==9?38:52)&&clear(px,py,enemies[i].x,enemies[i].y)){
     slowed_enemies[i]=60;game_enemy_hurt(i,24,0,CREATURE_WATER);enemies[i].flash=12;impact(enemies[i].x,enemies[i].y);if(!enemies[i].hp)kill_enemy(&enemies[i]);
 }
 return 1;
}
void regional_powers_tick(void){unsigned i;int age;
 for(i=0;i<6;i++)if(slowed_enemies[i])slowed_enemies[i]--;
 if(!regional_power_time)return;
 regional_power_time--;if(regional_power_kind!=11)return;age=36-regional_power_time;
 if(age>=17)pin_return=1;
 if(!pin_return){int step;for(step=0;step<4;step++){int nx=pin_x+(pin_direction==2?-1:pin_direction==3?1:0),ny=pin_y+(pin_direction==1?-1:pin_direction==0?1:0);if(solid(nx,ny)){pin_return=1;break;}pin_x=nx;pin_y=ny;
    for(i=0;i<6&&!pin_hit;i++)if(enemies[i].hp&&near(pin_x,pin_y,enemies[i].x,enemies[i].y,10)&&clear(pin_x,pin_y,enemies[i].x,enemies[i].y)){
        game_enemy_hurt(i,32,0,CREATURE_METAL);enemies[i].flash=18;
        if(enemy_windups[i]){enemy_windups[i]=0;enemy_clocks[i]=60;}
        impact(pin_x,pin_y);pin_hit=1;pin_return=1;if(!enemies[i].hp)kill_enemy(&enemies[i]);break;
    }
    if(pin_return)break;
 }}else{int dx=origin_x-pin_x,dy=origin_y-pin_y;pin_x+=sign(dx)*(absolute(dx)>4?4:absolute(dx));pin_y+=sign(dy)*(absolute(dy)>4?4:absolute(dy));}
}
void regional_powers_draw(void){unsigned i;static const signed char dx[8]={1,1,0,-1,-1,-1,0,1},dy[8]={0,1,1,1,0,-1,-1,-1};if(!regional_power_time)return;
 if(regional_power_kind==11){obj_add(OBJ_POWER_PIN,pin_x-8,pin_y-8,16,16,1,pin_y+1,0);return;}
 for(i=0;i<8;i++){int radius=regional_power_kind==9?24:36,x=origin_x+dx[i]*radius,y=origin_y+dy[i]*radius;if(!solid(x,y))obj_add(GFX_OBJ_WATER_DROP,x-4,y-4,8,8,1,y,0);}
}
