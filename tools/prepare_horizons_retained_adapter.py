#!/usr/bin/env python3
"""Prepare an explicit content8 successor to the preserved Return7 adapter.

Only copied test helpers change: expected current headers, an independent
read-only migration check, complete engine linkage and a PSG register mock.
Every original gameplay assertion and every cartridge source byte stays intact.
Preparation is not a test result.
"""
import argparse
import hashlib
import json
from pathlib import Path

import prepare_retained_native_adapter as prior

ROOT = Path(__file__).resolve().parents[1]
MODULES = ['horizons_game', 'horizons_art', 'horizons_quests',
           'horizons_creature_art', 'horizons_powers', 'horizons_power_art',
           'horizons_audio']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(candidate, output):
    # This exact revision is a deliberate contract, not a wildcard header.
    assert 'SAVE5_CONTENT_REVISION = 8,' in (candidate/'src/save5.h').read_text()
    src = prior.prepare(candidate, output)
    receipt = json.loads((output/'adapter-receipt.json').read_text())
    (output/'return7-preparation-receipt.json').write_text(
        json.dumps(receipt, indent=2)+'\n')
    changes = receipt['changes']

    def edit(name, pairs, explanation):
        path = src/name
        text = path.read_text()
        before = sha(path)
        for old, new in pairs:
            assert text.count(old) == 1, (name, old, text.count(old))
            text = text.replace(old, new, 1)
        path.write_text(text)
        row = changes.setdefault(name, {'original_sha256': sha(ROOT/name)})
        row['adapted_sha256'] = sha(path)
        row.setdefault('horizons_changes', []).append({
            'prior_adapted_sha256': before,
            'explanation': explanation,
            'replacements': [{'before': a, 'after': b} for a, b in pairs]})

    for name, pairs in prior.SUBSTITUTIONS.items():
        edits = [(after, after.replace('7', '8')) for _, after in pairs]
        if name in prior.MIGRATIONS:
            edits.append(('current7 CRC', 'current8 CRC'))
        edit(name, edits, 'Current content8 header; prior fixture and gameplay checks preserved.')

    edit('tests/retained_migration_validator.py', [
        ('prior_revision in (3,4,5,6)', 'prior_revision in (3,4,5,6,7)'),
        ('validate_bank(current_bank,7)', 'validate_bank(current_bank,8)')],
        'Independently prove content8 CRC, unchanged durable payload and preserved prior committed bank.')

    edit('tests/return_journey.py', [
        ("int.from_bytes(bank[12:14], 'little') == 7", "int.from_bytes(bank[12:14], 'little') == 8"),
        ('ordinary Continue commits content revision7', 'ordinary Continue commits content revision8'),
        ('revision6 to7 preserves every durable payload byte', 'revision6 to8 preserves every durable payload byte'),
        ("self.snapshot('00-revision7-exact-migration')", "self.snapshot('00-revision8-exact-migration')")],
        'Retained Return route upgrades exact revision6 input to8; payload and prior-bank assertions are unchanged.')
    edit('tests/return_companion_controls.py', [
        ("int.from_bytes(b[12:14],'little')==7", "int.from_bytes(b[12:14],'little')==8")],
        'Follow-up controls require a fresh same-candidate revision8 producer.')

    files = ['tests/test_save_feedback.py'] + [
        'tests/underwater_engine_review/'+name for name in (
            'test_legacy_deferred_anchor_linked.py',
            'test_legacy_deferred_anchor_current.py',
            'test_engine_lifecycle.py', 'test_bounded_magma_return.py',
            'test_bounded_southern_rest.py', 'test_bounded_magma_save_current.py')]
    for name in files:
        if name == 'tests/test_save_feedback.py':
            marker = '    subprocess.run(shlex.split('
            linkage = '    modules += '+repr(MODULES)+'\n'
        else:
            marker = "RESULT={'scope':"
            linkage = 'MODULES += '+repr(MODULES)+'\n'
        edit(name, [(marker, linkage+marker),
                    ("'-DGAME_HOST_TEST'", "'-DGAME_HOST_TEST','-DHORIZONS_AUDIO_HOST'")],
             'Link all real Horizons engine modules; only PSG MMIO uses the guarded host register array.')
        if name != 'tests/test_save_feedback.py':
            source_root = 'ROOT' if name.endswith('test_legacy_deferred_anchor_linked.py') else 'SOURCE_ROOT'
            edit(name, [(
                "assert CACHE_FIELD_COUNT in (32,34),'Retained indices require an explicit adapter for any other layout'",
                "from retained_horizons_cache import verify_cache_layout\n"
                + "RESULT['cache_layout_contract']=verify_cache_layout(" + source_root + ",CACHE_FIELD_COUNT)")],
                'Require exact pinned content8 game source and ordered36-field key; the original34-field prefix and all existing comparisons are unchanged; the view covers both complete pages.')

    edit('tests/retained_host_audio.c', [
        ('int music_tick,music_step;',
         'int music_tick,music_step;\nunsigned short horizons_audio_host_registers[128];')],
         'Provide inert PSG2 registers for real Horizons sequence code; no audio/timing claim.')

    runtime = json.loads((candidate/'build/source-hashes.json').read_text())
    assert all(sha(src/name) == value for name, value in runtime.items())
    assert all(sha(ROOT/name) == row['original_sha256']
               for name, row in changes.items() if 'original_sha256' in row)
    inputs = {str(path.relative_to(src)): sha(path)
              for directory in ('src', 'tests', 'assets', 'tools')
              for path in (src/directory).rglob('*')
              if path.is_file() and 'sysroot' not in path.parts
              and '__pycache__' not in path.parts
              and path.suffix in ('.c', '.h', '.s', '.inc', '.py', '.json', '.txt', '.sav')}
    inputs.update({name: sha(src/name) for name in ('Makefile', 'linker.ld')})
    (output/'adapter-inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')
    receipt.update(scope='Explicit content8 retained-test adapter; preparation only',
                   content_revision=8,
                   input_manifest_sha256=sha(output/'adapter-inputs.json'),
                   predecessor_receipt_sha256=sha(output/'return7-preparation-receipt.json'),
                   original_helpers_unchanged=True, runtime_unchanged=True,
                   preparation_script_sha256=sha(Path(__file__)))
    (output/'adapter-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'prepared': str(src), 'runtime_unchanged': True,
                      'receipt_sha256': sha(output/'adapter-receipt.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.candidate_source.resolve(), args.output.resolve())
