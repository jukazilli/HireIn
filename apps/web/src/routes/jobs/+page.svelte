<script lang="ts">
  import { onMount } from 'svelte';

  const API = 'http://localhost:8000/api/v1/jobs';

  type Requirement = {
    kind: string;
    importance: string;
    value: string;
    min_years: string;
    source_text: string;
  };

  type JobSummary = {
    id: string;
    company_name: string;
    title: string;
    location_text: string | null;
    work_model: string | null;
    contract_type: string | null;
    status: string;
    source_platform: string | null;
    requirement_count: number;
  };

  const newRequirement = (): Requirement => ({
    kind: 'SKILL',
    importance: 'REQUIRED',
    value: '',
    min_years: '',
    source_text: ''
  });

  let form = {
    source_kind: 'MANUAL',
    source_platform: '',
    external_id: '',
    source_url: '',
    apply_url: '',
    company_name: '',
    title: '',
    location_text: '',
    city: '',
    state: '',
    work_model: '',
    contract_type: '',
    seniority: '',
    salary_min: '',
    salary_max: '',
    salary_period: 'MONTH',
    description_raw: '',
    requirements: [] as Requirement[]
  };

  let jobs: JobSummary[] = [];
  let loading = true;
  let saving = false;
  let message = '';
  let error = '';

  const optional = (value: string) => value.trim() || null;
  const numberOrNull = (value: string) => (value.trim() ? Number(value) : null);

  function addRequirement() {
    form.requirements = [...form.requirements, newRequirement()];
  }

  function removeRequirement(index: number) {
    form.requirements = form.requirements.filter((_, itemIndex) => itemIndex !== index);
  }

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

  function payload() {
    return {
      source_kind: form.source_kind,
      source_platform: optional(form.source_platform),
      external_id: optional(form.external_id),
      source_url: optional(form.source_url),
      apply_url: optional(form.apply_url),
      company_name: form.company_name.trim(),
      title: form.title.trim(),
      location_text: optional(form.location_text),
      city: optional(form.city),
      state: optional(form.state),
      country_code: 'BR',
      work_model: optional(form.work_model),
      contract_type: optional(form.contract_type),
      seniority: optional(form.seniority),
      description_raw: form.description_raw.trim(),
      salary_min: numberOrNull(form.salary_min),
      salary_max: numberOrNull(form.salary_max),
      salary_currency: 'BRL',
      salary_period: optional(form.salary_period),
      status: 'ACTIVE',
      requirements: form.requirements
        .filter((requirement) => requirement.value.trim())
        .map((requirement) => ({
          kind: requirement.kind,
          importance: requirement.importance,
          value: requirement.value.trim(),
          min_years: numberOrNull(requirement.min_years),
          source_text: optional(requirement.source_text)
        }))
    };
  }

  async function save() {
    message = '';
    error = '';
    saving = true;
    try {
      const response = await fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload())
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? `Falha ao salvar (${response.status}).`);
      }
      message = 'Vaga salva. Ela já pode ser analisada no Match.';
      await loadJobs();
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível salvar a vaga.';
    } finally {
      saving = false;
    }
  }

  onMount(loadJobs);
</script>

<svelte:head>
  <title>Vagas · HireIn</title>
  <meta name="description" content="Workspace de vagas reais do piloto HireIn." />
</svelte:head>

