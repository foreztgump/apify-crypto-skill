# Apify Crypto Skill Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Python skill package that wraps two Apify actors (KuCoin OHLCV, CoinGecko Intelligence) into 9 async functions consumable by AI agents.

**Architecture:** Flat async functions in domain modules (`kucoin.py`, `coingecko.py`) call a thin Apify REST API client (`client.py`). All actor outputs validated through Pydantic models. No classes, no state.

**Tech Stack:** Python 3.12+, httpx, pydantic, pytest + pytest-asyncio + respx

**Spec:** `docs/superpowers/specs/2026-03-16-crypto-skill-architecture-design.md`

---

## Pre-requisites

- [ ] **Step 0a: Create venv and install dependencies**

```bash
cd /home/cownose/projects/apify-crypto-skill
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

- [ ] **Step 0b: Verify tooling works**

```bash
pytest --version    # Expected: pytest 8.x+
ruff --version      # Expected: ruff 0.15.x+
python -c "import httpx; print(httpx.__version__)"     # Expected: 0.28.x
python -c "import pydantic; print(pydantic.__version__)" # Expected: 2.x
```

---

## Chunk 1: Foundation (constants, exceptions, models, client)

### Task 1: Constants and Exceptions

**Files:**
- Create: `src/crypto_skill/constants.py`
- Create: `src/crypto_skill/exceptions.py`
- Test: `tests/test_exceptions.py`

- [ ] **Step 1.1: Write test for exception hierarchy**

```python
# tests/test_exceptions.py
from crypto_skill.exceptions import (
    ActorDataError,
    ApifyActorError,
    ApifyAuthError,
    ApifyTimeoutError,
    CryptoSkillError,
)


def test_all_exceptions_inherit_from_base():
    assert issubclass(ApifyAuthError, CryptoSkillError)
    assert issubclass(ApifyActorError, CryptoSkillError)
    assert issubclass(ApifyTimeoutError, CryptoSkillError)
    assert issubclass(ActorDataError, CryptoSkillError)


def test_base_inherits_from_exception():
    assert issubclass(CryptoSkillError, Exception)


def test_exception_message():
    err = ApifyActorError("run failed")
    assert str(err) == "run failed"
```

- [ ] **Step 1.2: Run test to verify it fails**

Run: `pytest tests/test_exceptions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crypto_skill.exceptions'`

- [ ] **Step 1.3: Implement constants.py**

```python
# src/crypto_skill/constants.py
APIFY_BASE_URL = "https://api.apify.com/v2"
KUCOIN_ACTOR_ID = "moving_beacon-owner1~my-actor-14"
COINGECKO_ACTOR_ID = "benthepythondev~crypto-intelligence"
DEFAULT_TIMEOUT = 300  # seconds, matches Apify sync endpoint limit
DEFAULT_DATA_LIMIT = 100
DEFAULT_VS_CURRENCY = "usd"
DEFAULT_SORT_ORDER = "market_cap_desc"
REALTIME_TIMEFRAME = "1m"
REALTIME_DATA_LIMIT = 1
```

- [ ] **Step 1.4: Implement exceptions.py**

```python
# src/crypto_skill/exceptions.py
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

- [ ] **Step 1.5: Run test to verify it passes**

Run: `pytest tests/test_exceptions.py -v`
Expected: 3 PASSED

- [ ] **Step 1.6: Commit**

```bash
git add src/crypto_skill/constants.py src/crypto_skill/exceptions.py tests/test_exceptions.py
git commit -m "feat(core): add constants and exception hierarchy"
```

---

### Task 2: Pydantic Models

**Files:**
- Create: `src/crypto_skill/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 2.1: Write tests for KuCoin models**

