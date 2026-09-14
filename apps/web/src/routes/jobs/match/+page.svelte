<script lang="ts">
  import { onMount } from 'svelte';

  const API = 'http://localhost:8000/api/v1/jobs';

  type JobSummary = {
    id: string;
    company_name: string;
    title: string;
    location_text: string | null;
    work_model: string | null;
    contract_type: string | null;
    seniority: string | null;
    requirement_count: number;
  };

  type Evidence = {
    entity_type: string;
    entity_id: string;
    value: string;
    source_type: string;
    detail: string | null;
  };

  type RequirementResult = {
    requirement_id: string;
    kind: string;
    importance: string;
    value: string;
    status: 'MATCHED' | 'GAP' | 'UNKNOWN' | 'INFO';
    weight: number;
    evidence: Evidence[];
    reason: string;
  };

  type PreferenceResult = {
    aspect: string;
    status: 'ALIGNED' | 'CONFLICT' | 'UNKNOWN';
    candidate_value: string[];
    job_value: string[];
    reason: string;
  };

  type MatchResult = {
    job_id: string;
    profile_id: string;
    score: number | null;
    band: string;
    requirement_score: number | null;
    preference_score: number | null;
    evaluation_coverage: number;
    matched_required: number;
    missing_required: number;
    matched_preferred: number;
    missing_preferred: number;
    unknown_requirements: number;
    requirement_results: RequirementResult[];
    preference_results: PreferenceResult[];
    warnings: string[];
  };

  let jobs: JobSummary[] = [];
  let selectedJob: JobSummary | null = null;
  let result: MatchResult | null = null;
  let loading = true;
  let calculating = false;
  let error = '';

  const bandLabel: Record<string, string> = {
    STRONG: 'Forte',
    GOOD: 'Boa',
    PARTIAL: 'Parcial',
    LOW: 'Baixa',
    INSUFFICIENT_DATA: 'Dados insuficientes'
  };

  const statusLabel: Record<string, string> = {
    MATCHED: 'Atendido',
    GAP: 'Gap',
    UNKNOWN: 'Não avaliável',
    INFO: 'Informativo',
    ALIGNED: 'Alinhado',
    CONFLICT: 'Conflito'
  };

  async function loadJobs() {
    try {
      const response = await fetch(API);
      if (!response.ok) throw new Error(`Falha ao carregar vagas (${response.status}).`);
      jobs = await response.json();
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível carregar as vagas.';
    } finally {
      loading = false;
    }
  }

  async function calculate(job: JobSummary) {
    selectedJob = job;
    result = null;
    error = '';
    calculating = true;
    try {
      const response = await fetch(`${API}/${job.id}/match`);
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? `Falha ao calcular (${response.status}).`);
      }
      result = await response.json();
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível calcular o match.';
    } finally {
      calculating = false;
    }
  }

  onMount(loadJobs);
</script>

<svelte:head>
  <title>Match · HireIn</title>
  <meta name="description" content="Match determinístico e explicável do piloto HireIn." />
</svelte:head>

