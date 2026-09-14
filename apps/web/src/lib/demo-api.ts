import { browser } from '$app/environment';

const LOCAL_API_PREFIX = 'http://localhost:8000/api/v1';
const STORAGE_KEY = 'hirein.visual-preview.v1';

type Evaluation = {
  job_id: string;
  relevance: number;
  blocker_real: boolean;
  reason: string | null;
  error_category: string | null;
};

type DemoJob = {
  id: string;
  company_name: string;
  title: string;
  location_text: string | null;
  city: string | null;
  state: string | null;
  work_model: string | null;
  contract_type: string | null;
  seniority: string | null;
  status: string;
  source_platform: string | null;
  requirement_count: number;
};

type DemoState = {
  profile: Record<string, unknown>;
  jobs: DemoJob[];
  evaluations: Record<string, Evaluation>;
};

const defaultProfile = {
  id: 'demo-profile-001',
  full_name: 'Ana Martins',
  headline: 'Analista de Projetos & Implantação',
  email: 'ana.demo@example.com',
  phone: '(11) 90000-0000',
  city: 'São Paulo',
  state: 'SP',
  country_code: 'BR',
  professional_summary:
    'Profissional em início de carreira com experiência em implantação de sistemas, organização de projetos e contato com usuários.',
  linkedin_url: 'https://linkedin.com/in/ana-demo',
  github_url: null,
  portfolio_url: null,
  preferences: {
    desired_titles: ['Analista de Projetos', 'Analista de Implantação'],
    desired_areas: ['Projetos', 'Implantação', 'Tecnologia'],
    target_locations: ['São Paulo', 'Remoto'],
    seniority_levels: ['JUNIOR'],
    work_models: ['REMOTE', 'HYBRID'],
    contract_types: ['CLT'],
    salary_min: 4200,
    salary_max: 6500,
    salary_currency: 'BRL',
    willing_to_travel: true,
    willing_to_relocate: false
  },
  experiences: [
    {
      id: 'demo-exp-1',
      company_name: 'Lumina Sistemas',
      role_title: 'Assistente de Implantação',
      start_date: '2025-02-01',
      end_date: null,
      is_current: true,
      description: 'Apoio a projetos de implantação de software e acompanhamento de usuários.',
      facts: [
        { id: 'demo-fact-1', kind: 'RESPONSIBILITY', value: 'Levantamento e organização de requisitos com usuários', source_type: 'USER_CONFIRMED' },
        { id: 'demo-fact-2', kind: 'RESPONSIBILITY', value: 'Acompanhamento de cronogramas e pendências de implantação', source_type: 'USER_CONFIRMED' },
        { id: 'demo-fact-3', kind: 'RESPONSIBILITY', value: 'Treinamento funcional para usuários finais', source_type: 'USER_CONFIRMED' }
      ]
    },
    {
      id: 'demo-exp-2',
      company_name: 'Orbit Tech',
      role_title: 'Estagiária de Operações',
      start_date: '2024-03-01',
      end_date: '2025-01-15',
      is_current: false,
      description: 'Suporte a rotinas operacionais e documentação de processos.',
      facts: [
        { id: 'demo-fact-4', kind: 'RESPONSIBILITY', value: 'Documentação de processos e procedimentos internos', source_type: 'USER_CONFIRMED' }
      ]
    }
  ],
  education: [
    {
      id: 'demo-edu-1',
      institution: 'Universidade Metropolitana',
      course: 'Engenharia de Software',
      status: 'IN_PROGRESS',
      start_date: '2025-01-01',
      end_date: '2028-12-01'
    }
  ],
  skills: [
    { id: 'demo-skill-1', name: 'Gestão de Projetos', source_type: 'USER_CONFIRMED' },
    { id: 'demo-skill-2', name: 'Levantamento de Requisitos', source_type: 'USER_CONFIRMED' },
    { id: 'demo-skill-3', name: 'Jira', source_type: 'USER_CONFIRMED' },
    { id: 'demo-skill-4', name: 'APIs e JSON', source_type: 'USER_CONFIRMED' }
  ],
  facts: [
    { id: 'demo-profile-fact-1', kind: 'OTHER', value: 'Experiência com contato direto com usuários', source_type: 'USER_CONFIRMED' }
  ],
  languages: [
    { id: 'demo-language-1', name: 'Português', proficiency: 'NATIVE', source_type: 'USER_CONFIRMED' },
    { id: 'demo-language-2', name: 'Inglês', proficiency: 'INTERMEDIATE', source_type: 'USER_CONFIRMED' }
  ],
  certifications: [
    { id: 'demo-cert-1', name: 'Fundamentos de Gestão de Projetos', issuer: 'Instituto Exemplo', source_type: 'USER_CONFIRMED' }
  ]
};

