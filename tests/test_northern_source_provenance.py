#!/usr/bin/env python3
"""Reproduce Northern combat-source provenance acceptance and rejection tests.

Run after the same-target controller journey, for example:
  python3 tests/test_northern_source_provenance.py \
    --source-report build/northern-journey/northern-journey.json \
    --rom build/emberbond.gba --symbols build/emberbond.sym

The sole accepted input is a fresh, successful, current-source journey for the
provided ROM and symbols. Fourteen negative cases mutate temporary JSON copies
only. No archived N0/N1 artifact is required, no SRAM bytes are altered, and no
emulator or game-RAM mutation occurs. Source files are hash-checked afterward.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path

from northern_combat_tests import ROOT, SOURCE_SNAPSHOT, digest, validate_source_report


def mutate_cases():
    """Each denial must reach its intended guard, not fail incidentally on IO."""
    zero = '0' * 64
    return (
        ('untrusted-foreign-rom', 'Unpinned cross-ROM report',
         lambda p: p.__setitem__('rom_sha256', zero)),
        ('wrong-symbols', 'Unpinned cross-ROM report',
         lambda p: p.__setitem__('symbols_sha256', zero)),
        ('RAM-writing-producer', 'Source is not controller-only',
         lambda p: p.__setitem__('game_ram_writes', 1)),
        ('non-controller-producer', 'Source is not controller-only',
         lambda p: p.__setitem__('controller_only', False)),
        ('failed-producer-check', 'Source journey did not pass',
         lambda p: p['checks'][0].__setitem__('passed', False)),
        ('failed-producer-suite', 'Source journey did not pass',
         lambda p: p['failures'].append({'error': 'synthetic rejection test'})),
        ('unverified-R5-ancestor', 'Unverified R5 ancestor',
         lambda p: p['provenance'].__setitem__('sram_sha256', zero)),
        ('wrong-controller-source', 'Source journey script hash differs: tests/northern_journey.py',
         lambda p: p['test_sources'].__setitem__('tests/northern_journey.py', zero)),
        ('wrong-content-contract', 'Source contract differs',
         lambda p: p.__setitem__('content_contract_sha256', zero)),
        ('incomplete-lifecycle', 'Source journey has not finished its lifecycle checks',
         lambda p: p['snapshots'].pop('11-north-death-retry')),
        ('missing-recruitment', 'Missing native recruitment evidence',
         lambda p: p.__setitem__('acquisitions', [])),
        ('wrong-SRAM-hash', 'Snapshot SRAM bytes differ: ' + SOURCE_SNAPSHOT,
         lambda p: p['snapshots'][SOURCE_SNAPSHOT].__setitem__('sram_sha256', zero)),
        ('false-owned-metadata', 'Snapshot metadata disagrees with CRC-valid SRAM',
         lambda p: p['snapshots'][SOURCE_SNAPSHOT]['owned_form_ids'].__setitem__(0, 127)),
        ('wrong-snapshot-target', 'Snapshot target differs from journey',
         lambda p: p['snapshots']['04-machine-ready'].__setitem__('rom_sha256', zero)),
    )


def run(source_report: Path, rom: Path, symbols: Path) -> dict:
    if not __debug__:
        raise RuntimeError('Run without Python -O: the production validator uses assertions')
    source_report, rom, symbols = (p.resolve() for p in (source_report, rom, symbols))
    rom_sha, symbols_sha = digest(rom), digest(symbols)
    evidence = validate_source_report(source_report, rom_sha, symbols_sha)
    if evidence['trust'] != 'same-target-current-controller-journey':
        raise AssertionError('Generate a fresh same-target journey; an archived pin is not this test fixture')

    # Make copied manifests independent of their temporary directory. These
    # paths refer only to unchanged inputs already authenticated above.
    baseline = copy.deepcopy(evidence['report'])
    baseline['rom_path'], baseline['symbols_path'] = str(rom), str(symbols)
    baseline['provenance']['fixture_path'] = evidence['ancestor_fixture']
    for name, item in evidence['snapshots'].items():
        baseline['snapshots'][name]['sram_path'] = str(item['path'])

    protected = {
        'source_report': source_report,
        'ROM': rom,
        'symbols': symbols,
        'combat_harness': ROOT / 'tests/northern_combat_tests.py',
        'ancestor_fixture': Path(evidence['ancestor_fixture']),
    }
    protected.update({name: item['path'] for name, item in evidence['snapshots'].items()})
    before = {name: digest(path) for name, path in protected.items()}
    checks = []
    with tempfile.TemporaryDirectory(prefix='northern-source-provenance-') as directory:
        directory = Path(directory)
        accepted = directory / 'accepted-same-target.json'
        accepted.write_text(json.dumps(baseline, indent=2) + '\n')
        accepted_result = validate_source_report(accepted, rom_sha, symbols_sha)
        checks.append({
            'case': 'accepted-same-target',
            'passed': accepted_result['trust'] == 'same-target-current-controller-journey',
            'trust': accepted_result['trust'],
            'temporary_manifest_sha256': digest(accepted),
        })
        for name, expected, change in mutate_cases():
            mutated = copy.deepcopy(baseline)
            change(mutated)
            path = directory / (name + '.json')
            path.write_text(json.dumps(mutated, indent=2) + '\n')
            result = {'case': name, 'expected_rejection': expected,
                      'temporary_manifest_sha256': digest(path)}
            try:
                validate_source_report(path, rom_sha, symbols_sha)
            except AssertionError as exc:
                result.update(rejected=True, reason=str(exc), passed=str(exc) == expected)
            except Exception as exc:
                result.update(rejected=True, reason=f'{type(exc).__name__}: {exc}', passed=False)
            else:
                result.update(rejected=False, reason='Invalid manifest was accepted', passed=False)
            checks.append(result)

    unchanged = {name: digest(path) == before[name] for name, path in protected.items()}
    return {
        'suite': 'northern-combat-source-provenance',
        'host_only': True, 'emulator_runs': 0, 'game_ram_writes': 0, 'sram_mutations': 0,
        'synthetic_inputs': 'Fourteen rejected temporary JSON mutations only; no fabricated native evidence',
        'source_report': str(source_report), 'source_report_sha256': before['source_report'],
        'rom_path': str(rom), 'rom_sha256': rom_sha,
        'symbols_path': str(symbols), 'symbols_sha256': symbols_sha,
        'test_source_sha256': digest(__file__),
        'combat_harness_sha256': before['combat_harness'],
        'checks': checks, 'unchanged_inputs': unchanged,
        'passed_checks': sum(check['passed'] for check in checks), 'total_checks': len(checks),
        'all_passed': all(check['passed'] for check in checks) and all(unchanged.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report', required=True, type=Path)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--symbols', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/northern-source-provenance-tests.json',
                        help='JSON report path (default: build/northern-source-provenance-tests.json)')
    args = parser.parse_args()
    output = args.output.resolve()
    protected_outputs = {p.resolve() for p in (
        args.source_report, args.rom, args.symbols, Path(__file__),
        ROOT / 'tests/northern_combat_tests.py', ROOT / 'assets/northern_region/contract.json',
    )}
    if output.suffix.lower() != '.json' or output in protected_outputs:
        parser.error('--output must be a separate JSON report, never an input or source file')
    try:
        report = run(args.source_report, args.rom, args.symbols)
    except Exception as exc:
        report = {'suite': 'northern-combat-source-provenance', 'host_only': True,
                  'emulator_runs': 0, 'game_ram_writes': 0, 'sram_mutations': 0,
                  'all_passed': False, 'setup_error': f'{type(exc).__name__}: {exc}'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    if report['all_passed']:
        print(f"PASS {report['passed_checks']}/{report['total_checks']}: same-target accepted; "
              '14 intended denials; source files unchanged')
    else:
        print('FAIL: ' + report.get('setup_error', 'source provenance check failed'), file=sys.stderr)
        for check in report.get('checks', []):
            if not check['passed']:
                print(f"  {check['case']}: {check.get('reason', 'unexpected acceptance')}", file=sys.stderr)
    print(f'Report: {args.output.resolve()}')
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
