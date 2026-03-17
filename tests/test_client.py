import httpx
import pytest
import respx

from crypto_skill.client import run_actor_sync
from crypto_skill.constants import APIFY_BASE_URL
from crypto_skill.exceptions import (
    ActorDataError,
    ApifyActorError,
    ApifyAuthError,
    ApifyTimeoutError,
)

ACTOR_ID = "test-user~test-actor"
EXPECTED_URL = f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/run-sync-get-dataset-items"


class TestRunActorSyncSuccess:
    @respx.mock
    async def test_returns_dataset_items(self, apify_token_env):
        items = [{"key": "value"}]
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(200, json=items))
        result = await run_actor_sync(ACTOR_ID, {"input": "data"})
        assert result == items

    @respx.mock
    async def test_sends_auth_header(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(200, json=[]))
        await run_actor_sync(ACTOR_ID, {})
        request = respx.calls.last.request
        assert request.headers["authorization"] == "Bearer test-token-abc123"

    @respx.mock
    async def test_sends_json_body(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(200, json=[]))
        await run_actor_sync(ACTOR_ID, {"symbol": "BTC/USDT"})
        request = respx.calls.last.request
        assert b'"symbol"' in request.content
        assert b'"BTC/USDT"' in request.content


class TestRunActorSyncAuthErrors:
    async def test_missing_token_raises_auth_error(self, monkeypatch):
        monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
        with pytest.raises(ApifyAuthError, match="APIFY_API_TOKEN"):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_401_raises_auth_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(401))
        with pytest.raises(ApifyAuthError):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_403_raises_auth_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(403))
        with pytest.raises(ApifyAuthError):
            await run_actor_sync(ACTOR_ID, {})


class TestRunActorSyncTimeoutErrors:
    @respx.mock
    async def test_408_raises_timeout_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(408))
        with pytest.raises(ApifyTimeoutError):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_httpx_timeout_raises_timeout_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(side_effect=httpx.ReadTimeout("timed out"))
        with pytest.raises(ApifyTimeoutError):
            await run_actor_sync(ACTOR_ID, {})


class TestRunActorSyncActorErrors:
    @respx.mock
    async def test_500_raises_actor_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(500))
        with pytest.raises(ApifyActorError):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_429_raises_actor_error_with_rate_limit_message(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(429))
        with pytest.raises(ApifyActorError, match="rate limited"):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_connection_error_raises_actor_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(side_effect=httpx.ConnectError("refused"))
        with pytest.raises(ApifyActorError):
            await run_actor_sync(ACTOR_ID, {})


class TestRunActorSyncDataErrors:
    @respx.mock
    async def test_non_list_response_raises_data_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(return_value=httpx.Response(200, json={"error": "bad"}))
        with pytest.raises(ActorDataError, match="Expected list"):
            await run_actor_sync(ACTOR_ID, {})

    @respx.mock
    async def test_invalid_json_raises_data_error(self, apify_token_env):
        respx.post(EXPECTED_URL).mock(
            return_value=httpx.Response(
                200, content=b"not json", headers={"content-type": "text/html"}
            )
        )
        with pytest.raises(ActorDataError, match="Invalid JSON"):
            await run_actor_sync(ACTOR_ID, {})


class TestRunActorSyncExceptionChaining:
    @respx.mock
    async def test_timeout_preserves_cause(self, apify_token_env):
        original = httpx.ReadTimeout("timed out")
        respx.post(EXPECTED_URL).mock(side_effect=original)
        with pytest.raises(ApifyTimeoutError) as exc_info:
            await run_actor_sync(ACTOR_ID, {})
        assert exc_info.value.__cause__ is original

    @respx.mock
    async def test_connection_error_preserves_cause(self, apify_token_env):
        original = httpx.ConnectError("refused")
        respx.post(EXPECTED_URL).mock(side_effect=original)
        with pytest.raises(ApifyActorError) as exc_info:
            await run_actor_sync(ACTOR_ID, {})
        assert exc_info.value.__cause__ is original