<main class="app-main">
  <section class="page-intro">
    <div class="page-intro-copy">
      <p class="eyebrow">Vagas do piloto</p>
      <h1 class="page-title">Uma oportunidade de cada vez, com contexto suficiente.</h1>
      <p class="page-lead">
        Registre uma vaga real, preserve o texto original e marque apenas os requisitos que você consegue
        sustentar na descrição. A qualidade dessa estrutura determina a qualidade do Match.
      </p>
    </div>
    <aside class="context-note">
      <strong>Sem automação escondida.</strong>
      O cadastro ainda é manual. Parsing por IA e Auto Apply continuam desligados no piloto.
    </aside>
  </section>

  {#if error}<div class="status-notice error" aria-live="polite">{error}</div>{/if}
  {#if message}<div class="status-notice success" aria-live="polite">{message}</div>{/if}

  <div class="jobs-layout">
    <section class="work-surface job-editor">
      <div class="work-section">
        <div class="section-head">
          <div class="section-head-copy">
            <p class="section-kicker">Origem</p>
            <h2 class="section-title">De onde veio esta vaga?</h2>
            <p class="section-description">Plataforma, ID e URL ajudam a reconhecer a mesma oportunidade quando ela reaparece.</p>
          </div>
        </div>
        <div class="form-grid three">
          <label class="field">Origem
            <select bind:value={form.source_kind}>
              <option value="MANUAL">Manual</option>
              <option value="ATS">ATS</option>
              <option value="JOB_BOARD">Job board</option>
              <option value="COMPANY_SITE">Site da empresa</option>
              <option value="OTHER">Outra</option>
            </select>
          </label>
          <label class="field">Plataforma<input bind:value={form.source_platform} placeholder="Ex.: Gupy" /></label>
          <label class="field">ID externo<input bind:value={form.external_id} placeholder="ID da vaga" /></label>
        </div>
        <div class="form-grid compact-top">
          <label class="field">URL da vaga<input bind:value={form.source_url} type="url" placeholder="https://..." /></label>
          <label class="field">URL para candidatura<input bind:value={form.apply_url} type="url" placeholder="https://..." /></label>
        </div>
      </div>

      <div class="work-section">
        <div class="section-head">
          <div class="section-head-copy">
            <p class="section-kicker">Oportunidade</p>
            <h2 class="section-title">O que está sendo oferecido</h2>
          </div>
        </div>
        <div class="form-grid">
          <label class="field">Empresa<input bind:value={form.company_name} required placeholder="Empresa" /></label>
          <label class="field">Cargo<input bind:value={form.title} required placeholder="Cargo anunciado" /></label>
        </div>
        <div class="form-grid three compact-top">
          <label class="field">Local exibido<input bind:value={form.location_text} placeholder="Joinville - SC" /></label>
          <label class="field">Cidade<input bind:value={form.city} /></label>
          <label class="field">Estado<input bind:value={form.state} maxlength="2" /></label>
        </div>
        <div class="form-grid three compact-top">
          <label class="field">Modalidade
            <select bind:value={form.work_model}>
              <option value="">Não definida</option><option value="REMOTE">Remoto</option>
              <option value="HYBRID">Híbrido</option><option value="ONSITE">Presencial</option>
            </select>
          </label>
          <label class="field">Contrato
            <select bind:value={form.contract_type}>
              <option value="">Não definido</option><option value="CLT">CLT</option>
              <option value="PJ">PJ</option><option value="INTERNSHIP">Estágio</option>
              <option value="TEMPORARY">Temporário</option><option value="OTHER">Outro</option>
            </select>
          </label>
          <label class="field">Senioridade
            <select bind:value={form.seniority}>
              <option value="">Não definida</option><option value="JUNIOR">Júnior</option>
              <option value="MID">Pleno</option><option value="SENIOR">Sênior</option>
              <option value="SPECIALIST">Especialista</option><option value="LEAD">Lead</option>
              <option value="MANAGER">Gestão</option>
            </select>
          </label>
        </div>
        <div class="form-grid three compact-top">
          <label class="field">Salário mínimo<input type="number" min="0" bind:value={form.salary_min} /></label>
          <label class="field">Salário máximo<input type="number" min="0" bind:value={form.salary_max} /></label>
          <label class="field">Período
            <select bind:value={form.salary_period}>
              <option value="MONTH">Mensal</option><option value="YEAR">Anual</option>
              <option value="HOUR">Hora</option><option value="DAY">Dia</option>
            </select>
          </label>
        </div>
        <label class="field description-field">Descrição original
          <textarea bind:value={form.description_raw} rows="12" required placeholder="Cole aqui o texto integral da vaga. O HireIn preserva este conteúdo para auditoria."></textarea>
        </label>
      </div>

      <div class="work-section">
        <div class="section-head">
          <div class="section-head-copy">
            <p class="section-kicker">Requisitos</p>
            <h2 class="section-title">O que a vaga realmente pede</h2>
            <p class="section-description">Estruture só o que está sustentado no texto original. Requisito obrigatório e desejável têm pesos diferentes no Match.</p>
          </div>
          <button class="btn btn-secondary" type="button" onclick={addRequirement}>Adicionar requisito</button>
        </div>

        {#if form.requirements.length === 0}
          <div class="empty-state">Nenhum requisito estruturado ainda. O texto original continua preservado e pode ser revisado depois.</div>
        {/if}

        {#each form.requirements as requirement, index}
          <div class="requirement-editor">
            <div class="requirement-number">{String(index + 1).padStart(2, '0')}</div>
            <div class="requirement-fields">
              <div class="form-grid three">
                <label class="field">Tipo
                  <select bind:value={requirement.kind}>
                    <option value="SKILL">Skill</option><option value="TOOL">Ferramenta</option>
                    <option value="DOMAIN">Domínio</option><option value="EXPERIENCE">Experiência</option>
                    <option value="EDUCATION">Formação</option><option value="LANGUAGE">Idioma</option>
                    <option value="CERTIFICATION">Certificação</option><option value="LOCATION">Localização</option>
                    <option value="WORK_MODEL">Modalidade</option><option value="CONTRACT">Contrato</option>
                    <option value="RESPONSIBILITY">Responsabilidade</option><option value="OTHER">Outro</option>
                  </select>
                </label>
                <label class="field">Importância
                  <select bind:value={requirement.importance}>
                    <option value="REQUIRED">Obrigatório</option>
                    <option value="PREFERRED">Desejável</option>
                    <option value="INFO">Informativo</option>
                  </select>
                </label>
                <label class="field">Anos mínimos<input type="number" min="0" step="0.5" bind:value={requirement.min_years} /></label>
              </div>
              <label class="field compact-top">Requisito<input bind:value={requirement.value} placeholder="Ex.: TOTVS Protheus" /></label>
              <label class="field compact-top">Trecho que sustenta o requisito<textarea bind:value={requirement.source_text} rows="2" placeholder="Cole o trecho exato da vaga que justifica esta leitura."></textarea></label>
              <button class="btn btn-danger" type="button" onclick={() => removeRequirement(index)}>Remover requisito</button>
            </div>
          </div>
        {/each}
      </div>

      <div class="work-section save-job">
        <div>
          <strong>Pronto para entrar no dataset?</strong>
          <span>A vaga ficará disponível no Match e na revisão humana assim que for salva.</span>
        </div>
        <button class="btn btn-primary" type="button" disabled={saving || !form.company_name.trim() || !form.title.trim() || !form.description_raw.trim()} onclick={save}>
          {saving ? 'Salvando vaga…' : 'Salvar esta vaga'}
        </button>
      </div>
    </section>

    <aside class="surface surface-padded sticky-panel dataset-panel">
      <div class="dataset-head">
        <div>
          <p class="section-kicker">Dataset do piloto</p>
          <h2 class="dataset-title">Vagas registradas</h2>
        </div>
        <span class="count-mark">{jobs.length}</span>
      </div>
      <p class="dataset-copy">Use vagas que você realmente consideraria. O objetivo aqui é qualidade de comparação, não volume.</p>

      {#if loading}
        <div class="status-notice">Carregando vagas…</div>
      {:else if jobs.length === 0}
        <div class="empty-state">Sua primeira vaga real inicia o smoke test.</div>
      {:else}
        <div class="opportunity-list">
          {#each jobs as job}
            <article class="opportunity-card compact-card">
              <div>
                <p class="opportunity-company">{job.company_name}</p>
                <h3 class="opportunity-title">{job.title}</h3>
                <p class="opportunity-meta">{job.location_text ?? 'Local n/d'} · {job.work_model ?? 'modalidade n/d'}</p>
                <div class="job-tags">
                  {#if job.contract_type}<span class="pill">{job.contract_type}</span>{/if}
                  <span class="pill brand">{job.requirement_count} requisitos</span>
                </div>
              </div>
              <span class="source-label">{job.source_platform ?? 'manual'}</span>
            </article>
          {/each}
        </div>
      {/if}

      {#if jobs.length > 0}
        <a class="btn btn-accent review-link" href="/jobs/match">Analisar compatibilidade</a>
      {/if}
    </aside>
  </div>
</main>

<style>
  .jobs-layout { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(280px, .72fr); gap: 1rem; align-items: start; }
  .compact-top { margin-top: 1rem; }
  .description-field { margin-top: 1rem; }
  .requirement-editor { display: grid; grid-template-columns: 40px 1fr; gap: .8rem; }
  .requirement-number { color: var(--brand-500); font-family: var(--font-display); font-size: .8rem; font-weight: 700; }
  .requirement-fields { min-width: 0; }
  .save-job { display: flex; justify-content: space-between; align-items: center; gap: 1rem; background: #fdfdff; }
  .save-job > div { display: grid; gap: .2rem; }
  .save-job span { color: var(--text-muted); font-size: .8rem; }
  .dataset-head { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }
  .dataset-title { margin: .1rem 0 0; font-size: 1.35rem; }
  .count-mark { display: grid; place-items: center; min-width: 40px; height: 40px; border-radius: 50%; background: var(--brand-50); color: var(--brand-700); font-family: var(--font-display); font-weight: 700; }
  .dataset-copy { margin: .65rem 0 1.1rem; color: var(--text-muted); font-size: .82rem; line-height: 1.5; }
  .compact-card { align-items: flex-start; padding: .85rem; }
  .source-label { color: var(--text-muted); font-size: .68rem; white-space: nowrap; }
  .job-tags { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .55rem; }
  .review-link { width: 100%; margin-top: 1rem; }
  @media (max-width: 980px) { .jobs-layout { grid-template-columns: 1fr; } }
  @media (max-width: 640px) {
    .requirement-editor { grid-template-columns: 1fr; }
    .requirement-number { padding-bottom: .2rem; border-bottom: 1px solid var(--brand-100); }
    .save-job { align-items: stretch; flex-direction: column; }
  }
</style>
