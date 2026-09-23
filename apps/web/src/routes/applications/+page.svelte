<script lang="ts">
  import { onMount } from 'svelte';
  import {
    api,
    type ApplicationDraft,
    type ApplicationStatus,
    type CandidateProfile,
    type JobPosting,
    type JobSummary,
    type ResumeTailoringPreview
  } from '$lib/api';
  import {
    buildTruthInventory,
    type ApplicationTruthItem
  } from '$lib/application-studio';

  let profile: CandidateProfile | null = null;
  let jobs: JobSummary[] = [];
  let reviewedJobIds = new Set<string>();
  let applicationsByJob = new Map<string, ApplicationDraft>();
  let selectedSummary: JobSummary | null = null;
  let selectedJob: JobPosting | null = null;
  let application: ApplicationDraft | null = null;
  let truthInventory: ApplicationTruthItem[] = [];
  let loading = true;
  let preparing = false;
  let actionBusy = false;
  let tailoringBusy = false;
  let resumePreview: ResumeTailoringPreview | null = null;
  let error = '';
  let copyMessage = '';
  let actionMessage = '';

  const categoryLabel: Record<ApplicationTruthItem['category'], string> = {
    EXPERIENCE: 'Experiência',
    FACT: 'Fato profissional',
    SKILL: 'Competência',
    EDUCATION: 'Formação',
    CERTIFICATION: 'Certificação',
    LANGUAGE: 'Idioma'
  };

  const statusLabel: Record<ApplicationStatus, string> = {
    DRAFT: 'Em preparação',
    READY_FOR_REVIEW: 'Pronto para revisão',
    APPROVED: 'Base aprovada'
  };

  async function load() {
    try {
      const loadedProfile = await api.getProfile();
      profile = loadedProfile;
      truthInventory = profile ? buildTruthInventory(profile) : [];

      const [jobRows, reviewRows, preparedRows] = await Promise.all([
        api.listJobs(),
        api.listReviewJobs(),
        profile ? api.listApplications() : Promise.resolve([])
      ]);
      jobs = jobRows;
      reviewedJobIds = new Set(
        reviewRows.filter((job) => job.evaluation).map((job) => job.job_id)
      );
      applicationsByJob = new Map(preparedRows.map((row) => [row.job_id, row]));
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível abrir o Application Studio.';
    } finally {
      loading = false;
    }
  }

  async function openJob(job: JobSummary) {
    if (!reviewedJobIds.has(job.id)) return;
    selectedSummary = job;
    selectedJob = null;
    application = null;
    error = '';
    copyMessage = '';
    actionMessage = '';
    resumePreview = null;
    preparing = true;

    try {
      const [loadedJob, stored] = await Promise.all([
        api.getJob(job.id),
        api.getApplicationForJob(job.id)
      ]);
      selectedJob = loadedJob;
      application = stored ?? (await api.prepareApplication(job.id));
      applicationsByJob = new Map(applicationsByJob).set(job.id, application);
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível preparar esta candidatura.';
    } finally {
      preparing = false;
    }
  }

  async function refreshDraft() {
    if (!selectedJob || application?.status !== 'DRAFT') return;
    actionBusy = true;
    actionMessage = '';
    try {
      application = await api.prepareApplication(selectedJob.id);
      applicationsByJob = new Map(applicationsByJob).set(selectedJob.id, application);
      actionMessage = 'Snapshot atualizado com o perfil e o Match atuais.';
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível atualizar o draft.';
    } finally {
      actionBusy = false;
    }
  }

  async function markReady() {
    if (!selectedJob || !application || application.status !== 'DRAFT') return;
    actionBusy = true;
    actionMessage = '';
    try {
      application = await api.markApplicationReadyForReview(application.id);
      applicationsByJob = new Map(applicationsByJob).set(selectedJob.id, application);
      actionMessage = 'A base foi congelada e está pronta para sua revisão final.';
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível avançar a revisão.';
    } finally {
      actionBusy = false;
    }
  }

  async function approve() {
    if (!selectedJob || !application || application.status !== 'READY_FOR_REVIEW') return;
    actionBusy = true;
    actionMessage = '';
    try {
      application = await api.approveApplication(application.id);
      applicationsByJob = new Map(applicationsByJob).set(selectedJob.id, application);
      actionMessage = 'Base da candidatura aprovada por você.';
      resumePreview = null;
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível aprovar a preparação.';
    } finally {
      actionBusy = false;
    }
  }

  async function loadResumePreview() {
    if (!application || application.status !== 'APPROVED') return;
    tailoringBusy = true;
    actionMessage = '';
    try {
      resumePreview = await api.getResumeTailoringPreview(application.id);
      actionMessage = 'Preview determinístico carregado. Nenhum texto foi inventado.';
    } catch (reason) {
      error =
        reason instanceof Error
          ? reason.message
          : 'Não foi possível montar o preview de currículo.';
    } finally {
      tailoringBusy = false;
    }
  }

  async function copyBrief() {
    if (!application?.brief_text) return;
    try {
      await navigator.clipboard.writeText(application.brief_text);
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
        O Studio reúne vaga, Match e fatos confirmados em um draft auditável. O snapshot só usa evidências
        confirmadas e precisa passar por revisão humana antes de ser aprovado.
      </p>
    </div>
    <aside class="context-note">
      <strong>A fronteira de verdade agora é persistida.</strong>
      O draft guarda as evidências usadas naquele momento. UNKNOWN continua UNKNOWN e AUTO SUBMIT permanece desligado.
    </aside>
  </section>

  {#if error}<div class="status-notice error" role="alert">{error}</div>{/if}

  <section class="studio-flow" aria-label="Fluxo do Application Studio">
    <span class="active">1. oportunidade</span>
    <i aria-hidden="true"></i>
    <span class:selected={Boolean(application)}>2. evidências</span>
    <i aria-hidden="true"></i>
    <span class:selected={Boolean(resumePreview)}>3. tailoring</span>
    <i aria-hidden="true"></i>
    <span class:selected={application?.status === 'READY_FOR_REVIEW' || application?.status === 'APPROVED'}>4. revisão</span>
  </section>

  <section class="surface surface-padded">
    <div class="section-head">
      <div class="section-head-copy">
        <p class="section-kicker">Escolha a candidatura</p>
        <h2 class="section-title">Comece por uma vaga que você já avaliou.</h2>
        <p class="section-description">
          O Studio respeita o gate cego do piloto. A preparação fica associada à vaga e não cria drafts duplicados.
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
          {@const stored = applicationsByJob.get(job.id)}
          <button
            class="studio-job"
            class:selected={selectedSummary?.id === job.id}
            type="button"
            disabled={preparing}
            onclick={() => openJob(job)}
          >
            <span>
              <small>{job.company_name}</small>
              <strong>{job.title}</strong>
              <em>{job.location_text ?? 'Local não informado'} · {job.work_model ?? 'modalidade n/d'}</em>
            </span>
            <b>
              {preparing && selectedSummary?.id === job.id
                ? 'Abrindo…'
                : stored
                  ? statusLabel[stored.status]
                  : 'Preparar'}
            </b>
          </button>
        {/each}
      </div>
    {/if}
  </section>

  {#if selectedJob && application}
    <section class="studio-workspace" aria-live="polite">
      <header class="workspace-head">
        <div>
          <p class="section-kicker">{selectedJob.company_name}</p>
          <h2>{selectedJob.title}</h2>
          <p>
            {selectedJob.location_text ?? 'Local não informado'} ·
            {selectedJob.work_model ?? 'modalidade n/d'} ·
            {selectedJob.contract_type ?? 'contrato n/d'}
          </p>
        </div>
        <div class="fit-read">
          <span>Professional Fit</span>
          <strong>
            {application.match_snapshot.band === 'INSUFFICIENT_DATA'
              ? 'Incerto'
              : `${application.match_snapshot.score ?? '—'}%`}
          </strong>
          <small>{application.match_snapshot.confidence}% de confiança · {statusLabel[application.status]}</small>
        </div>
      </header>

      {#if application.match_snapshot.band === 'INSUFFICIENT_DATA'}
        <div class="status-notice warning">
          Esta vaga ainda tem evidência insuficiente. O draft preserva o que já é seguro usar, mas os UNKNOWNs continuam explícitos.
        </div>
      {/if}

      <div class="workspace-section">
        <div class="workspace-copy">
          <span class="step-number">01</span>
          <div>
            <h3>Evidências congeladas neste draft</h3>
            <p>
              Este snapshot pertence à preparação salva. Refresh é permitido somente enquanto o estado ainda é DRAFT.
            </p>
          </div>
        </div>

        {#if application.evidence_snapshot.length === 0}
          <div class="empty-state compact">Nenhuma evidência confirmada foi ligada a requisitos atendidos.</div>
        {:else}
          <div class="evidence-lines">
            {#each application.evidence_snapshot as requirement}
              <article>
                <span>{requirement.requirement}</span>
                {#each requirement.evidence as evidence}
                  <strong>{evidence.value}</strong>
                  {#if evidence.detail}<small>{evidence.detail}</small>{/if}
                {/each}
              </article>
            {/each}
          </div>
        {/if}
      </div>

      <div class="workspace-section">
        <div class="workspace-copy">
          <span class="step-number">02</span>
          <div>
            <h3>Fonte de verdade profissional atual</h3>
            <p>
              Este inventário mostra o Candidate Core de hoje. O draft acima continua com seu snapshot próprio para auditoria.
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
            <h3>Briefing persistido da candidatura</h3>
            <p>
              Ele registra o que pode ser destacado, quais gaps devem ser respeitados e o que ainda não foi comprovado.
            </p>
          </div>
        </div>

        <div class="brief-panel">
          <pre>{application.brief_text}</pre>
          <div class="brief-actions">
            <button class="btn btn-primary" type="button" onclick={copyBrief}>Copiar briefing</button>
            <span aria-live="polite">{copyMessage}</span>
          </div>
        </div>
      </div>

      {#if application.status === 'APPROVED'}
        <div class="workspace-section tailoring-section">
          <div class="workspace-copy">
            <span class="step-number">04</span>
            <div>
              <h3>Currículo direcionado determinístico</h3>
              <p>
                Antes de qualquer LLM, o HireIn consegue mostrar como o currículo muda apenas com
                priorização de evidências aprovadas. Nenhuma frase é reescrita nesta etapa.
              </p>
            </div>
          </div>

          <div class="tailoring-panel">
            {#if !resumePreview}
              <div class="tailoring-empty">
                <strong>A base está aprovada.</strong>
                <p>
                  Gere o preview para comparar a ordem original com a versão direcionada e revisar o diff.
                </p>
                <button
                  class="btn btn-primary"
                  type="button"
                  disabled={tailoringBusy}
                  onclick={loadResumePreview}
                >
                  {tailoringBusy ? 'Montando preview…' : 'Ver currículo direcionado'}
                </button>
              </div>
            {:else}
              <div class="tailoring-meta">
                <div>
                  <span>Sem geração</span>
                  <strong>{resumePreview.diff.length} priorizações rastreadas</strong>
                </div>
                <div>
                  <span>Fronteira factual</span>
                  <strong>{resumePreview.allowed_evidence_ids.length} evidências aprovadas</strong>
                </div>
              </div>

              {#if resumePreview.diff.length === 0}
                <div class="status-notice">
                  O currículo já estava na mesma ordem de prioridade das evidências desta vaga.
                </div>
              {:else}
                <div class="resume-diff">
                  {#each resumePreview.diff as change}
                    <article>
                      <span>{change.entity_type}</span>
                      <strong>{change.label}</strong>
                      <small>
                        posição {change.before_index + 1} → {change.after_index + 1}
                      </small>
                    </article>
                  {/each}
                </div>
              {/if}

              <article class="resume-sheet">
                <header>
                  <div>
                    <h4>{resumePreview.targeted_resume.full_name}</h4>
                    {#if resumePreview.targeted_resume.headline}
                      <p>{resumePreview.targeted_resume.headline}</p>
                    {/if}
                  </div>
                  <span>preview estruturado</span>
                </header>

                {#if resumePreview.targeted_resume.skills.length}
                  <section>
                    <h5>Competências</h5>
                    <div class="resume-tags">
                      {#each resumePreview.targeted_resume.skills as skill}
                        <span>{skill.name}</span>
                      {/each}
                    </div>
                  </section>
                {/if}

                {#if resumePreview.targeted_resume.highlights.length}
                  <section>
                    <h5>Destaques</h5>
                    <ul>
                      {#each resumePreview.targeted_resume.highlights as claim}
                        <li>{claim.value}</li>
                      {/each}
                    </ul>
                  </section>
                {/if}

                {#if resumePreview.targeted_resume.experiences.length}
                  <section>
                    <h5>Experiência</h5>
                    <div class="resume-experiences">
                      {#each resumePreview.targeted_resume.experiences as experience}
                        <div>
                          <strong>{experience.role_title} · {experience.company_name}</strong>
                          <small>
                            {experience.start_date.slice(0, 7)} →
                            {experience.is_current
                              ? 'atual'
                              : experience.end_date?.slice(0, 7) ?? 'n/d'}
                          </small>
                          {#if experience.claims.length}
                            <ul>
                              {#each experience.claims as claim}
                                <li>{claim.value}</li>
                              {/each}
                            </ul>
                          {/if}
                        </div>
                      {/each}
                    </div>
                  </section>
                {/if}
              </article>

              <details class="guardrail-details">
                <summary>Guardrails deste preview</summary>
                <ul>
                  {#each resumePreview.guardrails as guardrail}
                    <li>{guardrail}</li>
                  {/each}
                </ul>
              </details>
            {/if}
          </div>
        </div>
      {/if}

      <footer class="studio-next">
        <div>
          <span>{statusLabel[application.status]}</span>
          {#if application.status === 'DRAFT'}
            <strong>Confira a base antes de congelá-la para revisão.</strong>
            <p>Você ainda pode atualizar o snapshot caso tenha confirmado novas evidências no perfil.</p>
          {:else if application.status === 'READY_FOR_REVIEW'}
            <strong>O snapshot está congelado. A decisão de aprovação é sua.</strong>
            <p>Aprovar não envia candidatura; apenas registra a revisão humana desta base.</p>
          {:else}
            <strong>Base aprovada para a próxima etapa de tailoring.</strong>
            <p>A aprovação ficou registrada. Nenhuma candidatura foi enviada externamente.</p>
          {/if}
          {#if actionMessage}<p class="action-message" aria-live="polite">{actionMessage}</p>{/if}
        </div>

        <div class="next-actions">
          {#if application.status === 'DRAFT'}
            <button class="btn btn-secondary" type="button" disabled={actionBusy} onclick={refreshDraft}>
              Atualizar snapshot
            </button>
            <button class="btn btn-primary" type="button" disabled={actionBusy} onclick={markReady}>
              Pronto para revisão
            </button>
          {:else if application.status === 'READY_FOR_REVIEW'}
            <button class="btn btn-primary" type="button" disabled={actionBusy} onclick={approve}>
              Aprovar base
            </button>
          {:else}
            <span class="approved-state">Revisão humana registrada</span>
          {/if}
        </div>
      </footer>
    </section>
  {/if}
</main>

<style>
  .studio-page { display: grid; gap: 1.2rem; }

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
    background: var(--neutral-50);
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
  .studio-next > div:first-child { display: grid; gap: .2rem; }
  .studio-next div > span { color: var(--lime-600); font-size: .68rem; font-weight: 760; text-transform: uppercase; letter-spacing: .08em; }
  .studio-next strong { font-family: var(--font-display); font-size: .9rem; }
  .studio-next p { max-width: 720px; margin: 0; color: var(--text-secondary); font-size: .74rem; }
  .next-actions { display: flex; flex: 0 0 auto; gap: .55rem; align-items: center; }
  .approved-state {
    padding: .6rem .75rem;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg-surface);
    color: var(--brand-700) !important;
  }
  .action-message { color: var(--brand-700) !important; font-weight: 650; }

  .tailoring-panel { min-width: 0; display: grid; gap: 1rem; }
  .tailoring-empty {
    display: grid;
    gap: .45rem;
    justify-items: start;
    padding: 1rem;
    border: 1px dashed var(--border-strong);
    border-radius: 14px;
    background: var(--neutral-50);
  }
  .tailoring-empty p { margin: 0 0 .35rem; color: var(--text-secondary); font-size: .78rem; }
  .tailoring-meta {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: .75rem;
  }
  .tailoring-meta > div {
    display: grid;
    gap: .15rem;
    padding: .8rem .9rem;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--neutral-50);
  }
  .tailoring-meta span { color: var(--text-muted); font-size: .66rem; text-transform: uppercase; letter-spacing: .06em; }
  .tailoring-meta strong { font-size: .82rem; }

  .resume-diff { display: grid; gap: .55rem; }
  .resume-diff article {
    display: grid;
    grid-template-columns: 90px minmax(0, 1fr) auto;
    gap: .75rem;
    align-items: center;
    padding: .7rem 0;
    border-bottom: 1px solid var(--border);
  }
  .resume-diff article:last-child { border-bottom: 0; }
  .resume-diff span { color: var(--lime-600); font-size: .66rem; font-weight: 760; }
  .resume-diff strong { font-size: .8rem; }
  .resume-diff small { color: var(--text-muted); font-size: .68rem; }

  .resume-sheet {
    display: grid;
    gap: 1rem;
    padding: 1.15rem;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: var(--bg-surface);
  }
  .resume-sheet header {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding-bottom: .85rem;
    border-bottom: 1px solid var(--border);
  }
  .resume-sheet h4 { margin: 0; font-family: var(--font-display); font-size: 1.15rem; }
  .resume-sheet header p { margin: .15rem 0 0; color: var(--text-secondary); font-size: .76rem; }
  .resume-sheet header > span { color: var(--text-muted); font-size: .64rem; text-transform: uppercase; letter-spacing: .06em; }
  .resume-sheet section { display: grid; gap: .45rem; }
  .resume-sheet h5 { margin: 0; color: var(--text-muted); font-size: .66rem; text-transform: uppercase; letter-spacing: .07em; }
  .resume-sheet ul { margin: 0; padding-left: 1.1rem; color: var(--text-secondary); font-size: .76rem; }
  .resume-tags { display: flex; flex-wrap: wrap; gap: .35rem; }
  .resume-tags span {
    padding: .28rem .5rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--neutral-50);
    font-size: .7rem;
  }
  .resume-experiences { display: grid; gap: .85rem; }
  .resume-experiences > div { display: grid; gap: .2rem; }
  .resume-experiences strong { font-size: .8rem; }
  .resume-experiences small { color: var(--text-muted); font-size: .68rem; }
  .guardrail-details {
    padding-top: .75rem;
    border-top: 1px solid var(--border);
    color: var(--text-secondary);
    font-size: .72rem;
  }
  .guardrail-details summary { cursor: pointer; color: var(--text-primary); font-weight: 680; }
  .guardrail-details ul { margin-bottom: 0; padding-left: 1.1rem; }

  .empty-state.compact { min-height: auto; padding: 1rem; }

  @media (max-width: 760px) {
    .studio-flow { margin-inline: -.1rem; }
    .workspace-head { grid-template-columns: 1fr; padding: 1.1rem; }
    .fit-read { justify-items: start; }
    .studio-workspace > .status-notice { margin-inline: 1.1rem; }
    .workspace-section { grid-template-columns: 1fr; gap: 1rem; padding: 1.1rem; }
    .truth-row { grid-template-columns: 88px 1fr; }
    .studio-next { align-items: stretch; flex-direction: column; padding: 1.1rem; }
    .next-actions { flex-direction: column; align-items: stretch; }
    .tailoring-meta { grid-template-columns: 1fr; }
    .resume-diff article { grid-template-columns: 1fr; gap: .1rem; }
    .resume-sheet header { flex-direction: column; }
  }
</style>
