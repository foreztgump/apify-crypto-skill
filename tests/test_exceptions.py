from crypto_skill.exceptions import (
    ActorDataError,
    ApifyActorError,
    ApifyAuthError,
    ApifyTimeoutError,
    CryptoSkillError,
)


def test_all_exceptions_inherit_from_base():
    assert issubclass(ApifyAuthError, CryptoSkillError)
    assert issubclass(ApifyActorError, CryptoSkillError)
    assert issubclass(ApifyTimeoutError, CryptoSkillError)
    assert issubclass(ActorDataError, CryptoSkillError)


def test_base_inherits_from_exception():
    assert issubclass(CryptoSkillError, Exception)


def test_exception_message():
    err = ApifyActorError("run failed")
    assert str(err) == "run failed"
