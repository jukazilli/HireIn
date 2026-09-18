<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type JobMatch, type JobSummary } from '$lib/api';

  let jobs: JobSummary[] = [];
  let selectedJob: JobSummary | null = null;
  let result: JobMatch | null = null;
  let loading = true;
  let calculating = false;
  let error = '';

  const bandLabel: Record<string, string> = {
    STRONG: 'Aderência profissional forte', GOOD: 'Boa aderência profissional',
    PARTIAL: 'Aderência profissional parcial', LOW: 'Aderência profissional baixa',
    INSUFFICIENT_DATA: 'Dados insuficientes'
  };

  const statusLabel: Record<string, string> = {
    MATCHED: 'Atendido', GAP: 'Gap', UNKNOWN: 'Não avaliável', INFO: 'Informativo',
    ALIGNED: 'Alinhado', CONFLICT: 'Conflito'
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

  async function calculate(job: JobSummary) {
    selectedJob = job; result = null; error = ''; calculating = true;
    try {
      result = await api.getJobMatch(job.id);
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível calcular o Match.';
    } finally {
      calculating = false;
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
        avaliar com segurança. No v1.7, a separação do v1.6 é preservada e a recuperação de evidências profissionais ficou mais precisa.
      </p>
    </div>
    <aside class="context-note">
      <strong>Match v1.7 determinístico.</strong>
      Professional Fit mede capacidade; Opportunity Compatibility mede condições da vaga. Apply Intent continua sendo sua decisão.
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
    .dimension-strip { grid-template-columns: 1fr; }
    .preferences-panel { position: static; }
  }
  @media (max-width: 640px) {
    .opportunity-card { flex-direction: column; }
    .requirement-meta { white-space: normal; }
  }
</style>
