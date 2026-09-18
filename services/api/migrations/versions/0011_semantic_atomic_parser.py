"""Repair v1.10 atomic evidence with preserved semantic context.

Revision ID: 0011_semantic_atomic_parser
Revises: 0010_atomic_evidence
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_semantic_atomic_parser"
down_revision: str | None = "0010_atomic_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SHARED_COMPLEMENT_HEADS = {
    "alinhamento",
    "analise",
    "acompanhamento",
    "comunicacao",
    "controle",
    "criacao",
    "definicao",
    "desenho",
    "documentacao",
    "elaboracao",
    "gestao",
    "gerenciamento",
    "levantamento",
    "mapeamento",
    "modelagem",
    "planejamento",
    "priorizacao",
    "revisao",
    "tratamento",
    "validacao",
}
_SHARED_PREFIX_HEADS = {
    "capacidade",
    "comunicacao",
    "conhecimento",
    "documentacao",
    "experiencia",
    "gestao",
    "requisito",
    "requisitos",
    "teste",
    "testes",
}
_PREPOSITIONS = {"de", "do", "da", "dos", "das", "com", "para", "em"}
_MAX_WORDS_PER_ATOM = 4


def _canonical_word(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in normalized if not unicodedata.combining(char)
    ).casefold()


def _clean_atom(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t\n,;|./")


def _legacy_options(value: str) -> list[str]:
    compact = re.sub(r"\s+", " ", value).strip()
    has_or = re.search(r"\s+ou\s+", compact, flags=re.IGNORECASE) is not None
    has_and = re.search(r"\s+e\s+", compact, flags=re.IGNORECASE) is not None
    has_list_separator = any(separator in compact for separator in (",", ";", "|"))

    if has_or:
        splitter = r"\s*(?:,|;|\|)\s*|\s+ou\s+"
    elif has_and or has_list_separator:
        splitter = r"\s*(?:,|;|\|)\s*|\s+e\s+"
    else:
        return []

    parts = [
        _clean_atom(item)
        for item in re.split(splitter, compact, flags=re.IGNORECASE)
    ]
    return [item for item in parts if len(item) >= 2]


def _shared_complement(option: str) -> tuple[str, str] | None:
    words = option.split()
    if len(words) < 3:
        return None
    for index, word in enumerate(words[1:], start=1):
        if _canonical_word(word) in _PREPOSITIONS:
            return " ".join(words[:index]), " ".join(words[index:])
    return None


def _semantic_options(value: str) -> list[str]:
    repaired = _legacy_options(value)
    if len(repaired) < 2:
        return repaired

    for index in range(len(repaired) - 1):
        left = repaired[index]
        right = repaired[index + 1]
        if len(left.split()) != 1:
            continue
        right_parts = _shared_complement(right)
        if right_parts is None:
            continue
        right_head, complement = right_parts
        if (
            _canonical_word(left) in _SHARED_COMPLEMENT_HEADS
            and _canonical_word(right_head.split()[0]) in _SHARED_COMPLEMENT_HEADS
        ):
            repaired[index] = f"{left} {complement}"

    semantic: list[str] = []
    active_head: str | None = None
    for option in repaired:
        words = option.split()
        if (
            len(words) >= 2
            and _canonical_word(words[0]) in _SHARED_PREFIX_HEADS
        ):
            active_head = words[0]
            semantic.append(option)
            continue

        short_modifier = (
            active_head is not None
            and 1 <= len(words) <= 2
            and option[:1].islower()
            and not any(_canonical_word(word) in _PREPOSITIONS for word in words)
        )
        if short_modifier:
            semantic.append(f"{active_head} {option}")
        else:
            semantic.append(option)

    if any(len(option.split()) > _MAX_WORDS_PER_ATOM for option in semantic):
        return []
    return semantic


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _remap_atoms(
    requirement_value: str,
    selected_atoms: list[str],
    *,
    reverse: bool = False,
) -> list[str] | None:
    legacy = _legacy_options(requirement_value)
    semantic = _semantic_options(requirement_value)
    if len(legacy) != len(semantic) or not legacy:
        return None

    source = semantic if reverse else legacy
    target = legacy if reverse else semantic
    by_source = {_normalized(value): index for index, value in enumerate(source)}

    remapped: list[str] = []
    for selected in selected_atoms:
        index = by_source.get(_normalized(selected))
        if index is None:
            return None
        remapped.append(target[index])
    return remapped


def _apply(*, reverse: bool) -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT
                cer.id::text AS resolution_id,
                cer.confirmed_atoms,
                jr.value AS requirement_value
            FROM candidate_evidence_resolutions AS cer
            JOIN job_requirements AS jr
              ON jr.id = cer.job_requirement_id
            WHERE jr.kind IN ('SKILL', 'TOOL')
              AND jsonb_array_length(cer.confirmed_atoms) > 0
            """
        )
    ).mappings()

    for row in rows:
        selected_atoms = list(row["confirmed_atoms"] or [])
        remapped = _remap_atoms(
            row["requirement_value"],
            selected_atoms,
            reverse=reverse,
        )
        if remapped is None or remapped == selected_atoms:
            continue

        bind.execute(
            sa.text(
                """
                UPDATE candidate_evidence_resolutions
                SET confirmed_atoms = CAST(:atoms AS jsonb)
                WHERE id = CAST(:resolution_id AS uuid)
                """
            ),
            {
                "atoms": json.dumps(remapped, ensure_ascii=False),
                "resolution_id": row["resolution_id"],
            },
        )

        base_ref = f"evidence-gap:{row['resolution_id']}:atom:"
        for index, value in enumerate(remapped):
            bind.execute(
                sa.text(
                    """
                    UPDATE candidate_facts
                    SET value = :value
                    WHERE source_ref = :source_ref
                    """
                ),
                {
                    "value": value,
                    "source_ref": f"{base_ref}{index}",
                },
            )


def upgrade() -> None:
    _apply(reverse=False)


def downgrade() -> None:
    _apply(reverse=True)
