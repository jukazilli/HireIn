<script lang="ts">
  import { onMount } from 'svelte';

  const API = 'http://localhost:8000/api/v1/profile';

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
    status: 'IN_PROGRESS' | 'COMPLETED' | 'PAUSED' | 'DROPPED';
    start_date: string;
    end_date: string;
  };

  type Language = {
    name: string;
    proficiency: 'BASIC' | 'INTERMEDIATE' | 'ADVANCED' | 'FLUENT' | 'NATIVE';
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
    seniority: '', work_models: [] as string[], contract_types: [] as string[],
    salary_min: '', salary_max: '', willing_to_travel: false, willing_to_relocate: false,
    skills: '', facts: '', experiences: [] as Experience[], education: [] as Education[],
    languages: [] as Language[], certifications: [] as Certification[]
  };

  let loading = true;
  let saving = false;
  let message = '';
  let error = '';

  const list = (value: string) => value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean);
  const optional = (value: string) => value.trim() || null;
  const toggle = (items: string[], value: string) =>
    items.includes(value) ? items.filter((item) => item !== value) : [...items, value];

  function addExperience() { form.experiences = [...form.experiences, newExperience()]; }
  function addEducation() { form.education = [...form.education, newEducation()]; }
  function addLanguage() { form.languages = [...form.languages, newLanguage()]; }
  function addCertification() { form.certifications = [...form.certifications, newCertification()]; }

  async function load() {
    try {
      const response = await fetch(API);
      if (response.status === 404) return;
      if (!response.ok) throw new Error(`Falha ao carregar (${response.status}).`);
      const data = await response.json();
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
      form.skills = data.skills.map((item: { name: string }) => item.name).join(', ');
      form.facts = data.facts.map((item: { value: string }) => item.value).join('\n');
      form.experiences = data.experiences.map((item: any) => ({
        company_name: item.company_name, role_title: item.role_title,
        start_date: item.start_date, end_date: item.end_date ?? '', is_current: item.is_current,
        description: item.description ?? '', facts: item.facts.map((fact: any) => fact.value).join('\n')
      }));
      form.education = data.education.map((item: any) => ({
        institution: item.institution, course: item.course, status: item.status,
        start_date: item.start_date ?? '', end_date: item.end_date ?? ''
      }));
      form.languages = data.languages.map((item: any) => ({ name: item.name, proficiency: item.proficiency }));
      form.certifications = data.certifications.map((item: any) => ({ name: item.name, issuer: item.issuer ?? '' }));
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível carregar o perfil.';
    } finally {
      loading = false;
    }
  }

  function payload() {
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
        company_name: item.company_name, role_title: item.role_title, start_date: item.start_date,
        end_date: item.is_current ? null : optional(item.end_date), is_current: item.is_current,
        description: optional(item.description),
        facts: list(item.facts).map((value) => ({ kind: 'RESPONSIBILITY', value }))
      })),
      education: form.education.map((item) => ({
        institution: item.institution, course: item.course, status: item.status,
        start_date: optional(item.start_date), end_date: optional(item.end_date)
      })),
      skills: list(form.skills).map((name) => ({ name })),
      facts: list(form.facts).map((value) => ({ kind: 'OTHER', value })),
      languages: form.languages.map((item) => ({ name: item.name, proficiency: item.proficiency })),
      certifications: form.certifications.map((item) => ({ name: item.name, issuer: optional(item.issuer) }))
    };
  }

  async function save(event: SubmitEvent) {
    event.preventDefault(); saving = true; message = ''; error = '';
    try {
      const response = await fetch(API, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload())
      });
      if (!response.ok) throw new Error(`Não foi possível salvar (${response.status}). ${await response.text()}`);
      message = 'Perfil salvo como informação confirmada por você.';
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível salvar.';
    } finally { saving = false; }
  }

  onMount(load);
</script>

<svelte:head><title>Meu perfil · HireIn</title></svelte:head>

