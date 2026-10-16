"""Fail closed on producer changes to the exact current reviewed input set.

Used only by the active current host aggregates. Historical reconstructed
helpers retain their original source and contracts.
"""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import field_controls_boundary as boundary


class ProductionGuard:
    def __init__(self):
        self.contract=boundary.load()
        boundary.authenticate(self.contract,boundary.state(self.contract))

    def error(self):
        """Return the exact fail-closed delta for the just-completed producer."""
        try:
            boundary.authenticate(self.contract,boundary.state(self.contract))
        except (AssertionError,OSError,ValueError) as failure:
            detail=failure.args[0] if failure.args else str(failure)
            return detail if isinstance(detail,dict) else {'error':str(detail)}
        return None
