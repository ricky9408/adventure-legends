#!/usr/bin/env python3
"""Package exact final-C native evidence, or verify its portable source export.

The export contains controller-earned SRAM and lossless receipts, not emulator
states or executables. --verify needs no historical workspace or native tools.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path('docs/evidence/horizons-native-c')
FIXTURES = Path('tests/fixtures/v5-revision8')
PINS = {
    'emberbond.gba': '4166bdafdba0bf689a8230d6d8d407ae7faf0271925df480b4e3b0aa917f1a91',
    'emberbond.elf': 'c5648eb363bdcfaf2e9f553d003dd4ca2150f23bb8607d042470ae85ee19dc28',
    'emberbond.sym': 'e0cd163b6233c850c8c86711aeff39ce2c7f62de3cffab0e9fcf76ebea693d71',
    'source-hashes.json': 'e4f99d30802a5e6a97f1d5c639ff3f3d8d59ddb2ad4a91d6c61b212b0ed91a54',
}
STATUS_SHA = '8d77fa5e49715a8225fce8913f38e5e2d0161452cb8d5fd1c8895891b344cde8'
HELPER_SHA = '441aa8be60fd1df6003f5a6ce52a2f1973163978aabfa80944d9528d7fdead07'
TEASER_SHA = '932feb9a565e46fba3032e94a7da728d036662a2e0edbe3592a48136c80fe221'
REPORTS = {
    'full': '1d4e000918e7b77bd5f6e2585abff3e7e13c3c703eb4b50a14546e647d6cc45a',
    'repeats': '98ed0d0bb4ed3b12220e8cfee68804d7d62292c6efdbf9308882243c7a2c7c3e',
    'minimal-stage-lifecycle': '99d471bdbcfde387a6eba41a766daec3831b5af45dc086bc20d71b9c685a9adf',
    'minimal-water': 'f78d5b7cab0bace554106b0931a6da9debb3b739b373b82a0651747f38cd467d',
}
# stage, original snapshot, exported SRAM name, historical forms, individuals,
# whether this exact snapshot follows a measured ordinary SRAM cold reload.
SNAPSHOTS = [
    ('full', '07-all120-cold-reboot-after', 'horizons-all120-64-cold.sav', 120, 64, True),
    ('repeats', 'all12-repeats-cold-reboot-after', 'horizons-all120-76-repeats-cold.sav', 120, 76, True),
    ('minimal-stage-lifecycle', 'main-cold-save-after', 'horizons-minimal18-stage-cold.sav', 18, 18, True),
    ('minimal-water', '04-main-horizons-complete', 'horizons-minimal18-water-saved.sav', 18, 18, False),
    ('full', '05-all60-quests46-gear', 'horizons-all116-64-before-evolutions.sav', 116, 64, False),
    ('minimal-water', '01-horizons-intro', 'horizons-fairground15-teaser-input.sav', 15, 15, False),
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def checked_json(path, expected=None):
    if expected:
        require(digest(path) == expected, f'Hash mismatch: {path}')
    return json.loads(path.read_bytes())


def safe_path(root, relative):
    relative = Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts, f'Unsafe relative path: {relative}')
    result = root / relative
    require(result.resolve().is_relative_to(root.resolve()), f'Path escapes root: {result}')
    return result


def write_exact(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == content, f'Refusing to replace different existing bytes: {path}')
    else:
        path.write_bytes(content)


def validate_report(report):
    require(report['controller_only'] and report['game_ram_writes'] == 0 and
            report['machine_state_loads'] == 0, 'Controller provenance failed')
    require(not report['failures'] and all(c['passed'] for c in report['checks']), 'Failed checks')
    for key, filename in [('rom_sha256', 'emberbond.gba'), ('elf_sha256', 'emberbond.elf'),
                          ('symbols_sha256', 'emberbond.sym'), ('source_manifest_sha256', 'source-hashes.json')]:
        require(report[key] == PINS[filename], f'Candidate mismatch: {key}')
    g = report['global_native']
    require(g['enabled'] and g['closed'] and not g['exceptions'], 'Incomplete global frame gate')
    require(g['hardware_frames'] == g['strict_frames'] + g['loader_frames'], 'Frame totals disagree')
    require(all(p['done'] and p['hardware_frames'] <= 160 for p in g['cold_prefixes']), 'Unbounded cold prefix')


def validate_trace(path, summary):
    count = strict = loader = maximum = oam = 0
    boot_frames = {}
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            count += 1
            require(row['sample_index'] == count - 1, f'Trace sample gap at {count}')
            boot = row['boot_serial']
            expected_frame = boot_frames.get(boot, 0) + 1
            require(row['hardware_frame'] == expected_frame, f'Trace hardware frame gap at {count}')
            boot_frames[boot] = expected_frame
            if row['cold_loader_exempt']:
                loader += 1
                continue
            strict += 1
            require(row['update_delta'] == 1 and row['page_flip'], f'Frame cadence failed at {count}')
            require(row['cycles'] < 280896 and row['obj_count'] <= 128, f'Hardware bound failed at {count}')
            require(all(row['music'][k] == 0 for k in ['music_faults', 'music_recoveries', 'music_stopped']),
                    f'Audio gate failed at {count}')
            maximum = max(maximum, row['cycles'])
            oam = max(oam, row['obj_count'])
    require([count, strict, loader, maximum, oam] == [summary[k] for k in
            ['hardware_frames', 'strict_frames', 'loader_frames', 'maximum_cycles', 'maximum_obj_count']],
            f'Trace/summary mismatch: {path}')


def package(root, native, teaser):
    status = checked_json(native / 'run-status.json', STATUS_SHA)
    require(status['candidate'] == PINS and status['all_requested_stages_passed'] and
            status['runtime_closure_still_exact'] and status['helper_closure_still_exact'], 'Candidate incomplete')
    for name, expected in PINS.items():
        require(digest(native / 'candidate' / name) == expected, f'Candidate changed: {name}')
    runtime = checked_json(native / 'candidate/source-hashes.json')
    for relative, expected in runtime.items():
        require(digest(safe_path(native / 'runtime-source', relative)) == expected, f'Frozen runtime changed: {relative}')
    reports = {stage: checked_json(native / stage / 'horizons-journey.json', sha) for stage, sha in REPORTS.items()}
    media = checked_json(teaser / 'teaser-report.json', TEASER_SHA)
    for report in [*reports.values(), media]:
        validate_report(report)
    rows = []

    def add(source, relative, compress=False, decode_gzip=False):
        target = safe_path(root, relative)
        original_sha = digest(source)
        raw_hash = hashlib.sha256()
        raw_bytes = 0
        output = io.BytesIO()
        source_open = gzip.open if decode_gzip else open
        with source_open(source, 'rb') as stream:
            if compress:
                # Empty filename, zero timestamp and fixed level: no host paths or clock in gzip header.
                with gzip.GzipFile(fileobj=output, mode='wb', filename='', mtime=0, compresslevel=9) as packed:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        raw_hash.update(chunk)
                        raw_bytes += len(chunk)
                        packed.write(chunk)
            else:
                content = stream.read()
                raw_hash.update(content)
                raw_bytes = len(content)
                output.write(content)
        content = output.getvalue()
        write_exact(target, content)
        rows.append(dict(path=str(relative), bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
                         encoding='gzip' if compress else 'identity', raw_bytes=raw_bytes,
                         raw_sha256=raw_hash.hexdigest(), original_path=str(source.resolve()),
                         original_bytes=source.stat().st_size, original_sha256=original_sha,
                         original_encoding='gzip' if decode_gzip else 'identity'))

    add(native / 'run-status.json', EVIDENCE / 'run-status.json')
    add(native / 'candidate/source-hashes.json', EVIDENCE / 'runtime-source-hashes.json')
    add(native / 'helpers/helper-hashes.json', EVIDENCE / 'runner-helper-hashes.json')
    require(digest(native / 'helpers/helper-hashes.json') == HELPER_SHA, 'Runner helper manifest changed')
    for stage, report in reports.items():
        require(report['timing_mode'] == 'strict', f'Non-strict report: {stage}')
        add(native / stage / 'horizons-journey.json', EVIDENCE / stage / 'horizons-journey.json.gz', True)
        for name in ['helper-source-hashes.json', 'emulator-library.json']:
            add(native / stage / name, EVIDENCE / stage / name)
        trace = native / stage / 'native-global.jsonl.gz'
        require(digest(trace) == report['global_native']['trace_sha256'], f'Trace hash changed: {stage}')
        validate_trace(trace, report['global_native'])
        add(trace, EVIDENCE / stage / 'native-global.jsonl.gz', True, True)
    for name in ['teaser-report.json', 'horizons-journey.json']:
        add(teaser / name, EVIDENCE / 'teaser' / (name + '.gz'), True)
    for name in ['helper-source-hashes.json', 'emulator-library.json']:
        add(teaser / name, EVIDENCE / 'teaser' / name)
    for name, expected in [('native-global.jsonl.gz', media['global_native']['trace_sha256']),
                           ('capture-frame-trace.jsonl.gz', media['files']['capture-frame-trace.jsonl.gz']['sha256'])]:
        require(digest(teaser / name) == expected, f'Teaser trace changed: {name}')
        add(teaser / name, EVIDENCE / 'teaser' / name, True, True)
    validate_trace(teaser / 'native-global.jsonl.gz', media['global_native'])

    # Archive the exact consumed text helpers, including their compiled bridge/header receipt.
    # Runtime inputs are already in the source export and are bound by their separate manifest.
    helpers = {}
    omitted = {}
    for base, mapping in [(native / 'helpers', checked_json(native / 'helpers/helper-hashes.json')),
                          (teaser / 'helper-source', media['helper_sources'])]:
        for relative, expected in mapping.items():
            source = safe_path(base, relative)
            require(digest(source) == expected, f'Frozen helper changed: {relative}')
            if Path(relative).suffix not in {'.py', '.c', '.sh', '.json'}:
                omitted[relative] = expected
                continue
            if relative in helpers:
                require(helpers[relative] == expected, f'Conflicting frozen helper: {relative}')
                continue
            helpers[relative] = expected
            add(source, EVIDENCE / 'frozen-helpers' / (relative + '.gz'), True)

    fixture_rows = []
    for stage, name, output, history, count, cold in SNAPSHOTS:
        report = reports[stage]
        snapshot = report['snapshots'][name]
        source = native / stage / (name + '.sav')
        require(source.stat().st_size == 32768 and digest(source) == snapshot['sram_sha256'], f'SRAM mismatch: {source}')
        require(snapshot['sram_export'] == 'mCore.savedataClone', 'Unexpected SRAM export method')
        require(len(snapshot['obtained_form_ids']) == history and len(snapshot['individuals']) == count,
                f'Unexpected fixture collection: {name}')
        require(len({x['instance_id'] for x in snapshot['individuals']}) == count, f'Duplicate identity: {name}')
        add(source, FIXTURES / output)
        fixture_rows.append(dict(path=str(FIXTURES / output), bytes=32768, sha256=snapshot['sram_sha256'],
            stage=stage, source_snapshot=name, producer_path=str(EVIDENCE / stage / 'horizons-journey.json.gz'),
            producer_raw_sha256=REPORTS[stage], original_producer_path=str((native / stage / 'horizons-journey.json').resolve()),
            original_sram_path=snapshot['sram_path'], ordinary_cold_reload_observed=cold,
            history_count=history, individual_count=count, claimed_quest_count=snapshot['quests'].count(3),
            gear_count=len(snapshot['gear_items']), snapshot=snapshot, source_ancestry=report['provenance']))
    provenance = dict(schema=1, content_revision=8, save_format=5, candidate=PINS,
        run_status_path=str(EVIDENCE / 'run-status.json'), run_status_sha256=STATUS_SHA,
        scope='Automated controller-earned cartridge SRAM, copied byte-for-byte; no player data or emulator machine states.',
        usage='Read fixtures through the real save decoder. Copy before using in an emulator. Do not count fixture imports as fresh native acquisition.',
        freeze_status='Native gates passed. Source-export replay and overall release acceptance are separate; this package does not modify migration policy.',
        fixtures=fixture_rows)
    provenance_path = root / FIXTURES / 'provenance.json'
    write_exact(provenance_path, json_bytes(provenance))
    for relative in [FIXTURES / 'provenance.json', FIXTURES / 'README.md', EVIDENCE / 'README.md']:
        add(root / relative, relative)
    totals = {key: sum(r['global_native'][key] for r in reports.values()) for key in
              ['hardware_frames', 'strict_frames', 'loader_frames']}
    totals['maximum_cycles'] = max(r['global_native']['maximum_cycles'] for r in reports.values())
    totals['maximum_obj_count'] = max(r['global_native']['maximum_obj_count'] for r in reports.values())
    manifest = dict(schema=1, candidate=PINS, native_totals=totals, report_raw_sha256=REPORTS,
        run_status_sha256=STATUS_SHA, teaser_report_raw_sha256=TEASER_SHA,
        package_script_path='tools/package_horizons_evidence.py', package_script_sha256=digest(Path(__file__)),
        scope='Exact final-C native matrix and teaser receipts plus authentic revision8 SRAM fixtures. No overall release acceptance asserted.',
        self_contained='All listed archive files, exact reports, full compact frame traces, frozen text helpers and fixture SRAM are bundled. Verification requires only Python standard library.',
        external_scope='Original absolute paths are historical provenance, not required local paths. ROM, ELF, symbols, emulator and bridge binaries, consumed external headers, full runtime-source copies, screenshots and A/V media are omitted. The runtime manifest maps into the separate source export. Original media hashes remain in the exact teaser report. This is not a self-contained historical execution environment.',
        omitted_binary_helper_sha256=omitted, files=sorted(rows, key=lambda r: r['path']))
    write_exact(root / EVIDENCE / 'manifest.json', json_bytes(manifest))
    return verify(root)


def verify(root):
    manifest_path = root / EVIDENCE / 'manifest.json'
    manifest = checked_json(manifest_path)
    require(manifest['candidate'] == PINS, 'Wrong packaged candidate')
    require(digest(root / manifest['package_script_path']) == manifest['package_script_sha256'], 'Packaging script changed')
    listed = set()
    for row in manifest['files']:
        path = safe_path(root, row['path'])
        require(row['path'] not in listed, f'Duplicate manifest path: {path}')
        listed.add(row['path'])
        require(path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], f'Packaged bytes changed: {path}')
        raw_hash = hashlib.sha256()
        raw_bytes = 0
        opener = gzip.open if row['encoding'] == 'gzip' else open
        with opener(path, 'rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                raw_hash.update(chunk)
                raw_bytes += len(chunk)
        require(raw_hash.hexdigest() == row['raw_sha256'] and raw_bytes == row['raw_bytes'], f'Lossless decoding failed: {path}')
    present = {str(p.relative_to(root)) for folder in [EVIDENCE, FIXTURES] for p in (root / folder).rglob('*') if p.is_file()}
    require(present == listed | {str(EVIDENCE / 'manifest.json')}, 'Unlisted or missing package files')
    status = checked_json(root / EVIDENCE / 'run-status.json', STATUS_SHA)
    require(status['all_requested_stages_passed'], 'Packaged matrix did not pass')
    reports = {}
    for stage, expected in REPORTS.items():
        data = gzip.decompress((root / EVIDENCE / stage / 'horizons-journey.json.gz').read_bytes())
        require(hashlib.sha256(data).hexdigest() == expected, f'Producer changed: {stage}')
        reports[stage] = json.loads(data)
        validate_report(reports[stage])
        validate_trace(root / EVIDENCE / stage / 'native-global.jsonl.gz', reports[stage]['global_native'])
    media_raw = gzip.decompress((root / EVIDENCE / 'teaser/teaser-report.json.gz').read_bytes())
    require(hashlib.sha256(media_raw).hexdigest() == TEASER_SHA, 'Teaser producer changed')
    media = json.loads(media_raw)
    validate_report(media)
    validate_trace(root / EVIDENCE / 'teaser/native-global.jsonl.gz', media['global_native'])
    provenance = checked_json(root / FIXTURES / 'provenance.json')
    for fixture in provenance['fixtures']:
        snapshot = reports[fixture['stage']]['snapshots'][fixture['source_snapshot']]
        require(fixture['snapshot'] == snapshot and digest(root / fixture['path']) == snapshot['sram_sha256'],
                f'Fixture producer mismatch: {fixture["path"]}')
    return dict(verified=True, files=len(listed) + 1, fixture_count=len(provenance['fixtures']),
                bytes=sum(r['bytes'] for r in manifest['files']) + manifest_path.stat().st_size,
                manifest_path=str(EVIDENCE / 'manifest.json'), manifest_sha256=digest(manifest_path),
                native_totals=manifest['native_totals'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Verify portable package without historical inputs')
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    parser.add_argument('--native-root', type=Path, default=ROOT / 'build/native-horizons-final-c01')
    parser.add_argument('--teaser-root', type=Path, default=ROOT / 'build/native-horizons-teaser-c01')
    args = parser.parse_args()
    result = verify(args.repo_root.resolve()) if args.verify else package(args.repo_root.resolve(), args.native_root.resolve(), args.teaser_root.resolve())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
