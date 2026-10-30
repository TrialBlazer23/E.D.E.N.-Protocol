"""E.D.E.N. verify step for this repo: runs the stdlib unittest suite in tests/."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.exit(subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=ROOT))
