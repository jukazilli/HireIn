import { env } from '$env/dynamic/private';
import { json, type RequestHandler } from '@sveltejs/kit';

const EXPECTED_KEY_SHA256 = '0ab52137c949a1c1419591f18761df346600635a65ece59b710a598d12d0ed44';

const jobs = [
  {
    source_kind: 'ATS',
    source_platform: 'Gupy',
    external_id: '12504889',
    source_url: 'https://gaudium.gupy.io/jobs/12504889?jobBoardSource=gupy_public_page',
    apply_url: 'https://gaudium.gupy.io/jobs/12504889?jobBoardSource=gupy_public_page',
    company_name: 'Gaudium',
    title: 'Analista de Implantação',
    location_text: 'Brasil · 100% remoto',
    country_code: 'BR',
    work_model: 'REMOTE',
    contract_type: 'CLT',
    salary_min: 3621.4,
    salary_max: 3621.4,
    salary_currency: 'BRL',
    salary_period: 'MONTH',
    description_raw:
      'Atuação remota na área de Geração, responsável por gerar, manter e atualizar aplicativos Android e iOS, acompanhar demandas e indicadores, seguir políticas das lojas e propor melhorias de processo.',
    status: 'ACTIVE',
    requirements: [
      { kind: 'EDUCATION', importance: 'REQUIRED', value: 'Sistemas de Informação, ADS, Ciência da Computação ou áreas correlatas', source_text: 'Ensino superior cursando ou concluído em Sistemas de Informação, ADS, Ciência da Computação ou áreas correlatas.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Organização e atenção a detalhes', source_text: 'Organização e atenção a detalhes para lidar com múltiplas demandas operacionais.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Comunicação e raciocínio lógico', source_text: 'Boa comunicação e bom raciocínio lógico.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Senso de prioridade', source_text: 'Senso de prioridade.' },
      { kind: 'DOMAIN', importance: 'PREFERRED', value: 'Google Play e App Store', source_text: 'Noções de atualização e manutenção de aplicativos na Google Play e App Store.' },
      { kind: 'TOOL', importance: 'PREFERRED', value: 'Ferramentas de automação de processos', source_text: 'Experiência ou familiaridade com ferramentas de automação de processos.' },
      { kind: 'SKILL', importance: 'PREFERRED', value: 'Scripts de automação', source_text: 'Noções de programação para desenvolvimento e manutenção de scripts de automação.' }
    ]
  },
  {
    source_kind: 'ATS',
    source_platform: 'Gupy',
    external_id: '11622615',
    source_url: 'https://populos.gupy.io/jobs/11622615?jobBoardSource=gupy_public_page',
    apply_url: 'https://populos.gupy.io/jobs/11622615?jobBoardSource=gupy_public_page',
    company_name: 'Populos',
    title: 'Analista de Implementação ITSM Pleno',
    location_text: 'Pinheiros, São Paulo - SP · Híbrido · 2 dias presenciais por semana',
    city: 'São Paulo',
    state: 'SP',
    country_code: 'BR',
    work_model: 'HYBRID',
    seniority: 'MID',
    description_raw:
      'Implantação, configuração, evolução e sustentação de plataforma ITSM, com levantamento de requisitos, desenho de processos, workflows, SLAs, integrações, documentação e melhoria contínua.',
    status: 'ACTIVE',
    requirements: [
      { kind: 'EXPERIENCE', importance: 'REQUIRED', value: 'Implementação e sustentação de Freshservice, Jira ou outras plataformas ITSM', source_text: 'Experiência com implementação e sustentação de Freshservice, Jira ou outras plataformas ITSM.' },
      { kind: 'EXPERIENCE', importance: 'REQUIRED', value: 'Configuração e customização de ferramentas ITSM', source_text: 'Experiência em configuração e customização de ferramentas ITSM.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Integrações via API REST', source_text: 'Conhecimento em integrações via API REST.' },
      { kind: 'DOMAIN', importance: 'REQUIRED', value: 'ITIL 4', source_text: 'Conhecimento em ITIL 4.' },
      { kind: 'RESPONSIBILITY', importance: 'REQUIRED', value: 'Levantamento de requisitos e interação com usuários e stakeholders', source_text: 'Capacidade de conduzir levantamento de requisitos e interagir com usuários e stakeholders.' },
      { kind: 'EDUCATION', importance: 'REQUIRED', value: 'Tecnologia da Informação ou áreas correlatas', source_text: 'Ensino superior completo ou cursando em Tecnologia da Informação ou áreas correlatas.' },
      { kind: 'CERTIFICATION', importance: 'PREFERRED', value: 'ITIL 4 ou Freshworks', source_text: 'Certificações ITIL 4 ou Freshworks são diferenciais.' },
      { kind: 'SKILL', importance: 'PREFERRED', value: 'BPMN, COBIT ou automação de processos', source_text: 'BPMN, COBIT e automação de processos são diferenciais.' }
    ]
  },
  {
    source_kind: 'ATS',
    source_platform: 'Gupy',
    external_id: '11865169',
    source_url: 'https://autoglassadministrativo.gupy.io/jobs/11865169?jobBoardSource=gupy_public_page',
    apply_url: 'https://autoglassadministrativo.gupy.io/jobs/11865169?jobBoardSource=gupy_public_page',
    company_name: 'Grupo Autoglass',
    title: 'Analista de Projetos I - PMO',
    location_text: 'Modalidade/local não informados claramente na publicação',
    country_code: 'BR',
    description_raw:
      'Apoio a projetos de inovação e melhoria contínua, com escopo, cronograma, orçamento, riscos, indicadores, relatórios, documentação, comunicação com stakeholders e aplicação de metodologias e templates do PMO.',
    status: 'ACTIVE',
    requirements: [
      { kind: 'EDUCATION', importance: 'REQUIRED', value: 'Administração, Engenharia ou áreas afins', required_education_status: 'IN_PROGRESS', source_text: 'Graduação em andamento em Administração, Engenharia ou áreas afins.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Lean, Kaizen, PDCA, 5S ou A3', required_level: 'BEGINNER', source_text: 'Conhecimento básico em filosofia Lean e ferramentas de melhoria contínua.' },
      { kind: 'TOOL', importance: 'REQUIRED', value: 'Pacote Office', required_level: 'BEGINNER', source_text: 'Pacote Office em nível básico.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'PMBOK ou Scrum', source_text: 'Metodologias de projetos PMBOK e Scrum.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Comunicação e articulação com stakeholders', source_text: 'Boa comunicação e habilidade de articulação com múltiplas áreas e níveis hierárquicos.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Análise crítica e pensamento sistêmico', source_text: 'Capacidade de análise crítica e pensamento sistêmico.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Priorização, organização e gestão do tempo', source_text: 'Forte senso de priorização e urgência, organização e gestão de tempo.' }
    ]
  },
  {
    source_kind: 'ATS',
    source_platform: 'Gupy',
    external_id: '12439153',
    source_url: 'https://neogridcarreiras.gupy.io/jobs/12439153?jobBoardSource=gupy_public_page',
    apply_url: 'https://neogridcarreiras.gupy.io/jobs/12439153?jobBoardSource=gupy_public_page',
    company_name: 'Neogrid',
    title: 'Product Manager Specialist I',
    location_text: 'Brasil · Remoto',
    country_code: 'BR',
    work_model: 'REMOTE',
    seniority: 'SPECIALIST',
    description_raw:
      'Product Manager especialista para produto B2B de cadeia de abastecimento, com roadmap, discovery contínuo, backlog, indicadores e colaboração com desenvolvimento, dados, implantação, Customer Success e Design.',
    status: 'ACTIVE',
    requirements: [
      { kind: 'EXPERIENCE', importance: 'REQUIRED', value: 'Product Manager em produtos B2B complexos', source_text: 'Experiência sólida como Product Manager em produtos B2B complexos.' },
      { kind: 'DOMAIN', importance: 'REQUIRED', value: 'Modelos colaborativos entre indústria, varejo, fabricante e distribuidor', source_text: 'Conhecimento em modelos de negócio colaborativos entre elos da cadeia.' },
      { kind: 'EXPERIENCE', importance: 'REQUIRED', value: 'Produtos com forte componente de dados', source_text: 'Vivência em produtos com forte componente de dados.' },
      { kind: 'RESPONSIBILITY', importance: 'REQUIRED', value: 'Transformar conhecimento operacional em artefatos de produto estruturados', source_text: 'Facilidade para transformar conhecimento operacional de campo em artefatos de produto estruturados.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Comunicação executiva orientada a evidências', source_text: 'Comunicação executiva orientada a evidência para públicos diversos, incluindo comitê e diretoria.' },
      { kind: 'EXPERIENCE', importance: 'REQUIRED', value: 'Referência técnica de produto em nível especialista', source_text: 'Senioridade suficiente para atuar como referência técnica de produto.' },
      { kind: 'DOMAIN', importance: 'PREFERRED', value: 'Supply chain, DRP, VMI, CMI ou S&OP', source_text: 'Experiência com plataformas de abastecimento e supply chain é um plus.' },
      { kind: 'EXPERIENCE', importance: 'PREFERRED', value: 'Modernização ou migração de arquitetura legada', source_text: 'Vivência em modernização ou migração de arquitetura legada é um plus.' }
    ]
  },
  {
    source_kind: 'ATS',
    source_platform: 'Gupy',
    external_id: '12267568',
    source_url: 'https://carreirasomie.gupy.io/jobs/12267568?jobBoardSource=gupy_public_page',
    apply_url: 'https://carreirasomie.gupy.io/jobs/12267568?jobBoardSource=gupy_public_page',
    company_name: 'Omie',
    title: 'Analista de Implementação Pleno (Multivarejo)',
    location_text: 'Brasil · Remoto',
    country_code: 'BR',
    work_model: 'REMOTE',
    seniority: 'MID',
    description_raw:
      'Onboarding e implementação para clientes de varejo, com entendimento de necessidades, setup inicial, cronograma, integrações, treinamentos, indicadores de sucesso e evolução da experiência inicial do cliente.',
    status: 'ACTIVE',
    requirements: [
      { kind: 'DOMAIN', importance: 'REQUIRED', value: 'Software ou SaaS', source_text: 'Atuação no segmento de Software ou SaaS.' },
      { kind: 'EDUCATION', importance: 'REQUIRED', value: 'Ensino superior completo ou cursando', source_text: 'Superior completo ou cursando; Administração, Sistemas de Informação e Gestão Comercial são diferenciais.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Comunicação e didática para treinamento de clientes', source_text: 'Boa comunicação verbal e escrita, com didática, clareza e naturalidade ao treinar pessoas.' },
      { kind: 'EXPERIENCE', importance: 'REQUIRED', value: 'Onboarding, atendimento B2B e Customer Success', source_text: 'Experiência prévia em onboarding, atendimento ao cliente B2B e Customer Success.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Organização, resiliência e gestão do tempo', source_text: 'Organização, resiliência e boa gestão do tempo.' },
      { kind: 'SKILL', importance: 'REQUIRED', value: 'Pensamento analítico e orientação a dados', source_text: 'Pensamento analítico e orientado a dados.' },
      { kind: 'TOOL', importance: 'PREFERRED', value: 'CRM e ferramentas de suporte', source_text: 'Domínio de CRM e ferramentas de suporte será considerado um diferencial.' },
      { kind: 'DOMAIN', importance: 'PREFERRED', value: 'PDV, e-commerce e marketplaces', source_text: 'Vivência com integração de canais de venda, como PDV, e-commerce e marketplaces, é diferencial.' }
    ]
  }
];

async function sha256(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
}

export const GET: RequestHandler = async ({ url }) => {
  const providedKey = url.searchParams.get('key') ?? '';
  if (!providedKey || (await sha256(providedKey)) !== EXPECTED_KEY_SHA256) {
    return json({ detail: 'not found' }, { status: 404 });
  }

  const apiUrl = env.HIREIN_API_URL?.trim()?.replace(/\/$/, '');
  const backendToken = env.HIREIN_BACKEND_TOKEN?.trim();
  if (!apiUrl || !backendToken) {
    return json({ detail: 'backend not configured' }, { status: 503 });
  }

  const results: Array<Record<string, unknown>> = [];
  let created = 0;
  let conflicts = 0;
  let failures = 0;

  for (const job of jobs) {
    try {
      const response = await fetch(`${apiUrl}/api/v1/jobs`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-hirein-pilot-token': backendToken
        },
        body: JSON.stringify(job),
        signal: AbortSignal.timeout(20_000)
      });

      let payload: unknown = null;
      try {
        payload = await response.json();
      } catch {
        payload = null;
      }

      if (response.status === 201) created += 1;
      else if (response.status === 409) conflicts += 1;
      else failures += 1;

      results.push({
        company_name: job.company_name,
        title: job.title,
        status: response.status,
        response: payload
      });
    } catch (error) {
      failures += 1;
      results.push({
        company_name: job.company_name,
        title: job.title,
        status: 0,
        error: error instanceof Error ? error.message : 'request failed'
      });
    }
  }

  return json(
    {
      holdout: 'Match v1.5 — Blind Holdout #4',
      attempted: jobs.length,
      created,
      conflicts,
      failures,
      match_queried: false,
      results
    },
    { headers: { 'cache-control': 'no-store' } }
  );
};
