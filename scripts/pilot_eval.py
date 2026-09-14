from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hirein_api.evals.ranking import RankingSample, calculate_ranking_metrics, rank_samples

DEFAULT_JOBS_DIR = Path(".local-data/jobs")
DEFAULT_LABELS_PATH = Path(".local-data/evals/matching-labels.json")
DEFAULT_MANIFEST_PATH = Path(".local-data/evals/import-manifest.json")
DEFAULT_REPORT_JSON = Path(".local-data/evals/matching-report.json")
DEFAULT_REPORT_MD = Path(".local-data/evals/matching-report.md")


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _request_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        parsed: Any
        try:
            parsed = json.loads(body) if body else None
        except json.JSONDecodeError:
            parsed = body
        return exc.code, parsed


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "jobs": {}}
    manifest = _read_json(path)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("jobs"), dict):
        raise ValueError(f"invalid manifest format: {path}")
    return manifest


def import_jobs(api_base: str, jobs_dir: Path, manifest_path: Path) -> dict[str, Any]:
    if not jobs_dir.exists():
        raise FileNotFoundError(
            f"jobs directory does not exist: {jobs_dir}. Create local JSON job files first."
        )

    manifest = _load_manifest(manifest_path)
    manifest["api_base"] = api_base.rstrip("/")
    manifest["updated_at"] = datetime.now(UTC).isoformat()
    jobs: dict[str, Any] = manifest["jobs"]

    job_files = sorted(jobs_dir.glob("*.json"))
    if not job_files:
        raise ValueError(f"no .json job files found in {jobs_dir}")

    imported = 0
    skipped = 0
    for path in job_files:
        key = path.name
        if key in jobs and jobs[key].get("job_id"):
            skipped += 1
            print(f"skip  {key}: already mapped to {jobs[key]['job_id']}")
            continue

        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise ValueError(f"job payload must be a JSON object: {path}")

        status, response = _request_json(
            f"{api_base.rstrip('/')}/api/v1/jobs",
            method="POST",
            payload=payload,
        )
        if status == 201 and isinstance(response, dict):
            job_id = response.get("id")
            if not isinstance(job_id, str):
                raise RuntimeError(f"API response without job id for {key}")
            jobs[key] = {
                "job_id": job_id,
                "fingerprint": response.get("fingerprint"),
                "company_name": response.get("company_name"),
                "title": response.get("title"),
                "imported_at": datetime.now(UTC).isoformat(),
            }
            imported += 1
            print(f"import {key}: {job_id}")
            continue

        detail = response.get("detail") if isinstance(response, dict) else response
        if status == 409:
            raise RuntimeError(
                f"duplicate job while importing {key}: {detail}. "
                "The API already has this job but the local manifest has no mapping. "
                "Restore the manifest or reset the local pilot database before re-importing."
            )
        raise RuntimeError(f"failed to import {key}: HTTP {status}: {detail}")

    _write_json(manifest_path, manifest)
    print(f"manifest: {manifest_path} | imported={imported} skipped={skipped}")
    return manifest


def _load_labels(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"labels file does not exist: {path}. Copy the documented local template first."
        )
    raw = _read_json(path)
    if not isinstance(raw, list):
        raise ValueError("matching labels must be a JSON array")

    labels: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each matching label must be a JSON object")
        job_file = item.get("job_file")
        relevance = item.get("relevance")
        if not isinstance(job_file, str) or not job_file.endswith(".json"):
            raise ValueError("each label needs job_file ending in .json")
        if job_file in seen:
            raise ValueError(f"duplicate label for {job_file}")
        if not isinstance(relevance, int) or not 0 <= relevance <= 4:
            raise ValueError(f"relevance for {job_file} must be an integer from 0 to 4")
        blocker_real = item.get("blocker_real", False)
        if not isinstance(blocker_real, bool):
            raise ValueError(f"blocker_real for {job_file} must be boolean")
        reason = item.get("reason")
        if reason is not None and not isinstance(reason, str):
            raise ValueError(f"reason for {job_file} must be text or null")
        labels.append(
            {
                "job_file": job_file,
                "relevance": relevance,
                "blocker_real": blocker_real,
                "reason": reason,
            }
        )
        seen.add(job_file)
    return labels


