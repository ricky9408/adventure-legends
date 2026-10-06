#!/usr/bin/env python3
"""Authenticate delivered S3 SRAM and exact, chunked producer reports.

Read-only host checks: no emulator, current catalog, synthesized progress, SRAM
mutation, or machine-state load. These are prior-ROM migration inputs, not
evidence that a later ROM awards or preserves progress correctly.
"""
from __future__ import annotations

import binascii
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/v5-revision4'
ROM_SHA256 = '87d16a0fc513d7e8a491e0b5ac5929f7951e1e44e18b7f534f1e5e0cc794d4de'
SYMBOLS_SHA256 = 'ceedba1a6052fe450f17c91375eef6ddd5200d1a7bb01394c1eb95d2bc4f1305'
SOURCE_MANIFEST_SHA256 = '609104f75fa341bb67d0d1e2a362db7b03ed655ecb6eed41c101b0c799b2f089'
PINS = {
    'all41': {
        'provenance': 'provenance.json',
        'fixture': 'southern-all41-town.sav',
        'fixture_sha256': '0bd83c19eb0dee81b3cd9e2b48462f6362b559786e38fa119312fe05787b0bd3',
        'report_sha256': '780317f27cb2595ece2741a33edc085aa6646e0ab2687e98f2a62689056fd635',
        'report_bytes': 3112391,
        'suite': 'southern-native-controller-journey',
        'snapshot': '08-complete41-independent-reboot',
        'checks': 15732,
        'inputs': 18283,
        'parts': 104,
        'counts': (41, 21, 25, 30),
        'chapter_flags': 15,
    },
    'minimal8': {
        'provenance': 'southern-minimal8-town.provenance.json',
        'fixture': 'southern-minimal8-town.sav',
        'fixture_sha256': '968066ed983bd48fc2af0d7ffeb79f635624037ef2099809fd00c97aaa04cc0c',
        'report_sha256': 'b028d1aa5020b53fa9b17eed863921d39d66c6bff0e93c93b464546452045b09',
        'report_bytes': 569857,
        'suite': 'southern-minimal-native-controller-route',
        'snapshot': '05-minimal-independent-reboot',
        'checks': 1889,
        'inputs': 2116,
        'parts': 20,
        'counts': (8, 8, 2, 6),
        'chapter_flags': 3,
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_frozen_report(name: str) -> dict:
    """Reconstruct and authenticate one report without following source paths."""
    pin = PINS[name]
    provenance = json.loads((FIXTURES / pin['provenance']).read_bytes())
    manifest_path = FIXTURES / provenance['source_report_manifest']
    manifest_bytes = manifest_path.read_bytes()
    if digest(manifest_bytes) != provenance['source_report_manifest_sha256']:
        raise ValueError('Frozen report manifest hash differs')
    manifest = json.loads(manifest_bytes)
    if (manifest['format'] != 'exact-byte-concatenation-v1'
            or manifest['original_sha256'] != pin['report_sha256']
            or manifest['original_bytes'] != pin['report_bytes']
            or manifest['max_part_bytes'] != 30000
            or len(manifest['parts']) != pin['parts']):
        raise ValueError('Frozen report original identity differs')
    chunks = []
    offset = 0
    for index, part in enumerate(manifest['parts']):
        if part['file'] != f'part_{index:03}.txt' or part['offset'] != offset:
            raise ValueError('Frozen report part order differs')
        chunk = (manifest_path.parent / part['file']).read_bytes()
        if (not 0 < len(chunk) <= 30000 or len(chunk) != part['bytes']
                or digest(chunk) != part['sha256']):
            raise ValueError('Frozen report part bytes differ')
        chunk.decode('utf-8')
        chunks.append(chunk)
        offset += len(chunk)
    raw = b''.join(chunks)
    if len(raw) != pin['report_bytes'] or digest(raw) != pin['report_sha256']:
        raise ValueError('Reconstructed report differs from the delivered original')
    return json.loads(raw)


def wire_state(bank: bytes, offset: int) -> dict:
    """Decode only stable v5 wire fields, independently of the current sources."""
    obtained = [i + 1 for i in range(128) if bank[112 + i // 8] & (1 << (i % 8))]
    owned = [bank[160 + 24 * i] for i in range(160) if bank[160 + 24 * i]]
    items = [int.from_bytes(bank[4544 + 8 * i:4546 + 8 * i], 'little')
             for i in range(48)]
    items = [item for item in items if item]
    quests = [(bank[4032 + i // 4] >> (2 * (i % 4))) & 3 for i in range(64)]
    return {
        'bank_offset': offset,
        'sequence': int.from_bytes(bank[8:12], 'little'),
        'content_revision': int.from_bytes(bank[12:14], 'little'),
        'obtained_form_count': len(obtained),
        'owned_instance_count': len(owned),
        'gear_item_count': len(items),
        'claimed_quest_count': quests.count(3),
        'obtained_form_ids': obtained,
        'owned_form_ids': owned,
        'gear_item_ids': items,
        'quests': quests,
        'room': bank[32],
        'spawn': bank[33],
        'chapter_flags': bank[34],
        'party_slots': list(bank[4000:4004]),
        'selected_party': bank[4004],
        'next_instance_id': int.from_bytes(bank[4008:4012], 'little'),
    }


class SouthernFrozenFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provenance = {name: json.loads((FIXTURES / pin['provenance']).read_bytes())
                          for name, pin in PINS.items()}
        cls.reports = {name: read_frozen_report(name) for name in PINS}

    def test_exact_reports_pin_released_target_and_successful_controller_evidence(self):
        for name, pin in PINS.items():
            with self.subTest(fixture=name):
                report, provenance = self.reports[name], self.provenance[name]
                self.assertEqual(provenance['source_report_sha256'], pin['report_sha256'])
                self.assertEqual(provenance['source_report_bytes'], pin['report_bytes'])
                self.assertEqual(report['suite'], pin['suite'])
                self.assertEqual(report['rom_sha256'], ROM_SHA256)
                self.assertEqual(report['symbols_sha256'], SYMBOLS_SHA256)
                self.assertEqual(report['rom_bytes'], 5858700)
                self.assertEqual(provenance['source_rom_sha256'], ROM_SHA256)
                self.assertEqual(provenance['source_symbols_sha256'], SYMBOLS_SHA256)
                self.assertIs(report['controller_only'], True)
                self.assertEqual(report['game_ram_writes'], 0)
                self.assertIs(report['provenance']['source_machine_state_loaded'], False)
                self.assertEqual(report['failures'], [])
                self.assertEqual(len(report['checks']), pin['checks'])
                self.assertTrue(all(check['passed'] is True for check in report['checks']))
                self.assertEqual(len(report['inputs']), pin['inputs'])

    def test_source_manifest_and_archived_producer_tests_match_report_pins(self):
        source_bytes = (FIXTURES / 'source-hashes.json').read_bytes()
        self.assertEqual(digest(source_bytes), SOURCE_MANIFEST_SHA256)
        source_manifest = json.loads(source_bytes)
        self.assertEqual(len(source_manifest), 707)
        for name, report in self.reports.items():
            with self.subTest(fixture=name):
                provenance = self.provenance[name]
                self.assertEqual(report['source_manifest_sha256'], SOURCE_MANIFEST_SHA256)
                self.assertEqual(set(report['frozen_source_checks']), set(source_manifest))
                self.assertTrue(all(value is True for value in report['frozen_source_checks'].values()))
                self.assertEqual(provenance['source_tests'], report['test_sources'])
                for path, expected in report['test_sources'].items():
                    archived = (ROOT / path if path.startswith('tests/fixtures/')
                                else FIXTURES / 'producer-test-source' / path)
                    self.assertEqual(digest(archived.read_bytes()), expected, path)

    def test_fixtures_and_snapshot_metadata_are_pinned_to_original_report(self):
        for name, pin in PINS.items():
            with self.subTest(fixture=name):
                provenance, report = self.provenance[name], self.reports[name]
                data = (FIXTURES / pin['fixture']).read_bytes()
                self.assertEqual(len(data), 32768)
                self.assertEqual(digest(data), pin['fixture_sha256'])
                self.assertEqual(provenance['fixture'], pin['fixture'])
                self.assertEqual(provenance['sha256'], pin['fixture_sha256'])
                self.assertEqual(provenance['source_snapshot'], pin['snapshot'])
                source = report['snapshots'][pin['snapshot']]
                self.assertEqual(provenance['source_state'], source)
                self.assertEqual(source['sram_sha256'], pin['fixture_sha256'])
                self.assertEqual(source['rom_sha256'], ROM_SHA256)
                self.assertEqual(source['symbols_sha256'], SYMBOLS_SHA256)

    def test_both_revision4_banks_have_valid_crc_and_exact_earned_counts(self):
        for name, pin in PINS.items():
            data = (FIXTURES / pin['fixture']).read_bytes()
            states = []
            for offset in (0x200, 0x1A00):
                with self.subTest(fixture=name, bank=hex(offset)):
                    bank = data[offset:offset + 6144]
                    self.assertEqual(bank[:8], bytes.fromhex('454205200018c013'))
                    self.assertEqual(bank[12:16], bytes((4, 0, 0, 0)))
                    self.assertEqual(bank[20], 0xA5)
                    normalized = bytearray(bank)
                    normalized[16:20] = bytes(4)
                    normalized[20] = 0
                    self.assertEqual(int.from_bytes(bank[16:20], 'little'),
                                     binascii.crc32(normalized))
                    decoded = wire_state(bank, offset)
                    states.append(decoded)
                    self.assertEqual(tuple(decoded[field] for field in (
                        'obtained_form_count', 'owned_instance_count',
                        'gear_item_count', 'claimed_quest_count')), pin['counts'])
                    self.assertEqual(decoded['room'], 30)
                    self.assertEqual(decoded['chapter_flags'], pin['chapter_flags'])
            current = max(states, key=lambda state: state['sequence'])
            self.assertEqual(current, self.provenance[name]['wire_state'])
            source = self.reports[name]['snapshots'][pin['snapshot']]
            for field in ('owned_form_ids', 'obtained_form_ids'):
                self.assertEqual(current[field], source[field])
            self.assertEqual(current['quests'][:30], source['quests'])
            self.assertEqual(current['quests'][30:], [0] * 34)

    def test_minimal_route_has_no_optional_recruits_evolutions_or_quests(self):
        report = self.reports['minimal8']
        state = self.provenance['minimal8']['wire_state']
        self.assertIs(report['completed'], True)
        self.assertEqual(report['machine_state_loads'], 0)
        self.assertEqual(state['obtained_form_ids'], [1, 4, 7, 10, 19, 77, 79, 85])
        self.assertEqual(state['owned_form_ids'], state['obtained_form_ids'])
        self.assertEqual(state['gear_item_ids'], [1, 4])
        self.assertEqual([i for i, value in enumerate(state['quests']) if value],
                         [11, 13, 21, 22, 23, 24])
        self.assertEqual(len(report['acquisitions']), 2)
        observed = report['state_records']['independent-reboot']
        self.assertEqual(state['owned_instance_count'], len(observed['individuals']))
        self.assertEqual(state['gear_item_ids'], observed['gear_item_ids'])
        self.assertTrue(all(instance['trial_flags'] == 0 for instance in observed['individuals']))

    def test_original_source_artifacts_still_match_when_available(self):
        """Portable archives remain sufficient when the original checkout is absent."""
        for name, pin in PINS.items():
            report, provenance = self.reports[name], self.provenance[name]
            candidates = {
                report['rom_path']: ROM_SHA256,
                report['symbols_path']: SYMBOLS_SHA256,
                str(Path(provenance['source_directory']) /
                    provenance['source_report_original_filename']): pin['report_sha256'],
            }
            for source in report['snapshots'].values():
                for kind in ('sram', 'state'):
                    candidates[source[kind + '_path']] = source[kind + '_sha256']
            for path, expected in candidates.items():
                original = Path(path)
                if original.is_file():
                    self.assertEqual(digest(original.read_bytes()), expected, path)


if __name__ == '__main__':
    unittest.main()
