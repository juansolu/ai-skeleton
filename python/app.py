"""201: the trigger layer. Vercel runs this.

GET  /          browser UI — submit a prompt, see every tool call
POST /          same page, runs the loop and renders the trace
POST /feedback  save a good/bad rating for a trace
POST /run       webhook. body {"task": "..."}, header Authorization: Bearer $WEBHOOK_SECRET
GET  /cron      Vercel Cron hits this on the schedule in vercel.json

Local: flask --app app run
"""
import os

from flask import Flask, jsonify, render_template, request

from agent import loop, validate
from agent.tools import save_feedback as _save_feedback

app = Flask(__name__)

DEFAULT_SCAN_LIMIT = int(os.environ.get("MERCHANT_SCAN_LIMIT", "7"))


def authorized(secret_name: str) -> bool:
    secret = os.environ.get(secret_name)
    return bool(secret) and request.headers.get("Authorization") == f"Bearer {secret}"


def _build_task(raw_task: str, budget: str, scan_limit: int) -> str:
    """Prepend structured constraints to the task so the agent respects them."""
    lines = []
    if budget != "any":
        lines.append(f"Budget constraint: {budget}.")
    if scan_limit < DEFAULT_SCAN_LIMIT:
        lines.append(f"Scan at most {scan_limit} merchants — call list_merchants with limit={scan_limit}.")
    lines.append(raw_task)
    return "\n".join(lines)


@app.route("/", methods=["GET", "POST"])
def index():
    trace = None
    task = ""
    budget = "any"
    scan_limit = DEFAULT_SCAN_LIMIT
    if request.method == "POST":
        task = (request.form.get("task") or "").strip()
        budget = request.form.get("budget", "any")
        scan_limit = int(request.form.get("scan_limit", DEFAULT_SCAN_LIMIT))
        if task:
            enriched = _build_task(task, budget, scan_limit)
            trace = loop.run(enriched)
    return render_template("index.html", trace=trace, task=task, budget=budget, scan_limit=scan_limit, default_scan_limit=DEFAULT_SCAN_LIMIT)


@app.post("/feedback")
def feedback():
    body = request.get_json(silent=True) or {}
    trace_id = body.get("trace_id", "")
    rating = body.get("rating", "")
    result = _save_feedback(trace_id, rating)
    if result.startswith("error:"):
        return jsonify(error=result), 400
    return jsonify(ok=True)


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