```python
# tests/test_models.py
import pytest
from crypto_skill.models import (
    CoinDetail,
    CryptoCategory,
    HistoricalData,
    MarketCoin,
    OHLCVCandle,
    RealtimePrice,
    SimplePrice,
    TrendingCoin,
)


class TestOHLCVCandle:
    def test_valid_candle(self):
        candle = OHLCVCandle(
            timestamp=1710000000.0,
            open=65000.0,
            high=66000.0,
            low=64000.0,
            close=65500.0,
            volume=1234.56,
            symbol="BTC/USDT",
        )
        assert candle.close == 65500.0
        assert candle.symbol == "BTC/USDT"

    def test_extra_fields_ignored(self):
        candle = OHLCVCandle(
            timestamp=1710000000.0,
            open=65000.0,
            high=66000.0,
            low=64000.0,
            close=65500.0,
            volume=1234.56,
            symbol="BTC/USDT",
            extra_field="should be ignored",
        )
        assert not hasattr(candle, "extra_field")

    def test_missing_required_field_raises(self):
        with pytest.raises(Exception):
            OHLCVCandle(
                timestamp=1710000000.0,
                open=65000.0,
                high=66000.0,
                low=64000.0,
                # missing close
                volume=1234.56,
                symbol="BTC/USDT",
            )


class TestRealtimePrice:
    def test_valid_price(self):
        price = RealtimePrice(
            symbol="ETH/USDT",
            price=3200.50,
            timestamp=1710000000.0,
        )
        assert price.price == 3200.50


class TestSimplePrice:
    def test_valid_simple_price(self):
        sp = SimplePrice(
            coin_id="bitcoin",
            prices={"usd": 93000.0, "eur": 85000.0},
        )
        assert sp.prices["usd"] == 93000.0


class TestMarketCoin:
    def test_required_fields_only(self):
        coin = MarketCoin(
            id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            current_price=93000.0,
            market_cap=1850000000000.0,
            market_cap_rank=1,
            total_volume=50000000000.0,
        )
        assert coin.high_24h is None
        assert coin.market_cap_rank == 1

    def test_all_optional_fields(self):
        coin = MarketCoin(
            id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            current_price=93000.0,
            market_cap=1850000000000.0,
            market_cap_rank=1,
            total_volume=50000000000.0,
            high_24h=95000.0,
            low_24h=91000.0,
            ath=126000.0,
            atl=67.81,
            last_updated="2026-03-16T08:00:00Z",
        )
        assert coin.ath == 126000.0


class TestCoinDetail:
    def test_with_defaults(self):
        detail = CoinDetail(
            id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            description="A peer-to-peer electronic cash system",
            categories=["Cryptocurrency", "Layer 1"],
        )
        assert detail.links == {}
        assert detail.genesis_date is None


class TestHistoricalData:
    def test_price_data_tuples(self):
        hist = HistoricalData(
            coin_id="bitcoin",
            price_data=[(1710000000.0, 93000.0), (1710003600.0, 93500.0)],
            price_start=93000.0,
            price_end=93500.0,
            price_change=500.0,
            price_change_percentage=0.54,
            price_high=93800.0,
            price_low=92500.0,
        )
        assert len(hist.price_data) == 2
        assert hist.price_data[0] == (1710000000.0, 93000.0)


class TestTrendingCoin:
    def test_optional_rank(self):
        coin = TrendingCoin(id="pepe", symbol="pepe", name="Pepe")
        assert coin.market_cap_rank is None


class TestCryptoCategory:
    def test_optional_market_cap(self):
        cat = CryptoCategory(id="defi", name="DeFi")
        assert cat.market_cap is None
```

- [ ] **Step 2.2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crypto_skill.models'`

- [ ] **Step 2.3: Implement models.py**

```python
# src/crypto_skill/models.py
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


# --- KuCoin Models ---


class OHLCVCandle(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: float
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


# --- CoinGecko Models ---


class SimplePrice(BaseModel):
    model_config = ConfigDict(extra="ignore")

    coin_id: str
    prices: dict[str, float]


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
    price_data: list[tuple[float, float]]
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

- [ ] **Step 2.4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: 11 PASSED

- [ ] **Step 2.5: Commit**

```bash
git add src/crypto_skill/models.py tests/test_models.py
git commit -m "feat(models): add pydantic models for KuCoin and CoinGecko data"
```

---

### Task 3: Apify Client

**Files:**
- Create: `src/crypto_skill/client.py`
- Create: `tests/conftest.py`
- Create: `tests/test_client.py`

- [ ] **Step 3.1: Write conftest with shared fixtures**

```python
# tests/conftest.py
import pytest


@pytest.fixture()
def apify_token_env(monkeypatch):
    """Set APIFY_TOKEN env var for tests."""
    monkeypatch.setenv("APIFY_TOKEN", "test-token-abc123")


@pytest.fixture()
def sample_ohlcv_response():
    """Sample KuCoin OHLCV dataset items."""
    return [
        {
            "timestamp": 1710000000000,
            "open": 65000.0,
            "high": 66000.0,
            "low": 64000.0,
            "close": 65500.0,
            "volume": 1234.56,
            "symbol": "BTC/USDT",
        },
        {
            "timestamp": 1710000900000,
            "open": 65500.0,
            "high": 66500.0,
            "low": 65000.0,
            "close": 66000.0,
            "volume": 2345.67,
            "symbol": "BTC/USDT",
        },
    ]


@pytest.fixture()
def sample_market_response():
    """Sample CoinGecko market data dataset items."""
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 93000.0,
            "market_cap": 1850000000000.0,
            "market_cap_rank": 1,
            "total_volume": 50000000000.0,
            "price_change_percentage_24h": 7.3,
        },
    ]


@pytest.fixture()
def sample_coin_detail_response():
    """Sample CoinGecko coin detail dataset items."""
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "description": "A peer-to-peer electronic cash system",
            "categories": ["Cryptocurrency", "Layer 1"],
            "links": {"homepage": ["https://bitcoin.org"]},
            "genesis_date": "2009-01-03",
        },
    ]


@pytest.fixture()
def sample_historical_response():
    """Sample CoinGecko historical data dataset items."""
    return [
        {
            "coin_id": "bitcoin",
            "price_data": [[1710000000.0, 93000.0], [1710003600.0, 93500.0]],
            "price_start": 93000.0,
            "price_end": 93500.0,
            "price_change": 500.0,
            "price_change_percentage": 0.54,
            "price_high": 93800.0,
            "price_low": 92500.0,
        },
    ]


