from unittest.mock import AsyncMock, patch

import pytest

from crypto_skill.constants import COINGECKO_ACTOR_ID, DEFAULT_DATA_LIMIT, DEFAULT_SORT_ORDER
from crypto_skill.exceptions import ActorDataError
from crypto_skill.models import MarketCoin

MODULE_PATH = "crypto_skill.coingecko.run_actor_sync"


class TestGetSimplePrices:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_market_coins(self, mock_run, sample_market_response):
        mock_run.return_value = sample_market_response
        from crypto_skill.coingecko import get_simple_prices

        result = await get_simple_prices(["bitcoin"])
        assert len(result) == 1
        assert isinstance(result[0], MarketCoin)
        assert result[0].current_price == 93000.0

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_builds_correct_actor_input(self, mock_run):
        mock_run.return_value = []
        from crypto_skill.coingecko import get_simple_prices

        await get_simple_prices(["bitcoin"], vs_currencies=["usd", "eur"])
        mock_run.assert_called_once_with(
            COINGECKO_ACTOR_ID,
            {"scrapeMode": "simple_prices", "coinIds": ["bitcoin"], "vsCurrencies": ["usd", "eur"]},
        )

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_default_vs_currencies(self, mock_run):
        mock_run.return_value = []
        from crypto_skill.coingecko import get_simple_prices

        await get_simple_prices(["bitcoin"])
        call_input = mock_run.call_args[0][1]
        assert call_input["vsCurrencies"] == ["usd"]

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_data_raises_actor_data_error(self, mock_run, bad_actor_response):
        mock_run.return_value = bad_actor_response
        from crypto_skill.coingecko import get_simple_prices

        with pytest.raises(ActorDataError):
            await get_simple_prices(["bitcoin"])


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
                "sortOrder": DEFAULT_SORT_ORDER,
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

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_data_raises_actor_data_error(self, mock_run, bad_actor_response):
        mock_run.return_value = bad_actor_response
        from crypto_skill.coingecko import get_market_data

        with pytest.raises(ActorDataError):
            await get_market_data()


class TestGetCoinDetail:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_market_coin(self, mock_run, sample_market_response):
        mock_run.return_value = sample_market_response
        from crypto_skill.coingecko import get_coin_detail

        result = await get_coin_detail("bitcoin")
        assert isinstance(result, MarketCoin)
        assert result.id == "bitcoin"

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_wraps_coin_id_in_list(self, mock_run, sample_market_response):
        mock_run.return_value = sample_market_response
        from crypto_skill.coingecko import get_coin_detail

        await get_coin_detail("bitcoin")
        call_input = mock_run.call_args[0][1]
        assert call_input["coinIds"] == ["bitcoin"]

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_include_details_false(self, mock_run, sample_market_response):
        mock_run.return_value = sample_market_response
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
    async def test_invalid_data_raises_actor_data_error(self, mock_run, bad_actor_response):
        mock_run.return_value = bad_actor_response
        from crypto_skill.coingecko import get_coin_detail

        with pytest.raises(ActorDataError):
            await get_coin_detail("bitcoin")


class TestGetHistorical:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_market_coin(self, mock_run, sample_market_response):
        mock_run.return_value = sample_market_response
        from crypto_skill.coingecko import get_historical

        result = await get_historical("bitcoin", days=30)
        assert isinstance(result, MarketCoin)

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_empty_response_raises_data_error(self, mock_run):
        mock_run.return_value = []
        from crypto_skill.coingecko import get_historical

        with pytest.raises(ActorDataError, match="No data returned"):
            await get_historical("bitcoin")

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_builds_correct_actor_input(self, mock_run, sample_market_response):
        mock_run.return_value = sample_market_response
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

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_data_raises_actor_data_error(self, mock_run, bad_actor_response):
        mock_run.return_value = bad_actor_response
        from crypto_skill.coingecko import get_historical

        with pytest.raises(ActorDataError):
            await get_historical("bitcoin")


class TestGetTrending:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_market_coins(self, mock_run, sample_market_response):
        mock_run.return_value = sample_market_response
        from crypto_skill.coingecko import get_trending

        result = await get_trending()
        assert len(result) == 1
        assert isinstance(result[0], MarketCoin)

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_data_raises_actor_data_error(self, mock_run, bad_actor_response):
        mock_run.return_value = bad_actor_response
        from crypto_skill.coingecko import get_trending

        with pytest.raises(ActorDataError):
            await get_trending()


class TestGetCategories:
    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_returns_market_coins(self, mock_run, sample_market_response):
        mock_run.return_value = sample_market_response
        from crypto_skill.coingecko import get_categories

        result = await get_categories()
        assert len(result) == 1
        assert isinstance(result[0], MarketCoin)

    @patch(MODULE_PATH, new_callable=AsyncMock)
    async def test_invalid_data_raises_actor_data_error(self, mock_run, bad_actor_response):
        mock_run.return_value = bad_actor_response
        from crypto_skill.coingecko import get_categories

        with pytest.raises(ActorDataError):
            await get_categories()