const defaultJobs: DemoJob[] = [
  {
    id: 'demo-job-1',
    company_name: 'Nuvem Labs',
    title: 'Analista de Projetos Júnior',
    location_text: 'São Paulo, SP · Híbrido',
    city: 'São Paulo',
    state: 'SP',
    work_model: 'HYBRID',
    contract_type: 'CLT',
    seniority: 'JUNIOR',
    status: 'ACTIVE',
    source_platform: 'Gupy',
    requirement_count: 6
  },
  {
    id: 'demo-job-2',
    company_name: 'Ativa Sistemas',
    title: 'Analista de Implantação',
    location_text: 'Remoto · Brasil',
    city: null,
    state: null,
    work_model: 'REMOTE',
    contract_type: 'CLT',
    seniority: 'JUNIOR',
    status: 'ACTIVE',
    source_platform: 'Site da empresa',
    requirement_count: 7
  },
  {
    id: 'demo-job-3',
    company_name: 'Mosaico Digital',
    title: 'Assistente de Projetos de Tecnologia',
    location_text: 'Campinas, SP · Híbrido',
    city: 'Campinas',
    state: 'SP',
    work_model: 'HYBRID',
    contract_type: 'CLT',
    seniority: 'JUNIOR',
    status: 'ACTIVE',
    source_platform: 'LinkedIn',
    requirement_count: 5
  },
  {
    id: 'demo-job-4',
    company_name: 'Prisma Commerce',
    title: 'Analista de Customer Success',
    location_text: 'São Paulo, SP · Presencial',
    city: 'São Paulo',
    state: 'SP',
    work_model: 'ONSITE',
    contract_type: 'CLT',
    seniority: 'JUNIOR',
    status: 'ACTIVE',
    source_platform: 'Gupy',
    requirement_count: 6
  },
  {
    id: 'demo-job-5',
    company_name: 'Vértice Tech',
    title: 'Coordenador de Projetos Sênior',
    location_text: 'Curitiba, PR · Presencial',
    city: 'Curitiba',
    state: 'PR',
    work_model: 'ONSITE',
    contract_type: 'PJ',
    seniority: 'SENIOR',
    status: 'ACTIVE',
    source_platform: 'Site da empresa',
    requirement_count: 8
  }
];

const defaultEvaluations: Record<string, Evaluation> = {
  'demo-job-1': {
    job_id: 'demo-job-1',
    relevance: 4,
    blocker_real: false,
    reason: 'Cargo, senioridade, rotina de projetos e modelo híbrido fazem sentido para o momento atual.',
    error_category: null
  },
  'demo-job-2': {
    job_id: 'demo-job-2',
    relevance: 4,
    blocker_real: false,
    reason: 'A vaga combina bem com implantação, treinamento e contato com usuários.',
    error_category: 'SIMPLE_ALIAS'
  },
  'demo-job-3': {
    job_id: 'demo-job-3',
    relevance: 3,
    blocker_real: false,
    reason: 'Boa vaga, mas a descrição usa terminologia diferente da experiência registrada.',
    error_category: 'SEMANTIC_EQUIVALENCE'
  }
};

