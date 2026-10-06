#!/usr/bin/env python3
"""Bounded source-pinned native evidence summaries, with full-report hashes.

Only passing exact-cartridge controller reports are accepted. The release
checklist separately establishes completed expected suite coverage; row counts
alone cannot establish completeness. Summaries deliberately do
not count synthetic tests, isolated ARM timing, or enabled catalog rows as
controller acquisition evidence. Full traces stay in build/ and are reproducible
with the checked-in harnesses; each summary pins their original report bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def summarize(path, rom_sha, symbols_sha):
    report = json.loads(path.read_text())
    assert report['rom_sha256'] == rom_sha and report['symbols_sha256'] == symbols_sha
    assert report.get('controller_only') is True and report.get('game_ram_writes') == 0
    assert report.get('failures') == []
    checks = report['checks']
    assert checks and all(c.get('passed') is True for c in checks)
    result = {k: report[k] for k in ('suite', 'rom_sha256', 'symbols_sha256', 'rom_bytes',
              'elf_sha256', 'source_manifest_sha256', 'content_contract_sha256',
              'emulator_bridge_sha256', 'emulator_bridge_source_sha256', 'test_sources',
              'timing_caveat', 'native_commands_accepted', 'coverage') if k in report}
    result.update(full_report_sha256=digest(path), full_report_bytes=path.stat().st_size,
                  passed_checks=len(checks), checks_canonical_sha256=canonical(checks),
                  failures=[], controller_only=True, game_ram_writes=0,
                  counting_note='Checks overlap other suites; do not interpret their sum as unique behaviors.')
    provenance = report.get('provenance', {})
    result['provenance'] = {k: v for k, v in provenance.items()
                            if 'sha256' in k or k in ('source_machine_state_loaded', 'trust', 'scope', 'snapshot')}
    windows = []
    for row in report.get('frame_windows', []):
        value = {k: v for k, v in row.items() if k not in ('trace', 'captures')}
        trace = row.get('trace', [])
        if trace:
            value['trace_canonical_sha256'] = canonical(trace)
            value['trace_count'] = len(trace)
            value['missed_update_or_flip_rows'] = [n for n, r in enumerate(trace)
                                                    if r.get('update_delta', 1) != 1 or not r.get('page_flip', True)]
            assert not value['missed_update_or_flip_rows']
        windows.append(value)
    result['frame_windows'] = windows
    result['snapshots'] = {}
    for name, record in report.get('snapshots', {}).items():
        value = {k: v for k, v in record.items() if k.endswith('sha256')}
        for key in ('owned_form_ids', 'obtained_form_ids', 'quests'):
            if key in record: value[key] = record[key]
        result['snapshots'][name] = value
    result['case_records'] = len(report.get('cases', []))
    result['cases_canonical_sha256'] = canonical(report.get('cases', []))
    result['pixel_case_records'] = len(report.get('pixel_cases', []))
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('rom', 'symbols', 'output'): p.add_argument('--' + key, type=Path, required=True)
    p.add_argument('--report', action='append', required=True, metavar='NAME=PATH')
    a = p.parse_args()
    rom_sha, symbols_sha = digest(a.rom), digest(a.symbols)
    a.output.mkdir(parents=True, exist_ok=True)
    index = {'schema': 1, 'scope': 'Exact-candidate native-controller summaries; developer spoilers',
             'rom_sha256': rom_sha, 'symbols_sha256': symbols_sha, 'reports': []}
    for spec in a.report:
        name, path = spec.split('=', 1)
        assert name and all(c.isalnum() or c in '-_' for c in name)
        source = Path(path)
        result = summarize(source, rom_sha, symbols_sha)
        target = a.output / (name + '.json')
        target.write_text(json.dumps(result, separators=(',', ':')) + '\n')
        assert target.stat().st_size < 90000, 'Split evidence rather than exceed public text payload limits'
        index['reports'].append({'path': target.name, 'sha256': digest(target),
                                 'full_report_sha256': result['full_report_sha256'],
                                 'passed_checks': result['passed_checks']})
    index['overlapping_native_check_sum'] = sum(r['passed_checks'] for r in index['reports'])
    (a.output / 'index.json').write_text(json.dumps(index, indent=2) + '\n')
    print(json.dumps(index, indent=2))

if __name__ == '__main__':
    main()
