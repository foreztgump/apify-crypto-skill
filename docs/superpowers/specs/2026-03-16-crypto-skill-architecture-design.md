# Apify Crypto Skill — Architecture Design

**Date:** 2026-03-16
**Status:** Reviewed
**Scope:** Python skill package wrapping two Apify actors for AI agent consumption

## Overview

A lightweight Python package providing async functions that fetch cryptocurrency data via Apify actors. AI agents import functions directly — no CLI, no MCP server, no SDK dependencies beyond httpx and pydantic.

### Actors

| Actor | Canonical ID | URL Path Form (tilde-encoded) | Source | Data |
|-------|-------------|-------------------------------|--------|------|
| Crypto Data Scraper | `moving_beacon-owner1/my-actor-14` | `moving_beacon-owner1~my-actor-14` | KuCoin | OHLCV candlesticks, real-time prices |
| CoinGecko Intelligence | `benthepythondev/crypto-intelligence` | `benthepythondev~crypto-intelligence` | CoinGecko | Market data, prices, coin details, historical, trending, categories |

Constants store the tilde-encoded form because it is used directly in URL path construction. The `Authorization: Bearer` header is used (not `?token=` query param) to keep tokens out of logs.

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Consumption model | Python import | AI agents call `from crypto_skill import get_ohlcv` |
| Actor run mode | Sync only | Simple. 300s Apify timeout is sufficient for single-pair/reasonable queries |
| HTTP client lifecycle | Per-call | Each function creates/closes its own httpx client. No state, trivial to test |
| HTTP library | httpx | Async-native, no SDK dependency |
| Validation | Pydantic | Typed models for all actor outputs |
| Architecture | Flat functions | No classes. Each public function is a standalone async callable |

## Package Structure

```
src/crypto_skill/
  __init__.py          # Re-exports all 9 public functions via __all__
  client.py            # Single function: run_actor_sync()
  constants.py         # Actor IDs, API base URL, timeouts, defaults
  exceptions.py        # Typed exception hierarchy
  kucoin.py            # 3 functions wrapping KuCoin actor
  coingecko.py         # 6 functions wrapping CoinGecko actor
  models.py            # All Pydantic input/output models
tests/
  conftest.py          # Shared fixtures (sample responses, env mock)
  test_client.py       # Client layer tests (httpx mocked with respx)
  test_kucoin.py       # KuCoin functions (client.run_actor_sync mocked)
  test_coingecko.py    # CoinGecko functions (client.run_actor_sync mocked)
  test_models.py       # Pydantic validation edge cases
```

## Module Details

### constants.py

All magic values live here. Nothing is hardcoded elsewhere.

```python
APIFY_BASE_URL = "https://api.apify.com/v2"
KUCOIN_ACTOR_ID = "moving_beacon-owner1~my-actor-14"
COINGECKO_ACTOR_ID = "benthepythondev~crypto-intelligence"
DEFAULT_TIMEOUT = 300  # seconds, matches Apify sync endpoint limit
DEFAULT_DATA_LIMIT = 100
DEFAULT_VS_CURRENCY = "usd"
DEFAULT_SORT_ORDER = "market_cap_desc"
```

### client.py

Single function — the only module that touches the Apify REST API.

```python
async def run_actor_sync(actor_id: str, run_input: dict) -> list[dict]:
    """Run an Apify actor synchronously and return dataset items.

    POST /v2/acts/{actor_id}/run-sync-get-dataset-items

    Reads APIFY_TOKEN from os.environ.
    Raises:
        ApifyAuthError: Missing or invalid token (401/403)
        ApifyActorError: Actor run failed (other non-2xx)
        ApifyTimeoutError: 408 or httpx timeout
    """
```

Implementation:
1. Read `APIFY_TOKEN` from `os.environ`, raise `ApifyAuthError` if missing
2. Use `async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:` to ensure cleanup on all paths (success, error, timeout)
3. POST to `{APIFY_BASE_URL}/acts/{actor_id}/run-sync-get-dataset-items` with JSON body and `Authorization: Bearer {token}` header
4. Map HTTP errors: 401/403 → `ApifyAuthError`, 408 → `ApifyTimeoutError`, 429 → `ApifyActorError` (with "rate limited" message), other non-2xx → `ApifyActorError`
5. Map `httpx.TimeoutException` → `ApifyTimeoutError`
6. Map other `httpx.RequestError` (ConnectError, ReadError, etc.) → `ApifyActorError` with original error as cause
7. Parse `response.json()` — if result is not a `list`, raise `ActorDataError("Expected list, got {type}")`
8. Return the validated `list[dict]`

