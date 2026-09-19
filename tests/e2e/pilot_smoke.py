from __future__ import annotations

import os
import re
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

WEB_BASE_URL = os.getenv("E2E_WEB_BASE_URL", "http://localhost:5173")
ARTIFACT_DIR = Path(os.getenv("E2E_ARTIFACT_DIR", "e2e-artifacts"))
PILOT_PASSWORD = os.getenv("E2E_PILOT_PASSWORD", "hirein-e2e-password")

CANDIDATE_NAME = "Candidato Sintetico E2E"
COMPANY_NAME = "Empresa Sintetica E2E"
JOB_TITLE = "Analista de Projetos E2E"
SKILLS = "Gestão de Projetos, Levantamento de Requisitos, Implantação de Sistemas"


def combobox(page: Page, label: str):
    return page.get_by_role("combobox", name=re.compile(rf"^{re.escape(label)}"))


def login(page: Page) -> None:
    page.goto(f"{WEB_BASE_URL}/pilot", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r"/login\?next="))
    expect(page.get_by_role("heading", name="Entre no seu HireIn")).to_be_visible()
    page.get_by_label("Senha do piloto", exact=True).fill(PILOT_PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page).to_have_url(f"{WEB_BASE_URL}/pilot")


def fill_profile(page: Page) -> None:
    page.goto(WEB_BASE_URL, wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="Mostre ao HireIn o que você já construiu.")).to_be_visible()

    expect(page.get_by_label("Nome completo", exact=True)).to_be_visible()

    page.get_by_label("Nome completo", exact=True).fill(CANDIDATE_NAME)
    page.get_by_label("Título profissional", exact=True).fill("Analista de Projetos e Implantação")
    page.get_by_label("Cidade", exact=True).fill("Joinville")
    page.get_by_label("Estado", exact=True).fill("SC")
    page.get_by_label("Cargos desejados", exact=True).fill("Analista de Projetos")
    page.get_by_label("Áreas de interesse", exact=True).fill("Projetos, Implantação")
    page.get_by_label("Localidades", exact=True).fill("Joinville, Remoto")
    combobox(page, "Senioridade").select_option("MID")
    page.get_by_label("Remoto", exact=True).check()
    page.get_by_label("CLT", exact=True).check()
    page.get_by_label("Skills", exact=True).fill(SKILLS)
    page.get_by_label("Outros fatos confirmados", exact=True).fill(
        "Experiência com contato direto com usuários"
    )

    page.get_by_role("button", name="Adicionar experiência").click()
    page.get_by_label("Empresa", exact=True).fill("Empresa Anterior Sintetica")
    page.get_by_label("Cargo", exact=True).fill("Assistente de Implantação")
    page.get_by_label("Início", exact=True).fill("2025-01-10")
    page.get_by_label("É meu trabalho atual", exact=True).check()
    page.get_by_label("Contexto da experiência", exact=True).fill(
        "Apoio a projetos de implantação de software e organização de demandas."
    )
    page.get_by_label("Fatos que podem ser comprovados", exact=True).fill(
        "Levantamento de requisitos com usuários\nTreinamento funcional para usuários finais"
    )

    page.get_by_role("button", name="Salvar meu perfil").click()
    expect(
        page.get_by_text("Perfil salvo. Estas informações estão confirmadas por você.")
    ).to_be_visible()

    page.reload(wait_until="domcontentloaded")
    expect(page.get_by_label("Nome completo", exact=True)).to_be_visible()
    expect(page.get_by_label("Nome completo", exact=True)).to_have_value(CANDIDATE_NAME)
    expect(page.get_by_label("Skills", exact=True)).to_have_value(SKILLS)


def assert_profile_persisted(page: Page) -> None:
    response = page.request.get(f"{WEB_BASE_URL}/api/v1/profile")
    assert response.ok, f"GET /profile returned {response.status}: {response.text()}"
    body = response.json()
    assert body["full_name"] == CANDIDATE_NAME
    assert any(skill["name"] == "Gestão de Projetos" for skill in body["skills"])
    assert all(skill["source_type"] == "USER_CONFIRMED" for skill in body["skills"])


