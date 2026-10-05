#include "weapon_actions.h"
static int valid_stats(const EquipmentStats *s){
    return s && s->weapon_class>=EQUIPMENT_SWORD && s->weapon_class<=EQUIPMENT_BOW &&
        s->attack_q4<=EQUIPMENT_MAX_ATTACK_Q4 && s->reach_px<=4 && s->stagger<=3 &&
        (s->phase<5 || s->phase==EQUIPMENT_NEUTRAL_PHASE);
}
void weapon_action_init(WeaponAttack *a){
    unsigned i;unsigned char *p=(unsigned char*)a;if(!a)return;
    for(i=0;i<sizeof *a;i++)p[i]=0;
}
static void snapshot(WeaponAttack *a,const EquipmentStats*s,const EquipmentMove*m){
    a->damage_q4=m->damage_q4;a->attack_q4=s->attack_q4;
    a->reach_px=(EquipmentU8)(m->reach_px+s->reach_px);
    a->half_width_px=m->half_width_px;a->stagger=s->stagger;a->element=s->phase;
    a->hit_mask=0;
}
static unsigned begin(WeaponAttack*a,const EquipmentStats*s,unsigned direction){
    const EquipmentWeapon*w=&equipment_weapons[s->weapon_class];unsigned next=0;
    if(s->weapon_class==EQUIPMENT_SWORD && a->weapon_class==EQUIPMENT_SWORD &&
       a->combo_clock && a->combo<3)next=a->combo;
    a->weapon_class=s->weapon_class;a->move=(EquipmentU8)next;
    a->combo=(EquipmentU8)(next+1);a->combo_clock=w->combo_window;
    a->direction=(EquipmentU8)direction;a->age=0;a->charge=0;a->buffer=0;
    snapshot(a,s,&w->moves[next]);
    a->phase=s->weapon_class==EQUIPMENT_BOW?WEAPON_CHARGING:WEAPON_WINDUP;
    if(a->phase==WEAPON_CHARGING)a->charge=1;
    return WEAPON_EVENT_START;
}
static unsigned release_bow(WeaponAttack*a,unsigned live){
    const EquipmentWeapon*w=&equipment_weapons[EQUIPMENT_BOW];
    const EquipmentMove*m=&w->moves[a->move];
    a->phase=WEAPON_RECOVERY;a->age=0;a->damage_q4=m->damage_q4;
    /* Preserve the gear reach delta captured with the first bow move. */
    a->reach_px=(EquipmentU8)(a->reach_px-w->moves[0].reach_px+m->reach_px);
    a->arrow_pending=(EquipmentU8)(live<w->max_live_arrows);
    return a->arrow_pending?WEAPON_EVENT_ARROW:WEAPON_EVENT_BLOCKED;
}
unsigned weapon_action_tick(WeaponAttack*a,const EquipmentStats*s,unsigned d,
                            int held,int pressed,unsigned live){
    const EquipmentWeapon*w;const EquipmentMove*m;unsigned result=0;
    if(!a||!valid_stats(s)||d>3||live>WEAPON_ARROW_CAPACITY||
       (held!=0&&held!=1)||(pressed!=0&&pressed!=1)||a->phase>WEAPON_CHARGING)return 0;
    a->arrow_pending=0;
    if(a->suppress_until_release){
        if(!held)a->suppress_until_release=0;
        held=pressed=0;
    }
    if(a->combo_clock)--a->combo_clock;
    if(a->buffer)--a->buffer;
    if(a->phase==WEAPON_IDLE){
        if(pressed||a->buffer)return begin(a,s,d);
        return 0;
    }
    if(a->weapon_class<EQUIPMENT_SWORD||a->weapon_class>EQUIPMENT_BOW)return 0;
    w=&equipment_weapons[a->weapon_class];
    if(a->move>=w->move_count)return 0;
    m=&w->moves[a->move];
    if(a->phase==WEAPON_CHARGING){
        a->direction=(EquipmentU8)d;
        if(held){if(a->charge<w->charge_max_updates)++a->charge;return 0;}
        a->move=a->charge>=w->charge_min_updates?1:0;
        if(a->charge+1u<w->moves[0].windup){a->phase=WEAPON_WINDUP;a->age=(EquipmentU8)(a->charge+1);return 0;}
        return release_bow(a,live);
    }
    if(a->weapon_class==EQUIPMENT_BOW){
        if(a->phase==WEAPON_WINDUP){if(++a->age>=w->moves[0].windup)return release_bow(a,live);}
        else if(++a->age>=m->recovery){a->phase=WEAPON_IDLE;result=WEAPON_EVENT_FINISH;}
        return result;
    }
    if(pressed)a->buffer=w->buffer;
    ++a->age;
    if(a->age<m->windup)a->phase=WEAPON_WINDUP;
    else if(a->age<m->windup+m->active){a->phase=WEAPON_ACTIVE;result=WEAPON_EVENT_ACTIVE;}
    else if(a->age<m->windup+m->active+m->recovery)a->phase=WEAPON_RECOVERY;
    else {a->phase=WEAPON_IDLE;result=WEAPON_EVENT_FINISH;if(a->buffer)result|=begin(a,s,d);}
    return result;
}
void weapon_action_suspend(WeaponAttack*a){
    if(!a)return;
    a->buffer=0;a->suppress_until_release=1;a->arrow_pending=0;
    if(a->weapon_class==EQUIPMENT_BOW && (a->phase==WEAPON_CHARGING||a->phase==WEAPON_WINDUP)){
        a->phase=WEAPON_IDLE;a->age=a->charge=0;
    }
}
unsigned weapon_action_busy(const WeaponAttack*a,unsigned live){
    unsigned busy=live?EQUIPMENT_BUSY_PLAYER_PROJECTILE:0;
    if(!a)return busy;
    if(a->phase==WEAPON_CHARGING)busy|=EQUIPMENT_BUSY_CHARGING;
    else if(a->phase==WEAPON_WINDUP||a->phase==WEAPON_ACTIVE)busy|=EQUIPMENT_BUSY_ATTACKING;
    else if(a->phase==WEAPON_RECOVERY)busy|=EQUIPMENT_BUSY_RECOVERING;
    return busy;
}
int weapon_action_contains(const WeaponAttack*a,int ox,int oy,int tx,int ty){
    int dx,dy,f,l;
    if(!a||a->phase!=WEAPON_ACTIVE||a->weapon_class==EQUIPMENT_BOW||a->direction>3||
       (unsigned)ox>WEAPON_COORDINATE_MAX||(unsigned)oy>WEAPON_COORDINATE_MAX||
       (unsigned)tx>WEAPON_COORDINATE_MAX||(unsigned)ty>WEAPON_COORDINATE_MAX)return 0;
    dx=tx-ox;dy=ty-oy;f=a->direction==0?dy:a->direction==1?-dy:a->direction==2?-dx:dx;
    l=a->direction<2?dx:dy;if(l<0)l=-l;
    if(a->weapon_class==EQUIPMENT_LANCE)return f>=0 && f<=a->reach_px && l<=a->half_width_px;
    if(a->weapon_class!=EQUIPMENT_SWORD)return 0;
    return f>=-6 && (f<0?-f:f)+l<=a->reach_px && l<=a->half_width_px;
}
int weapon_action_can_hit(const WeaponAttack*a,unsigned id){
    return a && a->phase==WEAPON_ACTIVE &&
        (a->weapon_class==EQUIPMENT_SWORD || a->weapon_class==EQUIPMENT_LANCE) &&
        id<WEAPON_TARGET_CAPACITY && !(a->hit_mask&(1u<<id));
}
int weapon_action_mark_hit(WeaponAttack*a,unsigned id){
    if(!weapon_action_can_hit(a,id))return 0;
    a->hit_mask=(EquipmentU16)(a->hit_mask|(1u<<id));return 1;
}
int weapon_arrow_spawn(WeaponArrow*a,WeaponAttack*s,int x,int y){
    if(!a||!s||a->active||!s->arrow_pending||s->weapon_class!=EQUIPMENT_BOW||s->phase!=WEAPON_RECOVERY||
       s->direction>3||(unsigned)x>WEAPON_COORDINATE_MAX||(unsigned)y>WEAPON_COORDINATE_MAX)return 0;
    a->x_q8=x*256;a->y_q8=y*256;a->remaining_q8=(EquipmentU16)(s->reach_px*256u);
    a->speed_q8=equipment_weapons[EQUIPMENT_BOW].projectile_speed_q8;
    a->active=1;a->direction=s->direction;a->damage_q4=s->damage_q4;
    a->attack_q4=s->attack_q4;a->stagger=s->stagger;a->element=s->element;
    a->reserved[0]=a->reserved[1]=0;s->arrow_pending=0;return 1;
}
void weapon_arrow_tick(WeaponArrow*a,WeaponPointTest solid,WeaponPointTest target,void*ctx){
    unsigned remaining,step;int dx,dy,x,y;
    if(!a||!a->active||!solid||!target)return;
    if(a->direction>3||a->speed_q8>2048u||!a->speed_q8){a->active=0;return;}
    remaining=a->speed_q8;if(remaining>a->remaining_q8)remaining=a->remaining_q8;
    dx=a->direction==2?-1:a->direction==3?1:0;dy=a->direction==1?-1:a->direction==0?1:0;
    while(remaining){
        step=remaining>256u?256u:remaining;
        a->x_q8+=dx*(int)step;a->y_q8+=dy*(int)step;
        remaining-=step;a->remaining_q8=(EquipmentU16)(a->remaining_q8-step);
        x=a->x_q8>>8;y=a->y_q8>>8;
        if((unsigned)x>WEAPON_COORDINATE_MAX||(unsigned)y>WEAPON_COORDINATE_MAX||
           solid(ctx,x,y)||target(ctx,x,y)){a->active=0;return;}
    }
    if(!a->remaining_q8)a->active=0;
}
