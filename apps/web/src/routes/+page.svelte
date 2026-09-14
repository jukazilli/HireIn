<script lang="ts">
  import { onMount } from 'svelte';
  import {
    api,
    type CandidateProfileUpsert,
    type ContractType,
    type EducationStatus,
    type LanguageProficiency,
    type Seniority,
    type WorkModel
  } from '$lib/api';

  type Experience = {
    company_name: string;
    role_title: string;
    start_date: string;
    end_date: string;
    is_current: boolean;
    description: string;
    facts: string;
  };

  type Education = {
    institution: string;
    course: string;
    status: EducationStatus;
    start_date: string;
    end_date: string;
  };

  type Language = {
    name: string;
    proficiency: LanguageProficiency;
  };

  type Certification = {
    name: string;
    issuer: string;
  };

  const newExperience = (): Experience => ({
    company_name: '', role_title: '', start_date: '', end_date: '',
    is_current: false, description: '', facts: ''
  });
  const newEducation = (): Education => ({
    institution: '', course: '', status: 'IN_PROGRESS', start_date: '', end_date: ''
  });
  const newLanguage = (): Language => ({ name: '', proficiency: 'INTERMEDIATE' });
  const newCertification = (): Certification => ({ name: '', issuer: '' });

  let form = {
    full_name: '', headline: '', email: '', phone: '', city: '', state: '',
    professional_summary: '', linkedin_url: '', github_url: '', portfolio_url: '',
    desired_titles: '', desired_areas: '', target_locations: '',
    seniority: '' as Seniority | '', work_models: [] as WorkModel[], contract_types: [] as ContractType[],
    salary_min: '', salary_max: '', willing_to_travel: false, willing_to_relocate: false,
    skills: '', facts: '', experiences: [] as Experience[], education: [] as Education[],
    languages: [] as Language[], certifications: [] as Certification[]
  };

  let loading = true;
  let saving = false;
  let message = '';
  let error = '';

  $: completionSignals = [
    Boolean(form.full_name.trim()),
    Boolean(form.headline.trim()),
    Boolean(form.city.trim() || form.state.trim()),
    Boolean(form.desired_titles.trim()),
    form.work_models.length > 0,
    form.experiences.length > 0,
    Boolean(form.skills.trim())
  ];
  $: profileCompletion = Math.round(
    (completionSignals.filter(Boolean).length / completionSignals.length) * 100
  );

  const list = (value: string) => value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean);
  const optional = (value: string) => value.trim() || null;
  const toggle = <T extends string>(items: T[], value: T) =>
    items.includes(value) ? items.filter((item) => item !== value) : [...items, value];
  const provenance = () => ({ source_type: 'USER_CONFIRMED' as const, confidence: 1 });
  const workModelOptions: { value: WorkModel; label: string }[] = [
    { value: 'REMOTE', label: 'Remoto' },
    { value: 'HYBRID', label: 'Híbrido' },
    { value: 'ONSITE', label: 'Presencial' }
  ];
  const contractOptions: { value: ContractType; label: string }[] = [
    { value: 'CLT', label: 'CLT' },
    { value: 'PJ', label: 'PJ' },
    { value: 'INTERNSHIP', label: 'Estágio' }
  ];

  function addExperience() { form.experiences = [...form.experiences, newExperience()]; }
  function addEducation() { form.education = [...form.education, newEducation()]; }
  function addLanguage() { form.languages = [...form.languages, newLanguage()]; }
  function addCertification() { form.certifications = [...form.certifications, newCertification()]; }

  async function load() {
    try {
      const data = await api.getProfile();
      if (!data) return;
      form.full_name = data.full_name;
      form.headline = data.headline ?? '';
      form.email = data.email ?? '';
      form.phone = data.phone ?? '';
      form.city = data.city ?? '';
      form.state = data.state ?? '';
      form.professional_summary = data.professional_summary ?? '';
      form.linkedin_url = data.linkedin_url ?? '';
      form.github_url = data.github_url ?? '';
      form.portfolio_url = data.portfolio_url ?? '';
      form.desired_titles = data.preferences.desired_titles.join(', ');
      form.desired_areas = data.preferences.desired_areas.join(', ');
      form.target_locations = data.preferences.target_locations.join(', ');
      form.seniority = data.preferences.seniority_levels[0] ?? '';
      form.work_models = data.preferences.work_models;
      form.contract_types = data.preferences.contract_types;
      form.salary_min = data.preferences.salary_min?.toString() ?? '';
      form.salary_max = data.preferences.salary_max?.toString() ?? '';
      form.willing_to_travel = data.preferences.willing_to_travel;
      form.willing_to_relocate = data.preferences.willing_to_relocate;
      form.skills = data.skills.map((item) => item.name).join(', ');
      form.facts = data.facts.map((item) => item.value).join('\n');
      form.experiences = data.experiences.map((item) => ({
        company_name: item.company_name, role_title: item.role_title,
        start_date: item.start_date, end_date: item.end_date ?? '', is_current: item.is_current,
        description: item.description ?? '', facts: item.facts.map((fact) => fact.value).join('\n')
      }));
      form.education = data.education.map((item) => ({
        institution: item.institution, course: item.course, status: item.status,
        start_date: item.start_date ?? '', end_date: item.end_date ?? ''
      }));
      form.languages = data.languages.map((item) => ({ name: item.name, proficiency: item.proficiency }));
      form.certifications = data.certifications.map((item) => ({ name: item.name, issuer: item.issuer ?? '' }));
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível carregar o perfil.';
    } finally {
      loading = false;
    }
  }

  function payload(): CandidateProfileUpsert {
    return {
      full_name: form.full_name,
      headline: optional(form.headline), email: optional(form.email), phone: optional(form.phone),
      city: optional(form.city), state: optional(form.state), country_code: 'BR',
      professional_summary: optional(form.professional_summary),
      linkedin_url: optional(form.linkedin_url), github_url: optional(form.github_url),
      portfolio_url: optional(form.portfolio_url),
      preferences: {
        desired_titles: list(form.desired_titles), desired_areas: list(form.desired_areas),
        target_locations: list(form.target_locations),
        seniority_levels: form.seniority ? [form.seniority] : [],
        work_models: form.work_models, contract_types: form.contract_types,
        salary_min: form.salary_min ? Number(form.salary_min) : null,
        salary_max: form.salary_max ? Number(form.salary_max) : null,
        salary_currency: 'BRL', willing_to_travel: form.willing_to_travel,
        willing_to_relocate: form.willing_to_relocate
      },
      experiences: form.experiences.map((item) => ({
        ...provenance(),
        company_name: item.company_name, role_title: item.role_title, start_date: item.start_date,
        end_date: item.is_current ? null : optional(item.end_date), is_current: item.is_current,
        description: optional(item.description),
        facts: list(item.facts).map((value) => ({ ...provenance(), kind: 'RESPONSIBILITY', value }))
      })),
      education: form.education.map((item) => ({
        ...provenance(),
        institution: item.institution, course: item.course, status: item.status,
        start_date: optional(item.start_date), end_date: optional(item.end_date)
      })),
      skills: list(form.skills).map((name) => ({ ...provenance(), name })),
      facts: list(form.facts).map((value) => ({ ...provenance(), kind: 'OTHER', value })),
      languages: form.languages.map((item) => ({ ...provenance(), name: item.name, proficiency: item.proficiency })),
      certifications: form.certifications.map((item) => ({ ...provenance(), name: item.name, issuer: optional(item.issuer) }))
    };
  }

  async function save(event: SubmitEvent) {
    event.preventDefault(); saving = true; message = ''; error = '';
    try {
      await api.upsertProfile(payload());
      message = 'Perfil salvo. Estas informações estão confirmadas por você.';
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível salvar.';
    } finally { saving = false; }
  }

  onMount(load);
