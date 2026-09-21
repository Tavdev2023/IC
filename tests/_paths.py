"""Makes the ``sensor_monitor`` package importable without setting PYTHONPATH."""

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src" / "python"))
