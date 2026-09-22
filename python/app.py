"""Trigger layer — browser UI + webhook + cron.

The browser UI streams loop events in real-time via Server-Sent Events (SSE).
The client POSTs the task to /stream and reads a chunked text/event-stream
response; each SSE line is one loop event (start, thinking, tool_call, etc.).

Start:  flask --app app run    (or python app.py)
"""
import json
import os
import queue
import threading

from flask import Flask, Response, jsonify, render_template, request

from agent import loop, validate
from agent.tools import save_feedback as _save_feedback

app = Flask(__name__)

DEFAULT_SCAN_LIMIT = int(os.environ.get("MERCHANT_SCAN_LIMIT", "7"))


def authorized(secret_name: str) -> bool:
    secret = os.environ.get(secret_name)
    return bool(secret) and request.headers.get("Authorization") == f"Bearer {secret}"


def _build_task(raw_task: str, budget: str, scan_limit: int) -> str:
    lines = []
    if budget != "any":
        lines.append(f"Budget constraint: {budget}.")
    if scan_limit < DEFAULT_SCAN_LIMIT:
        lines.append(f"Scan at most {scan_limit} merchants — call list_merchants with limit={scan_limit}.")
    lines.append(raw_task)
    return "\n".join(lines)


# ── browser UI ────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", default_scan_limit=DEFAULT_SCAN_LIMIT)


@app.post("/stream")
def stream():
    """Run the agent loop and stream events back as Server-Sent Events."""
    body = request.get_json(silent=True) or {}
    task = _build_task(
        (body.get("task") or "").strip(),
        body.get("budget", "any"),
        int(body.get("scan_limit", DEFAULT_SCAN_LIMIT)),
    )
    if not task.strip():
        return jsonify(error="task is required"), 400

    # thread-safe queue between the loop thread and the generator
    q: queue.Queue = queue.Queue()

    def on_event(event: dict) -> None:
        q.put(event)

    def run_loop() -> None:
        try:
            loop.run(task, on_event=on_event)
        except Exception as exc:
            q.put({"type": "error", "message": str(exc)})
        finally:
            q.put(None)  # sentinel: generator knows to stop

    threading.Thread(target=run_loop, daemon=True).start()

    def generate():
        while True:
            event = q.get()       # blocks until the loop emits something
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── feedback ──────────────────────────────────────────────────────────────────

@app.post("/feedback")
def feedback():
    body = request.get_json(silent=True) or {}
    result = _save_feedback(body.get("trace_id", ""), body.get("rating", ""))
    if result.startswith("error:"):
        return jsonify(error=result), 400
    return jsonify(ok=True)


# ── JSON API (webhook + cron) ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"ok": True, "model": os.environ.get("MODEL", "claude-sonnet-5")}


@app.post("/run")
def run():
    if not authorized("WEBHOOK_SECRET"):
        return jsonify(error="unauthorized"), 401
    task = (request.get_json(silent=True) or {}).get("task")
    if not task:
        return jsonify(error='body must be {"task": "..."}'), 400
    return jsonify(validate.run_validated(task))


@app.get("/cron")
def cron():
    if not authorized("CRON_SECRET"):
        return jsonify(error="unauthorized"), 401
    task = os.environ.get("CRON_TASK", "Recall what we stored under last_run and summarize it in one line.")
    return jsonify(validate.run_validated(task))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
