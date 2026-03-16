import pytest


@pytest.fixture()
def apify_token_env(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "test-token-abc123")


@pytest.fixture()
def sample_ohlcv_response():
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
        }
    ]


@pytest.fixture()
def sample_coin_detail_response():
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "description": "A peer-to-peer electronic cash system",
            "categories": ["Cryptocurrency", "Layer 1"],
            "links": {"homepage": ["https://bitcoin.org"]},
            "genesis_date": "2009-01-03",
        }
    ]


@pytest.fixture()
def sample_historical_response():
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
        }
    ]


@pytest.fixture()
def sample_trending_response():
    return [
        {"id": "pepe", "symbol": "pepe", "name": "Pepe", "market_cap_rank": 25},
        {"id": "bonk", "symbol": "bonk", "name": "Bonk"},
    ]


@pytest.fixture()
def sample_categories_response():
    return [
        {"id": "defi", "name": "DeFi", "market_cap": 100000000000.0},
        {"id": "layer-1", "name": "Layer 1", "market_cap": 500000000000.0},
    ]


@pytest.fixture()
def sample_simple_prices_response():
    return [
        {"coin_id": "bitcoin", "prices": {"usd": 93000.0, "eur": 85000.0}},
        {"coin_id": "ethereum", "prices": {"usd": 3200.0, "eur": 2900.0}},
    ]