@pytest.fixture()
def sample_trending_response():
    """Sample CoinGecko trending dataset items."""
    return [
        {"id": "pepe", "symbol": "pepe", "name": "Pepe", "market_cap_rank": 25},
        {"id": "bonk", "symbol": "bonk", "name": "Bonk"},
    ]


@pytest.fixture()
def sample_categories_response():
    """Sample CoinGecko categories dataset items."""
    return [
        {"id": "defi", "name": "DeFi", "market_cap": 100000000000.0},
        {"id": "layer-1", "name": "Layer 1", "market_cap": 500000000000.0},
    ]


@pytest.fixture()
def sample_simple_prices_response():
    """Sample CoinGecko simple prices dataset items."""
    return [
        {"coin_id": "bitcoin", "prices": {"usd": 93000.0, "eur": 85000.0}},
        {"coin_id": "ethereum", "prices": {"usd": 3200.0, "eur": 2900.0}},
    ]
```

- [ ] **Step 3.2: Write tests for client.run_actor_sync**

```python
# tests/test_client.py
import httpx
import pytest
import respx

from crypto_skill.client import run_actor_sync
from crypto_skill.constants import APIFY_BASE_URL
from crypto_skill.exceptions import (
    ActorDataError,
    ApifyActorError,
    ApifyAuthError,
    ApifyTimeoutError,
)

ACTOR_ID = "test-user~test-actor"
EXPECTED_URL = f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/run-sync-get-dataset-items"


class TestRunActorSyncSuccess:
    @respx.mock
    async def test_returns_dataset_items(self, apify_token_env):
        items = [{"key": "value"}]
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(200, json=items))

        result = await run_actor_sync(ACTOR_ID, {"input": "data"})

        assert result == items

    @respx.mock
    async def test_sends_auth_header(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(200, json=[]))

        await run_actor_sync(ACTOR_ID, {})

        request = respx.calls.last.request
        assert request.headers["authorization"] == "Bearer test-token-abc123"

    @respx.mock
    async def test_sends_json_body(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(200, json=[]))

        await run_actor_sync(ACTOR_ID, {"symbol": "BTC/USDT"})

        request = respx.calls.last.request
        assert b'"symbol"' in request.content
        assert b'"BTC/USDT"' in request.content


class TestRunActorSyncAuthErrors:
    async def test_missing_token_raises_auth_error(self, monkeypatch):
        monkeypatch.delenv("APIFY_TOKEN", raising=False)

        with pytest.raises(ApifyAuthError, match="APIFY_TOKEN"):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_401_raises_auth_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(401))

        with pytest.raises(ApifyAuthError):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_403_raises_auth_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(403))

        with pytest.raises(ApifyAuthError):
            await run_actor_sync(ACTOR_ID, {})


class TestRunActorSyncTimeoutErrors:
    @respx.mock
    async def test_408_raises_timeout_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(408))

        with pytest.raises(ApifyTimeoutError):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_httpx_timeout_raises_timeout_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(side_effect=httpx.ReadTimeout("timed out"))

        with pytest.raises(ApifyTimeoutError):
            await run_actor_sync(ACTOR_ID, {})


class TestRunActorSyncActorErrors:
    @respx.mock
    async def test_500_raises_actor_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(500))

        with pytest.raises(ApifyActorError):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_429_raises_actor_error_with_rate_limit_message(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(429))

        with pytest.raises(ApifyActorError, match="rate limited"):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_connection_error_raises_actor_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(side_effect=httpx.ConnectError("refused"))

        with pytest.raises(ApifyActorError):
            await run_actor_sync(ACTOR_ID, {})


class TestRunActorSyncDataErrors:
    @respx.mock
    async def test_non_list_response_raises_data_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(
            return_value=httpx.Response(200, json={"error": "bad"})
        )

        with pytest.raises(ActorDataError, match="Expected list"):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_invalid_json_raises_data_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(
            return_value=httpx.Response(200, content=b"not json", headers={"content-type": "text/html"})
        )

        with pytest.raises(ActorDataError, match="Invalid JSON"):
            await run_actor_sync(ACTOR_ID, {})


class TestRunActorSyncExceptionChaining:
    @respx.mock
    async def test_timeout_preserves_cause(self, apify_token_env):
        original = httpx.ReadTimeout("timed out")
        respx.post(EXPECTED_URL).mock(side_effect=original)

        with pytest.raises(ApifyTimeoutError) as exc_info:
            await run_actor_sync(ACTOR_ID, {})

        assert exc_info.value.__cause__ is original

    @respx.mock
    async def test_connection_error_preserves_cause(self, apify_token_env):
        original = httpx.ConnectError("refused")
        respx.post(EXPECTED_URL).mock(side_effect=original)

        with pytest.raises(ApifyActorError) as exc_info:
            await run_actor_sync(ACTOR_ID, {})

        assert exc_info.value.__cause__ is original
```

- [ ] **Step 3.3: Run tests to verify they fail**

Run: `pytest tests/test_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crypto_skill.client'`

