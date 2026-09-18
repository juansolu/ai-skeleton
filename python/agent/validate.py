"""201: a second agent judges the first.

    python -m agent.validate "task"

Runs the loop, hands the trace and criteria.md to a reviewer, gets a structured
verdict. Rejected runs go back to the loop with the feedback, up to MAX_ATTEMPTS.
After that a human decides. That is the point: you review verdicts, not runs.
"""
import json
import sys
from pathlib import Path

import anthropic
from pydantic import BaseModel

from agent import loop

CRITERIA = (Path(__file__).parent / "criteria.md").read_text()
MAX_ATTEMPTS = 3

client = anthropic.Anthropic()


class Verdict(BaseModel):
    approved: bool
    score: int
    feedback: str


def validate(trace: dict) -> Verdict:
    response = client.messages.parse(
        model=loop.MODEL,
        max_tokens=16000,
        system="You are a strict reviewer. Judge the run against the criteria. Never fix the work yourself.",
        messages=[
            {
                "role": "user",
                "content": f"# Criteria\n{CRITERIA}\n\n# Run\n{json.dumps(trace, indent=2, default=str)}",
            }
        ],
        output_format=Verdict,
    )
    return response.parsed_output


def run_validated(task: str) -> dict:
    feedback = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        prompt = task if not feedback else f"{task}\n\nA reviewer rejected your last attempt. Their feedback:\n{feedback}"
        trace = loop.run(prompt)
        verdict = validate(trace)
        trace["verdict"] = verdict.model_dump() | {"attempt": attempt}
        loop.save(trace)
        if verdict.approved:
            return trace
        feedback = verdict.feedback
    return trace


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or "What time is it? Remember it under last_run."
    t = run_validated(task)
    print(t["output"])
    print(f"\nverdict: {json.dumps(t['verdict'], indent=2)}", file=sys.stderr)
