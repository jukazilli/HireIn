from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from hirein_api.jobs.domain import RequirementKind

AtomicOperator = Literal["ANY", "ALL"]

_MAX_ATOMIC_OPTIONS = 8
_MAX_WORDS_PER_ATOM = 4

# Only heads with a strong, repeatable linguistic pattern are allowed to borrow
# a complement from the next coordinated phrase. This keeps the parser
# deterministic and deliberately conservative.
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

# Heads that safely carry over to short adjectival complements.
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


@dataclass(frozen=True, slots=True)
class AtomicRequirement:
    operator: AtomicOperator
    options: tuple[str, ...]


def _canonical_word(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()


def _clean_atom(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t\n,;|./")


def _split_raw(value: str) -> tuple[AtomicOperator | None, list[str]]:
    compact = re.sub(r"\s+", " ", value).strip()
    has_or = re.search(r"\s+ou\s+", compact, flags=re.IGNORECASE) is not None
    has_and = re.search(r"\s+e\s+", compact, flags=re.IGNORECASE) is not None
    has_list_separator = any(separator in compact for separator in (",", ";", "|"))

    if has_or:
        operator: AtomicOperator = "ANY"
        splitter = r"\s*(?:,|;|\|)\s*|\s+ou\s+"
    elif has_and or has_list_separator:
        operator = "ALL"
        splitter = r"\s*(?:,|;|\|)\s*|\s+e\s+"
    else:
        return None, []

    raw_parts = re.split(splitter, compact, flags=re.IGNORECASE)
    options: list[str] = []
    seen: set[str] = set()
    for raw_part in raw_parts:
        part = _clean_atom(raw_part)
        key = _canonical_word(part)
        if len(part) < 2 or key in seen:
            continue
        seen.add(key)
        options.append(part)

    if not 2 <= len(options) <= _MAX_ATOMIC_OPTIONS:
        return None, []
    return operator, options


def _shared_complement(option: str) -> tuple[str, str] | None:
    words = option.split()
    if len(words) < 3:
        return None

    for index, word in enumerate(words[1:], start=1):
        if _canonical_word(word) in _PREPOSITIONS:
            head = " ".join(words[:index])
            complement = " ".join(words[index:])
            return head, complement
    return None


def _restore_shared_complements(options: list[str]) -> list[str]:
    repaired = list(options)
    for index in range(len(repaired) - 1):
        left = repaired[index]
        right = repaired[index + 1]

        if len(left.split()) != 1:
            continue

        right_parts = _shared_complement(right)
        if right_parts is None:
            continue

        right_head, complement = right_parts
        left_head_key = _canonical_word(left)
        right_head_key = _canonical_word(right_head.split()[0])

        if (
            left_head_key in _SHARED_COMPLEMENT_HEADS
            and right_head_key in _SHARED_COMPLEMENT_HEADS
        ):
            repaired[index] = f"{left} {complement}"

    return repaired


def _looks_like_short_modifier(option: str) -> bool:
    words = option.split()
    if not 1 <= len(words) <= 2:
        return False
    if any(_canonical_word(word) in _PREPOSITIONS for word in words):
        return False
    # Proper nouns/acronyms are usually independent alternatives (Kanban,
    # Copilot, Power BI). Lower-case modifiers are the safe carry-over case.
    return option[:1].islower()


def _restore_shared_prefixes(options: list[str]) -> list[str]:
    if not options:
        return options

    first_words = options[0].split()
    if len(first_words) < 2:
        return options

    head = first_words[0]
    head_key = _canonical_word(head)
    if head_key not in _SHARED_PREFIX_HEADS:
        return options

    repaired = [options[0]]
    for option in options[1:]:
        if _looks_like_short_modifier(option):
            repaired.append(f"{head} {option}")
        else:
            repaired.append(option)
    return repaired


def parse_atomic_requirement(
    value: str,
    kind: RequirementKind,
) -> AtomicRequirement | None:
    """Parse only safe SKILL/TOOL coordination into semantic atomic concepts.

    The parser keeps list cardinality/order stable so previously selected v1.10
    atoms can be migrated by position without guessing new user intent.
    """

    if kind not in {RequirementKind.SKILL, RequirementKind.TOOL}:
        return None

    operator, options = _split_raw(value)
    if operator is None:
        return None

    options = _restore_shared_complements(options)
    options = _restore_shared_prefixes(options)

    if any(len(option.split()) > _MAX_WORDS_PER_ATOM for option in options):
        return None

    return AtomicRequirement(operator=operator, options=tuple(options))