<main>
  <header>
    <div>
      <a class="back" href="/">← Perfil</a>
      <p class="eyebrow">HireIn · Match v0</p>
      <h1>Compatibilidade com evidência, não palpite.</h1>
      <p class="lead">
        O score usa apenas dados confirmados do perfil, mostra a cobertura real da análise e separa
        gaps profissionais de conflitos de preferência.
      </p>
    </div>
    <div class="guardrail">
      <span>LLM</span><strong>desligado</strong>
      <span>Embeddings</span><strong>desligados</strong>
      <span>Blockers automáticos</span><strong>desligados</strong>
    </div>
  </header>

  <section class="card">
    <div class="section-title">
      <div><p class="eyebrow">Dataset</p><h2>Escolha uma vaga</h2></div>
      <span>{jobs.length} vaga{jobs.length === 1 ? '' : 's'}</span>
    </div>

    {#if loading}
      <p class="empty">Carregando…</p>
    {:else if jobs.length === 0}
      <p class="empty">Cadastre uma vaga no Job Core antes de calcular compatibilidade.</p>
    {:else}
      <div class="job-list">
        {#each jobs as job}
          <article class:selected={selectedJob?.id === job.id}>
            <div>
              <p class="company">{job.company_name}</p>
              <h3>{job.title}</h3>
              <p class="meta">
                {job.location_text ?? 'Local não informado'} · {job.work_model ?? 'modalidade n/d'} ·
                {job.contract_type ?? 'contrato n/d'}
              </p>
            </div>
            <div class="job-side">
              <span>{job.requirement_count} requisitos</span>
              <button type="button" disabled={calculating} onclick={() => calculate(job)}>
                {calculating && selectedJob?.id === job.id ? 'Calculando…' : 'Calcular match'}
              </button>
            </div>
          </article>
        {/each}
      </div>
    {/if}
  </section>

  {#if error}
    <section class="notice error" aria-live="polite">{error}</section>
  {/if}

  {#if result && selectedJob}
    <section class="card result-card">
      <div class="result-head">
        <div>
          <p class="eyebrow">Resultado auditável</p>
          <h2>{selectedJob.title}</h2>
          <p>{selectedJob.company_name}</p>
        </div>
        <div class="score-block">
          <strong>{result.score === null ? '—' : `${result.score}%`}</strong>
          <span>{bandLabel[result.band] ?? result.band}</span>
        </div>
      </div>

      <div class="metrics">
        <div><span>Requisitos</span><strong>{result.requirement_score ?? '—'}{result.requirement_score === null ? '' : '%'}</strong></div>
        <div><span>Preferências</span><strong>{result.preference_score ?? '—'}{result.preference_score === null ? '' : '%'}</strong></div>
        <div><span>Cobertura</span><strong>{result.evaluation_coverage}%</strong></div>
        <div><span>Obrigatórios atendidos</span><strong>{result.matched_required}</strong></div>
      </div>

      {#if result.band === 'INSUFFICIENT_DATA'}
        <div class="notice">
          O HireIn não emitiu score porque menos de 60% do peso dos requisitos pôde ser avaliado com
          segurança. Isso é falta de evidência estruturada, não reprovação.
        </div>
      {/if}
    </section>

    <section class="card">
      <div class="section-title">
        <div><p class="eyebrow">Evidências</p><h2>Requisitos da vaga</h2></div>
        <span>{result.unknown_requirements} não avaliável{result.unknown_requirements === 1 ? '' : 'is'}</span>
      </div>

      <div class="result-list">
        {#each result.requirement_results as item}
          <article class="result-row">
            <div class="row-top">
              <div>
                <span class="status" data-status={item.status}>{statusLabel[item.status]}</span>
                <span class="kind">{item.importance} · {item.kind} · peso {item.weight}</span>
              </div>
              <strong>{item.value}</strong>
            </div>
            <p>{item.reason}</p>
            {#if item.evidence.length > 0}
              <div class="evidence-list">
                {#each item.evidence as evidence}
                  <div>
                    <span>{evidence.entity_type}</span>
                    <strong>{evidence.value}</strong>
                    <small>{evidence.source_type}{evidence.detail ? ` · ${evidence.detail}` : ''}</small>
                  </div>
                {/each}
              </div>
            {/if}
          </article>
        {/each}
      </div>
    </section>

    <section class="card">
      <div class="section-title">
        <div><p class="eyebrow">Preferências</p><h2>Alinhamento pessoal</h2></div>
        <span>não gera blocker no v0</span>
      </div>
      <div class="preference-grid">
        {#each result.preference_results as item}
          <article>
            <div class="row-top">
              <span class="status" data-status={item.status}>{statusLabel[item.status]}</span>
              <strong>{item.aspect}</strong>
            </div>
            <p>{item.reason}</p>
            <small>
              Você: {item.candidate_value.join(', ') || 'n/d'} · Vaga: {item.job_value.join(', ') || 'n/d'}
            </small>
          </article>
        {/each}
      </div>
    </section>

    <section class="warning-card">
      <strong>Como interpretar este resultado</strong>
      <p>
        O score mede apenas compatibilidade segundo as regras determinísticas desta versão. Ele não é
        probabilidade de entrevista ou contratação e não substitui sua decisão sobre a vaga.
      </p>
      <div class="warning-tags">
        {#each result.warnings as warning}<span>{warning}</span>{/each}
      </div>
    </section>
  {/if}
</main>

<style>
  :global(*) { box-sizing: border-box; }
  :global(body) {
    margin: 0;
    min-width: 320px;
    background: #f7f7fa;
    color: #18181f;
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  main { width: min(1120px, calc(100% - 2rem)); margin: 0 auto; padding: 3rem 0 5rem; }
  header { display: flex; justify-content: space-between; gap: 2rem; align-items: flex-end; margin-bottom: 2rem; }
  h1 { max-width: 790px; margin: .35rem 0 .8rem; font-size: clamp(2.25rem, 5vw, 4.2rem); line-height: 1; letter-spacing: -.055em; }
  h2, h3, p { margin-top: 0; }
  .lead { max-width: 730px; color: #5e5c69; line-height: 1.6; }
  .eyebrow { margin: 0; color: #6a6877; font-size: .76rem; font-weight: 750; letter-spacing: .09em; text-transform: uppercase; }
  .back { display: inline-block; margin-bottom: 1.5rem; color: #555361; text-decoration: none; }
  .guardrail { min-width: 230px; display: grid; grid-template-columns: 1fr auto; gap: .65rem 1rem; padding: 1rem 1.1rem; border: 1px solid #e4e3e9; border-radius: 16px; background: white; font-size: .82rem; }
  .guardrail strong { font-weight: 750; }
  .card { margin-top: 1rem; padding: clamp(1.3rem, 3vw, 2rem); border: 1px solid #e6e5eb; border-radius: 22px; background: white; }
  .section-title, .result-head, .row-top { display: flex; justify-content: space-between; gap: 1rem; align-items: center; }
  .section-title { margin-bottom: 1.3rem; }
  .section-title h2 { margin: .25rem 0 0; }
  .section-title > span { color: #6a6874; font-size: .86rem; }
  .job-list, .result-list { display: grid; gap: .7rem; }
  .job-list article { display: flex; justify-content: space-between; gap: 1rem; align-items: center; padding: 1rem 1.1rem; border: 1px solid #ecebf0; border-radius: 16px; }
  .job-list article.selected { border-color: #b9b7c3; background: #fafafd; }
  .company { margin: 0 0 .2rem; color: #6a6874; font-size: .82rem; }
  .job-list h3 { margin: 0 0 .35rem; }
  .meta { margin: 0; color: #777480; font-size: .86rem; }
  .job-side { display: grid; justify-items: end; gap: .55rem; color: #6a6874; font-size: .8rem; }
  button { border: 0; border-radius: 11px; padding: .7rem .9rem; background: #1f1e24; color: white; font-weight: 720; cursor: pointer; }
  button:disabled { opacity: .55; cursor: wait; }
  .result-head { align-items: flex-start; }
  .result-head h2 { margin: .25rem 0 .25rem; }
  .result-head p:last-child { color: #6a6874; }
  .score-block { min-width: 150px; display: grid; justify-items: end; }
  .score-block strong { font-size: clamp(2.8rem, 7vw, 5rem); letter-spacing: -.07em; line-height: .95; }
  .score-block span { margin-top: .45rem; color: #66636f; font-weight: 700; }
  .metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .7rem; margin-top: 1.5rem; }
  .metrics div { display: grid; gap: .35rem; padding: 1rem; border: 1px solid #ecebf0; border-radius: 14px; }
  .metrics span { color: #777480; font-size: .78rem; }
  .metrics strong { font-size: 1.4rem; }
  .notice { margin-top: 1rem; padding: 1rem; border: 1px solid #e4e2c8; border-radius: 14px; background: #fffef3; color: #5b5739; line-height: 1.5; }
  .notice.error { width: min(1120px, calc(100% - 2rem)); margin: 1rem auto; border-color: #edd7d7; background: #fff8f8; color: #8a3c3c; }
  .result-row { padding: 1rem 0; border-top: 1px solid #efedf2; }
  .result-row:first-child { border-top: 0; }
  .result-row p, .preference-grid p { margin: .65rem 0 0; color: #66636f; line-height: 1.5; font-size: .9rem; }
  .row-top > div { display: flex; align-items: center; gap: .6rem; }
  .status { display: inline-flex; padding: .3rem .55rem; border-radius: 999px; background: #f0eff3; color: #56535e; font-size: .72rem; font-weight: 780; }
  .status[data-status='MATCHED'], .status[data-status='ALIGNED'] { background: #f0f7f1; color: #45614b; }
  .status[data-status='GAP'], .status[data-status='CONFLICT'] { background: #fff4f2; color: #844e46; }
  .status[data-status='UNKNOWN'] { background: #f6f4ef; color: #6c6455; }
  .kind { color: #85818c; font-size: .75rem; }
  .evidence-list { display: grid; gap: .45rem; margin-top: .8rem; }
  .evidence-list div { display: grid; grid-template-columns: 90px 1fr auto; gap: .7rem; align-items: center; padding: .65rem .75rem; border-radius: 10px; background: #f8f8fa; font-size: .82rem; }
  .evidence-list span, .evidence-list small { color: #777480; }
  .preference-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .7rem; }
  .preference-grid article { padding: 1rem; border: 1px solid #ecebf0; border-radius: 14px; }
  .preference-grid small { display: block; margin-top: .65rem; color: #85818c; line-height: 1.45; }
  .warning-card { margin-top: 1rem; padding: 1.3rem; border: 1px dashed #d8d6de; border-radius: 18px; color: #55525f; }
  .warning-card p { margin: .5rem 0 1rem; max-width: 820px; line-height: 1.55; }
  .warning-tags { display: flex; gap: .45rem; flex-wrap: wrap; }
  .warning-tags span { padding: .3rem .55rem; border-radius: 999px; background: #ecebf0; font: 650 .72rem ui-monospace, SFMono-Regular, Menlo, monospace; }
  .empty { color: #777480; }
  @media (max-width: 800px) {
    header { display: grid; align-items: start; }
    .guardrail { width: 100%; }
    .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .preference-grid { grid-template-columns: 1fr; }
    .job-list article, .result-head { align-items: flex-start; }
    .job-list article { display: grid; }
    .job-side { justify-items: start; }
    .score-block { justify-items: start; }
    .evidence-list div { grid-template-columns: 1fr; gap: .2rem; }
  }
</style>
