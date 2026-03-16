import pytest

from crypto_skill.models import MarketCoin, OHLCVCandle, RealtimePrice


class TestOHLCVCandle:
    def test_valid_candle(self):
        candle = OHLCVCandle(
            date="2026-03-16 23:15:00",
            open=65000.0,
            high=66000.0,
            low=64000.0,
            close=65500.0,
            volume=1234.56,
            symbol="BTC/USDT",
        )
        assert candle.close == 65500.0
        assert candle.symbol == "BTC/USDT"
        assert candle.date == "2026-03-16 23:15:00"

    def test_symbol_defaults_to_empty(self):
        candle = OHLCVCandle(
            date="2026-03-16 23:15:00",
            open=65000.0,
            high=66000.0,
            low=64000.0,
            close=65500.0,
            volume=1234.56,
        )
        assert candle.symbol == ""

    def test_extra_fields_ignored(self):
        candle = OHLCVCandle(
            date="2026-03-16 23:15:00",
            open=65000.0,
            high=66000.0,
            low=64000.0,
            close=65500.0,
            volume=1234.56,
            extra_field="should be ignored",
        )
        assert not hasattr(candle, "extra_field")

    def test_missing_required_field_raises(self):
        with pytest.raises(ValueError):
            OHLCVCandle(
                date="2026-03-16 23:15:00",
                open=65000.0,
                high=66000.0,
                low=64000.0,
                volume=1234.56,
            )


class TestRealtimePrice:
    def test_valid_price(self):
        price = RealtimePrice(
            symbol="ETH/USDT",
            price=3200.50,
            date="2026-03-16 23:15:00",
        )
        assert price.price == 3200.50


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

    def test_extra_fields_ignored(self):
        coin = MarketCoin(
            id="bitcoin",
            symbol="btc",
            name="Bitcoin",
            current_price=93000.0,
            market_cap=1850000000000.0,
            market_cap_rank=1,
            total_volume=50000000000.0,
            image="https://example.com/btc.png",
            fully_diluted_valuation=2000000000000.0,
        )
        assert not hasattr(coin, "image")
