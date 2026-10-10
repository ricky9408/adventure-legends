/* Mixed-size final chapter drawing and finite ordinary defense waves. New
 * orchestration stays in ROM; no extra OAM reservation or resident bitmap. */
COLD void copy_covenants(void){
 const CovenantsArtRoom*r=&covenants_art_rooms[room-70];u32 src,dst,mode;int y,width=r->width;
 if(COPY_OPAQUE_MODAL_BITMAP&&copy_modal_background(r->bitmap,r->bitmap_odd,width))return;
 if(width==240){REG32(0x040000D4)=(u32)(r->bitmap+camera_y*240);REG32(0x040000D8)=(u32)screen;REG32(0x040000DC)=0x84000000|9600;return;}
 src=(u32)(((camera_x&1)?r->bitmap_odd:r->bitmap)+camera_y*width+(camera_x&~1));dst=(u32)screen;
 /* Retain halfword DMA when either pointer or the authored stride is not
  * word aligned. Integer MMIO addresses also avoid forming an unused
  * pointer beyond the bitmap after the final row. */
 mode=((src|dst|(u32)width)&3u)?0x80000000u|120u:0x84000000u|60u;
 for(y=0;y<160;y++){REG32(0x040000D4)=src;REG32(0x040000D8)=dst;REG32(0x040000DC)=mode;src+=width;dst+=240;}
}
COLD void draw_covenants_map(void){
 int i,mx=20,my=62;box(8,31,224,123);centered(covenants_game_name(),35,GOLD);
 rect(mx,my,120,80,PAL_GOLD4);rect(mx+8,my+8,104,64,PAL_PINE3);
 line(mx+12,my+58,mx+106,my+16,PAL_TEAL2);
 for(i=0;i<8;i++){int x=168+(i&1)*30,y=62+(i/2)*19;
  rect(x,y,10,10,covenants_fulfilled(&adventure_save,(unsigned)i+1)?GOLD:PAL_STONE2);
  if(room==70+i)rect(x-2,y-2,14,2,TEAL);
 }
 rect(mx+px*120/world_width()-1,my+py*80/world_height()-1,3,3,PAL_HEART);
 centered(TX_G_NEXT_TAB,140,TEAL);
}
COLD int covenants_hint_text(void){
 static const int hints[]={0,TX_CP_WARD,TX_CP_BANK,TX_CP_HOLD,TX_CP_GAP,TX_CP_WAIT};
 unsigned h=covenants_powers_hint();return h<sizeof(hints)/sizeof(hints[0])?hints[h]:0;
}
static COLD void covenants_enemy_generation(unsigned i){
 defeated_enemy_mask&=(unsigned char)~(1u<<i);
 southern_powers_enemy_spawn(i);magma_powers_enemy_spawn(i);underwater_powers_enemy_spawn(i);
 return_powers_enemy_spawn(i);horizons_powers_enemy_spawn(i);covenants_powers_enemy_spawn(i);
}
static COLD void covenants_shot_generation(unsigned i){
 northern_powers_shot_spawn(i);return_powers_shot_spawn(i);
 horizons_powers_shot_spawn(i);covenants_powers_shot_spawn(i);
}
COLD unsigned game_covenants_enemies_alive(void){
 unsigned i,n=0;if(room!=77)return 0;
 for(i=0;i<3;i++)if((covenants_wave_enemies&(1u<<i))&&enemies[i].hp>0&&
  (enemies[i].kind==0||enemies[i].kind==2))n++;
 return n;
}
COLD int game_covenants_spawn_wave(unsigned wave){
 static const CovenantsEnemySpawn waves[3][3]={
  {{64,120,4,0,CREATURE_WOOD},{176,120,4,0,CREATURE_WATER},{0,0,0,0,0}},
  {{64,120,5,0,CREATURE_METAL},{176,120,5,0,CREATURE_EARTH},{120,136,4,2,CREATURE_FIRE}},
  {{72,120,5,0,CREATURE_WATER},{168,120,5,0,CREATURE_WOOD},{120,136,5,2,CREATURE_METAL}}
 };
 unsigned i,count;if(room!=77||wave>3)return 0;
 if(!wave){
  for(i=0;i<3;i++)if((covenants_wave_enemies&(1u<<i))&&(enemies[i].kind==0||enemies[i].kind==2)){
   enemies[i].hp=enemy_hp_q4[i]=enemy_clocks[i]=enemy_windups[i]=0;
   enemy_stagger_ticks[i]=rooted_enemies[i]=slowed_enemies[i]=0;covenants_enemy_generation(i);
  }
  for(i=0;i<12;i++)if((covenants_wave_shots&(1u<<i))&&ordinary_hostile_shots[i]){
   shots[i].life=0;ordinary_hostile_shots[i]=0;covenants_shot_generation(i);
  }
  covenants_wave_enemies=0;covenants_wave_shots=0;return 1;
 }
 if(game_covenants_enemies_alive())return 0;
 count=wave==1?2:3;
 /* No partial wave or actor displacement. A blocked wave remains retryable. */
 for(i=0;i<count;i++){
  const CovenantsEnemySpawn*s=&waves[wave-1][i];
  if(enemies[i].hp>0||covenants_game_solid(s->x,s->y)||
   game_region_actor_overlap(s->x-5,s->y-5,s->x+5,s->y+5))return 0;
 }
 if(!game_covenants_spawn_wave(0))return 0;
 for(i=0;i<count;i++){
  const CovenantsEnemySpawn*s=&waves[wave-1][i];
  enemies[i]=(Enemy){s->x,s->y,s->hp,0,s->kind};enemy_hp_q4[i]=s->hp*16;enemy_phases[i]=s->phase;
  enemy_clocks[i]=enemy_windups[i]=enemy_aimx[i]=enemy_aimy[i]=0;
  enemy_stagger_ticks[i]=rooted_enemies[i]=slowed_enemies[i]=0;
  covenants_wave_enemies|=(unsigned char)(1u<<i);covenants_enemy_generation(i);
 }
 return 1;
}
/* Called only inside the historical authored exposure branch. This consumes
 * one real contact per cast; flash, phase clamps and rewards remain the boss
 * resolver's responsibility exactly as for a weapon contact. */
