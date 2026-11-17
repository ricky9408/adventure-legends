from pathlib import Path
from trust.contracts import input_snapshot, snapshot_delta

ROOT=Path(__file__).resolve().parents[1]


class ProductionGuard:
    def __init__(self):
        self.before=input_snapshot(ROOT)

    def error(self):
        try:
            delta=snapshot_delta(self.before,input_snapshot(ROOT))
            return delta if any(delta.values()) else None
        except (OSError,ValueError) as failure:
            return {'error':str(failure)}