def create_job(page: Page) -> None:
    page.goto(f"{WEB_BASE_URL}/jobs", wait_until="domcontentloaded")
    expect(
        page.get_by_role("heading", name="Uma oportunidade de cada vez, com contexto suficiente.")
    ).to_be_visible()

    page.get_by_label("Plataforma", exact=True).fill("E2E")
    page.get_by_label("ID externo", exact=True).fill("e2e-job-001")
    page.get_by_label("Empresa", exact=True).fill(COMPANY_NAME)
    page.get_by_label("Cargo", exact=True).fill(JOB_TITLE)
    page.get_by_label("Local exibido", exact=True).fill("Remoto · Brasil")
    combobox(page, "Modalidade").select_option("REMOTE")
    combobox(page, "Contrato").select_option("CLT")
    combobox(page, "Senioridade").select_option("MID")
    page.get_by_label("Descrição original", exact=True).fill(
        "Buscamos Analista de Projetos com experiência em gestão de projetos, "
        "levantamento de requisitos e contato com usuários. Trabalho remoto e contratação CLT."
    )

    page.get_by_role("button", name="Adicionar requisito").click()
    combobox(page, "Tipo").select_option("SKILL")
    combobox(page, "Importância").select_option("REQUIRED")
    page.get_by_label("Requisito", exact=True).fill("Gestão de Projetos")
    page.get_by_label("Trecho que sustenta o requisito", exact=True).fill(
        "experiência em gestão de projetos"
    )

    page.get_by_role("button", name="Salvar esta vaga").click()
    expect(page.get_by_text("Vaga salva. Ela já pode ser analisada no Match.")).to_be_visible()
    expect(page.get_by_text(COMPANY_NAME, exact=True)).to_be_visible()


def get_created_job_id(page: Page) -> str:
    response = page.request.get(f"{WEB_BASE_URL}/api/v1/jobs")
    assert response.ok, f"GET /jobs returned {response.status}: {response.text()}"
    jobs = response.json()
    created = next((job for job in jobs if job["company_name"] == COMPANY_NAME), None)
    assert created is not None, "Synthetic job was not persisted in PostgreSQL."
    assert created["requirement_count"] == 1
    return str(created["id"])


def assert_match_locked_before_review(page: Page) -> None:
    page.goto(f"{WEB_BASE_URL}/jobs/match", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="Qual vaga você quer entender?")).to_be_visible()

    job_button = page.get_by_role("button").filter(has_text=COMPANY_NAME)
    expect(job_button).to_have_count(1)
    expect(job_button).to_be_disabled()
    expect(job_button).to_contain_text("Avalie primeiro")


def calculate_match(page: Page) -> None:
    page.goto(f"{WEB_BASE_URL}/jobs/match", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="Qual vaga você quer entender?")).to_be_visible()

    job_button = page.get_by_role("button").filter(has_text=COMPANY_NAME)
    expect(job_button).to_have_count(1)
    expect(job_button).to_be_enabled()
    job_button.click()

    expect(page.get_by_text("Confiança da evidência", exact=True)).to_be_visible()
    expect(page.locator(".match-score-panel")).to_contain_text("Faixa possível")
    expect(page.locator(".match-score-panel")).to_contain_text("sinal de ranking")
    dimension_strip = page.locator(".dimension-strip")
    expect(
        dimension_strip.get_by_text("Opportunity Compatibility", exact=True)
    ).to_be_visible()
    expect(dimension_strip.get_by_text("Apply Intent", exact=True)).to_be_visible()


def assert_match_api(page: Page, job_id: str) -> None:
    response = page.request.get(f"{WEB_BASE_URL}/api/v1/jobs/{job_id}/match")
    assert response.ok, f"GET /jobs/{{id}}/match returned {response.status}: {response.text()}"
    match = response.json()
    assert match["job_id"] == job_id
    assert match["evaluation_coverage"] > 0
    assert match["professional_fit"] is not None
    assert match["professional_fit"]["confidence"] == match["evaluation_coverage"]
    assert match["professional_fit"]["score"] == match["score"]
    assert match["professional_fit"]["ranking_score"] is not None
    assert match["professional_fit"]["score_floor"] is not None
    assert match["professional_fit"]["score_ceiling"] is not None
    assert match["professional_fit"]["score_floor"] <= match["professional_fit"]["score_ceiling"]
    assert match["opportunity_compatibility"] is not None
    assert len(match["requirement_results"]) == 1
    assert match["requirement_results"][0]["value"] == "Gestão de Projetos"


