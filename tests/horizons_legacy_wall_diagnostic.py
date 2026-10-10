#!/usr/bin/env python3
"""Cross-candidate SRAM-only diagnostics for legacy-wall performance.

The acquired120 source is genuine but has five documented cadence failures.
This observer never relabels it as accepted and cannot produce collection
acceptance. The caller must pin the complete target candidate explicitly.
"""
import argparse
import json
import sys
from pathlib import Path
import horizons_journey as journey
SOURCE_REPORT=None

class LegacyWallDiagnostic(journey.HorizonsJourney):
    def run(self,scope,arm_order):
        assert self.timing_mode=='collect-diagnostic' and SOURCE_REPORT
        report=Path(SOURCE_REPORT).resolve()
        assert journey.digest(report)=='ae6f30d1068a4a5157497801a9ef5735d27431677e6b87edf5ee83dd4b8ad515'
        data=json.loads(report.read_text());snapshot=data['snapshots']['07-all120-cold-reboot-after']
        assert data['controller_only'] and not data['game_ram_writes'] and not data['machine_state_loads']
        assert data['finished_scope']=='full' and len(data['global_native']['exceptions'])==5
        self.fixture=Path(snapshot['sram_path'])
        if not self.fixture.is_file():self.fixture=report.parent/self.fixture.name
        assert journey.digest(self.fixture)==snapshot['sram_sha256']=='d0786e3db82cd23c5f9ba948900f3d73340de8df004738d26ad1c2956055994e'
        self.provenance.update(diagnostic_resume_report=str(report),diagnostic_resume_sha256=journey.digest(report),
            diagnostic_source_cadence_exceptions=5,source_rom_sha256=data['rom_sha256'],sram_sha256=snapshot['sram_sha256'],
            fixture_path=str(self.fixture),source_snapshot='07-all120-cold-reboot-after',source_individuals=64,source_history=120,
            cross_rom_sram_diagnostic=self.target_sha!=data['rom_sha256'],source_acceptance_eligible=False)
        self.source_bytes=self.fixture.read_bytes();self.source_bank=journey.newest_bank(self.source_bytes)
        self.same_candidate_source=True;self.prior_count=64;self.prior_history=120
        self.e.close();self.e=journey.HorizonsEmulator(self.rom);self.e.load_save(self.fixture);self.e.reset()
        self.boot();self.old_wall_stress()
        self.finished_scope='diagnostic-legacy-walls-only';self.verify_closures();self.report()

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--diagnostic-producer-report',required=True)
    extra,rest=parser.parse_known_args();SOURCE_REPORT=extra.diagnostic_producer_report;sys.argv=[sys.argv[0],*rest]
    journey.HorizonsJourney=LegacyWallDiagnostic
    raise SystemExit(journey.main())
