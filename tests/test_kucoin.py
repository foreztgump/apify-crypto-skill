from unittest.mock import AsyncMock, patch

import pytest

from crypto_skill.constants import DEFAULT_DATA_LIMIT, KUCOIN_ACTOR_ID
from crypto_skill.exceptions import ActorDataError
from crypto_skill.models import OHLCVCandle, RealtimePrice

MODULE_PATH = "crypto_skill.kucoin.run_actor_sync"


class TestGetOhlcv:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_candles_with_converted_timestamps(self, mock_run, sample_ohlcv_response):
        mock_run.return_value = sample_ohlcv_response
        from crypto_skill.kucoin import get_ohlcv

        result = await get_ohlcv("BTC/USDT", "15m")
        assert len(result) == 2
        assert isinstance(result[0], OHLCVCandle)
        assert result[0].timestamp == 1710000000.0
        assert result[0].close == 65500.0

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_builds_correct_actor_input(self, mock_run):
        mock_run.return_value = []
        from crypto_skill.kucoin import get_ohlcv

        await get_ohlcv("ETH/USDT", "1h", limit=50)
        mock_run.assert_called_once_with(
            KUCOIN_ACTOR_ID, {"symbol": "ETH/USDT", "timeframe": "1h", "data_limit": 50}
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
        assert result.price == 65500.0
        assert result.symbol == "BTC/USDT"
        assert result.timestamp == 1710000000.0

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

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_data_raises_actor_data_error(self, mock_run):
        mock_run.return_value = [{"bad": "data"}]
        from crypto_skill.kucoin import get_all_coins_ohlcv

        with pytest.raises(ActorDataError):
            await get_all_coins_ohlcv("1h")
