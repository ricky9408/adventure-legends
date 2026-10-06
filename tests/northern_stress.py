#!/usr/bin/env python3
"""Same-ROM controller branches: native source pixels, input and hardware cadence.

Requires a successful controller-earned Northern journey report. Its snapshot
must match this exact ROM and symbols, including both saved-state and SRAM SHA.
No game-memory writes or cross-cartridge machine states are permitted.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from northern_journey import *

class NorthernStress(NorthernJourney):
    def __init__(self,*args,journey_report,forward_sram=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.source_report=Path(journey_report).resolve();source=json.loads(self.source_report.read_text())
        assert source['controller_only'] and source['game_ram_writes']==0
        assert not source['failures'] and all(c['passed'] for c in source['checks'])
        self.old_ids={1,2,3,4,5,6}
        if forward_sram:
            record=source['snapshots']['09-complete21-independent-reboot'];saved=Path(record['sram_path'])
            if not saved.is_file():saved=self.source_report.parent/saved.name
            assert digest(saved)==record['sram_sha256']
            self.e.load_save(saved);self.e.reset();self.step(150);self.tap('START',2,35);self.settle()
            bank=newest_bank(saved.read_bytes());state=self.state()
            self.check(bytes(state.roster.instances)==bank[160:4000] and bytes(state.quests)==bank[4032:4296] and bytes(state.equipment)==bank[4544:5056],'forward SRAM-only import retains actual earned collection/quest/gear bytes')
            self.check(self.collection()==ALL_FORMS and len(self.live())==11,'fresh target-ROM boot retains genuine21-history/11-instance collection')
            self.snapshots={};self.provenance={'fixture_path':str(saved),'sram_sha256':record['sram_sha256'],'source_rom_sha256':source['rom_sha256'],'source_machine_state_loaded':False,'scope':'Previously controller-earned Northern collection imported as SRAM only into a fresh target. This stress run makes no new acquisition claim.','source_journey':str(self.source_report),'source_journey_sha256':digest(self.source_report),'original_r5_ancestor_sram_sha256':R5_SHA}
            self.snapshot('09-complete21-independent-reboot')
        else:
            assert source['rom_sha256']==self.target_sha and source['symbols_sha256']==self.symbol_sha
            self.snapshots={name:dict(record) for name,record in source['snapshots'].items()}
            for record in self.snapshots.values():
                for field,hash_field in (('state_path','state_sha256'),('sram_path','sram_sha256')):
                    saved_path=Path(record[field])
                    if not saved_path.is_file():
                        sibling=self.source_report.parent/saved_path.name
                        assert sibling.is_file() and digest(sibling)==record[hash_field],'Packaged state/SRAM pair missing or hash-mismatched'
                        record['original_'+field]=record[field];record[field]=str(sibling.resolve())
            self.provenance['same_rom_controller_journey']={'path':str(self.source_report),'sha256':digest(self.source_report)}
            self.restore('09-complete21-independent-reboot')
        self.check(self.get('room')==22,'stress begins from actual completed Northern town')
    def report(self):
        super().report()
        if not hasattr(self,'provenance'):return
        p=self.out/'northern-journey.json';r=json.loads(p.read_text())
        r['suite']='northern-native-stress';r['stress_test_sha256']=digest(__file__)
        (self.out/'northern-stress.json').write_text(json.dumps(r,indent=2)+'\n')
    def pixel_rgb(self,name):
        self.pixel_case(name);cx,cy=self.get('camera_x'),self.get('camera_y');d=self.north['rooms'][self.get('room')-22];w,h=d['size']
        atlas=self.e.bytes(self.sym['north_background_'+d['key']],w*h)
        expected=b''.join(atlas[(cy+y)*w+cx:(cy+y)*w+cx+240] for y in range(160));mask=bytearray(38400)
        tiles=self.e.bytes(0x06010000,32768)
        for o in self.oam():
            assert o['eightbit']
            for sy in range(o['h']):
                y=o['y']+sy
                if not 0<=y<160:continue
                ty=o['h']-1-sy if o['flipy'] else sy
                for sx in range(o['w']):
                    x=o['x']+sx
                    if not 0<=x<240:continue
                    tx=o['w']-1-sx if o['flipx'] else sx
                    index=o['tile']*32+(ty//8)*(o['w']//8)*64+(tx//8)*64+(ty%8)*8+tx%8
                    if tiles[index]:mask[y*240+x]=1
        palette=self.e.bytes(0x05000000,512);colors=[]
        for i in range(256):
            c=int.from_bytes(palette[2*i:2*i+2],'little');colors.append(bytes((((c>>s)&31)<<3)|(((c>>s)&31)>>2) for s in (0,5,10)))
        rgb=self.e.screenshot().tobytes();bad=[i for i in range(38400) if not mask[i] and rgb[i*3:i*3+3]!=colors[expected[i]]]
        self.pixel_cases[-1].update({'rgb_background_pixels':38400-sum(mask),'rgb_mismatches':len(bad),'rgb_examples':bad[:20]})
        self.check(not bad,'native RGB image preserves source behind transparent corner HUD and actors')
    def pixels_and_input(self):
        self.goto(240,204);self.snapshot('stress-town-safe');seen=set()
        for _ in range(14):
            self.step(45);phase=self.get('camera_x')%4
            if phase not in seen:self.pixel_rgb(f'quay-source-alignment-{phase}');seen.add(phase)
            if len(seen)==4:break
            self.step(1,'RIGHT')
        self.check(seen=={0,1,2,3},'all four camera/source word alignments preserve240x160 pixels')
        movements=[]
        for keys in ('RIGHT','RIGHT+UP','RIGHT+DOWN','LEFT+UP'):
            self.restore('stress-town-safe');self.step(30)
            start=[self.get('px_q8'),self.get('py_q8')];self.step(12,keys);end=[self.get('px_q8'),self.get('py_q8')]
            dx,dy=end[0]-start[0],end[1]-start[1];movements.append({'keys':keys,'q8_delta':[dx,dy],'distance_q8':math.hypot(dx,dy),'updates':12})
        axial=movements[0]['distance_q8']
        self.check(axial>0 and all(abs(r['distance_q8']/axial-1)<0.015 for r in movements[1:]),'diagonal controller speed is normalized within1.5percent of cardinal')
        self.cases.append({'case':'normalized-real-controller-input','movements':movements,'passed':True})
        self.restore('stress-town-safe');self.cadence('scrolling-camera-active-updates',240,lambda i:'RIGHT' if i%80<40 else 'LEFT')
        self.restore('stress-town-safe');self.goto(104,208)
        # Capture cold START/tab changes and an actual ordinary rest/save.
        journal={0:'START',5:'A',10:'A',15:'A',20:'A',25:'A',30:'A',40:'DOWN',45:'UP',55:'B'}
        self.cadence('cold-journal-seven-tabs',80,lambda i:journal.get(i,0))
        self.check(self.get('game_state')==PLAY,'journal closes to active game')
        self.cadence('cold-rest-autosave-dialogue',140,lambda i:'A' if i in (0,40,80,120) else 0)
        self.settle();self.check(not self.get('save_failed'),'cold ordinary save succeeds')
        self.snapshot('stress-cold-ui-save-complete')
    def field_stress(self):
        self.restore('09-complete21-independent-reboot');self.equip_item(0,19);self.equip_item(1,35);self.owned_select(20);self.set_command(14)
        self.act(104,208);self.entry(23);self.goto(304,176);self.ready();self.face(2);self.snapshot('stress-field-ready')
        # Keep the bow pointing into open floor to retain two arrows rather than
        # killing the only ranged adversary. Real movement changes camera parity.
        rows=[];last=self.get('frame');page=self.e.read(0x04000000,2)&16;captures=[]
        for n in range(600):
            phase=n%90
            key='A' if phase<24 or phase==48 else 'R' if phase==53 else 'LEFT' if 57<=phase<62 else 'RIGHT' if 67<=phase<72 else 0
            self.step(1,key);now=self.get('frame');newpage=self.e.read(0x04000000,2)&16
            cx,cy=self.get('camera_x'),self.get('camera_y');enemies=self.enemies()
            row={'hardware_frame':self.e.frame,'update_delta':(now-last)&0xffffffff,'page_flip':newpage!=page,'cycles':self.get('render_cycles'),
                'camera':[cx,cy],'arrows':sum(a['active'] for a in self.arrows()),'hostile_shots':sum(bool(s['life'] and s['owner']) for s in self.shots()),
                'enemies':sum(e['hp']>0 for e in enemies),'visible_enemies':sum(e['hp']>0 and cx-8<e['x']<cx+248 and cy-8<e['y']<cy+168 for e in enemies),
                'north_effect':self.get('northern_power_time'),'north_cast':self.get('northern_power_cast_time'),'obj_count':self.get('obj_count'),
                'hp_q4':self.hp_q4(),'fractional_hp':bool(self.hp_q4()%16),'keys':key,'state':self.get('game_state')}
            rows.append(row);last,page=now,newpage
            if row['arrows']==2 and row['hostile_shots'] and row['north_effect'] and row['visible_enemies']>=2:
                if len(captures)<5:
                    name='stress-combined-'+str(len(captures));self.e.screenshot(self.out/(name+'.png'));captures.append({'screenshot':name+'.png',**row})
            if self.get('game_state')!=PLAY:break
        result={'name':'combined-camera-enemies-hostile-shots-two-arrows-new-effect','hardware_frames':len(rows),'max_cycles':max(r['cycles'] for r in rows),
            'max_oam':max(r['obj_count'] for r in rows),'maximum_visible_enemies':max(r['visible_enemies'] for r in rows),
            'maximum_hostile_shots':max(r['hostile_shots'] for r in rows),'two_arrow_frames':sum(r['arrows']==2 for r in rows),
            'new_effect_frames':sum(r['north_effect']>0 for r in rows),'simultaneous_representative_frames':sum(r['arrows']==2 and r['hostile_shots']>0 and r['north_effect']>0 and r['visible_enemies']>=2 for r in rows),
            'distinct_camera_parities':sorted({(r['camera'][0]%4,r['camera'][1]%2) for r in rows}),'captures':captures,'trace':rows}
        self.frame_windows.append(result);self.report()
        self.check(all(r['update_delta']==1 and r['page_flip'] for r in rows) and result['max_cycles']<280896,'combined scene updates and flips once each actual hardware frame')
        self.check(result['max_oam']<=128,'combined scene respects OAM budget')
        self.check(bool(captures),'representative single window includes two arrows, hostile shot, new effect and multiple visible enemies')
        self.snapshot('stress-combined-complete')
    def field_journal(self):
        self.restore('09-complete21-independent-reboot');self.equip_item(0,19);self.equip_item(1,35);self.owned_select(20);self.set_command(14)
        self.act(104,208);self.entry(23);self.goto(304,176);self.ready();self.snapshot('cold-field-journal-ready')
        journal={0:'START',5:'A',10:'A',15:'A',20:'A',25:'A',30:'A',40:'DOWN',45:'UP',55:'B'}
        result=self.cadence('cold-field-journal-with-enemies',80,lambda i:journal.get(i,0))
        self.check(max(row['enemies'] for row in result['trace'])>=5,'cold field journal keeps allfive actual enemies alive')
        self.snapshot('cold-field-journal-complete')
    def run(self,scope='all'):
        if scope in ('all','pixels'):self.pixels_and_input()
        if scope in ('all','field'):self.field_stress()
        if scope in ('all','field-journal'):self.field_journal()
        if scope=='save':
            self.restore('09-complete21-independent-reboot');self.cadence('cold-rest-autosave-dialogue',140,lambda i:'A' if i in (0,40,80,120) else 0);self.settle();self.snapshot('cold-save-complete')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('rom','symbols','output','journey-report'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--forward-sram',action='store_true',help='Import only authenticated earned SRAM into a different target ROM and create fresh target machine states');p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);p.add_argument('--scope',choices=('all','pixels','field','save','field-journal'),default='all');a=p.parse_args()
    run=NorthernStress(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,journey_report=a.journey_report,forward_sram=a.forward_sram)
    try:run.run(a.scope)
    except Exception as e:
        run.failures.append({'error':str(e),'status':run.status()});run.snapshot('stress-failure',settle=False);raise
    finally:run.report();run.e.close()
if __name__=='__main__':main()
