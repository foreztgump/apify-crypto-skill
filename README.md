# Apify Crypto Skill

Crypto data skills for AI agents — async Python functions wrapping Apify actors for KuCoin OHLCV and CoinGecko market data.

## Installation

```bash
pip install -e .
```

## Setup

Set your Apify API token as an environment variable:

```bash
export APIFY_API_TOKEN=your_apify_token_here
```

## Usage

```python
import asyncio
from crypto_skill import get_ohlcv, get_realtime_price, get_market_data, get_trending

async def main():
    # KuCoin OHLCV candlestick data
    candles = await get_ohlcv("BTC/USDT", "15m", limit=10)
    for c in candles:
        print(f"{c.date} | O={c.open} H={c.high} L={c.low} C={c.close}")

    # Current price
    price = await get_realtime_price("ETH/USDT")
    print(f"{price.symbol} = ${price.price:,.2f}")

    # CoinGecko market data (top coins)
    coins = await get_market_data(max_results=5)
    for c in coins:
        print(f"{c.name} ({c.symbol}) ${c.current_price:,.2f} | Rank #{c.market_cap_rank}")

    # Trending coins
    trending = await get_trending()
    for c in trending[:5]:
        print(f"{c.name} 24h: {c.price_change_percentage_24h:.2f}%")

asyncio.run(main())
```

## API Reference

### KuCoin Functions (via Crypto Data Scraper actor)

| Function | Description | Returns |
|----------|-------------|---------|
| `get_ohlcv(symbol, timeframe, limit=100)` | OHLCV candlestick data | `list[OHLCVCandle]` |
| `get_realtime_price(symbol)` | Current price for a pair | `RealtimePrice` |
| `get_all_coins_ohlcv(timeframe, limit=100)` | OHLCV for all coins | `list[OHLCVCandle]` |

**Supported timeframes:** `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`

### CoinGecko Functions (via Crypto Intelligence actor)

| Function | Description | Returns |
|----------|-------------|---------|
| `get_simple_prices(coin_ids, vs_currencies=None)` | Price data for specific coins | `list[MarketCoin]` |
| `get_market_data(vs_currency="usd", category=None, max_results=100)` | Top coins by market cap | `list[MarketCoin]` |
| `get_coin_detail(coin_id, include_details=True)` | Single coin data | `MarketCoin` |
| `get_historical(coin_id, days=30, vs_currency="usd")` | Coin data (historical mode) | `MarketCoin` |
| `get_trending()` | Trending cryptocurrencies | `list[MarketCoin]` |
| `get_categories()` | Coins by categories | `list[MarketCoin]` |

### Models

**OHLCVCandle** — `date`, `open`, `high`, `low`, `close`, `volume`, `symbol`

**RealtimePrice** — `symbol`, `price`, `date`

**MarketCoin** — `id`, `symbol`, `name`, `current_price`, `market_cap`, `market_cap_rank`, `total_volume`, `high_24h`, `low_24h`, `price_change_24h`, `price_change_percentage_24h`, `ath`, `atl`, `last_updated`, and more

### Exceptions

All exceptions inherit from `CryptoSkillError`:

| Exception | When |
|-----------|------|
| `ApifyAuthError` | Missing or invalid `APIFY_API_TOKEN` |
| `ApifyActorError` | Actor run failed, rate limited, or connection error |
| `ApifyTimeoutError` | Actor run exceeded 300s timeout |
| `ActorDataError` | Response doesn't match expected schema |

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/
ruff format src/ tests/
```

## Apify Actors

- **Crypto Data Scraper** (`moving_beacon-owner1/my-actor-14`) — KuCoin exchange data
- **CoinGecko Crypto Intelligence** (`benthepythondev/crypto-intelligence`) — CoinGecko market data
