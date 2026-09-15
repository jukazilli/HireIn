from hirein_api.security import valid_backend_token


def test_backend_token_is_optional_when_not_configured() -> None:
    assert valid_backend_token(None, None) is True
    assert valid_backend_token(None, "anything") is True


def test_backend_token_rejects_missing_or_wrong_value() -> None:
    assert valid_backend_token("expected-secret", None) is False
    assert valid_backend_token("expected-secret", "wrong-secret") is False


def test_backend_token_accepts_exact_match() -> None:
    assert valid_backend_token("expected-secret", "expected-secret") is True
