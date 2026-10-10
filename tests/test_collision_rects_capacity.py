#!/usr/bin/env python3
"""Bound the 48-slot, radius-64 cache across every supported dynamic state.

The host proof scans every in-world origin in each static/equivalence class.
For freely movable objects, changing their positions adds at most their object
count to any measured query's rectangle count. Deliberately do not subtract
objects already present in the measured query: this remains an upper bound.
"""
import json
from test_collision_rects import ROOT, OUT, current_pins, digest


def main():
    strict = json.loads((OUT / 'strict-report.json').read_text())
    sanitized = json.loads((OUT / 'sanitized-report.json').read_text())
    for report in (strict, sanitized):
        assert report['source_pins'] == current_pins(), 'Production geometry changed since proof'
        assert report['snapshot_sha256'] == digest((ROOT / 'src/collision_rects.inc').read_bytes())
        assert report['api_header_sha256'] == digest((ROOT / 'src/collision_rects.h').read_bytes())
        assert report['harness_sha256'] == digest((ROOT / 'tests/collision_rects_host.c').read_bytes())
        assert report['magma_test_wrapper_sha256'] == digest((ROOT / 'tests/collision_rects_magma_host.c').read_bytes())
        assert report['return_test_wrapper_sha256'] == digest((ROOT / 'tests/collision_rects_return_host.c').read_bytes())
        assert report['equality_mismatches'] == report['cast_48_overflows'] == 0
    assert sanitized['sanitizers'] == ['address', 'undefined']
    assert strict['cast_room_distributions'] == sanitized['cast_room_distributions']
    assert len(strict['negative_controls']) >= 9 and all(x['rejected'] for x in strict['negative_controls'].values())
    rooms = {x['room']: x for x in strict['cast_room_distributions']}
    assert set(rooms) == set(range(46)) | set(range(54, 62))
    # Production trial parcels / regional crates / Magma lesson-screen-puzzle
    # objects are the only movable geometries not exhaustively cross-combined
    # with every origin. Their cardinalities are independently source-pinned.
    allowances = {15: 2, 20: 2, 38: 1, 39: 1, 40: 1, 42: 1, 43: 2, 44: 2}
    bounds = [{'room': room, 'measured_maximum': data['max_rectangles'],
               'unseen_position_allowance': allowances.get(room, 0),
               'all_dynamic_states_upper_bound': data['max_rectangles'] + allowances.get(room, 0)}
              for room, data in sorted(rooms.items())]
    maximum = max(x['all_dynamic_states_upper_bound'] for x in bounds)
    assert maximum <= 48, 'A normal supported cast can exceed the measured cache capacity'
    result = {'scope': '129x129 inclusive queries centered at every in-world integer origin, lower endpoints clamped at zero',
              'snapshot_sha256': strict['snapshot_sha256'], 'capacity': 48,
              'measured_cast_queries': strict['cast_queries'], 'observed_overflows': 0,
              'all_supported_dynamic_states_upper_bound': maximum,
              'count_explanation': 'Each moving object contributes at most one clipped rectangle; adding every possible moving object to the measured maximum is conservative. Other dynamic predicates have every geometry-equivalence class scanned.',
              'rooms': bounds, 'not_native_pacing_acceptance': True}
    (OUT / 'capacity-report.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Capacity 48 verified: all-state upper bound', maximum, 'across', len(rooms), 'supported rooms')


if __name__ == '__main__':
    main()
