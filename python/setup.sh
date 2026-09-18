#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
[ -f ../.env ] || cp ../.env.example ../.env

cat <<MSG

done. next:
  1. put the shared key in ../.env   (ANTHROPIC_API_KEY=...)
  2. source .venv/bin/activate
  3. python -m agent.loop "What time is it? Remember it under last_run."
MSG
