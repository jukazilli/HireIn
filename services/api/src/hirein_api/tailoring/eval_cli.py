from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from hirein_api.tailoring.evals import (
    HumanRewriteReview,
    ResumeRewriteEvalReport,
    evaluate_resume_rewrite,
)
from hirein_api.tailoring.rewrite import ResumeRewriteCandidate
from hirein_api.tailoring.schemas import ResumeTailoringPreviewResponse

DEFAULT_PREVIEW = Path(".local-data/evals/tailoring/preview.json")
DEFAULT_CANDIDATES_DIR = Path(".local-data/evals/tailoring/candidates")
DEFAULT_REVIEWS_DIR = Path(".local-data/evals/tailoring/reviews")
DEFAULT_REPORT_JSON = Path(".local-data/evals/tailoring/report.json")
DEFAULT_REPORT_MD = Path(".local-data/evals/tailoring/report.md")


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _load_review(path: Path) -> HumanRewriteReview | None:
    if not path.exists():
        return None
    return HumanRewriteReview.model_validate(_read_json(path))


def evaluate_directory(
    preview_path: Path,
    candidates_dir: Path,
    reviews_dir: Path,
) -> list[ResumeRewriteEvalReport]:
    preview = ResumeTailoringPreviewResponse.model_validate(_read_json(preview_path))
    if not candidates_dir.exists():
        raise FileNotFoundError(f"candidates directory does not exist: {candidates_dir}")

    candidate_paths = sorted(candidates_dir.glob("*.json"))
    if not candidate_paths:
        raise ValueError(f"no candidate JSON files found in {candidates_dir}")

    reports: list[ResumeRewriteEvalReport] = []
    for path in candidate_paths:
        candidate = ResumeRewriteCandidate.model_validate(_read_json(path))
        review = _load_review(reviews_dir / path.name)
        report = evaluate_resume_rewrite(preview, candidate, review)
        reports.append(report)
        print(
            f"eval {path.name}: structural={report.metrics.structural_pass} "
            f"coverage={report.metrics.evidence_coverage:.2%} "
            f"anchor={report.metrics.average_anchor_overlap:.2%}"
        )
    return reports


def _markdown(reports: list[ResumeRewriteEvalReport]) -> str:
    lines = [
        "# HireIn — Resume Rewriter Eval",
        "",
        "## Candidates",
        "",
        (
            "| Provider | Model | Prompt | Structural | Evidence coverage | "
            "Anchor overlap | Human factual | Human usefulness |"
        ),
        "|---|---|---|---|---:|---:|---:|---:|",
    ]

    for report in reports:
        human = report.human_review
        lines.append(
            "| "
            f"{report.provider} | {report.model} | {report.prompt_version} | "
            f"{'PASS' if report.metrics.structural_pass else 'FAIL'} | "
            f"{report.metrics.evidence_coverage:.1%} | "
            f"{report.metrics.average_anchor_overlap:.1%} | "
            f"{human.factual_precision if human else '—'} | "
            f"{human.usefulness if human else '—'} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "- Structural PASS only proves references and targets stay inside "
                "the approved boundary."
            ),
            (
                "- Anchor overlap is diagnostic and must not be treated as proof "
                "of factual correctness."
            ),
            (
                "- Human factual precision must be 5/5 with zero unsupported claims "
                "to pass the human gate."
            ),
            "- This report intentionally does not select a winning provider.",
            "",
        ]
    )
    return "\n".join(lines)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate structured resume rewrite candidates against an approved preview."
    )
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    parser.add_argument("--candidates-dir", type=Path, default=DEFAULT_CANDIDATES_DIR)
    parser.add_argument("--reviews-dir", type=Path, default=DEFAULT_REVIEWS_DIR)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        reports = evaluate_directory(
            args.preview,
            args.candidates_dir,
            args.reviews_dir,
        )
        _write_json(
            args.report_json,
            [report.model_dump(mode="json") for report in reports],
        )
        args.report_md.parent.mkdir(parents=True, exist_ok=True)
        args.report_md.write_text(_markdown(reports), encoding="utf-8")
        print(f"report: {args.report_json}")
        print(f"report: {args.report_md}")
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
