#!/usr/bin/env python3
"""Forward-render regression: cold SRAM imports, then same-candidate controls.

This is not a fresh acquisition producer. It imports earned SRAM from a pinned
completed producer, rebuilds every trial origin with buttons on the candidate,
and loads only those newly created candidate's machine states for branch tests.
"""
import argparse
import json
from pathlib import Path
import traceback

from return_followup_diagnostics import Followup
from return_journey import digest, newest_bank
from return_collection_route import TRIALS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'producer-report', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('rom-sha', 'symbols-sha', 'elf-sha', 'manifest-sha', 'producer-sha'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    assert digest(args.producer_report) == args.producer_sha
    producer = json.loads(args.producer_report.read_text())
    assert producer['finished_scope'] == 'full' and not producer['failures']
    assert producer['controller_only'] and not producer['game_ram_writes']
    assert not producer['machine_state_loads'] and producer['global_native']['closed']
    assert not producer['global_native']['exceptions']
    build = args.candidate / 'build'
    run = Followup(build / 'emberbond.gba', build / 'emberbond.sym', args.output,
                   args.rom_sha, args.symbols_sha, args.elf_sha,
                   build / 'source-hashes.json', args.manifest_sha,
                   source_root=args.candidate, timing_mode='strict')
    run.source_producer = {
        'report': str(args.producer_report.resolve()), 'sha256': args.producer_sha,
        'source_rom_sha256': producer['rom_sha256'],
        'scope': 'Cross-candidate cold-SRAM forward-render regression only',
        'cross_candidate_machine_states_imported': 0,
    }
    run.producer_snapshots = {}
    try:
        for index in range(len(TRIALS)):
            key = f'trial-{index:02d}-start'
            saved = producer['snapshots'][key]
            assert digest(saved['sram_path']) == saved['sram_sha256']
            source_bank = newest_bank(Path(saved['sram_path']).read_bytes())
            run.cases.append({'forward_cold_sram_import': key,
                              'sram_path': saved['sram_path'],
                              'sram_sha256': saved['sram_sha256'],
                              'machine_state_import': False})
            run.e.load_save(saved['sram_path'])
            run.e.reset()
            run.step(150)
            run.measured(f'forward-trial{index}-bounded-cold',
                         lambda: (run.tap('START', 2, 90), run.settle()), cold_continue=True)
            current = newest_bank(run.e.bytes(0x0e000000, 32768))
            run.check(current[32:] == source_bank[32:],
                      'forward cold import preserves exact earned durable payload')
            run.begin_return_trial(index)
            run.producer_snapshots[key] = run.snapshots[key]
        run.check(run.machine_state_loads == 0,
                  'all forward origins were rebuilt through buttons from SRAM only')
        run.trial_control_matrix()
        run.finished_scope = 'segmented-forward-trial-controls'
        run.verify_closures()
    except Exception as exc:
        run.failures.append({'error': str(exc), 'traceback': traceback.format_exc(),
                             'status': run.status()})
        run.snapshot('failure', settle=False)
        raise
    finally:
        run.close_global_trace()
        run.report()
        run.e.close()
    return bool(run.failures)


if __name__ == '__main__':
    raise SystemExit(main())