- [ ] **Step 3.4: Implement client.py**

```python
# src/crypto_skill/client.py
from __future__ import annotations

import os

import httpx

from crypto_skill.constants import APIFY_BASE_URL, DEFAULT_TIMEOUT
from crypto_skill.exceptions import (
    ActorDataError,
    ApifyActorError,
    ApifyAuthError,
    ApifyTimeoutError,
)

AUTH_ERROR_CODES = frozenset({401, 403})
TIMEOUT_ERROR_CODE = 408
RATE_LIMIT_ERROR_CODE = 429


async def run_actor_sync(actor_id: str, run_input: dict) -> list[dict]:
    """Run an Apify actor synchronously and return dataset items.

    POST /v2/acts/{actor_id}/run-sync-get-dataset-items

    Reads APIFY_TOKEN from os.environ.
    """
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise ApifyAuthError("APIFY_TOKEN environment variable is not set")

    url = f"{APIFY_BASE_URL}/acts/{actor_id}/run-sync-get-dataset-items"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(url, json=run_input, headers=headers)
    except httpx.TimeoutException as exc:
        raise ApifyTimeoutError(f"Request timed out: {exc}") from exc
    except httpx.RequestError as exc:
        raise ApifyActorError(f"Request failed: {exc}") from exc

    status = response.status_code

    if status in AUTH_ERROR_CODES:
        raise ApifyAuthError(f"Authentication failed (HTTP {status})")

    if status == TIMEOUT_ERROR_CODE:
        raise ApifyTimeoutError(f"Actor run timed out (HTTP {status})")

    if status == RATE_LIMIT_ERROR_CODE:
        raise ApifyActorError(f"Apify API rate limited (HTTP {status})")

    if status >= 400:
        raise ApifyActorError(f"Actor run failed (HTTP {status})")

    try:
        data = response.json()
    except ValueError as exc:
        raise ActorDataError(f"Invalid JSON response: {exc}") from exc

    if not isinstance(data, list):
        raise ActorDataError(f"Expected list, got {type(data).__name__}")

    return data
```

- [ ] **Step 3.5: Run tests to verify they pass**

Run: `pytest tests/test_client.py -v`
Expected: 15 PASSED

- [ ] **Step 3.6: Run ruff check**

Run: `ruff check src/crypto_skill/ tests/ && ruff format --check src/crypto_skill/ tests/`
Expected: All passed

- [ ] **Step 3.7: Commit**

```bash
git add src/crypto_skill/client.py tests/conftest.py tests/test_client.py
git commit -m "feat(client): add Apify REST API client with error mapping"
```

---

## Chunk 2: Domain Modules and Package Init

### Task 4: KuCoin Module

**Files:**
- Create: `src/crypto_skill/kucoin.py`
- Create: `tests/test_kucoin.py`

- [ ] **Step 4.1: Write tests for kucoin functions**

```python
# tests/test_kucoin.py
from unittest.mock import AsyncMock, patch

import pytest

from crypto_skill.constants import DEFAULT_DATA_LIMIT, KUCOIN_ACTOR_ID
from crypto_skill.exceptions import ActorDataError
from crypto_skill.models import OHLCVCandle, RealtimePrice

MODULE_PATH = "crypto_skill.kucoin.run_actor_sync"


class TestGetOhlcv:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_candles_with_converted_timestamps(
        self, mock_run, sample_ohlcv_response
    ):
        mock_run.return_value = sample_ohlcv_response

        from crypto_skill.kucoin import get_ohlcv

        result = await get_ohlcv("BTC/USDT", "15m")

        assert len(result) == 2
        assert isinstance(result[0], OHLCVCandle)
        assert result[0].timestamp == 1710000000.0  # ms / 1000
        assert result[0].close == 65500.0

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_builds_correct_actor_input(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.kucoin import get_ohlcv

        await get_ohlcv("ETH/USDT", "1h", limit=50)

        mock_run.assert_called_once_with(
            KUCOIN_ACTOR_ID,
            {"symbol": "ETH/USDT", "timeframe": "1h", "data_limit": 50},
        )

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_uses_default_limit(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.kucoin import get_ohlcv

        await get_ohlcv("BTC/USDT", "15m")

        call_input = mock_run.call_args[0][1]
        assert call_input["data_limit"] == DEFAULT_DATA_LIMIT

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_model_data_raises_actor_data_error(self, mock_run):
        mock_run.return_value = [{"bad": "data"}]

        from crypto_skill.kucoin import get_ohlcv

        with pytest.raises(ActorDataError):
            await get_ohlcv("BTC/USDT", "15m")


class TestGetRealtimePrice:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_extracts_price_from_candle(self, mock_run, sample_ohlcv_response):
        mock_run.return_value = [sample_ohlcv_response[0]]

        from crypto_skill.kucoin import get_realtime_price

        result = await get_realtime_price("BTC/USDT")

        assert isinstance(result, RealtimePrice)
        assert result.price == 65500.0  # close price
        assert result.symbol == "BTC/USDT"
        assert result.timestamp == 1710000000.0  # ms / 1000

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_empty_response_raises_data_error(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.kucoin import get_realtime_price

        with pytest.raises(ActorDataError, match="No data returned"):
            await get_realtime_price("BTC/USDT")

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_sends_data_limit_1(self, mock_run):
        mock_run.return_value = [
            {
                "timestamp": 1710000000000,
                "open": 65000.0,
                "high": 66000.0,
                "low": 64000.0,
                "close": 65500.0,
                "volume": 100.0,
                "symbol": "BTC/USDT",
            }
        ]

        from crypto_skill.kucoin import get_realtime_price

        await get_realtime_price("BTC/USDT")

        call_input = mock_run.call_args[0][1]
        assert call_input["data_limit"] == 1


class TestGetRealtimePriceErrors:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_candle_data_raises_data_error(self, mock_run):
        mock_run.return_value = [{"bad": "data"}]

        from crypto_skill.kucoin import get_realtime_price

        with pytest.raises(ActorDataError, match="Failed to parse"):
            await get_realtime_price("BTC/USDT")


class TestGetAllCoinsOhlcv:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_passes_empty_symbol(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.kucoin import get_all_coins_ohlcv

        await get_all_coins_ohlcv("1h")

        call_input = mock_run.call_args[0][1]
        assert call_input["symbol"] == ""

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_parsed_candles(self, mock_run, sample_ohlcv_response):
        mock_run.return_value = sample_ohlcv_response

        from crypto_skill.kucoin import get_all_coins_ohlcv

        result = await get_all_coins_ohlcv("1h", limit=50)

        assert len(result) == 2
        assert isinstance(result[0], OHLCVCandle)

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_uses_default_limit(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.kucoin import get_all_coins_ohlcv

        await get_all_coins_ohlcv("1h")

        call_input = mock_run.call_args[0][1]
        assert call_input["data_limit"] == DEFAULT_DATA_LIMIT
```

