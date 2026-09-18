"""201: the trigger layer. Vercel runs this.

POST /run   webhook. body {"task": "..."}, header Authorization: Bearer $WEBHOOK_SECRET
GET  /cron  Vercel Cron hits this on the schedule in vercel.json, with Authorization: Bearer $CRON_SECRET

Local: flask --app app run
"""
import os

from flask import Flask, jsonify, request

from agent import validate

app = Flask(__name__)


def authorized(secret_name: str) -> bool:
    secret = os.environ.get(secret_name)
    return bool(secret) and request.headers.get("Authorization") == f"Bearer {secret}"


@app.get("/")
def health():
    return {"ok": True, "model": os.environ.get("MODEL", "claude-opus-5")}


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
