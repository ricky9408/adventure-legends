"""Exact content8 cache layout for copied retained full-engine host probes.

The first 34 cache-key expressions are identical to frozen Return H game.c
(55ffdfb3cdcbd028efe7e4f2c4930afd5b6e12eeba9bede96331a03b0d2ce30e).
Horizons appends two fields; the full two-page view is retained. Probes with
existing byte comparisons still include every field in both pages.
No cache data or production function is replaced by this adapter.
"""
import hashlib
import re

GAME_SHA256 = '841b1659d0b9ab588007d1b7bf3decb8fe5936f67c3b5a40a659f659fff024a4'
FIELDS = ['room', 'game_state', 'spirit', 'summoned', 'bridge_open', 'torches', 'dpage', 'game_state==PLAY&&toast_ticks>0', 'game_state==PLAY?toast_id:0', 'has_save', 'journal_tab', 'room_flags', 'chapter_flags', 'optional_flags', 'game_state==DIALOG?dialog_lines[dpage*2]:-1', 'game_state==DIALOG?dialog_lines[dpage*2+1]:-1', 'game_state==DIALOG?dialog_speakers[dpage]:-1', 'scrolling_room()?camera_x:0', 'scrolling_room()?camera_y:0', 'progression_revision', 'area_ticks>0', 'quickparty_revision', 'save_notice_visible()', 'gear_menu_revision', 'region_game_revision', 'north_game_revision', 'south_game_revision', 'game_state==PLAY?southern_powers_hint():0', 'magma_game_revision', 'game_state==PLAY?magma_powers_hint():0', 'underwater_game_revision', 'game_state==PLAY?underwater_powers_hint():0', 'return_game_revision', 'game_state==PLAY?return_powers_hint():0', 'horizons_game_revision', 'game_state==PLAY?horizons_powers_hint():0']


def verify_cache_layout(source_root, field_count):
    path = source_root/'src/game.c'
    text = path.read_text()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == GAME_SHA256
    match = re.search(r'u32 key\[CACHE_FIELDS\]=\{([^}]+)\}', text)
    assert match and match[1].split(',') == FIELDS
    assert field_count == len(FIELDS) == 36
    return {'fields_per_page': 36, 'ordered_fields': FIELDS,
            'game_source_sha256': GAME_SHA256,
            'unchanged_return_prefix_fields': 34,
            'added_fields': FIELDS[34:],
            'view_scope': 'All 36 fields of both real production cache pages; existing comparisons are preserved'}
