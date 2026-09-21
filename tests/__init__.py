"""Test package.

Puts this directory on ``sys.path`` so that ``import _paths`` also works when the
tests are loaded as ``tests.test_*`` (``python -m unittest``, ``discover -t .``).
With ``discover -s tests`` unittest already does this itself.
"""

import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)
