import os
from pathlib import Path

# vercel's filesystem is read-only except /tmp, and /tmp is wiped between invocations
_default = "/tmp/runs" if os.environ.get("VERCEL") else str(Path(__file__).resolve().parent.parent / "runs")
RUNS_DIR = Path(os.environ.get("RUNS_DIR", _default))
