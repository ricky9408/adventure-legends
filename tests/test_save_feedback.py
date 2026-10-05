#!/usr/bin/env python3
"""Synthetic host integration: save failures, modal notices and safe retry.

Actual C save/puzzle/journal/update functions run against fault-injected host
SRAM and explicitly constructed game state, never normal controller gameplay.
Audio is held below its hardware-write interval. The actual notice/box/glyph
renderer uses a host framebuffer and CPU rectangle fills instead of DMA; this
is a pixel/OBJ unit check, not a native-ROM screenshot or full-render test.
"""
import ctypes as C
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
from test_save5 import Save, Roster
ROOT=Path(__file__).resolve().parents[1]
PLAY,DIALOG,PAUSE,DEAD,WIN,SAVE_PENDING,EVOLVE_CONFIRM,EVOLVE_ANIM=range(1,9)

class UiRun(C.Structure):
    _fields_=[('offset',C.c_ushort),('count',C.c_ubyte),('mask',C.c_ubyte)]

class UiText(C.Structure):
    _fields_=[('width',C.c_ushort),('height',C.c_ubyte),('reserved',C.c_ubyte),
              ('runs',C.POINTER(UiRun)*2),('count',C.c_ushort*2)]

with tempfile.TemporaryDirectory(prefix='emberbond-save-feedback-') as temp:
    library=Path(temp)/'game-host.so'
    modules=['game','assets','ui','world','campaign_art','campaign_rules','save4',
             'creatures','creature_data','save5','progression','evolution_art',
             'advanced_powers','trials','trial_art','quickparty','equipment','equipment_data',
             'combat_rules','weapon_actions','gear_runtime','gear_menu','regional_quests',
             'regional_creature_art','regional_powers','region_art','region_game']
    subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+[
        '-shared','-fPIC','-O0','-std=c99','-fno-builtin','-Wno-attributes',
        '-Wno-pointer-to-int-cast','-Wno-int-to-pointer-cast',
        '-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-DGAME_HOST_TEST','-Dmain=gba_main',
        *[str(ROOT/'src'/(n+'.c')) for n in modules],'-o',str(library)],check=True)
    lib=C.CDLL(str(library));lib.save5_load.argtypes=[C.POINTER(Save)]
    lib.save5_load.restype=C.c_int
    lib.creatures_migrate_legacy.argtypes=[C.c_void_p,C.c_uint,C.c_uint]
    lib.creatures_evolve.argtypes=[C.POINTER(Roster),C.c_uint,C.c_uint,C.c_int,C.c_int]
    lib.save5_test_fail_after.argtypes=[C.c_int]
    lib.save5_test_write_count.restype=C.c_uint
    def get(n):return C.c_int.in_dll(lib,n).value
    def put(n,v):C.c_int.in_dll(lib,n).value=v
    sram=(C.c_ubyte*32768).in_dll(lib,'save5_test_sram');sram[:]=b'\xff'*32768
    old=(C.c_ubyte*256).in_dll(lib,'save4_test_sram');old[:]=b'\xff'*256
    live=Save.in_dll(lib,'adventure_save')
    assert lib.creatures_migrate_legacy(C.byref(live.roster),1,2)==1
    lib.equipment_init(C.byref(live.equipment))
    for n,v in {'room':7,'game_state':1,'checkpoint_spawn':0,'chapter_flags':1,
                'bridge_open':1,'torches':3,'room_flags':7,'story_seen':2,
                'spirit':2,'px':56,'py':112,'pressed':0}.items():put(n,v)
    def update(pressed=0):
        put('pressed',pressed);put('music_tick',-1000);lib.update();put('pressed',0)
    def wait_updates(count):
        for _ in range(count):update()
    def drain(resume=PLAY):
        lib.save_frame();assert get('game_state')==SAVE_PENDING
        for _ in range(200):
            update()
            if get('game_state')!=SAVE_PENDING:break
        assert get('game_state')==resume,'writer returns to its requesting state'
    def load():
        s=Save();assert lib.save5_load(C.byref(s))==1;return s
    ids=list(dict.fromkeys(re.findall(r'\bTX_[A-Z0-9_]+\b',(ROOT/'src/ui.h').read_text())))
    lib.save5_test_fail_after(-1);lib.save_game();drain()
    assert get('save_failed')==0
    prior=load();before=bytes(sram)
    assert prior.campaign.room_flags==7
    lib.save5_test_fail_after(0)
    assert lib.campaign_power()==1
    assert get('room_flags')==15 and get('save_requested')==1
    drain();after=load()
    assert get('save_failed')==1
    assert get('save_failure_notice')==1
    assert ids[get('toast_id')]=='TX_C_SAVE_FAILED'
    assert bytes(sram)==before and lib.save5_test_write_count()==0
    assert after.campaign.room_flags==7 and after.campaign.sequence==prior.campaign.sequence
    lib.save5_test_fail_after(-1);lib.save_game()
    assert get('toast_ticks')==0,'retry dismisses stale failure feedback'
    drain();recovered=load()
    assert get('save_failed')==0 and recovered.campaign.room_flags==15
    assert get('save_failure_notice')==0
    assert recovered.campaign.sequence==prior.campaign.sequence+1
    assert get('toast_ticks')==0,'successful retry never redisplays old failure'

    # Synthetic evolved creature fixture: exercise the real journal command
    # request, asynchronous failure, paused wait, close and recovery paths.
    fox=live.roster.instances[0];fox.bond=40;fox.trial_flags=1
    assert lib.creatures_evolve(C.byref(live.roster),0,1,1,1)==0
    for n,v in {'room':0,'spirit':0,'checkpoint_spawn':3,'game_state':PAUSE,
                'journal_tab':3,'px':120,'py':128}.items():put(n,v)
    # This is a synthetic fixture: select the actual owned fox instance.
    # Engine adapter `spirit` alone no longer overrides the authoritative party.
    lib.progression_select(0);lib.progression_refresh();lib.save_game();drain(PAUSE)
    prior=load();before=bytes(sram);old_command=lib.progression_command()
    lib.save5_test_fail_after(0)
    assert lib.progression_menu_input(256)==1
    changed_command=lib.progression_command();assert changed_command!=old_command
    drain(PAUSE);assert get('save_failed')==get('save_failure_notice')==1
    wait_updates(140)
    assert get('game_state')==PAUSE and get('toast_ticks')==0
    assert get('save_failure_notice')==1,'paused timeout must not dismiss failure'
    # Other modal feedback and page changes cannot overwrite the failure.
    lib.toast(ids.index('TX_E_GROWN'));wait_updates(140)
    for _ in range(6):
        update(1);assert get('save_failure_notice')==1
    assert get('journal_tab')==3 and bytes(sram)==before

    # Check exact glyph pixels, the opaque background, and bounding rectangle
    # against independently decoded authored UI spans, not merely a text ID.
    text=(UiText*len(ids)).in_dll(lib,'ui_texts')[ids.index('TX_C_SAVE_FAILED')]
    x=(240-text.width)//2;left=(240-text.width-10)//2;top=8;height=19
    width=240-2*left;cream=47;border=45;ink=1
    pixels=(C.c_ubyte*(240*160))()
    C.c_void_p.in_dll(lib,'screen').value=C.addressof(pixels)
    expected=bytearray([ink]*(width*height))
    for yy in range(height):
        for xx in range(width):
            if yy in (0,height-1) or xx in (0,width-1):expected[yy*width+xx]=border
    glyph_pixels=set()
    for i in range(text.count[x&1]):
        run=text.runs[x&1][i]
        for pair in range(run.count):
            pixel=((top+2)*120+x//2+run.offset+pair)*2
            for side in range(2):
                if run.mask&(1<<side):
                    xx=(pixel+side)%240-left;yy=(pixel+side)//240-top
                    assert 0<xx<width-1 and 0<yy<height-1
                    expected[yy*width+xx]=cream;glyph_pixels.add((xx,yy))
    assert len(glyph_pixels)>200,'notice contains readable authored glyphs'
    modal_states=[DIALOG,PAUSE,DEAD,WIN,EVOLVE_CONFIRM,EVOLVE_ANIM]
    for state in modal_states:
        put('game_state',state);pixels[:]=bytes([241])*len(pixels)
        lib.box(8,31,224,122);background=bytes(pixels)
        lib.draw_save_failure_notice()
        for yy in range(160):
            for xx in range(240):
                actual=pixels[yy*240+xx]
                if left<=xx<left+width and top<=yy<top+height:
                    assert actual==expected[(yy-top)*width+xx-left],(state,xx,yy)
                else:assert actual==background[yy*240+xx],'notice stays above panel'
        for priority in (0,1,2):
            put('obj_count',0);lib.obj_add(0,left,top,16,16,priority,9999,0)
            assert get('obj_count')==0,'world and HUD OBJ must not obscure notice'
        put('obj_count',0);lib.obj_add(0,left+width,top,8,8,0,9999,0)
        assert get('obj_count')==1,'nonoverlapping corner HUD remains visible'
    for state in (0,PLAY,SAVE_PENDING):
        put('game_state',state);pixels[:]=bytes([241])*len(pixels)
        lib.draw_save_failure_notice();assert bytes(pixels)==bytes([241])*len(pixels)
    put('game_state',PLAY);put('obj_count',0)
    lib.obj_add(0,left,top,16,16,0,9999,0)
    assert get('obj_count')==1,'normal-play HUD is not reserved for this notice'

    # Canceling evolution returns to a modal, so it is not acknowledgement.
    put('game_state',EVOLVE_CONFIRM);update(2)
    assert get('game_state')==PAUSE and get('save_failure_notice')==1
    # A repeated failed attempt replaces the prior notice, then persists again.
    lib.save_game();assert get('save_failure_notice')==0
    drain(PAUSE);wait_updates(140)
    assert get('save_failure_notice')==1 and get('toast_ticks')==0
    update(2)
    assert get('game_state')==PLAY and get('save_failure_notice')==0
    assert get('save_failed')==1,'acknowledgement must not claim the write succeeded'
    assert bytes(sram)==before and load().campaign.sequence==prior.campaign.sequence
    assert load().roster.instances[0].equipped[0]==old_command
    lib.save5_test_fail_after(-1);lib.save_game();drain()
    recovered=load()
    assert get('save_failed')==get('save_failure_notice')==get('toast_ticks')==0
    assert recovered.roster.instances[0].equipped[0]==changed_command
    assert recovered.campaign.sequence==prior.campaign.sequence+1
    update(8)
    assert get('game_state')==PAUSE and get('save_failure_notice')==0

    # Dialogue failures persist through waits and clear only at return to PLAY.
    lib.dialogue(ids.index('TX_INTRO1A'),ids.index('TX_INTRO1B'),PLAY)
    lib.save5_test_fail_after(0);lib.save_game();drain(DIALOG);wait_updates(140)
    assert get('save_failure_notice')==1 and get('toast_ticks')==0
    lib.finish_dialogue()
    assert get('game_state')==PLAY and get('save_failure_notice')==0 and get('save_failed')==1
    # Validation rejection before SAVE_PENDING also exposes the same notice.
    put('game_state',PAUSE);prior_chapter=get('chapter_flags');put('chapter_flags',2)
    before=bytes(sram);lib.save_game();lib.save_frame()
    assert get('game_state')==PAUSE and get('save_failed')==get('save_failure_notice')==1
    assert bytes(sram)==before
    put('chapter_flags',prior_chapter);lib.save5_test_fail_after(-1)
    lib.save_game();assert get('toast_ticks')==get('save_failure_notice')==0
    drain(PAUSE);assert get('save_failed')==0
    # Revision2 validates typed quest reservation incrementally, before writes.
    before=bytes(sram);live.quests.variables[63]=1;lib.save_game();drain(PAUSE)
    assert get('save_failed')==get('save_failure_notice')==1 and bytes(sram)==before
    live.quests.variables[63]=0;lib.save_game();drain(PAUSE)
    assert get('save_failed')==get('save_failure_notice')==0
    # New party panel: the real R assignment path shares the same failure
    # notice and transactional recovery, without changing any owned instance.
    put('game_state',PAUSE);put('journal_tab',2)
    put('quickparty_menu_slot',0)
    put('quickparty_menu_candidate',live.roster.party[1])
    old_party=bytes(live.roster.party);owned_before=bytes(live.roster.instances)
    prior=load();before=bytes(sram)
    lib.save5_test_fail_after(0);update(256)
    new_party=bytes(live.roster.party)
    assert new_party!=old_party and get('save_requested')==1
    assert bytes(live.roster.instances)==owned_before
    drain(PAUSE);wait_updates(140)
    assert get('save_failed')==get('save_failure_notice')==1
    assert get('toast_ticks')==0 and lib.save_notice_visible()==1
    assert bytes(sram)==before and bytes(load().roster.party)==old_party
    assert bytes(live.roster.instances)==owned_before
    update(2)
    assert get('game_state')==PLAY and get('save_failure_notice')==0
    assert get('save_failed')==1
    lib.save5_test_fail_after(-1);lib.save_game();drain()
    recovered=load()
    assert bytes(recovered.roster.party)==new_party
    assert bytes(recovered.roster.instances)==owned_before
    assert recovered.campaign.sequence==prior.campaign.sequence+1
    assert get('save_failed')==get('save_failure_notice')==0

    print(json.dumps({'passed':True,
                      'scope':'Synthetic host C state/SRAM fault injection plus actual notice/glyph/OBJ helpers',
                      'failed_write_preserves_prior_bank':True,'failure_feedback_retained':True,
                      'paused_updates_before_close':140,'unrelated_toast_and_page_changes_preserve_notice':True,
                      'explicit_close_acknowledges_without_claiming_save_success':True,
                      'dialogue_return_acknowledges':True,'begin_rejection_notice':True,
                      'successful_retry_clears_stale_error':True,
                      'rendered_modal_states':modal_states,'verified_glyph_pixels':len(glyph_pixels),
                      'hud_and_world_obj_cannot_obscure_notice':True,'normal_play_has_no_notice_bar':True,
                      'party_assignment_failure_visible_after_wait':True,
                      'party_assignment_retry_preserves_ownership':True,
                      'native_rom_gameplay':False,'emulator_game_ram_injection':False},indent=2))
