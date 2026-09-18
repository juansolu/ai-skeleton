#!/usr/bin/env bash
# usage: scripts/trigger.sh python|ts https://ws-you-python.vercel.app "task text"
# hits the deployed webhook and saves the returned trace into <lang>/runs/ so improve can read it.
set -euo pipefail
cd "$(dirname "$0")/.."
lang="${1:?usage: scripts/trigger.sh python|ts <url> <task>}"; shift
url="${1:?deployment url}"; shift
task="${*:?task}"
set -a; source .env; set +a
: "${WEBHOOK_SECRET:?set WEBHOOK_SECRET in .env}"

path="/run"; [ "$lang" = "ts" ] && path="/api/run"
out="$lang/runs/$(date +%Y%m%d-%H%M%S)-remote.json"
body="$(python3 -c 'import json,sys; print(json.dumps({"task": sys.argv[1]}))' "$task")"

curl -sS -X POST "$url$path" \
  -H "Authorization: Bearer $WEBHOOK_SECRET" \
  -H 'Content-Type: application/json' \
  -d "$body" -o "$out"

python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); print(t.get("output") or t); print("\nverdict:", t.get("verdict"))' "$out"
echo "saved $out"
