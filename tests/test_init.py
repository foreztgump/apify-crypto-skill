import crypto_skill

EXPECTED_EXPORTS = [
    "get_ohlcv",
    "get_realtime_price",
    "get_all_coins_ohlcv",
    "get_simple_prices",
    "get_market_data",
    "get_coin_detail",
    "get_historical",
    "get_trending",
    "get_categories",
    "CryptoSkillError",
    "ApifyAuthError",
    "ApifyActorError",
    "ApifyTimeoutError",
    "ActorDataError",
]


def test_all_exports_present():
    assert len(crypto_skill.__all__) == len(EXPECTED_EXPORTS)
    for name in EXPECTED_EXPORTS:
        assert name in crypto_skill.__all__, f"{name} missing from __all__"


def test_all_exports_importable():
    for name in EXPECTED_EXPORTS:
        assert hasattr(crypto_skill, name), f"{name} not importable from crypto_skill"