<header><strong>HireIn</strong><span>Piloto individual · Auto Apply desativado</span></header>
<main>
  <div class="intro"><small>CANDIDATE CORE</small><h1>Seu perfil profissional</h1><p>Fonte de verdade do futuro Match. Nesta etapa a IA não preenche nem inventa informações.</p></div>
  {#if loading}<div class="card">Carregando…</div>{:else}
  <form onsubmit={save}>
    <section class="card"><h2>01 · Identidade profissional</h2><div class="grid">
      <label>Nome completo<input bind:value={form.full_name} required /></label>
      <label>Título profissional<input bind:value={form.headline} placeholder="Analista de Implantação ERP" /></label>
      <label>E-mail<input bind:value={form.email} type="email" /></label><label>Telefone<input bind:value={form.phone} /></label>
      <label>Cidade<input bind:value={form.city} /></label><label>Estado<input bind:value={form.state} /></label>
    </div><label>Resumo<textarea bind:value={form.professional_summary} rows="4"></textarea></label>
    <div class="grid three"><label>LinkedIn<input bind:value={form.linkedin_url} type="url" /></label><label>GitHub<input bind:value={form.github_url} type="url" /></label><label>Portfólio<input bind:value={form.portfolio_url} type="url" /></label></div></section>

    <section class="card"><h2>02 · Objetivos</h2><div class="grid">
      <label>Cargos desejados<textarea bind:value={form.desired_titles} rows="3" placeholder="Separe por vírgula"></textarea></label>
      <label>Áreas de interesse<textarea bind:value={form.desired_areas} rows="3"></textarea></label>
      <label>Localidades<textarea bind:value={form.target_locations} rows="3"></textarea></label>
      <label>Senioridade<select bind:value={form.seniority}><option value="">Não definida</option><option value="JUNIOR">Júnior</option><option value="MID">Pleno</option><option value="SENIOR">Sênior</option><option value="SPECIALIST">Especialista</option><option value="MANAGER">Gestão</option></select></label>
    </div><div class="choices">{#each [['REMOTE','Remoto'],['HYBRID','Híbrido'],['ONSITE','Presencial']] as option}<label><input type="checkbox" checked={form.work_models.includes(option[0])} onchange={() => form.work_models = toggle(form.work_models, option[0])} />{option[1]}</label>{/each}</div>
    <div class="choices">{#each ['CLT','PJ','INTERNSHIP'] as contract}<label><input type="checkbox" checked={form.contract_types.includes(contract)} onchange={() => form.contract_types = toggle(form.contract_types, contract)} />{contract === 'INTERNSHIP' ? 'Estágio' : contract}</label>{/each}</div>
    <div class="grid three"><label>Salário mínimo<input bind:value={form.salary_min} type="number" min="0" /></label><label>Salário máximo<input bind:value={form.salary_max} type="number" min="0" /></label><div class="checks"><label><input bind:checked={form.willing_to_travel} type="checkbox" />Viajar</label><label><input bind:checked={form.willing_to_relocate} type="checkbox" />Mudar de cidade</label></div></div></section>

    <section class="card"><div class="title"><h2>03 · Experiências</h2><button type="button" onclick={addExperience}>Adicionar</button></div>{#each form.experiences as item, index}<div class="item"><div class="grid"><label>Empresa<input bind:value={item.company_name} required /></label><label>Cargo<input bind:value={item.role_title} required /></label><label>Início<input bind:value={item.start_date} type="date" required /></label><label>Fim<input bind:value={item.end_date} type="date" disabled={item.is_current} /></label></div><label class="check"><input bind:checked={item.is_current} type="checkbox" />Trabalho atual</label><label>Descrição<textarea bind:value={item.description} rows="3"></textarea></label><label>Fatos / responsabilidades<textarea bind:value={item.facts} rows="4" placeholder="Uma evidência por linha"></textarea></label><button class="remove" type="button" onclick={() => form.experiences = form.experiences.filter((_, i) => i !== index)}>Remover</button></div>{/each}</section>

    <section class="card"><div class="title"><h2>04 · Formação</h2><button type="button" onclick={addEducation}>Adicionar</button></div>{#each form.education as item, index}<div class="item"><div class="grid"><label>Instituição<input bind:value={item.institution} required /></label><label>Curso<input bind:value={item.course} required /></label><label>Status<select bind:value={item.status}><option value="IN_PROGRESS">Em andamento</option><option value="COMPLETED">Concluído</option><option value="PAUSED">Pausado</option><option value="DROPPED">Interrompido</option></select></label><label>Conclusão / previsão<input bind:value={item.end_date} type="date" /></label></div><button class="remove" type="button" onclick={() => form.education = form.education.filter((_, i) => i !== index)}>Remover</button></div>{/each}</section>

    <section class="card"><h2>05 · Competências e evidências</h2><label>Skills<textarea bind:value={form.skills} rows="4" placeholder="SQL, Protheus, Gestão de Projetos…"></textarea></label><label>Outros fatos confirmados<textarea bind:value={form.facts} rows="4" placeholder="Uma informação por linha"></textarea></label></section>

    <section class="card"><div class="title"><h2>06 · Idiomas e certificações</h2><div><button type="button" onclick={addLanguage}>Idioma</button><button type="button" onclick={addCertification}>Certificação</button></div></div>{#each form.languages as item, index}<div class="row"><input bind:value={item.name} placeholder="Idioma" required /><select bind:value={item.proficiency}><option value="BASIC">Básico</option><option value="INTERMEDIATE">Intermediário</option><option value="ADVANCED">Avançado</option><option value="FLUENT">Fluente</option><option value="NATIVE">Nativo</option></select><button class="remove" type="button" onclick={() => form.languages = form.languages.filter((_, i) => i !== index)}>×</button></div>{/each}{#each form.certifications as item, index}<div class="row"><input bind:value={item.name} placeholder="Certificação" required /><input bind:value={item.issuer} placeholder="Emissor" /><button class="remove" type="button" onclick={() => form.certifications = form.certifications.filter((_, i) => i !== index)}>×</button></div>{/each}</section>

    {#if error}<div class="notice error" role="alert">{error}</div>{/if}{#if message}<div class="notice success">{message}</div>{/if}
    <footer><span>Dados desta tela: <b>USER_CONFIRMED</b></span><button class="primary" type="submit" disabled={saving || !form.full_name.trim()}>{saving ? 'Salvando…' : 'Salvar perfil'}</button></footer>
  </form>{/if}
</main>

<style>
  :global(*){box-sizing:border-box}:global(body){margin:0;background:#f7f7fa;color:#1c1c22;font-family:ui-sans-serif,system-ui,sans-serif}header{height:64px;padding:0 5vw;display:flex;align-items:center;justify-content:space-between;background:#fff;border-bottom:1px solid #e7e7ed;position:sticky;top:0;z-index:4}header span{font-size:.8rem;color:#777581}main{width:min(960px,calc(100% - 2rem));margin:auto;padding:4rem 0 7rem}.intro{max-width:720px;margin-bottom:2rem}.intro small{font-weight:800;letter-spacing:.08em;color:#777385}.intro h1{font-size:clamp(2.3rem,5vw,4rem);letter-spacing:-.05em;margin:.6rem 0}.intro p{color:#65636d;line-height:1.6}.card{background:#fff;border:1px solid #e5e5eb;border-radius:20px;padding:2rem;margin-bottom:1rem}h2{font-size:1.05rem;margin:0 0 1.4rem}.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.grid.three{grid-template-columns:repeat(3,1fr)}label{display:grid;gap:.4rem;font-size:.8rem;font-weight:650;color:#5a5862;margin-top:.9rem}input,textarea,select{font:inherit;width:100%;padding:.72rem .8rem;border:1px solid #dddde5;border-radius:10px;background:#fff;color:#222}textarea{resize:vertical}.choices,.checks{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:1rem}.choices label,.check{display:flex;align-items:center;gap:.45rem;border:1px solid #e3e3e9;border-radius:999px;padding:.5rem .7rem;margin:0}.choices input,.checks input,.check input{width:auto}.title{display:flex;align-items:center;justify-content:space-between}.title h2{margin:0}.title div{display:flex;gap:.5rem}button{font:inherit;border:1px solid #dcdce4;background:#fff;border-radius:9px;padding:.55rem .8rem;cursor:pointer}.item{border-top:1px solid #ececf1;margin-top:1.2rem;padding-top:1.2rem}.remove{color:#8c4f58;border:0;padding:.3rem 0}.row{display:grid;grid-template-columns:1.4fr 1fr auto;gap:.7rem;margin-top:.8rem}.row .remove{padding:.6rem}.notice{padding:1rem;border-radius:12px;margin:1rem 0}.error{background:#fff7f8;color:#7f454c}.success{background:#f6fbf7;color:#46604b}footer{position:sticky;bottom:1rem;background:#fff;border:1px solid #dddde5;border-radius:15px;padding:1rem;display:flex;justify-content:space-between;align-items:center;box-shadow:0 16px 50px #2222}footer span{font-size:.78rem;color:#777}.primary{background:#25242c;color:#fff;border-color:#25242c;font-weight:750}.primary:disabled{opacity:.45}@media(max-width:700px){header span{display:none}main{padding-top:2rem}.grid,.grid.three,.row{grid-template-columns:1fr}.card{padding:1.3rem}footer{flex-direction:column;align-items:stretch;gap:.7rem}.primary{width:100%}}
</style>
