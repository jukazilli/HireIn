<script lang="ts">
  import { onMount } from 'svelte';
  import {
    api,
    type EvaluationErrorCategory,
    type JobMatch,
    type PilotEvaluationUpsert,
    type PilotReviewJob
  } from '$lib/api';

  const fitLabels = ['Não atende', 'Baixa', 'Parcial', 'Boa', 'Muito alinhada'];
  const fitShort = ['Não', 'Pouco', 'Parcial', 'Sim', 'Muito'];
  const intentLabels = ['Não aplicaria', 'Muito improvável', 'Talvez', 'Provavelmente', 'Aplicaria'];
  const intentShort = ['Não', 'Pouco', 'Talvez', 'Sim', 'Muito'];
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
  let loading = true;
  let loadingMatch = false;
  let saving = false;
  let error = '';
  let message = '';

  let professionalFit: number | null = null;
  let applyIntent: number | null = null;
  let blockerReal = false;
  let reason = '';
  let errorCategory: EvaluationErrorCategory | '' = '';

  const matchCache = new Map<string, JobMatch>();

  $: reviewedCount = jobs.filter((job) => job.evaluation).length;

  function fillEvaluation(job: PilotReviewJob) {
    professionalFit = job.evaluation?.relevance ?? null;
    applyIntent = job.evaluation?.apply_intent ?? null;
    blockerReal = job.evaluation?.blocker_real ?? false;
    reason = job.evaluation?.reason ?? '';
    errorCategory = job.evaluation?.error_category ?? '';
  }

  async function loadJobs() { jobs = await api.listReviewJobs(); }

  async function refresh() {
    error = '';
    try {
      await loadJobs();
    } catch (reasonValue) {
      error = reasonValue instanceof Error ? reasonValue.message : 'Não foi possível carregar o piloto.';
    } finally {
      loading = false;
    }
  }

  async function loadMatchForJob(jobId: string, failureMessage: string) {
    const cached = matchCache.get(jobId);
    if (cached) {
      if (selectedJob?.job_id === jobId) {
        match = cached;
        loadingMatch = false;
      }
      return;
    }

    if (selectedJob?.job_id === jobId) loadingMatch = true;
    try {
      const nextMatch = await api.getJobMatch(jobId);
      matchCache.set(jobId, nextMatch);
      if (selectedJob?.job_id === jobId) match = nextMatch;
    } catch (reasonValue) {
      if (selectedJob?.job_id === jobId) {
        error = reasonValue instanceof Error ? reasonValue.message : failureMessage;
      }
    } finally {
      if (selectedJob?.job_id === jobId) loadingMatch = false;
    }
  }

  function selectJob(job: PilotReviewJob) {
    selectedJob = job; fillEvaluation(job); match = null; error = ''; message = '';
    if (!job.evaluation) {
      loadingMatch = false;
      return;
    }
    void loadMatchForJob(job.job_id, 'Não foi possível calcular o Match.');
  }

  async function saveEvaluation() {
    if (!selectedJob || professionalFit === null) return;
    if (!selectedJob.evaluation && applyIntent === null) return;

    const jobId = selectedJob.job_id;
    saving = true; error = ''; message = '';
    let savedSuccessfully = false;
    try {
      const payload: PilotEvaluationUpsert = {
        relevance: professionalFit,
        apply_intent: applyIntent,
        blocker_real: blockerReal,
        reason: reason.trim() || null,
        error_category: errorCategory || null
      };
      const saved = await api.upsertEvaluation(jobId, payload);
      jobs = jobs.map((job) =>
        job.job_id === jobId ? { ...job, evaluation: saved } : job
      );
      selectedJob = jobs.find((job) => job.job_id === jobId) ?? selectedJob;
      matchCache.delete(jobId);
      message = 'Sua avaliação foi salva. O Match está sendo revelado sem bloquear sua navegação.';
      savedSuccessfully = true;
    } catch (reasonValue) {
      error = reasonValue instanceof Error ? reasonValue.message : 'Não foi possível salvar a avaliação.';
    } finally {
      saving = false;
    }

    if (savedSuccessfully) {
      void loadMatchForJob(
        jobId,
        'A avaliação foi salva, mas não foi possível revelar o Match.'
      );
    }
  }

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
      <h1 class="page-title">Primeiro a sua opinião. Depois, a do algoritmo.</h1>
      <p class="page-lead">
        Nas vagas pendentes, o Match fica oculto até você salvar sua avaliação. No Blind #4 separamos
        aderência profissional da sua vontade real de se candidatar para não misturar capacidade com preferência.
      </p>
    </div>
    <aside class="context-note">
      <strong>{reviewedCount}/{jobs.length} vagas revisadas.</strong>
      Sua avaliação é referência do benchmark. Ela não treina nem altera o Match automaticamente.
    </aside>
  </section>

  <div class="status-notice benchmark-note">
    Professional Fit mede o quanto seu perfil atual atende a vaga. Apply Intent mede o quanto você realmente
    gostaria de se candidatar. O Match será comparado ao Professional Fit, não ao desejo de aplicar.
  </div>

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
                  <strong class="human-rating">Fit {job.evaluation.relevance}/4</strong>
                  {#if job.evaluation.apply_intent !== null}
                    <span>Intent {job.evaluation.apply_intent}/4</span>
                  {:else}
                    <span>{fitLabels[job.evaluation.relevance]}</span>
                  {/if}
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
          <h2>Escolha uma vaga para avaliar.</h2>
          <p>Nas vagas pendentes, você avalia Fit e Intent primeiro. O Match aparece somente depois que a sua avaliação for salva.</p>
        </div>
      {:else}
        <div class="work-section review-hero">
          <div class="job-identity">
            <p class="section-kicker">{selectedJob.company_name}</p>
            <h2>{selectedJob.title}</h2>
            <p>{selectedJob.location_text ?? 'Local n/d'} · {selectedJob.work_model ?? 'modalidade n/d'} · {selectedJob.contract_type ?? 'contrato n/d'}</p>
          </div>
          <div class="algorithm-read">
            <span>Professional Fit</span>
            {#if !selectedJob.evaluation}
              <strong>?</strong>
              <small>Revelado após salvar</small>
            {:else if loadingMatch}
              <strong>…</strong>
              <small>Analisando</small>
            {:else if match}
              <strong>{(match.professional_fit?.score ?? match.score) === null ? '—' : `${match.professional_fit?.score ?? match.score}%`}</strong>
              <small>
                {bandLabels[match.professional_fit?.band ?? match.band] ?? (match.professional_fit?.band ?? match.band)}
                · confiança {match.professional_fit?.confidence ?? match.evaluation_coverage}%
              </small>
            {:else}
              <strong>—</strong>
            {/if}
          </div>
        </div>

        {#if match}
          <div class="work-section dimension-summary">
            <div class="dimension-card">
              <span>Professional Fit</span>
              <strong>{(match.professional_fit?.score ?? match.score) === null ? '—' : `${match.professional_fit?.score ?? match.score}%`}</strong>
              <small>Competência profissional · confiança {match.professional_fit?.confidence ?? match.evaluation_coverage}%</small>
            </div>
            <div class="dimension-card" class:blocked={match.opportunity_compatibility?.blocked}>
              <span>Opportunity Compatibility</span>
              <strong>{match.opportunity_compatibility?.score === null || match.opportunity_compatibility?.score === undefined ? '—' : `${match.opportunity_compatibility.score}%`}</strong>
              <small>
                {match.opportunity_compatibility?.blocked
                  ? `Blocker objetivo: ${match.opportunity_compatibility.blockers.join(', ')}`
                  : `Preferências avaliadas: ${match.opportunity_compatibility?.coverage ?? 0}%`}
              </small>
            </div>
            <div class="dimension-card">
              <span>Apply Intent</span>
              <strong>{selectedJob.evaluation?.apply_intent ?? '—'}{selectedJob.evaluation?.apply_intent !== null && selectedJob.evaluation?.apply_intent !== undefined ? '/4' : ''}</strong>
              <small>Declarado por você; não é inferido pelo Match.</small>
            </div>
          </div>

          <div class="work-section match-readout">
            <div class="readout-item"><span>Confiança da evidência</span><strong>{match.professional_fit?.confidence ?? match.evaluation_coverage}%</strong></div>
            <div class="readout-item"><span>Obrigatórios atendidos</span><strong>{match.matched_required}</strong></div>
            <div class="readout-item"><span>Gaps obrigatórios</span><strong>{match.missing_required}</strong></div>
            <div class="readout-item"><span>Não avaliáveis</span><strong>{match.unknown_requirements}</strong></div>
          </div>
        {/if}

        <div class="work-section human-read">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">Professional Fit</p>
              <h2 class="section-title">Quanto seu perfil profissional atual atende esta vaga?</h2>
              <p class="section-description">Ignore por um momento se você gostaria de trabalhar nessa empresa. Avalie somente capacidade, experiência, formação e requisitos.</p>
            </div>
          </div>

          <div class="rating-scale" role="group" aria-label="Professional Fit de zero a quatro">
            {#each fitLabels as label, value}
              <button class:active={professionalFit === value} type="button" onclick={() => (professionalFit = value)}>
                <span>{value}</span>
                <strong>{fitShort[value]}</strong>
                <small>{label}</small>
              </button>
            {/each}
          </div>

          <div class="dimension-divider"></div>

          <div class="section-head intent-head">
            <div class="section-head-copy">
              <p class="section-kicker">Apply Intent</p>
              <h2 class="section-title">Quanto você realmente gostaria de se candidatar?</h2>
              <p class="section-description">Agora considere modalidade, localização, empresa, salário conhecido, momento de carreira e vontade de fazer essa transição.</p>
            </div>
          </div>

          <div class="rating-scale" role="group" aria-label="Apply Intent de zero a quatro">
            {#each intentLabels as label, value}
              <button class:active={applyIntent === value} type="button" onclick={() => (applyIntent = value)}>
                <span>{value}</span>
                <strong>{intentShort[value]}</strong>
                <small>{label}</small>
              </button>
            {/each}
          </div>

          <label class="blocker-row" class:active={blockerReal}>
            <input type="checkbox" bind:checked={blockerReal} />
            <span><strong>Existe um blocker real</strong><small>Algo objetivo que sozinho impediria a candidatura ou tornaria a oportunidade inviável.</small></span>
          </label>

          <div class="form-grid review-fields">
            {#if selectedJob.evaluation}
              <label class="field">Onde o Match mais errou? <small>Opcional, depois de ver o score</small>
                <select bind:value={errorCategory}>
                  <option value="">Nenhum erro dominante / ainda não sei</option>
                  {#each Object.entries(errorLabels) as [value, label]}
                    <option {value}>{label}</option>
                  {/each}
                </select>
              </label>
            {/if}
            <label class="field">Por quê? <small>Opcional, mas valioso</small>
              <textarea rows="5" maxlength="2000" bind:value={reason} placeholder="Ex.: profissionalmente eu atenderia bem, mas não me candidataria por ser presencial; ou eu gostaria da vaga apesar de ainda ter alguns gaps."></textarea>
            </label>
          </div>

          <div class="action-row save-review">
            <span class="muted small">
              {selectedJob.evaluation
                ? 'O Match já foi revelado. Você pode classificar o erro e atualizar suas respostas.'
                : 'Para vagas novas, Fit e Intent são obrigatórios. O Match permanece oculto até salvar.'}
            </span>
            <button class="btn btn-primary" type="button" disabled={saving || professionalFit === null || (!selectedJob.evaluation && applyIntent === null)} onclick={saveEvaluation}>
              {saving ? 'Salvando avaliação…' : selectedJob.evaluation ? 'Atualizar minha avaliação' : 'Salvar e revelar Match'}
            </button>
          </div>
        </div>
      {/if}
    </section>
  </div>
</main>

<style>
  .benchmark-note { margin-bottom: 1rem; }
  .message-space { margin-bottom: 1rem; }
  .review-workspace { grid-template-columns: minmax(300px, .8fr) minmax(0, 1.5fr); }
  .queue-panel { max-height: calc(100vh - var(--nav-height) - 2rem); overflow: auto; }
  .queue-head { margin-bottom: .8rem; }
  .queue-card { padding: .8rem; }
  .human-rating { color: var(--brand-700); font-family: var(--font-display); font-size: .9rem; }
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
  .dimension-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: .65rem; background: var(--surface-subtle); }
  .dimension-card { display: grid; gap: .28rem; min-width: 0; padding: .9rem; border: 1px solid var(--border); border-radius: var(--radius-md); background: white; }
  .dimension-card > span { color: var(--text-muted); font-size: .7rem; }
  .dimension-card > strong { font-family: var(--font-display); font-size: 1.55rem; letter-spacing: -.03em; color: var(--brand-700); }
  .dimension-card > small { color: var(--text-muted); font-size: .72rem; line-height: 1.4; }
  .dimension-card.blocked { border-color: var(--danger); background: var(--danger-soft); }
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
  .dimension-divider { height: 1px; margin: 1.4rem 0; background: var(--border); }
  .intent-head { margin-bottom: .8rem; }
  .blocker-row { display: flex; gap: .75rem; align-items: flex-start; margin-top: 1rem; padding: .9rem; border: 1px solid var(--border); border-radius: var(--radius-md); cursor: pointer; }
  .blocker-row.active { border-color: #f0caca; background: var(--danger-soft); }
  .blocker-row input { margin-top: .2rem; accent-color: var(--danger); }
  .blocker-row span { display: grid; gap: .15rem; }
  .blocker-row small { color: var(--text-muted); font-size: .75rem; }
  .review-fields { margin-top: 1rem; }
  .save-review { margin-bottom: 0; }
  @media (max-width: 900px) {
    .queue-panel { max-height: none; }
    .dimension-summary { grid-template-columns: 1fr; }
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
