<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type EvidenceDecision, type EvidenceGapItem, type EvidenceGapList, type JobMatch, type JobSummary } from '$lib/api';

  let jobs: JobSummary[] = [];
  let reviewedJobIds = new Set<string>();
  let selectedJob: JobSummary | null = null;
  let result: JobMatch | null = null;
  let loading = true;
  let calculating = false;
  let error = '';
  let evidenceGaps: EvidenceGapList | null = null;
  let evidenceError = '';
  let evidenceMessage = '';
  let evidenceSavingId = '';
  let atomicEditingId = '';
  let atomicDrafts: Record<string, string[]> = {};

  const bandLabel: Record<string, string> = {
    STRONG: 'Aderência profissional forte', GOOD: 'Boa aderência profissional',
    PARTIAL: 'Aderência profissional parcial', LOW: 'Aderência profissional baixa',
    INSUFFICIENT_DATA: 'Dados insuficientes'
  };

  const statusLabel: Record<string, string> = {
    MATCHED: 'Atendido', GAP: 'Gap', UNKNOWN: 'Não avaliável', INFO: 'Informativo',
    ALIGNED: 'Alinhado', CONFLICT: 'Conflito'
  };

  const resolutionLabel: Record<EvidenceDecision, string> = {
    CONFIRMED: 'Confirmado por você',
    PARTIAL: 'Você possui parte dos itens',
    NOT_HAVE: 'Você indicou que não possui',
    UNSURE: 'Ainda não confirmado'
  };

  async function loadJobs() {
    try {
      const [jobRows, reviewRows] = await Promise.all([
        api.listJobs(),
        api.listReviewJobs()
      ]);
      jobs = jobRows;
      reviewedJobIds = new Set(
        reviewRows.filter((job) => job.evaluation).map((job) => job.job_id)
      );
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível carregar as vagas.';
    } finally {
      loading = false;
    }
  }

  async function loadEvidenceGaps(jobId: string) {
    try {
      evidenceGaps = await api.getEvidenceGaps(jobId);
    } catch (reason) {
      evidenceGaps = null;
      evidenceError = reason instanceof Error ? reason.message : 'Não foi possível carregar as lacunas de evidência.';
    }
  }

  async function calculate(job: JobSummary) {
    if (!reviewedJobIds.has(job.id)) {
      error = 'Avalie esta vaga em Revisar vagas antes de abrir o Match.';
      return;
    }

    selectedJob = job;
    result = null;
    evidenceGaps = null;
    error = '';
    evidenceError = '';
    evidenceMessage = '';
    atomicEditingId = '';
    atomicDrafts = {};
    calculating = true;
    try {
      result = await api.getJobMatch(job.id);
      if (result.unknown_requirements > 0) {
        await loadEvidenceGaps(job.id);
      }
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível calcular o Match.';
    } finally {
      calculating = false;
    }
  }

  function beginAtomicSelection(gap: EvidenceGapItem) {
    atomicEditingId = gap.requirement_id;
    atomicDrafts = {
      ...atomicDrafts,
      [gap.requirement_id]: [...(gap.resolution?.confirmed_atoms ?? [])]
    };
    evidenceError = '';
    evidenceMessage = '';
  }

  function toggleAtomicOption(gap: EvidenceGapItem, option: string) {
    const current = atomicDrafts[gap.requirement_id] ?? [];
    atomicDrafts = {
      ...atomicDrafts,
      [gap.requirement_id]: current.includes(option)
        ? current.filter((item) => item !== option)
        : [...current, option]
    };
  }

  async function resolveGap(
    gap: EvidenceGapItem,
    decision: EvidenceDecision,
    confirmedAtoms: string[] = []
  ) {
    if (!selectedJob) return;

    evidenceSavingId = gap.requirement_id;
    evidenceError = '';
    evidenceMessage = '';
    try {
      const saved = await api.upsertEvidenceResolution(selectedJob.id, gap.requirement_id, {
        decision,
        evidence_text: null,
        confirmed_atoms: confirmedAtoms
      });

      [result, evidenceGaps] = await Promise.all([
        api.getJobMatch(selectedJob.id),
        api.getEvidenceGaps(selectedJob.id)
      ]);
      atomicEditingId = '';
      evidenceMessage =
        saved.decision === 'CONFIRMED'
          ? 'Experiência confirmada. O HireIn aprendeu os conceitos selecionados e recalculou o Professional Fit.'
          : saved.decision === 'PARTIAL'
            ? 'Conhecimento parcial salvo. Os itens confirmados foram aprendidos, mas o requisito completo continua como gap.'
            : saved.decision === 'NOT_HAVE'
              ? 'Gap confirmado por você. O Professional Fit foi recalculado.'
              : 'Item mantido como desconhecido.';
    } catch (reason) {
      evidenceError = reason instanceof Error ? reason.message : 'Não foi possível salvar sua resposta.';
    } finally {
      evidenceSavingId = '';
    }
  }

  onMount(loadJobs);
