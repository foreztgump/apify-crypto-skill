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
    symbol: str, timeframe: str, limit: int = DEFAULT_DATA_LIMIT
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
        candle = OHLCVCandle(**{**items[0], "timestamp": items[0]["timestamp"] / MS_TO_SECONDS})
    except (ValidationError, TypeError, KeyError) as exc:
        raise ActorDataError(f"Failed to parse realtime price: {exc}") from exc

    return RealtimePrice(symbol=symbol, price=candle.close, timestamp=candle.timestamp)


async def get_all_coins_ohlcv(timeframe: str, limit: int = DEFAULT_DATA_LIMIT) -> list[OHLCVCandle]:
    """Fetch OHLCV data for all available coins on KuCoin."""
    actor_input = {"symbol": "", "timeframe": timeframe, "data_limit": limit}
    items = await run_actor_sync(KUCOIN_ACTOR_ID, actor_input)
    return _parse_candles(items)


def _parse_candles(items: list[dict]) -> list[OHLCVCandle]:
    """Validate and convert raw candle dicts to OHLCVCandle models."""
    try:
        return [
            OHLCVCandle(**{**item, "timestamp": item["timestamp"] / MS_TO_SECONDS})
            for item in items
        ]
    except (ValidationError, TypeError, KeyError) as exc:
        raise ActorDataError(f"Failed to parse OHLCV data: {exc}") from exc