### exceptions.py

```python
class CryptoSkillError(Exception):
    """Base exception for all crypto skill errors."""

class ApifyAuthError(CryptoSkillError):
    """Missing or invalid APIFY_TOKEN (401/403)."""

class ApifyActorError(CryptoSkillError):
    """Actor run failed: non-2xx status, rate limit (429), or connection error."""

class ApifyTimeoutError(CryptoSkillError):
    """Actor run exceeded timeout (408 or httpx timeout)."""

class ActorDataError(CryptoSkillError):
    """Actor response doesn't match expected schema."""
```

### kucoin.py

3 public functions. All call `client.run_actor_sync(KUCOIN_ACTOR_ID, input)` internally.

| Function | Signature | Returns | Notes |
|----------|-----------|---------|-------|
| `get_ohlcv` | `(symbol: str, timeframe: str, limit: int = DEFAULT_DATA_LIMIT)` | `list[OHLCVCandle]` | Converts timestamps ms → s |
| `get_realtime_price` | `(symbol: str)` | `RealtimePrice` | Single-item extraction (see below) |
| `get_all_coins_ohlcv` | `(timeframe: str, limit: int = DEFAULT_DATA_LIMIT)` | `list[OHLCVCandle]` | Passes `symbol=""` to actor for wildcard |

**Actor input field mapping (KuCoin):**

| Function param | Actor input field | Example |
|---------------|-------------------|---------|
| `symbol` | `"symbol"` | `"BTC/USDT"` |
| `timeframe` | `"timeframe"` | `"15m"` |
| `limit` | `"data_limit"` | `100` |

**`get_realtime_price` actor input:** Same as OHLCV with `data_limit=1`. The function sends `{"symbol": "BTC/USDT", "timeframe": "1m", "data_limit": 1}` and extracts the close price + timestamp from the single returned candle.

**`get_all_coins_ohlcv` wildcard:** The actor documentation states that leaving `symbol` blank or using `"*"` fetches all coins. We pass `symbol=""`. **Known limitation:** This function uses the sync endpoint like all others, but fetching all coins is more likely to hit the 300s timeout. CLAUDE.md suggests async+polling for long-running calls, but we keep sync-only for v0.1 simplicity. If this proves unreliable, a future version should add async+polling for this function specifically. Callers should use small `limit` values to reduce risk.

**Single-item extraction rule:** For `get_realtime_price` (returns one model, not a list):
- Take `items[0]` from the dataset result
- If the list is empty, raise `ActorDataError("No data returned for {symbol}")`

**Input validation policy:** Domain functions do NOT validate inputs eagerly. Invalid values (empty symbol, bad timeframe) are passed to the actor, which returns an error that maps to `ApifyActorError`. This avoids duplicating the actor's validation logic.

Each function:
1. Builds the actor input dict (mapping function params to actor input fields per table above)
2. Calls `run_actor_sync`
3. Validates response through Pydantic models, catching `ValidationError` → `ActorDataError`
4. Returns typed model instances

### coingecko.py

6 public functions. All call `client.run_actor_sync(COINGECKO_ACTOR_ID, input)` internally.

| Function | Signature | Returns |
|----------|-----------|---------|
| `get_simple_prices` | `(coin_ids: list[str], vs_currencies: list[str] \| None = None)` | `list[SimplePrice]` |
| `get_market_data` | `(vs_currency: str = "usd", category: str \| None = None, max_results: int = DEFAULT_DATA_LIMIT)` | `list[MarketCoin]` |
| `get_coin_detail` | `(coin_id: str, include_details: bool = True)` | `CoinDetail` |
| `get_historical` | `(coin_id: str, days: int = 30, vs_currency: str = "usd")` | `HistoricalData` |
| `get_trending` | `()` | `list[TrendingCoin]` |
| `get_categories` | `()` | `list[CryptoCategory]` |