def _report_markdown(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "# HireIn — Pilot Matching Eval",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Samples | {metrics['sample_count']} |",
        f"| Human relevant (3–4) | {metrics['relevant_count']} |",
        f"| Match score available | {metrics['scored_count']} |",
        f"| Average evaluation coverage | {metrics['average_coverage']:.2f}% |",
        f"| Recall@5 | {metrics['recall_at_5']:.4f} |",
        f"| Recall@10 | {metrics['recall_at_10']:.4f} |",
        f"| NDCG@5 | {metrics['ndcg_at_5']:.4f} |",
        f"| NDCG@10 | {metrics['ndcg_at_10']:.4f} |",
        "",
        "## Ranking",
        "",
        "| Rank | Job | Match | Coverage | Human | Band | Blocker real |",
        "|---:|---|---:|---:|---:|---|---|",
    ]
    for index, item in enumerate(report["ranking"], start=1):
        score = "—" if item["score"] is None else f"{item['score']}%"
        blocker = "yes" if item["blocker_real"] else "no"
        lines.append(
            f"| {index} | `{item['key']}` | {score} | {item['coverage']}% | "
            f"{item['relevance']} | {item['band']} | {blocker} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Human relevance: 0 irrelevante, 1 fraca, 2 razoável, 3 boa, 4 excelente.",
            "- Recall considers labels 3–4 as relevant.",
            "- NDCG uses the full 0–4 graded relevance.",
            "- Jobs without a Match score rank after scored jobs; this exposes coverage failures.",
            "- This report is local pilot evidence, not a hiring-performance claim.",
            "",
        ]
    )
    return "\n".join(lines)


def evaluate(
    api_base: str,
    manifest_path: Path,
    labels_path: Path,
    report_json: Path,
    report_md: Path,
) -> dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    jobs: dict[str, Any] = manifest["jobs"]
    labels = _load_labels(labels_path)
    if not labels:
        raise ValueError("at least one human-labeled job is required")

    samples: list[RankingSample] = []
    raw_matches: dict[str, Any] = {}
    for label in labels:
        key = label["job_file"]
        entry = jobs.get(key)
        if not isinstance(entry, dict) or not isinstance(entry.get("job_id"), str):
            raise ValueError(
                f"label {key} has no imported job id in {manifest_path}. Run import first."
            )
        job_id = entry["job_id"]
        status, match = _request_json(
            f"{api_base.rstrip('/')}/api/v1/jobs/{job_id}/match"
        )
        if status != 200 or not isinstance(match, dict):
            detail = match.get("detail") if isinstance(match, dict) else match
            raise RuntimeError(f"match failed for {key}: HTTP {status}: {detail}")

        score = match.get("score")
        coverage = match.get("evaluation_coverage")
        band = match.get("band")
        if score is not None and not isinstance(score, int):
            raise ValueError(f"invalid match score for {key}")
        if not isinstance(coverage, int) or not isinstance(band, str):
            raise ValueError(f"invalid match response for {key}")

        samples.append(
            RankingSample(
                key=key,
                relevance=label["relevance"],
                score=score,
                coverage=coverage,
                band=band,
                blocker_real=label["blocker_real"],
                reason=label["reason"],
            )
        )
        raw_matches[key] = match
        print(
            f"eval   {key}: score={score if score is not None else 'n/a'} "
            f"coverage={coverage}% human={label['relevance']}"
        )

    ranked = rank_samples(samples)
    metrics = calculate_ranking_metrics(samples)
    report: dict[str, Any] = {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "api_base": api_base.rstrip("/"),
        "relevance_threshold": 3,
        "metrics": asdict(metrics),
        "ranking": [asdict(sample) for sample in ranked],
        "matches": raw_matches,
    }
    _write_json(report_json, report)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text(_report_markdown(report), encoding="utf-8")
    print(f"report: {report_json}")
    print(f"report: {report_md}")
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import the local HireIn pilot dataset and evaluate Match v0 ranking."
    )
    parser.add_argument(
        "command",
        choices=["import", "evaluate", "run"],
        help="import jobs, evaluate labels, or do both",
    )
    parser.add_argument("--api-base", default="http://localhost:8000")
    parser.add_argument("--jobs-dir", type=Path, default=DEFAULT_JOBS_DIR)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command in {"import", "run"}:
            import_jobs(args.api_base, args.jobs_dir, args.manifest)
        if args.command in {"evaluate", "run"}:
            evaluate(
                args.api_base,
                args.manifest,
                args.labels,
                args.report_json,
                args.report_md,
            )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
