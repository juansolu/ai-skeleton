# ai-workshop-skeleton

One agentic loop, three levels, two languages. Clone it, drop in the shared key, run the loop, then make it yours.

Everything you need is provided. You do not need to sign up for anything. The Anthropic key and the Vercel token get handed out in the room and revoked at the end of the day.

## Setup (5 minutes)

1. Clone it and pick a language. `python/` and `ts/` are the same skeleton twice. Pick the one you think in.

        git clone <url> && cd ai-workshop-skeleton

2. Install.

        python/setup.sh              # venv + deps, copies .env.example to .env
        cd ts && npm install         # ts folks

3. Paste the shared `ANTHROPIC_API_KEY` into `.env` at the repo root. It gets revoked tonight, so don't build anything that needs it tomorrow.

4. Check you are ready before you burn a call finding out.

        scripts/check.sh python      # or ts

   It tells you what is missing and prints the next command. Every `FIX` line is a thing to fix now.

5. Run the loop twice.

        cd python && source .venv/bin/activate
        python -m agent.loop "What time is it? Remember it under last_run."
        python -m agent.loop "When did we last run?"

        cd ts
        npm run loop -- "What time is it? Remember it under last_run."
        npm run loop -- "When did we last run?"

   Second run uses `recall`. That is state. Open `runs/<id>.json` and read what happened. That file is the whole story.

If you use Claude Code, open the repo and it already knows the layout (`CLAUDE.md`, `.claude/`). `/start` walks you from here to a running agent on a project you pick. `/add-tool <what it does>` adds a tool. The `reviewer` agent judges your last run.

## The levels

| Level | Idea | Python | TS | Run |
|---|---|---|---|---|
| 101 | Execution. A system prompt, tools, a loop that runs until the model stops calling tools. | `agent/loop.py`, `agent/tools.py`, `agent/system.md` | `src/loop.ts`, `src/tools.ts`, `src/system.md` | `python -m agent.loop "task"` / `npm run loop -- "task"` |
| 201 | Validation and trigger. A second agent judges the first against written criteria and sends it back with feedback, bounded. Then move the trigger off your laptop: webhook and cron on Vercel. | `agent/validate.py`, `agent/criteria.md`, `app.py` | `src/validate.ts`, `src/criteria.md`, `api/*.ts` | `python -m agent.validate "task"` / `npm run validate -- "task"`, then `scripts/deploy.sh python|ts` |
| 301 | State. Every run leaves a trace in `runs/`. An improvement agent reads the traces and proposes edits to the prompt, criteria, or tools. You apply them. | `agent/improve.py` | `src/improve.ts` | `python -m agent.improve` / `npm run improve` |

### 101: make it yours

Pick a task with a non-deterministic shape: the model has to look something up, decide, maybe look again. Swap the sample tools for tools that touch your problem (an internal API, a file format, a database read). Rewrite `system.md`. Run it ten times. Read the traces. Notice what it got wrong and why.

### 201: stop babysitting it

`validate` runs the loop, then a reviewer. Rejected runs go back with the reviewer's feedback, up to three attempts. Tune `criteria.md` until the reviewer rejects the things you would reject. Be specific enough that a stranger could grade with it.

Then deploy. Put the shared `VERCEL_TOKEN` and `VERCEL_TEAM` in `.env`, pick a `WEBHOOK_SECRET` and a `CRON_SECRET`, and run

        scripts/deploy.sh python        # or ts

Your project is named `ws-<your login>-<lang>`. Set `VERCEL_PROJECT` in `.env` if that collides. Hit it:

        scripts/trigger.sh python https://ws-you-python.vercel.app "your task"

The response is the full trace plus verdict, and `trigger.sh` saves it into `runs/` so 301 can read it. Vercel's filesystem is throwaway, so the deployed copy keeps nothing between runs. `vercel.json` also schedules the cron endpoint daily. Change the schedule, or trigger it from the project's Cron Jobs page in the Vercel dashboard.

The trigger layer is just an HTTP handler and a scheduler. If you already have access to GCP or AWS, the same `app.py` runs on Cloud Run and the same handlers run on Lambda. Vercel is the default because it is one command and nobody needs a new account.

### 301: let it read its own history

After a dozen runs, run `improve`. It writes `runs/improvements-<ts>.md` with proposed edits to `system.md`, `criteria.md`, and tool descriptions, grounded in patterns across runs and citing run ids. Apply what you agree with, run again, compare approval rates. That is the whole loop.

## Layout

        python/                       ts/
          agent/loop.py      101        src/loop.ts
          agent/tools.py                src/tools.ts
          agent/system.md               src/system.md
          agent/validate.py  201        src/validate.ts
          agent/criteria.md             src/criteria.md
          app.py             201        api/run.ts, api/cron.ts
          agent/improve.py   301        src/improve.ts
          vercel.json                   vercel.json
          tests/                        tests/
          runs/                         runs/
        scripts/check.sh, scripts/deploy.sh, scripts/trigger.sh
        .claude/            settings, /start and /add-tool skills, reviewer agent
        .env                shared secrets, never committed

## Things that will bite

Rate limits. A hundred of us share one key. If you see 429s, wait a few seconds. The SDK already retries twice. Do not loop-spam.

Cost. `MODEL` defaults to `claude-opus-5`. Set `MODEL=claude-sonnet-5` in `.env` for cheaper iteration while you tune prompts, then switch back to compare.

Turn cap. `MAX_TURNS` is 10, and `MAX_TURNS=25` in `.env` raises it. A trace ending with `stop_reason: tool_use` hit the cap.

Offline tests. `python tests/test_loop.py` and `npm test` run with a fake client and no key. Run them after you touch the loop or tools.

Vercel names. If deploy says the project name is taken, someone shares your login. Set `VERCEL_PROJECT` in `.env` and redeploy.
