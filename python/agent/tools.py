"""Tools the agent can call. Add yours here (or ask Claude Code: /add-tool).

Three edits per tool: the function, an entry in HANDLERS, a schema in SCHEMAS.
"""
import json
import urllib.request
from datetime import datetime, timezone

from agent import RUNS_DIR

MEMORY = RUNS_DIR / "memory.json"


def get_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_url(url: str) -> str:
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.read(20_000).decode("utf-8", errors="replace")


def remember(key: str, value: str) -> str:
    data = _load()
    data[key] = value
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    MEMORY.write_text(json.dumps(data, indent=2))
    return f"stored {key}"


def recall(key: str) -> str:
    return _load().get(key, f"nothing stored under {key}")


def _load() -> dict:
    return json.loads(MEMORY.read_text()) if MEMORY.exists() else {}


HANDLERS = {
    "get_time": get_time,
    "fetch_url": fetch_url,
    "remember": remember,
    "recall": recall,
}

# the description is the only thing the model reads when deciding to call a tool. write it for the model.
SCHEMAS = [
    {
        "name": "get_time",
        "description": "Current UTC time as ISO 8601.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "fetch_url",
        "description": "HTTP GET a public URL. Returns the first 20KB of the body as text.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Absolute http(s) URL."}},
            "required": ["url"],
        },
    },
    {
        "name": "remember",
        "description": "Persist a key/value so a future run can read it with recall.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
            "required": ["key", "value"],
        },
    },
    {
        "name": "recall",
        "description": "Read a value stored by remember in this or an earlier run.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    },
]


def dispatch(name: str, args: dict) -> str:
    fn = HANDLERS.get(name)
    if fn is None:
        return f"error: unknown tool {name}"
    try:
        return str(fn(**args))
    except Exception as e:  # errors go back to the model as text so it can recover
        return f"error: {type(e).__name__}: {e}"
