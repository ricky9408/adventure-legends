#!/usr/bin/env python3
"""Strict native carousel capacity; historical/prepared SRAM, never acquisition.

Six fresh cores cover immediate controller-ready PLAY and settled PLAY with72,
160, and160 stride256 identities. Host preparation uses production creatures
and Save5 APIs. Native operations use only buttons, reads and SRAM boot input;
game-RAM writes and machine-state imports are disabled. Loading observations
remain separately labelled. This gate never replaces the fresh earned route.
"""
import argparse,ctypes as C,gzip,hashlib,json,os,shutil,subprocess,sys,traceback
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from test_save5 import Save
from mgba_runner import keymask

LIMIT=280896
HISTORICAL_SHA='eec8efbfeaf83a51b66faa0c8e9d6a3061af36b88fb6d7b3aa77fbc47107122a'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def prepare_fixtures(source,out,historical):
    names=('save4.c','save5.c','creatures.c','creature_data.c','equipment.c','equipment_data.c','economy.c')
    factory=ROOT/'tests/field_carousel_capacity_fixture.c';exe=out/'create-capacity-fixture'
    command=[os.environ.get('HOST_CC','cc'),'-std=c99','-O2','-Wall','-Wextra','-Werror',
             '-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-I'+str(source/'src'),str(factory),
             *[str(source/'src'/name) for name in names],'-o',str(exe)]
    subprocess.run(command,check=True,capture_output=True,text=True)
    fixture_rows=[]
    for label,extra in (('synthetic160',[]),('synthetic160-stride256',['stride256'])):
        path=out/(label+'.sav')
        result=subprocess.run([str(exe),str(historical),str(path),*extra],check=True,capture_output=True,text=True)
        proof=json.loads(result.stdout)
        assert proof['after_count']==160 and proof['state_bytes']==C.sizeof(Save)
        assert proof['real_save5_validate_and_roundtrip'] and proof['rekey_changes_only_ids_and_next_id']
        fixture_rows.append({'name':label,'path':path,'count':160,'synthetic':True,
                             'sha256':sha(path),'factory_proof':proof})
    return fixture_rows,{'command':command,'factory_source_sha256':sha(factory),'factory_executable_sha256':sha(exe),
                         'codec_sources':{name:sha(source/'src'/name) for name in names}}


