#!/usr/bin/env python3
"""Read-only, standard-library authentication of the final-D minimal fixture.

Run from any working directory. No emulator, machine-state load, game-RAM write,
SRAM mutation, current catalog, or third-party Python package is used.
"""
import argparse
import binascii
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROM = '90ba47f30a0c94c28f073d26cc31ac5f5c736eb4d6e704d090892d2776f1ffb2'
ELF = '0b56a0a525ef59d36b14a89a2786e5811f29fd9a54c386093fa06528f3afcc99'
SYMBOLS = 'add52be1a5d23d2e8df8fd616f4ef1c7fde8d3e1906e1d789925d68476cf50f6'
REPORT = 'c650e0982ff84ecda77faf4cc75270d2eff6ac73f05596ed8ffedd3f39715632'
MANIFEST = 'a72fd93eddb0a39322b22e45caf0f4ac49496d962776ee616dfd83642342ef3f'
SRAM = 'f584de3b29cb77731148b31b99dc40e0c7e4ec05f1aac42e0d38dd5b44612eeb'
PRIOR_REPORT = 'b028d1aa5020b53fa9b17eed863921d39d66c6bff0e93c93b464546452045b09'
PRIOR_SRAM = '968066ed983bd48fc2af0d7ffeb79f635624037ef2099809fd00c97aaa04cc0c'
PRIOR_ROM = '87d16a0fc513d7e8a491e0b5ac5929f7951e1e44e18b7f534f1e5e0cc794d4de'
SNAPSHOT = '09-minimal-independent-reboot'
OLD_FORMS = [1, 4, 7, 10, 19, 77, 79, 85]
FORMS = OLD_FORMS + [31, 34]
OLD_QUESTS = [11, 13, 21, 22, 23, 24]
QUESTS = OLD_QUESTS + [30, 31, 32]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def local(relative):
    p = Path(relative)
    require(not p.is_absolute() and '..' not in p.parts, 'Unsafe archive path')
    require(p != Path('.'), 'Empty archive path')
    return HERE / p


def checked(relative, expected):
    raw = local(relative).read_bytes()
    require(digest(raw) == expected, 'SHA-256 mismatch: ' + relative)
    return raw


def reconstruct(descriptor, expected):
    path = local(descriptor['manifest'])
    manifest = json.loads(checked(descriptor['manifest'], descriptor['manifest_sha256']))
    require(manifest['format'] == 'exact-byte-concatenation-v1', 'Wrong part format')
    require(manifest['max_part_bytes'] == 30000, 'Wrong part limit')
    require(manifest['original_sha256'] == descriptor['original_sha256'] == expected,
            'Wrong original report identity')
    pieces = []
    offset = 0
    for index, row in enumerate(manifest['parts']):
        require(row['file'] == f'part_{index:03d}.txt' and row['offset'] == offset,
                'Part order differs')
        raw = (path.parent / row['file']).read_bytes()
        raw.decode('utf-8')
        require(0 < len(raw) <= 30000 and len(raw) == row['bytes'], 'Part size differs')
        require(digest(raw) == row['sha256'], 'Part checksum differs')
        pieces.append(raw)
        offset += len(raw)
    raw = b''.join(pieces)
    require(len(raw) == manifest['original_bytes'] == descriptor['original_bytes'],
            'Reconstructed size differs')
    require(digest(raw) == expected and len(pieces) == descriptor['part_count'],
            'Reconstructed identity differs')
    return json.loads(raw)


