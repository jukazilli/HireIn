<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type CandidateProfile, type JobMatch, type JobPosting, type JobSummary } from '$lib/api';
  import {
    buildApplicationBrief,
    buildMatchedEvidence,
    buildTruthInventory,
    type ApplicationEvidenceItem,
    type ApplicationTruthItem
  } from '$lib/application-studio';

  let profile: CandidateProfile | null = null;
  let jobs: JobSummary[] = [];
  let reviewedJobIds = new Set<string>();
  let selectedSummary: JobSummary | null = null;
  let selectedJob: JobPosting | null = null;
  let match: JobMatch | null = null;
  let truthInventory: ApplicationTruthItem[] = [];
  let matchedEvidence: ApplicationEvidenceItem[] = [];
  let brief = '';
  let loading = true;
  let preparing = false;
  let error = '';
  let copyMessage = '';

  const categoryLabel: Record<ApplicationTruthItem['category'], string> = {
    EXPERIENCE: 'Experiência',
    FACT: 'Fato profissional',
    SKILL: 'Competência',
    EDUCATION: 'Formação',
    CERTIFICATION: 'Certificação',
    LANGUAGE: 'Idioma'
  };

  async function load() {
    try {
      const [loadedProfile, jobRows, reviewRows] = await Promise.all([
        api.getProfile(),
        api.listJobs(),
        api.listReviewJobs()
      ]);
      profile = loadedProfile;
      jobs = jobRows;
      reviewedJobIds = new Set(
        reviewRows.filter((job) => job.evaluation).map((job) => job.job_id)
      );
      truthInventory = profile ? buildTruthInventory(profile) : [];
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível abrir o Application Studio.';
    } finally {
      loading = false;
    }
  }

  async function prepare(job: JobSummary) {
    if (!reviewedJobIds.has(job.id)) return;
    selectedSummary = job;
    selectedJob = null;
    match = null;
    matchedEvidence = [];
    brief = '';
    error = '';
    copyMessage = '';
    preparing = true;

    try {
      [selectedJob, match] = await Promise.all([
        api.getJob(job.id),
        api.getJobMatch(job.id)
      ]);
      matchedEvidence = buildMatchedEvidence(match);
      brief = buildApplicationBrief(selectedJob, match);
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível preparar esta candidatura.';
    } finally {
      preparing = false;
    }
  }

  async function copyBrief() {
    if (!brief) return;
    try {
      await navigator.clipboard.writeText(brief);
      copyMessage = 'Briefing copiado.';
    } catch {
      copyMessage = 'Não foi possível copiar automaticamente.';
    }
  }

  onMount(load);
</script>

<svelte:head>
  <title>Application Studio · HireIn</title>
  <meta
    name="description"
    content="Prepare candidaturas usando somente evidências profissionais confirmadas."
  />
</svelte:head>