Note: `get_market_data` always sorts by market cap descending (the dominant use case). The `sort_by` parameter was removed to stay within the 3-parameter hard rule. If other sort orders are needed later, they can be added via a Pydantic input model.

**Actor input mapping (CoinGecko):**

Each function builds the actor input with the appropriate `scrapeMode` value:
- `get_simple_prices` → `{"scrapeMode": "simple_prices", "coinIds": [...], "vsCurrencies": [...]}`
- `get_market_data` → `{"scrapeMode": "market_data", "vsCurrency": "usd", "sortOrder": "market_cap_desc", "maxResults": 100, ...}`
- `get_coin_detail` → `{"scrapeMode": "coin_detail", "coinIds": ["bitcoin"], "includeDetails": true}` — wraps single `coin_id` string into `["bitcoin"]` list
- `get_historical` → `{"scrapeMode": "historical_data", "coinIds": ["bitcoin"], "days": 30, "vsCurrency": "usd"}` — wraps single `coin_id` string into list
- `get_trending` → `{"scrapeMode": "trending"}`
- `get_categories` → `{"scrapeMode": "categories"}`

**Single-item extraction rule:** For functions returning one model (`get_coin_detail`, `get_historical`):
- Take `items[0]` from the dataset result
- If the list is empty, raise `ActorDataError("No data returned for {coin_id}")`

**Input validation policy:** Same as KuCoin — no eager validation. Invalid inputs propagate to the actor and return as `ApifyActorError`.

**HistoricalData computed fields:** The fields `price_start`, `price_end`, `price_change`, `price_change_percentage`, `price_high`, `price_low` all come directly from the actor response — they are NOT computed by the skill. The `price_data` field comes from the actor as a list of 2-element arrays `[[timestamp, price], ...]` which Pydantic maps to `list[tuple[float, float]]`.

**Exception re-exports:** `__init__.py` also re-exports all exception classes from `exceptions.py` in `__all__`, so agents can `from crypto_skill import ApifyTimeoutError`. Total `__all__` count: 9 functions + 5 exception classes = 14 exports.

**Mutable default avoidance:** `get_simple_prices` uses `vs_currencies: list[str] | None = None` and defaults to `["usd"]` inside the function body, avoiding ruff B006 (mutable default argument).

### models.py

All models use `model_config = ConfigDict(extra="ignore")` to handle extra fields from actors gracefully.

**KuCoin models:**

```python
class OHLCVCandle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    timestamp: float        # Unix seconds (converted from ms by kucoin.py)
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str

class RealtimePrice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    symbol: str
    price: float
    timestamp: float
```

**CoinGecko models:**

```python
class SimplePrice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    coin_id: str
    prices: dict[str, float]   # e.g. {"usd": 93000.0, "eur": 85000.0}

class MarketCoin(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    symbol: str
    name: str
    current_price: float
    market_cap: float
    market_cap_rank: int
    total_volume: float
    high_24h: float | None = None
    low_24h: float | None = None
    price_change_24h: float | None = None
    price_change_percentage_24h: float | None = None
    circulating_supply: float | None = None
    total_supply: float | None = None
    max_supply: float | None = None
    ath: float | None = None
    atl: float | None = None
    last_updated: str | None = None

class CoinDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    symbol: str
    name: str
    description: str
    categories: list[str]
    links: dict[str, Any] = {}
    genesis_date: str | None = None
    sentiment_votes_up: float | None = None
    sentiment_votes_down: float | None = None
    community_data: dict[str, Any] | None = None
    developer_data: dict[str, Any] | None = None

class HistoricalData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    coin_id: str
    price_data: list[tuple[float, float]]  # (timestamp, price)
    price_start: float
    price_end: float
    price_change: float
    price_change_percentage: float
    price_high: float
    price_low: float

class TrendingCoin(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    symbol: str
    name: str
    market_cap_rank: int | None = None

class CryptoCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    market_cap: float | None = None
```

## Data Flow

