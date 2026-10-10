#!/usr/bin/env python3
"""Explicit A-only controller workaround diagnostic; never acceptance.

The initial implementation can apply one106 cast twice to a moving room66 glyph.
This diagnostic uses a closer normal player approach so the moved glyph is
behind the cast and cannot be hit by its returning beat. The production bug
must still be fixed; strict acceptance retains the original approach.
"""
import argparse
import json
import sys
from pathlib import Path
import horizons_journey as journey
DIAGNOSTIC_PRODUCER = None

class Diagnostic(journey.HorizonsJourney):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        assert self.target_sha=='a0a1de68d3b9201087870f2a5e781a6ef3e92701f9d5787bc672d62ef5d1bf2e'
        assert self.timing_mode=='collect-diagnostic'
        self.coverage.append('A-only documented room66 closer-approach workaround; excluded from acceptance')
    def cast_at(self,form,command,x,y,direction,wait=110,prepare=True):
        if self.get('room')==66 and command==106 and (x,y,direction)==(176,248,2):
            self.cases.append({'diagnostic_workaround':'A double-application bug','ordinary_requested_origin_before':[x,y],'ordinary_requested_origin_after':[160,y]})
            x=160
        return super().cast_at(form,command,x,y,direction,wait,prepare)
    def run(self,scope,arm_order):
        if DIAGNOSTIC_PRODUCER is None:return super().run(scope,arm_order)
        assert scope=='repeats'
        report=Path(DIAGNOSTIC_PRODUCER).resolve()
        assert journey.digest(report)=='ae6f30d1068a4a5157497801a9ef5735d27431677e6b87edf5ee83dd4b8ad515'
        data=json.loads(report.read_text());snapshot=data['snapshots']['07-all120-cold-reboot-after']
        assert data['controller_only'] and not data['game_ram_writes'] and not data['machine_state_loads']
        assert data['rom_sha256']==self.target_sha and data['symbols_sha256']==self.symbol_sha
        assert data['elf_sha256']==self.candidate['elf_sha256'] and data['source_manifest_sha256']==self.source_manifest_sha
        assert data['finished_scope']=='full' and data['timing_mode']=='collect-diagnostic' and len(data['global_native']['exceptions'])==5
        self.fixture=Path(snapshot['sram_path'])
        assert journey.digest(self.fixture)==snapshot['sram_sha256']=='d0786e3db82cd23c5f9ba948900f3d73340de8df004738d26ad1c2956055994e'
        self.provenance.update(diagnostic_resume_report=str(report),diagnostic_resume_sha256=journey.digest(report),
            diagnostic_source_cadence_exceptions=5,source_rom_sha256=self.target_sha,sram_sha256=snapshot['sram_sha256'],
            fixture_path=str(self.fixture),source_snapshot='07-all120-cold-reboot-after',source_individuals=64,source_history=120)
        self.source_bytes=self.fixture.read_bytes();self.source_bank=journey.newest_bank(self.source_bytes)
        self.same_candidate_source=True;self.prior_count=64;self.prior_history=120
        self.e.close();self.e=journey.HorizonsEmulator(self.rom);self.e.load_save(self.fixture);self.e.reset()
        self.boot();self.controls();self.repeat_route()
        self.finished_scope='A-diagnostic-controls-and-repeats';self.verify_closures();self.report()

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--diagnostic-producer-report')
    extra,rest=parser.parse_known_args();DIAGNOSTIC_PRODUCER=extra.diagnostic_producer_report;sys.argv=[sys.argv[0],*rest]
    journey.HorizonsJourney=Diagnostic
    raise SystemExit(journey.main())
