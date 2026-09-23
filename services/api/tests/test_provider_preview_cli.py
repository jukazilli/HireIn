from __future__ import annotations

import json
from pathlib import Path

import pytest

from hirein_api.tailoring.provider_preview_cli import render_request_previews

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_ROOT = REPO_ROOT / "evals" / "tailoring"


def test_provider_preview_renders_all_registered_synthetic_requests(
    tmp_path: Path,
) -> None:
    written = render_request_previews(
        registry_path=EVAL_ROOT / "providers.json",
        prompt_path=EVAL_ROOT / "prompt-v2.md",
        input_path=EVAL_ROOT / "fixtures" / "synthetic-rewrite-input.json",
        output_dir=tmp_path,
    )

    assert len(written) == 4
    assert {path.name for path in written} == {
        "openai-gpt-6-luna.json",
        "openai-gpt-6-sol.json",
        "anthropic-claude-sonnet-5.json",
        "google-gemini-3.8-flash.json",
    }

    for path in written:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["method"] == "POST"
        assert "auth_header" in payload
        assert "body" in payload

        serialized = path.read_text(encoding="utf-8")
        assert "Bearer " not in serialized
        assert "OPENAI_API_KEY" not in serialized
        assert "ANTHROPIC_API_KEY" not in serialized
        assert "GEMINI_API_KEY" not in serialized


def test_provider_preview_rejects_non_fixture_input(tmp_path: Path) -> None:
    real_like_input = tmp_path / "candidate.json"
    real_like_input.write_text(
        (EVAL_ROOT / "fixtures" / "synthetic-rewrite-input.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="only accepts committed synthetic fixtures",
    ):
        render_request_previews(
            registry_path=EVAL_ROOT / "providers.json",
            prompt_path=EVAL_ROOT / "prompt-v2.md",
            input_path=real_like_input,
            output_dir=tmp_path / "output",
        )
