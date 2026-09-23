from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from hirein_api.tailoring.provider_benchmark_cli import (
    main,
    run_live_synthetic_benchmark,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_ROOT = REPO_ROOT / "evals" / "tailoring"
FIXTURES = EVAL_ROOT / "fixtures"
CREDENTIAL_MARKER = "fixture-credential-value"


class FakeTransport:
    def post_json(
        self,
        *,
        endpoint: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        assert endpoint == "https://api.openai.com/v1/responses"
        assert headers["Authorization"] == f"Bearer {CREDENTIAL_MARKER}"
        assert body["store"] is False
        return {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {
                                    "blocks": [
                                        {
                                            "section": "SUMMARY",
                                            "text": (
                                                "Atuação com levantamento de requisitos "
                                                "e conhecimento básico de SQL."
                                            ),
                                            "source_evidence_ids": [
                                                "22222222-2222-2222-2222-222222222222",
                                                "11111111-1111-1111-1111-111111111111",
                                            ],
                                            "target_experience_id": None,
                                        }
                                    ]
                                }
                            ),
                        }
                    ],
                }
            ],
            "usage": {
                "input_tokens": 100,
                "input_tokens_details": {"cached_tokens": 0},
                "output_tokens": 50,
                "output_tokens_details": {"reasoning_tokens": 10},
            },
        }


def test_live_benchmark_writes_redacted_report_with_injected_transport(
    tmp_path: Path,
) -> None:
    report = tmp_path / "report.json"

    runs = run_live_synthetic_benchmark(
        registry_path=EVAL_ROOT / "providers.json",
        prompt_path=EVAL_ROOT / "prompt-v2.md",
        input_path=FIXTURES / "synthetic-rewrite-input.json",
        preview_path=FIXTURES / "synthetic-preview.json",
        report_path=report,
        requested_candidates=["openai/gpt-6-luna"],
        transport=FakeTransport(),
        secret_loader=lambda provider: CREDENTIAL_MARKER,
    )

    assert len(runs) == 1
    assert runs[0].status == "SUCCESS"
    serialized = report.read_text(encoding="utf-8")
    assert CREDENTIAL_MARKER not in serialized
    assert "Bearer " not in serialized
    assert "instructions" not in serialized
    assert '"structural_pass": true' in serialized


def test_cli_requires_explicit_network_acknowledgement(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "provider_benchmark.py",
            "--candidate",
            "openai/gpt-6-luna",
        ],
    )

    assert main() == 2
