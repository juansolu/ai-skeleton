# ai-workshop-skeleton

Agentic loop teaching repo. Same skeleton twice: `python/` and `ts/`. Pick one. Three levels, one loop.

Layout (per language):
- `loop` (`python/agent/loop.py`, `ts/src/loop.ts`) is 101. The loop. Read it first.
- `tools` is what the agent can do. Add tools here, or `/add-tool`.
- `system.md` and `criteria.md` are the prompt and the rubric. Plain text on purpose: edit, rerun, compare traces.
- `validate` is 201. A second agent judges the first against `criteria.md`, bounded retry with feedback.
- `app.py` / `api/*.ts` plus `vercel.json` are 201's trigger layer: webhook and cron. Deploy with `scripts/deploy.sh python|ts`.
- `improve` is 301. Reads `runs/*.json`, proposes prompt, criteria, and tool edits. Human applies them.
- `runs/` holds every trace. That is the state layer. Gitignored.
- `scripts/check.sh python|ts` is the preflight: key, deps, live auth check. Point people there before debugging a setup by hand. `/start` walks a beginner from a fresh clone to a first run.

Rules:
- Never read, print, or commit `.env`. The key in it is shared with 100 people and gets revoked tonight.
- After changing agent code, run the offline test: `python tests/test_loop.py` (in `python/`) or `npm test` (in `ts/`). No API key needed.
- Prefer editing `system.md` / `criteria.md` over adding code. Prompt first, code second.
- Do not add frameworks. The loop is 40 lines because the loop is the lesson.
