#!/usr/bin/env python3
"""Focused controller controls probe from a passing same-candidate full producer.
This intentionally excludes the separate legacy-wall and twelve-repeat routes.
"""
import horizons_journey as journey
class ControlsProbe(journey.HorizonsJourney):
    def old_wall_stress(self):
        self.coverage.append('focused controls scope excludes separate legacy-wall matrix')
    def run(self,scope,arm_order):
        assert self.same_candidate_source and self.timing_mode=='strict'
        self.boot();self.controls();self.finished_scope='focused-controls-only'
        self.verify_closures();self.report()
if __name__=='__main__':
    journey.HorizonsJourney=ControlsProbe
    raise SystemExit(journey.main())
