# Merchant Recommender — Python Agent Loop

A working example of a Recharge product recommendation agent built on the 101 skeleton. Given what a user is interested in and what they have already bought, the agent browses a merchant catalog and recommends a specific subscription product.

## How the loop works

```
┌─────────────────────────────────────────────────────────────────────┐
│  loop.py — the agentic loop (agent/loop.py:34)                      │
│                                                                     │
│  messages = [{"role": "user", "content": task}]                     │
│                                                                     │
│  for _ in range(MAX_TURNS):          ← LOOP STARTS HERE            │
│      response = claude(messages)     ← model decides what to do    │
│                                                                     │
│      if stop_reason != "tool_use":                                  │
│          break                       ← model is done, exit loop    │
│                                                                     │
│      for each tool_use in response:                                 │
│          result = tools.dispatch(name, args)   ← run the tool      │
│          collect results                                            │
│                                                                     │
│      messages.append(tool results)   ← feed results back           │
│  ── repeat ──────────────────────────────────────────────────────── │
│                                                                     │
│  Everything that happened is saved to runs/<id>.json               │
└─────────────────────────────────────────────────────────────────────┘
```

Each iteration is one round-trip to the model. The model decides whether to call a tool or stop. If it calls tools, the results go back into `messages` and the loop runs again. The loop exits when `stop_reason == "end_turn"` (model is done) or when `MAX_TURNS` is hit.

For a recommendation task the model typically takes 3–4 turns:

| Turn | What the model does |
|------|---------------------|
| 1 | Calls `list_merchants` to see what's available |
| 2 | Calls `get_merchant_products` for 1–2 relevant merchants |
| 3 | (Optional) Calls `search_products` to cross-check a keyword |
| 4 | Produces a final text recommendation and calls `remember` to persist it |

## Run it

```bash
cd python
source .venv/bin/activate

# basic recommendation
python -m agent.loop "I love coffee and wellness. I already subscribe to Seed Health probiotics."

# different profile
python -m agent.loop "I have a dog and I'm into healthy snacking. I already buy Blue Bottle Coffee."
```

The full trace lands in `runs/<id>.json`. Read it to see every tool call and result.

## Tools

### Merchant catalog tools (new in this branch)

| Tool | What it does |
|------|--------------|
| `list_merchants` | Lists all merchants: id, name, category, description. **Always call this first.** |
| `get_merchant_products(merchant_id)` | Returns every product a merchant offers — title, price, interval, description, tags. |
| `search_products(query)` | Full-text search across all products and merchant metadata by keyword. |

The catalog is mock data in `agent/tools.py` (`_MERCHANTS`, `_PRODUCTS`). Swap those for a live Recharge API call to use real store data.

### Baseline tools

| Tool | What it does |
|------|--------------|
| `get_time` | Returns current UTC time as ISO 8601. |
| `fetch_url(url)` | HTTP GET a public URL. Returns the first 20 KB as text. |
| `remember(key, value)` | Persists a value across runs in `runs/memory.json`. |
| `recall(key)` | Reads a value stored by `remember`. |

### Adding your own tool

Three edits in `agent/tools.py`:

```python
# 1. The function
def my_tool(arg: str) -> str:
    return "result"

# 2. Register it
HANDLERS = {
    ...
    "my_tool": my_tool,
}

# 3. Describe it for the model
SCHEMAS = [
    ...
    {
        "name": "my_tool",
        "description": "One sentence — what this returns and when to call it.",
        "input_schema": {
            "type": "object",
            "properties": {"arg": {"type": "string", "description": "What arg is."}},
            "required": ["arg"],
        },
    },
]
```

Or just run `/add-tool <what it does>` in Claude Code and it writes all three edits for you.

## Files changed in this branch

| File | What changed |
|------|--------------|
| `agent/tools.py` | Added `_MERCHANTS`, `_PRODUCTS` mock catalog and three new tools |
| `agent/system.md` | Rewritten as a product recommender prompt |
| `agent/criteria.md` | Updated rubric to validate recommender behavior |
| `python/README.md` | This file |

## Security note

`.env` (which holds `ANTHROPIC_API_KEY`) is in `.gitignore` and will never be committed. Never remove it from `.gitignore`. The `.env.example` file shows which keys are expected without containing real values.
