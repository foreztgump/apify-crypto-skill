import pytest


@pytest.fixture()
def apify_token_env(monkeypatch):
    """Set APIFY_API_TOKEN env var for tests."""
    monkeypatch.setenv("APIFY_API_TOKEN", "test-token-abc123")


@pytest.fixture()
def sample_ohlcv_response():
    """Sample KuCoin OHLCV dataset items (actual actor format: capitalized keys, Date string)."""
    return [
        {
            "Date": "2026-03-16 23:15:00",
            "Open": 65000.0,
            "High": 66000.0,
            "Low": 64000.0,
            "Close": 65500.0,
            "Volume": 1234.56,
        },
        {
            "Date": "2026-03-16 23:30:00",
            "Open": 65500.0,
            "High": 66500.0,
            "Low": 65000.0,
            "Close": 66000.0,
            "Volume": 2345.67,
        },
    ]


@pytest.fixture()
def sample_market_response():
    """Sample CoinGecko market data (used by all CoinGecko modes)."""
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
def bad_actor_response():
    """Invalid actor response data for error-path tests."""
    return [{"bad": "data"}]