def save_human_review(page: Page) -> None:
    page.goto(f"{WEB_BASE_URL}/jobs/review", wait_until="domcontentloaded")
    expect(
        page.get_by_role("heading", name="Primeiro a sua opinião. Depois, a do algoritmo.")
    ).to_be_visible()

    queue_button = page.get_by_role("button").filter(has_text=COMPANY_NAME)
    expect(queue_button).to_have_count(1)
    queue_button.click()

    expect(
        page.get_by_role("heading", name="Quanto seu perfil profissional atual atende esta vaga?")
    ).to_be_visible()
    expect(
        page.get_by_role("heading", name="Quanto você realmente gostaria de se candidatar?")
    ).to_be_visible()
    expect(page.get_by_text("Oculto durante a revisão humana", exact=True)).to_be_visible()
    expect(page.get_by_text("Confiança da evidência", exact=True)).to_have_count(0)
    expect(page.get_by_text("Obrigatórios atendidos", exact=True)).to_have_count(0)

    fit_group = page.get_by_role("group", name="Professional Fit de zero a quatro")
    fit_group.get_by_role("button").nth(4).click()
    intent_group = page.get_by_role("group", name="Apply Intent de zero a quatro")
    intent_group.get_by_role("button").nth(3).click()
    page.get_by_label(re.compile(r"^Por quê\?"), exact=False).fill(
        "Fit alto e intenção boa para a oportunidade sintética do smoke test."
    )
    page.get_by_role("button", name="Salvar avaliação").click()

    expect(page.get_by_text(re.compile(r"^Sua avaliação foi salva\."))).to_be_visible()
    expect(page.get_by_text("Confiança da evidência", exact=True)).to_have_count(0)
    expect(page.get_by_text("Obrigatórios atendidos", exact=True)).to_have_count(0)
    expect(page.get_by_text("Oculto durante a revisão humana", exact=True)).to_be_visible()

    page.reload(wait_until="domcontentloaded")
    queue_button = page.get_by_role("button").filter(has_text=COMPANY_NAME)
    expect(queue_button).to_contain_text("Fit 4/4")
    expect(queue_button).to_contain_text("Intent 3/4")


def assert_review_api(page: Page, job_id: str) -> None:
    response = page.request.get(f"{WEB_BASE_URL}/api/v1/evals/jobs")
    assert response.ok, f"GET /evals/jobs returned {response.status}: {response.text()}"
    jobs = response.json()
    created = next((job for job in jobs if job["job_id"] == job_id), None)
    assert created is not None
    assert created["evaluation"] is not None
    assert created["evaluation"]["relevance"] == 4
    assert created["evaluation"]["apply_intent"] == 3

    report_response = page.request.get(f"{WEB_BASE_URL}/api/v1/evals/report")
    assert report_response.ok, (
        f"GET /evals/report returned {report_response.status}: {report_response.text()}"
    )
    report = report_response.json()
    assert report["metrics"]["sample_count"] == 1
    assert report["ranking"][0]["relevance"] == 4
    assert report["ranking"][0]["apply_intent"] == 3


def logout(page: Page) -> None:
    page.get_by_role("button", name="Sair").click()
    expect(page).to_have_url(f"{WEB_BASE_URL}/login")
    page.goto(f"{WEB_BASE_URL}/pilot", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r"/login\?next="))


def run() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    page_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        try:
            login(page)
            fill_profile(page)
            assert_profile_persisted(page)
            create_job(page)
            job_id = get_created_job_id(page)
            assert_match_locked_before_review(page)
            save_human_review(page)
            assert_review_api(page, job_id)
            calculate_match(page)
            assert_match_api(page, job_id)
            logout(page)

            assert not page_errors, f"Browser page errors detected: {page_errors}"
            page.screenshot(path=str(ARTIFACT_DIR / "pilot-smoke-success.png"), full_page=True)
        except Exception:
            page.screenshot(path=str(ARTIFACT_DIR / "pilot-smoke-failure.png"), full_page=True)
            raise
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    run()
