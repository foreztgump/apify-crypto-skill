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