```
Agent calls get_ohlcv("BTC/USDT", "15m", limit=100)
  → kucoin.get_ohlcv() builds input: {"symbol": "BTC/USDT", "timeframe": "15m", "data_limit": 100}
  → calls client.run_actor_sync(KUCOIN_ACTOR_ID, input)
    → reads APIFY_TOKEN from os.environ
    → creates httpx.AsyncClient(timeout=300)
    → POSTs to https://api.apify.com/v2/acts/moving_beacon-owner1~my-actor-14/run-sync-get-dataset-items
    → Apify runs actor synchronously, returns dataset items as JSON array
    → returns list[dict]
  → kucoin.get_ohlcv() validates each dict through OHLCVCandle model
  → converts timestamp from milliseconds to seconds
  → returns list[OHLCVCandle]
```

## Error Handling

| Source | Exception | When |
|--------|-----------|------|
| Missing env var | `ApifyAuthError` | `APIFY_TOKEN` not in `os.environ` |
| HTTP 401/403 | `ApifyAuthError` | Invalid token |
| HTTP 408 | `ApifyTimeoutError` | Apify sync timeout |
| HTTP 429 | `ApifyActorError` | Rate limited (message includes "rate limited") |
| httpx `TimeoutException` | `ApifyTimeoutError` | Network/connection timeout |
| httpx `RequestError` (non-timeout) | `ApifyActorError` | Connection error, read error, etc. (original error as `__cause__`) |
| HTTP other non-2xx | `ApifyActorError` | Actor failed, bad input, etc. |
| Non-list JSON response | `ActorDataError` | Response is valid JSON but not a list |
| Empty list for single-item fn | `ActorDataError` | `get_realtime_price`, `get_coin_detail`, `get_historical` get `[]` |
| Pydantic validation | `ActorDataError` | Actor output doesn't match model schema |

No retries. Callers decide retry strategy.

## Testing Strategy

All tests mock at the boundary — no real Apify API calls.

| Test File | What's Mocked | What's Tested |
|-----------|---------------|---------------|
| `test_client.py` | httpx via `respx` | Auth header, URL construction, status code → exception mapping, timeout handling |
| `test_kucoin.py` | `client.run_actor_sync` via `unittest.mock.patch` | Input dict building, model parsing, timestamp ms→s conversion, error propagation |
| `test_coingecko.py` | `client.run_actor_sync` via `unittest.mock.patch` | All 6 scrapeMode values, model parsing, default params, error propagation |
| `test_models.py` | Nothing | Pydantic validation, extra fields ignored, optional field defaults, edge cases |
| `conftest.py` | N/A | Shared fixtures: sample actor responses, `APIFY_TOKEN` env var mock |

## Dependencies

| Package | Purpose | Version Constraint |
|---------|---------|-------------------|
| httpx | Async HTTP client | `>=0.28` |
| pydantic | Model validation | `>=2.10` |
| pytest | Test runner | `>=8.0` (dev) |
| pytest-asyncio | Async test support | `>=0.24` (dev) |
| respx | httpx mocking | `>=0.22` (dev) |
| ruff | Linting + formatting | `>=0.15` (dev) |
| pyright | Type checking | `>=1.1` (dev) |

## Public API Summary

```python
# KuCoin (via Crypto Data Scraper actor)
from crypto_skill import get_ohlcv, get_realtime_price, get_all_coins_ohlcv

candles = await get_ohlcv("BTC/USDT", "15m", limit=100)
price = await get_realtime_price("BTC/USDT")
all_candles = await get_all_coins_ohlcv("1h", limit=50)

# CoinGecko (via Crypto Intelligence actor)
from crypto_skill import (
    get_simple_prices, get_market_data, get_coin_detail,
    get_historical, get_trending, get_categories,
)

prices = await get_simple_prices(["bitcoin", "ethereum"])
market = await get_market_data(category="layer-1")
detail = await get_coin_detail("bitcoin")
history = await get_historical("bitcoin", days=90)
trending = await get_trending()
cats = await get_categories()

# Exceptions (also re-exported from crypto_skill)
from crypto_skill import (
    CryptoSkillError, ApifyAuthError, ApifyActorError,
    ApifyTimeoutError, ActorDataError,
)
```
