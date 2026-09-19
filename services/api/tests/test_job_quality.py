from __future__ import annotations

from hirein_api.jobs.quality import JobQualityStatus, assess_job_quality


def test_flags_explicit_title_description_role_conflict() -> None:
    result = assess_job_quality(
        "Analista de Dados Pleno - Exclusiva Rio de Janeiro",
        (
            "A descrição da vaga busca Analista de Sistemas Pleno para implantação, "
            "sustentação e evolução do produto."
        ),
    )

    assert result.status == JobQualityStatus.REVIEW
    assert result.rankable is False
    assert result.declared_role == "analista de sistemas pleno"
    assert result.warnings == (
        "job_title_specialization_conflicts_with_description",
    )


def test_accepts_explicit_role_that_matches_title() -> None:
    result = assess_job_quality(
        "Analista de Projetos Pleno",
        "A vaga busca Analista de Projetos Pleno para conduzir projetos estratégicos.",
    )

    assert result.status == JobQualityStatus.OK
    assert result.rankable is True
    assert result.warnings == ()


def test_ignores_incidental_mentions_of_other_roles() -> None:
    result = assess_job_quality(
        "Analista de Projetos",
        (
            "Responsável por conduzir projetos e fazer interface com analistas de "
            "sistemas, fornecedores e usuários."
        ),
    )

    assert result.status == JobQualityStatus.OK
    assert result.rankable is True
    assert result.declared_role is None


def test_flags_explicit_role_family_conflict() -> None:
    result = assess_job_quality(
        "Product Owner",
        "Buscamos Analista de Sistemas para atuar com backlog e stakeholders.",
    )

    assert result.status == JobQualityStatus.REVIEW
    assert result.rankable is False
    assert result.warnings == (
        "job_role_family_conflicts_with_description",
    )


def test_no_explicit_declared_role_remains_rankable() -> None:
    result = assess_job_quality(
        "Consultor de Implantação",
        "Atuação com implantação de software, treinamento e go-live.",
    )

    assert result.status == JobQualityStatus.OK
    assert result.rankable is True
    assert result.warnings == ()
