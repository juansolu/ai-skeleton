"""Tools the agent can call. Add yours here (or ask Claude Code: /add-tool).

Three edits per tool: the function, an entry in HANDLERS, a schema in SCHEMAS.
"""
import json
import urllib.request
from datetime import datetime, timezone

from agent import RUNS_DIR

MEMORY = RUNS_DIR / "memory.json"

# ---------------------------------------------------------------------------
# Recharge merchant catalog (mock data — swap for a live API call if needed)
# ---------------------------------------------------------------------------

_MERCHANTS = [
    {
        "id": "m_brew",
        "name": "Blue Bottle Coffee",
        "category": "coffee",
        "description": "Single-origin and blended roasts shipped fresh bi-weekly.",
        "tags": ["coffee", "caffeine", "morning", "subscription"],
    },
    {
        "id": "m_bork",
        "name": "The Farmer's Dog",
        "category": "pet_food",
        "description": "Human-grade, vet-formulated fresh dog food delivered weekly.",
        "tags": ["dog", "pet", "food", "fresh"],
    },
    {
        "id": "m_ritual",
        "name": "Ritual Vitamins",
        "category": "supplements",
        "description": "Science-backed multivitamins and protein powders on monthly subscription.",
        "tags": ["vitamins", "health", "supplements", "wellness"],
    },
    {
        "id": "m_seed",
        "name": "Seed Health",
        "category": "supplements",
        "description": "Daily synbiotic capsules combining probiotics and prebiotics.",
        "tags": ["probiotics", "gut health", "supplements", "wellness"],
    },
    {
        "id": "m_prose",
        "name": "Prose Hair Care",
        "category": "beauty",
        "description": "Custom shampoo and conditioner formulated from a hair quiz.",
        "tags": ["hair", "shampoo", "beauty", "personalized"],
    },
    {
        "id": "m_eight",
        "name": "Eight Sleep",
        "category": "sleep",
        "description": "Temperature-regulating mattress covers and sleep accessories.",
        "tags": ["sleep", "recovery", "wellness", "tech"],
    },
    {
        "id": "m_graze",
        "name": "Graze Snacks",
        "category": "snacks",
        "description": "Nutritionist-approved snack boxes curated to your taste preferences.",
        "tags": ["snacks", "healthy", "food", "variety"],
    },
]

