import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .env lives at the repo root, one level above python/. absolute so it works from any cwd.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# vercel's filesystem is read-only except /tmp, and /tmp is wiped between invocations
_default = "/tmp/runs" if os.environ.get("VERCEL") else str(Path(__file__).resolve().parent.parent / "runs")
RUNS_DIR = Path(os.environ.get("RUNS_DIR", _default))

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit(
        "no ANTHROPIC_API_KEY.\n"
        "paste the shared key into .env at the repo root, then run this again.\n"
        "  scripts/check.sh python    tells you what else is missing"
    )
