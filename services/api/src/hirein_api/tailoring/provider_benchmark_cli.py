from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ValidationError

from hirein_api.tailoring.provider_benchmark_runner import (
    JsonTransport,
    SyntheticBenchmarkRun,
    UrllibJsonTransport,
    load_provider_secret,
    run_synthetic_benchmark_candidate,
)
from hirein_api.tailoring.provider_preview_cli import assert_synthetic_fixture
from hirein_api.tailoring.providers import (
    ProviderBenchmarkCandidate,
    load_provider_benchmark_registry,
)
from hirein_api.tailoring.rewrite import ResumeRewriteInput
from hirein_api.tailoring.schemas import ResumeTailoringPreviewResponse

DEFAULT_REGISTRY = Path("evals/tailoring/providers.json")
DEFAULT_PROMPT = Path("evals/tailoring/prompt-v2.md")
DEFAULT_INPUT = Path("evals/tailoring/fixtures/synthetic-rewrite-input.json")
DEFAULT_PREVIEW = Path("evals/tailoring/fixtures/synthetic-preview.json")
DEFAULT_REPORT = Path(".local-data/evals/tailoring/synthetic-live-report.json")


def _read_model[T: BaseModel](path: Path, model_type: type[T]) -> T:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return model_type.model_validate(payload)


def _candidate_key(candidate: ProviderBenchmarkCandidate) -> str:
    return f"{candidate.provider}/{candidate.model}"


def _select_candidates(
    all_candidates: list[ProviderBenchmarkCandidate],
    requested: list[str],
) -> list[ProviderBenchmarkCandidate]:
    by_key = {_candidate_key(candidate): candidate for candidate in all_candidates}
    missing = [key for key in requested if key not in by_key]
    if missing:
        raise ValueError(f"unknown benchmark candidate(s): {', '.join(missing)}")
    return [by_key[key] for key in requested]


def run_live_synthetic_benchmark(
    *,
    registry_path: Path,
    prompt_path: Path,
    input_path: Path,
    preview_path: Path,
    report_path: Path,
    requested_candidates: list[str],
    transport: JsonTransport | None = None,
    secret_loader: Callable[[str], str] = load_provider_secret,
) -> list[SyntheticBenchmarkRun]:
    assert_synthetic_fixture(input_path)
    assert_synthetic_fixture(preview_path)

    registry = load_provider_benchmark_registry(registry_path)
    selected = _select_candidates(registry.candidates, requested_candidates)
    prompt = prompt_path.read_text(encoding="utf-8")
    payload = _read_model(input_path, ResumeRewriteInput)
    preview = _read_model(preview_path, ResumeTailoringPreviewResponse)
    active_transport = transport or UrllibJsonTransport()

    runs: list[SyntheticBenchmarkRun] = []
    for candidate in selected:
        secret = secret_loader(candidate.provider)
        run = run_synthetic_benchmark_candidate(
            candidate=candidate,
            prompt=prompt,
            prompt_version="v2",
            payload=payload,
            preview=preview,
            secret=secret,
            transport=active_transport,
        )
        runs.append(run)
        print(
            f"run {candidate.provider}/{candidate.model}: "
            f"{run.status} {run.latency_ms}ms"
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            [run.model_dump(mode="json") for run in runs],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"report: {report_path}")
    return runs


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute paid provider calls only against committed synthetic HireIn "
            "fixtures and write a redacted local benchmark report."
        )
    )
    parser.add_argument(
        "--execute-network",
        action="store_true",
        help="Required acknowledgement that this command performs external API calls.",
    )
    parser.add_argument(
        "--candidate",
        action="append",
        required=True,
        help=(
            "Explicit provider/model key, e.g. openai/gpt-6-luna. "
            "Repeat to benchmark more than one candidate."
        ),
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if not args.execute_network:
        print(
            "error: --execute-network is required; no external request was sent",
            file=sys.stderr,
        )
        return 2

    try:
        runs = run_live_synthetic_benchmark(
            registry_path=args.registry,
            prompt_path=args.prompt,
            input_path=args.input,
            preview_path=args.preview,
            report_path=args.report,
            requested_candidates=args.candidate,
        )
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 1 if any(run.status == "FAILED" for run in runs) else 0
