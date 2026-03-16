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
        with pytest.raises(ValueError):
            OHLCVCandle(
                timestamp=1710000000.0,
                open=65000.0,
                high=66000.0,
                low=64000.0,
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