- [ ] **Step 4.2: Run tests to verify they fail**

Run: `pytest tests/test_kucoin.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crypto_skill.kucoin'`

- [ ] **Step 4.3: Implement kucoin.py**

```python
# src/crypto_skill/kucoin.py
from __future__ import annotations

from pydantic import ValidationError

from crypto_skill.client import run_actor_sync
from crypto_skill.constants import (
    DEFAULT_DATA_LIMIT,
    KUCOIN_ACTOR_ID,
    REALTIME_DATA_LIMIT,
    REALTIME_TIMEFRAME,
)
from crypto_skill.exceptions import ActorDataError
from crypto_skill.models import OHLCVCandle, RealtimePrice

MS_TO_SECONDS = 1000.0


async def get_ohlcv(
    symbol: str,
    timeframe: str,
    limit: int = DEFAULT_DATA_LIMIT,
) -> list[OHLCVCandle]:
    """Fetch OHLCV candlestick data from KuCoin."""
    actor_input = {"symbol": symbol, "timeframe": timeframe, "data_limit": limit}
    items = await run_actor_sync(KUCOIN_ACTOR_ID, actor_input)
    return _parse_candles(items)


async def get_realtime_price(symbol: str) -> RealtimePrice:
    """Fetch the current price for a cryptocurrency pair from KuCoin."""
    actor_input = {
        "symbol": symbol,
        "timeframe": REALTIME_TIMEFRAME,
        "data_limit": REALTIME_DATA_LIMIT,
    }
    items = await run_actor_sync(KUCOIN_ACTOR_ID, actor_input)

    if not items:
        raise ActorDataError(f"No data returned for {symbol}")

    try:
        candle = OHLCVCandle(
            **{**items[0], "timestamp": items[0]["timestamp"] / MS_TO_SECONDS}
        )
    except (ValidationError, TypeError, KeyError) as exc:
        raise ActorDataError(f"Failed to parse realtime price: {exc}") from exc

    return RealtimePrice(
        symbol=symbol,
        price=candle.close,
        timestamp=candle.timestamp,
    )


async def get_all_coins_ohlcv(
    timeframe: str,
    limit: int = DEFAULT_DATA_LIMIT,
) -> list[OHLCVCandle]:
    """Fetch OHLCV data for all available coins on KuCoin."""
    actor_input = {"symbol": "", "timeframe": timeframe, "data_limit": limit}
    items = await run_actor_sync(KUCOIN_ACTOR_ID, actor_input)
    return _parse_candles(items)


def _parse_candles(items: list[dict]) -> list[OHLCVCandle]:
    """Validate and convert raw candle dicts to OHLCVCandle models."""
    try:
        return [
            OHLCVCandle(
                **{**item, "timestamp": item.get("timestamp", 0) / MS_TO_SECONDS}
            )
            for item in items
        ]
    except (ValidationError, TypeError, KeyError) as exc:
        raise ActorDataError(f"Failed to parse OHLCV data: {exc}") from exc
```

- [ ] **Step 4.4: Run tests to verify they pass**

Run: `pytest tests/test_kucoin.py -v`
Expected: 11 PASSED

- [ ] **Step 4.5: Commit**

