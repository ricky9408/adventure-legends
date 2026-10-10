#!/usr/bin/env python3
"""Controller-only isolated opening, skip, cold-save and 59.73Hz cadence proof.

Existing saves are historical fixtures for compatibility only. No memory writes
or emulator machine states. All new first-checkpoint saves are controller-earned.
"""
import argparse,atexit,ctypes as C,gzip,hashlib,json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
from player_feedback_native import Native
from mgba_runner import keymask
from test_save5 import Save
class ReadOnlyNative(Native):
 def write(self,*a,**kw):raise AssertionError('No game memory writes')
 def state(self,*a,**kw):raise AssertionError('No machine states')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists();a.output.mkdir(parents=True)
 rom=ROOT/'build/emberbond.gba';symbols=ROOT/'build/emberbond.sym'
 frozen=json.loads((ROOT/'build/source-hashes.json').read_text());assert all(sha(ROOT/f)==h for f,h in frozen.items())
 sym={v[2]:int(v[0],16)for line in symbols.read_text().splitlines() if len(v:=line.split())==3}
 fixture=ROOT/'tests/fixtures/v5-revision2/all-eleven-town.sav';assert sha(fixture)=='74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106'
 report={'scope':__doc__,'rom_sha256':sha(rom),'symbols_sha256':sha(symbols),'elf_sha256':sha(rom.with_suffix('.elf')),'source_hashes_sha256':sha(ROOT/'build/source-hashes.json'),'bridge_sha256':sha(a.bridge),'harness_sha256':sha(__file__),'fixture_sha256':sha(fixture),'controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'checks':[],'sessions':[],'screenshots':[]}
 trace=gzip.open(a.output/'frames.jsonl.gz','wt');inputs_trace=gzip.open(a.output/'inputs.jsonl.gz','wt');e=None;row=None
 def check(label,value):
  report['checks'].append({'session':row['name'],'check':label,'passed':bool(value)});assert value,(row['name'],label,{n:g(n)for n in ('game_state','frame','room','save_failed')})
 def preserve_failure():
  # atexit covers assertions anywhere in this existing controller harness.
  # Timeout/SIGKILL still leaves the incrementally flushed frame/input trace.
  if (a.output/'report.json').is_file():return
  report['result']='FAIL_INCOMPLETE';report['failure_session']=row['name'] if row else None
  (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
  try:
   if e and e.ptr:
    e.screenshot(a.output/'failure.png')
    (a.output/'failure-test-cartridge.sav').write_bytes(e.bytes(0x0e000000,32768))
  except Exception as capture_error:print('Failure capture unavailable:',capture_error,file=sys.stderr)
  finally:
   trace.close();inputs_trace.close()
   if e and e.ptr:e.close()
 atexit.register(preserve_failure)
 def g(name,width=4):return e.read(sym[name],width)
 def raw():return e.bytes(0x0e000000,32768)
 def snapshot(name):
  path=a.output/(name+'.sav');path.write_bytes(raw());return path
 def state_bytes():return e.bytes(sym['adventure_save'],C.sizeof(Save))
 def step(n,k=0,measured=True):
  row['inputs'].append({'frame':e.frame,'frames':n,'keys':keymask(k)})
  inputs_trace.write(json.dumps({'input':row['inputs'][-1],'session':row['name']})+'\n');inputs_trace.flush();trace.flush()
  for _ in range(n):
   before=g('frame');oldstate=g('game_state');oldpage=e.read(0x04000000,2)&16;e.frames(1,k)
   f={'session':row['name'],'hw':e.frame,'state':g('game_state'),'delta':(g('frame')-before)&0xffffffff,'flip':(e.read(0x04000000,2)&16)!=oldpage,'cycles':g('render_cycles'),'faults':e.lib.eb_faults(e.ptr),'measured':measured}
   trace.write(json.dumps(f,separators=(',',':'))+'\n');assert not f['faults'];assert not g('save_failed')
   if measured:
    row['frames']+=1;row['peak_cycles']=max(row['peak_cycles'],f['cycles']);row['flip_misses']+=not f['flip'];row['overruns']+=f['cycles']>=280896
    # New-game initialization resets the simulation clock, by design.
    row['update_misses']+=f['delta']!=1 and not(oldstate in(0,9)and g('game_state')==14 and g('frame')==0)
 def tap(k,hold=2,release=4):step(hold,k);step(release)
 def boot(name,save=None):
  nonlocal e,row
  if e:e.close()
  row={'name':name,'cadence_scope':'opening_and_field','inputs':[],'frames':0,'peak_cycles':0,'flip_misses':0,'update_misses':0,'overruns':0};report['sessions'].append(row)
  e=ReadOnlyNative(str(rom),str(a.bridge));e.lib.eb_write=e.write;e.lib.eb_state=e.state
  if save:e.load_save(save);e.reset()
  step(160,measured=False);check('cold boot to title',g('game_state')==0)
 def enter(existing=False,key='A',hold=2):
  if existing:tap('DOWN');tap('A');check('new-game overwrite confirmation retained',g('game_state')==9)
  step(hold,key);check('new adventure begins with first opening page',g('game_state')==14 and g('opening_page',1)==0)
 def settle(expected_room=0):
  for _ in range(1600):
   if g('game_state')==1 and not g('save_requested') and not g('save_feedback_background') and not g('scene_present_phase'):break
   step(1)
  else:raise AssertionError('first checkpoint did not settle')
  step(4);check('saved village with no failure',(expected_room is None or g('room')==expected_room) and g('has_save')==1 and g('save_failed')==0)
 def shot(name):
  path=a.output/(name+'.png');e.screenshot(path);report['screenshots'].append({'file':path.name,'sha256':sha(path),'size':[240,160],'session':row['name'],'frame':e.frame})
 def continue_check(name,path,expected=None):
  boot(name,path);row['cadence_scope']='cold_continue_observed';check('completed or previous save remains recognizable',g('has_save')==1);tap('START');settle();check('Continue never replays opening',g('game_state')==1)
  if expected is not None:check('prior roster remains intact',e.bytes(sym['adventure_save']+Save.roster.offset,C.sizeof(Save._fields_[1][1]))==expected)
 boot('historical-reference',fixture);row['cadence_scope']='cold_continue_observed';tap('A');settle(None);historical_state=state_bytes()
 # Entry buttons must first be released. Ignored buttons cannot mutate game.
 for key in('A','START'):
  boot('empty-held-'+key);before=raw();enter(key=key,hold=120);check('held title control cannot advance or skip',g('opening_page',1)==0 and raw()==before)
  state=state_bytes();positions=(g('px'),g('py'),g('summoned'),g('spirit'));step(5);tap('SELECT+R+B+L+LEFT+RIGHT+UP+DOWN',60,5)
  check('unrelated controls cannot move, attack, summon, select or save',state_bytes()==state and positions==(g('px'),g('py'),g('summoned'),g('spirit')) and raw()==before and not g('save_requested'))
  step(120,'A');check('held A advances exactly one page',g('opening_page',1)==1);step(5);step(120,'START');settle();check('held skip cannot open journal or act after save',g('game_state')==1 and g('summoned')==0 and not g('swing'));path=snapshot('held-'+key+'-completed');continue_check('continue-held-'+key,path)
 # Every pre-finish page preserves all32KiB of SRAM, including existing saves.
 for old in(False,True):
  for target in range(8):
   boot(('old'if old else'empty')+'-interrupt-'+str(target),fixture if old else None);before=raw();enter(existing=old);step(5)
   for _ in range(target):tap('A')
   step(90);check('opening page stable before interruption',g('opening_page',1)==target and g('game_state')==14)
   check('every SRAM byte survives unfinished intro',raw()==before);path=snapshot(('old'if old else'empty')+'-interrupted-'+str(target))
   boot(('old'if old else'empty')+'-reboot-'+str(target),path);check('reset preserves prior save availability',g('has_save')==int(old));check('cold boot preserves exact SRAM',raw()==before)
   if old:row['cadence_scope']='cold_continue_observed';tap('A');settle(None);check('old Continue bypasses opening',g('game_state')==1)
   else:enter();step(5);check('unfinished empty new game restarts opening',g('opening_page',1)==0)
 # A visible Start skip is safe from every story beat and earns one checkpoint.
 for target in range(8):
  boot('skip-'+str(target));enter();step(5)
  for _ in range(target):tap('A')
  tap('START');settle();path=snapshot('skip-'+str(target)+'-village');continue_check('skip-'+str(target)+'-continue',path)
 # Full eight-page play-through, readable native captures and return to control.
 boot('read-entire-opening');before=raw();enter();step(5)
 for target in range(8):
  step(96);check('correct ordered page',g('opening_page',1)==target);check('no save until final page is completed',raw()==before);shot('page-'+str(target));tap('A')
 settle();shot('completed-village');completed=snapshot('read-completed-village')
 check('new checkpoint has initial campaign only',g('chapter_flags')==g('room_flags')==g('optional_flags')==g('story_seen')==0)
 check('initial companion slots preserved',[i.form_id for i in Save.from_buffer_copy(state_bytes()).roster.instances if i.flags&1]==[1,4])
 tap('START');check('journal available immediately',g('game_state')==3);shot('journal-hub');tap('START');check('journal closes safely',g('game_state')==1)
 # Show natural elder follow-up; no changed collision or field controls.
 step(18,'UP');tap('A');check('elder conversation still reachable',g('game_state')==2);shot('elder-followup');tap('A');settle()
 continue_check('read-completed-continue',completed);new_state=state_bytes();shot('cold-continue-village')
 # Confirmation cancel remains byte-pure on an older checkpoint.
 for cancel in('B','START','A+B'):
  boot('cancel-'+cancel,fixture);before=raw();tap('DOWN');tap('A');check('explicit replacement confirmation appears',g('game_state')==9);tap(cancel);check('cancel returns title without changing SRAM',g('game_state')==0 and raw()==before)
 # Interrupt each native hardware frame of first-checkpoint publication.
 for old in(False,True):
  boot(('old'if old else'empty')+'-first-write',fixture if old else None);enter(existing=old);step(5)
  cut_paths=[];step(1,'START')
  for index in range(1600):
   cut_paths.append(snapshot(('old'if old else'empty')+'-commit-cut-'+str(index)))
   if g('game_state')==1 and not g('save_requested') and not g('save_feedback_background'):break
   step(1)
  else:raise AssertionError('first checkpoint never ended')
  check('first save completed',g('has_save')==1)
  for index,path in enumerate(cut_paths):
   boot(('old'if old else'empty')+'-commit-reboot-'+str(index),path)
   if old:check('previous valid save survives every publication interruption',g('has_save')==1)
   if g('has_save'):
    row['cadence_scope']='cold_continue_observed';tap('A');settle(None);s=Save.from_buffer_copy(state_bytes());count=sum(bool(i.flags&1)for i in s.roster.instances)
    check('power cut recovers whole previous or whole new adventure',state_bytes() in ((new_state,historical_state)if old else(new_state,)) and g('game_state')==1)
    if count==2:check('new first checkpoint resumes in village without opening',g('room')==0)
   else:check('unfinished empty first checkpoint remains a new cartridge',not old)
 e.close();trace.close();inputs_trace.close()
 report['metrics']={k:sum(r[k]for r in report['sessions'])for k in('frames','flip_misses','update_misses','overruns')};report['metrics']['peak_cycles']=max(r['peak_cycles']for r in report['sessions'])
 report['cadence_by_scope']={}
 for scope in('opening_and_field','cold_continue_observed'):
  selected=[r for r in report['sessions']if r['cadence_scope']==scope]
  report['cadence_by_scope'][scope]={k:sum(r[k]for r in selected)for k in('frames','flip_misses','update_misses','overruns')}
  report['cadence_by_scope'][scope]['peak_cycles']=max(r['peak_cycles']for r in selected)
 report['limitations']=['Cold Continue uses the inherited synchronous save-load path; its measured stalls are reported separately and are not a 59.73Hz pass. Physical hardware and the whole gameplay campaign were not tested by this opening-only suite.']
 report['result']='PASS_OPENING_AND_SAVE'if not any(report['cadence_by_scope']['opening_and_field'][k]for k in('flip_misses','update_misses','overruns'))else'FAIL_OPENING_CADENCE'
 assert all(sha(ROOT/f)==h for f,h in frozen.items());shutil.copyfile(__file__,a.output/'opening_scene_native.py')
 (a.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'result':report['result'],'checks':len(report['checks']),'sessions':len(report['sessions']),'cadence_by_scope':report['cadence_by_scope']}));return report['result']!='PASS_OPENING_AND_SAVE'
if __name__=='__main__':raise SystemExit(main())