</script>

<svelte:head>
  <title>Meu perfil · HireIn</title>
  <meta name="description" content="Fonte de verdade profissional do piloto HireIn." />
</svelte:head>

<main class="app-main">
  <section class="page-intro">
    <div class="page-intro-copy">
      <p class="eyebrow">Seu perfil</p>
      <h1 class="page-title">Mostre ao HireIn o que você já construiu.</h1>
      <p class="page-lead">
        Esta é a fonte de verdade da sua trajetória. O Match só usa fatos confirmados aqui para
        reconhecer experiência, competências e preferências.
      </p>
    </div>
    <aside class="context-note">
      <strong>Você continua no controle.</strong>
      Nesta etapa nada é preenchido por IA e nenhuma informação vira experiência sem sua confirmação.
    </aside>
  </section>

  {#if loading}
    <div class="status-notice">Carregando seu perfil profissional…</div>
  {:else}
    <div class="profile-layout">
      <aside class="profile-rail">
        <p class="profile-rail-name">{form.full_name || 'Seu perfil'}</p>
        <p class="profile-rail-role">{form.headline || 'Defina como você quer ser apresentado'}</p>
        <div class="completion">
          <div><span>Base do Match</span><strong>{profileCompletion}%</strong></div>
          <div class="progress-bar"><span style={`width: ${profileCompletion}%`}></span></div>
        </div>
        <nav class="profile-nav" aria-label="Seções do perfil">
          <a href="#identidade">Identidade</a>
          <a href="#objetivos">Objetivos</a>
          <a href="#experiencias">Experiências</a>
          <a href="#formacao">Formação</a>
          <a href="#competencias">Competências</a>
          <a href="#idiomas">Idiomas</a>
        </nav>
        <p class="rail-foot">Dados salvos aqui recebem origem <strong>USER_CONFIRMED</strong>.</p>
      </aside>

      <form class="work-surface" onsubmit={save}>
        <section class="work-section" id="identidade">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">01 · Identidade</p>
              <h2 class="section-title">Como você se apresenta</h2>
              <p class="section-description">Informações básicas para contextualizar sua trajetória e futuras candidaturas.</p>
            </div>
          </div>
          <div class="form-grid">
            <label class="field">Nome completo<input bind:value={form.full_name} required /></label>
            <label class="field">Título profissional<input bind:value={form.headline} placeholder="Ex.: Analista de Projetos e Implantação" /></label>
            <label class="field">E-mail<input bind:value={form.email} type="email" /></label>
            <label class="field">Telefone<input bind:value={form.phone} /></label>
            <label class="field">Cidade<input bind:value={form.city} /></label>
            <label class="field">Estado<input bind:value={form.state} maxlength="2" /></label>
          </div>
          <label class="field wide-field">Resumo profissional<textarea bind:value={form.professional_summary} rows="4" placeholder="Conte em poucas linhas o tipo de problema que você sabe resolver e em que contexto trabalhou."></textarea></label>
          <div class="form-grid three">
            <label class="field">LinkedIn<input bind:value={form.linkedin_url} type="url" placeholder="https://linkedin.com/in/..." /></label>
            <label class="field">GitHub<input bind:value={form.github_url} type="url" placeholder="https://github.com/..." /></label>
            <label class="field">Portfólio<input bind:value={form.portfolio_url} type="url" placeholder="https://..." /></label>
          </div>
        </section>

        <section class="work-section" id="objetivos">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">02 · Direção</p>
              <h2 class="section-title">O que faz sentido agora</h2>
              <p class="section-description">Preferências orientam o ranking, mas não transformam automaticamente uma vaga em inelegível.</p>
            </div>
          </div>
          <div class="form-grid">
            <label class="field">Cargos desejados<textarea bind:value={form.desired_titles} rows="3" placeholder="Analista de Projetos, Analista de Implantação"></textarea></label>
            <label class="field">Áreas de interesse<textarea bind:value={form.desired_areas} rows="3" placeholder="Projetos, Implantação, Produto"></textarea></label>
            <label class="field">Localidades<textarea bind:value={form.target_locations} rows="3" placeholder="Joinville, Santa Catarina, Remoto"></textarea></label>
            <label class="field">Senioridade<select bind:value={form.seniority}><option value="">Não definida</option><option value="JUNIOR">Júnior</option><option value="MID">Pleno</option><option value="SENIOR">Sênior</option><option value="SPECIALIST">Especialista</option><option value="MANAGER">Gestão</option></select></label>
          </div>
          <div class="preference-block">
            <span>Modelo de trabalho</span>
            <div class="choice-row">
              {#each workModelOptions as option}
                <label class="choice"><input type="checkbox" checked={form.work_models.includes(option.value)} onchange={() => form.work_models = toggle(form.work_models, option.value)} />{option.label}</label>
              {/each}
            </div>
          </div>
          <div class="preference-block">
            <span>Tipo de contratação</span>
            <div class="choice-row">
              {#each contractOptions as option}
                <label class="choice"><input type="checkbox" checked={form.contract_types.includes(option.value)} onchange={() => form.contract_types = toggle(form.contract_types, option.value)} />{option.label}</label>
              {/each}
            </div>
          </div>
          <div class="form-grid three compact-top">
            <label class="field">Salário mínimo<input bind:value={form.salary_min} type="number" min="0" /></label>
            <label class="field">Salário máximo<input bind:value={form.salary_max} type="number" min="0" /></label>
            <div class="availability">
              <label class="choice"><input bind:checked={form.willing_to_travel} type="checkbox" />Disponível para viajar</label>
              <label class="choice"><input bind:checked={form.willing_to_relocate} type="checkbox" />Considera mudança</label>
            </div>
          </div>
        </section>

        <section class="work-section" id="experiencias">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">03 · Trajetória</p>
              <h2 class="section-title">Experiências com evidência</h2>
              <p class="section-description">Responsabilidades concretas ajudam o Match mais do que uma lista genérica de palavras-chave.</p>
            </div>
            <button class="btn btn-secondary" type="button" onclick={addExperience}>Adicionar experiência</button>
          </div>
          {#if form.experiences.length === 0}
            <div class="empty-state">Adicione ao menos uma experiência para o HireIn ter contexto profissional real.</div>
          {/if}
          <div class="timeline-list">
            {#each form.experiences as item, index}
              <article class="timeline-item">
                <div class="timeline-dot" aria-hidden="true"></div>
                <div class="timeline-body">
                  <div class="form-grid">
                    <label class="field">Empresa<input bind:value={item.company_name} required /></label>
                    <label class="field">Cargo<input bind:value={item.role_title} required /></label>
                    <label class="field">Início<input bind:value={item.start_date} type="date" required /></label>
                    <label class="field">Fim<input bind:value={item.end_date} type="date" disabled={item.is_current} /></label>
                  </div>
                  <label class="choice current-job"><input bind:checked={item.is_current} type="checkbox" />É meu trabalho atual</label>
                  <label class="field">Contexto da experiência<textarea bind:value={item.description} rows="3" placeholder="Responsabilidade geral, time, produto ou contexto."></textarea></label>
                  <label class="field">Fatos que podem ser comprovados<textarea bind:value={item.facts} rows="4" placeholder="Uma evidência por linha. Ex.: conduzi implantação do módulo X; treinei usuários; levantei requisitos…"></textarea></label>
                  <button class="btn btn-danger remove-action" type="button" onclick={() => form.experiences = form.experiences.filter((_, i) => i !== index)}>Remover experiência</button>
                </div>
              </article>
            {/each}
          </div>
        </section>

        <section class="work-section" id="formacao">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">04 · Formação</p>
              <h2 class="section-title">Aprendizado formal</h2>
            </div>
            <button class="btn btn-secondary" type="button" onclick={addEducation}>Adicionar formação</button>
          </div>
          {#if form.education.length === 0}
            <div class="empty-state">Nenhuma formação registrada.</div>
          {/if}
          <div class="stacked-editors">
            {#each form.education as item, index}
              <div class="editor-row">
                <div class="form-grid">
                  <label class="field">Instituição<input bind:value={item.institution} required /></label>
                  <label class="field">Curso<input bind:value={item.course} required /></label>
                  <label class="field">Status<select bind:value={item.status}><option value="IN_PROGRESS">Em andamento</option><option value="COMPLETED">Concluído</option><option value="PAUSED">Pausado</option><option value="DROPPED">Interrompido</option></select></label>
                  <label class="field">Conclusão / previsão<input bind:value={item.end_date} type="date" /></label>
                </div>
                <button class="btn btn-danger" type="button" onclick={() => form.education = form.education.filter((_, i) => i !== index)}>Remover</button>
              </div>
            {/each}
          </div>
        </section>

        <section class="work-section" id="competencias">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">05 · Competências</p>
              <h2 class="section-title">O que você sabe usar e fazer</h2>
              <p class="section-description">Use nomes objetivos. O Match v0 ainda não tenta adivinhar sinônimos ou equivalências semânticas.</p>
            </div>
          </div>
          <div class="form-grid">
            <label class="field">Skills<textarea bind:value={form.skills} rows="5" placeholder="Protheus, levantamento de requisitos, implantação de sistemas…"></textarea></label>
            <label class="field">Outros fatos confirmados<textarea bind:value={form.facts} rows="5" placeholder="Uma informação por linha que você considera verdadeira e pode sustentar."></textarea></label>
          </div>
        </section>

        <section class="work-section" id="idiomas">
          <div class="section-head">
            <div class="section-head-copy">
              <p class="section-kicker">06 · Complementos</p>
              <h2 class="section-title">Idiomas e certificações</h2>
            </div>
            <div class="inline-actions">
              <button class="btn btn-secondary" type="button" onclick={addLanguage}>Adicionar idioma</button>
              <button class="btn btn-secondary" type="button" onclick={addCertification}>Adicionar certificação</button>
            </div>
          </div>
          <div class="stacked-editors">
            {#each form.languages as item, index}
              <div class="inline-editor">
                <label class="field"><span>Idioma</span><input bind:value={item.name} placeholder="Português" required /></label>
                <label class="field"><span>Proficiência</span><select bind:value={item.proficiency}><option value="BASIC">Básico</option><option value="INTERMEDIATE">Intermediário</option><option value="ADVANCED">Avançado</option><option value="FLUENT">Fluente</option><option value="NATIVE">Nativo</option></select></label>
                <button class="btn btn-danger" type="button" onclick={() => form.languages = form.languages.filter((_, i) => i !== index)}>Remover</button>
              </div>
            {/each}
            {#each form.certifications as item, index}
              <div class="inline-editor">
                <label class="field"><span>Certificação</span><input bind:value={item.name} placeholder="Nome da certificação" required /></label>
                <label class="field"><span>Emissor</span><input bind:value={item.issuer} placeholder="Instituição" /></label>
                <button class="btn btn-danger" type="button" onclick={() => form.certifications = form.certifications.filter((_, i) => i !== index)}>Remover</button>
              </div>
            {/each}
          </div>
        </section>

        <section class="work-section save-section">
          <div>
            {#if error}<div class="status-notice error" role="alert">{error}</div>{/if}
            {#if message}<div class="status-notice success" aria-live="polite">{message}</div>{/if}
          </div>
          <div class="save-copy">
            <div><strong>Revise antes de salvar.</strong><span>O Match passa a considerar estes dados como confirmados por você.</span></div>
            <button class="btn btn-primary save-button" type="submit" disabled={saving || !form.full_name.trim()}>{saving ? 'Salvando perfil…' : 'Salvar meu perfil'}</button>
          </div>
        </section>
      </form>
    </div>
  {/if}
</main>

<style>
  .completion { display: grid; gap: .45rem; }
  .completion > div:first-child { display: flex; justify-content: space-between; gap: 1rem; color: var(--text-muted); font-size: .76rem; }
  .completion strong { color: var(--brand-700); }
  .rail-foot { margin: 1rem 0 0; padding-top: .9rem; border-top: 1px solid var(--border); color: var(--text-muted); font-size: .72rem; line-height: 1.45; }
  .rail-foot strong { color: var(--text-secondary); font-size: .68rem; }
  .wide-field { margin-top: 1rem; }
  .preference-block { display: grid; gap: .55rem; margin-top: 1.1rem; }
  .preference-block > span { color: var(--text-secondary); font-size: .78rem; font-weight: 650; }
  .compact-top { margin-top: 1.15rem; }
  .availability { display: grid; align-content: end; gap: .5rem; }
  .current-job { margin: .15rem 0 1rem; }
  .timeline-list { position: relative; display: grid; gap: 1.3rem; }
  .timeline-list::before { content: ''; position: absolute; top: .7rem; bottom: .7rem; left: .38rem; width: 2px; background: var(--brand-100); }
  .timeline-item { position: relative; display: grid; grid-template-columns: 28px 1fr; }
  .timeline-dot { z-index: 1; width: .8rem; height: .8rem; margin-top: .6rem; border: 3px solid white; border-radius: 50%; background: var(--brand-500); box-shadow: 0 0 0 2px var(--brand-200); }
  .timeline-body { min-width: 0; padding: 1rem; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--neutral-50); }
  .timeline-body > .field + .field { margin-top: .9rem; }
  .remove-action { margin-top: .6rem; }
  .stacked-editors { display: grid; gap: .8rem; }
  .editor-row { padding: 1rem; border-left: 3px solid var(--brand-100); background: var(--neutral-50); }
  .editor-row > .btn { margin-top: .7rem; }
  .inline-editor { display: grid; grid-template-columns: 1fr 1fr auto; gap: .7rem; align-items: end; padding: .85rem; border-bottom: 1px solid var(--border); }
  .inline-editor:last-child { border-bottom: 0; }
  .save-section { background: #fdfdff; }
  .save-copy { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
  .save-copy > div { display: grid; gap: .2rem; }
  .save-copy span { color: var(--text-muted); font-size: .8rem; }
  .save-section .status-notice { margin-bottom: 1rem; }
  .save-button { min-width: 170px; }
  @media (max-width: 720px) {
    .inline-editor { grid-template-columns: 1fr; }
    .save-copy { align-items: stretch; flex-direction: column; }
    .save-button { width: 100%; }
    .timeline-item { grid-template-columns: 20px 1fr; }
    .timeline-list::before { left: .28rem; }
  }
</style>
