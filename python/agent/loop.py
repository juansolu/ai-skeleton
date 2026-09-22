"""101: the agentic loop.

    python -m agent.loop "What time is it? Remember it under last_run."

One call to the model, run whatever tools it asked for, feed results back, repeat
until it stops asking. Everything that happened lands in runs/<id>.json.

The SDK ships a helper that does this loop for you (client.beta.messages.tool_runner).
It is written out here because the loop is the point of 101.
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path

import anthropic

from agent import RUNS_DIR, tools

MODEL = os.environ.get("MODEL", "claude-sonnet-5")
SYSTEM = (Path(__file__).parent / "system.md").read_text()
MAX_TURNS = int(os.environ.get("MAX_TURNS", "10"))

client = anthropic.Anthropic()


def run(task: str, on_event=None) -> dict:
    def emit(event: dict) -> None:
        if on_event:
            on_event(event)

    run_id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    messages = [{"role": "user", "content": task}]
    trace = {"id": run_id, "task": task, "model": MODEL, "steps": [], "usage": {"input": 0, "output": 0}}

    emit({"type": "start", "run_id": run_id, "task": task})

    # ─── THE LOOP ────────────────────────────────────────────────────────────
    for turn in range(MAX_TURNS):
        emit({"type": "thinking", "turn": turn + 1})   # ← loop back to model

        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            tools=tools.SCHEMAS,
            messages=messages,
        )
        trace["usage"]["input"] += response.usage.input_tokens
        trace["usage"]["output"] += response.usage.output_tokens
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break                                       # ← model decided it's done

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            emit({"type": "tool_call", "turn": turn + 1, "tool": block.name, "input": block.input})
            out = tools.dispatch(block.name, block.input)
            truncated = out[:2000]
            trace["steps"].append({"tool": block.name, "input": block.input, "output": truncated})
            emit({"type": "tool_result", "turn": turn + 1, "tool": block.name, "output": truncated})
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": out,
                    "is_error": out.startswith("error:"),
                }
            )
        messages.append({"role": "user", "content": results})  # ← feed results back, repeat
    # ─────────────────────────────────────────────────────────────────────────

    # stop_reason still "tool_use" here means MAX_TURNS was hit
    trace["stop_reason"] = response.stop_reason
    trace["output"] = "".join(b.text for b in response.content if b.type == "text")
    save(trace)
    emit({"type": "answer", "text": trace["output"], "run_id": run_id,
          "usage": trace["usage"], "stop_reason": trace["stop_reason"],
          "step_count": len(trace["steps"])})
    return trace


def save(trace: dict) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{trace['id']}.json"
    path.write_text(json.dumps(trace, indent=2, default=str))
    return path


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or "What time is it? Remember it under last_run."
    t = run(task)
    print(t["output"])
    print(
        f"\n[{len(t['steps'])} tool calls, stop={t['stop_reason']}, "
        f"tokens in/out={t['usage']['input']}/{t['usage']['output']}, trace={RUNS_DIR}/{t['id']}.json]",
        file=sys.stderr,
    )
