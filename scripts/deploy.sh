#!/usr/bin/env bash
# usage: scripts/deploy.sh python|ts
# links the language folder to its own vercel project and deploys it, passing .env as runtime env.
set -euo pipefail
cd "$(dirname "$0")/.."
lang="${1:?usage: scripts/deploy.sh python|ts}"
[ -d "$lang" ] || { echo "no such folder: $lang"; exit 1; }
set -a; source .env; set +a

: "${VERCEL_TOKEN:?set VERCEL_TOKEN in .env}"
: "${VERCEL_TEAM:?set VERCEL_TEAM in .env}"
: "${ANTHROPIC_API_KEY:?set ANTHROPIC_API_KEY in .env}"
: "${WEBHOOK_SECRET:?set WEBHOOK_SECRET in .env}"
: "${CRON_SECRET:?set CRON_SECRET in .env}"
project="${VERCEL_PROJECT:-ws-${USER}-${lang}}"

vercel link --yes --cwd "$lang" --project "$project" --scope "$VERCEL_TEAM" --token "$VERCEL_TOKEN"
vercel deploy --prod --yes --cwd "$lang" --scope "$VERCEL_TEAM" --token "$VERCEL_TOKEN" \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e MODEL="${MODEL:-claude-opus-5}" \
  -e WEBHOOK_SECRET="$WEBHOOK_SECRET" \
  -e CRON_SECRET="$CRON_SECRET"
