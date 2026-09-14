<script lang="ts">
  import { onMount } from 'svelte';
  import {
    api,
    type EvaluationErrorCategory,
    type JobMatch,
    type PilotEvalReport,
    type PilotEvaluationUpsert,
    type PilotReviewJob
  } from '$lib/api';

  const ratingLabels = ['Irrelevante', 'Fraca', 'Razoável', 'Boa', 'Excelente'];
  const ratingShort = ['Não', 'Pouco', 'Talvez', 'Sim', 'Muito'];
  const errorLabels: Record<string, string> = {
    MISSING_PROFILE_EVIDENCE: 'Falta evidência no perfil',
    BAD_JOB_NORMALIZATION: 'Normalização ruim da vaga',
    SIMPLE_ALIAS: 'Alias / nome equivalente simples',
    SEMANTIC_EQUIVALENCE: 'Equivalência semântica',
    PREFERENCE_RULE: 'Regra de preferência',
    COVERAGE_FAILURE: 'Cobertura insuficiente',
    RANKING_WEIGHT: 'Peso / ranking', OTHER: 'Outro'
  };

  const bandLabels: Record<string, string> = {
    STRONG: 'Forte', GOOD: 'Boa', PARTIAL: 'Parcial', LOW: 'Baixa',
    INSUFFICIENT_DATA: 'Dados insuficientes'
  };

  let jobs: PilotReviewJob[] = [];
  let selectedJob: PilotReviewJob | null = null;
  let match: JobMatch | null = null;
  let report: PilotEvalReport | null = null;
  let loading = true;
  let loadingMatch = false;
  let saving = false;
  let error = '';
  let message = '';

  let relevance: number | null = null;
  let blockerReal = false;
  let reason = '';
  let errorCategory: EvaluationErrorCategory | '' = '';

  $: reviewedCount = jobs.filter((job) => job.evaluation).length;

  function fillEvaluation(job: PilotReviewJob) {
    relevance = job.evaluation?.relevance ?? null;
    blockerReal = job.evaluation?.blocker_real ?? false;
    reason = job.evaluation?.reason ?? '';
    errorCategory = job.evaluation?.error_category ?? '';
  }

  async function loadJobs() { jobs = await api.listReviewJobs(); }
  async function loadReport() { report = await api.getEvalReport(); }

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

  async function selectJob(job: PilotReviewJob) {
    selectedJob = job; fillEvaluation(job); match = null; error = ''; message = ''; loadingMatch = true;
    try {
      match = await api.getJobMatch(job.job_id);
    } catch (reasonValue) {
      error = reasonValue instanceof Error ? reasonValue.message : 'Não foi possível calcular o Match.';
    } finally {
      loadingMatch = false;
    }
  }

  async function saveEvaluation() {
    if (!selectedJob || relevance === null) return;
    saving = true; error = ''; message = '';
    try {
      const payload: PilotEvaluationUpsert = {
        relevance,
        blocker_real: blockerReal,
        reason: reason.trim() || null,
        error_category: errorCategory || null
      };
      const saved = await api.upsertEvaluation(selectedJob.job_id, payload);
      jobs = jobs.map((job) =>
        job.job_id === selectedJob?.job_id ? { ...job, evaluation: saved } : job
      );
      selectedJob = jobs.find((job) => job.job_id === selectedJob?.job_id) ?? selectedJob;
      message = 'Sua avaliação foi salva sem alterar o algoritmo.';
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
  <title>Revisar vagas · HireIn</title>
  <meta name="description" content="Avaliação humana do Match no piloto HireIn." />
</svelte:head>

<main class="app-main">
  <section class="page-intro">
    <div class="page-intro-copy">
      <p class="eyebrow">Revisão humana</p>
      <h1 class="page-title">O algoritmo tem uma opinião. Agora queremos a sua.</h1>
      <p class="page-lead">
        Compare o Match com a sua leitura da oportunidade. Essa diferença mostra onde o produto precisa
        melhorar antes de receber mais automação ou IA.
      </p>
    </div>
    <aside class="context-note">
      <strong>{reviewedCount}/{jobs.length} vagas revisadas.</strong>
      A sua nota é referência do benchmark. Ela não treina nem altera o Match automaticamente.
    </aside>
  </section>

  {#if report}
    <section class="benchmark-line" aria-label="Sinais atuais do benchmark">
      <div><span>Recall@5</span><strong>{percent(report.metrics.recall_at_5)}</strong></div>
      <div><span>NDCG@5</span><strong>{percent(report.metrics.ndcg_at_5)}</strong></div>
      <div><span>Cobertura média</span><strong>{coverage(report.metrics.average_coverage)}</strong></div>
      <p>{report.metrics.sample_count} avaliações · {report.metrics.relevant_count} vagas boas ou excelentes</p>
    </section>
  {:else}
    <div class="status-notice benchmark-note">O benchmark aparece depois da primeira avaliação. O smoke test começa com 5 vagas; a decisão técnica vem entre 30 e 50.</div>
  {/if}

  {#if error}<div class="status-notice error message-space" aria-live="polite">{error}</div>{/if}
  {#if message}<div class="status-notice success message-space" aria-live="polite">{message}</div>{/if}

  <div class="split-workspace review-workspace">
    <aside class="surface surface-padded sticky-panel queue-panel">
      <div class="section-head queue-head">
        <div class="section-head-copy">
          <p class="section-kicker">Fila</p>
          <h2 class="section-title">Escolha a próxima</h2>
        </div>
        <span class="section-meta">{reviewedCount}/{jobs.length}</span>
      </div>

      {#if loading}
        <div class="status-notice">Carregando vagas…</div>
      {:else if jobs.length === 0}
        <div class="empty-state">Cadastre vagas reais antes de iniciar a revisão.</div>
      {:else}
        <div class="opportunity-list review-queue">
          {#each jobs as job}
            <button class="opportunity-card queue-card" class:selected={selectedJob?.job_id === job.job_id} type="button" onclick={() => selectJob(job)}>
              <div>
                <p class="opportunity-company">{job.company_name}</p>
                <h3 class="opportunity-title">{job.title}</h3>
                <p class="opportunity-meta">{job.location_text ?? 'Local n/d'} · {job.work_model ?? 'modalidade n/d'}</p>
              </div>
              <div class="opportunity-side">
                {#if job.evaluation}
                  <strong class="human-rating">{job.evaluation.relevance}/4</strong>
                  <span>{ratingLabels[job.evaluation.relevance]}</span>
                {:else}
                  <strong class="pending-label">Pendente</strong>
                {/if}
              </div>
            </button>
          {/each}
        </div>
      {/if}
    </aside>

    <section class="work-surface review-panel">
      {#if !selectedJob}
        <div class="review-placeholder">
          <span class="placeholder-line"></span>
          <p class="section-kicker">Sua leitura</p>
          <h2>Escolha uma vaga para comparar.</h2>
          <p>Primeiro mostramos o Match. Depois você registra o quanto essa oportunidade realmente faz sentido para o seu momento.</p>
        </div>
      {:else}
        <div class="work-section review-hero">
          <div class="job-identity">
            <p class="section-kicker">{selectedJob.company_name}</p>
            <h2>{selectedJob.title}</h2>
            <p>{selectedJob.location_text ?? 'Local n/d'} · {selectedJob.work_model ?? 'modalidade n/d'} · {selectedJob.contract_type ?? 'contrato n/d'}</p>
          </div>
          <div class="algorithm-read">
            <span>Leitura do HireIn</span>
            {#if loadingMatch}
              <strong>…</strong>
              <small>Analisando</small>
            {:else if match}
              <strong>{match.score === null ? '—' : `${match.score}%`}</strong>
              <small>{bandLabels[match.band] ?? match.band}</small>
            {:else}
              <strong>—</strong>
            {/if}
          </div>
        </div>

        {#if match}
          <div class="work-section match-readout">
            <div class="readout-item"><span>Cobertura</span><strong>{match.evaluation_coverage}%</strong></div>
            <div class="readout-item"><span>Obrigatórios atendidos</span><strong>{match.matched_required}</strong></div>
            <div class="readout-item"><span>Gaps obrigatórios</span><strong>{match.missing_required}</strong></div>
            <div class="readout-item"><span>Não avaliáveis</span><strong>{match.unknown_requirements}</strong></div>
          </div>
        {/if}

        <div class="work-section human-read">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">Sua decisão</p>
              <h2 class="section-title">Quanto essa vaga faz sentido para você?</h2>
              <p class="section-description">Não tente concordar com o score. Responda como candidato.</p>
            </div>
          </div>

          <div class="rating-scale" role="group" aria-label="Relevância da vaga de zero a quatro">
            {#each ratingLabels as label, value}
              <button class:active={relevance === value} type="button" onclick={() => (relevance = value)}>
                <span>{value}</span>
                <strong>{ratingShort[value]}</strong>
                <small>{label}</small>
              </button>
            {/each}
          </div>

          <label class="blocker-row" class:active={blockerReal}>
            <input type="checkbox" bind:checked={blockerReal} />
            <span><strong>Existe um blocker real</strong><small>Algo que sozinho faria você descartar esta oportunidade, independentemente do score.</small></span>
          </label>

          <div class="form-grid review-fields">
            <label class="field">Onde o Match mais errou? <small>Opcional</small>
              <select bind:value={errorCategory}>
                <option value="">Nenhum erro dominante / ainda não sei</option>
                {#each Object.entries(errorLabels) as [value, label]}
                  <option {value}>{label}</option>
                {/each}
              </select>
            </label>
            <label class="field">Por quê? <small>Opcional, mas valioso</small>
              <textarea rows="5" maxlength="2000" bind:value={reason} placeholder="Ex.: a vaga é boa, mas Protheus e ERP aparecem com nomes diferentes e o Match perdeu essa equivalência."></textarea>
            </label>
          </div>

          <div class="action-row save-review">
            <span class="muted small">Sua avaliação fica separada do algoritmo para podermos medir melhora de verdade.</span>
            <button class="btn btn-primary" type="button" disabled={saving || relevance === null} onclick={saveEvaluation}>
              {saving ? 'Salvando avaliação…' : 'Salvar minha avaliação'}
            </button>
          </div>
        </div>
      {/if}
    </section>
  </div>
</main>

<style>
  .benchmark-line { display: flex; align-items: center; gap: 1.35rem; margin-bottom: 1rem; padding: .85rem 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
  .benchmark-line > div { display: flex; gap: .4rem; align-items: baseline; }
  .benchmark-line span { color: var(--text-muted); font-size: .75rem; }
  .benchmark-line strong { font-size: .92rem; }
  .benchmark-line p { margin: 0 0 0 auto; color: var(--text-muted); font-size: .76rem; }
  .benchmark-note { margin-bottom: 1rem; }
  .message-space { margin-bottom: 1rem; }
  .review-workspace { grid-template-columns: minmax(300px, .8fr) minmax(0, 1.5fr); }
  .queue-panel { max-height: calc(100vh - var(--nav-height) - 2rem); overflow: auto; }
  .queue-head { margin-bottom: .8rem; }
  .queue-card { padding: .8rem; }
  .human-rating { color: var(--brand-700); font-family: var(--font-display); font-size: 1rem; }
  .pending-label { color: var(--text-muted); font-size: .7rem; text-transform: uppercase; letter-spacing: .06em; }
  .review-panel { min-height: 520px; }
  .review-placeholder { min-height: 520px; display: grid; align-content: center; justify-items: start; padding: clamp(1.5rem, 6vw, 4rem); }
  .review-placeholder h2 { margin: .35rem 0 .5rem; font-size: clamp(1.8rem, 4vw, 3rem); }
  .review-placeholder p:last-child { max-width: 560px; color: var(--text-muted); line-height: 1.6; }
  .placeholder-line { width: 54px; height: 7px; margin-bottom: 1.2rem; border-radius: 999px; background: var(--lime-400); transform: rotate(-5deg); }
  .review-hero { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
  .job-identity h2 { margin: .2rem 0 .3rem; font-size: clamp(1.6rem, 3vw, 2.4rem); }
  .job-identity > p:last-child { margin: 0; color: var(--text-muted); font-size: .82rem; }
  .algorithm-read { display: grid; min-width: 150px; justify-items: end; }
  .algorithm-read span { color: var(--text-muted); font-size: .72rem; }
  .algorithm-read strong { font-family: var(--font-display); font-size: 2.7rem; line-height: 1; letter-spacing: -.06em; color: var(--brand-700); }
  .algorithm-read small { margin-top: .2rem; color: var(--text-muted); }
  .match-readout { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; padding-top: 0; padding-bottom: 0; }
  .readout-item { display: grid; gap: .2rem; padding: 1rem; border-left: 1px solid var(--border); }
  .readout-item:first-child { border-left: 0; padding-left: 0; }
  .readout-item span { color: var(--text-muted); font-size: .72rem; }
  .readout-item strong { font-size: 1rem; }
  .rating-scale { display: grid; grid-template-columns: repeat(5, 1fr); gap: .45rem; }
  .rating-scale button { display: grid; gap: .12rem; min-height: 92px; padding: .65rem; border: 1px solid var(--border); border-radius: var(--radius-md); background: white; color: var(--text-secondary); cursor: pointer; text-align: left; }
  .rating-scale button:hover { border-color: var(--brand-200); }
  .rating-scale button.active { border-color: var(--brand-400); background: var(--brand-50); color: var(--brand-800); box-shadow: inset 0 -3px 0 var(--lime-400); }
  .rating-scale button > span { color: var(--text-muted); font-size: .68rem; }
  .rating-scale button > strong { font-size: .9rem; }
  .rating-scale button > small { color: var(--text-muted); font-size: .68rem; }
  .blocker-row { display: flex; gap: .75rem; align-items: flex-start; margin-top: 1rem; padding: .9rem; border: 1px solid var(--border); border-radius: var(--radius-md); cursor: pointer; }
  .blocker-row.active { border-color: #f0caca; background: var(--danger-soft); }
  .blocker-row input { margin-top: .2rem; accent-color: var(--danger); }
  .blocker-row span { display: grid; gap: .15rem; }
  .blocker-row small { color: var(--text-muted); font-size: .75rem; }
  .review-fields { margin-top: 1rem; }
  .save-review { margin-bottom: 0; }
  @media (max-width: 900px) {
    .benchmark-line { flex-wrap: wrap; }
    .benchmark-line p { width: 100%; margin-left: 0; }
    .queue-panel { max-height: none; }
    .match-readout { grid-template-columns: repeat(2, 1fr); }
    .readout-item:nth-child(3) { border-left: 0; }
  }
  @media (max-width: 640px) {
    .review-hero { flex-direction: column; }
    .algorithm-read { justify-items: start; }
    .rating-scale { grid-template-columns: 1fr; }
    .rating-scale button { min-height: 0; grid-template-columns: 28px 1fr auto; align-items: center; text-align: left; }
    .rating-scale button > small { justify-self: end; }
    .match-readout { grid-template-columns: 1fr 1fr; }
    .readout-item { border-left: 0; border-top: 1px solid var(--border); padding-left: 0; }
  }
</style>