const matchTemplates: Record<string, { score: number | null; band: string; coverage: number; matched: number; missing: number; unknown: number; preferences: number | null }> = {
  'demo-job-1': { score: 88, band: 'STRONG', coverage: 92, matched: 4, missing: 1, unknown: 1, preferences: 100 },
  'demo-job-2': { score: 83, band: 'GOOD', coverage: 86, matched: 4, missing: 1, unknown: 2, preferences: 100 },
  'demo-job-3': { score: 67, band: 'PARTIAL', coverage: 76, matched: 2, missing: 1, unknown: 2, preferences: 75 },
  'demo-job-4': { score: 51, band: 'PARTIAL', coverage: 70, matched: 2, missing: 2, unknown: 2, preferences: 50 },
  'demo-job-5': { score: 29, band: 'LOW', coverage: 82, matched: 1, missing: 5, unknown: 2, preferences: 0 }
};

function clone<T>(value: T): T {
  return structuredClone(value);
}

function defaultState(): DemoState {
  return {
    profile: clone(defaultProfile),
    jobs: clone(defaultJobs),
    evaluations: clone(defaultEvaluations)
  };
}

function readState(): DemoState {
  if (!browser) return defaultState();
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    const state = defaultState();
    writeState(state);
    return state;
  }
  try {
    return JSON.parse(raw) as DemoState;
  } catch {
    const state = defaultState();
    writeState(state);
    return state;
  }
}

function writeState(state: DemoState) {
  if (browser) localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  });
}

