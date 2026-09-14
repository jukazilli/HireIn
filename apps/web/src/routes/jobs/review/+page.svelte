<script lang="ts">
  import { onMount } from 'svelte';

  const API = 'http://localhost:8000/api/v1';

  type Evaluation = {
    job_id: string;
    relevance: number;
    blocker_real: boolean;
    reason: string | null;
    error_category: string | null;
  };

  type ReviewJob = {
    job_id: string;
    company_name: string;
    title: string;
    location_text: string | null;
    work_model: string | null;
    contract_type: string | null;
    seniority: string | null;
    requirement_count: number;
    evaluation: Evaluation | null;
  };

  type MatchResult = {
    score: number | null;
    band: string;
    requirement_score: number | null;
    preference_score: number | null;
    evaluation_coverage: number;
    matched_required: number;
    missing_required: number;
    unknown_requirements: number;
    warnings: string[];
  };

  type Report = {
    metrics: {
      sample_count: number;
      relevant_count: number;
      scored_count: number;
      average_coverage: number;
      recall_at_5: number;
      recall_at_10: number;
      ndcg_at_5: number;
      ndcg_at_10: number;
    };
  };

  const ratingLabels = ['Irrelevante', 'Fraca', 'Razoável', 'Boa', 'Excelente'];
  const errorLabels: Record<string, string> = {
    MISSING_PROFILE_EVIDENCE: 'Falta evidência no perfil',
    BAD_JOB_NORMALIZATION: 'Normalização ruim da vaga',
    SIMPLE_ALIAS: 'Alias / nome equivalente simples',
    SEMANTIC_EQUIVALENCE: 'Equivalência semântica',
    PREFERENCE_RULE: 'Regra de preferência',
    COVERAGE_FAILURE: 'Cobertura insuficiente',
    RANKING_WEIGHT: 'Peso / ranking',
    OTHER: 'Outro'
  };

  const bandLabels: Record<string, string> = {
    STRONG: 'Forte',
    GOOD: 'Boa',
    PARTIAL: 'Parcial',
    LOW: 'Baixa',
    INSUFFICIENT_DATA: 'Dados insuficientes'
  };

  let jobs: ReviewJob[] = [];
  let selectedJob: ReviewJob | null = null;
  let match: MatchResult | null = null;
  let report: Report | null = null;
  let loading = true;
  let loadingMatch = false;
  let saving = false;
  let error = '';
  let message = '';

  let relevance: number | null = null;
  let blockerReal = false;
  let reason = '';
  let errorCategory = '';

  function fillEvaluation(job: ReviewJob) {
    relevance = job.evaluation?.relevance ?? null;
    blockerReal = job.evaluation?.blocker_real ?? false;
    reason = job.evaluation?.reason ?? '';
    errorCategory = job.evaluation?.error_category ?? '';
  }

  async function loadJobs() {
    const response = await fetch(`${API}/evals/jobs`);
    if (!response.ok) throw new Error(`Falha ao carregar vagas (${response.status}).`);
    jobs = await response.json();
  }

  async function loadReport() {
    const response = await fetch(`${API}/evals/report`);
    if (response.status === 404) {
      report = null;
      return;
    }
    if (!response.ok) throw new Error(`Falha ao carregar relatório (${response.status}).`);
    report = await response.json();
  }

  async function refresh() {
    error = '';
    try {
      await loadJobs();
      if (jobs.some((job) => job.evaluation)) await loadReport();
      else report = null;
    } catch (reasonValue) {
      error = reasonValue instanceof Error ? reasonValue.message : 'Não foi possível carregar o piloto.';
    } finally {
      loading = false;
    }
  }

  async function selectJob(job: ReviewJob) {
    selectedJob = job;
    fillEvaluation(job);
    match = null;
    error = '';
    message = '';
    loadingMatch = true;
    try {
      const response = await fetch(`${API}/jobs/${job.job_id}/match`);
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? `Falha ao calcular Match (${response.status}).`);
      }
      match = await response.json();
    } catch (reasonValue) {
      error = reasonValue instanceof Error ? reasonValue.message : 'Não foi possível calcular o Match.';
    } finally {
      loadingMatch = false;
    }
  }

  async function saveEvaluation() {
    if (!selectedJob || relevance === null) return;
    saving = true;
    error = '';
    message = '';
    try {
      const response = await fetch(`${API}/evals/jobs/${selectedJob.job_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          relevance,
          blocker_real: blockerReal,
          reason: reason.trim() || null,
          error_category: errorCategory || null
        })
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? `Falha ao salvar (${response.status}).`);
      }
      const saved: Evaluation = await response.json();
      jobs = jobs.map((job) =>
        job.job_id === selectedJob?.job_id ? { ...job, evaluation: saved } : job
      );
      selectedJob = jobs.find((job) => job.job_id === selectedJob?.job_id) ?? selectedJob;
      message = 'Avaliação humana salva.';
      await loadReport();
    } catch (reasonValue) {
      error = reasonValue instanceof Error ? reasonValue.message : 'Não foi possível salvar a avaliação.';
    } finally {
      saving = false;
    }
  }

  const percent = (value: number) => `${Math.round(value * 100)}%`;
  const coverage = (value: number) => `${Math.round(value)}%`;

  onMount(refresh);
</script>

<svelte:head>
  <title>Revisão do piloto · HireIn</title>
  <meta
    name="description"
    content="Rotulagem humana e avaliação do ranking do Match do piloto HireIn."
  />
</svelte:head>

<main>
  <header>
    <div>
      <nav><a href="/jobs/match">← Match</a><a href="/jobs">Job Core</a></nav>
      <p class="eyebrow">HireIn · Pilot Evaluation</p>
      <h1>Ensine o produto com decisões reais.</h1>
      <p class="lead">
        Compare o Match com a sua percepção da vaga. As suas notas são a referência do benchmark;
        elas não alteram o algoritmo automaticamente.
      </p>
    </div>
    <div class="guardrail">
      <span>Dados reais no Git</span><strong>não</strong>
      <span>IA no benchmark</span><strong>não</strong>
      <span>Meta inicial</span><strong>30–50 vagas</strong>
    </div>
  </header>

  {#if report}
    <section class="metric-strip" aria-label="Métricas do piloto">
      <div><span>Avaliadas</span><strong>{report.metrics.sample_count}</strong></div>
      <div><span>Boas ou excelentes</span><strong>{report.metrics.relevant_count}</strong></div>
      <div><span>Recall@5</span><strong>{percent(report.metrics.recall_at_5)}</strong></div>
      <div><span>NDCG@5</span><strong>{percent(report.metrics.ndcg_at_5)}</strong></div>
      <div><span>Cobertura média</span><strong>{coverage(report.metrics.average_coverage)}</strong></div>
    </section>
  {:else}
    <section class="intro-note">
      O benchmark começa quando você salvar a primeira avaliação. Para uma leitura útil de ranking,
      busque pelo menos 5 vagas; o gate de decisão continua sendo 30–50.
    </section>
  {/if}

  {#if error}<div class="notice error" aria-live="polite">{error}</div>{/if}
  {#if message}<div class="notice success" aria-live="polite">{message}</div>{/if}

  <div class="workspace">
    <section class="card jobs-card">
      <div class="section-title">
        <div><p class="eyebrow">Fila de revisão</p><h2>Vagas</h2></div>
        <span>{jobs.filter((job) => job.evaluation).length}/{jobs.length} avaliadas</span>
      </div>

      {#if loading}
        <p class="empty">Carregando…</p>
      {:else if jobs.length === 0}
        <p class="empty">Cadastre vagas no Job Core para iniciar o piloto.</p>
      {:else}
        <div class="job-list">
          {#each jobs as job}
            <button
              type="button"
              class:selected={selectedJob?.job_id === job.job_id}
              onclick={() => selectJob(job)}
            >
              <div>
                <small>{job.company_name}</small>
                <strong>{job.title}</strong>
                <span>{job.location_text ?? 'Local n/d'} · {job.work_model ?? 'modalidade n/d'}</span>
              </div>
              {#if job.evaluation}
                <b title={ratingLabels[job.evaluation.relevance]}>{job.evaluation.relevance}/4</b>
              {:else}
                <em>avaliar</em>
              {/if}
            </button>
          {/each}
        </div>
      {/if}
    </section>

    <section class="card review-card">
      {#if !selectedJob}
        <div class="placeholder">
          <p class="eyebrow">Avaliação humana</p>
          <h2>Escolha uma vaga.</h2>
          <p>Primeiro veja o Match; depois registre o quanto essa oportunidade faz sentido para você.</p>
        </div>
      {:else}
        <div class="review-head">
          <div>
            <p class="eyebrow">Sua referência</p>
            <h2>{selectedJob.title}</h2>
            <p>{selectedJob.company_name}</p>
          </div>
          {#if loadingMatch}
            <div class="match-score muted">…</div>
          {:else if match}
            <div class="match-score">
              <strong>{match.score === null ? '—' : `${match.score}%`}</strong>
              <span>{bandLabels[match.band] ?? match.band}</span>
            </div>
          {/if}
        </div>

        {#if match}
          <div class="match-summary">
            <div><span>Cobertura</span><strong>{match.evaluation_coverage}%</strong></div>
            <div><span>Req. atendidos</span><strong>{match.matched_required}</strong></div>
            <div><span>Req. ausentes</span><strong>{match.missing_required}</strong></div>
            <div><span>Não avaliáveis</span><strong>{match.unknown_requirements}</strong></div>
          </div>
        {/if}

        <div class="divider"></div>
        <fieldset>
          <legend>Quanto essa vaga realmente interessa?</legend>
          <div class="rating-grid">
            {#each ratingLabels as label, value}
              <button
                class:active={relevance === value}
                type="button"
                onclick={() => (relevance = value)}
              >
                <strong>{value}</strong><span>{label}</span>
              </button>
            {/each}
          </div>
        </fieldset>

        <label class="checkbox-row">
          <input type="checkbox" bind:checked={blockerReal} />
          <span><strong>Existe blocker real para mim</strong><small>Algo que por si só faria você descartar a vaga.</small></span>
        </label>

        <label>
          O Match errou principalmente em quê? <span class="optional">opcional</span>
          <select bind:value={errorCategory}>
            <option value="">Nenhum erro dominante / ainda não sei</option>
            {#each Object.entries(errorLabels) as [value, label]}
              <option {value}>{label}</option>
            {/each}
          </select>
        </label>

        <label>
          Motivo <span class="optional">opcional, mas valioso</span>
          <textarea
            rows="5"
            maxlength="2000"
            bind:value={reason}
            placeholder="Ex.: a vaga é boa, mas Protheus e ERP aparecem com nomes diferentes e o Match perdeu essa equivalência."
          ></textarea>
        </label>

        <div class="save-row">
          <small>Essa nota não treina nem altera o algoritmo automaticamente.</small>
          <button
            class="primary"
            type="button"
            disabled={saving || relevance === null}
            onclick={saveEvaluation}
          >
            {saving ? 'Salvando…' : 'Salvar avaliação'}
          </button>
        </div>
      {/if}
    </section>
  </div>
</main>

<style>
  :global(*) { box-sizing: border-box; }
  :global(body) { margin: 0; min-width: 320px; background: #f7f7fa; color: #18181f; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  main { width: min(1180px, calc(100% - 2rem)); margin: 0 auto; padding: 3rem 0 5rem; }
  header { display: flex; justify-content: space-between; gap: 2rem; align-items: flex-end; margin-bottom: 1.2rem; }
  nav { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
  nav a { color: #555361; text-decoration: none; font-size: .9rem; }
  h1 { max-width: 760px; margin: .35rem 0 .8rem; font-size: clamp(2.2rem, 5vw, 4.1rem); line-height: 1; letter-spacing: -.055em; }
  h2, p { margin-top: 0; }
  .lead { max-width: 720px; color: #5e5c69; line-height: 1.6; }
  .eyebrow { margin: 0; color: #6a6877; font-size: .75rem; font-weight: 760; letter-spacing: .09em; text-transform: uppercase; }
  .guardrail { min-width: 230px; display: grid; grid-template-columns: 1fr auto; gap: .65rem 1rem; padding: 1rem 1.1rem; border: 1px solid #e4e3e9; border-radius: 16px; background: white; font-size: .82rem; }
  .metric-strip { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .65rem; margin: 1rem 0; }
  .metric-strip div { display: grid; gap: .3rem; padding: .9rem 1rem; border: 1px solid #e7e6eb; border-radius: 14px; background: white; }
  .metric-strip span { color: #777480; font-size: .76rem; }
  .metric-strip strong { font-size: 1.25rem; }
  .intro-note, .notice { margin: 1rem 0; padding: 1rem 1.1rem; border: 1px solid #e5e3cf; border-radius: 14px; background: #fffef5; color: #5d5940; line-height: 1.5; }
  .notice.error { border-color: #ead5d5; background: #fff8f8; color: #823a3a; }
  .notice.success { border-color: #d8e5d9; background: #f8fff8; color: #426348; }
  .workspace { display: grid; grid-template-columns: minmax(320px, .75fr) minmax(0, 1.25fr); gap: 1rem; align-items: start; }
  .card { padding: clamp(1.2rem, 2.6vw, 1.8rem); border: 1px solid #e6e5eb; border-radius: 22px; background: white; }
  .section-title, .review-head, .save-row { display: flex; justify-content: space-between; gap: 1rem; align-items: center; }
  .section-title { margin-bottom: 1rem; }
  .section-title h2 { margin: .2rem 0 0; }
  .section-title > span { color: #777480; font-size: .82rem; }
  .job-list { display: grid; gap: .55rem; max-height: 720px; overflow: auto; padding-right: .2rem; }
  .job-list > button { width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .9rem; border: 1px solid #ecebf0; border-radius: 14px; background: white; color: inherit; text-align: left; cursor: pointer; }
  .job-list > button.selected { border-color: #b8b6c1; background: #fafafd; }
  .job-list div { display: grid; gap: .18rem; }
  .job-list small, .job-list span { color: #777480; }
  .job-list span { font-size: .78rem; }
  .job-list b { min-width: 42px; text-align: center; font-size: .82rem; }
  .job-list em { color: #817e8b; font-size: .78rem; font-style: normal; }
  .placeholder { min-height: 350px; display: grid; place-content: center; max-width: 520px; color: #66636f; }
  .placeholder h2 { margin: .4rem 0 .6rem; color: #18181f; }
  .review-head { align-items: flex-start; }
  .review-head h2 { margin: .25rem 0; }
  .review-head p:last-child { color: #6c6975; }
  .match-score { min-width: 120px; display: grid; justify-items: end; }
  .match-score strong { font-size: 2.6rem; line-height: 1; letter-spacing: -.055em; }
  .match-score span { margin-top: .35rem; color: #6d6a76; font-size: .82rem; font-weight: 700; }
  .match-score.muted { color: #aaa8b0; font-size: 2rem; }
  .match-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .55rem; margin-top: 1rem; }
  .match-summary div { display: grid; gap: .28rem; padding: .8rem; border: 1px solid #eeedf1; border-radius: 12px; }
  .match-summary span { color: #777480; font-size: .72rem; }
  .divider { height: 1px; margin: 1.35rem 0; background: #eeedf1; }
  fieldset { margin: 0 0 1.2rem; padding: 0; border: 0; }
  legend { margin-bottom: .75rem; font-size: .88rem; font-weight: 720; }
  .rating-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .45rem; }
  .rating-grid button { display: grid; gap: .25rem; min-height: 70px; padding: .65rem .4rem; border: 1px solid #dfdee5; border-radius: 12px; background: white; color: #34323b; cursor: pointer; }
  .rating-grid button.active { border-color: #222128; background: #222128; color: white; }
  .rating-grid strong { font-size: 1.15rem; }
  .rating-grid span { font-size: .68rem; }
  label { display: grid; gap: .45rem; margin-top: 1rem; color: #45434e; font-size: .84rem; }
  select, textarea { width: 100%; border: 1px solid #dcdbe2; border-radius: 11px; background: white; color: #1f1e24; font: inherit; padding: .72rem .78rem; }
  textarea { resize: vertical; line-height: 1.45; }
  .optional { color: #8b8893; font-weight: 400; }
  .checkbox-row { grid-template-columns: auto 1fr; align-items: start; padding: .85rem; border: 1px solid #ecebf0; border-radius: 12px; }
  .checkbox-row input { margin-top: .18rem; }
  .checkbox-row span { display: grid; gap: .18rem; }
  .checkbox-row small { color: #777480; font-weight: 400; }
  .save-row { margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid #eeedf1; }
  .save-row small { max-width: 380px; color: #777480; line-height: 1.4; }
  .primary { border: 0; border-radius: 11px; padding: .78rem 1rem; background: #1f1e24; color: white; font-weight: 720; cursor: pointer; }
  .primary:disabled { opacity: .45; cursor: not-allowed; }
  .empty { color: #777480; }
  @media (max-width: 900px) {
    header { display: grid; align-items: stretch; }
    .guardrail { min-width: 0; }
    .metric-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .workspace { grid-template-columns: 1fr; }
    .job-list { max-height: 430px; }
  }
  @media (max-width: 620px) {
    main { width: min(100% - 1rem, 1180px); padding-top: 1.5rem; }
    .rating-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .match-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .review-head { align-items: center; }
    .save-row { align-items: flex-start; flex-direction: column; }
  }
</style>