```bash
git add src/crypto_skill/kucoin.py tests/test_kucoin.py
git commit -m "feat(kucoin): add OHLCV, realtime price, and all-coins functions"
```

---

### Task 5: CoinGecko Module

**Files:**
- Create: `src/crypto_skill/coingecko.py`
- Create: `tests/test_coingecko.py`

- [ ] **Step 5.1: Write tests for coingecko functions**

```python
# tests/test_coingecko.py
from unittest.mock import AsyncMock, patch

import pytest

from crypto_skill.constants import COINGECKO_ACTOR_ID, DEFAULT_DATA_LIMIT
from crypto_skill.exceptions import ActorDataError
from crypto_skill.models import (
    CoinDetail,
    CryptoCategory,
    HistoricalData,
    MarketCoin,
    SimplePrice,
    TrendingCoin,
)

MODULE_PATH = "crypto_skill.coingecko.run_actor_sync"


class TestGetSimplePrices:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_simple_prices(self, mock_run, sample_simple_prices_response):
        mock_run.return_value = sample_simple_prices_response

        from crypto_skill.coingecko import get_simple_prices

        result = await get_simple_prices(["bitcoin", "ethereum"])

        assert len(result) == 2
        assert isinstance(result[0], SimplePrice)
        assert result[0].prices["usd"] == 93000.0

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_builds_correct_actor_input(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.coingecko import get_simple_prices

        await get_simple_prices(["bitcoin"], vs_currencies=["usd", "eur"])

        mock_run.assert_called_once_with(
            COINGECKO_ACTOR_ID,
            {
                "scrapeMode": "simple_prices",
                "coinIds": ["bitcoin"],
                "vsCurrencies": ["usd", "eur"],
            },
        )

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_default_vs_currencies(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.coingecko import get_simple_prices

        await get_simple_prices(["bitcoin"])

        call_input = mock_run.call_args[0][1]
        assert call_input["vsCurrencies"] == ["usd"]


class TestGetMarketData:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_market_coins(self, mock_run, sample_market_response):
        mock_run.return_value = sample_market_response

        from crypto_skill.coingecko import get_market_data

        result = await get_market_data()

        assert len(result) == 1
        assert isinstance(result[0], MarketCoin)
        assert result[0].current_price == 93000.0

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_builds_correct_actor_input_with_defaults(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.coingecko import get_market_data

        await get_market_data()

        mock_run.assert_called_once_with(
            COINGECKO_ACTOR_ID,
            {
                "scrapeMode": "market_data",
                "vsCurrency": "usd",
                "sortOrder": "market_cap_desc",
                "maxResults": DEFAULT_DATA_LIMIT,
            },
        )

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_passes_category_filter(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.coingecko import get_market_data

        await get_market_data(category="layer-1")

        call_input = mock_run.call_args[0][1]
        assert call_input["category"] == "layer-1"


class TestGetMarketDataErrors:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_data_raises_actor_data_error(self, mock_run):
        mock_run.return_value = [{"bad": "data"}]

        from crypto_skill.coingecko import get_market_data

        with pytest.raises(ActorDataError):
            await get_market_data()


class TestGetCoinDetail:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_coin_detail(self, mock_run, sample_coin_detail_response):
        mock_run.return_value = sample_coin_detail_response

        from crypto_skill.coingecko import get_coin_detail

        result = await get_coin_detail("bitcoin")

        assert isinstance(result, CoinDetail)
        assert result.id == "bitcoin"
        assert "Cryptocurrency" in result.categories

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_wraps_coin_id_in_list(self, mock_run):
        mock_run.return_value = [
            {
                "id": "bitcoin",
                "symbol": "btc",
                "name": "Bitcoin",
                "description": "test",
                "categories": [],
            }
        ]

        from crypto_skill.coingecko import get_coin_detail

        await get_coin_detail("bitcoin")

        call_input = mock_run.call_args[0][1]
        assert call_input["coinIds"] == ["bitcoin"]

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_include_details_false(self, mock_run):
        mock_run.return_value = [
            {
                "id": "bitcoin",
                "symbol": "btc",
                "name": "Bitcoin",
                "description": "test",
                "categories": [],
            }
        ]

        from crypto_skill.coingecko import get_coin_detail

        await get_coin_detail("bitcoin", include_details=False)

        call_input = mock_run.call_args[0][1]
        assert call_input["includeDetails"] is False

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_empty_response_raises_data_error(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.coingecko import get_coin_detail

        with pytest.raises(ActorDataError, match="No data returned"):
            await get_coin_detail("bitcoin")

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_data_raises_actor_data_error(self, mock_run):
        mock_run.return_value = [{"bad": "data"}]

        from crypto_skill.coingecko import get_coin_detail

        with pytest.raises(ActorDataError):
            await get_coin_detail("bitcoin")


class TestGetHistorical:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_historical_data(self, mock_run, sample_historical_response):
        mock_run.return_value = sample_historical_response

        from crypto_skill.coingecko import get_historical

        result = await get_historical("bitcoin", days=30)

        assert isinstance(result, HistoricalData)
        assert len(result.price_data) == 2
        assert result.price_change == 500.0

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_empty_response_raises_data_error(self, mock_run):
        mock_run.return_value = []

        from crypto_skill.coingecko import get_historical

        with pytest.raises(ActorDataError, match="No data returned"):
            await get_historical("bitcoin")

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_builds_correct_actor_input(self, mock_run):
        mock_run.return_value = [
            {
                "coin_id": "bitcoin",
                "price_data": [],
                "price_start": 0,
                "price_end": 0,
                "price_change": 0,
                "price_change_percentage": 0,
                "price_high": 0,
                "price_low": 0,
            }
        ]

        from crypto_skill.coingecko import get_historical

        await get_historical("bitcoin", days=90, vs_currency="eur")

        mock_run.assert_called_once_with(
            COINGECKO_ACTOR_ID,
            {
                "scrapeMode": "historical_data",
                "coinIds": ["bitcoin"],
                "days": 90,
                "vsCurrency": "eur",
            },
        )


class TestGetTrending:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_trending_coins(self, mock_run, sample_trending_response):
        mock_run.return_value = sample_trending_response

        from crypto_skill.coingecko import get_trending

        result = await get_trending()

        assert len(result) == 2
        assert isinstance(result[0], TrendingCoin)
        assert result[0].id == "pepe"


class TestGetCategories:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_categories(self, mock_run, sample_categories_response):
        mock_run.return_value = sample_categories_response

        from crypto_skill.coingecko import get_categories

        result = await get_categories()

        assert len(result) == 2
        assert isinstance(result[0], CryptoCategory)
        assert result[0].name == "DeFi"
```

