"""Transient combat evidence must not idle through attacks or claim a checkpoint."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from campaign_tests import CampaignRun
from journey_guidance_earned import Evidence


class BossObservationTests(unittest.TestCase):
    def test_legacy_capture_keeps_snapshot_contract(self):
        names = []
        run = SimpleNamespace(snapshot=lambda name: names.append(name) or Path('/tmp/checkpoint.state'))
        result = CampaignRun.boss_observation(run, 'boss-phase')
        self.assertEqual(names, ['boss-phase'])
        self.assertEqual(result, Path('/tmp/checkpoint.state'))

    def test_native_boss_capture_uses_live_observation(self):
        names = []
        run = SimpleNamespace(live_observation=names.append)
        Evidence.boss_observation(run, 'boss-phase')
        self.assertEqual(names, ['boss-phase'])

    def test_capture_does_not_advance_frames_or_export_a_save(self):
        screenshots = []
        emulator = SimpleNamespace(frame=42, screenshot=screenshots.append)
        status = {'boss_state': 5, 'hp': 4}
        run = SimpleNamespace(e=emulator, out=Path('/tmp'), observations={},
                              proof_state=lambda: {'status': dict(status), 'owned_forms': [13]})
        Evidence.live_observation(run, 'boss-8-phase-0-state-5')
        self.assertEqual(emulator.frame, 42)
        self.assertEqual(screenshots, [Path('/tmp/boss-8-phase-0-state-5.png')])
        row = run.observations['boss-8-phase-0-state-5']
        self.assertEqual(row['status'], status)
        self.assertEqual(row['frame'], 42)
        self.assertEqual(row['owned_forms'], [13])
        self.assertNotIn('sram_path', row)
        self.assertIn('not a durable save checkpoint', row['provenance'])


if __name__ == '__main__':
    unittest.main()