</script>

<svelte:head>
  <title>Match · HireIn</title>
  <meta name="description" content="Compatibilidade explicável entre perfil e vagas no HireIn." />
</svelte:head>

<main class="app-main">
  <section class="page-intro">
    <div class="page-intro-copy">
      <p class="eyebrow">HireIn Match</p>
      <h1 class="page-title">Não basta dizer que combina. Mostre o porquê.</h1>
      <p class="page-lead">
        O Match só é liberado depois que a avaliação humana da vaga estiver salva. Isso protege o holdout contra
        contaminação acidental. No v1.12, baixa cobertura deixa de parecer certeza: Fit observado, confiança e faixa possível ficam separados.
      </p>
    </div>
    <aside class="context-note">
      <strong>Match v1.12 com confiança explícita.</strong>
      Professional Fit continua baseado em evidências confirmadas. O sinal de ranking é ajustado pela cobertura e requisitos UNKNOWN permanecem como incerteza, não como gap.
    </aside>
  </section>

  {#if error}<div class="status-notice error" aria-live="polite">{error}</div>{/if}

  <section class="surface surface-padded">
    <div class="section-head">
      <div class="section-head-copy">
        <p class="section-kicker">Escolha a oportunidade</p>
        <h2 class="section-title">Qual vaga você quer entender?</h2>
        <p class="section-description">Vagas ainda não avaliadas ficam bloqueadas. Primeiro finalize Fit + Intent em Revisar vagas.</p>
      </div>
      <span class="section-meta">{jobs.length} vaga{jobs.length === 1 ? '' : 's'}</span>
    </div>

    {#if loading}
      <div class="status-notice">Carregando vagas do piloto…</div>
    {:else if jobs.length === 0}
      <div class="empty-state">Cadastre uma vaga real antes de calcular compatibilidade.</div>
    {:else}
      <div class="opportunity-list job-picker">
        {#each jobs as job}
          <button
            class="opportunity-card"
            class:selected={selectedJob?.id === job.id}
            class:holdout-locked={!reviewedJobIds.has(job.id)}
            type="button"
            disabled={calculating || !reviewedJobIds.has(job.id)}
            onclick={() => calculate(job)}
          >
            <div>
              <p class="opportunity-company">{job.company_name}</p>
              <h3 class="opportunity-title">{job.title}</h3>
              <p class="opportunity-meta">{job.location_text ?? 'Local não informado'} · {job.work_model ?? 'modalidade n/d'} · {job.contract_type ?? 'contrato n/d'}</p>
            </div>
            <div class="opportunity-side">
              <span>{job.requirement_count} requisitos</span>
              <strong class="match-link">
                {!reviewedJobIds.has(job.id)
                  ? 'Avalie primeiro'
                  : calculating && selectedJob?.id === job.id
                    ? 'Analisando…'
                    : 'Ver compatibilidade'}
              </strong>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </section>

  {#if result && selectedJob}
    <section class="result-space" aria-live="polite">
      <div class="match-overview">
        <div class="match-score-panel">
          <div>
            <p class="eyebrow">Professional Fit</p>
            {#if (result.professional_fit?.band ?? result.band) === 'INSUFFICIENT_DATA'}
              <span class="match-score-state">Aderência ainda incerta</span>
              <p class="match-score-label">{result.professional_fit?.confidence ?? result.evaluation_coverage}% dos requisitos avaliados</p>
            {:else}
              <span class="match-score-value">{(result.professional_fit?.score ?? result.score) === null ? '—' : `${result.professional_fit?.score ?? result.score}%`}</span>
              <p class="match-score-label">{bandLabel[result.professional_fit?.band ?? result.band] ?? (result.professional_fit?.band ?? result.band)}</p>
            {/if}
          </div>
          <small>
            {#if result.professional_fit?.score_floor !== null && result.professional_fit?.score_floor !== undefined && result.professional_fit?.score_ceiling !== null && result.professional_fit?.score_ceiling !== undefined}
              Faixa possível {result.professional_fit.score_floor}%–{result.professional_fit.score_ceiling}% · sinal de ranking {result.professional_fit.ranking_score ?? '—'}
            {:else}
              Sem evidência profissional suficiente para estimar uma faixa.
            {/if}
          </small>
        </div>
        <div class="match-summary-panel">
          <p class="section-kicker">{selectedJob.company_name}</p>
          <h2 class="selected-title">{selectedJob.title}</h2>
          <p class="selected-meta">{selectedJob.location_text ?? 'Local n/d'} · {selectedJob.work_model ?? 'modalidade n/d'} · {selectedJob.contract_type ?? 'contrato n/d'}</p>

          <div class="dimension-strip">
            <div class="dimension-read">
              <span>Professional Fit</span>
              <strong>
                {(result.professional_fit?.band ?? result.band) === 'INSUFFICIENT_DATA'
                  ? 'Incerto'
                  : (result.professional_fit?.score ?? result.score) === null
                    ? '—'
                    : `${result.professional_fit?.score ?? result.score}%`}
              </strong>
              <small>
                confiança {result.professional_fit?.confidence ?? result.evaluation_coverage}%
                {result.professional_fit?.ranking_score !== null && result.professional_fit?.ranking_score !== undefined
                  ? ` · ranking ${result.professional_fit.ranking_score}`
                  : ''}
              </small>
            </div>
            <div class="dimension-read" class:blocked={result.opportunity_compatibility?.blocked}>
              <span>Opportunity Compatibility</span>
              <strong>{result.opportunity_compatibility?.score === null || result.opportunity_compatibility?.score === undefined ? '—' : `${result.opportunity_compatibility.score}%`}</strong>
              <small>{result.opportunity_compatibility?.blocked ? 'blocker objetivo' : `cobertura ${result.opportunity_compatibility?.coverage ?? 0}%`}</small>
            </div>
            <div class="dimension-read">
              <span>Apply Intent</span>
              <strong>Humano</strong>
              <small>declarado por você na revisão</small>
            </div>
          </div>

          <div class="match-facts">
            <div class="match-fact"><span>Confiança da evidência</span><strong>{result.professional_fit?.confidence ?? result.evaluation_coverage}%</strong></div>
            <div class="match-fact"><span>Requisitos atendidos</span><strong>{result.matched_required} obrigatórios</strong></div>
            <div class="match-fact"><span>Gaps obrigatórios</span><strong>{result.missing_required}</strong></div>
            <div class="match-fact"><span>Itens não avaliáveis</span><strong>{result.unknown_requirements}</strong></div>
          </div>

          {#if result.opportunity_compatibility?.blocked}
            <div class="status-notice warning opportunity-note">
              Esta oportunidade possui blocker objetivo ({result.opportunity_compatibility.blockers.join(', ')}), mas isso não reduz seu Professional Fit.
            </div>
          {/if}

          {#if (result.professional_fit?.band ?? result.band) === 'INSUFFICIENT_DATA'}
            <div class="status-notice warning insufficient-note">
              A confiança está abaixo de 60%. O HireIn não apresenta o Fit observado como certeza: a faixa possível mantém os UNKNOWNs explícitos e o sinal de ranking é puxado para um prior neutro de 50 até haver mais evidência.
            </div>
          {/if}
        </div>
      </div>

      {#if evidenceGaps && evidenceGaps.baseline_unknown_count > 0}
        <section class="surface surface-padded evidence-resolver">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">Evidence Gap Resolver</p>
              <h2 class="section-title">O que ainda vale a pena confirmar?</h2>
              <p class="section-description">
                O HireIn pergunta apenas sobre itens que o v1.7 não conseguiu comprovar nem negar. Requisitos simples continuam com Tenho, Não tenho ou Não sei; listas como “Bizagi, Visio ou Miro” pedem quais itens você realmente possui.
              </p>
            </div>
            <div class="resolver-confidence">
              <span>Confiança atual</span>
              <strong>{evidenceGaps.current_confidence}%</strong>
            </div>
          </div>

          {#if evidenceMessage}<div class="status-notice success" aria-live="polite">{evidenceMessage}</div>{/if}
          {#if evidenceError}<div class="status-notice error" role="alert">{evidenceError}</div>{/if}

          {#if evidenceGaps.gaps.length > 0}
            <div class="evidence-gap-list">
              {#each evidenceGaps.gaps as gap}
                <article class="evidence-gap-card">
                  <div class="evidence-gap-head">
                    <div>
                      <span class="status-chip" data-status="UNKNOWN">{gap.importance === 'REQUIRED' ? 'Obrigatório' : 'Preferencial'}</span>
                      <h3>{gap.value}</h3>
                    </div>
                    <span class="impact-badge">até +{gap.coverage_impact} p.p. de cobertura</span>
                  </div>

                  <p class="evidence-question">{gap.question}</p>

                  {#if gap.partial_evidence.length > 0}
                    <div class="partial-evidence">
                      <span>Já encontramos parte da evidência:</span>
                      {#each gap.partial_evidence as item}
                        <strong>{item.value}</strong>
                      {/each}
                    </div>
                  {/if}

                  {#if gap.resolution}
                    <div class="resolution-state" data-decision={gap.resolution.decision}>
                      <strong>{resolutionLabel[gap.resolution.decision]}</strong>
                      {#if gap.resolution.confirmed_atoms.length > 0}
                        <div class="confirmed-atom-list">
                          {#each gap.resolution.confirmed_atoms as atom}<span>{atom}</span>{/each}
                        </div>
                      {:else if gap.resolution.decision === 'CONFIRMED'}
                        <span>Conhecimento incorporado ao perfil para futuras análises.</span>
                      {/if}
                    </div>
                  {/if}

                  {#if gap.atomic_options.length > 0 && atomicEditingId === gap.requirement_id}
                    <div class="atomic-editor">
                      <div class="atomic-guidance">
                        <strong>Selecione exatamente o que você possui</strong>
                        <span>
                          {gap.atomic_operator === 'ANY'
                            ? 'Um ou mais itens podem atender este requisito. Marque tudo que se aplica a você.'
                            : 'O requisito completo pede todos os itens. Selecione tudo que você realmente possui.'}
                        </span>
                      </div>
                      <div class="atomic-options" role="group" aria-label="Itens confirmados">
                        {#each gap.atomic_options as option}
                          <button
                            type="button"
                            class:active={(atomicDrafts[gap.requirement_id] ?? []).includes(option)}
                            aria-pressed={(atomicDrafts[gap.requirement_id] ?? []).includes(option)}
                            onclick={() => toggleAtomicOption(gap, option)}
                          >{option}</button>
                        {/each}
                      </div>
                      <div class="resolver-actions">
                        <button
                          class="btn btn-primary"
                          type="button"
                          disabled={evidenceSavingId === gap.requirement_id || (atomicDrafts[gap.requirement_id] ?? []).length === 0}
                          onclick={() => resolveGap(gap, 'CONFIRMED', atomicDrafts[gap.requirement_id] ?? [])}
                        >Confirmar seleção</button>
                        <button
                          class="btn btn-ghost"
                          type="button"
                          disabled={evidenceSavingId === gap.requirement_id}
                          onclick={() => (atomicEditingId = '')}
                        >Cancelar</button>
                      </div>
                    </div>
                  {:else}
                    <div class="resolver-actions">
                      <button
                        class="btn btn-primary"
                        type="button"
                        disabled={evidenceSavingId === gap.requirement_id}
                        onclick={() => gap.atomic_options.length > 0 ? beginAtomicSelection(gap) : resolveGap(gap, 'CONFIRMED')}
                      >Tenho</button>
                      <button
                        class="btn btn-secondary"
                        type="button"
                        disabled={evidenceSavingId === gap.requirement_id}
                        onclick={() => resolveGap(gap, 'NOT_HAVE')}
                      >Não tenho</button>
                      <button
                        class="btn btn-ghost"
                        type="button"
                        disabled={evidenceSavingId === gap.requirement_id}
                        onclick={() => resolveGap(gap, 'UNSURE')}
                      >Não sei</button>
                    </div>
                  {/if}
                </article>
              {/each}
            </div>
          {/if}

          {#if evidenceGaps.profile_only_unknown_count > 0}
            <div class="status-notice resolver-profile-note">
              {evidenceGaps.profile_only_unknown_count} item(ns) exigem dados estruturados como idioma, formação, certificação, nível ou tempo de experiência.
              <a href="/">Atualizar meu perfil</a>
            </div>
          {/if}
        </section>
      {/if}

      <div class="result-columns">
        <section class="surface surface-padded">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">Evidências</p>
              <h2 class="section-title">O que sustentou esta leitura</h2>
              <p class="section-description">Cada requisito mantém seu motivo e, quando existe, a evidência profissional usada pelo Match.</p>
            </div>
          </div>

          <div class="match-evidence-list">
            {#each result.requirement_results as item}
              <article class="match-evidence">
                <div class="match-evidence-head">
                  <div>
                    <span class="status-chip" data-status={item.status}>{statusLabel[item.status]}</span>
                    <h3 class="match-evidence-title">{item.value}</h3>
                  </div>
                  <span class="requirement-meta">{item.importance} · {item.kind} · peso {item.weight}</span>
                </div>
                <p class="match-evidence-reason">{item.reason}</p>
                {#if item.evidence.length > 0}
                  <div class="proof-list">
                    {#each item.evidence as evidence}
                      <div class="evidence-proof">
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

        <aside class="surface surface-padded preferences-panel">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">Opportunity Compatibility</p>
              <h2 class="section-title">A oportunidade funciona para você?</h2>
              <p class="section-description">Localização, modalidade, contrato, salário e demais preferências são avaliados aqui sem alterar sua capacidade profissional.</p>
            </div>
          </div>
          <div class="preference-list">
            {#each result.preference_results as item}
              <article class="preference-item">
                <div class="preference-head">
                  <strong>{item.aspect}</strong>
                  <span class="status-chip" data-status={item.status}>{statusLabel[item.status]}</span>
                </div>
                <p>{item.reason}</p>
                <small>Você: {item.candidate_value.join(', ') || 'n/d'}<br />Vaga: {item.job_value.join(', ') || 'n/d'}</small>
              </article>
            {/each}
          </div>

          <div class="interpretation">
            <strong>Como ler este resultado</strong>
            <p>Professional Fit não é probabilidade de entrevista ou contratação. Opportunity Compatibility não decide sua candidatura. Apply Intent pertence a você; o HireIn organiza os sinais sem misturá-los.</p>
            {#if result.warnings.length > 0}
              <div class="warning-list">
                {#each result.warnings as warning}<span>{warning}</span>{/each}
              </div>
            {/if}
          </div>
          <a class="btn btn-accent review-cta" href="/jobs/review">Dar minha avaliação desta vaga</a>
        </aside>
      </div>
    </section>
  {/if}
</main>

<style>
  .job-picker { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .evidence-resolver { display: grid; gap: 1rem; }
  .resolver-confidence { display: grid; justify-items: end; gap: .15rem; min-width: 110px; }
  .resolver-confidence span { color: var(--text-muted); font-size: .68rem; }
  .resolver-confidence strong { color: var(--brand-700); font-family: var(--font-display); font-size: 1.45rem; }
  .evidence-gap-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; }
  .evidence-gap-card { display: grid; gap: .8rem; padding: 1rem; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--surface-subtle); }
  .evidence-gap-head { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }
  .evidence-gap-head h3 { margin: .4rem 0 0; font-size: .98rem; line-height: 1.35; }
  .impact-badge { flex: 0 0 auto; color: var(--brand-700); background: var(--brand-50); border: 1px solid var(--brand-100); border-radius: 999px; padding: .3rem .5rem; font-size: .66rem; font-weight: 700; }
  .evidence-question { margin: 0; color: var(--text-secondary); font-size: .82rem; line-height: 1.5; }
  .partial-evidence { display: flex; flex-wrap: wrap; gap: .35rem; align-items: center; color: var(--text-muted); font-size: .7rem; }
  .partial-evidence strong { padding: .25rem .4rem; border-radius: 7px; background: white; color: var(--text-secondary); font-size: .7rem; }
  .resolution-state { display: grid; gap: .25rem; padding: .7rem; border-radius: var(--radius-sm); background: var(--neutral-50); border: 1px solid var(--border); }
  .resolution-state strong { font-size: .74rem; color: var(--text-secondary); }
  .resolution-state span { color: var(--text-muted); font-size: .72rem; line-height: 1.45; }
  .resolution-state[data-decision='CONFIRMED'] { background: var(--success-soft); border-color: var(--success); }
  .resolution-state[data-decision='NOT_HAVE'] { background: var(--danger-soft); border-color: var(--danger); }
  .resolution-state[data-decision='PARTIAL'] { background: var(--warning-soft); border-color: var(--warning); }
  .confirmed-atom-list { display: flex; flex-wrap: wrap; gap: .35rem; }
  .confirmed-atom-list span { padding: .24rem .42rem; border-radius: 999px; background: white; border: 1px solid var(--border); color: var(--text-secondary); font-size: .68rem; }
  .atomic-editor { display: grid; gap: .7rem; padding: .8rem; border: 1px solid var(--brand-100); border-radius: var(--radius-sm); background: white; }
  .atomic-guidance { display: grid; gap: .2rem; }
  .atomic-guidance strong { font-size: .78rem; }
  .atomic-guidance span { color: var(--text-muted); font-size: .72rem; line-height: 1.45; }
  .atomic-options { display: flex; flex-wrap: wrap; gap: .4rem; }
  .atomic-options button { padding: .45rem .65rem; border: 1px solid var(--border); border-radius: 999px; background: var(--surface-subtle); color: var(--text-secondary); cursor: pointer; font: inherit; font-size: .74rem; }
  .atomic-options button:hover { border-color: var(--brand-200); }
  .atomic-options button.active { border-color: var(--brand-400); background: var(--brand-50); color: var(--brand-800); font-weight: 700; }
  .resolver-actions { display: flex; flex-wrap: wrap; gap: .45rem; }
  .resolver-profile-note { margin-top: .25rem; }
  .resolver-profile-note a { margin-left: .3rem; font-weight: 700; }
  .match-link { color: var(--brand-600); font-size: .78rem; font-weight: 700; }
  .opportunity-card.holdout-locked { opacity: .58; cursor: not-allowed; background: var(--surface-subtle); }
  .opportunity-card.holdout-locked .match-link { color: var(--text-muted); }
  .result-space { display: grid; gap: 1rem; margin-top: 1rem; }
  .selected-title { margin: .18rem 0 .35rem; font-size: clamp(1.6rem, 3vw, 2.3rem); }
  .selected-meta { margin: 0; color: var(--text-muted); font-size: .84rem; }
  .match-score-panel small { color: var(--brand-200); font-size: .74rem; }
  .match-score-state { display: block; max-width: 240px; font-family: var(--font-display); font-size: clamp(1.7rem, 4vw, 2.8rem); line-height: .96; letter-spacing: -.04em; }
  .dimension-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: .55rem; margin-top: 1.2rem; }
  .dimension-read { display: grid; gap: .18rem; padding: .75rem; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--surface-subtle); }
  .dimension-read > span { color: var(--text-muted); font-size: .66rem; }
  .dimension-read > strong { font-family: var(--font-display); font-size: 1.1rem; color: var(--brand-700); }
  .dimension-read > small { color: var(--text-muted); font-size: .66rem; }
  .dimension-read.blocked { border-color: var(--danger); background: var(--danger-soft); }
  .insufficient-note, .opportunity-note { margin-top: 1rem; }
  .result-columns { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(280px, .75fr); gap: 1rem; align-items: start; }
  .requirement-meta { color: var(--text-muted); font-size: .7rem; white-space: nowrap; }
  .proof-list { display: grid; gap: .55rem; }
  .preferences-panel { position: sticky; top: calc(var(--nav-height) + 1rem); }
  .preference-list { display: grid; gap: 0; }
  .preference-item { padding: .9rem 0; border-top: 1px solid var(--border); }
  .preference-item:first-child { border-top: 0; padding-top: 0; }
  .preference-head { display: flex; justify-content: space-between; gap: .8rem; align-items: center; }
  .preference-item p { margin: .45rem 0; color: var(--text-secondary); font-size: .82rem; line-height: 1.5; }
  .preference-item small { color: var(--text-muted); font-size: .72rem; }
  .interpretation { margin-top: 1.2rem; padding: 1rem 0 0; border-top: 1px solid var(--border); }
  .interpretation p { margin: .4rem 0 0; color: var(--text-muted); font-size: .8rem; line-height: 1.5; }
  .warning-list { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .65rem; }
  .warning-list span { padding: .25rem .45rem; border-radius: 7px; background: var(--warning-soft); color: #75500f; font-size: .68rem; }
  .review-cta { width: 100%; margin-top: 1rem; }
  @media (max-width: 900px) {
    .job-picker { grid-template-columns: 1fr; }
    .result-columns { grid-template-columns: 1fr; }
    .evidence-gap-list { grid-template-columns: 1fr; }
    .dimension-strip { grid-template-columns: 1fr; }
    .preferences-panel { position: static; }
  }
  @media (max-width: 640px) {
    .opportunity-card { flex-direction: column; }
    .requirement-meta { white-space: normal; }
  }
</style>
