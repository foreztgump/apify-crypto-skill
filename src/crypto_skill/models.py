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
