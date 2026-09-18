<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type EvidenceDecision, type EvidenceGapItem, type EvidenceGapList, type JobMatch, type JobSummary } from '$lib/api';

  let jobs: JobSummary[] = [];
  let selectedJob: JobSummary | null = null;
  let result: JobMatch | null = null;
  let loading = true;
  let calculating = false;
  let error = '';
  let evidenceGaps: EvidenceGapList | null = null;
  let evidenceError = '';
  let evidenceMessage = '';
  let evidenceSavingId = '';
  let editingGapId = '';
  let evidenceDrafts: Record<string, string> = {};

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
    NOT_HAVE: 'Você indicou que não possui',
    UNSURE: 'Ainda não confirmado'
  };

  async function loadJobs() {
    try {
      jobs = await api.listJobs();
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível carregar as vagas.';
    } finally {
      loading = false;
    }
  }

  async function loadEvidenceGaps(jobId: string) {
    try {
      evidenceGaps = await api.getEvidenceGaps(jobId);
      evidenceDrafts = Object.fromEntries(
        evidenceGaps.gaps.map((gap) => [gap.requirement_id, gap.resolution?.evidence_text ?? ''])
      );
    } catch (reason) {
      evidenceGaps = null;
      evidenceError = reason instanceof Error ? reason.message : 'Não foi possível carregar as lacunas de evidência.';
    }
  }

  async function calculate(job: JobSummary) {
    selectedJob = job;
    result = null;
    evidenceGaps = null;
    error = '';
    evidenceError = '';
    evidenceMessage = '';
    editingGapId = '';
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

  async function resolveGap(gap: EvidenceGapItem, decision: EvidenceDecision) {
    if (!selectedJob) return;

    const evidenceText = evidenceDrafts[gap.requirement_id]?.trim() ?? '';
    if (decision === 'CONFIRMED' && evidenceText.length < 12) {
      evidenceError = 'Descreva uma evidência profissional concreta antes de confirmar.';
      return;
    }

    evidenceSavingId = gap.requirement_id;
    evidenceError = '';
    evidenceMessage = '';
    try {
      await api.upsertEvidenceResolution(selectedJob.id, gap.requirement_id, {
        decision,
        evidence_text: decision === 'CONFIRMED' ? evidenceText : null
      });

      [result, evidenceGaps] = await Promise.all([
        api.getJobMatch(selectedJob.id),
        api.getEvidenceGaps(selectedJob.id)
      ]);
      evidenceDrafts = Object.fromEntries(
        evidenceGaps.gaps.map((item) => [item.requirement_id, item.resolution?.evidence_text ?? ''])
      );
      editingGapId = '';
      evidenceMessage =
        decision === 'CONFIRMED'
          ? 'Evidência confirmada. O Professional Fit foi recalculado.'
          : decision === 'NOT_HAVE'
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
        Escolha uma vaga e veja o que foi atendido, o que está faltando e o que o HireIn ainda não consegue
        avaliar com segurança. No v1.8, UNKNOWNs relevantes podem ser resolvidos por você com evidência concreta, sem alterar pesos ou esconder incerteza.
      </p>
    </div>
    <aside class="context-note">
      <strong>Match v1.8 auditável.</strong>
      Professional Fit usa evidências confirmadas; Opportunity Compatibility mede condições da vaga. O resolver humano atua somente no que continua UNKNOWN.
    </aside>
  </section>

  {#if error}<div class="status-notice error" aria-live="polite">{error}</div>{/if}

  <section class="surface surface-padded">
    <div class="section-head">
      <div class="section-head-copy">
        <p class="section-kicker">Escolha a oportunidade</p>
        <h2 class="section-title">Qual vaga você quer entender?</h2>
        <p class="section-description">O HireIn calcula uma vaga por vez para manter a leitura focada e auditável.</p>
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
          <button class="opportunity-card" class:selected={selectedJob?.id === job.id} type="button" disabled={calculating} onclick={() => calculate(job)}>
            <div>
              <p class="opportunity-company">{job.company_name}</p>
              <h3 class="opportunity-title">{job.title}</h3>
              <p class="opportunity-meta">{job.location_text ?? 'Local não informado'} · {job.work_model ?? 'modalidade n/d'} · {job.contract_type ?? 'contrato n/d'}</p>
            </div>
            <div class="opportunity-side">
              <span>{job.requirement_count} requisitos</span>
              <strong class="match-link">{calculating && selectedJob?.id === job.id ? 'Analisando…' : 'Ver compatibilidade'}</strong>
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
            <span class="match-score-value">{(result.professional_fit?.score ?? result.score) === null ? '—' : `${result.professional_fit?.score ?? result.score}%`}</span>
            <p class="match-score-label">{bandLabel[result.professional_fit?.band ?? result.band] ?? (result.professional_fit?.band ?? result.band)}</p>
          </div>
          <small>{(result.professional_fit?.score ?? result.score) === null ? 'Sem evidência suficiente para aderência' : 'Competência profissional entre evidências avaliadas'}</small>
        </div>
        <div class="match-summary-panel">
          <p class="section-kicker">{selectedJob.company_name}</p>
          <h2 class="selected-title">{selectedJob.title}</h2>
          <p class="selected-meta">{selectedJob.location_text ?? 'Local n/d'} · {selectedJob.work_model ?? 'modalidade n/d'} · {selectedJob.contract_type ?? 'contrato n/d'}</p>

          <div class="dimension-strip">
            <div class="dimension-read">
              <span>Professional Fit</span>
              <strong>{(result.professional_fit?.score ?? result.score) === null ? '—' : `${result.professional_fit?.score ?? result.score}%`}</strong>
              <small>confiança {result.professional_fit?.confidence ?? result.evaluation_coverage}%</small>
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
              A confiança está abaixo de 60%. A aderência exibida considera apenas as evidências que puderam ser avaliadas; os itens desconhecidos continuam explícitos e não viram gaps artificiais.
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
                O HireIn pergunta apenas sobre itens que o v1.7 não conseguiu comprovar nem negar. Uma confirmação positiva exige contexto profissional concreto.
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
                      {#if gap.resolution.evidence_text}<span>{gap.resolution.evidence_text}</span>{/if}
                    </div>
                  {/if}

                  {#if editingGapId === gap.requirement_id}
                    <div class="evidence-editor">
                      <label class="field">
                        Evidência profissional concreta
                        <textarea
                          bind:value={evidenceDrafts[gap.requirement_id]}
                          rows="3"
                          placeholder="Ex.: em qual projeto, atividade ou contexto você aplicou isso?"
                        ></textarea>
                      </label>
                      <div class="resolver-actions">
                        <button
                          class="btn btn-primary"
                          type="button"
                          disabled={evidenceSavingId === gap.requirement_id}
                          onclick={() => resolveGap(gap, 'CONFIRMED')}
                        >
                          {evidenceSavingId === gap.requirement_id ? 'Salvando…' : 'Confirmar evidência'}
                        </button>
                        <button class="btn btn-secondary" type="button" onclick={() => editingGapId = ''}>Cancelar</button>
                      </div>
                    </div>
                  {:else}
                    <div class="resolver-actions">
                      <button class="btn btn-primary" type="button" onclick={() => editingGapId = gap.requirement_id}>Tenho evidência</button>
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
                      >Ainda não sei</button>
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
  .evidence-editor { display: grid; gap: .65rem; }
  .resolver-actions { display: flex; flex-wrap: wrap; gap: .45rem; }
  .resolver-profile-note { margin-top: .25rem; }
  .resolver-profile-note a { margin-left: .3rem; font-weight: 700; }
  .match-link { color: var(--brand-600); font-size: .78rem; font-weight: 700; }
  .result-space { display: grid; gap: 1rem; margin-top: 1rem; }
  .selected-title { margin: .18rem 0 .35rem; font-size: clamp(1.6rem, 3vw, 2.3rem); }
  .selected-meta { margin: 0; color: var(--text-muted); font-size: .84rem; }
  .match-score-panel small { color: var(--brand-200); font-size: .74rem; }
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
