#!/usr/bin/env python3
"""Real-C hold controls plus retained damage/field/lifetime cases; host only."""
from pathlib import Path
import ast,json,os,platform,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/readable-aim-host';OUT.mkdir(parents=True,exist_ok=True)
CASES=[
 ('return','test_return_powers.py','return_powers_host.c',104,False),
 ('underwater','test_underwater_powers.py','underwater_powers_native.c',68,False),
 ('horizons','test_horizons_powers.py','horizons_powers_host.c',106,False),
 ('magma','test_magma_powers.py','magma_powers_native.c',51,True),
]
COMMON=r'''
static void hold_step(void){assert(HOLD(256));updates(1);PREVIEW;}
static void hold_contract(void){unsigned i,c;int time,pose,cd,hp;unsigned identity,action;
 /* Every current command either offers held anticipation or stays on its
  * original non-aimable timeline; no catalog row gains extra live frames. */
 for(c=FIRST_COMMAND;c<=LAST_COMMAND;c++){
  setup(c);assert(POWER(c));time=TIME;pose=POSE;
  if(!CAN_AIM()){assert(!HOLD(256));updates(1);assert(AGE==1&&TIME==time-1);continue;}
  for(i=0;i<60;i++)hold_step();assert(!AGE&&TIME==time&&POSE==pose);
  assert(!HOLD(0));updates(1);assert(AGE==1&&TIME==time-1);
 }
 setup(COMMAND);MAKE_ENEMY;SET_FIELD;assert(POWER(COMMAND));action=ACTION_TOKEN;
 time=TIME;pose=POSE;cd=ability_cd;hp=enemy_hp_q4[0];identity=caster.instance_id;
 for(i=0;i<60;i++)hold_step();
 assert(!AGE&&TIME==time&&POSE==pose&&enemy_hp_q4[0]==hp&&FIELD_PROGRESS==0&&ACTION_TOKEN==action);
 assert(ability_cd==(cd>60?cd-60:0)&&caster.instance_id==identity);
 /* A decision well beyond the original8/12-frame limit is still accepted.
  * It can be revised before release, without restarting or live contacts. */
 assert(CAN_AIM());assert(CHOOSE(FIRST_CHOICE));assert(CAN_AIM());REPEATED_CHOICE;assert(CHOOSE(SECOND_CHOICE));
 hold_step();assert(!AGE&&TIME==time&&enemy_hp_q4[0]==hp);
 assert(!HOLD(0));updates(1);assert(AGE==1&&TIME==time-1&&POSE==pose-1);
 assert(!HOLD(256));updates(1);assert(AGE==2&&TIME==time-2);
 updates((unsigned)time);assert(!TIME);
 /* Merely keeping the key held is bounded: exactly90 frozen updates, then
  * the original effect timeline starts, with no reentry or cooldown refund. */
 setup(COMMAND);assert(POWER(COMMAND));time=TIME;pose=POSE;cd=ability_cd;
 for(i=0;i<90;i++){hold_step();assert(!AGE&&TIME==time&&POSE==pose);}
 assert(!HOLD(256));updates(1);assert(AGE==1&&TIME==time-1);
 assert(ability_cd==(cd>91?cd-91:0));assert(!HOLD(256));
 /* Hitstop/paused engine calls cannot spend the anticipation budget. */
 setup(COMMAND);assert(POWER(COMMAND));for(i=0;i<30;i++)hold_step();
 time=TIME;pose=POSE;cd=ability_cd;hitstop=3;
 for(i=0;i<100;i++)updates(1);
 assert(!AGE&&TIME==time&&POSE==pose&&ability_cd==cd);
 hitstop=0;for(i=0;i<60;i++)hold_step();assert(!HOLD(256));updates(1);assert(AGE==1);
 /* A changed caster cannot keep or reenter an anticipation preview. */
 setup(COMMAND);assert(POWER(COMMAND));hold_step();caster.instance_id++;
 assert(!HOLD(256));updates(1);assert(AGE==1);
 /* Tap/release keeps the original module startup and total live lifetime. */
 setup(COMMAND);assert(POWER(COMMAND));time=TIME;assert(!HOLD(0));updates(1);
 assert(AGE==1&&TIME==time-1);updates((unsigned)(time-1));assert(!TIME);
 RESET();assert(!HOLD(256));
 puts("hold controls: late/revised direction, release,90-frame cap, hitstop, identity, cooldown and original tap lifetime passed");
}
int main(void){assert(!inherited_main());hold_contract();return 0;}
'''
results=[]
with tempfile.TemporaryDirectory(prefix='readable-aim-')as folder:
 folder=Path(folder)
 for prefix,script,fixture,command,magma in CASES:
  tree=ast.parse((ROOT/'tests'/script).read_text())
  sources=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SOURCES'for t in n.targets))
  sources=sources[1:]
  extra=''
  if prefix=='horizons':
   extra='int game_collision_rects(int a,int b,int c,int d,short e[][4],unsigned f){(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;return -1;}\nint underwater_game_supercover(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;return -1;}\n'
   extra+='int game_road_box_touched(unsigned a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;return 0;}\n'
  # Isolated fixtures cannot enter other chapters. Explicit fail-closed stubs
  # make the weak-hook boundary portable to Darwin (no weak-import default).
  for chapter in ('return','horizons','covenants'):
   if chapter==prefix:continue
   extra+=f'''int {chapter}_power_time;
int {chapter}_game_is_room(unsigned a){{(void)a;return 0;}}
int {chapter}_game_clear_box(int a,int b,int c,int d){{(void)a;(void)b;(void)c;(void)d;return 0;}}
int {chapter}_game_supercover(int a,int b,int c,int d){{(void)a;(void)b;(void)c;(void)d;return -1;}}
unsigned {chapter}_game_action_begin(unsigned a){{(void)a;return 0;}}
int {chapter}_game_field_target(unsigned a,int*b,int*c,int*d){{(void)a;(void)b;(void)c;(void)d;return 0;}}
int {chapter}_game_field_hit(unsigned a,unsigned b,unsigned c,unsigned d,unsigned e){{(void)a;(void)b;(void)c;(void)d;(void)e;return 0;}}
void {chapter}_game_revoke_cast(unsigned a){{(void)a;}}
'''
  if prefix=='magma':extra+='int underwater_power_time;\n'
  if prefix in ('magma','underwater'):extra+='int return_legacy_box_certificate(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;return 0;}\n'
  macros={
   'COMMAND':str(command),'POWER':prefix+'_power','HOLD':prefix+'_powers_hold_input',
   'CAN_AIM':prefix+'_powers_can_aim','AGE':prefix+'_power_age','TIME':prefix+'_power_time',
   'POSE':prefix+'_power_cast_time','RESET':prefix+'_powers_reset',
   'FIRST_CHOICE':'16'if prefix=='underwater'else'64','SECOND_CHOICE':'32'if prefix=='underwater'else'128',
   'FIRST_COMMAND':str({'return':91,'underwater':67,'horizons':106,'magma':43}[prefix]),
   'LAST_COMMAND':str({'return':105,'underwater':90,'horizons':121,'magma':66}[prefix]),
   'MAKE_ENEMY':'enemy(0,140,100,10)'if magma else 'enemy(0,120,100,10)'if prefix=='underwater'else 'enemy(0,20,0,0)',
   'SET_FIELD':'chapter_enabled=1;chapter_x=140;chapter_y=100'if magma else 'field_enabled=1;field_x=120;field_y=100'if prefix=='underwater'else'field_count=1;field_x=120;field_y=100',
   'FIELD_PROGRESS':'chapter_used'if magma else'field_calls',
   'ACTION_TOKEN':'chapter_tokens[3]'if magma else'underwater_serial'if prefix=='underwater'else'token',
   'PREVIEW':'draws=0;'+prefix+'_powers_draw();assert(draws<='+('24'if magma else'25')+')'if prefix in ('magma','underwater')else'((void)0)',
   'REPEATED_CHOICE':'((void)0)'if magma else'assert(!CHOOSE(FIRST_CHOICE))',
  }
  header='#define main inherited_main\n#include "'+fixture+'"\n#undef main\n'+extra
  header+='\n'.join('#define '+k+' '+v for k,v in macros.items())+'\n'
  header+='#define CHOOSE(p) (face=((p)==64?1:0),magma_powers_aim())\n'if magma else '#define CHOOSE(p) '+prefix+'_powers_input(p)\n'
  source=folder/(prefix+'.c');source.write_text(header+COMMON)
  for sanitized in (False,True):
   name=prefix+('-sanitized'if sanitized else '-strict');exe=OUT/name
   flags=['-fsanitize=address,undefined','-fno-omit-frame-pointer']if sanitized else []
   gc='-Wl,-dead_strip'if platform.system()=='Darwin'else'-Wl,--gc-sections'
   args=[os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-ffunction-sections','-fdata-sections',gc,'-Isrc','-Itests',*flags,str(source),*sources,'-o',str(exe)]
   subprocess.run(args,cwd=ROOT,check=True)
   subprocess.run([str(exe)],cwd=ROOT,check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
   results.append({'case':name,'passed':True})
(OUT/'report.json').write_text(json.dumps({'scope':__doc__,'results':results},indent=2)+'\n')
