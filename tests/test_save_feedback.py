#!/usr/bin/env python3
"""Current contract; the prior control/scheduler test remains in fixtures."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('test_player_feedback_engine.py')),run_name='__main__')
