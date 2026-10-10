/* Real catalog/Q4, synthetic component geometry. No controller acceptance. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "covenants_powers.h"
#include "covenants_power_art.h"
#include "covenants_creature_art.h"
#include "covenants_game.h"
#include "northern_powers.h"
#include "progression.h"
#include "gear_runtime.h"
#include "combat_rules.h"
#include "obj_layout.h"
typedef struct { int x,y,hp,flash,kind; } Enemy;
typedef struct { int x,y,dx,dy,life,owner; } Shot;
Enemy enemies[6];Shot shots[12];Save5State adventure_save;
volatile int px,py,room;int face,ability_cd,ability_max,hitstop;
unsigned char slowed_enemies[6];
static unsigned owner,generation,token,revoked,scene=1,attempt=1,revision=1,draws,max_draws;
static unsigned field_count,field_accepts,field_beats,field_tokens[2],shot_serial[12];
static unsigned snapshots,rays,solid_calls,max_rays,max_solids,boxes;
static unsigned snapshot_refuse;
static int targets[8][3],wall_count;
static short walls[48][4];
static unsigned char vram[16384];
static int draw_x[32],draw_y[32],draw_off[32],draw_w[32];
static const unsigned commands[8]={12,122,123,124,125,126,127,128};
static const unsigned cooldown[8]={240,180,210,200,165,195,180,240};
static const unsigned lifetime[8]={148,102,72,132,72,112,60,132};
static const unsigned base_damage[8]={24,32,48,32,32,0,32,32};
CreatureInstance *progression_selected(void) {
    CreatureRoster *r=&adventure_save.roster;
    return r->selected_party<4&&r->party[r->selected_party]<160?&r->instances[r->party[r->selected_party]]:0;
}
int northern_powers_tiles_claim(unsigned o) { if(owner||o!=NORTHERN_TILES_COVENANTS)return 0;owner=o;generation++;return 1; }
int northern_powers_tiles_release(unsigned o) { if(owner!=o||covenants_power_time)return 0;owner=0;generation++;return 1; }
unsigned northern_powers_tiles_owner(void) { return owner; }
unsigned northern_powers_tiles_generation(void) { return generation; }
unsigned northern_powers_shot_serial(unsigned i) { return i<12?shot_serial[i]:0; }
void impact(int x,int y) { (void)x;(void)y; }
void sfx(int s) { (void)s; }
void kill_enemy(Enemy *e) { assert(e>=enemies&&e<enemies+6);e->hp=0; }
void obj_upload(const unsigned char *p,int w,int h,int off) {
    assert(off==GFX_OBJ_POWER_PIN||off==GFX_OBJ_WATER_DROP);memcpy(vram+off,p,(unsigned)(w*h));
}
void obj_add(int off,int x,int y,int w,int h,int priority,int depth,int flip) {
    (void)priority;(void)depth;(void)flip;
    assert((off==GFX_OBJ_POWER_PIN||off==GFX_OBJ_WATER_DROP)&&(w==8||w==16)&&h==w&&draws<32);
    draw_x[draws]=x;draw_y[draws]=y;draw_off[draws]=off;draw_w[draws++]=w;
}
int solid(int x,int y) {
    int i;solid_calls++;
    if(x<0||x>=480||y<0||y>=320)return 1;
    for(i=0;i<wall_count;i++)if(x>=walls[i][0]&&x<=walls[i][2]&&y>=walls[i][1]&&y<=walls[i][3])return 1;
    return 0;
}
int game_clear_box(int x0,int y0,int x1,int y1) {
    int i;boxes++;
    if(x0<0||y0<0||x1>=480||y1>=320||x0>x1||y0>y1)return 0;
    for(i=0;i<wall_count;i++)if(x0<=walls[i][2]&&x1>=walls[i][0]&&y0<=walls[i][3]&&y1>=walls[i][1])return 0;
    return 1;
}
int game_collision_rects(int x0,int y0,int x1,int y1,short out[][4],unsigned cap) {
    int i,n=0;snapshots++;
    if(snapshot_refuse) { if(cap)out[0][0]=100;return snapshot_refuse==2?(int)cap+1:-1; }
    for(i=0;i<wall_count;i++) {
        if(walls[i][0]>x1||walls[i][2]<x0||walls[i][1]>y1||walls[i][3]<y0)continue;
        if((unsigned)n==cap)return -1;
        memcpy(out[n++],walls[i],sizeof walls[i]);
    }
    return n;
}
static int supercover(int x,int y,int tx,int ty) {
    int ax=abs(tx-x),ay=-abs(ty-y),sx=x<tx?1:-1,sy=y<ty?1:-1,e=ax+ay;
    rays++;
    if(solid(x,y)||solid(tx,ty))return 0;
    while(x!=tx||y!=ty) {
        int q=e*2,nx=x,ny=y;
        if(q>=ay) { e+=ay;nx+=sx; }if(q<=ax) { e+=ax;ny+=sy; }
        if(nx!=x&&ny!=y&&(solid(nx,y)||solid(x,ny)))return 0;
        x=nx;y=ny;if(solid(x,y))return 0;
    }
    return 1;
}
int covenants_game_supercover(int x,int y,int tx,int ty) { return supercover(x,y,tx,ty); }
int horizons_game_supercover(int x,int y,int tx,int ty) { return supercover(x,y,tx,ty); }
int return_game_supercover(int x,int y,int tx,int ty) { return supercover(x,y,tx,ty); }
int underwater_game_supercover(int x,int y,int tx,int ty) { return supercover(x,y,tx,ty); }
unsigned covenants_game_scene_generation(void) { return scene; }
unsigned covenants_game_attempt_generation(void) { return attempt; }
unsigned covenants_game_geometry_revision(void) { return revision; }
unsigned covenants_game_action_begin(unsigned channel) { assert(channel==3);revoked=0;return ++token; }
void covenants_game_revoke_cast(unsigned t) { if(t==token)revoked=1; }
int covenants_game_field_target(unsigned i,int *x,int *y,int *r) {
    if(i>=field_count)return 0;
    *x=targets[i][0];*y=targets[i][1];*r=targets[i][2];return 1;
}
int covenants_game_field_hit(unsigned i,unsigned command,unsigned identity,unsigned form,unsigned t) {
    const CovenantsPowerProof *p=covenants_powers_proof();unsigned beat=covenants_powers_beat();
    assert(i<field_count);
    if(!p||revoked||t!=token||p->caster!=identity||p->form!=form||p->command!=command)return 0;
    assert(beat==1||beat==2);field_accepts++;field_beats|=1u<<beat;field_tokens[beat-1]=t;return 1;
}
static void wall(int x,int y,int width,int height) {
    assert(wall_count<48);walls[wall_count][0]=(short)x;walls[wall_count][1]=(short)y;
    walls[wall_count][2]=(short)(x+width-1);walls[wall_count++][3]=(short)(y+height-1);
    revision++;covenants_powers_geometry_changed();
}
static void member(CreatureInstance *c,unsigned form,unsigned id,unsigned command) {
    memset(c,0,sizeof *c);c->form_id=(unsigned char)form;c->flags=CREATURE_OCCUPIED;c->level=40;
    c->xp=creatures_xp_threshold(40);c->bond=80;c->instance_id=id;c->polarity=creatures_form(form)->polarity;
    c->equipped[0]=(unsigned char)command;assert(creatures_instance_validate(c));
}
static void setup(unsigned command) {
    unsigned form=command==12?121:command;
    covenants_powers_reset();owner=0;memset(&adventure_save,0,sizeof adventure_save);
    memset(enemies,0,sizeof enemies);memset(shots,0,sizeof shots);memset(shot_serial,0,sizeof shot_serial);
    memset(slowed_enemies,0,sizeof slowed_enemies);memset(enemy_stagger_ticks,0,6);
    memset(field_tokens,0,sizeof field_tokens);memset(vram,0,sizeof vram);
    adventure_save.roster.party[0]=7;adventure_save.roster.party[1]=9;
    adventure_save.roster.party[2]=adventure_save.roster.party[3]=255;
    member(&adventure_save.roster.instances[7],form,71,command);
    member(&adventure_save.roster.instances[9],101,91,102);
    px=py=100;room=70;face=3;wall_count=ability_cd=hitstop=0;
    field_count=field_accepts=field_beats=draws=rays=solid_calls=boxes=0;revoked=0;
    gear_stats.power_cooldown=EQUIPMENT_BASE_POWER_COOLDOWN;
}
static void enemy(unsigned i,int f,int s,int kind) {
    enemies[i]=(Enemy){100+f,100+s,100,0,kind};enemy_hp_q4[i]=1600;enemy_phases[i]=255;
    covenants_powers_enemy_spawn(i);
}
static void shot(unsigned i,int f,int s,int df,int ds,int hostile) {
    shots[i]=(Shot){100+f,100+s,df,ds,90,hostile};if(++shot_serial[i]==0)shot_serial[i]=1;
    covenants_powers_shot_spawn(i);
}
static void target(unsigned i,int f,int s,int radius) {
    assert(i<8);targets[i][0]=100+f;targets[i][1]=100+s;targets[i][2]=radius;
    if(field_count<=i)field_count=i+1;
}
static void tick(void) {
    unsigned i;rays=solid_calls=0;covenants_powers_tick();
    if(!hitstop) { if(ability_cd)ability_cd--;for(i=0;i<6;i++)if(slowed_enemies[i])slowed_enemies[i]--; }
    draws=0;covenants_powers_draw();if(draws>max_draws)max_draws=draws;
    if(rays>max_rays)max_rays=rays;if(solid_calls>max_solids)max_solids=solid_calls;
    assert(draws<=25);assert(covenants_powers_moving_objects()<=3);
}
static void updates(unsigned n) { while(n--)tick(); }
static void invalid_contract(void) {
    unsigned c;setup(12);
    for(c=0;c<512;c++)if(c!=12)assert(!covenants_power(c));
    assert(!covenants_power(~0u));face=4;assert(!covenants_power(12));face=3;
    owner=NORTHERN_TILES_HORIZONS;assert(!covenants_power(12));owner=0;
    progression_selected()->instance_id=0;assert(!covenants_power(12));
    setup(12);progression_selected()->form_id=120;assert(!covenants_power(12));
    setup(123);progression_selected()->equipped[0]=12;assert(!covenants_power(123));
    setup(126);assert(covenants_power(126));updates(6);shot(0,18,0,-4,0,1);
    assert(!covenants_powers_intercept_shot(0,0x7fffffff,100,0x7fffffff,100,1));
    assert(!covenants_powers_intercept_shot(0,118,100,114,100,1u<<31));
    puts("commands reject wrong form, command121, full-width invalid IDs, no identity, illegal facing and occupied tile lease");
}
static void prepare(unsigned index) {
    switch(index) {
    case 0:enemy(0,30,0,0);break;case 1:enemy(0,20,0,0);break;
    case 2:enemy(0,30,0,0);break;case 3:enemy(0,25,0,0);break;
    case 4:enemy(0,24,0,0);break;case 5:enemy(0,16,0,0);break;
    case 6:enemy(0,16,0,0);break;case 7:enemy(0,20,0,0);break;
    }
}
static void all_commands(void) {
    unsigned i,t,p;
    for(i=0;i<8;i++)for(p=0;p<6;p++) {
        setup(commands[i]);prepare(i);enemy_phases[0]=(unsigned char)(p==5?255:p);
        assert(covenants_power(commands[i]));assert(ability_cd==(int)cooldown[i]);assert(!covenants_power(commands[i]));
        for(t=1;t<=lifetime[i];t++) { if(i==3&&t==8)enemies[0].x=124;tick(); }
        assert(!covenants_power_time&&!owner&&ability_cd>0);
        if(enemy_hp_q4[0]!=1600-(int)combat_damage_q4(base_damage[i],0,0,creatures_ability(commands[i])->phase,p==5?255:p,0))
            printf("damage mismatch command%u phase%u got%d\n",commands[i],p,1600-enemy_hp_q4[0]);
        assert(enemy_hp_q4[0]==1600-(int)combat_damage_q4(base_damage[i],0,0,creatures_ability(commands[i])->phase,p==5?255:p,0));
    }
    puts("all8 commands: real128-form catalog, real five-phase+neutral Q4 damage, one-hit cap, finite lifetimes and cooldowns");
}
static void ownership(void) {
    unsigned change;
    for(change=0;change<12;change++) {
        unsigned id;int cd;setup(123);target(0,30,0,0);assert(covenants_power(123));updates(12);
        id=covenants_powers_proof()->action_serial;cd=ability_cd;
        switch(change) {
        case 0:adventure_save.roster.instances[9].instance_id++;break;
        case 1:adventure_save.roster.instances[9].equipped[1]=102;break;
        case 2:adventure_save.roster.party[1]=255;break;
        case 3:adventure_save.roster.selected_party=1;break;
        case 4:progression_selected()->instance_id++;break;
        case 5:progression_selected()->form_id++;break;
        case 6:progression_selected()->selected_command=1;break;
        case 7:scene++;break;case 8:attempt++;break;case 9:room++;break;
        case 10:covenants_powers_selection_changed();break;case 11:covenants_powers_reset();break;
        }
        assert(!covenants_powers_proof());tick();assert(!covenants_power_time&&ability_cd>=cd-1&&!field_accepts);
        assert(!covenants_powers_proof());
        setup(123);assert(covenants_power(123));assert(covenants_powers_proof()->action_serial!=id);
    }
    setup(123);target(0,30,0,0);assert(covenants_power(123));updates(12);revision++;tick();
    assert(!covenants_powers_proof());revision--;updates(60);assert(!field_accepts&&revoked);
    setup(123);assert(covenants_power(123));updates(12);
    { int age=covenants_power_age,cd=ability_cd,time=covenants_power_time;hitstop=1;updates(80);
      assert(covenants_power_age==age&&ability_cd==cd&&covenants_power_time==time&&covenants_powers_proof());hitstop=0; }
    puts("full party/member edits, owner/form/command switches, scene/attempt/room/death/reset and permanent geometry revocation; hitstop freeze");
}
static void fields(void) {
    unsigned i,t;static const int f[8]={14,28,-8,24,24,16,28,20};
    for(i=0;i<8;i++) {
        setup(commands[i]);target(0,f[i],0,0);assert(covenants_power(commands[i]));
        for(t=0;t<lifetime[i];t++)tick();assert(field_accepts>=1);
    }
    setup(123);target(0,-8,0,0);target(1,30,0,0);assert(covenants_power(123));updates(65);
    assert(field_accepts==2&&field_beats==6&&field_tokens[0]==field_tokens[1]);
    setup(123);target(0,-8,0,0);target(1,30,0,0);assert(covenants_power(123));updates(10);
    assert(field_accepts==1);wall(114,90,1,20);wall_count=0;updates(62);assert(field_accepts==1&&revoked);
    for(i=0;i<8;i++) {
        setup(commands[i]);wall(111,0,1,320);target(0,124-100,0,0);assert(covenants_power(commands[i]));updates(lifetime[i]);assert(!field_accepts);
    }
    setup(128);wall(110,100,1,1);assert(covenants_power(128));updates(66);assert(!covenants_powers_overlap(120,100,0));
    setup(126);assert(covenants_power(126));updates(6);assert(!covenants_powers_overlap(88,100,0));
    setup(127);wall(116,100,1,1);enemy(0,28,24,0);assert(covenants_power(127));updates(18);
    wall_count=0;updates(42);assert(enemy_hp_q4[0]==1600);
    puts("optional targets on exact pixels; same-token heat beats; first-wall lifetime stops, hidden-wall rejection and deliberate shelter gap");
}
static void guards(void) {
    unsigned index,j,cap;static const unsigned guardcmd[4]={12,125,126,128};
    for(index=0;index<4;index++) {
        int x=index==0?14:index==1?24:index==2?16:20;
        cap=index==0?3:index==1?1:2;setup(guardcmd[index]);assert(covenants_power(guardcmd[index]));updates(index==1?22:6);
        for(j=0;j<cap;j++) {
            int side=index==0?((int)j-1)*12:0;
            shot(0,x+2,side,-4,0,1);
            assert(!covenants_powers_intercept_shot(0,102+x,100+side,98+x,100+side,0));
            assert(!covenants_powers_intercept_shot(0,102+x,100+side,97+x,100+side,1));
            shots[0].owner=0;assert(!covenants_powers_intercept_shot(0,102+x,100+side,98+x,100+side,1));shots[0].owner=1;
            assert(covenants_powers_intercept_shot(0,102+x,100+side,98+x,100+side,1));assert(!shots[0].life);
        }
        shot(1,x+2,0,-4,0,1);assert(!covenants_powers_intercept_shot(1,102+x,100,98+x,100,1));
    }
    setup(126);assert(covenants_power(126));updates(6);shot(0,0,18,0,-4,1);
    assert(covenants_powers_intercept_shot(0,100,118,100,114,1));
    setup(126);assert(covenants_power(126));updates(6);shot(0,-14,0,4,0,1);
    assert(!covenants_powers_intercept_shot(0,86,100,90,100,1));
    setup(12);enemy(0,30,-12,0);enemy(1,30,0,0);assert(covenants_power(12));updates(36);
    shot(0,16,-12,-4,0,1);assert(covenants_powers_intercept_shot(0,116,88,112,88,1));
    assert(covenants_powers_input(256)==2);assert(!covenants_powers_input(256));updates(22);
    assert(enemy_hp_q4[0]==1600&&enemy_hp_q4[1]==1576&&!covenants_power_time&&ability_cd>0);
    puts("guard caps3/1/2/2, hostile provenance, exact segment, spawn reuse, side protection/open mouth and spent-drop counterplay");
}
static void movement_bosses(void) {
    setup(127);enemy(0,16,0,3);assert(covenants_power(127));updates(30);assert(enemies[0].x==116);
    setup(127);enemy(0,16,0,0);wall(123,104,1,1);assert(covenants_power(127));updates(30);assert(enemies[0].x<=118);
    setup(127);enemy(0,16,0,0);enemy(1,25,0,0);assert(covenants_power(127));updates(30);assert(enemies[0].x==116);
    setup(122);enemy(0,20,0,3);assert(covenants_power(122));updates(6);assert(!slowed_enemies[0]);
    setup(122);enemy(0,20,0,0);assert(covenants_power(122));updates(6);assert(slowed_enemies[0]);
    enemy(0,20,0,0);updates(90);assert(enemy_hp_q4[0]==1600);
    setup(128);assert(covenants_power(128));updates(65);assert(!covenants_powers_boss_damage(120,100,0,1));tick();
    assert(!covenants_powers_boss_damage(120,100,0,0));assert(covenants_powers_boss_damage(120,100,0,1)==32);
    assert(!covenants_powers_boss_damage(120,100,0,1));
    setup(123);enemy(0,30,0,0);enemy(1,30,0,0);assert(covenants_power(123));updates(72);
    assert(enemy_hp_q4[0]==1552&&enemy_hp_q4[1]==1600);
    setup(123);enemy(0,30,0,0);assert(covenants_power(123));updates(52);
    assert(enemy_hp_q4[0]==1552&&!covenants_powers_boss_damage(130,100,0,1));
    setup(123);enemy(0,40,0,0);assert(covenants_power(123));updates(52);
    assert(covenants_powers_boss_damage(130,100,3,1)==48);updates(20);assert(enemy_hp_q4[0]==1600);
    setup(12);assert(covenants_power(12));updates(126);
    assert(covenants_powers_moving_objects()==3);
    assert(covenants_powers_boss_damage(114,88,3,1)==24&&covenants_powers_moving_objects()==2);
    enemy(0,30,-12,0); /* New slot is already excluded; also inspect visible drop removal. */
    assert(!covenants_powers_overlap(114,88,0));
    puts("ordinary-only8px swept pushes, actor/wall stops, no boss slow/displacement, delayed authored-window boss cap and first-target ember");
}
static void pixel_authority(void) {
    unsigned i,d,t,j,checked=0;int x,y;
    for(i=0;i<8;i++)for(d=0;d<4;d++) {
        setup(commands[i]);face=(int)d;assert(covenants_power(commands[i]));
        for(t=1;t<lifetime[i]-6;t++) {
            tick();if(t<6||t%17)continue;
            for(y=68;y<=132;y++)for(x=68;x<=132;x++) {
                int pixel=0;
                for(j=0;j<draws;j++) {
                    int xx=x-draw_x[j],yy=y-draw_y[j];
                    if(draw_w[j]==8&&xx>=0&&yy>=0&&xx<8&&yy<8&&vram[draw_off[j]+yy*8+xx])pixel=1;
                }
                assert(covenants_powers_overlap(x,y,0)==pixel);checked++;
            }
        }
    }
    printf("%u exact native rendered-pixel vs field-authority checks across8 commands/4 facings\n",checked);
}
static void cache_lifetime(void) {
    unsigned before;setup(128);wall(90,78,20,1);assert(covenants_power(128));before=snapshots;updates(100);
    assert(snapshots==before);wall(89,77,20,1);tick();assert(snapshots==before+1);before=snapshots;
    updates(5);assert(snapshots==before);assert(!covenants_powers_proof());
    puts("one exact/failed snapshot per cast geometry revision; no repeated full-room cache fill");
    setup(124);assert(covenants_power(124));updates(18);
    assert(covenants_powers_overlap(124,100,0));wall(132,90,2,10);tick();
    assert(!covenants_powers_proof()&&!covenants_powers_overlap(124,100,0));
    assert(covenants_powers_boss_damage(124,100,0,1)==32);
    setup(124);assert(covenants_power(124));updates(18);wall(123,100,1,1);tick();
    assert(!covenants_powers_boss_damage(124,100,0,1));
    setup(126);assert(covenants_power(126));updates(18);wall(132,90,2,10);tick();
    assert(!covenants_powers_proof());shot(0,18,0,-4,0,1);
    assert(covenants_powers_intercept_shot(0,118,100,114,100,1));
    setup(126);wall(115,100,1,1);assert(covenants_power(126));updates(18);wall_count=0;revision++;covenants_powers_geometry_changed();tick();
    shot(0,18,0,-4,0,1);assert(covenants_powers_intercept_shot(0,118,100,114,100,1));
    puts("complete clear ring survives unrelated geometry visually; field stays revoked; newly blocked ring is rebuilt");
}
static void visible_beats(void) {
    unsigned i;setup(125);assert(covenants_power(125));updates(6);
    assert(draws);for(i=0;i<draws;i++)assert(draw_off[i]==GFX_OBJ_WATER_DROP);
    updates(16);assert(draws);for(i=0;i<draws;i++)assert(draw_off[i]==GFX_OBJ_POWER_PIN);
    setup(128);assert(covenants_power(128));updates(6);
    assert(draws);for(i=0;i<draws;i++)assert(draw_off[i]==GFX_OBJ_POWER_PIN);
    updates(60);assert(draws);for(i=0;i<draws;i++)assert(draw_off[i]==GFX_OBJ_WATER_DROP);
    for(i=0;i<8;i++){unsigned pixel;for(pixel=0;pixel<64;pixel++)
        assert(!!covenants_power_particles[i][0][pixel]==!!covenants_power_particles[i][1][pixel]);}
    puts("damage/highlight versus field-guard/flat native stamp selection is visibly phased with identical alpha masks");
}
static void rendered(unsigned char *pixels) {
    unsigned j;int x,y;
    memset(pixels,0,96*96);
    for(j=0;j<draws;j++)for(y=0;y<draw_w[j];y++)for(x=0;x<draw_w[j];x++) {
        int xx=draw_x[j]+x-52,yy=draw_y[j]+y-52;unsigned char value=vram[draw_off[j]+y*draw_w[j]+x];
        if(value&&xx>=0&&xx<96&&yy>=0&&yy<96)pixels[yy*96+xx]=value;
    }
}
static void cache_differential(void) {
    unsigned seed=713,trial,mode,i,n;static unsigned char capture[3][5][96*96];
    static const unsigned ages[5]={6,22,42,66,126};short blocks[12][4];
    for(trial=0;trial<96;trial++) {
        unsigned command=commands[trial%8],direction=(trial/8)%4;
        for(i=0;i<12;i++) {
            unsigned a,b;seed=seed*1664525u+1013904223u;a=seed;seed=seed*1664525u+1013904223u;b=seed;
            blocks[i][0]=(short)(66+a%69);blocks[i][1]=(short)(66+b%69);
            blocks[i][2]=(short)(1+(a>>12)%5);blocks[i][3]=(short)(1+(b>>12)%5);
        }
        for(mode=0;mode<3;mode++) {
            snapshot_refuse=mode;setup(command);face=(int)direction;
            for(i=0;i<12&&trial%3;i++)if(!(100>=blocks[i][0]&&100<blocks[i][0]+blocks[i][2]&&
                                 100>=blocks[i][1]&&100<blocks[i][1]+blocks[i][3]))
                wall(blocks[i][0],blocks[i][1],blocks[i][2],blocks[i][3]);
            assert(covenants_power(command));
            for(n=1;n<=126;n++) {
                if(n==12) {
                    if(trial%3==1)wall(114,98,1,5);
                    else { wall_count=0;revision++;covenants_powers_geometry_changed(); }
                }
                tick();for(i=0;i<5;i++)if(n==ages[i])rendered(capture[mode][i]);
            }
        }
        if(memcmp(capture[0],capture[1],sizeof capture[0]))printf("cache differential mismatch trial%u command%u facing%u\n",trial,command,direction);
        assert(!memcmp(capture[0],capture[1],sizeof capture[0]));
        assert(!memcmp(capture[0],capture[2],sizeof capture[0]));
    }
    puts("96 wall layouts/4 facings and mid-cast geometry revisions: exact retained/rebuilt pixels equal failed/partial and over-capacity snapshot fallbacks at5 phases");
}
int main(void) {
    unsigned fallback;
    for(fallback=0;fallback<2;fallback++) {
        snapshot_refuse=fallback;invalid_contract();all_commands();ownership();fields();guards();movement_bosses();cache_lifetime();visible_beats();
    }
    cache_differential();snapshot_refuse=0;pixel_authority();
    assert(covenants_powers_state_bytes()<=768);
    printf("Covenants host passed: RAM%u; maximum draws%u; synthetic fallback ray calls/update%u; synthetic point probes/update%u\n",
           covenants_powers_state_bytes(),max_draws,max_rays,max_solids);
    return 0;
}
