#!/usr/bin/env bash
# usage: scripts/check.sh python|ts
# says whether you are ready to run the loop, instead of letting you find out from a stack trace.
set -uo pipefail
cd "$(dirname "$0")/.."
lang="${1:-}"
case "$lang" in
  python|ts) ;;
  *) echo "usage: scripts/check.sh python|ts"; exit 1 ;;
esac

fail=0
ok()  { printf '  ok   %s\n' "$1"; }
bad() { printf '  FIX  %s\n' "$1"; fail=1; }

echo "checking $lang"

if [ -f .env ]; then
  ok ".env exists"
  set -a; source .env; set +a
  src=".env"
else
  src="your shell"
fi

key="${ANTHROPIC_API_KEY:-}"
if [ -z "$key" ]; then
  bad "no ANTHROPIC_API_KEY.  run: cp .env.example .env   then paste the shared key into it"
elif [ "${#key}" -lt 20 ]; then
  bad "ANTHROPIC_API_KEY looks like the placeholder (${#key} chars).  paste the real one into .env"
else
  ok "ANTHROPIC_API_KEY set (${#key} chars, from $src)"
fi

py=python/.venv/bin/python
if [ "$lang" = python ]; then
  if [ -x "$py" ]; then ok "venv exists"; else bad "no venv.  run: python/setup.sh"; fi
  if [ -x "$py" ] && "$py" -c 'import anthropic, flask, dotenv' 2>/dev/null; then
    ok "deps installed"
  else
    bad "deps missing.  run: python/setup.sh"
  fi
else
  if [ -d ts/node_modules ]; then ok "deps installed"; else bad "no node_modules.  run: cd ts && npm install"; fi
fi

# the key can be present and still be revoked, mistyped, or from the wrong org. models.list is free.
if [ "$fail" = 0 ]; then
  if [ "$lang" = python ]; then
    probe="$("$py" -c 'import anthropic; anthropic.Anthropic().models.list(limit=1); print("ok")' 2>&1 | tail -1)"
  else
    probe="$(cd ts && node -e '
      import("@anthropic-ai/sdk")
        .then((m) => new m.default().models.list({ limit: 1 }))
        .then(() => console.log("ok"))
        .catch((e) => console.log(String(e.message || e).slice(0, 160)));
    ' 2>&1 | tail -1)"
  fi
  if [ "$probe" = ok ]; then ok "key works"; else bad "key rejected: $probe"; fi
fi

echo
if [ "$fail" != 0 ]; then
  echo "not ready. fix the FIX lines above, then run this again."
  exit 1
fi

if [ "$lang" = python ]; then
  cat <<'MSG'
ready. next:
  cd python && source .venv/bin/activate
  python -m agent.loop "What time is it? Remember it under last_run."
  python -m agent.loop "When did we last run?"
MSG
else
  cat <<'MSG'
ready. next:
  cd ts
  npm run loop -- "What time is it? Remember it under last_run."
  npm run loop -- "When did we last run?"
MSG
fi
echo
echo "then open the newest file in $lang/runs/ and read it. that file is the whole story."