- [ ] **Step 5.2: Run tests to verify they fail**

Run: `pytest tests/test_coingecko.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crypto_skill.coingecko'`

- [ ] **Step 5.3: Implement coingecko.py**

```python
# src/crypto_skill/coingecko.py
from __future__ import annotations

from pydantic import ValidationError

from crypto_skill.client import run_actor_sync
from crypto_skill.constants import (
    COINGECKO_ACTOR_ID,
    DEFAULT_DATA_LIMIT,
    DEFAULT_SORT_ORDER,
    DEFAULT_VS_CURRENCY,
)
from crypto_skill.exceptions import ActorDataError
from crypto_skill.models import (
    CoinDetail,
    CryptoCategory,
    HistoricalData,
    MarketCoin,
    SimplePrice,
    TrendingCoin,
)


async def get_simple_prices(
    coin_ids: list[str],
    vs_currencies: list[str] | None = None,
) -> list[SimplePrice]:
    """Fetch simple price data for multiple coins from CoinGecko."""
    currencies = vs_currencies if vs_currencies is not None else [DEFAULT_VS_CURRENCY]
    actor_input = {
        "scrapeMode": "simple_prices",
        "coinIds": coin_ids,
        "vsCurrencies": currencies,
    }
    items = await run_actor_sync(COINGECKO_ACTOR_ID, actor_input)
    return _parse_list(items, SimplePrice)


async def get_market_data(
    vs_currency: str = DEFAULT_VS_CURRENCY,
    category: str | None = None,
    max_results: int = DEFAULT_DATA_LIMIT,
) -> list[MarketCoin]:
    """Fetch market data for top cryptocurrencies from CoinGecko."""
    actor_input: dict = {
        "scrapeMode": "market_data",
        "vsCurrency": vs_currency,
        "sortOrder": DEFAULT_SORT_ORDER,
        "maxResults": max_results,
    }
    if category is not None:
        actor_input["category"] = category
    items = await run_actor_sync(COINGECKO_ACTOR_ID, actor_input)
    return _parse_list(items, MarketCoin)


async def get_coin_detail(
    coin_id: str,
    include_details: bool = True,
) -> CoinDetail:
    """Fetch detailed information for a specific coin from CoinGecko."""
    actor_input = {
        "scrapeMode": "coin_detail",
        "coinIds": [coin_id],
        "includeDetails": include_details,
    }
    items = await run_actor_sync(COINGECKO_ACTOR_ID, actor_input)
    return _extract_single(items, CoinDetail, coin_id)


async def get_historical(
    coin_id: str,
    days: int = 30,
    vs_currency: str = DEFAULT_VS_CURRENCY,
) -> HistoricalData:
    """Fetch historical price data for a coin from CoinGecko."""
    actor_input = {
        "scrapeMode": "historical_data",
        "coinIds": [coin_id],
        "days": days,
        "vsCurrency": vs_currency,
    }
    items = await run_actor_sync(COINGECKO_ACTOR_ID, actor_input)
    return _extract_single(items, HistoricalData, coin_id)


async def get_trending() -> list[TrendingCoin]:
    """Fetch currently trending cryptocurrencies from CoinGecko."""
    items = await run_actor_sync(COINGECKO_ACTOR_ID, {"scrapeMode": "trending"})
    return _parse_list(items, TrendingCoin)


async def get_categories() -> list[CryptoCategory]:
    """Fetch cryptocurrency categories from CoinGecko."""
    items = await run_actor_sync(COINGECKO_ACTOR_ID, {"scrapeMode": "categories"})
    return _parse_list(items, CryptoCategory)


def _parse_list[T](items: list[dict], model_class: type[T]) -> list[T]:
    """Validate a list of dicts against a Pydantic model."""
    try:
        return [model_class(**item) for item in items]
    except (ValidationError, TypeError) as exc:
        raise ActorDataError(f"Failed to parse {model_class.__name__}: {exc}") from exc


def _extract_single[T](items: list[dict], model_class: type[T], identifier: str) -> T:
    """Extract and validate a single item from the dataset result."""
    if not items:
        raise ActorDataError(f"No data returned for {identifier}")
    try:
        return model_class(**items[0])
    except (ValidationError, TypeError) as exc:
        raise ActorDataError(f"Failed to parse {model_class.__name__}: {exc}") from exc
```

