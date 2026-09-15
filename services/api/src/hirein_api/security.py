from __future__ import annotations

from hmac import compare_digest


def valid_backend_token(configured: str | None, provided: str | None) -> bool:
    if configured is None:
        return True
    if not provided:
        return False
    return compare_digest(provided, configured)
