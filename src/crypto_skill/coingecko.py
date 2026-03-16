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
    coin_ids: list[str], vs_currencies: list[str] | None = None
) -> list[SimplePrice]:
    """Fetch simple price data for multiple coins from CoinGecko."""
    currencies = vs_currencies if vs_currencies is not None else [DEFAULT_VS_CURRENCY]
    actor_input = {"scrapeMode": "simple_prices", "coinIds": coin_ids, "vsCurrencies": currencies}
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


async def get_coin_detail(coin_id: str, include_details: bool = True) -> CoinDetail:
    """Fetch detailed information for a specific coin from CoinGecko."""
    actor_input = {
        "scrapeMode": "coin_detail",
        "coinIds": [coin_id],
        "includeDetails": include_details,
    }
    items = await run_actor_sync(COINGECKO_ACTOR_ID, actor_input)
    return _extract_single(items, CoinDetail, coin_id)


async def get_historical(
    coin_id: str, days: int = 30, vs_currency: str = DEFAULT_VS_CURRENCY
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