static COLD int covenants_boss_contact(void){
 unsigned base;if(!covenants_power_time)return 0;
 base=covenants_powers_boss_damage(boss_x,boss_y,16,!boss_flash);
 if(!base)return 0;
 game_boss_hurt(base,0,(unsigned)covenants_power_phase);return 1;
}
static COLD int game_boss_contact(void){
 if(covenants_boss_contact())return 1;
 if(!game_melee_hit(6,boss_x,boss_y,1))return 0;
 game_boss_hurt(weapon_action.damage_q4==48?32:16,weapon_action.attack_q4,weapon_action.element);return 1;
}
/* Older authored phase changes replenish their original power meter. A
 * successful legendary cast retains this same shared meter through dismissal
 * and recovery until its natural expiry; it never gains a phase-change refund. */
static COLD void game_boss_phase_cooldown(void){
 if(!covenants_cooldown_owned)ability_cd=0;
}
/* The same eased follow retains subpixel motion. World-edge and scenery
 * checks keep both its target and next point valid; the player is the safe
 * fallback when a shoulder offset falls outside a road or into an obstacle. */
static COLD void game_companion_follow(void){
 int tx,ty,dx,dy,nx,ny,oldx=cx_q8,oldy=cy_q8;if(!summoned)return;
 tx=px+(face==2?17:-17);ty=py+8;
 if(!game_companion_position_open(tx,ty)){tx=px;ty=py;}
 tx*=256;ty*=256;
 dx=(tx-cx_q8)/6;dy=(ty-cy_q8)/6;
 nx=cx_q8+dx;ny=cy_q8+dy;
 if(game_companion_position_open(nx>>8,ny>>8)){cx_q8=nx;cy_q8=ny;cx=nx>>8;cy=ny>>8;}
 else game_companion_reanchor(px,py);
 dx=cx_q8-oldx;dy=cy_q8-oldy;
 if(dx||dy)covenants_walk_direction=(unsigned char)(ab(dx)>ab(dy)?(dx<0?2:3):(dy<0?1:0));
}
