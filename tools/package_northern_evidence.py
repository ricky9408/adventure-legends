#!/usr/bin/env python3
"""Package bounded, deterministic evidence for the frozen Northern N5 cartridge.

This is a summarizer/validator, not a test runner. Raw traces, state files, saves,
and local paths never become public evidence. Report hashes are exact byte hashes;
summary hashes use canonical JSON where explicitly named. Documentation and the
Makefile are deliberately excluded from current-source guards. An old successful
report cannot silently substitute for any pinned N5 input.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = '302316c53d6fb9dafa0ecbf9f679c9c39af3a150af3aa78398c368312e50399e'
SYM_SHA = '7110402451d7bea92ebd1d83dfddbf2f389468028e8842ef6afa22f043595018'
ROM_BYTES = 4351688
FROZEN_MANIFEST_SHA = '0effd60dc5e3d255e54269e862033b3a3eac1829cc1245c205db4a4acc6df792'
# Report-relative names, exact byte hashes, and separately counted native checks.
REPORTS = {
    'journey': ('northern-native-n5/northern-journey.json', '41b317d122abec224f68832ec0842b7d971567cfb0763377e39495c9062a2dfc', 9978),
    'sky-route': ('northern-sky-native-n5/northern-journey.json', 'b1e0eb43aa6a7ec36e0cae8aac41673fd831ae574db63234a2006ce6bb49ecba', 4668),
    'stress': ('northern-stress-n5-final/northern-stress.json', '6588538ce5576bdacbdbd0abecb962b9f0082f2447ad1496ca6d87c6a00bf238', 314),
    'boss-controls': ('northern-boss-controls-n5/northern-stress.json', 'b60d91bc43329eef84c6cf232f10eec0c48e5ec7d301add6ebc8e099f2ae7b07', 221),
    'modal-controller': ('northern-modal-n5/northern-journey.json', '7c1fc488cb5f692bcd412999ed7e85f1743b612979eff96cc214e9ba44c20bad', 162),
    'combat': ('northern-combat-n5-portable/northern-combat.json', '352228d6080399e9e82ac2cd45585ddd98aca158d0e1a72fab96e1843fbaede1', 8837),
}
AUXILIARY = {
    'acceptance': ('northern-final-controller-acceptance.json', 'bf2a5d21ec2c71eaa0237b8bee81eeb91aed197f8969ffaeb4f1cf1a22221013'),
    'modal-scenes': ('northern-modal-n5/modal-scenes.json', '4a683c7997418b0aa881261f982c60501a82b55910defb416a6a3968a5b2fada'),
    'modal-equivalence': ('northern-modal-n5/modal-equivalence.json', '90073a9cb629580423da3e8042c9b4d7d4edd9a76c2ed27621d9d35604bdce19'),
    'host-orders-capacity': ('northern-native-n5/northern-host-orders-capacity.json', 'd2f7259811df985d698966d9a14b16658b4711d6023b160fff68d53062819da9'),
}
PROVENANCE_PATH = 'northern-source-provenance-reproducible.json'
PROVENANCE_SHA = '34cb595ddb9ec8eaceee500109ed8256adceb91ccb4fb6ad6abd0d060ab74c7f'
MEDIA_PATH = 'northern-teaser/portable/capture.json'
MEDIA_SHA = '3985c506f57117ba9f1b901f8e7cc87ea1a48fe371559f18b27b874bf7e2fdf5'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def scalar_fields(record):
    return {k: v for k, v in record.items() if isinstance(v, (str, int, float, bool)) or v is None}


def relative_source(path):
    p = Path(path)
    require(not p.is_absolute() and '..' not in p.parts, 'Unsafe source-relative path')
    return p


def source_guards(build):
    manifest = build / 'northern-n5/source-hashes.json'
    require(sha(manifest) == FROZEN_MANIFEST_SHA, 'Frozen source manifest differs')
    archived = json.loads(manifest.read_text())
    guarded = {k: v for k, v in archived.items()
               if (k.startswith('src/') and Path(k).suffix in {'.c', '.h', '.s', '.inc'}) or k == 'linker.ld'}
    require(guarded, 'No compiled source inputs found')
    for name, expected in guarded.items():
        require(sha(ROOT / relative_source(name)) == expected, 'Compiled source changed: ' + name)
    return {
        'frozen_manifest_sha256': FROZEN_MANIFEST_SHA,
        'compiled_source_files_checked': len(guarded),
        'compiled_source_manifest_canonical_sha256': canonical_sha(guarded),
        'guard_scope': 'src C/header/assembly/include files and linker.ld; excludes mutable documentation, Makefile and harnesses',
        'report_harness_hashes_are_historical': True,
    }


def report_info(build, relative, report):
    return {'report': 'build/' + relative, 'report_sha256': sha(build / relative),
            'report_bytes': (build / relative).stat().st_size,
            'suite': report.get('suite'), 'player_facing': False}


def checked_report(build, relative, expected):
    path = build / relative
    require(sha(path) == expected, 'Pinned report differs: ' + relative)
    return json.loads(path.read_text())


def window_summary(window):
    result = scalar_fields(window)
    trace = window.get('trace', [])
    n = window['hardware_frames']
    require(len(trace) == n, 'Timing trace frame count differs')
    require(all(t['update_delta'] == 1 and t['page_flip'] for t in trace), 'Dropped gameplay update or presentation')
    peak = max(t.get('cycles', t.get('render_cycles', 0)) for t in trace)
    require(peak == window.get('maximum_cycles', window.get('max_cycles')), 'Timing peak differs')
    require(peak < 280896, 'Timing exceeds native frame budget')
    result['verified_trace_frames'] = len(trace)
    result['verified_updates'] = sum(t['update_delta'] for t in trace)
    result['verified_page_flips'] = sum(bool(t['page_flip']) for t in trace)
    result['camera_positions_observed'] = len({tuple(t['camera']) for t in trace})
    if 'camera_parities' in window:
        result['camera_parities'] = window['camera_parities']
    if trace and 'visible_enemy_bodies' in trace[0]:
        result['five_visible_enemies_two_visible_hostile_shots_two_arrows_active_effect_frames'] = sum(
            t['visible_enemy_bodies'] >= 5 and t['visible_hostile_shots'] >= 2 and
            t['player_arrows'] >= 2 and t['northern_effect'] > 0 for t in trace)
    return result



# Populated only from the final successful make test test-tools invocation.
AGGREGATE_LOG_SHA = '821f5eb5e8cb955f329eb10902dd5e5a445b059bd796a8a810245c2ade1ab6bf'
AGGREGATE_PUBLIC_SHA = '5b92409cc61a20186def1d7bbcba13f4237d77d3a62739c2cba74a0073df887e'
AGGREGATE_REPORTS = {
    'first-chapter': 'qa/playthrough.json', 'review-with-corrupt-save': 'review/review-tests.json',
    'exploration': 'exploration/exploration-tests.json',
    'campaign-minimal': 'campaign-qa/campaign-report.json', 'campaign-optional': 'campaign-optional/campaign-report.json',
    'fullscreen': 'fullscreen-qa/fullscreen-report.json', 'evolution-eight': 'evolution-qa/evolution-report.json',
    'evolution-six-hearts': 'evolution-six-hearts/evolution-report.json', 'evolution-migrated': 'evolution-migrated/evolution-report.json',
    'advanced-powers': 'advanced-power-qa/advanced-power-report.json',
    'quickparty': 'quickparty-qa/quickparty-report.json', 'quickparty-evolved': 'quickparty-evolved-qa/quickparty-report.json',
    'expeditions': 'expedition-qa/expedition-report.json',
    'pr5-migration': 'pr5-quickparty-migration-qa/quickparty-migration-report.json',
    'river-journey': 'region-journey/region-journey.json', 'river-combat': 'region-combat/region-combat.json',
    'northern-journey': 'northern-journey/northern-journey.json',
    'northern-sky-route': 'northern-sky-route/northern-journey.json',
    'northern-stress': 'northern-stress/northern-stress.json',
    'northern-boss-controls': 'northern-boss-controls/northern-stress.json',
    'northern-modal-controller': 'northern-modal-pixels/northern-journey.json',
    'northern-combat': 'northern-combat/northern-combat.json',
}


def aggregate_summary(build, regeneration):
    require(AGGREGATE_LOG_SHA is not None, 'Whole-game aggregate completion is not pinned yet')
    log = build / 'n5-full-aggregate.log'
    require(sha(log) == AGGREGATE_LOG_SHA, 'Successful aggregate log differs')
    require(sha(build / 'emberbond.gba') == ROM_SHA and sha(build / 'emberbond.sym') == SYM_SHA,
            'Aggregate cartridge/symbols differ')
    require(regeneration is not None and sha(regeneration) ==
            'dab7abffb382c8638bc6fb5109feeb52b919ea13eb917c710717c60604bb531a', 'Asset regeneration evidence differs')
    art = json.loads(regeneration.read_text())
    require(not art['changed'] and art['existing_file_count'] == 859 and len(art['new']) == 4, 'Asset regeneration differs')
    rows = {}
    for name, relative in AGGREGATE_REPORTS.items():
        report = json.loads((build / relative).read_text())
        target = report.get('candidate', report)
        require(target.get('rom_sha256') == ROM_SHA, 'Aggregate report ROM differs: ' + name)
        sym = target.get('symbols_sha256', target.get('symbol_sha256'))
        require(sym in (None, SYM_SHA), 'Aggregate symbols differ: ' + name)
        checks = report.get('passes', report.get('checks', []))
        require(checks and not report.get('failures') and
                all(not isinstance(c, dict) or c.get('passed', True) for c in checks), 'Aggregate checks failed: ' + name)
        require(report.get('controller_only', report.get('ordinary_gameplay_controller_only')) is True,
                'Aggregate controller mode differs: ' + name)
        require(not report.get('game_ram_writes', report.get('normal_game_ram_writes', 0)), 'Aggregate RAM writes')
        rows[name] = dict(report_info(build, relative, report), checks_passed=len(checks), checks_failed=0,
            evidence='native controller inputs plus deliberate copied-SRAM corruption' if name == 'review-with-corrupt-save'
                     else 'native controller gameplay', symbols_hash_recorded=sym is not None)
    require(rows['northern-combat']['checks_passed'] == 8837 and
            rows['northern-modal-controller']['checks_passed'] == 161, 'Incomplete fresh Northern aggregate')
    perf = {}
    for route in ('minimal', 'optional'):
        relative = 'campaign-performance-' + route + '/campaign-performance.json'
        report = json.loads((build / relative).read_text())
        require(report['rom_sha256'] == ROM_SHA and report['symbols_sha256'] == SYM_SHA and
                report['full_strict_60hz_pass'] and not report['failures'] and
                not report['strict_cold_failures'] and not report['unavailable_fixtures'], 'Campaign cadence failed')
        perf[route] = dict(report_info(build, relative, report), full_strict_native_cadence_pass=True,
                          scene_count=len(report['scenes']), transition_count=len(report['transitions']))
    host = {}
    for name, relative in {
        'advanced-source-contract': 'advanced-power-qa/source-contract-report.json',
        'northern-orders-capacity': 'northern-host-cases.json',
        'northern-source-provenance': 'northern-source-provenance.json',
    }.items():
        report = json.loads((build / relative).read_text())
        checks = report.get('checks', report.get('cases', []))
        require(checks and all(c['passed'] for c in checks), 'Aggregate host checks failed')
        host[name] = dict(report_info(build, relative, report), checks_passed=len(checks), native_obtainability_proof=False)
    relative = 'quickparty-synthetic-qa/quickparty-report.json'
    synthetic = json.loads((build / relative).read_text())
    require(synthetic['candidate']['rom_sha256'] == ROM_SHA and not synthetic['failures'] and
            synthetic['controller_only'] is False and synthetic['synthetic_game_ram_writes'] == 3,
            'Synthetic interruption evidence differs')
    quickparty = dict(report_info(build, relative, synthetic), total_recorded_checks=len(synthetic['passes']),
        repeated_normal_checks=synthetic['normal_pass_count'],
        synthetic_checks=len(synthetic['passes']) - synthetic['normal_pass_count'], game_ram_writes=3,
        excluded_from_controller_total=True)
    return {'schema': 1, 'player_facing': False, 'spoilers': True, 'status': 'passed',
        'rom_sha256': ROM_SHA, 'symbols_sha256': SYM_SHA, 'rom_bytes': ROM_BYTES,
        'command': 'make test test-tools', 'exit_code': 0,
        'clean_rebuild': {'rom_and_symbols_byte_identical': True},
        'asset_regeneration': dict(art, report_sha256=sha(regeneration),
                                   new_files_are_excluded_generated_overviews=True),
        'completion_evidence': {'log': 'build/n5-full-aggregate.log', 'sha256': AGGREGATE_LOG_SHA,
                                'bytes': log.stat().st_size, 'raw_log_not_published': True},
        'native_suites': rows, 'native_controller_suite_count': len(rows) - 1,
        'native_controller_checks': sum(v['checks_passed'] for k, v in rows.items() if k != 'review-with-corrupt-save'),
        'mixed_review_checks': rows['review-with-corrupt-save']['checks_passed'],
        'campaign_cadence': perf, 'synthetic_host_reports': host, 'synthetic_quickparty': quickparty,
        'bridge_smoke_tests_completed': True,
        'host_scope': 'All make test host targets and make test-tools completed in the pinned successful log; only separately structured host reports are counted here',
        'prior_attempt': 'An obsolete advanced-power host shim failed before the fresh complete rerun; the shim was corrected without changing runtime/art',
        'counting_notes': [
            'One report per suite; intermediate campaign manifests copied into other reports are not counted again',
            'Assertions repeat across frames and branches; totals are not counts of distinct behaviors',
            'The independent historical N5 acceptance includes one additional modal equivalence check; this fresh no-comparison modal setup has 161 checks',
            'The separately retained 25-scene before/after modal comparison and player teaser are outside this fresh aggregate',
            'Do not add this rerun total to archived Northern acceptance totals as unique coverage'],
        'limits': ['Emulator verification only; physical GBA/flash cartridges untested',
                   'Full 128-form roster and later regions remain unfinished']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'build')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/northern')
    parser.add_argument('--aggregate-build', type=Path, help='Completed, log-pinned clean QA build directory')
    parser.add_argument('--art-regeneration-report', type=Path)
    args = parser.parse_args()
    build, output = args.build.resolve(), args.output.resolve()
    candidate = build / 'northern-n5'
    require(sha(candidate / 'emberbond.gba') == ROM_SHA, 'Frozen N5 ROM differs')
    require(sha(candidate / 'emberbond.sym') == SYM_SHA, 'Frozen N5 symbols differ')
    require((candidate / 'emberbond.gba').stat().st_size == ROM_BYTES, 'ROM size differs')
    guards = source_guards(build)
    native, suite_results = {}, {}
    for name, (relative, expected, checks) in REPORTS.items():
        report = checked_report(build, relative, expected)
        require(report['rom_sha256'] == ROM_SHA and report['symbols_sha256'] == SYM_SHA, name + ': target differs')
        require(report['controller_only'] is True and report['game_ram_writes'] == 0, name + ': not controller-only')
        require(not report['failures'] and len(report['checks']) == checks and
                all(c['passed'] is True for c in report['checks']), name + ': check outcomes differ')
        require(all(c.get('passed') is True for c in report['cases']), name + ': case failed')
        native[name] = report
        suite_results[name] = dict(report_info(build, relative, report), checks_passed=checks,
                                  checks_failed=0, functional_cases=len(report['cases']),
                                  source_report_sha256=report['provenance'].get('source_report_sha256'),
                                  harness_sha256=report.get('test_source_sha256'),
                                  harness_source_hashes=report.get('test_sources', {}))
    auxiliary = {k: checked_report(build, *v) for k, v in AUXILIARY.items()}
    acceptance = auxiliary['acceptance']
    require(acceptance['status'] == 'passed' and acceptance['rom_sha256'] == ROM_SHA, 'Acceptance failed')
    for item in acceptance['controller_only_native_suites'].values():
        require(sha(build / item['path'].removeprefix('build/')) == item['sha256'], 'Acceptance report reference differs')
    journey = native['journey']
    collection = journey['snapshots']['09-complete21-independent-reboot']
    earned = acceptance['acquisition_evidence']
    require(collection['obtained_form_ids'] == earned['obtained_form_ids'] and len(collection['obtained_form_ids']) == 21,
            'Final obtained collection differs')
    require(collection['quests'] == [3] * 22 and len(collection['owned_form_ids']) == 11, 'Final quests/instances differ')
    require(collection['sram_sha256'] == earned['sram_sha256'], 'Final SRAM metadata differs')
    require(sha(build / 'northern-native-n5/09-complete21-independent-reboot.sav') == collection['sram_sha256'], 'Final earned SRAM differs')
    fixture = ROOT / 'tests/fixtures/v5-revision2/all-eleven-town.sav'
    require(sha(fixture) == '74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106', 'Authentic R5 fixture differs')
    require(native['combat']['provenance']['source_report_sha256'] == REPORTS['journey'][1], 'Combat source differs')
    require(native['combat']['provenance']['source_machine_state_loaded'] is False, 'Combat imported machine state')
    timing = {name: [window_summary(w) for w in native[name]['frame_windows']] for name in ('stress', 'combat')}
    equivalence = auxiliary['modal-equivalence']
    require(equivalence['after_rom_sha256'] == ROM_SHA and equivalence['cross_rom_machine_states_loaded'] is False,
            'Modal target/provenance differs')
    require(len(equivalence['comparisons']) == 25 and all(
        x['passed'] and x['pixels_identical'] and x['visible_oam_identical'] for x in equivalence['comparisons']),
        'Modal comparison failed')
    scenes = auxiliary['modal-scenes']
    require(scenes['rom_sha256'] == ROM_SHA and scenes['symbols_sha256'] == SYM_SHA and
            scenes['controller_only'] and scenes['game_ram_writes'] == 0 and not scenes['source_machine_state_loaded'],
            'Modal scene provenance differs')
    host = auxiliary['host-orders-capacity']
    require(host['native'] is False and host['controller_only'] is False and host['count'] == 78 and
            len(host['cases']) == 78 and all(c['passed'] for c in host['cases']), 'Synthetic host cases differ')
    provenance = checked_report(build, PROVENANCE_PATH, PROVENANCE_SHA)
    require(provenance['host_only'] and provenance['emulator_runs'] == 0 and provenance['all_passed'] and
            len(provenance['checks']) == 15 and provenance['passed_checks'] == provenance['total_checks'] == 15 and
            all(c['passed'] for c in provenance['checks']) and
            sum(c.get('rejected') is True for c in provenance['checks']) == 14 and
            all(provenance['unchanged_inputs'].values()) and
            provenance['source_report_sha256'] == REPORTS['journey'][1] and
            provenance['combat_harness_sha256'] == native['combat']['test_source_sha256'], 'Provenance validator differs')
    mapping = (candidate / 'emberbond.map').read_text()
    sizes = {key: int(re.search(r'^\.' + key + r'\s+0x[0-9a-f]+\s+(0x[0-9a-f]+)', mapping, re.M).group(1), 16)
             for key in ('iwram', 'data', 'bss')}
    require(sizes['iwram'] == 28120 and sizes['data'] + sizes['bss'] == 47548, 'Native memory allocation differs')
    artifacts = {}
    def add(name, data):
        encoded = (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()
        require(len(encoded) < 32000, 'Public evidence exceeds size bound: ' + name)
        require(not any(p in encoded for p in (b'/workspace/', b'/home/', b'/tmp/', b'file://')), 'Local path leaked: ' + name)
        artifacts[name] = encoded
    common = {'schema': 1, 'player_facing': False, 'spoilers': True, 'rom_sha256': ROM_SHA, 'symbols_sha256': SYM_SHA}
    add('suites.json', dict(common, suites=suite_results,
        native_checks_passed=sum(r['checks_passed'] for r in suite_results.values()),
        check_count_scope='Six named Northern suites only; repeated assertions are counted as recorded, not unique behaviors'))
    add('acquisition.json', dict(common, acquisition=earned, final_quest_states=collection['quests'],
        main_route=acceptance['main_route_evidence'],
        prior_r5_fixture={'path': 'tests/fixtures/v5-revision2/all-eleven-town.sav', 'sha256': sha(fixture),
                         'source_rom_sha256': journey['provenance']['source_rom_sha256'],
                         'owned_instances': 6, 'historical_forms': 11, 'northern_progress': False},
        journey_report_sha256=REPORTS['journey'][1], source_machine_states_imported=False,
        acquisition_event_warning='Alternate branches may repeat a recruit event; only the independently rebooted collection establishes retained counts'))
    add('combat.json', dict(common, report_sha256=REPORTS['combat'][1], checks_passed=8837,
        functional_cases=85, cases=[scalar_fields(c) for c in native['combat']['cases']],
        coverage=sorted(set(native['combat']['coverage'])), provenance={
            k: v for k, v in native['combat']['provenance'].items() if k in (
                'source_report_sha256', 'source_rom_sha256', 'source_snapshot', 'sram_sha256',
                'source_machine_state_loaded', 'source_trust', 'ancestor_sram_sha256')}))
    add('timing.json', dict(common, hardware_clock_hz=16777216, frame_cycles=280896,
        nominal_refresh_hz=16777216 / 280896, windows=timing,
        method='Actual emulated hardware frames, update counter and displayed Mode4 page flips; render timer excludes final VBlank wait/OAM commit',
        limitation='Representative authored windows, not exhaustive theoretical pool maxima or physical-hardware certification'))
    pixels = [{**scalar_fields(x), 'camera': x['camera']} for x in native['stress']['pixel_cases']]
    require(len(pixels) == 4 and all(p['mismatches'] == 0 and p['rgb_mismatches'] == 0 for p in pixels), 'Pixel checks differ')
    modal_scenes = {name: {'rgb_sha256': s['rgb_sha256'], 'visible_oam_entries': len(s['oam']),
                          'visible_oam_canonical_sha256': canonical_sha(s['oam'])} for name, s in scenes['scenes'].items()}
    add('pixels-and-modal.json', dict(common, source_pixel_alignments=pixels,
        independent_boot_comparison=equivalence, current_rom_scenes=modal_scenes,
        resume_observations=scenes['resumes'],
        scene_report_sha256=AUXILIARY['modal-scenes'][1],
        modal_comparison_report_sha256=AUXILIARY['modal-equivalence'][1]))
    add('synthetic-host.json', dict(common, establishes_native_obtainability=False,
        objective_order_capacity={**report_info(build, AUXILIARY['host-orders-capacity'][0], host),
            'count': host['count'], 'cases': host['cases'], 'sources': host['sources'], 'scope': host['evidence_scope']},
        source_provenance={**report_info(build, PROVENANCE_PATH, provenance),
            'source_report_sha256': provenance['source_report_sha256'],
            'harness_sha256': provenance['test_source_sha256'],
            'combat_harness_sha256': provenance['combat_harness_sha256'],
            'synthetic_inputs': provenance['synthetic_inputs'], 'emulator_runs': 0,
            'valid_current_target_accepted': True, 'checks_passed': 15,
            'unchanged_inputs': provenance['unchanged_inputs'],
            'invalid_sources_rejected': 14, 'checks': provenance['checks']},
        persistence_evidence='../NORTHERN_SAVE3_VERIFICATION.json; host codec and isolated ARM subsystem evidence, not whole-frame measurements'))
    add('controls.json', dict(common,
        movement_cases=native['stress']['cases'], machine_timing_cases=native['boss-controls']['cases'],
        stress_report_sha256=REPORTS['stress'][1], machine_report_sha256=REPORTS['boss-controls'][1]))
    media = checked_report(build, MEDIA_PATH, MEDIA_SHA)
    require(media['rom_sha256'] == ROM_SHA and media['symbols_sha256'] == SYM_SHA and
            media['controller_only'] and media['game_ram_writes'] == 0 and not media['failures'] and
            len(media['checks']) == 110 and all(c['passed'] for c in media['checks']), 'Player media checks differ')
    require(all(media[k] == 0 for k in ('machine_state_loads', 'capture_sram_reloads', 'capture_cuts', 'capture_reset_count')),
            'Player capture is not uninterrupted')
    require(media['captured_frames'] == 1200 and all(media['native_frame_stats'][k] == 1200
            for k in ('hardware_frames', 'game_updates', 'display_page_flips')), 'Player cadence differs')
    require(media['files']['capture-start.sav']['sha256'] == media['files']['capture-end.sav']['sha256'],
            'Player capture changed saved progress')
    require(media['capture_rgb_stream_sha256'] == media['native_lossless_decoded_rgb_stream_sha256'] and
            media['native_audio_minus_video_seconds'] == 0, 'Lossless media verification differs')
    require(media['source_verification']['status'] == 'verified_against_frozen_build_manifest' and
            media['source_verification']['manifest_sha256'] == FROZEN_MANIFEST_SHA and
            media['test_sources']['tests/capture_northern_teaser.py'] ==
            '54440847d27b16b6a587ccb7de29c25a559f490e49e74d13ddea98bc3a700767', 'Player capture source provenance differs')
    media_files = {name: item for name, item in media['files'].items()
                   if name.endswith(('.mp4', '.mkv', '.wav', '.png'))}
    for name, item in media_files.items():
        path = build / Path(MEDIA_PATH).parent / relative_source(name)
        require(sha(path) == item['sha256'] and path.stat().st_size == item['bytes'], 'Player media file differs: ' + name)
    add('player-teaser.json', {
        'schema': 1, 'player_facing': True, 'spoilers': False, 'rom_sha256': ROM_SHA, 'symbols_sha256': SYM_SHA,
        'report': 'build/' + MEDIA_PATH, 'report_sha256': MEDIA_SHA,
        'harness_sha256': media['test_sources']['tests/capture_northern_teaser.py'],
        'source_verification': {k: v for k, v in media['source_verification'].items() if k != 'manifest_path'},
        'scope': media['scope'], 'checks_passed': 110, 'checks_failed': 0,
        'controller_only': True, 'game_ram_writes': 0, 'machine_state_loads': 0,
        'capture_cuts': 0, 'capture_reset_count': 0, 'captured_frames': media['captured_frames'],
        'hardware_clock_ratio': media['hardware_clock_ratio'], 'frame_rate': media['frame_rate'],
        'duration_seconds': media['duration_seconds'], 'native_resolution': media['native_resolution'],
        'video_resolution': media['video_resolution'], 'scaling': media['scaling'],
        'native_frame_stats': media['native_frame_stats'], 'audio': media['audio'],
        'native_audio': media['native_audio'], 'native_audio_minus_video_seconds': 0,
        'lossless_rgb_stream_sha256': media['native_lossless_decoded_rgb_stream_sha256'],
        'saved_progress_unchanged_during_capture': True,
        'preview_frame_offsets': media['preview_frame_offsets'], 'files': media_files,
        'scope_note': 'Media checks are separate from the six gameplay suites and the whole-game aggregate',
    })
    aggregate = None
    if args.aggregate_build:
        aggregate = aggregate_summary(args.aggregate_build.resolve(), args.art_regeneration_report)
    elif AGGREGATE_PUBLIC_SHA is not None:
        saved = output / 'aggregate.json'
        require(saved.is_file() and sha(saved) == AGGREGATE_PUBLIC_SHA,
                'Supply --aggregate-build to regenerate the frozen aggregate summary')
        aggregate = json.loads(saved.read_text())
    if aggregate is not None:
        add('aggregate.json', aggregate)
    summary = dict(common, date_utc='2026-10-05', release='Northern N5', rom_bytes=ROM_BYTES,
        save_wire_version=5, save_content_revision=3, source_guards=guards,
        memory_bytes={**sizes, 'ewram_data_plus_bss': sizes['data'] + sizes['bss'], 'iwram_code_limit': 28672},
        content={'implemented_obtainable_controller_verified_forms': 21, 'retained_family_instances': 11,
                 'total_areas': 30, 'northern_areas': 8, 'regional_quests': 22, 'northern_quests': 11,
                 'equipment_items': 19, 'new_equipment_items': 6, 'weapon_classes': 3,
                 'enabled_evolution_edges': 10, 'quick_slots': 4, 'target_forms': 128,
                 'authored_designs_including_disabled_legendary': 22, 'obtainable_legendary_forms': 0},
        native_checks_passed=sum(r['checks_passed'] for r in suite_results.values()), native_checks_failed=0,
        native_suite_counts={k: v['checks_passed'] for k, v in suite_results.items()},
        game_ram_writes=0, cross_rom_machine_states_loaded=False,
        controller_acceptance_source=report_info(build, AUXILIARY['acceptance'][0], acceptance),
        controller_acceptance_scope='Original five-suite acceptance plus separately validated combat suite; not a whole-game aggregate',
        verified_same_rom_state_sram_pairs_in_original_acceptance=acceptance['unique_same_rom_state_sram_pairs_verified'],
        whole_game_aggregate={'status': 'not_included_in_this_evidence_set',
                              'scope': 'These exact report counts establish the named Northern suites; consult VERIFICATION.md for separately completed whole-game checks'},
        synthetic_host_cases=78, synthetic_invalid_source_rejections=14, synthetic_source_provenance_checks=15,
        player_teaser={'frames': 1200, 'checks_passed': 110, 'duration_seconds': media['duration_seconds'],
                       'mp4_sha256': media_files['hearthwake-native-teaser.mp4']['sha256']},
        limits=['Physical GBA and flash cartridges untested; measurements use mGBA 0.10.5',
                'Cold Continue checkpoint decoding is a blocking load transition, not active gameplay cadence',
                'Host/synthetic results and isolated ARM save benchmarks are not native-controller acquisition or whole-engine timing',
                'The full 128-form roster, legendary progression and additional southern-island/magma-mountain/underwater regions remain unfinished',
                'No theoretical worst-case crowd, full-game campaign-length or whole-program stack-high-water claim'],
        files={name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in artifacts.items()})
    if aggregate is not None:
        summary['whole_game_aggregate'] = {
            'status': 'passed', 'report': 'aggregate.json',
            'report_sha256': hashlib.sha256(artifacts['aggregate.json']).hexdigest(),
            'native_controller_checks': aggregate['native_controller_checks'],
            'mixed_review_checks': aggregate['mixed_review_checks'],
            'counting_scope': 'Fresh complete rerun, separate from archived Northern suite and teaser counts',
        }
    add('summary.json', summary)
    output.mkdir(parents=True, exist_ok=True)
    for name, data in artifacts.items():
        (output / name).write_bytes(data)
    print(json.dumps({'files': len(artifacts), 'maximum_file_bytes': max(map(len, artifacts.values())),
                      'native_checks': summary['native_checks_passed'], 'rom_sha256': ROM_SHA}, indent=2))


if __name__ == '__main__':
    main()
