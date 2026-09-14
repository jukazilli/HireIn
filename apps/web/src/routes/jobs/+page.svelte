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
      message = 'Vaga estruturada salva.';
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
  <meta name="description" content="Job Core manual do piloto HireIn." />
</svelte:head>

<main>
  <header>
    <div>
      <a class="back" href="/">← Perfil</a>
      <p class="eyebrow">HireIn · Job Core v0</p>
      <h1>Transforme uma vaga em dados confiáveis.</h1>
      <p class="lead">
        Cole a vaga manualmente, preserve o texto original e descreva os requisitos que depois
        alimentarão o HireIn Match.
      </p>
    </div>
    <div class="guardrail">
      <span>Parsing por IA</span><strong>desligado</strong>
      <span>Auto Apply</span><strong>desligado</strong>
    </div>
  </header>

  <section class="card form-card">
    <div class="section-title">
      <div><p class="eyebrow">Fonte</p><h2>Identidade da vaga</h2></div>
      <p>IDs e URLs serão usados para evitar duplicidade.</p>
    </div>

    <div class="grid three">
      <label>Origem
        <select bind:value={form.source_kind}>
          <option value="MANUAL">Manual</option>
          <option value="ATS">ATS</option>
          <option value="JOB_BOARD">Job board</option>
          <option value="COMPANY_SITE">Site da empresa</option>
          <option value="OTHER">Outra</option>
        </select>
      </label>
      <label>Plataforma<input bind:value={form.source_platform} placeholder="Ex.: Gupy" /></label>
      <label>ID externo<input bind:value={form.external_id} placeholder="ID da vaga" /></label>
    </div>

    <div class="grid two">
      <label>URL da vaga<input bind:value={form.source_url} placeholder="https://..." /></label>
      <label>URL para candidatura<input bind:value={form.apply_url} placeholder="https://..." /></label>
    </div>

    <div class="divider"></div>
    <div class="grid two">
      <label>Empresa<input bind:value={form.company_name} required placeholder="Empresa" /></label>
      <label>Cargo<input bind:value={form.title} required placeholder="Cargo anunciado" /></label>
    </div>
    <div class="grid three">
      <label>Local exibido<input bind:value={form.location_text} placeholder="Joinville - SC" /></label>
      <label>Cidade<input bind:value={form.city} /></label>
      <label>Estado<input bind:value={form.state} maxlength="2" /></label>
    </div>
    <div class="grid three">
      <label>Modalidade
        <select bind:value={form.work_model}>
          <option value="">Não definida</option><option value="REMOTE">Remoto</option>
          <option value="HYBRID">Híbrido</option><option value="ONSITE">Presencial</option>
        </select>
      </label>
      <label>Contrato
        <select bind:value={form.contract_type}>
          <option value="">Não definido</option><option value="CLT">CLT</option>
          <option value="PJ">PJ</option><option value="INTERNSHIP">Estágio</option>
          <option value="TEMPORARY">Temporário</option><option value="OTHER">Outro</option>
        </select>
      </label>
      <label>Senioridade
        <select bind:value={form.seniority}>
          <option value="">Não definida</option><option value="JUNIOR">Júnior</option>
          <option value="MID">Pleno</option><option value="SENIOR">Sênior</option>
          <option value="SPECIALIST">Especialista</option><option value="LEAD">Lead</option>
          <option value="MANAGER">Gestão</option>
        </select>
      </label>
    </div>
    <div class="grid three">
      <label>Salário mínimo<input type="number" min="0" bind:value={form.salary_min} /></label>
      <label>Salário máximo<input type="number" min="0" bind:value={form.salary_max} /></label>
      <label>Período
        <select bind:value={form.salary_period}>
          <option value="MONTH">Mensal</option><option value="YEAR">Anual</option>
          <option value="HOUR">Hora</option><option value="DAY">Dia</option>
        </select>
      </label>
    </div>

    <label>Descrição original
      <textarea bind:value={form.description_raw} rows="10" required placeholder="Cole aqui o texto integral da vaga..."></textarea>
    </label>
  </section>

  <section class="card">
    <div class="section-title">
      <div><p class="eyebrow">Estrutura</p><h2>Requisitos</h2></div>
      <button class="secondary" type="button" onclick={addRequirement}>+ requisito</button>
    </div>

    {#if form.requirements.length === 0}
      <p class="empty">Nenhum requisito estruturado ainda. O texto original continua preservado.</p>
    {/if}

    {#each form.requirements as requirement, index}
      <div class="requirement">
        <div class="grid three">
          <label>Tipo
            <select bind:value={requirement.kind}>
              <option value="SKILL">Skill</option><option value="TOOL">Ferramenta</option>
              <option value="DOMAIN">Domínio</option><option value="EXPERIENCE">Experiência</option>
              <option value="EDUCATION">Formação</option><option value="LANGUAGE">Idioma</option>
              <option value="CERTIFICATION">Certificação</option><option value="LOCATION">Localização</option>
              <option value="WORK_MODEL">Modalidade</option><option value="CONTRACT">Contrato</option>
              <option value="RESPONSIBILITY">Responsabilidade</option><option value="OTHER">Outro</option>
            </select>
          </label>
          <label>Importância
            <select bind:value={requirement.importance}>
              <option value="REQUIRED">Obrigatório</option>
              <option value="PREFERRED">Desejável</option>
              <option value="INFO">Informativo</option>
            </select>
          </label>
          <label>Anos mínimos<input type="number" min="0" step="0.5" bind:value={requirement.min_years} /></label>
        </div>
        <label>Requisito<input bind:value={requirement.value} placeholder="Ex.: TOTVS Protheus" /></label>
        <label>Trecho de origem<textarea bind:value={requirement.source_text} rows="2" placeholder="Trecho exato da vaga que sustenta este requisito"></textarea></label>
        <button class="danger" type="button" onclick={() => removeRequirement(index)}>Remover</button>
      </div>
    {/each}

    <div class="actions">
      <div aria-live="polite">
        {#if message}<p class="success">{message}</p>{/if}
        {#if error}<p class="error">{error}</p>{/if}
      </div>
      <button class="primary" type="button" disabled={saving} onclick={save}>
        {saving ? 'Salvando…' : 'Salvar vaga estruturada'}
      </button>
    </div>
  </section>

  <section class="card">
    <div class="section-title">
      <div><p class="eyebrow">Dataset do piloto</p><h2>Vagas registradas</h2></div>
      <span>{jobs.length} vaga{jobs.length === 1 ? '' : 's'}</span>
    </div>
    {#if loading}
      <p class="empty">Carregando…</p>
    {:else if jobs.length === 0}
      <p class="empty">Nenhuma vaga registrada. Comece com uma oportunidade real que você avaliaria.</p>
    {:else}
      <div class="job-list">
        {#each jobs as job}
          <article>
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
              <small>{job.source_platform ?? 'manual'}</small>
            </div>
          </article>
        {/each}
      </div>
    {/if}
  </section>
</main>

<style>
  :global(*) { box-sizing: border-box; }
  :global(body) { margin: 0; min-width: 320px; background: #f7f7fa; color: #18181f; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  main { width: min(1120px, calc(100% - 2rem)); margin: 0 auto; padding: 3rem 0 5rem; }
  header { display: flex; justify-content: space-between; gap: 2rem; align-items: flex-end; margin-bottom: 2rem; }
  h1 { max-width: 760px; margin: .35rem 0 .8rem; font-size: clamp(2.25rem, 5vw, 4.2rem); line-height: 1; letter-spacing: -.055em; }
  h2, h3, p { margin-top: 0; }
  .lead { max-width: 720px; color: #5e5c69; line-height: 1.6; }
  .eyebrow { margin: 0; color: #6a6877; font-size: .76rem; font-weight: 750; letter-spacing: .09em; text-transform: uppercase; }
  .back { display: inline-block; margin-bottom: 1.5rem; color: #555361; text-decoration: none; }
  .guardrail { min-width: 210px; display: grid; grid-template-columns: 1fr auto; gap: .65rem 1rem; padding: 1rem 1.1rem; border: 1px solid #e4e3e9; border-radius: 16px; background: white; font-size: .84rem; }
  .guardrail strong { font-weight: 750; }
  .card { margin-top: 1rem; padding: clamp(1.3rem, 3vw, 2rem); border: 1px solid #e6e5eb; border-radius: 22px; background: white; }
  .section-title { display: flex; justify-content: space-between; gap: 1rem; align-items: center; margin-bottom: 1.4rem; }
  .section-title h2 { margin: .25rem 0 0; }
  .section-title > p, .section-title > span { color: #6a6874; font-size: .9rem; }
  .grid { display: grid; gap: 1rem; margin-bottom: 1rem; }
  .grid.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .grid.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  label { display: grid; gap: .45rem; color: #45434e; font-size: .85rem; font-weight: 650; }
  input, select, textarea { width: 100%; border: 1px solid #dcdbe2; border-radius: 11px; padding: .78rem .85rem; background: white; color: inherit; font: inherit; font-weight: 450; outline: none; }
  input:focus, select:focus, textarea:focus { border-color: #888694; box-shadow: 0 0 0 3px rgb(80 78 95 / 8%); }
  textarea { resize: vertical; line-height: 1.55; }
  .divider { height: 1px; background: #efeff3; margin: 1.5rem 0; }
  .requirement { padding: 1.2rem; margin-bottom: 1rem; border: 1px solid #ebeaf0; border-radius: 16px; background: #fbfbfd; }
  .requirement > label { margin-top: .8rem; }
  button { border: 0; border-radius: 11px; padding: .75rem 1rem; font: inherit; font-weight: 700; cursor: pointer; }
  button:disabled { opacity: .55; cursor: default; }
  .primary { background: #24232a; color: white; }
  .secondary { background: #efeff3; color: #34323b; }
  .danger { margin-top: .8rem; padding: .55rem .75rem; background: transparent; color: #8a4444; }
  .actions { display: flex; justify-content: space-between; align-items: center; gap: 1rem; border-top: 1px solid #eeeef2; margin-top: 1.5rem; padding-top: 1.3rem; }
  .success { margin: 0; color: #32704b; }
  .error { margin: 0; color: #9a4040; }
  .empty { padding: 1.3rem; border-radius: 14px; background: #f8f8fa; color: #716f7a; }
  .job-list { display: grid; gap: .7rem; }
  article { display: flex; justify-content: space-between; gap: 1.2rem; padding: 1rem 0; border-top: 1px solid #eeeeF2; }
  article:first-child { border-top: 0; }
  article h3 { margin: .2rem 0 .35rem; }
  .company, .meta, .job-side { color: #6b6975; font-size: .86rem; }
  .company { margin-bottom: 0; font-weight: 700; }
  .meta { margin-bottom: 0; }
  .job-side { display: grid; text-align: right; align-content: center; gap: .25rem; white-space: nowrap; }
  @media (max-width: 760px) { header { display: block; } .guardrail { margin-top: 1.5rem; } .grid.two, .grid.three { grid-template-columns: 1fr; } .section-title, .actions, article { align-items: stretch; } .actions { flex-direction: column; } .primary { width: 100%; } }
</style>
