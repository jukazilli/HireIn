from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from hirein_api.tailoring.provider_adapters import build_provider_request
from hirein_api.tailoring.providers import load_provider_benchmark_registry
from hirein_api.tailoring.rewrite import ResumeRewriteInput

DEFAULT_REGISTRY = Path("evals/tailoring/providers.json")
DEFAULT_PROMPT = Path("evals/tailoring/prompt-v2.md")
DEFAULT_INPUT = Path("evals/tailoring/fixtures/synthetic-rewrite-input.json")
DEFAULT_OUTPUT_DIR = Path(".local-data/evals/tailoring/provider-requests")
SYNTHETIC_ROOT = Path("evals/tailoring/fixtures")


def _read_input(path: Path) -> ResumeRewriteInput:
    with path.open(encoding="utf-8") as handle:
        return ResumeRewriteInput.model_validate(json.load(handle))


def _assert_synthetic_fixture(path: Path) -> None:
    resolved = path.resolve()
    fixture_root = SYNTHETIC_ROOT.resolve()
    if not resolved.is_relative_to(fixture_root):
        raise ValueError(
            "provider request preview only accepts committed synthetic fixtures"
        )


def render_request_previews(
    *,
    registry_path: Path,
    prompt_path: Path,
    input_path: Path,
    output_dir: Path,
) -> list[Path]:
    _assert_synthetic_fixture(input_path)
    registry = load_provider_benchmark_registry(registry_path)
    prompt = prompt_path.read_text(encoding="utf-8")
    payload = _read_input(input_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for candidate in registry.candidates:
        request = build_provider_request(
            provider=candidate.provider,
            model=candidate.model,
            prompt=prompt,
            payload=payload,
        )
        filename = f"{candidate.provider}-{candidate.model}.json"
        path = output_dir / filename
        path.write_text(
            json.dumps(
                request.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        written.append(path)
        print(f"preview {candidate.provider}/{candidate.model}: {path}")

    return written


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render network-free provider request templates from the committed "
            "synthetic HireIn fixture."
        )
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        render_request_previews(
            registry_path=args.registry,
            prompt_path=args.prompt,
            input_path=args.input,
            output_dir=args.output_dir,
        )
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
