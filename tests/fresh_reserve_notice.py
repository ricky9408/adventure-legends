#!/usr/bin/env python3
"""Empty-SRAM Grove -> early Water -> Sky -> reserved Stone discovery proof.

Uses one StrictNative controller session, plus only its own SRAM for Continue.
The original Core/ending and regional full-campaign routes are outside this test.
No historical save, emulator machine-state import, or game-RAM write is allowed.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import traceback

sys.dont_write_bytecode = True

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def badge_matches(path):
    """Check the native 13x7 NEW bitmap, independent of RGB expansion policy."""
    from PIL import Image
    im = Image.open(path).convert('RGB')
    rows = ((5,7,7,7,5),(7,4,6,4,7),(5,5,7,7,5))
    background = im.getpixel((18,86))
    foreground = im.getpixel((19,87))
    if background == foreground:
        return False
    for y in range(7):
        for x in range(13):
            lit = False
            if 1 <= y <= 5 and 1 <= x <= 11:
                letter, column = divmod(x-1,4)
                lit = column < 3 and bool(rows[letter][y-1] & (4 >> column))
            if im.getpixel((18+x,86+y)) != (foreground if lit else background):
                return False
    return True

def earned_carousel(route, stone):
    """Exercise current controls after the unchanged earned-reserve boundary."""
    roster=route.state().roster
    owned=[i for i,c in enumerate(roster.instances) if c.flags&1]
    route.check(len(owned)>4 and stone in owned and stone not in roster.party,
                'carousel proof starts with more than four actually earned individuals and reserved Stone')
    original_instances=bytes(roster.instances)
    route.select_owned_instance(stone)
    selected=route.state().roster
    route.check(selected.party[selected.selected_party]==stone,
                'physical L with Left/Right selects earned reserve Stone without opening a journal')
    route.check(bytes(selected.instances)==original_instances,
                'reserve selection preserves every earned individual byte')
    sweeps=[]
    for direction in ('RIGHT','LEFT'):
        before=route.state()
        current=before.roster.party[before.roster.selected_party]
        route.open_owned_carousel()
        route.check(route.get('quickparty_candidate')==current,'held L opens on actual selected roster index')
        visited=[]
        for _ in owned:
            route.step(1,'L+'+direction);route.step(1,'L')
            visited.append(route.get('quickparty_candidate'))
        route.check(len(set(visited))==len(owned) and set(visited)==set(owned) and visited[-1]==current,
                    direction+' traverses every earned individual, including reserves, and wraps once')
        route.check(bytes(route.state().roster)==bytes(before.roster),
                    'full carousel preview leaves the real roster and selection unchanged')
        route.step(1,'L+B');route.step(1)
        route.check(not route.get('quickparty_open') and bytes(route.state().roster)==bytes(before.roster),
                    'physical B cancels carousel without committing or casting')
        sweeps.append({'direction':direction,'visited_roster_indices':visited})
    route.select_owned_identity(selected.instances[stone].instance_id)
    route.set_summoned(True);route.ready()
    summoned=route.get('summoned')
    route.field_ability(1,1)
    route.check(route.get('ability_cd')>0 and route.get('summoned')==summoned,
                'physical B executes earned Stone ability without recalling its companion')
    route.set_summoned(False)
    route.check(not route.get('summoned'),'physical R recalls after the actual B ability')
    route.ready();route.field_ability(1,1)
    route.check(route.get('summoned') and route.get('ability_cd')>0,
                'fresh physical B summons a recalled earned companion and executes its ability once')
    chords=earned_button_chords(route)
    route.set_summoned(False)
    route.drain_background();before_continue=route.state()
    route.cold_reboot('earned-reserve-carousel')
    continued=route.state()
    route.check(bytes(continued.roster)==bytes(before_continue.roster) and
                continued.roster.party[continued.roster.selected_party]==stone,
                'ordinary own-SRAM Continue retains carousel-selected reserve and every individual')
    route.coverage += ['earned-reserve-field-carousel-both-directions-and-wrap',
                       'physical-B-ability-and-R-recall','own-Continue-retains-carousel-selected-reserve']
    return {'owned_count':len(owned),'reserved_stone_index':stone,'sweeps':sweeps,'button_chords':chords,
            'physical_ability':'B','physical_summon_recall':'R','controller_only':True,
            'game_ram_writes':0,'machine_state_imports':0,'historical_progress_imports':0}


def earned_button_chords(route):
    """Observe fresh physical edges on the earned Stone, never injected state."""
    cases=[]
    def prepare():
        route.step(1);route.ready();route.set_summoned(True);route.step(1)
        route.check(route.get('ability_cd')==0 and route.get('summoned'),
                    'button-order case starts with naturally cleared cooldown and summoned earned Stone')
    def observe(name):
        cases.append({'name':name,'hardware_frame':route.e.frame,
                      'summoned':route.get('summoned'),'ability_cd':route.get('ability_cd')})
    prepare()
    route.step(1,'R');route.check(not route.get('summoned') and not route.get('ability_cd'),
                                'R-only recalls without starting an ability')
    route.step(1,'B')
    route.check(route.get('summoned') and route.get('ability_cd')>0,
                'fresh B directly after R-only release summons and casts')
    observe('R-only then fresh B');route.step(1)
    prepare();route.step(1,'R');route.step(1,'R+B')
    route.check(not route.get('summoned') and not route.get('ability_cd'),
                'R-first overlap blocks the fresh B edge')
    route.step(3,'B')
    route.check(not route.get('summoned') and not route.get('ability_cd'),
                'releasing R while B stays held cannot summon or cast')
    observe('R-first overlap and R release while B held')
    route.step(1);route.step(1,'B')
    route.check(route.get('summoned') and route.get('ability_cd')>0,
                'B works after physical B release following an R-first chord')
    route.step(1)
    prepare();route.set_summoned(False);route.step(1,'B')
    route.check(route.get('summoned') and route.get('ability_cd')>0,
                'B-first begins one actual earned ability')
    cooldown=route.get('ability_cd');route.step(1,'B+R')
    route.check(not route.get('summoned') and 0<route.get('ability_cd')<=cooldown,
                'fresh R owns a B-first chord without refunding its existing cooldown')
    route.step(route.get('ability_cd')+2,'B')
    route.check(not route.get('summoned') and not route.get('ability_cd'),
                'B held after R release stays blocked even after natural cooldown expiry')
    observe('B-first overlap through cooldown expiry')
    route.step(1);route.step(1,'B')
    route.check(route.get('summoned') and route.get('ability_cd')>0,
                'fresh B works after releasing the B-first chord')
    route.step(1)
    prepare();route.step(1,'R+B')
    route.check(not route.get('summoned') and not route.get('ability_cd'),
                'simultaneous fresh R+B recalls and starts no ability')
    route.step(3,'B')
    route.check(not route.get('summoned') and not route.get('ability_cd'),
                'simultaneous chord also requires physical B release')
    observe('simultaneous R+B')
    route.step(1);route.field_ability(1,1)
    route.check(route.get('summoned') and route.get('ability_cd')>0,
                'B release restores ordinary ability after the simultaneous chord')
    route.coverage.append('earned-physical-B-R-both-orders-simultaneous-and-release-latch')
    return cases

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--bridge',type=Path,required=True)
    p.add_argument('--expected-commit',required=True)
    p.add_argument('--expected-manifest-sha',help='Explicit receipt for an uncommitted current build')
    opts=p.parse_args()
    root=opts.source_root.resolve();out=opts.output.resolve()
    assert out!=root and out not in root.parents,'output may not replace the source checkout or its parent'
    out.mkdir(parents=True,exist_ok=False)
    head=subprocess.check_output(['git','-c','safe.directory='+str(root),'rev-parse','HEAD'],cwd=root,text=True).strip()
    manifest=root/'build/source-hashes.json'
    sources=json.loads(manifest.read_text())
    assert all(sha(root/name)==digest for name,digest in sources.items()),'candidate source receipt differs from production files'
    if opts.expected_manifest_sha:
        assert sha(manifest)==opts.expected_manifest_sha,'explicit current build receipt changed'
    subprocess.run(['git','-c','safe.directory='+str(root),'merge-base','--is-ancestor',opts.expected_commit,head],cwd=root,check=True)
    changed=subprocess.check_output(['git','-c','safe.directory='+str(root),'diff','--name-only',opts.expected_commit,head],cwd=root,text=True).splitlines()
    dirty=subprocess.check_output(['git','-c','safe.directory='+str(root),'diff','--name-only','HEAD'],cwd=root,text=True).splitlines()
    untracked=subprocess.check_output(['git','-c','safe.directory='+str(root),'ls-files','--others','--exclude-standard'],cwd=root,text=True).splitlines()
    runtime_changes=sorted((set(changed)|set(dirty)|set(untracked))&set(sources))
    assert not runtime_changes or opts.expected_manifest_sha,'dirty runtime requires an explicitly pinned current build receipt'
    runtime_commit=None if runtime_changes else opts.expected_commit
    candidate=out/'candidate';candidate.mkdir()
    for suffix in ('gba','sym','elf'):
        shutil.copyfile(root/'build'/('emberbond.'+suffix),candidate/('emberbond.'+suffix))
    shutil.copyfile(manifest,candidate/'source-hashes.json')
    shutil.copyfile(__file__,out/'fresh_reserve_notice.py')
    helper_hashes={}
    for directory,pattern in (('tests','*.py'),('tools','mgba_runner.py')):
        for src in (root/directory).glob(pattern):
            dst=out/'helper-source'/directory/src.name;dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(src,dst);helper_hashes[str(dst.relative_to(out))]=sha(dst)
    (out/'helper-source-hashes.json').write_text(json.dumps(helper_hashes,indent=2)+'\n')
    sys.path[:0]=[str(root/'tests'),str(root/'tools')]
    import journey_guidance_earned as journey
    from treasure_full_journey import TreasureOriginalJourney
    a=SimpleNamespace(output=out,rom=candidate/'emberbond.gba',symbols=candidate/'emberbond.sym',
      bridge=opts.bridge.resolve(),source_root=root,baseline=False,cross_rom_diagnostic=False,
      stop_after='sky-reserve',diagnostic_boundary_report=None)
    a.expected_rom_sha=sha(a.rom);a.expected_symbols_sha=sha(a.symbols)
    a.candidate={'rom_sha256':a.expected_rom_sha,'symbols_sha256':a.expected_symbols_sha,
      'elf_sha256':sha(a.rom.with_suffix('.elf')),'source_manifest_sha256':sha(manifest),
      'bridge_sha256':sha(a.bridge)}
    (out/'candidate.json').write_text(json.dumps({**a.candidate,'runtime_commit':runtime_commit,
      'runtime_base_commit':opts.expected_commit,'runtime_worktree_changes':runtime_changes,
      'harness_head':head,'harness_only_changes_since_runtime':changed,'test_sha256':sha(__file__)},indent=2)+'\n')

    class ReserveOriginal(TreasureOriginalJourney):
        def select(self,spirit,summon=True):
            # Historical Sky helper selects Stone after the reward. In this
            # legitimate route Stone is reserve, so that optional convenience
            # must not assign or select it before the discovery observation.
            if spirit==3 and getattr(self,'reserve_scenario',False):
                r=self.state().roster
                self.check(self.get('chapter_flags')&7==3,'post-Sky reserve observation has earned Grove and Sky only')
                self.check(all(i<160 for i in r.party) and all(r.instances[i].form_id!=10 for i in r.party),
                           'full active party leaves Stone in reserve before inspection')
                self.cases.append({'case':'skip historical optional post-Sky Stone selection because Stone is reserve',
                                   'controller_only':True,'game_ram_writes':0})
                return
            return super().select(spirit,summon)

    class EarlyRegional(journey.RegionalJourney):
        def __init__(self,original):
            # Borrow the very same core, logs, metrics and live earned save.
            # Never call RegionalJourney's full-ending fixture constructor.
            self.__dict__=original.__dict__
            self.locals=journey.elf_locals(a.rom.with_suffix('.elf'),self.rom)
            for attribute,relative in (
                ('layout','assets/region/layout.json'),('world','assets/world_manifest.json'),
                ('campaign','assets/campaign_layouts.json'),('north','assets/northern_region/layout.json'),
                ('scene','assets/southern_region/scene.json'),('magma_layout','assets/magma_region/layout.json'),
                ('return_geometry','assets/return_region/geometry.json'),('covenants_geometry','assets/covenants_world/geometry.json')):
                setattr(self,attribute,json.loads((root/relative).read_text()))
            self.campaign_rooms={x['id']:x for x in self.campaign['rooms']}
            self.cv_rooms={x['id']:x for x in self.covenants_geometry['rooms']}
            self.descriptors={};self.mask_cache={};self.minimal=True
        # Keep Original's alias-aware reads while borrowing only navigation.
        get=ReserveOriginal.get

    r=None
    try:
        r=ReserveOriginal(a);r.first_chapter()
        r.check(r.get('chapter_flags')&15==1,'early regional detour begins after Grove, before Sky/Core/ending')
        early=EarlyRegional(r)
        early.chapter='early-water';early.entry(1);early.entry(16);early.entry(17)
        early.check(early.quest(2)==0,'early Water quest begins unclaimed')
        early.act(264,216);early.cast(4,240,199)
        early.check(early.state().quests.objectives[1]==3,'real handle and Nature restore the early dry road')
        early.act(120,232);early.cast(4,98,44);early.cast(7,184,88);early.act(184,88)
        state=early.state();party_before=bytes(state.roster.party)
        forms=[state.roster.instances[i].form_id for i in state.roster.party]
        early.check(early.quest(2)==3 and forms==[1,4,7,13],
                    'controller-earned early Water fills the fourth active slot after Fire/Nature/Wind')
        early.snapshot('water-fills-party');early.entry(16);early.entry(1);early.entry(0)
        r.chapter='sky';r.reserve_scenario=True;r.chapter_two()
        s=r.state();stone=next(i for i,c in enumerate(s.roster.instances) if c.flags&3==3 and c.form_id==10)
        r.check(bytes(s.roster.party)==party_before and stone not in s.roster.party,
                'real Sky reward recruits story Stone into reserve without changing the full active party')
        r.check(not s.economy.reserved[1]&2,'uninspected reserve Stone remains NEW after helper own-save Continue')
        def browse_stone():
            r.open_tab(2)
            for _ in range(161):
                if r.get('quickparty_menu_candidate')==stone:break
                r.tap('DOWN',2,3)
            r.check(r.get('quickparty_menu_candidate')==stone and not r.get('quickparty_menu_detail'),
                    'Down browses the actual reserved Stone candidate without assigning it')
        browse_stone();r.raw_step(3)
        before_shot=r.out/'sky-reserve-stone-NEW.png';r.e.screenshot(before_shot)
        r.check(badge_matches(before_shot),'native browsed reserve candidate displays the exact NEW bitmap')
        before=r.state();fixed={n:r.get(n) for n in ('px','py','hero_hp_q4','ability_cd','heal_cd','summoned')}
        r.tap('A',2,4);after=r.state();expected=type(before).from_buffer_copy(bytes(before));expected.economy.reserved[1]|=2
        r.check(r.get('quickparty_menu_detail')==1,'one fresh A opens reserved Stone inspector')
        r.check(bytes(after)==bytes(expected),'inspection changes only the Stone acknowledgement bit in the full Save5 state')
        r.check(all(r.get(n)==v for n,v in fixed.items()),'reserved inspection preserves paused position, HP and remaining cooldowns')
        r.shot('sky-reserve-stone-inspected');r.tap('B',2,4);r.raw_step(3)
        after_shot=r.out/'sky-reserve-stone-acknowledged.png';r.e.screenshot(after_shot)
        r.check(not badge_matches(after_shot),'returning to the reserve row removes the acknowledged NEW bitmap')
        r.close_menu();r.drain_background();before_continue=r.state();r.cold_reboot('reserve-stone-inspection')
        continued=r.state()
        r.check(continued.economy.reserved[1]&2 and bytes(continued.roster)==bytes(before_continue.roster),
                'own SRAM Continue retains acknowledgement, every individual, active slots and selected companion')
        r.check(stone not in continued.roster.party,'Stone remains reserved after acknowledged own-save Continue')
        browse_stone();r.raw_step(3);continued_shot=r.out/'sky-reserve-stone-continued.png';r.e.screenshot(continued_shot)
        r.check(not badge_matches(continued_shot),'continued reserve candidate stays acknowledged visually')
        r.close_menu();r.drain_background()
        carousel=earned_carousel(r,stone)
        r.route_complete=False;r.history=['grove','early-water','sky']
        r.coverage += ['fresh-early-Water-full-party','earned-Sky-Stone-reserve',
                       'browsed-reserve-NEW-bitmap','A-inspection-acknowledgement-only',
                       'own-Continue-keeps-acknowledged-reserve-and-party']
        r.snapshot('reserve-proof-complete');r._frames.close()
        measured=[json.loads(line) for line in gzip.open(r.out/'native-frames.jsonl.gz','rt')]
        active=[x for x in measured if x['phase']=='journey' and x['before_state']==x['state']==1]
        r.check(bool(active) and all(x['delta']==1 and x['flip'] and x['cycles']<280896 for x in active),
                'all measured active route frames update and present within native hardware budget')
        r.close();r=None
        report=json.loads((out/'original/report.json').read_text())
        summary={'accepted':not report['failures'] and all(x['passed'] for x in report['checks']),
                 'candidate':a.candidate,'runtime_commit':runtime_commit,'runtime_base_commit':opts.expected_commit,
                 'runtime_worktree_changes':runtime_changes,'harness_head':head,
                 'scope':'fresh Grove -> early Reedhaven Water -> Sky -> reserved Stone inspection and own SRAM Continue',
                 'full_campaign_proven':False,'full_collection_proven':False,'controller_only':True,
                 'provenance':report['provenance'],'checks':len(report['checks']),
                 'metrics':report['metrics'],'active_frames':len(active),
                 'max_active_cycles':max(x['cycles'] for x in active),
                 'party_forms':forms,'reserved_stone_index':stone,
                 'earned_field_controls':carousel,
                 'native_screenshots':{str(x.relative_to(out)):sha(x) for x in (before_shot,after_shot,continued_shot)}}
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary,indent=2))
    except Exception as error:
        failure={'error':repr(error),'traceback':traceback.format_exc()}
        (out/'failure.json').write_text(json.dumps(failure,indent=2)+'\n')
        if r:
            r.failures.append(failure);r.report()
            try:r.e.screenshot(r.out/'failure.png')
            finally:r.close()
        raise

if __name__=='__main__':main()
