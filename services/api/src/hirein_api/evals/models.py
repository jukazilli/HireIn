from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from hirein_api.db import Base


class PilotJobEvaluation(Base):
    __tablename__ = "pilot_job_evaluations"
    __table_args__ = (
        CheckConstraint(
            "relevance >= 0 AND relevance <= 4",
            name="ck_pilot_job_evaluations_relevance",
        ),
        CheckConstraint(
            "apply_intent IS NULL OR (apply_intent >= 0 AND apply_intent <= 4)",
            name="ck_pilot_job_evaluations_apply_intent",
        ),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # Historical rows used `relevance` as a general relevance label. From Blind Holdout #4
    # onward the same field is the human Professional Fit label used by ranking evals.
    relevance: Mapped[int] = mapped_column(Integer, nullable=False)
    apply_intent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blocker_real: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason: Mapped[str | None] = mapped_column(Text)
    error_category: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
