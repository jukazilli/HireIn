from __future__ import annotations

import re
from pathlib import Path

SCRIPTS: dict[str, str] = {
    "apps/web/src/routes/+page.svelte": r'''<script lang="ts">
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
</script>''',
    "apps/web/src/routes/jobs/+page.svelte": r'''<script lang="ts">
  import { onMount } from 'svelte';
  import {
    api,
    type ContractType,
    type JobPostingUpsert,
    type JobSourceKind,
    type JobSummary,
    type RequirementImportance,
    type RequirementKind,
    type SalaryPeriod,
    type Seniority,
    type WorkModel
  } from '$lib/api';

  type Requirement = {
    kind: RequirementKind;
    importance: RequirementImportance;
    value: string;
    min_years: string;
    source_text: string;
  };

  const newRequirement = (): Requirement => ({
    kind: 'SKILL', importance: 'REQUIRED', value: '', min_years: '', source_text: ''
  });

  let form = {
    source_kind: 'MANUAL' as JobSourceKind,
    source_platform: '', external_id: '', source_url: '', apply_url: '',
    company_name: '', title: '', location_text: '', city: '', state: '',
    work_model: '' as WorkModel | '', contract_type: '' as ContractType | '',
    seniority: '' as Seniority | '', salary_min: '', salary_max: '',
    salary_period: 'MONTH' as SalaryPeriod, description_raw: '', requirements: [] as Requirement[]
  };

  let jobs: JobSummary[] = [];
  let loading = true;
  let saving = false;
  let message = '';
  let error = '';

  const optional = (value: string) => value.trim() || null;
  const numberOrNull = (value: string) => (value.trim() ? Number(value) : null);

  function addRequirement() { form.requirements = [...form.requirements, newRequirement()]; }
  function removeRequirement(index: number) {
    form.requirements = form.requirements.filter((_, itemIndex) => itemIndex !== index);
  }

  async function loadJobs() {
    try {
      jobs = await api.listJobs();
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível carregar as vagas.';
    } finally {
      loading = false;
    }
  }

  function payload(): JobPostingUpsert {
    return {
      source_kind: form.source_kind,
      source_platform: optional(form.source_platform), external_id: optional(form.external_id),
      source_url: optional(form.source_url), apply_url: optional(form.apply_url),
      company_name: form.company_name.trim(), title: form.title.trim(),
      location_text: optional(form.location_text), city: optional(form.city), state: optional(form.state),
      country_code: 'BR', work_model: form.work_model || null, contract_type: form.contract_type || null,
      seniority: form.seniority || null, description_raw: form.description_raw.trim(),
      salary_min: numberOrNull(form.salary_min), salary_max: numberOrNull(form.salary_max),
      salary_currency: 'BRL', salary_period: form.salary_period, status: 'ACTIVE',
      requirements: form.requirements
        .filter((requirement) => requirement.value.trim())
        .map((requirement) => ({
          kind: requirement.kind, importance: requirement.importance,
          value: requirement.value.trim(), min_years: numberOrNull(requirement.min_years),
          source_text: optional(requirement.source_text)
        }))
    };
  }

  async function save() {
    message = ''; error = ''; saving = true;
    try {
      await api.createJob(payload());
      message = 'Vaga salva. Ela já pode ser analisada no Match.';
      await loadJobs();
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível salvar a vaga.';
    } finally {
      saving = false;
    }
  }

  onMount(loadJobs);
</script>''',
    "apps/web/src/routes/jobs/match/+page.svelte": r'''<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type JobMatch, type JobSummary } from '$lib/api';

  let jobs: JobSummary[] = [];
  let selectedJob: JobSummary | null = null;
  let result: JobMatch | null = null;
  let loading = true;
  let calculating = false;
  let error = '';

  const bandLabel: Record<string, string> = {
    STRONG: 'Compatibilidade forte', GOOD: 'Boa compatibilidade',
    PARTIAL: 'Compatibilidade parcial', LOW: 'Compatibilidade baixa',
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
</script>''',
    "apps/web/src/routes/jobs/review/+page.svelte": r'''<script lang="ts">
  import { onMount } from 'svelte';
  import {
    api,
    type EvaluationErrorCategory,
    type JobMatch,
    type PilotEvalReport,
    type PilotEvaluationUpsert,
    type PilotReviewJob
  } from '$lib/api';

  const ratingLabels = ['Irrelevante', 'Fraca', 'Razoável', 'Boa', 'Excelente'];
  const ratingShort = ['Não', 'Pouco', 'Talvez', 'Sim', 'Muito'];
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
  let report: PilotEvalReport | null = null;
  let loading = true;
  let loadingMatch = false;
  let saving = false;
  let error = '';
  let message = '';

  let relevance: number | null = null;
  let blockerReal = false;
  let reason = '';
  let errorCategory: EvaluationErrorCategory | '' = '';

  $: reviewedCount = jobs.filter((job) => job.evaluation).length;

  function fillEvaluation(job: PilotReviewJob) {
    relevance = job.evaluation?.relevance ?? null;
    blockerReal = job.evaluation?.blocker_real ?? false;
    reason = job.evaluation?.reason ?? '';
    errorCategory = job.evaluation?.error_category ?? '';
  }

  async function loadJobs() { jobs = await api.listReviewJobs(); }
  async function loadReport() { report = await api.getEvalReport(); }

  async function refresh() {
    error = '';
    try {
      await loadJobs();
      if (jobs.some((job) => job.evaluation)) await loadReport();
      else report = null;
    } catch (reasonValue) {
      error = reasonValue instanceof Error ? reasonValue.message : 'Não foi possível carregar o piloto.';
    } finally {
      loading = false;
    }
  }

  async function selectJob(job: PilotReviewJob) {
    selectedJob = job; fillEvaluation(job); match = null; error = ''; message = ''; loadingMatch = true;
    try {
      match = await api.getJobMatch(job.job_id);
    } catch (reasonValue) {
      error = reasonValue instanceof Error ? reasonValue.message : 'Não foi possível calcular o Match.';
    } finally {
      loadingMatch = false;
    }
  }

  async function saveEvaluation() {
    if (!selectedJob || relevance === null) return;
    saving = true; error = ''; message = '';
    try {
      const payload: PilotEvaluationUpsert = {
        relevance,
        blocker_real: blockerReal,
        reason: reason.trim() || null,
        error_category: errorCategory || null
      };
      const saved = await api.upsertEvaluation(selectedJob.job_id, payload);
      jobs = jobs.map((job) =>
        job.job_id === selectedJob?.job_id ? { ...job, evaluation: saved } : job
      );
      selectedJob = jobs.find((job) => job.job_id === selectedJob?.job_id) ?? selectedJob;
      message = 'Sua avaliação foi salva sem alterar o algoritmo.';
      await loadReport();
    } catch (reasonValue) {
      error = reasonValue instanceof Error ? reasonValue.message : 'Não foi possível salvar a avaliação.';
    } finally {
      saving = false;
    }
  }

  const percent = (value: number) => `${Math.round(value * 100)}%`;
  const coverage = (value: number) => `${Math.round(value)}%`;

  onMount(refresh);
</script>''',
    "apps/web/src/routes/pilot/+page.svelte": r'''<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type PilotEvalReport, type PilotReviewJob } from '$lib/api';

  let profileReady = false;
  let jobs: PilotReviewJob[] = [];
  let report: PilotEvalReport | null = null;
  let loading = true;
  let error = '';

  const errorLabels: Record<string, string> = {
    MISSING_PROFILE_EVIDENCE: 'Falta de evidência no perfil',
    BAD_JOB_NORMALIZATION: 'Normalização da vaga', SIMPLE_ALIAS: 'Alias simples',
    SEMANTIC_EQUIVALENCE: 'Equivalência semântica', PREFERENCE_RULE: 'Regra de preferência',
    SALARY_RULE: 'Regra salarial', SENIORITY_RULE: 'Regra de senioridade',
    COVERAGE_FAILURE: 'Cobertura insuficiente', RANKING_WEIGHT: 'Peso / ranking', OTHER: 'Outro'
  };

  $: reviewedCount = jobs.filter((job) => job.evaluation !== null).length;
  $: smokeProgress = Math.min(reviewedCount / 5, 1);
  $: baselineProgress = Math.min(reviewedCount / 30, 1);
  $: extendedProgress = Math.min(reviewedCount / 50, 1);
  $: goodCount = jobs.filter((job) => (job.evaluation?.relevance ?? -1) >= 3).length;
  $: blockerCount = jobs.filter((job) => job.evaluation?.blocker_real).length;
  $: uncategorizedCount = jobs.filter(
    (job) => job.evaluation && job.evaluation.error_category === null
  ).length;
  $: errorDistribution = buildErrorDistribution(jobs);
  $: topErrors = errorDistribution.slice(0, 5);
  $: nextStep = deriveNextStep();

  function buildErrorDistribution(items: PilotReviewJob[]) {
    const counts = new Map<string, number>();
    for (const item of items) {
      const category = item.evaluation?.error_category;
      if (!category) continue;
      counts.set(category, (counts.get(category) ?? 0) + 1);
    }
    return [...counts.entries()]
      .map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count || a.category.localeCompare(b.category));
  }

  function deriveNextStep() {
    if (!profileReady) return {
      title: 'Complete seu perfil profissional',
      description: 'O Match precisa de uma fonte de verdade antes de comparar você com uma vaga.',
      href: '/', action: 'Completar perfil'
    };
    if (jobs.length < 5) return {
      title: 'Cadastre as primeiras 5 vagas reais',
      description: `Há ${jobs.length}/5 vagas no smoke test. Priorize oportunidades que você realmente consideraria.`,
      href: '/jobs', action: 'Adicionar vagas'
    };
    if (reviewedCount < 5) return {
      title: 'Conclua o smoke test de revisão',
      description: `${reviewedCount}/5 vagas já receberam sua avaliação humana.`,
      href: '/jobs/review', action: 'Revisar vagas'
    };
    if (reviewedCount < 30) return {
      title: 'Expanda a baseline para 30 vagas',
      description: `Smoke test concluído. Faltam ${30 - reviewedCount} avaliações para o primeiro dataset útil.`,
      href: '/jobs/review', action: 'Continuar piloto'
    };
    if (reviewedCount < 50) return {
      title: 'Aumente a confiança da baseline',
      description: `A meta mínima foi atingida. Mais ${50 - reviewedCount} avaliações levam o piloto ao alvo estendido.`,
      href: '/jobs/review', action: 'Continuar até 50'
    };
    return {
      title: 'Dataset pronto para decisão técnica',
      description: 'Já existe evidência suficiente para decidir se o próximo ganho vem de regras, aliases, embeddings ou LLM.',
      href: '/jobs/review', action: 'Revisar diagnóstico'
    };
  }

  function metricPercent(value: number) { return `${Math.round(value * 100)}%`; }

  async function load() {
    loading = true; error = '';
    try {
      const [profile, reviewJobs] = await Promise.all([api.getProfile(), api.listReviewJobs()]);
      profileReady = profile !== null;
      jobs = reviewJobs;
      const reviewed = jobs.filter((job) => job.evaluation !== null).length;
      report = profileReady && reviewed > 0 ? await api.getEvalReport() : null;
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível carregar o piloto.';
    } finally {
      loading = false;
    }
  }

  onMount(load);
</script>'''
}

PATTERN = re.compile(r'<script lang="ts">.*?</script>', re.DOTALL)

for filename, replacement in SCRIPTS.items():
    path = Path(filename)
    current = path.read_text(encoding="utf-8")
    updated, count = PATTERN.subn(replacement, current, count=1)
    if count != 1:
        raise RuntimeError(f"expected one script block in {filename}, got {count}")
    path.write_text(updated, encoding="utf-8")
    print(f"updated {filename}")
