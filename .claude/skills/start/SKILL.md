---
name: start
description: Walk someone from a fresh clone to a running agent on a project they picked. Use when the user says "help me start", "I don't know what to build", "get me going", "set me up", or invokes /start.
---

The person in front of you may have never written an agent. Do not dump the repo on them. One step, then show the result, then the next step.

## 1. Is the machine ready

Ask which language they think in, Python or TypeScript, if they have not said. Then run `scripts/check.sh python` or `scripts/check.sh ts`.

Every FIX line it prints is a thing you fix with them now. Do not move on with a failing check. The most common one is an empty `ANTHROPIC_API_KEY`: the shared key gets handed out in the room and goes in `.env` at the repo root. Never print the key, never read `.env` into the transcript, never put it in a file other than `.env`.

## 2. Pick something to build

Ask, as a numbered menu, one question:

1. Chatbot that answers from a knowledge source it has to look up
2. Chess, where the rules live in a tool and the judgment stays in the model
3. Conway's Game of Life, where the agent searches for a seed you describe
4. They already have an idea

If there is no `kits/` directory in this checkout, say so and go straight to option 4.

For 1 to 3, read `kits/<name>/README.md` and follow it. For 4, take their idea and ask the one question that matters: what does this agent have to look up before it can answer? If there is no answer, it is a prompt, not an agent, and a loop will not help. Say so and help them find the lookup.

## 3. Get one run on the board

In this order, and stop to show them the result of each.

1. Copy the kit prompts over: `kits/<name>/system.md` to `python/agent/system.md` or `ts/src/system.md`, same for `criteria.md`.
2. Build the tools from the kit's tool table. Use the `add-tool` skill, one tool at a time, running the offline test after each.
3. Run the loop on the kit's first suggested task.
4. Open the newest `runs/*.json` and read it with them. Point at three things and nothing else: `steps` is every tool call the model made, `stop_reason` says whether it finished or hit the turn cap, `output` is what it told you. Ask them whether the tool calls are what they expected.

## 4. Where they go next

One sentence, not a lecture. They have a 101. The kit README says what 201 and 301 look like for their project, and `criteria.md` is the door into 201.

## Rules

- Change one thing at a time and run it. A beginner who watches five files change at once learns nothing.
- When something breaks, show the error and say which line caused it before you fix it.
- Push edits toward `system.md` and `criteria.md` before code. That is the lesson and it is also usually the fix.
- Do not add frameworks, do not restructure the loop, do not write comments explaining what the code does.
- If they ask for something the kit does not cover, follow them. The kit is a starting point, not a curriculum.
