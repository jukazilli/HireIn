from __future__ import annotations

import json
import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hirein_api.match.current import calculate_job_match


class BlindReportError(RuntimeError):
    pass


def parse_job_ids(raw: str) -> list[uuid.UUID]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise BlindReportError("blind report requires at least one job id")
    try:
        return [uuid.UUID(item) for item in values]
    except ValueError as exc:
        raise BlindReportError("blind report contains an invalid job id") from exc


async def build_blind_report(
    session_factory: async_sessionmaker[AsyncSession],
    job_ids: Sequence[uuid.UUID],
) -> str:
    rows: list[dict[str, object]] = []
    async with session_factory() as session:
        for job_id in job_ids:
            match = await calculate_job_match(session, job_id)
            rows.append(
                {
                    "job_id": str(match.job_id),
                    "score": match.score,
                    "band": match.band,
                    "evaluation_coverage": match.evaluation_coverage,
                    "ranking_score": (
                        match.professional_fit.ranking_score
                        if match.professional_fit is not None
                        else None
                    ),
                    "score_floor": (
                        match.professional_fit.score_floor
                        if match.professional_fit is not None
                        else None
                    ),
                    "score_ceiling": (
                        match.professional_fit.score_ceiling
                        if match.professional_fit is not None
                        else None
                    ),
                    "job_quality": (
                        {
                            "status": match.job_quality.status,
                            "rankable": match.job_quality.rankable,
                            "warnings": match.job_quality.warnings,
                            "declared_role": match.job_quality.declared_role,
                        }
                        if match.job_quality is not None
                        else None
                    ),
                    "matched_required": match.matched_required,
                    "missing_required": match.missing_required,
                    "matched_preferred": match.matched_preferred,
                    "missing_preferred": match.missing_preferred,
                    "unknown_requirements": match.unknown_requirements,
                    "opportunity_compatibility": (
                        match.opportunity_compatibility.model_dump(mode="json")
                        if match.opportunity_compatibility is not None
                        else None
                    ),
                    "requirement_results": [
                        {
                            "requirement_id": str(item.requirement_id),
                            "kind": item.kind,
                            "importance": item.importance,
                            "value": item.value,
                            "status": item.status,
                            "reason": item.reason,
                        }
                        for item in match.requirement_results
                    ],
                    "warnings": match.warnings,
                }
            )
    return json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
