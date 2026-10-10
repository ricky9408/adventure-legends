/* Real generated text/production draw calls. Portraits are host stand-ins. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "assets.h"
#include "ui.h"
#include "progression.h"
#include "journal_nav.h"
#include "gear_menu.h"
#include "quickparty.h"
extern int journal_tab;
extern unsigned covenants_game_journal_selection;
static union{unsigned short words[19200];unsigned char pixels[38400];}fb;
unsigned short*screen=fb.words;
static unsigned bad_bounds,empty_labels;
void rect(int x,int y,int w,int h,unsigned char c){int a,b;assert(x>=0&&y>=0&&x+w<=240&&y+h<=160);for(b=0;b<h;b++)for(a=0;a<w;a++)fb.pixels[(y+b)*240+x+a]=c;}
void box(int x,int y,int w,int h){rect(x,y,w,h,1);rect(x,y,w,1,PAL_GOLD2);rect(x,y+h-1,w,1,PAL_GOLD2);rect(x,y,1,h,PAL_GOLD2);rect(x+w-1,y,1,h,PAL_GOLD2);}
void text_spans(const UiText*t,int x,int y,int color){const UiRun*r;unsigned i,j;if(x<8||x+t->width>232||y<31||y+t->height>154){fprintf(stderr,"bounds: at%d,%d %ux%u\n",x,y,t->width,t->height);bad_bounds++;}r=t->runs[x&1];for(i=0;i<t->count[x&1];i++)for(j=0;j<r[i].count;j++){unsigned pair=(unsigned)(y*120+(x>>1))+r[i].offset+j;assert(pair<19200);if(r[i].mask&1)fb.pixels[pair*2]=(unsigned char)color;if(r[i].mask&2)fb.pixels[pair*2+1]=(unsigned char)color;}}
void text(int id,int x,int y,int color){assert(id>=0&&id<TX_COUNT);if(id==TX_G_EMPTY)empty_labels++;text_spans(&ui_texts[id],x,y,color);}
void centered(int id,int y,int color){text(id,(240-ui_texts[id].width)/2,y,color);}
void sprite(const unsigned char*p,int x,int y,int w,int h,int flash){(void)p;(void)flash;rect(x,y,w,h,PAL_TEAL2);}
static const unsigned char blank[256]={0};
const unsigned char*companion_form_pixels(unsigned f,unsigned d,unsigned n){(void)f;(void)d;(void)n;return blank;}
#define PORTRAIT(name) const unsigned char*name(unsigned f){(void)f;return 0;}
PORTRAIT(evolution_art_portrait)
PORTRAIT(regional_creature_art_portrait)
PORTRAIT(northern_creature_art_portrait)
PORTRAIT(southern_creature_art_portrait)
PORTRAIT(magma_creature_art_portrait)
PORTRAIT(underwater_creature_art_portrait)
PORTRAIT(return_creature_art_portrait)
PORTRAIT(horizons_creature_art_portrait)
PORTRAIT(covenants_creature_art_portrait)
static void clear(void){memset(&fb,0,sizeof fb);}
static void capture(const char*name){const char*dir=getenv("PLAYER_MENU_CAPTURE_DIR");char path[1024];FILE*f;unsigned i;if(!dir)return;snprintf(path,sizeof path,"%s/%s.ppm",dir,name);f=fopen(path,"wb");assert(f);fprintf(f,"P6\n240 160\n255\n");for(i=0;i<38400;i++){unsigned c=game_palette[fb.pixels[i]];fputc((int)((c&31)*255/31),f);fputc((int)(((c>>5)&31)*255/31),f);fputc((int)(((c>>10)&31)*255/31),f);}assert(!fclose(f));}
void menu_visual_checks(void){unsigned i,form;bad_bounds=0;clear();journal_nav_open();assert(journal_nav_draw());capture("hub-layout");journal_nav_category=5;journal_nav_input(1);clear();assert(journal_nav_draw());capture("quest-regions-layout");journal_nav_quest=8;journal_nav_input(1);covenants_game_journal_selection=11;clear();assert(journal_nav_draw());capture("quest-list-layout");for(i=0;i<8;i++){journal_tab=5+(int)i;journal_nav_detail=0;clear();assert(journal_nav_draw());}journal_tab=16;clear();assert(journal_nav_draw());capture("controls-layout");journal_tab=4;gear_menu_reset();clear();gear_menu_draw();capture("equipment-layout");for(i=0;i<5;i++){gear_menu_slot=(int)i;gear_menu_candidate=255;clear();gear_menu_draw();}
 for(i=0;i<EQUIPMENT_AUTHORED_COUNT;i++){unsigned id=equipment_authored_ids[i],ref;equipment_init(&adventure_save.equipment);if(id!=EQUIPMENT_STARTER_ID)assert(equipment_claim(&adventure_save.equipment,id,i,0)==EQUIPMENT_OK);ref=equipment_find(&adventure_save.equipment,id);assert(ref<48);gear_menu_slot=equipment_definition(id)->slot;gear_menu_candidate=(int)ref;clear();empty_labels=0;gear_menu_draw();assert(!empty_labels);if(id==40)capture("wayfarer-coat-layout");if(id==89)capture("porchlight-ring-layout");}
 journal_tab=2;quickparty_menu_reset();clear();quickparty_draw_journal();capture("party-layout");journal_tab=3;progression_menu_reset();clear();progression_draw_tab();capture("growth-layout");for(form=1;form<129;form++)if(creatures_form(form)){CreatureInstance*c=&adventure_save.roster.instances[0];c->form_id=(CreatureU8)form;c->polarity=creatures_form(form)->polarity;progression_menu_reset();clear();progression_draw_tab();}assert(!bad_bounds);puts("PASS host layout: all48 gear names/comparisons, all enabled forms and menu/list text fit; portraits are stand-ins");}

/* Additional host rasters for the readable full-width companion detail. */
#include "companion_guide.h"
void companion_visual_checks(void){
 static const unsigned forms[]={1,4,7,10,13,37,38,39,49,68,105,121,128};unsigned i;
 for(i=0;i<sizeof forms/sizeof forms[0];i++){
  CreatureInstance c;const CreatureForm*f=creatures_form(forms[i]);char label[80];memset(&c,0,sizeof c);c.form_id=f->id;c.polarity=f->polarity;c.level=50;c.equipped[0]=f->signature_ability;
  clear();companion_guide_page=0;companion_guide_draw(&c,f->signature_ability,1);snprintf(label,sizeof label,"companion-form-%u-combat",f->id);capture(label);
  clear();companion_guide_page=1;companion_guide_draw(&c,f->signature_ability,1);snprintf(label,sizeof label,"companion-form-%u-field",f->id);capture(label);
 }
 {
  extern unsigned progression_evolution_target,progression_evolution_reason,progression_evolution_count;
  for(i=0;i<CREATURE_EVOLUTION_COUNT;i++){
   char label[80];progression_evolution_target=creature_evolutions[i].to;progression_evolution_reason=CREATURE_EVOLVE_READY;progression_evolution_count=creatures_evolution_count(creature_evolutions[i].from);
   clear();progression_draw_confirm();
   if(creature_evolutions[i].from==37||creature_evolutions[i].from==49||creature_evolutions[i].from==1){snprintf(label,sizeof label,"companion-evolution-%u-to-%u",creature_evolutions[i].from,creature_evolutions[i].to);capture(label);}
  }
 }
 assert(!bad_bounds);
}
