"""301: the agent reads its own history and proposes how to get better.

    python -m agent.improve

Reads every trace in runs/, summarizes them, and asks the model for concrete edits
to system.md, criteria.md, and tool descriptions, grounded in patterns across runs.
Writes runs/improvements-<ts>.md. You read it and apply what you agree with.
The human stays on the loop. Measure approval rate before and after.
"""
import json
import sys
import time
from pathlib import Path

import anthropic

from agent import RUNS_DIR, loop, tools

HERE = Path(__file__).parent
client = anthropic.Anthropic()


def load_traces() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(RUNS_DIR.glob("*.json")) if p.name != "memory.json"]


def summarize(t: dict) -> dict:
    v = t.get("verdict") or {}
    return {
        "id": t["id"],
        "task": t["task"][:300],
        "tools": [s["tool"] for s in t["steps"]],
        "tool_errors": [s["output"][:200] for s in t["steps"] if s["output"].startswith("error:")],
        "stop_reason": t.get("stop_reason"),
        "approved": v.get("approved"),
        "score": v.get("score"),
        "feedback": v.get("feedback"),
        "output": (t.get("output") or "")[:500],
    }


def improve() -> Path:
    traces = load_traces()
    if not traces:
        sys.exit(f"no traces in {RUNS_DIR}. run the loop a few times first.")
    context = {
        "system_prompt": (HERE / "system.md").read_text(),
        "criteria": (HERE / "criteria.md").read_text(),
        "tool_schemas": tools.SCHEMAS,
        "runs": [summarize(t) for t in traces],
    }
    response = client.messages.create(
        model=loop.MODEL,
        max_tokens=16000,
        system=(
            "You improve an agent by reading its run history. Find patterns across runs, not one-offs. "
            "Propose concrete edits to the system prompt, the criteria, or tool descriptions as exact "
            "replacement text. For each edit, cite the run ids that motivate it. If the runs do not "
            "support a change, say so."
        ),
        messages=[{"role": "user", "content": json.dumps(context, indent=2, default=str)}],
    )
    report = "".join(b.text for b in response.content if b.type == "text")
    out = RUNS_DIR / f"improvements-{time.strftime('%Y%m%d-%H%M%S')}.md"
    out.write_text(report)
    return out


if __name__ == "__main__":
    path = improve()
    print(path.read_text())
    print(f"\n[saved {path}]", file=sys.stderr)