<main class="app-main studio-page">
  <section class="page-intro studio-intro">
    <div class="page-intro-copy">
      <p class="eyebrow">Application Studio</p>
      <h1 class="page-title">Prepare a candidatura sem inventar uma versão sua.</h1>
      <p class="page-lead">
        O Studio reúne vaga, Match e fatos confirmados em um único lugar. Nesta primeira slice ele não reescreve seu currículo:
        primeiro torna explícito o que pode — e o que não pode — sustentar uma candidatura.
      </p>
    </div>
    <aside class="context-note">
      <strong>Fase 4 começou com uma fronteira de verdade.</strong>
      Só evidências <code>USER_CONFIRMED</code> entram no briefing. Itens desconhecidos continuam desconhecidos.
      AUTO SUBMIT permanece desligado.
    </aside>
  </section>

  {#if error}<div class="status-notice error" role="alert">{error}</div>{/if}

  <section class="studio-flow" aria-label="Fluxo do Application Studio">
    <span class="active">1. oportunidade</span>
    <i aria-hidden="true"></i>
    <span class:selected={Boolean(selectedJob)}>2. evidências</span>
    <i aria-hidden="true"></i>
    <span>3. tailoring</span>
    <i aria-hidden="true"></i>
    <span>4. revisão</span>
  </section>

  <section class="surface surface-padded">
    <div class="section-head">
      <div class="section-head-copy">
        <p class="section-kicker">Escolha a candidatura</p>
        <h2 class="section-title">Comece por uma vaga que você já avaliou.</h2>
        <p class="section-description">
          O Studio respeita o mesmo gate cego do Match. Vagas sem avaliação humana continuam fora deste fluxo.
        </p>
      </div>
      <span class="section-meta">{jobs.filter((job) => reviewedJobIds.has(job.id)).length} disponíveis</span>
    </div>

    {#if loading}
      <div class="status-notice">Carregando oportunidades…</div>
    {:else if jobs.filter((job) => reviewedJobIds.has(job.id)).length === 0}
      <div class="empty-state">Nenhuma vaga avaliada está pronta para preparação.</div>
    {:else}
      <div class="studio-job-list">
        {#each jobs.filter((job) => reviewedJobIds.has(job.id)) as job}
          <button
            class="studio-job"
            class:selected={selectedSummary?.id === job.id}
            type="button"
            disabled={preparing}
            onclick={() => prepare(job)}
          >
            <span>
              <small>{job.company_name}</small>
              <strong>{job.title}</strong>
              <em>{job.location_text ?? 'Local não informado'} · {job.work_model ?? 'modalidade n/d'}</em>
            </span>
            <b>{preparing && selectedSummary?.id === job.id ? 'Preparando…' : 'Preparar'}</b>
          </button>
        {/each}
      </div>
    {/if}
  </section>

  {#if selectedJob && match}
    <section class="studio-workspace" aria-live="polite">
      <header class="workspace-head">
        <div>
          <p class="section-kicker">{selectedJob.company_name}</p>
          <h2>{selectedJob.title}</h2>
          <p>{selectedJob.location_text ?? 'Local não informado'} · {selectedJob.work_model ?? 'modalidade n/d'} · {selectedJob.contract_type ?? 'contrato n/d'}</p>
        </div>
        <div class="fit-read">
          <span>Professional Fit</span>
          <strong>
            {(match.professional_fit?.band ?? match.band) === 'INSUFFICIENT_DATA'
              ? 'Incerto'
              : `${match.professional_fit?.score ?? match.score ?? '—'}%`}
          </strong>
          <small>{match.professional_fit?.confidence ?? match.evaluation_coverage}% de confiança</small>
        </div>
      </header>

      {#if (match.professional_fit?.band ?? match.band) === 'INSUFFICIENT_DATA'}
        <div class="status-notice warning">
          Esta vaga ainda tem evidência insuficiente. O Studio mostra o que já é seguro usar, mas o próximo passo recomendado é resolver os UNKNOWNs no Match antes de qualquer tailoring.
        </div>
      {/if}

      <div class="workspace-section">
        <div class="workspace-copy">
          <span class="step-number">01</span>
          <div>
            <h3>Evidências que sustentam esta vaga</h3>
            <p>
              São apenas evidências de requisitos atendidos cuja origem está confirmada por você. Nenhuma inferência entra aqui.
            </p>
          </div>
        </div>

        {#if matchedEvidence.length === 0}
          <div class="empty-state compact">Nenhuma evidência confirmada foi ligada a requisitos atendidos.</div>
        {:else}
          <div class="evidence-lines">
            {#each matchedEvidence as item}
              <article>
                <span>{item.requirement}</span>
                <strong>{item.evidence}</strong>
                {#if item.detail}<small>{item.detail}</small>{/if}
              </article>
            {/each}
          </div>
        {/if}
      </div>

      <div class="workspace-section">
        <div class="workspace-copy">
          <span class="step-number">02</span>
          <div>
            <h3>Fonte de verdade profissional</h3>
            <p>
              Este inventário vem do Candidate Core e serve como limite do que um futuro rewriter poderá afirmar.
            </p>
          </div>
        </div>

        {#if truthInventory.length === 0}
          <div class="empty-state compact">Seu perfil ainda não possui fatos USER_CONFIRMED disponíveis.</div>
        {:else}
          <div class="truth-list">
            {#each truthInventory as item}
              <div class="truth-row">
                <span>{categoryLabel[item.category]}</span>
                <div>
                  <strong>{item.label}</strong>
                  {#if item.detail}<small>{item.detail}</small>{/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <div class="workspace-section brief-section">
        <div class="workspace-copy">
          <span class="step-number">03</span>
          <div>
            <h3>Briefing seguro da candidatura</h3>
            <p>
              Um artefato determinístico para a próxima slice de tailoring: o que destacar, quais gaps respeitar e o que continua sem comprovação.
            </p>
          </div>
        </div>

        <div class="brief-panel">
          <pre>{brief}</pre>
          <div class="brief-actions">
            <button class="btn btn-primary" type="button" onclick={copyBrief}>Copiar briefing</button>
            <span aria-live="polite">{copyMessage}</span>
          </div>
        </div>
      </div>

      <footer class="studio-next">
        <div>
          <span>Próxima slice</span>
          <strong>Currículo direcionado + diff + aprovação humana persistida</strong>
          <p>
            O rewriter só poderá reorganizar, resumir, destacar e adaptar vocabulário dentro desta fronteira de verdade.
          </p>
        </div>
        <span class="blocked-action" aria-disabled="true">Tailoring ainda bloqueado</span>
      </footer>
    </section>
  {/if}
</main>

<style>
  .studio-page { display: grid; gap: 1.2rem; }
  .studio-intro code { font-size: .72rem; }

  .studio-flow {
    display: flex;
    align-items: center;
    gap: .55rem;
    padding: .1rem .15rem;
    color: var(--text-muted);
    font-size: .7rem;
    font-weight: 680;
    text-transform: uppercase;
    letter-spacing: .06em;
    overflow-x: auto;
  }
  .studio-flow span { white-space: nowrap; }
  .studio-flow span.active,
  .studio-flow span.selected { color: var(--brand-700); }
  .studio-flow i { width: 34px; height: 1px; flex: 0 0 34px; background: var(--border); }

  .studio-job-list { display: grid; border-top: 1px solid var(--border); }
  .studio-job {
    width: 100%;
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 1rem;
    align-items: center;
    padding: 1rem .15rem;
    border: 0;
    border-bottom: 1px solid var(--border);
    background: transparent;
    color: inherit;
    text-align: left;
    cursor: pointer;
  }
  .studio-job:hover { background: var(--neutral-50); }
  .studio-job.selected { background: var(--brand-50); }
  .studio-job > span { display: grid; gap: .18rem; }
  .studio-job small { color: var(--brand-700); font-size: .72rem; font-weight: 720; }
  .studio-job strong { font-family: var(--font-display); font-size: 1rem; }
  .studio-job em { color: var(--text-muted); font-size: .76rem; font-style: normal; }
  .studio-job b { color: var(--brand-700); font-size: .76rem; }

  .studio-workspace {
    border: 1px solid var(--border);
    border-radius: 20px;
    background: var(--bg-surface);
    overflow: hidden;
  }
  .workspace-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 1.2rem;
    align-items: end;
    padding: 1.5rem;
    background: linear-gradient(180deg, var(--neutral-50), var(--bg-surface));
  }
  .workspace-head h2 {
    margin: .25rem 0 .35rem;
    font-family: var(--font-display);
    font-size: clamp(1.45rem, 3vw, 2rem);
    letter-spacing: -.035em;
  }
  .workspace-head p { margin: 0; color: var(--text-secondary); font-size: .82rem; }

  .fit-read { display: grid; justify-items: end; }
  .fit-read span, .fit-read small { color: var(--text-muted); font-size: .68rem; }
  .fit-read strong { font-family: var(--font-display); color: var(--brand-700); font-size: 1.35rem; }

  .studio-workspace > .status-notice { margin: 0 1.5rem 1rem; }

  .workspace-section {
    display: grid;
    grid-template-columns: minmax(220px, .72fr) minmax(0, 1.4fr);
    gap: 2rem;
    padding: 1.5rem;
    border-top: 1px solid var(--border);
  }
  .workspace-copy { display: flex; gap: .85rem; align-items: flex-start; }
  .step-number {
    flex: 0 0 auto;
    color: var(--lime-600);
    font-family: var(--font-display);
    font-size: .72rem;
    font-weight: 760;
    letter-spacing: .08em;
  }
  .workspace-copy h3 { margin: 0 0 .35rem; font-family: var(--font-display); font-size: 1.04rem; }
  .workspace-copy p { margin: 0; color: var(--text-secondary); font-size: .78rem; line-height: 1.55; }

  .evidence-lines { display: grid; gap: .7rem; }
  .evidence-lines article {
    display: grid;
    gap: .22rem;
    padding-bottom: .7rem;
    border-bottom: 1px solid var(--border);
  }
  .evidence-lines article:last-child { border-bottom: 0; }
  .evidence-lines span { color: var(--text-muted); font-size: .7rem; }
  .evidence-lines strong { font-size: .88rem; }
  .evidence-lines small { color: var(--text-secondary); font-size: .72rem; }

  .truth-list { display: grid; }
  .truth-row {
    display: grid;
    grid-template-columns: 110px 1fr;
    gap: .85rem;
    padding: .62rem 0;
    border-bottom: 1px solid var(--border);
  }
  .truth-row:last-child { border-bottom: 0; }
  .truth-row > span { color: var(--text-muted); font-size: .68rem; font-weight: 680; }
  .truth-row div { display: grid; gap: .12rem; }
  .truth-row strong { font-size: .82rem; }
  .truth-row small { color: var(--text-secondary); font-size: .7rem; }

  .brief-panel { min-width: 0; }
  .brief-panel pre {
    max-height: 430px;
    margin: 0;
    padding: 1rem;
    overflow: auto;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: var(--neutral-50);
    color: var(--text-secondary);
    white-space: pre-wrap;
    font-family: var(--font-body);
    font-size: .76rem;
    line-height: 1.6;
  }
  .brief-actions { display: flex; align-items: center; gap: .8rem; margin-top: .75rem; }
  .brief-actions span { color: var(--text-muted); font-size: .72rem; }

  .studio-next {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: center;
    padding: 1.25rem 1.5rem;
    border-top: 1px solid var(--border);
    background: var(--neutral-50);
  }
  .studio-next div { display: grid; gap: .2rem; }
  .studio-next div > span { color: var(--lime-600); font-size: .68rem; font-weight: 760; text-transform: uppercase; letter-spacing: .08em; }
  .studio-next strong { font-family: var(--font-display); font-size: .9rem; }
  .studio-next p { max-width: 720px; margin: 0; color: var(--text-secondary); font-size: .74rem; }
  .blocked-action {
    flex: 0 0 auto;
    padding: .6rem .75rem;
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text-muted);
    background: var(--bg-surface);
    font-size: .72rem;
    font-weight: 680;
  }

  .empty-state.compact { min-height: auto; padding: 1rem; }

  @media (max-width: 760px) {
    .studio-flow { margin-inline: -.1rem; }
    .workspace-head { grid-template-columns: 1fr; padding: 1.1rem; }
    .fit-read { justify-items: start; }
    .studio-workspace > .status-notice { margin-inline: 1.1rem; }
    .workspace-section { grid-template-columns: 1fr; gap: 1rem; padding: 1.1rem; }
    .truth-row { grid-template-columns: 88px 1fr; }
    .studio-next { align-items: stretch; flex-direction: column; padding: 1.1rem; }
    .blocked-action { text-align: center; }
  }
</style>
