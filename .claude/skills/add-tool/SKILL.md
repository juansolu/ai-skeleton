---
name: add-tool
description: Add a new tool the agent can call. Use when the user says "add a tool", "give the agent a way to X", or invokes /add-tool <what it does>.
---

Tools live in `python/agent/tools.py` and `ts/src/tools.ts`. Ask which language if the repo has both and the user did not say. Three edits, then prove it works.

1. Write a plain function. Its arguments are the tool inputs. It returns a string. On failure, raise or throw; `dispatch` turns that into text the model can read and recover from.
2. Add it to `HANDLERS`.
3. Add a schema to `SCHEMAS`. The `description` is the only thing the model sees when deciding whether to call the tool. Write it for the model, not for a human. Mark required arguments. Describe argument formats when they are not obvious.
4. Run the offline test (`python tests/test_loop.py` or `npm test`), then run the loop with a task that needs the new tool and confirm the trace in `runs/` shows the call.

Keep tools small and dumb. Judgment belongs in the model, mechanics in the tool. A tool that "decides" things is a tool that hides bugs.
