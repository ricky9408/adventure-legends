#!/usr/bin/env python3
"""Tie the retained historical failure to accepted C and prove durable de-duplication.

Synthetic linked-engine host evidence only. Neither historical recipe is edited.
The accepted Horizons source/evidence is read only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import runpy
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adapter', type=Path, required=True)
    parser.add_argument('--accepted-horizons', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    adapter = args.adapter.resolve()
    prior = args.accepted_horizons.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = adapter / 'source'
    inputs = json.loads((adapter / 'adapter-inputs.json').read_text())
    receipt = json.loads((adapter / 'adapter-receipt.json').read_text())
    def verify():
        assert all(sha(source / name) == digest for name, digest in inputs.items())
        assert all(sha(source / 'build' / name) == digest
                   for name, digest in receipt['candidate'].items())
    verify()
    summary_path = prior / 'build/horizons-retained-boundary/summary.json'
    prior_summary = json.loads(summary_path.read_text())
    prior_log = prior / 'build/horizons-retained-boundary/legacy-anchor-current-final.log'
    assertion = "assert get('save_begin_pending')==1 and count('anchor')==1 and count('begin')==0"
    assert assertion in prior_log.read_text()
    assert prior_summary['rom_sha256'] == '4166bdafdba0bf689a8230d6d8d407ae7faf0271925df480b4e3b0aa917f1a91'
    assert any('legacy-anchor-current-final.log' in ' '.join(item.get('logs', []))
               for item in prior_summary['preserved_failures'])
    prior_run_path = prior / 'build/horizons-retained-boundary-export-final/run-status.json'
    prior_run = json.loads(prior_run_path.read_text())
    assert prior_run['result'] == 'PASS'
    assert prior_run['candidate']['emberbond.gba'] == prior_summary['rom_sha256']
    prior_source = prior / 'build/horizons-retained-boundary-export-final/source'
    prior_manifest = prior_source / 'build/source-hashes.json'
    assert sha(prior_manifest) == prior_run['candidate']['source-hashes.json']
    prior_hashes = json.loads(prior_manifest.read_text())
    unchanged = {}
    for name in ('src/magma_game.c', 'src/magma_quests.c'):
        assert sha(prior_source / name) == prior_hashes[name] == sha(source / name)
        unchanged[name] = prior_hashes[name]
    report = {'scope': __doc__, 'candidate': receipt['candidate'],
              'adapter_receipt_sha256': sha(adapter / 'adapter-receipt.json'),
              'helper_sha256': sha(__file__), 'historical_failure_is_still_failure': True,
              'prior_rom_sha256': prior_summary['rom_sha256'],
              'prior_manifest_sha256': sha(prior_manifest),
              'prior_failure_assertion': assertion,
              'prior_evidence': {str(p.relative_to(prior)): sha(p)
                                 for p in (summary_path, prior_log, prior_run_path)},
              'unchanged_magma_sources': unchanged, 'cases': []}
    os.environ.update(UNDERWATER_REVIEW_SOURCE=str(source),
                      UNDERWATER_REVIEW_MANIFEST=str(source / 'build/source-hashes.json'),
                      PROBE_RESULT_NAME=str(out / 'bounded-successor.json'),
                      PYTHONDONTWRITEBYTECODE='1')
    sys.dont_write_bytecode = True
    os.chdir(source)
    sys.argv = ['test_bounded_magma_save_current.py']
    probe = runpy.run_path(str(source / 'tests/underwater_engine_review/test_bounded_magma_save_current.py'))
    assert probe['RESULT']['passed'] and len(probe['RESULT']['checks']) == 51
    L, S, SRAM = (probe[n] for n in ('L', 'S', 'SRAM'))
    get, count, update, render = (probe[n] for n in ('get', 'count', 'update', 'render'))
    for fixture in (probe['BASE'], probe['FULL']):
        for area in (38, 39):
            for lit in (False, True):
                expected = probe['synchronous_oracle'](area, lit, fixture)
                bank = probe['setup'](area, lit, fixture)
                old = probe['loaded']()
                assert L.magma_game_interact() == 1
                revision = (get('magma_game_revision'), get('progression_revision'))
                heals = count('heal')
                health = (get('hero_hp_q4'), get('hp'))
                for _ in range(4):
                    assert L.magma_game_interact() == 1
                    assert revision == (get('magma_game_revision'), get('progression_revision'))
                    assert count('heal') == heals and health == (get('hero_hp_q4'), get('hp'))
                assert count('begin') == count('anchor') == 0 and bytes(SRAM) == bank
                L.save_frame()
                assert get('save_begin_pending') == 3 and get('game_state') == 6
                render()
                update(1023)
                assert get('save_begin_pending') == 2
                render()
                slices = probe['finish_proof'](bank, bytes(S), True)
                assert bytes(S) == expected
                committed = bytes(S)
                for _ in range(4):
                    assert L.magma_game_prepare_save_step() == probe['FAILED']
                    assert bytes(S) == committed and bytes(SRAM) == bank
                update(1023)
                assert count('begin') == 1 and get('save_begin_pending') == 0
                probe['drain']()
                assert get('game_state') == 1 and not get('save_failed')
                saved = probe['loaded']()
                assert saved.campaign.sequence == old.campaign.sequence + 1
                assert saved.campaign.room == area and saved.campaign.spawn == 3
                assert saved.quests.anchors[3] & (1 << (area - 38))
                for field in ('roster', 'quests', 'equipment'):
                    assert bytes(getattr(saved, field)) == bytes(getattr(S, field))
                final_bank = bytes(SRAM)
                for _ in range(4):
                    L.save_frame()
                    assert not get('save_requested') and get('game_state') == 1
                    assert count('begin') == 1 and bytes(SRAM) == final_bank
                report['cases'].append({'fixture': fixture, 'area': area, 'previously_lit': lit,
                                        'duplicate_queue_calls': 4, 'proof_updates': slices,
                                        'stale_commit_calls_rejected': 4, 'writer_begins': 1,
                                        'durable_sequence_delta': 1, 'exact_saved_payload': True})
    verify()
    report.update(passed=True, inputs_and_candidate_unchanged=True,
                  bounded_successor_sha256=sha(out / 'bounded-successor.json'))
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': True, 'duplicate_durable_cases': len(report['cases']),
                      'historical_failure_preserved': True, 'output': str(out / 'report.json')}))


if __name__ == '__main__':
    main()
