from hirein_api.security import valid_backend_token, valid_ingestion_token


def test_backend_token_is_optional_when_not_configured() -> None:
    assert valid_backend_token(None, None) is True
    assert valid_backend_token(None, "anything") is True


def test_backend_token_rejects_missing_or_wrong_value() -> None:
    assert valid_backend_token("expected-secret", None) is False
    assert valid_backend_token("expected-secret", "wrong-secret") is False


def test_backend_token_accepts_exact_match() -> None:
    assert valid_backend_token("expected-secret", "expected-secret") is True


def test_ingestion_token_is_closed_when_not_configured() -> None:
    assert valid_ingestion_token(None, None) is False
    assert valid_ingestion_token(None, "anything") is False


def test_ingestion_token_rejects_missing_or_wrong_value() -> None:
    assert valid_ingestion_token("expected-ingestion-secret", None) is False
    assert (
        valid_ingestion_token("expected-ingestion-secret", "wrong-ingestion-secret")
        is False
    )


def test_ingestion_token_accepts_exact_match() -> None:
    assert (
        valid_ingestion_token(
            "expected-ingestion-secret",
            "expected-ingestion-secret",
        )
        is True
    )
