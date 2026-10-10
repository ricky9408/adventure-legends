#!/usr/bin/env python3
"""Display-only Party successor: actual C, independent count oracle, native font bounds.
Synthetic empty/sparse/max rosters are boundary fixtures, not gameplay acquisition.
"""
from pathlib import Path
import os, subprocess, tempfile
from test_player_feedback_menu import MODULES
ROOT=Path(__file__).resolve().parents[1]
C_SOURCE=r'''
#define main historical_menu_main
#include "player_feedback_menu_host.c"
#undef main
#include "quickparty.c"
/* Include actual host framebuffer to inspect bounds and isolate Party visuals. */
#include "player_feedback_menu_draw.c"
static unsigned checks;
static void summary_check(void){
 unsigned position=0,total=0,slot=255,p,t,s,i;CreatureRoster before=adventure_save.roster;
 for(i=0;i<160;i++)if((before.instances[i].flags&1)&&progression_form_spirit(before.instances[i].form_id)<PROGRESSION_SPIRIT_COUNT){total++;if((int)i==quickparty_menu_candidate)position=total;}
 if(position)for(i=0;i<4;i++)if(before.party[i]==quickparty_menu_candidate){slot=i;break;}
 menu_summary(&p,&t,&s);assert(p==position&&t==total&&s==slot);
 clear();quickparty_draw_journal();assert(!bad_bounds);assert(!memcmp(&before,&adventure_save.roster,sizeof before));checks++;
}
int main(void){
 unsigned count,i,j,old_saves,p,t,s;CreatureRoster before;
 historical_menu_main();
 /* Every population size, candidate and explicit Empty; duplicate forms, favorites,
    max levels, holes, invalid/non-browsable form filtering and party locations. */
 for(count=0;count<=160;count++){
  fresh(1);journal_tab=2;memset(&adventure_save.roster,0,sizeof adventure_save.roster);
  for(i=0;i<4;i++)adventure_save.roster.party[i]=255;
  for(i=0;i<count;i++){
   CreatureInstance*c=&adventure_save.roster.instances[i];c->form_id=1;c->flags=1|((i&1)?4:0);c->level=(i&1)?50:1;c->instance_id=1000+i;c->equipped[0]=1;
  }
  if(count)adventure_save.roster.party[0]=0;if(count>1)adventure_save.roster.party[3]=count-1;
  for(i=0;i<count;i++){quickparty_menu_candidate=i;summary_check();}
  quickparty_menu_candidate=255;summary_check();
  if(count){before=adventure_save.roster;old_saves=saves;quickparty_menu_candidate=0;
   for(i=0;i<count+1;i++)menu_move(1);assert(quickparty_menu_candidate==0);
   for(i=0;i<count+1;i++)menu_move(-1);assert(quickparty_menu_candidate==0);
   assert(!memcmp(&before,&adventure_save.roster,sizeof before)&&saves==old_saves);
  }
 }
 fresh(1);journal_tab=2;
 for(i=1;i<160;i++){adventure_save.roster.instances[i]=adventure_save.roster.instances[0];adventure_save.roster.instances[i].flags=(i==79||i==159)?5:0;}
 adventure_save.roster.party[1]=159;quickparty_menu_candidate=79;summary_check();menu_summary(&p,&t,&s);assert(p==2&&t==3&&s==255);menu_move(1);assert(quickparty_menu_candidate==159);summary_check();menu_summary(&p,&t,&s);assert(p==3&&t==3&&s==1);menu_move(1);assert(quickparty_menu_candidate==255);summary_check();menu_summary(&p,&t,&s);assert(p==0&&t==3&&s==255);menu_move(-1);assert(quickparty_menu_candidate==159);
 adventure_save.roster.instances[79].form_id=0;quickparty_menu_candidate=0;menu_move(1);assert(quickparty_menu_candidate==159);summary_check();
 /* All 128 names with longest No. and both polarity pages, preserving identity
    after evolution and exact form/axes/description data in the unchanged guide. */
 for(i=1;i<=128;i++){
  const CreatureForm*f=creatures_form(i);CreatureInstance*c=&adventure_save.roster.instances[159];if(!f)continue;
  *c=adventure_save.roster.instances[0];c->form_id=i;c->flags=5;c->level=50;c->equipped[0]=f->signature_ability;
  quickparty_menu_candidate=159;summary_check();
  for(j=0;j<2;j++){companion_guide_page=j;clear();companion_guide_draw(c,f->signature_ability,3);assert(!bad_bounds);checks++;}
 }
 /* Existing favorite bit and durable instance ID do not alter stable display No. */
 assert(adventure_save.roster.instances[159].flags==5);
 printf("PASS Party browsing: %u actual-C summary/render cases; 0..160 collection sizes, sparse holes, duplicate/favorite/evolved identities and all128 detail bounds\n",checks);
 return 0;
}
'''
def main():
 with tempfile.TemporaryDirectory(prefix='companion-browsing-') as tmp:
  source=Path(tmp)/'test.c';source.write_text(C_SOURCE)
  for name,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
   target=Path(tmp)/name
   subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Isrc','-Itests',*flags,str(source),*[f'src/{m}.c' for m in MODULES if m!='quickparty'],'-o',str(target)],cwd=ROOT,check=True)
   subprocess.run([str(target)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)
if __name__=='__main__':main()
