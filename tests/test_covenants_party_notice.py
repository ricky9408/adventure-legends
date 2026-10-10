#!/usr/bin/env python3
"""Real party core with synthetic owned instances: exact notice and no-side-effect rejection.
Native visibility/controller acquisition are separate checks.
"""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
SOURCE=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "quickparty.c"
Save5State adventure_save;
volatile int spirit,game_state,room;
int journal_tab,gfx_companion_frame;
unsigned progression_revision;
static unsigned saves,changes,sounds,title;
/* The production journal raster writes Mode4 halfwords directly. Keep a
 * complete bounded framebuffer even though this suite asserts notice state. */
static unsigned short framebuffer[240*160/2];
unsigned short *screen=framebuffer;
unsigned progression_form_spirit(unsigned id){return creatures_form(id)?0:PROGRESSION_SPIRIT_COUNT;}
unsigned progression_current_spirit(void){return 0;}
int progression_name_id(unsigned form){return (int)form;}
int progression_command_name_id(unsigned command){return (int)command;}
unsigned game_power_cooldown(unsigned base){return base;}
void progression_selection_changed(void){changes++;}
void save_game(void){saves++;}
void toast(int t){(void)t;}
void sfx(int n){(void)n;sounds++;}
void rect(int x,int y,int w,int h,u8 c){(void)x;(void)y;(void)w;(void)h;(void)c;}
void box(int x,int y,int w,int h){(void)x;(void)y;(void)w;(void)h;}
void text(int t,int x,int y,int c){(void)t;(void)x;(void)y;(void)c;}
void centered(int t,int y,int c){if(y==32)title=(unsigned)t;(void)c;}
void sprite(const u8*p,int x,int y,int w,int h,int f){(void)p;(void)x;(void)y;(void)w;(void)h;(void)f;}
const u8*companion_form_pixels(unsigned f,unsigned d,unsigned t){(void)f;(void)d;(void)t;return 0;}
static void header(unsigned expected){title=0;memset(framebuffer,0,sizeof framebuffer);quickparty_draw_journal();assert(title==expected);}
int main(void){unsigned first,second,tests=0;
 for(first=121;first<=128;first++)for(second=121;second<=128;second++)if(first!=second){
  unsigned i,a,b,initial_saves,initial_changes,revision;Save5State before;
  memset(&adventure_save,0,sizeof adventure_save);creatures_roster_init(&adventure_save.roster);
  for(i=0;i<4;i++)assert(creatures_grant(&adventure_save.roster,1+i*3,36,60,0,0)==i);
  a=creatures_grant(&adventure_save.roster,first,36,60,0,0);b=creatures_grant(&adventure_save.roster,second,36,60,0,0);
  assert(a==4&&b==5&&creatures_roster_validate(&adventure_save.roster));
  assert(quickparty_assign(0,a));assert(!menu_notice);before=adventure_save;
  initial_saves=saves;initial_changes=changes;revision=quickparty_revision;
  journal_tab=2;quickparty_menu_slot=1;quickparty_menu_candidate=(int)b;
  for(i=0;i<4;i++){assert(quickparty_menu_input(1));assert(quickparty_menu_detail);assert(!memcmp(&adventure_save,&before,sizeof before));assert(saves==initial_saves&&changes==initial_changes);assert(quickparty_menu_input(1));assert(!quickparty_menu_detail&&menu_notice==2);header(TX_CV_PARTY_ONE);assert(!memcmp(&adventure_save,&before,sizeof before));assert(saves==initial_saves&&changes==initial_changes);}
  assert(quickparty_revision==revision+12);
  assert(quickparty_menu_input(16));assert(!menu_notice);header(TX_Q_PARTY);assert(!memcmp(&adventure_save,&before,sizeof before));assert(saves==initial_saves&&changes==initial_changes);
  assert(quickparty_assign(2,a));assert(!menu_notice);assert(adventure_save.roster.party[2]==a&&adventure_save.roster.party[0]==2);assert(creatures_roster_validate(&adventure_save.roster));
  initial_saves=saves;initial_changes=changes;
  assert(quickparty_assign(2,b));assert(!menu_notice);assert(adventure_save.roster.party[2]==b);assert(saves==initial_saves+1&&changes==initial_changes+1);assert(creatures_roster_validate(&adventure_save.roster));
  assert(!quickparty_assign(2,b));assert(!menu_notice);header(TX_Q_PARTY);assert(saves==initial_saves+1&&changes==initial_changes+1);tests++;
 }
 /* Existing last-member notice remains distinct, with no accidental save. */
 {CreatureU8 party[4]={0,255,255,255};unsigned previous=saves;assert(creatures_party_set(&adventure_save.roster,party,0));assert(!quickparty_assign(0,255));assert(menu_notice==1);header(TX_Q_LAST_MEMBER);assert(saves==previous);}
 printf("PASS: %u ordered legendary pairs; repeat rejection preserves full save/selection and all save/revocation callbacks; move dismisses; existing swap and same-slot replacement work; last-member notice preserved\n",tests);return 0;
}
'''
paths=['src/quickparty.c','src/creatures.c','src/creatures.h','src/creature_data.c','src/ui.h','src/ui.c','src/companion_guide.c','src/companion_guide_text.c','tests/test_covenants_party_notice.py'];pins={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in paths};results={}
with tempfile.TemporaryDirectory(prefix='covenants-party-notice-')as temp:
 p=Path(temp);(p/'test.c').write_text(SOURCE)
 for label,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  exe=p/label;subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc',*flags,str(p/'test.c'),'src/creatures.c','src/creature_data.c','src/companion_guide.c','src/companion_guide_text.c','src/ui.c','-o',str(exe)],cwd=ROOT,check=True)
  result=subprocess.run([str(exe)],text=True,capture_output=True,check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'});print(label,result.stdout,end='');results[label]=result.stdout.strip()
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in pins.items())
(ROOT/'build/covenants-party-notice-host.json').write_text(json.dumps({'scope':__doc__,'results':results,'source_sha256':pins},indent=2)+'\n')