function requestBody(init?: RequestInit): Record<string, unknown> {
  if (!init?.body || typeof init.body !== 'string') return {};
  try {
    return JSON.parse(init.body) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function summary(job: DemoJob) {
  return {
    ...job,
    external_id: job.id,
    source_kind: 'MANUAL'
  };
}

function matchResult(jobId: string) {
  const state = readState();
  const job = state.jobs.find((item) => item.id === jobId);
  if (!job) return null;

  const template = matchTemplates[jobId] ?? {
    score: 62,
    band: 'PARTIAL',
    coverage: 72,
    matched: 2,
    missing: 1,
    unknown: Math.max(job.requirement_count - 3, 0),
    preferences: 75
  };

  const evidence = [
    {
      entity_type: 'EXPERIENCE',
      entity_id: 'demo-exp-1',
      value: 'Levantamento e organização de requisitos com usuários',
      source_type: 'USER_CONFIRMED',
      detail: 'Lumina Sistemas · Assistente de Implantação'
    }
  ];

  const requirementResults = [
    {
      requirement_id: `${jobId}-req-1`,
      kind: 'SKILL',
      importance: 'REQUIRED',
      value: jobId === 'demo-job-2' ? 'Implantação de sistemas' : 'Gestão e acompanhamento de projetos',
      status: 'MATCHED',
      weight: 3,
      evidence,
      reason: 'Há evidência confirmada no histórico profissional que sustenta este requisito.'
    },
    {
      requirement_id: `${jobId}-req-2`,
      kind: 'RESPONSIBILITY',
      importance: 'REQUIRED',
      value: 'Comunicação com usuários e áreas de negócio',
      status: 'MATCHED',
      weight: 3,
      evidence: [
        {
          entity_type: 'EXPERIENCE',
          entity_id: 'demo-exp-1',
          value: 'Treinamento funcional para usuários finais',
          source_type: 'USER_CONFIRMED',
          detail: 'Lumina Sistemas'
        }
      ],
      reason: 'A experiência registrada contém contato direto e treinamento de usuários.'
    },
    {
      requirement_id: `${jobId}-req-3`,
      kind: 'TOOL',
      importance: 'PREFERRED',
      value: jobId === 'demo-job-5' ? 'MS Project avançado' : 'Jira',
      status: jobId === 'demo-job-5' ? 'GAP' : 'MATCHED',
      weight: 1,
      evidence: jobId === 'demo-job-5' ? [] : [
        {
          entity_type: 'SKILL',
          entity_id: 'demo-skill-3',
          value: 'Jira',
          source_type: 'USER_CONFIRMED',
          detail: null
        }
      ],
      reason: jobId === 'demo-job-5'
        ? 'Não existe evidência confirmada deste nível de domínio no perfil.'
        : 'A ferramenta aparece como competência confirmada no perfil.'
    },
    {
      requirement_id: `${jobId}-req-4`,
      kind: 'EXPERIENCE',
      importance: 'REQUIRED',
      value: jobId === 'demo-job-5' ? '5 anos liderando projetos' : 'Experiência com projetos de tecnologia',
      status: jobId === 'demo-job-5' ? 'GAP' : 'UNKNOWN',
      weight: 3,
      evidence: [],
      reason: jobId === 'demo-job-5'
        ? 'A senioridade e o tempo mínimo pedidos estão acima das evidências registradas.'
        : 'Há contexto relacionado, mas o perfil ainda não traz evidência quantitativa suficiente para confirmar este requisito.'
    }
  ];

  return {
    job_id: jobId,
    profile_id: 'demo-profile-001',
    score: template.score,
    band: template.band,
    requirement_score: template.score,
    preference_score: template.preferences,
    evaluation_coverage: template.coverage,
    matched_required: template.matched,
    missing_required: template.missing,
    matched_preferred: 1,
    missing_preferred: jobId === 'demo-job-5' ? 1 : 0,
    unknown_requirements: template.unknown,
    requirement_results: requirementResults,
    preference_results: [
      {
        aspect: 'Modelo de trabalho',
        status: job.work_model === 'REMOTE' || job.work_model === 'HYBRID' ? 'ALIGNED' : 'CONFLICT',
        candidate_value: ['Remoto', 'Híbrido'],
        job_value: [job.work_model ?? 'Não informado'],
        reason: job.work_model === 'REMOTE' || job.work_model === 'HYBRID'
          ? 'O modelo da vaga está dentro das preferências atuais.'
          : 'A vaga é presencial e sua preferência atual prioriza remoto ou híbrido.'
      },
      {
        aspect: 'Tipo de contrato',
        status: job.contract_type === 'CLT' ? 'ALIGNED' : 'CONFLICT',
        candidate_value: ['CLT'],
        job_value: [job.contract_type ?? 'Não informado'],
        reason: job.contract_type === 'CLT'
          ? 'O contrato está alinhado ao que você procura.'
          : 'O tipo de contrato não está entre as preferências atuais.'
      }
    ],
    warnings: template.score === null ? ['Cobertura insuficiente para score confiável'] : []
  };
}

function dcg(labels: number[], k: number) {
  return labels.slice(0, k).reduce((sum, relevance, index) => {
    const gain = Math.pow(2, relevance) - 1;
    return sum + gain / Math.log2(index + 2);
  }, 0);
}

function report() {
  const state = readState();
  const evaluations = Object.values(state.evaluations);
  const ranking = evaluations
    .map((evaluation) => {
      const job = state.jobs.find((item) => item.id === evaluation.job_id)!;
      const match = matchResult(evaluation.job_id);
      return {
        job_id: evaluation.job_id,
        company_name: job.company_name,
        title: job.title,
        relevance: evaluation.relevance,
        score: match?.score ?? null,
        coverage: match?.evaluation_coverage ?? 0,
        band: match?.band ?? 'INSUFFICIENT_DATA',
        blocker_real: evaluation.blocker_real,
        reason: evaluation.reason,
        error_category: evaluation.error_category
      };
    })
    .sort((a, b) => (b.score ?? -1) - (a.score ?? -1));

  const relevantTotal = evaluations.filter((item) => item.relevance >= 3).length;
  const recall = (k: number) => {
    if (relevantTotal === 0) return 0;
    return ranking.slice(0, k).filter((item) => item.relevance >= 3).length / relevantTotal;
  };
  const labels = ranking.map((item) => item.relevance);
  const ideal = [...labels].sort((a, b) => b - a);
  const ndcg = (k: number) => {
    const best = dcg(ideal, k);
    return best === 0 ? 0 : dcg(labels, k) / best;
  };
  const scored = ranking.filter((item) => item.score !== null);
  const averageCoverage = ranking.length === 0
    ? 0
    : ranking.reduce((sum, item) => sum + item.coverage, 0) / ranking.length;

  return {
    metrics: {
      sample_count: evaluations.length,
      relevant_count: relevantTotal,
      scored_count: scored.length,
      average_coverage: averageCoverage,
      recall_at_5: recall(5),
      recall_at_10: recall(10),
      ndcg_at_5: ndcg(5),
      ndcg_at_10: ndcg(10)
    },
    ranking
  };
}

async function demoFetch(url: string, init?: RequestInit): Promise<Response> {
  const path = url.slice(LOCAL_API_PREFIX.length) || '/';
  const method = (init?.method ?? 'GET').toUpperCase();
  const state = readState();

  if (path === '/profile' && method === 'GET') return json(state.profile);
  if (path === '/profile' && method === 'PUT') {
    const body = requestBody(init);
    state.profile = { ...body, id: 'demo-profile-001' };
    writeState(state);
    return json(state.profile);
  }

  if (path === '/jobs' && method === 'GET') return json(state.jobs.map(summary));
  if (path === '/jobs' && method === 'POST') {
    const body = requestBody(init);
    const id = `demo-job-custom-${Date.now()}`;
    const requirements = Array.isArray(body.requirements) ? body.requirements : [];
    const job: DemoJob = {
      id,
      company_name: String(body.company_name ?? 'Empresa demo'),
      title: String(body.title ?? 'Nova oportunidade'),
      location_text: typeof body.location_text === 'string' ? body.location_text : null,
      city: typeof body.city === 'string' ? body.city : null,
      state: typeof body.state === 'string' ? body.state : null,
      work_model: typeof body.work_model === 'string' ? body.work_model : null,
      contract_type: typeof body.contract_type === 'string' ? body.contract_type : null,
      seniority: typeof body.seniority === 'string' ? body.seniority : null,
      status: 'ACTIVE',
      source_platform: typeof body.source_platform === 'string' ? body.source_platform : null,
      requirement_count: requirements.length
    };
    state.jobs = [job, ...state.jobs];
    writeState(state);
    return json(summary(job), 201);
  }

  const matchCapture = path.match(/^\/jobs\/([^/]+)\/match$/);
  const matchedJobId = matchCapture?.[1];
  if (matchedJobId && method === 'GET') {
    const result = matchResult(matchedJobId);
    return result ? json(result) : json({ detail: 'Vaga não encontrada.' }, 404);
  }

  if (path === '/evals/jobs' && method === 'GET') {
    return json(state.jobs.map((job) => ({
      job_id: job.id,
      company_name: job.company_name,
      title: job.title,
      location_text: job.location_text,
      work_model: job.work_model,
      contract_type: job.contract_type,
      seniority: job.seniority,
      requirement_count: job.requirement_count,
      evaluation: state.evaluations[job.id] ?? null
    })));
  }

  const evaluationCapture = path.match(/^\/evals\/jobs\/([^/]+)$/);
  const evaluatedJobId = evaluationCapture?.[1];
  if (evaluatedJobId && method === 'PUT') {
    const body = requestBody(init);
    const saved: Evaluation = {
      job_id: evaluatedJobId,
      relevance: Number(body.relevance ?? 0),
      blocker_real: Boolean(body.blocker_real),
      reason: typeof body.reason === 'string' ? body.reason : null,
      error_category: typeof body.error_category === 'string' ? body.error_category : null
    };
    state.evaluations[evaluatedJobId] = saved;
    writeState(state);
    return json(saved);
  }

  if (path === '/evals/report' && method === 'GET') {
    if (Object.keys(state.evaluations).length === 0) return json({ detail: 'Sem avaliações.' }, 404);
    return json(report());
  }

  return json({ detail: `Endpoint demo não implementado: ${method} ${path}` }, 404);
}

export function isVisualPreview() {
  if (!browser) return false;
  const host = window.location.hostname;
  return host !== 'localhost' && host !== '127.0.0.1';
}

export function installVisualPreviewApi() {
  if (!browser || !isVisualPreview()) return;

  const nativeFetch = window.fetch.bind(window);
  window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
    const url = input instanceof Request ? input.url : String(input);
    if (url.startsWith(LOCAL_API_PREFIX)) return demoFetch(url, init);
    return nativeFetch(input, init);
  }) as typeof window.fetch;
}