class Capacity:
    def __init__(self,args,report):
        self.args=args;self.report=report;self.out=args.output;self.core=None;self.rows=[];self.case=None
        self.phase='cold-title';self.active=False;self.trace=gzip.open(self.out/'native-frames.jsonl.gz','wt')
        self.symbols={v[2]:int(v[0],16) for line in args.symbols.read_text().splitlines() if len(v:=line.split())==3}
        self.lib=C.CDLL(str(args.bridge))
        for name,argv,ret in (
            ('eb_open',[C.c_char_p],C.c_void_p),('eb_close',[C.c_void_p],None),
            ('eb_frames',[C.c_void_p,C.c_uint,C.c_uint],None),
            ('eb_read',[C.c_void_p,C.c_uint32,C.c_uint],C.c_uint32),
            ('eb_bytes',[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint],None),
            ('eb_rgb',[C.c_void_p,C.c_void_p],None),('eb_framecounter',[C.c_void_p],C.c_uint),
            ('eb_faults',[C.c_void_p],C.c_uint),('eb_load_save',[C.c_void_p,C.c_char_p],C.c_int),
            ('eb_reset',[C.c_void_p],None)):
            function=getattr(self.lib,name);function.argtypes=argv;function.restype=ret
        def denied(*a,**kw):raise AssertionError('Capacity gate forbids native RAM writes and machine states')
        self.lib.eb_write=self.lib.eb_state=denied
        report['native_mutation_apis_disabled']=True

    def g(self,name,width=4):return self.lib.eb_read(self.core,self.symbols[name],width)
    def raw(self,address,size):
        value=(C.c_ubyte*size)();self.lib.eb_bytes(self.core,address,value,size);return bytes(value)
    def saved(self):return Save.from_buffer_copy(self.raw(self.symbols['adventure_save'],C.sizeof(Save)))
    def check(self,label,value):
        self.report['checks'].append({'case':self.case,'label':label,'passed':bool(value)})
        assert value,(self.case,label)
    def step(self,count,keys=0,phase=None):
        if phase is not None:self.phase=phase
        self.report['inputs'].append({'case':self.case,'phase':self.phase,'hardware_frame':self.lib.eb_framecounter(self.core),
                                      'frames':count,'physical_keys':keymask(keys)})
        result=[]
        for _ in range(count):
            previous=self.g('frame');before_state=self.g('game_state');page=self.lib.eb_read(self.core,0x04000000,2)&16
            self.lib.eb_frames(self.core,1,keymask(keys));serial=self.g('render_profile_serial')
            row={'case':self.case,'phase':self.phase,'active':self.active,'hardware_frame':self.lib.eb_framecounter(self.core),
                 'logical_frame':self.g('frame'),'before_state':before_state,'delta':(self.g('frame')-previous)&0xffffffff,
                 'flip':bool((self.lib.eb_read(self.core,0x04000000,2)&16)!=page),'profile_serial':serial,
                 'core_faults':self.lib.eb_faults(self.core),**{n:self.g(n)for n in (
                     'game_state','room','quickparty_open','quickparty_visible','quickparty_candidate','quickparty_hold_updates','render_cycles',
                     'save_requested','save_feedback_background','scene_present_phase','ability_cd','summoned',
                     'music_faults','music_recoveries','music_stopped','music_irq_late_max','load_resume_phase')}}
            if self.phase in ('L-arm-and-open','reopen-current'):
                row['roster_sha256']=hashlib.sha256(bytes(self.saved().roster)).hexdigest()
            if not serial&1:
                row['profile']={n:self.g('render_profile_'+n)for n in (
                    'world','card','actors','frame','state','room','update','save','render','music','deferred_actors',
                    'vblank_cycles','vblank_start','vblank_end','commit') if 'render_profile_'+n in self.symbols}
                row['profile']['coherent']=serial==self.g('render_profile_serial')
            self.rows.append(row);result.append(row);self.trace.write(json.dumps(row,separators=(',',':'))+'\n')
            assert not any(row[n]for n in ('core_faults','music_faults','music_recoveries','music_stopped')),row
            if self.active:
                assert row['game_state']==1 and row['delta']==1 and row['flip'] and row['render_cycles']<LIMIT,row
                assert row['music_irq_late_max']<208 and 'profile'in row and row['profile']['coherent'],row
                assert 160<=row['profile']['vblank_start']<=row['profile']['vblank_end']<228,row
        return result
    def drain(self):
        for _ in range(2000):
            if self.g('game_state')==1 and not self.g('save_requested')and not self.g('save_feedback_background'):return
            self.step(1)
        raise AssertionError(('ordinary save did not drain',self.case))
    def shot(self,label):
        pixels=(C.c_ubyte*(240*160*3))();self.lib.eb_rgb(self.core,pixels)
        path=self.out/(self.case+'-'+label+'.png');Image.frombytes('RGB',(240,160),bytes(pixels)).save(path)
        return {'file':path.name,'sha256':sha(path),'hardware_frame':self.lib.eb_framecounter(self.core)}
    @staticmethod
    def summary(rows):
        return {'hardware_frames':len(rows),'update_misses':sum(r['delta']!=1 for r in rows),
                'flip_misses':sum(not r['flip']for r in rows),'overrun_samples':sum(r['render_cycles']>=LIMIT for r in rows),
                'maximum_cycles':max((r['render_cycles']for r in rows),default=0),
                'core_faults':max((r['core_faults']for r in rows),default=0),
                'states':sorted({r['game_state']for r in rows}),
                'background_save_frames':sum(bool(r['save_requested']or r['save_feedback_background'])for r in rows)}
    def measure(self,row,label,count,keys=0):
        values=self.step(count,keys,label);row['phases'].append({'name':label,**self.summary(values)})
        return values
    def run(self,fixture,mode):
        self.case=fixture['name']+'-'+mode;self.rows=[];self.active=False
        row={'name':self.case,'fixture':str(fixture['path']),'fixture_sha256':fixture['sha256'],
             'synthetic_prepared_state':fixture['synthetic'],'historical_fixture':not fixture['synthetic'],
             'earned_collection_claim':False,'opening_mode':mode,'phases':[],'screenshots':[],'pacing_passed':False}
        self.report['cases'].append(row)
        self.core=self.lib.eb_open(str(self.args.rom).encode());assert self.core
        try:
            assert self.lib.eb_load_save(self.core,str(fixture['path']).encode())==1
            self.lib.eb_reset(self.core);self.step(600,0,'cold-title')
            self.check('fixture title ready',self.g('game_state')==0)
            self.step(1,'A','cold-continue');self.step(1,0,'cold-continue')
            for _ in range(6000):
                if self.g('game_state')==1 and not self.g('scene_present_phase'):break
                self.step(1)
            else:raise AssertionError(('controller-ready PLAY not reached',self.case))
            row['cold_boot_and_loading_observations']=self.summary(self.rows)
            row['loading_observations']=self.summary([r for r in self.rows if r['game_state']==15 or r['before_state']==15])
            row['first_controller_ready']={n:self.g(n)for n in ('game_state','scene_present_phase','save_requested','save_feedback_background','frame')}
            self.active=True
            if mode=='settled':
                start=len(self.rows);self.phase='settle-before-opening';self.drain();self.step(40)
                row['phases'].append({'name':'settle-before-opening',**self.summary(self.rows[start:])})
            initial=self.saved().roster;owned=[i for i,c in enumerate(initial.instances)if c.flags&1]
            self.check('native occupied count matches labelled fixture',len(owned)==fixture['count'])
            if 'stride256'in fixture['name']:
                self.check('all160 actual native identities use stride256',all(initial.instances[i].instance_id==1+256*i for i in owned))
            records=bytes(initial.instances);before=bytes(initial);current=initial.party[initial.selected_party]
            row['owned_count']=len(owned);row['first_L_save_flags']={n:self.g(n)for n in ('save_requested','save_feedback_background')}
            arming=self.measure(row,'L-arm-and-open',14,'L')
            self.check('L owns every arming update but becomes visible only at13',
                       all(r['quickparty_open']for r in arming) and all(not r['quickparty_visible']for r in arming[:12])
                       and all(r['quickparty_visible']for r in arming[12:])
                       and all(r['quickparty_candidate']==255 for r in arming[:12]))
            self.check('all arming updates leave roster and selection unchanged',
                       all(r['roster_sha256']==hashlib.sha256(before).hexdigest()for r in arming))
            self.check('visible carousel starts at current owned identity',self.g('quickparty_visible')and self.g('quickparty_candidate')==current)
            self.check('opening leaves complete roster unchanged',bytes(self.saved().roster)==before)
            row['screenshots'].append(self.shot('open'))
            values=self.measure(row,'held-right-repeat',24+6*(len(owned)+2),'L+RIGHT')
            self.check('held Right visits every owned physical instance',set(owned)<={r['quickparty_candidate']for r in values})
            changes=[i for i,r in enumerate(values)if i==0 or r['quickparty_candidate']!=values[i-1]['quickparty_candidate']]
            self.check('native repeat uses24-frame initial and6-frame subsequent spacing',changes[:2]==[0,24] and all(b-a==6 for a,b in zip(changes[1:],changes[2:])))
            self.check('full held preview preserves all roster bytes',bytes(self.saved().roster)==before)
            row['visited_roster_indices']=sorted({r['quickparty_candidate']for r in values});row['repeat_change_offsets']=changes
            self.measure(row,'reverse-left-edge',1,'L+LEFT');chosen=self.g('quickparty_candidate')
            self.measure(row,'release-confirm',12)
            selected=self.saved().roster
            self.check('L release commits exact physical instance',not self.g('quickparty_open')and selected.party[selected.selected_party]==chosen)
            self.check('release preserves every individual record',bytes(selected.instances)==records)
            row['screenshots'].append(self.shot('commit'))
            start=len(self.rows);self.phase='ordinary-save-drain';self.drain();self.step(8)
            row['phases'].append({'name':'ordinary-save-drain',**self.summary(self.rows[start:])})
            self.check('ordinary save returns to settled PLAY',not self.g('save_requested')and not self.g('save_feedback_background'))
            cancel_roster=bytes(self.saved().roster);cd=self.g('ability_cd')
            self.measure(row,'reopen-current',14,'L')
            self.check('reopen becomes visible at committed identity',self.g('quickparty_visible')and self.g('quickparty_candidate')==chosen)
            self.measure(row,'cancel-with-held-B',8,'L+B')
            self.check('B closes selector without assignment',not self.g('quickparty_open')and bytes(self.saved().roster)==cancel_roster)
            self.measure(row,'B-held-after-L-release',8,'B')
            self.check('cancel handoff cannot cast held B',self.g('ability_cd')<=cd and bytes(self.saved().roster)==cancel_roster)
            self.measure(row,'physical-action-release',3)
            row['screenshots'].append(self.shot('cancel'))
            party=list(self.saved().roster.party);start_slot=self.saved().roster.selected_party
            identities=[c.instance_id for c in self.saved().roster.instances]
            for number,duration in enumerate((1,12,1,12)):
                self.measure(row,'original-short-L-'+str(duration)+'-hold',duration,'L')
                self.check('short L owns input without showing the carousel',self.g('quickparty_open')and not self.g('quickparty_visible'))
                self.measure(row,'original-short-L-release',3)
                actual=self.saved().roster
                self.check('short neutral L release preserves original assigned-party order',
                           not self.g('quickparty_open')and actual.selected_party==(start_slot+number+1)%4 and list(actual.party)==party)
                self.check('short cycle retains every owned identity',identities==[c.instance_id for c in actual.instances])
            before_cancel=self.saved().roster.selected_party
            self.measure(row,'short-arm-before-B-release',1,'L')
            self.measure(row,'B-cancel-on-L-release',3,'B')
            self.check('fresh B wins over short L release without cycling or casting',
                       not self.g('quickparty_open')and self.saved().roster.selected_party==before_cancel and self.g('ability_cd')<=cd)
            self.measure(row,'release-short-cancel-buttons',3)
            start=len(self.rows);self.phase='final-background-save-drain';self.drain();self.step(8)
            row['phases'].append({'name':'final-background-save-drain',**self.summary(self.rows[start:])})
            active=[r for r in self.rows if r['active']];row['active_summary']=self.summary(active)
            self.check('all active phases retain strict one-update/flip/cycle budget',not any(row['active_summary'][n]for n in ('update_misses','flip_misses','overrun_samples','core_faults')))
            row['pacing_passed']=True
        finally:
            row['observed_summary']=self.summary(self.rows);self.lib.eb_close(self.core);self.core=None
    def close(self):
        if self.core:self.lib.eb_close(self.core)
        self.trace.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','symbols','bridge','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-root',type=Path,default=ROOT);p.add_argument('--expected-rom-sha')
    a=p.parse_args()
    for name in ('rom','symbols','bridge','output','source_root'):setattr(a,name,getattr(a,name).resolve())
    a.output.mkdir(parents=True,exist_ok=False);report={'scope':__doc__,'result':'RUNNING','controller_only':True,
        'native_game_ram_writes':0,'machine_state_imports':0,'historical_sram_inputs':True,
        'fresh_campaign_acceptance':False,'physical_hardware_tested':False,'limit_cycles':LIMIT,'cases':[],'checks':[],'inputs':[]}
    suite=None
    try:
        if a.expected_rom_sha:assert sha(a.rom)==a.expected_rom_sha,'Unexpected candidate ROM'
        manifest=a.rom.parent/'source-hashes.json';sources=json.loads(manifest.read_text())
        assert all(sha(a.source_root/name)==value for name,value in sources.items()),'Candidate source receipt differs'
        candidate=a.output/'candidate';candidate.mkdir()
        for path in (a.rom,a.symbols,a.rom.with_suffix('.elf'),manifest):shutil.copyfile(path,candidate/path.name)
        a.rom=candidate/a.rom.name;a.symbols=candidate/a.symbols.name
        origin=a.bridge;a.bridge=a.output/'native-bridge.so';shutil.copyfile(origin,a.bridge)
        assert sha(origin)==sha(a.bridge),'Supplied bridge copy changed'
        report.update(rom_sha256=sha(a.rom),symbols_sha256=sha(a.symbols),elf_sha256=sha(a.rom.with_suffix('.elf')),
            source_manifest_sha256=sha(manifest),runtime_source_inputs=len(sources),bridge_sha256=sha(a.bridge),harness_sha256=sha(__file__))
        for rel in ('tests/field_carousel_capacity_native.py','tests/field_carousel_capacity_fixture.c','tests/test_save5.py','tests/test_save4.py','tools/mgba_runner.py'):
            target=a.output/'helper-source'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)
        historical=ROOT/'tests/fixtures/v5-revision9/covenants-all128-72-cold.sav'
        assert sha(historical)==HISTORICAL_SHA,'Historical fixture changed'
        preparation=a.output/'fixture-preparation';preparation.mkdir()
        historical_copy=preparation/historical.name;shutil.copyfile(historical,historical_copy)
        fixtures,proof=prepare_fixtures(a.source_root,preparation,historical_copy)
        fixtures.insert(0,{'name':'historical72','path':historical_copy,'count':72,'synthetic':False,'sha256':HISTORICAL_SHA})
        report['fixture_factory']=proof
        (preparation/'provenance.json').write_text(json.dumps({'factory':proof,'fixtures':[{**v,'path':str(v['path'])}for v in fixtures]},indent=2)+'\n')
        suite=Capacity(a,report)
        for fixture in fixtures:
            for mode in ('immediate','settled'):suite.run(fixture,mode)
        assert len(report['cases'])==6 and all(row['pacing_passed']for row in report['cases'])
        report['result']='PASS'
    except Exception as error:
        report['result']='FAIL';report['error']=repr(error);report['traceback']=traceback.format_exc()
    finally:
        if suite:suite.close()
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'result':report['result'],'checks':len(report['checks']),'report':str(a.output/'report.json')}))
    return int(report['result']!='PASS')


if __name__=='__main__':raise SystemExit(main())
