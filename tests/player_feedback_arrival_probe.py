#!/usr/bin/env python3
"""Observe native arrival admission, scene paint, page copy and live resumption.

The focused town route uses controller input and authentic accepted SRAM only.
The optional portal route retains the standard suite's explicit late-room RAM
preparation. This observer never imports a machine state or changes game RAM.
"""
import argparse,ctypes as C,hashlib,json,shutil,struct
from pathlib import Path
from player_feedback_native import Run,sha,LIMIT,ROOT
from mgba_runner import keymask

FROZEN=('game_state','room','px','py','px_q8','py_q8','cx','cy','cx_q8','cy_q8',
        'ticks','transition','area_ticks','toast_ticks','hitstop','invuln',
        'ability_cd','heal_cd','stone_guard','guard_invuln','power_effect',
        'swing','sword_cd','combo_timer','boss_time','summoned','quickparty_open')

class Probe(Run):
    def __init__(self,a):
        super().__init__(a);self.watch=False;self.arrivals=[];self.active=None
        elf=self.rom.with_suffix('.elf')
        if elf.exists():self.hashes['elf_sha256']=sha(elf)
        helper=ROOT/'tests/magma_journey.py';target=self.out/'test-source/tests/magma_journey.py'
        shutil.copyfile(helper,target);self.hashes['test_sources']['tests/magma_journey.py']=sha(target)
    def play(self,saved=False):
        # This probe certifies live arrivals. Existing cold validation and its
        # presentation remain fully recorded under the parent's cold phases.
        watching=self.watch;self.watch=False
        try:return super().play(saved)
        finally:self.watch=watching
    def frozen(self):return {n:self.g(n) for n in FROZEN if n in self.sym}
    def display(self,tiles=None):
        io=self.e.lib.eb_io16;io.argtypes=[C.c_void_p,C.c_uint];io.restype=C.c_uint
        oam=self.e.bytes(0x07000000,1024);vram=self.e.bytes(0x06010000,32768)
        if tiles is None:
            tiles=set();mapping_1d=bool(self.e.read(0x04000000,2)&64)
            sizes=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))
            for i in range(128):
                a,b,c=struct.unpack_from('<HHH',oam,i*8);shape=a>>14
                if shape==3 or (not a&256 and a&512):continue
                w,h=sizes[shape][b>>14];x=b&511;y=a&255
                if x>=240:x-=512
                if y>=160:y-=256
                scale=2 if a&256 and a&512 else 1
                if x>=240 or y>=160 or x+w*scale<=0 or y+h*scale<=0:continue
                units=2 if a&8192 else 1;base=(c&1023)&(~1 if units==2 else 1023);stride=w//8*units if mapping_1d else 32
                for row in range(h//8):
                    for col in range(w//8*units):tiles.add((base+row*stride+col)&1023)
            tiles=sorted(tiles)
        relevant=b''.join(struct.pack('<H',tile)+vram[tile*32:(tile+1)*32] for tile in tiles)
        return {'rgb':hashlib.sha256(self.e.screenshot().tobytes()).hexdigest(),
                'oam':hashlib.sha256(oam).hexdigest(),'visible_obj_tiles':tiles,
                'visible_obj_sha256':hashlib.sha256(relevant).hexdigest(),
                'all_obj_sha256':hashlib.sha256(vram).hexdigest(),
                'obj_palette_sha256':hashlib.sha256(self.e.bytes(0x05000200,512)).hexdigest(),
                'blend':[io(self.e.ptr,x) for x in (0x50,0x52,0x54)]}
    def step(self,n=1,keys=0,phase='measured'):
        if not self.watch:return super().step(n,keys,phase)
        for _ in range(n):
            before_phase=self.g('scene_present_phase');before_room=self.g('room')
            before_display=self.display() if before_phase==0 else None
            before_image=self.e.screenshot() if before_phase==0 else None
            fixed=self.frozen() if before_phase else None
            writer=(self.g('writer_phase'),self.g('writer_position'))
            actual=1023 if before_phase else keymask(keys)
            super().step(1,actual,phase)
            after_phase=self.g('scene_present_phase');sample=self.frames[-1]
            if not before_phase and after_phase:
                self.check('admission reaches the retained-display phase',after_phase==2,after_phase)
                # runFrame stops at VBlank before obj_commit and the page flip.
                # This sample is the final normal source frame. The retained
                # admission frame appears at the following hardware boundary.
                display=self.display();prior_tiles=self.display(before_display['visible_obj_tiles'])
                same_tiles=before_display['visible_obj_sha256']==prior_tiles['visible_obj_sha256']
                self.check('admission does not change prior visible OBJ tile storage',same_tiles)
                self.active={'source_room':before_room,'target_room':self.g('room'),'admission_hw':self.e.frame,'prior_display':before_display,'admission_reference':display,'spawn':[self.g('px'),self.g('py')],'phases':[after_phase],'samples':[sample]}
                self.e.screenshot(self.out/f'arrival-{self.e.frame}-source.png')
            elif before_phase:
                self.check('arrival paint and copy consume action input and freeze gameplay',self.frozen()==fixed,{'before_phase':before_phase,'before':fixed,'after':self.frozen()})
                if before_phase==2:self.check('new scene paint leaves ordinary writer frozen',writer==(self.g('writer_phase'),self.g('writer_position')))
                self.check('arrival advances one expected presentation phase',after_phase==({2:3,3:0}.get(before_phase,-1)),{'before':before_phase,'after':after_phase})
                if self.active:
                    self.active['phases'].append(after_phase);self.active['samples'].append(sample)
                    if after_phase==3:
                        reference=self.active['admission_reference'];display=self.display(reference['visible_obj_tiles']);equal=all(reference[k]==display[k] for k in ('rgb','oam','blend','visible_obj_sha256','obj_palette_sha256'))
                        self.active['held_physical_display']=display;self.active['held_physical_display_equal']=equal
                        self.check('physical admission frame preserves source RGB, OAM, referenced OBJ tiles and brightness during new paint',equal,{'reference':reference,'physical_hold':display})
                        self.e.screenshot(self.out/f"arrival-{self.active['admission_hw']}-held.png")
                if after_phase==0 and self.active:
                    self.active['published_display']=self.display();self.active['final_spawn']=[self.g('px'),self.g('py')]
                    self.e.screenshot(self.out/f"arrival-{self.active['admission_hw']}-published.png")
                    self.check('arrival keeps its exact initialized spawn through both frozen phases',self.active['spawn']==self.active['final_spawn'])
                    self.check('arrival admission, paint and copy each update and flip within budget',all(x['delta']==1 and x['flip'] and x['cycles']<=LIMIT for x in self.active['samples']))
                    self.arrivals.append(self.active);self.active=None
    def settle_arrival(self):
        self.check('arrival publication completes within three hardware frames',self.wait(lambda:not self.g('scene_present_phase'),3))
    def town_handoff(self):
        self.play(True);self.tap('B');self.navigate(174,128);self.watch=True
        self.wait(lambda:self.g('room')==4,60,'RIGHT');self.settle_arrival()
        self.check('east stairs publish their authored spawn',self.g('room')==4 and (self.g('px'),self.g('py'))==(120,132))
        self.step(25);self.wait(lambda:self.g('room')==0,100,'DOWN');self.settle_arrival()
        self.check('village return publishes its authored spawn',self.g('room')==0 and (self.g('px'),self.g('py'))==(180,128))
        start=len(self.frames);x=self.g('px');self.step(12,'LEFT');window=self.frames[start:]
        self.check('movement resumes while ordinary destination save is active',self.g('px')<x and any(f['bg'] for f in window),{'before_x':x,'after_x':self.g('px'),'active_frames':sum(bool(f['bg']) for f in window)})
        self.check('first resumed movement keeps native cadence',all(f['delta']==1 and f['flip'] and f['cycles']<=LIMIT for f in window))
        self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1200)
        self.check('arrival writer settles without error',not self.g('save_failed'))
        self.check('all frozen action chords remain consumed',self.g('game_state')==1 and self.g('quickparty_open')==0 and self.g('summoned')==1)
        self.check('both genuine town handoffs were observed',len(self.arrivals)==2)
        self.watch=False
    def portal_handoffs(self):
        self.watch=True;self.portals();self.watch=False
        self.check('prepared extended entries include native handoff observations',len(self.arrivals)>=20,len(self.arrivals))
    def obj_reload_handoffs(self):
        self.play(True);self.location(1,168,278)
        for en in range(6):self.put('enemies',0,offset=en*20+8)
        self.step(3,phase='prepared');self.watch=True
        self.wait(lambda:self.g('room')==16,80,'UP');self.settle_arrival()
        self.check('real entry initializes the extended region before returning',self.g('room')==16 and (self.g('px'),self.g('py'))==(240,284))
        self.step(25);self.wait(lambda:self.g('room')==1,80,'DOWN');self.settle_arrival()
        self.check('extended return reloads original-world OBJ art at correct spawn',self.g('room')==1 and (self.g('px'),self.g('py'))==(168,264))
        self.watch=False;self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1200)
        self.location(7,120,64);self.put('chapter_flags',15)
        for en in range(6):self.put('enemies',0,offset=en*20+8)
        self.step(3,phase='prepared');self.watch=True
        self.wait(lambda:self.g('room')==8,80,'UP');self.settle_arrival()
        self.check('boss-room entry uploads boss art and reaches authored spawn',self.g('room')==8 and (self.g('px'),self.g('py'))==(120,132))
        self.watch=False
        self.check('OBJ-changing extended return and boss admission were observed',any(x['source_room']==16 and x['target_room']==1 for x in self.arrivals) and any(x['target_room']==8 for x in self.arrivals))
    def covenants_handoffs(self):
        from magma_journey import elf_locals
        fixture=ROOT/'tests/fixtures/v5-revision9/covenants-late26-stage-cold.sav'
        provenance=json.loads((fixture.parent/'provenance.json').read_text());expected=next(x['sha256'] for x in provenance['fixtures'] if x['path'].endswith(fixture.name));assert sha(fixture)==expected
        self.hashes['additional_fixtures']={str(fixture.relative_to(ROOT)):expected}
        local=elf_locals(self.rom.with_suffix('.elf'),self.rom)
        def npc_state():
            result={}
            for name in ('npc_x','npc_y','npc_stage','setting'):
                address,size=local['covenants_game.c:'+name];result[name]=self.e.bytes(address,size).hex()
            return result
        self.play(fixture);self.check('authenticated late fixture starts in final Covenants room',self.g('room')==77)
        quests=bytes(self.save_state().quests);npc=npc_state();self.watch=True
        self.wait(lambda:self.g('room')==76,40,'RIGHT');self.settle_arrival()
        self.check('ordinary final-region door reaches room76 checkpoint1',self.g('room')==76 and self.g('checkpoint_spawn')==1 and (self.g('px'),self.g('py'))==(448,128))
        self.step(25);self.wait(lambda:self.g('room')==77,40,'RIGHT');self.settle_arrival()
        self.check('ordinary return restores room77 checkpoint0',self.g('room')==77 and self.g('checkpoint_spawn')==0 and (self.g('px'),self.g('py'))==(208,128))
        self.check('final-region NPC work state reconstructs identically after return',npc_state()==npc,{'before':npc,'after':npc_state()})
        self.watch=False;self.step(25);self.navigate(144,140);self.tap('UP',hold=1,release=2);self.tap('A')
        after_lines=local['covenants_game.c:after_lines'][0];expected_line=self.e.read(after_lines+14*4)
        self.check('returned watcher gives its completed-covenant dialogue',self.g('game_state')==2 and self.g('dialog_lines')==expected_line)
        self.tap('A');self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1200)
        self.check('late-region entry and NPC interaction preserve earned quest history',bytes(self.save_state().quests)==quests and not self.g('save_failed'))
        path=self.out/'covenants-handoff-return.sav';self.e.save(path);self.play(path)
        self.check('independent cold Continue preserves late checkpoint and quest history',self.g('room')==77 and self.g('checkpoint_spawn')==0 and bytes(self.save_state().quests)==quests and npc_state()==npc and not self.g('save_failed'))
        self.check('late-region handoffs use only actual controller input',not self.writes and not self.state_loads and len(self.arrivals)==2)
    def first_region_handoff(self):
        path=self.a.earned_campaign_save;assert path and path.is_file(),'A same-candidate controller campaign SRAM is required'
        receipt=json.loads((path.parent/'candidate.json').read_text());assert receipt['rom_sha256']==self.hashes['rom_sha256'],'Campaign SRAM producer uses another ROM'
        self.hashes['controller_campaign_save']={'path':str(path.resolve()),'sha256':sha(path),'producer_candidate_sha256':sha(path.parent/'candidate.json')}
        self.play(path)
        if self.g('chapter_flags')&4 and not self.g('chapter_flags')&8:
            self.check('earned core clear permits ordinary elder prerequisite',self.g('room')==0 and self.g('chapter_flags')&7==7)
            self.navigate(120,116);self.tap('A')
            for _ in range(24):
                if self.g('game_state')==2:self.tap('A')
                elif self.g('game_state') in (6,10,12):self.wait(lambda:self.g('game_state') not in (6,10,12),1000)
                else:break
            self.check('ordinary elder conversation earns the ending prerequisite',self.g('chapter_flags')&8 and self.g('game_state')==5)
            self.tap('START');self.step(10);self.wait(lambda:self.g('game_state')==1 and not self.g('save_feedback_background') and not self.g('save_requested'),1200)
            prerequisite=self.out/'controller-elder-prerequisite.sav';self.e.save(prerequisite)
            self.cases.append({'case':'controller-earned-elder-prerequisite','sram_sha256':sha(prerequisite),'chapter_flags':self.g('chapter_flags'),'regional_visits':self.save_state().quests.region_flags[0]})
        before=self.save_state()
        valid=self.g('room')==0 and bool(self.g('chapter_flags')&1) and not before.quests.region_flags[0]&1
        self.check('earned campaign legitimately unlocks a still-unvisited first region',valid,{'room':self.g('room'),'chapter_flags':self.g('chapter_flags'),'regional_visits':before.quests.region_flags[0]})
        if not valid:return
        self.watch=True;self.wait(lambda:self.g('room')==1,180,'UP');self.settle_arrival()
        self.check('controller leaves village for the field',self.g('room')==1)
        self.check('controller reaches Reedhaven approach through field',self.navigate(168,280))
        self.wait(lambda:self.g('room')==16,80,'UP');self.settle_arrival()
        self.check('first ordinary regional entry publishes its authored spawn',self.g('room')==16 and (self.g('px'),self.g('py'))==(240,284))
        self.check('first visit is earned by actual entry',bool(self.save_state().quests.region_flags[0]&1))
        self.step(25);self.wait(lambda:not self.g('save_feedback_background') and not self.g('save_requested'),1200)
        first=self.out/'controller-first-region.sav';self.e.save(first)
        self.wait(lambda:self.g('room')==1,80,'DOWN');self.settle_arrival()
        self.check('first-region return restores the original-world spawn',self.g('room')==1 and (self.g('px'),self.g('py'))==(168,264))
        self.watch=False;self.play(first)
        self.check('first-visit checkpoint and region flag survive independent Continue',self.g('room')==16 and self.g('checkpoint_spawn')==0 and bool(self.save_state().quests.region_flags[0]&1) and not self.g('save_failed'))
        self.check('first-visit journey uses only actual controller input',not self.writes and not self.state_loads)
    def finish(self):
        if 'render_profile_deferred_actors' in self.sym and self.arrivals:
            publications={(f['emulator_id'],f['completed_profile']['serial']) for f in self.frames if f['phase']=='measured' and f.get('completed_profile',{}).get('deferred_actors',0)}
            self.check('every observed arrival includes a measured deferred OBJ publication',len(publications)>=len(self.arrivals),{'arrivals':len(self.arrivals),'unique_deferred_publications':len(publications)})
        self.cases.append({'case':'arrival-handoff-observations','controller_only':not self.writes,'machine_state_imports':self.state_loads,'action_stress_mask':1023,'arrivals':self.arrivals})
        return super().finish()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','symbols','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+name,required=True)
    p.add_argument('--earned-campaign-save',type=Path)
    p.add_argument('--case',choices=('town','portals','obj_reload','covenants','first_region'),default='town');a=p.parse_args();r=Probe(a)
    r.hashes['probe_script_sha256']=sha(__file__);shutil.copyfile(__file__,r.out/'test-source/tests/player_feedback_arrival_probe.py')
    action={'town':r.town_handoff,'portals':r.portal_handoffs,'obj_reload':r.obj_reload_handoffs,'covenants':r.covenants_handoffs,'first_region':r.first_region_handoff}[a.case]
    r.section('arrival_handoff_'+a.case,action);d=r.finish()
    return int(bool(d['failures']) or not d['exact_files_unchanged'] or not d['performance']['strict_measured_pacing_pass'])
if __name__=='__main__':raise SystemExit(main())