- [ ] **Step 5.4: Run tests to verify they pass**

Run: `pytest tests/test_coingecko.py -v`
Expected: 17 PASSED

- [ ] **Step 5.5: Commit**

```bash
git add src/crypto_skill/coingecko.py tests/test_coingecko.py
git commit -m "feat(coingecko): add all 6 CoinGecko data functions"
```

---

### Task 6: Package Init and Full Test Suite

**Files:**
- Modify: `src/crypto_skill/__init__.py`
- Create: `tests/test_init.py`

- [ ] **Step 6.1: Write test for package exports**

```python
# tests/test_init.py
import crypto_skill


EXPECTED_EXPORTS = [
    "get_ohlcv",
    "get_realtime_price",
    "get_all_coins_ohlcv",
    "get_simple_prices",
    "get_market_data",
    "get_coin_detail",
    "get_historical",
    "get_trending",
    "get_categories",
    "CryptoSkillError",
    "ApifyAuthError",
    "ApifyActorError",
    "ApifyTimeoutError",
    "ActorDataError",
]


def test_all_exports_present():
    assert len(crypto_skill.__all__) == 14
    for name in EXPECTED_EXPORTS:
        assert name in crypto_skill.__all__, f"{name} missing from __all__"


def test_all_exports_importable():
    for name in EXPECTED_EXPORTS:
        assert hasattr(crypto_skill, name), f"{name} not importable from crypto_skill"
```

- [ ] **Step 6.2: Run test to verify it fails**

Run: `pytest tests/test_init.py -v`
Expected: FAIL — `AttributeError: module 'crypto_skill' has no attribute '__all__'`

- [ ] **Step 6.3: Implement __init__.py with __all__**

```python
# src/crypto_skill/__init__.py
from crypto_skill.coingecko import (
    get_categories,
    get_coin_detail,
    get_historical,
    get_market_data,
    get_simple_prices,
    get_trending,
)
from crypto_skill.exceptions import (
    ActorDataError,
    ApifyActorError,
    ApifyAuthError,
    ApifyTimeoutError,
    CryptoSkillError,
)
from crypto_skill.kucoin import get_all_coins_ohlcv, get_ohlcv, get_realtime_price

__all__ = [
    # KuCoin functions
    "get_ohlcv",
    "get_realtime_price",
    "get_all_coins_ohlcv",
    # CoinGecko functions
    "get_simple_prices",
    "get_market_data",
    "get_coin_detail",
    "get_historical",
    "get_trending",
    "get_categories",
    # Exceptions
    "CryptoSkillError",
    "ApifyAuthError",
    "ApifyActorError",
    "ApifyTimeoutError",
    "ActorDataError",
]
```

- [ ] **Step 6.4: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass (3 + 11 + 15 + 11 + 17 + 2 = 59 tests)

- [ ] **Step 6.5: Run lint and format**

```bash
ruff check src/crypto_skill/ tests/
ruff format --check src/crypto_skill/ tests/
```

Expected: All passed. If format issues, run `ruff format src/crypto_skill/ tests/` then re-check.

- [ ] **Step 6.6: Commit**

```bash
git add src/crypto_skill/__init__.py tests/test_init.py
git commit -m "feat(init): add package exports with __all__ (9 functions + 5 exceptions)"
```

---

### Task 7: Final Verification

- [ ] **Step 7.1: Run full test suite with coverage summary**

Run: `pytest tests/ -v --tb=short`
Expected: 59 tests PASSED, 0 FAILED

- [ ] **Step 7.2: Verify imports work as documented in spec**

```bash
python -c "
from crypto_skill import (
    get_ohlcv, get_realtime_price, get_all_coins_ohlcv,
    get_simple_prices, get_market_data, get_coin_detail,
    get_historical, get_trending, get_categories,
    CryptoSkillError, ApifyAuthError, ApifyActorError,
    ApifyTimeoutError, ActorDataError,
)
print(f'All 14 exports imported successfully')
"
```

Expected: `All 14 exports imported successfully`

- [ ] **Step 7.3: Final ruff and format check**

```bash
ruff check src/ tests/ && ruff format --check src/ tests/
```

Expected: No issues

- [ ] **Step 7.4: Commit any format fixes and tag**

```bash
git add -A
git status  # Verify only expected files
git commit -m "chore: final lint and format pass" --allow-empty
```