def decode_banks(data, revision):
    require(len(data) == 32768, 'SRAM must be exactly 32 KiB')
    result = []
    for offset in (0x200, 0x1a00):
        b = data[offset:offset + 6144]
        require(b[:8] == bytes.fromhex('454205200018c013'), 'Wire header differs')
        require(b[12:16] == bytes((revision, 0, 0, 0)) and b[20] == 0xa5,
                'Content revision/commit differs')
        normalized = bytearray(b)
        normalized[16:20] = bytes(4)
        normalized[20] = 0
        require(binascii.crc32(normalized) == int.from_bytes(b[16:20], 'little'),
                'Bank CRC mismatch')
        for start, end in ((21, 32), (47, 96), (144, 160), (4005, 4008),
                           (4012, 4032), (4536, 4544), (5056, 6144)):
            require(not any(b[start:end]), 'Noncanonical reserved bytes')
        instances = []
        for i in range(160):
            record = b[160 + 24 * i:184 + 24 * i]
            if record[0]:
                require(record[1] & 1, 'Unowned populated instance')
                require(int.from_bytes(record[14:16], 'little') == 0,
                        'Optional personal trial unexpectedly present')
                instances.append({'instance_id': int.from_bytes(record[8:12], 'little'),
                                  'form_id': record[0], 'record_hex': record.hex()})
            else:
                require(not any(record), 'Nonempty unused instance slot')
        obtained = [i + 1 for i in range(128) if b[112 + i // 8] & (1 << (i % 8))]
        quests = [(b[4032 + i // 4] >> (2 * (i % 4))) & 3 for i in range(64)]
        objectives = [int.from_bytes(b[4048 + 2 * i:4050 + 2 * i], 'little')
                      for i in range(64)]
        items = [int.from_bytes(b[4544 + 8 * i:4546 + 8 * i], 'little')
                 for i in range(48)]
        equipped_slots = list(b[4928:4933])
        require(all(i == 255 or i < 48 for i in equipped_slots), 'Invalid gear reference')
        party = list(b[4000:4004])
        require(all(i < len(instances) for i in party) and len(set(party)) == 4,
                'Invalid party references')
        require(b[4004] < 4, 'Invalid selected party')
        result.append({
            'bank_offset': offset, 'sequence': int.from_bytes(b[8:12], 'little'),
            'content_revision': revision, 'crc32': f'{int.from_bytes(b[16:20], "little"):08x}',
            'room': b[32], 'spawn': b[33], 'chapter_flags': b[34],
            'campaign_hex': b[32:47].hex(), 'instances': instances,
            'owned_form_ids': [x['form_id'] for x in instances],
            'obtained_form_ids': obtained, 'quests': quests, 'objectives': objectives,
            'quest_rewards': list(b[4176:4184]), 'quest_variables': list(b[4184:4248]),
            'region_flags': list(b[4248:4280]), 'anchors': list(b[4280:4296]),
            'gear_item_ids': [i for i in items if i],
            'equipped_items': [items[i] if i < 48 else 0 for i in equipped_slots],
            'equipment_hex': b[4544:5056].hex(),
            'party_slots': party, 'selected_party': b[4004],
            'next_instance_id': int.from_bytes(b[4008:4012], 'little'),
        })
    require(abs(result[0]['sequence'] - result[1]['sequence']) == 1,
            'Expected consecutive authenticated bank sequences')
    return result


def check_semantics(bank, old=False):
    forms = OLD_FORMS if old else FORMS
    quests = OLD_QUESTS if old else QUESTS
    require(bank['owned_form_ids'] == forms, 'Retained base identities differ')
    require(bank['obtained_form_ids'] == sorted(forms), 'Earned histories differ')
    require([x['instance_id'] for x in bank['instances']] == list(range(1, len(forms) + 1)),
            'Stable owned identities differ')
    require(bank['next_instance_id'] == len(forms) + 1, 'Next identity differs')
    require(bank['quests'] == [3 if q in quests else 0 for q in range(64)],
            'Mandatory/optional quest state differs')
    require(all(not bank['objectives'][q] for q in range(64) if q not in quests),
            'Optional quest objectives present')
    require(bank['gear_item_ids'] == ([1, 4] if old else [1, 4, 20]), 'Gear differs')
    require(bank['equipped_items'] == [1, 0, 0, 0, 0], 'Starter-only equipment differs')
    require(bank['chapter_flags'] == 3, 'Unearned earlier endings present')
    campaign = bytes.fromhex(bank['campaign_hex'])
    require(campaign[5:8] == bytes(3), 'Optional relic/camp/flags unexpectedly present')
    require(bank['room'] == (30 if old else 38), 'Town differs')
    require(bank['spawn'] == (2 if old else 3), 'Town checkpoint differs')
    require(bank['party_slots'] == ([6, 7, 2, 3] if old else [8, 9, 2, 3]),
            'Authentic party differs')
    require(bank['selected_party'] == 1, 'Selected party differs')


def verify(runtime_root=None, original_run=None):
    p = json.loads((HERE / 'provenance.json').read_bytes())
    require(p['generated_test_fixture'] is True and p['player_save'] is False,
            'Wrong fixture scope')
    require(p['source_rom_sha256'] == ROM and p['source_symbols_sha256'] == SYMBOLS
            and p['source_elf_sha256'] == ELF, 'Wrong producer target')
    report = reconstruct(p['source_report'], REPORT)
    prior = reconstruct(p['ancestry']['report'], PRIOR_REPORT)
    manifest = reconstruct(p['source_manifest'], MANIFEST)
    require(len(manifest) == p['runtime_source_count'] == 893, 'Runtime source count differs')
    for r, count in ((report, 1837), (prior, 1889)):
        require(r['completed'] is True and r['controller_only'] is True, 'Run incomplete')
        require(r['game_ram_writes'] == r['machine_state_loads'] == 0, 'Synthetic game mutation')
        require(not r['failures'] and len(r['checks']) == count
                and all(c['passed'] is True for c in r['checks']), 'Controller checks failed')
    require(report['rom_sha256'] == ROM and report['symbols_sha256'] == SYMBOLS
            and report['elf_sha256'] == ELF and report['rom_bytes'] == 7495920,
            'Report target differs')
    require(report['source_manifest_sha256'] == MANIFEST, 'Wrong runtime manifest')
    require(report['synthetic_gameplay'] is False, 'Wrong gameplay scope')
    require(report['provenance']['sram_sha256'] == PRIOR_SRAM
            and report['provenance']['source_rom_sha256'] == prior['rom_sha256'] == PRIOR_ROM
            and report['provenance']['minimal_source_report_sha256'] == PRIOR_REPORT
            and report['provenance']['cross_rom_machine_state_loaded'] is False,
            'Prior-source authentication differs')
    require(p['ancestry']['snapshot'] == '05-minimal-independent-reboot'
            and prior['snapshots'][p['ancestry']['snapshot']]['sram_sha256'] == PRIOR_SRAM
            and prior['snapshots'][p['ancestry']['snapshot']]['owned_form_ids'] == OLD_FORMS
            and prior['snapshots'][p['ancestry']['snapshot']]['obtained_form_ids'] == OLD_FORMS,
            'Prior fixture/report pairing differs')
    require(report['cold_sram_imports'][0]['sha256'] == PRIOR_SRAM
            and report['cold_sram_imports'][1]['sha256'] == report['snapshots']['08-minimal-main-cleared']['sram_sha256']
            and len(report['cold_sram_imports']) == 2
            and all(x['machine_state_loaded'] is False for x in report['cold_sram_imports']),
            'Cold SRAM-only chain differs')
    require(report['main_route_selected_forms'] == [31, 34]
            and len(report['field_commands']) == 4
            and all((x['form_id'], x['instance_id']) in ((31, 9), (34, 10))
                    for x in report['field_commands']), 'Teaching-base field proof differs')
    require(p['source_snapshot'] == SNAPSHOT
            and p['source_state'] == report['snapshots'][SNAPSHOT], 'Endpoint differs')
    require(report['snapshots'][SNAPSHOT]['sram_sha256'] == p['sha256'] == SRAM,
            'Fixture/report pairing differs')
    require(report['snapshots']['10-minimal-old-region-return']['status']['room'] == 30
            and report['snapshots'][SNAPSHOT]['status']['room'] == 38,
            'Chosen snapshot must precede old-region return')
    raw = checked(p['fixture'], SRAM)
    old_raw = checked(p['ancestry']['fixture'], PRIOR_SRAM)
    banks = decode_banks(raw, 5)
    old_banks = decode_banks(old_raw, 4)
    for bank in banks:
        check_semantics(bank)
    for bank in old_banks:
        check_semantics(bank, old=True)
    require(raw[:512] == old_raw[:512], 'Legacy SRAM prefix changed')
    current = max(banks, key=lambda x: x['sequence'])
    old = max(old_banks, key=lambda x: x['sequence'])
    require(banks == p['wire_banks'] and old_banks == p['ancestry']['wire_banks'],
            'Wire capture differs')
    endpoint = report['state_records']['independent-reboot']
    require(current['instances'] == endpoint['individuals'], 'Raw retained records differ')
    require(current['quests'][:38] == endpoint['quests']
            and current['objectives'] == endpoint['objectives']
            and current['gear_item_ids'] == endpoint['gear']
            and current['equipped_items'] == endpoint['equipped'], 'Raw endpoint differs')
    prior_endpoint = prior['state_records']['independent-reboot']
    require(old['instances'] == [{k: x[k] for k in ('instance_id', 'form_id', 'record_hex')}
                                for x in prior_endpoint['individuals']], 'Prior records differ')
    require(old['instances'] == report['state_records']['before-new-teaching']['individuals'],
            'Prior eight were not retained exactly at import')
    require(current['quests'][:30] == old['quests'][:30]
            and current['objectives'][:30] == old['objectives'][:30]
            and current['quest_variables'][:30] == old['quest_variables'][:30],
            'Earlier quest progress changed')
    for q in range(30):
        require((current['quest_rewards'][q // 8] >> (q % 8)) & 1 ==
                (old['quest_rewards'][q // 8] >> (q % 8)) & 1, 'Earlier reward changed')
    for before, after in zip(old['instances'], current['instances'][:8]):
        b, a = bytes.fromhex(before['record_hex']), bytes.fromhex(after['record_hex'])
        require(a[:2] == b[:2] and a[8:] == b[8:], 'Earlier identity/seed/trial/commands changed')
        require(a[2] >= b[2] and a[3] >= b[3]
                and int.from_bytes(a[4:8], 'little') >= int.from_bytes(b[4:8], 'little'),
                'Earlier ordinary progression decreased')
    require(p['producer_test_sources'] == report['test_sources'], 'Re-pinned producer helpers')
    capture = json.loads(checked(p['source_capture']['path'], p['source_capture']['sha256']))
    require(capture['recorded_hashes_verified'] == report['test_sources'], 'Capture/report differs')
    for path, sha in report['test_sources'].items():
        checked('producer/test-source/' + path, sha)
    for path, sha in capture['runtime_wire_sources'].items():
        require(sha == manifest[path], 'Wire source not in original manifest')
        checked('producer/runtime-wire-source/' + path, sha)
    for path, desc in capture['supplemental_sources'].items():
        checked('producer/supplemental-source/' + path, desc['sha256'])
    receipts = json.loads(checked(p['verified_originals']['path'], p['verified_originals']['sha256']))
    require(len(receipts) == p['verified_originals']['count'] == 73
            and all(x['verified'] is True for x in receipts), 'Original verification receipt differs')
    receipt_map = {x['source_path']: x['sha256'] for x in receipts}
    for r in (report, prior):
        for snapshot in r['snapshots'].values():
            for kind in ('sram', 'state'):
                require(receipt_map[snapshot[kind + '_path']] == snapshot[kind + '_sha256'],
                        'Original snapshot pair not verified')
    ledger = json.loads((HERE / 'CHECKSUMS.json').read_bytes())
    files = {str(f.relative_to(HERE)) for f in HERE.rglob('*') if f.is_file()
             and '__pycache__' not in f.parts and f.name != 'CHECKSUMS.json'}
    require(set(ledger) == files, 'Archive file inventory differs')
    for path, sha in ledger.items():
        data = checked(path, sha)
        if not path.endswith(('.sav', '.bin')):
            data.decode('utf-8')
            require(len(data) < 90000, 'Text file exceeds 90KB limit')
    if runtime_root:
        for path, sha in manifest.items():
            require(digest((runtime_root / path).read_bytes()) == sha, 'Runtime differs: ' + path)
    if original_run:
        for filename, sha in (('magma-minimal-route.json', REPORT), ('tested.gba', ROM),
                              ('tested.elf', ELF), ('tested.sym', SYMBOLS),
                              ('candidate-source-hashes.json', MANIFEST)):
            require(digest((original_run / filename).read_bytes()) == sha,
                    'Original producer artifact differs: ' + filename)
        for name, snapshot in report['snapshots'].items():
            for kind, suffix in (('sram', '.sav'), ('state', '.state')):
                require(digest((original_run / (name + suffix)).read_bytes()) == snapshot[kind + '_sha256'],
                        'Original snapshot pair differs: ' + name)
    return {'passed': True, 'fixture_sha256': SRAM, 'source_rom_sha256': ROM,
            'owned_individuals': len(current['instances']), 'earned_histories': len(current['obtained_form_ids']),
            'claimed_quests': current['quests'].count(3), 'gear_item_ids': current['gear_item_ids'],
            'room': current['room'], 'spawn': current['spawn'], 'chapter_flags': current['chapter_flags'],
            'banks_verified': len(banks), 'ancestry_banks_verified': len(old_banks),
            'passing_original_controller_checks': len(report['checks']),
            'exact_report_parts': p['source_report']['part_count'],
            'ancestry_report_parts': p['ancestry']['report']['part_count'],
            'runtime_manifest_entries': len(manifest), 'checksum_files_verified': len(ledger),
            'original_run_reverified': bool(original_run), 'runtime_root_reverified': bool(runtime_root),
            'historical_unpinned_supplemental_sources': len(capture['supplemental_sources']),
            'machine_states_loaded_by_verifier': 0, 'game_ram_writes_by_verifier': 0,
            'fixture_bytes_changed': False, 'new_acquisition_run': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, help='Optional exact Magma D source root, never Underwater')
    parser.add_argument('--original-run', type=Path, help='Optional immutable original minimal run directory')
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.runtime_root, args.original_run), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('Fixture verification FAILED: ' + str(exc), file=sys.stderr)
        sys.exit(1)
