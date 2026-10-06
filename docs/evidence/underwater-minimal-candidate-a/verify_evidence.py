#!/usr/bin/env python3
"""Read-only portable evidence authentication; does not run a ROM or emulator."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def require(value, label):
    if not value:
        raise RuntimeError(label)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_parts(name):
    d = ROOT / name
    m = json.loads((d / 'manifest.json').read_text())
    data = []
    for row in m['parts']:
        part = (d / row['path']).read_bytes()
        require(len(part) == row['bytes'] and sha(part) == row['sha256'], 'Corrupt report part: ' + name)
        data.append(part)
    raw = b''.join(data)
    require(len(raw) == m['source_bytes'] and sha(raw) == m['source_sha256'], 'Report reconstruction failed: ' + name)
    return json.loads(raw), sha(raw)

def main():
    ledger = json.loads((ROOT / 'CHECKSUMS.json').read_text())
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name != 'CHECKSUMS.json' and '__pycache__' not in p.parts}
    require(actual == set(ledger), 'Missing or extra evidence files')
    for name, digest in ledger.items():
        require(sha((ROOT / name).read_bytes()) == digest, 'Checksum mismatch: ' + name)
    summary = json.loads((ROOT / 'summary.json').read_text())
    main_report, main_sha = read_parts('main-report')
    final, final_sha = read_parts('final-review-report')
    initial, _ = read_parts('startup-failure-report')
    first, _ = read_parts('first-review-report')
    sources, source_sha = read_parts('candidate-source-manifest')
    require(source_sha == 'f75b5b9924bda3e9118e64f80f12f5905d1d72cef166980c3d8a94d407484580' and len(sources) == 1161, 'Wrong candidate runtime manifest')
    require(final['rom_sha256'] == '0d7fd78733405a6fc8ec6eeca68ad207dfb11b91dcfe44a8d67f312552b46675', 'Wrong native ROM')
    require(final['symbols_sha256'] == 'da6615df0f932eb5f096442092962d2fa28fad684758640c65175bc535d8b176', 'Wrong symbols')
    require(final['source_main_report_sha256'] == main_sha, 'Final review uses a different main route')
    require(final['review_source_sha256'] == sha((ROOT / 'lifecycle-03-driver.py').read_bytes()), 'Final review driver differs')
    for report in (main_report, final):
        require(report['controller_only'] and report['game_ram_writes'] == 0, 'Native route authenticity flags differ')
        require(report['provenance']['sram_sha256'] == 'f584de3b29cb77731148b31b99dc40e0c7e4ec05f1aac42e0d38dd5b44612eeb', 'Wrong original minimal input')
    require(not main_report['failures'] and len(main_report['checks']) == 762 and all(c['passed'] for c in main_report['checks']), 'Main route did not pass')
    require(final['machine_state_loads'] == 0, 'Unexpected machine-state import')
    require(len(final['checks']) == 1187 and sum(c['passed'] for c in final['checks']) == 1177, 'Final assertion counts differ')
    require(len(final['failures']) == 10 and all(f['kind'] == 'whole-action-native-timing' for f in final['failures']), 'Timing failures were lost or functional failure appeared')
    failed_windows = []
    for w in final['frame_windows']:
        trace = w['trace']
        require(len(trace) == w['hardware_frames'], 'Incomplete hardware trace')
        require(w['updates'] == sum(t['delta'] for t in trace if not t['counter_reset']), 'Forward update count differs')
        require(w['flips'] == sum(t['flip'] for t in trace), 'Display page-flip count differs')
        require(w['max_cycles'] == max(t['cycles'] for t in trace), 'Maximum native cycles differs')
        if any(t['delta'] != 1 or not t['flip'] or t['cycles'] >= 280896 for t in trace):
            failed_windows.append(w['name'])
    require(sorted(failed_windows) == sorted(f['case'] for f in final['failures']), 'A strict frame violation was hidden')
    edges = {(e['from'],e['to']) for e in final['exit_checks']}
    require(len(edges) == 21 and (46,38) in edges and (38,46) in edges, 'Ordinary reciprocal exit coverage missing')
    require(any(e['from']==46 and e['to']==38 and e['spawn']==4 and e['position']==[416,240] for e in final['exit_checks']), 'Shell-lift spawn4 return missing')
    require(len(final['cold_boots']) == 8 and all(b['fresh_emulator'] and not b['machine_state_loaded'] for b in final['cold_boots']), 'Cold-boot evidence missing')
    require(len(initial['failures']) == 5 and len(first['failures']) == 10, 'Earlier failed attempts were altered')
    require(not summary['final_review']['acceptance_passed'], 'Strict failure incorrectly labeled accepted')
    print(json.dumps({'evidence_integrity_passed':True, 'strict_native_acceptance_passed':False,
                      'main_assertions_passed':762, 'independent_assertions_passed':1177,
                      'independent_timing_failures':10, 'directed_exit_edges':21,
                      'native_windows':len(final['frame_windows']), 'whole_action_hardware_frames':sum(w['hardware_frames'] for w in final['frame_windows']),
                      'source_manifest_files':len(sources), 'checksummed_files':len(ledger),
                      'emulator_run_by_verifier':False, 'final_report_sha256':final_sha},indent=2))

if __name__ == '__main__':
    main()