_PRODUCTS: dict[str, list[dict]] = {
    "m_brew": [
        {
            "id": "p_brew_01",
            "title": "Bella Donovan Blend",
            "price_usd": 19.00,
            "interval": "bi-weekly",
            "description": "Balanced, full-bodied blend of African and Latin American beans.",
            "tags": ["medium roast", "blend", "everyday"],
        },
        {
            "id": "p_brew_02",
            "title": "Three Africas Blend",
            "price_usd": 22.00,
            "interval": "bi-weekly",
            "description": "Bright, fruit-forward blend from Ethiopia, Uganda, and Burundi.",
            "tags": ["light roast", "fruity", "single-origin"],
        },
        {
            "id": "p_brew_03",
            "title": "Giant Steps Espresso",
            "price_usd": 20.00,
            "interval": "monthly",
            "description": "Dark, sweet espresso blend with notes of chocolate and brown sugar.",
            "tags": ["dark roast", "espresso", "bold"],
        },
    ],
    "m_bork": [
        {
            "id": "p_bork_01",
            "title": "Fresh Dog Food — Beef Recipe",
            "price_usd": 72.00,
            "interval": "weekly",
            "description": "USDA beef, sweet potato, lentils, and carrots. No fillers.",
            "tags": ["beef", "grain-free", "fresh"],
        },
        {
            "id": "p_bork_02",
            "title": "Fresh Dog Food — Chicken Recipe",
            "price_usd": 68.00,
            "interval": "weekly",
            "description": "Free-range chicken with peas, spinach, and carrots.",
            "tags": ["chicken", "lean", "fresh"],
        },
    ],
    "m_ritual": [
        {
            "id": "p_ritual_01",
            "title": "Essential Women's 18+ Multivitamin",
            "price_usd": 35.00,
            "interval": "monthly",
            "description": "9 essential nutrients including omega-3, iron, and D3.",
            "tags": ["women", "multivitamin", "daily"],
        },
        {
            "id": "p_ritual_02",
            "title": "Essential Protein Daily Shake",
            "price_usd": 45.00,
            "interval": "monthly",
            "description": "20g organic pea protein. Vanilla or chocolate flavor.",
            "tags": ["protein", "shake", "post-workout"],
        },
        {
            "id": "p_ritual_03",
            "title": "Essential Men's 18+ Multivitamin",
            "price_usd": 35.00,
            "interval": "monthly",
            "description": "9 key nutrients including omega-3, zinc, and magnesium.",
            "tags": ["men", "multivitamin", "daily"],
        },
    ],
    "m_seed": [
        {
            "id": "p_seed_01",
            "title": "DS-01 Daily Synbiotic",
            "price_usd": 50.00,
            "interval": "monthly",
            "description": "24-strain probiotic and prebiotic capsule for gut and immune support.",
            "tags": ["probiotics", "gut health", "immunity"],
        },
    ],
    "m_prose": [
        {
            "id": "p_prose_01",
            "title": "Custom Shampoo",
            "price_usd": 28.00,
            "interval": "bi-monthly",
            "description": "Sulfate-free formula built from your hair type, goals, and environment.",
            "tags": ["shampoo", "custom", "scalp care"],
        },
        {
            "id": "p_prose_02",
            "title": "Custom Conditioner",
            "price_usd": 28.00,
            "interval": "bi-monthly",
            "description": "Paired conditioner with moisturizing or volumizing actives.",
            "tags": ["conditioner", "custom", "hydration"],
        },
    ],
    "m_eight": [
        {
            "id": "p_eight_01",
            "title": "Pod 4 Cover — Queen",
            "price_usd": 199.00,
            "interval": "monthly",
            "description": "Active cooling and heating mattress cover with sleep tracking.",
            "tags": ["sleep", "temperature", "recovery"],
        },
    ],
    "m_graze": [
        {
            "id": "p_graze_01",
            "title": "Protein Box (8 snacks)",
            "price_usd": 14.00,
            "interval": "weekly",
            "description": "High-protein, low-sugar snacks: nuts, seeds, and protein bars.",
            "tags": ["protein", "healthy snacks", "on-the-go"],
        },
        {
            "id": "p_graze_02",
            "title": "Variety Nibble Box (12 snacks)",
            "price_usd": 18.00,
            "interval": "weekly",
            "description": "Mix of sweet and savory snacks across all macros.",
            "tags": ["variety", "sweet", "savory", "snacks"],
        },
    ],
}


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


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


def list_merchants() -> str:
    """Return all merchants in the catalog."""
    summary = [
        {"id": m["id"], "name": m["name"], "category": m["category"], "description": m["description"]}
        for m in _MERCHANTS
    ]
    return json.dumps(summary, indent=2)


def get_merchant_products(merchant_id: str) -> str:
    """Return all products for a given merchant id."""
    if merchant_id not in _PRODUCTS:
        ids = [m["id"] for m in _MERCHANTS]
        return f"error: unknown merchant_id '{merchant_id}'. Valid ids: {ids}"
    return json.dumps(_PRODUCTS[merchant_id], indent=2)


def search_products(query: str) -> str:
    """Full-text search across all merchant products by query string."""
    q = query.lower()
    hits = []
    for merchant_id, products in _PRODUCTS.items():
        merchant = next(m for m in _MERCHANTS if m["id"] == merchant_id)
        for product in products:
            searchable = " ".join(
                [
                    product["title"],
                    product["description"],
                    " ".join(product["tags"]),
                    merchant["name"],
                    merchant["category"],
                    " ".join(merchant["tags"]),
                ]
            ).lower()
            if q in searchable:
                hits.append({"merchant": merchant["name"], "merchant_id": merchant_id, **product})
    if not hits:
        return f"no products matched '{query}'"
    return json.dumps(hits, indent=2)


HANDLERS = {
    "get_time": get_time,
    "fetch_url": fetch_url,
    "remember": remember,
    "recall": recall,
    "list_merchants": list_merchants,
    "get_merchant_products": get_merchant_products,
    "search_products": search_products,
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
    {
        "name": "list_merchants",
        "description": "List all merchants in the Recharge catalog with their id, name, category, and description.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_merchant_products",
        "description": "Return every product offered by a merchant. Call list_merchants first to get a valid merchant_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "merchant_id": {"type": "string", "description": "The merchant id from list_merchants."}
            },
            "required": ["merchant_id"],
        },
    },
    {
        "name": "search_products",
        "description": "Search all products by keyword (e.g. 'coffee', 'protein', 'dog'). Returns matching products with their merchant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword or phrase to search for."}
            },
            "required": ["query"],
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
