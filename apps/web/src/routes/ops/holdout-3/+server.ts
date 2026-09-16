import { env } from '$env/dynamic/private';
import { json, type RequestHandler } from '@sveltejs/kit';

const EXPECTED_KEY_SHA256 = '3f9e264bafd6ff0ea172340b2c9198cd55acd8f63dd1e7c75e9125d045bcabf0';

const jobs = [
  {
    "source_kind": "ATS",
    "source_platform": "Gupy",
    "external_id": "11551816",
    "source_url": "https://logothink.gupy.io/jobs/11551816",
    "apply_url": "https://logothink.gupy.io/jobs/11551816",
    "company_name": "Logithink",
    "title": "Analista de Implantação Protheus (NFLegal)",
    "location_text": "Modelo divergente na publicação: remoto na listagem e híbrido no detalhe",
    "country_code": "BR",
    "contract_type": "PJ",
    "description_raw": "Implantação ponta a ponta do NFLegal no ecossistema TOTVS Protheus, incluindo mapeamento de processos fiscais, configuração, atualizações, ajustes básicos, administração de acessos e treinamento de usuários.",
    "status": "ACTIVE",
    "requirements": [
      {"kind":"TOOL","importance":"REQUIRED","value":"TOTVS Protheus - módulo Compras","source_text":"Conhecimento no Protheus, módulo Compras."},
      {"kind":"TOOL","importance":"REQUIRED","value":"TOTVS Protheus - Configurador","source_text":"Conhecimento no Protheus, módulo Configurador."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Pontos de entrada e desenvolvimento básico","source_text":"Conhecimentos em pontos de entrada e desenvolvimento básico."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Comunicação","source_text":"Excelentes habilidades de comunicação."},
      {"kind":"EXPERIENCE","importance":"PREFERRED","value":"Implantação de soluções de notas fiscais","source_text":"Experiência prática com implantação de soluções de notas fiscais."},
      {"kind":"TOOL","importance":"PREFERRED","value":"TOTVS Transmite","source_text":"TOTVS Transmite citado como diferencial."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Processos fiscais e lançamento de notas fiscais","source_text":"A função mapeia fluxos fiscais, notas e cadastros relacionados."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"TOTVS Atração de Talentos","external_id":"12183",
    "source_url":"https://atracaodetalentos.totvs.app/vempratotvs/12183/servicos-analista-de-implantacao-junior-microvix",
    "apply_url":"https://atracaodetalentos.totvs.app/vempratotvs/12183/servicos-analista-de-implantacao-junior-microvix",
    "company_name":"TOTVS","title":"[Serviços] Analista de Implantação Júnior | Microvix",
    "location_text":"Rio de Janeiro - RJ | Remoto","city":"Rio de Janeiro","state":"RJ","country_code":"BR",
    "work_model":"REMOTE","contract_type":"CLT","seniority":"JUNIOR",
    "description_raw":"Apoio à implantação de sistemas e soluções Linx, configuração conforme escopo, treinamento de usuários, acompanhamento de go-live, suporte inicial e interação com suporte, desenvolvimento e projetos.",
    "status":"ACTIVE",
    "requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Ensino superior cursando ou completo em TI, Sistemas ou áreas correlatas","source_text":"Ensino superior cursando ou completo em área de tecnologia ou correlata."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Implantação e parametrização de softwares ou ERPs","source_text":"Experiência com implantações e parametrizações em softwares ou ERPs."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Comunicação e didática para treinamentos","source_text":"Boa comunicação e didática para treinamentos."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Organização e gestão de atividades","source_text":"Organização e gestão de atividades."},
      {"kind":"OTHER","importance":"REQUIRED","value":"Disponibilidade de horário e para viagens","source_text":"Disponibilidade de horário e para viagens."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Microvix ou SETA","source_text":"Experiência com Microvix ou SETA é desejável."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Varejo","source_text":"Conhecimento em varejo é desejável."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Excel","required_level":"INTERMEDIATE","source_text":"Excel intermediário é desejável."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"TOTVS Atração de Talentos","external_id":"11852",
    "source_url":"https://atracaodetalentos.totvs.app/vempratotvs/11852/produto-product-manager-remoto",
    "apply_url":"https://atracaodetalentos.totvs.app/vempratotvs/11852/produto-product-manager-remoto",
    "company_name":"TOTVS","title":"[Produto] Product Manager (Remoto)",
    "location_text":"Florianópolis - SC | Remoto","city":"Florianópolis","state":"SC","country_code":"BR",
    "work_model":"REMOTE","contract_type":"CLT",
    "description_raw":"Product Manager do time de Integrações da Plataforma RH, atuando entre produto, requisitos e gestão de projetos, com roadmap, backlog, stakeholders, indicadores, cronogramas, validação de entregas e cerimônias ágeis.",
    "status":"ACTIVE",
    "requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Ensino superior completo em área de negócio ou tecnologia","required_education_status":"COMPLETED","source_text":"Superior completo, preferencialmente em negócio ou tecnologia."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Gestão de projetos","source_text":"Conhecimento prévio em gestão de projetos."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Gestão de indicadores","source_text":"Gestão de indicadores."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Técnicas de priorização","source_text":"Conhecimento de técnicas de priorização."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Metodologias ágeis","source_text":"Conhecimento de metodologias ágeis."},
      {"kind":"TOOL","importance":"REQUIRED","value":"Jira","source_text":"Gestão por meio do Jira."},
      {"kind":"EXPERIENCE","importance":"PREFERRED","value":"Projetos de integração de dados","source_text":"Experiência prévia com projetos de integração de dados é desejável."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Regras de negócio de produtos de RH","source_text":"Conhecimento de regras de negócio de produtos para RH é desejável."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Postman","source_text":"Ferramenta de teste de API citada como desejável."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Grafana ou OpenSearch","source_text":"Leitura de logs com Grafana ou OpenSearch é desejável."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"12148683",
    "source_url":"https://waycarbon.gupy.io/jobs/12148683?jobBoardSource=gupy_public_page",
    "apply_url":"https://waycarbon.gupy.io/jobs/12148683?jobBoardSource=gupy_public_page",
    "company_name":"WayCarbon","title":"Product Owner Junior - Sustentabilidade",
    "location_text":"Brasil: remoto fora da região de Belo Horizonte; híbrido em Belo Horizonte/MG","country_code":"BR",
    "seniority":"JUNIOR",
    "description_raw":"Product Owner Junior responsável pela entrega end to end de produtos digitais de sustentabilidade, priorização de backlog, levantamento de requisitos, histórias e critérios de aceite, sprints, roadmap e interface com stakeholders.",
    "status":"ACTIVE",
    "requirements":[
      {"kind":"DOMAIN","importance":"REQUIRED","value":"GHG Protocol e inventários de GEE","source_text":"Conhecimento de GHG Protocol e inventários de gases de efeito estufa."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Escopos 1, 2 e 3 de emissões","source_text":"Entendimento dos Escopos 1, 2 e 3."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Fatores de emissão","source_text":"Noção de fatores de emissão e cálculo."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Sustentabilidade ou mudanças climáticas","source_text":"Vivência em sustentabilidade ou mudanças climáticas."},
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Engenharia Ambiental, Gestão Ambiental, Engenharia de Produção, Ciências Ambientais ou áreas afins","source_text":"Formação em área ambiental, produção ou afins."},
      {"kind":"EXPERIENCE","importance":"PREFERRED","value":"Analista de Produtos, Product Owner ou Analista Funcional","source_text":"Vivência em funções de produto ou análise funcional é diferencial."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"SaaS ou dados de sustentabilidade","source_text":"Atuação em software de sustentabilidade SaaS ou dados é diferencial."},
      {"kind":"SKILL","importance":"PREFERRED","value":"Metodologias ágeis","source_text":"Prática com metodologias ágeis é diferencial."},
      {"kind":"CERTIFICATION","importance":"PREFERRED","value":"Programa Brasileiro GHG Protocol ou equivalente","source_text":"Certificação ou curso GHG Protocol é diferencial."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"12280658",
    "source_url":"https://brain.gupy.io/jobs/12280658?jobBoardSource=gupy_public_page",
    "apply_url":"https://brain.gupy.io/jobs/12280658?jobBoardSource=gupy_public_page",
    "company_name":"Brain","title":"PRODUCT OWNER I",
    "location_text":"Uberlândia - MG | Híbrido","city":"Uberlândia","state":"MG","country_code":"BR",
    "work_model":"HYBRID",
    "description_raw":"Product Owner I com foco em aprendizado e evolução de produtos digitais, construção e manutenção de backlog, MVPs, cerimônias ágeis, business case, roadmap e alinhamento com stakeholders.",
    "status":"ACTIVE",
    "requirements":[
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Produto digital e inovação","source_text":"Fundamentos de produto digital e inovação."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Scrum ou Lean Startup","source_text":"Noções de metodologias ágeis como Scrum e Lean Startup."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Edge, Cloud, serviços profissionais de TI ou Cybersegurança","source_text":"Conhecimento introdutório em tecnologias e serviços de TI citados."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Gestão de backlog","source_text":"Gestão de backlog."},
      {"kind":"TOOL","importance":"REQUIRED","value":"Jira, Miro ou Trello","source_text":"Ferramentas de colaboração como Jira, Miro ou Trello."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Canvas ou Lean Canvas","source_text":"Noções de modelagem de negócios com Canvas ou Lean Canvas."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"11969292",
    "source_url":"https://positivo.gupy.io/jobs/11969292?jobBoardSource=gupy_portal",
    "apply_url":"https://positivo.gupy.io/jobs/11969292?jobBoardSource=gupy_portal",
    "company_name":"Grupo Positivo","title":"ANALISTA DE PROJETOS PL",
    "location_text":"Curitiba - PR | Híbrido","city":"Curitiba","state":"PR","country_code":"BR",
    "work_model":"HYBRID","seniority":"MID",
    "description_raw":"Gestão de projetos de sistemas de TI desde o entendimento da necessidade até a entrega, com requisitos, planejamento, cronograma, riscos, escopo, indicadores, reuniões, fornecedores e stakeholders.",
    "status":"ACTIVE",
    "requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Ensino superior em TI, Engenharia, Administração ou áreas correlatas","source_text":"Ensino superior em TI, engenharias, administração ou correlatas."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Gerenciamento de projetos","min_years":2,"source_text":"Ao menos 2 anos de experiência com gerenciamento de projetos."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Cronograma, riscos, custos e escopo de projetos","source_text":"Experiência acompanhando cronograma, riscos, custos e escopo."},
      {"kind":"TOOL","importance":"REQUIRED","value":"MS Project","source_text":"Conhecimento em MS Project."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"11814947",
    "source_url":"https://howbe.gupy.io/jobs/11814947?jobBoardSource=gupy_public_page",
    "apply_url":"https://howbe.gupy.io/jobs/11814947?jobBoardSource=gupy_public_page",
    "company_name":"HowBe","title":"ANALISTA DE PROJETOS",
    "location_text":"Fortaleza - CE","city":"Fortaleza","state":"CE","country_code":"BR",
    "description_raw":"Atuação em planejamento e acompanhamento de projetos de tecnologia, cronogramas, orçamento e recursos, análise de dados, documentação, relatórios de status, comunicação com stakeholders e gestão de riscos.",
    "status":"ACTIVE",
    "requirements":[
      {"kind":"SKILL","importance":"REQUIRED","value":"Scrum, Kanban ou PMBOK","source_text":"Conhecimento em metodologias ágeis e tradicionais."},
      {"kind":"TOOL","importance":"REQUIRED","value":"Ferramentas de gestão de projetos","source_text":"Experiência em ferramentas de gestão."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Análise de requisitos e especificações técnicas","source_text":"Habilidade para análise de requisitos e especificações técnicas."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Liderança e influência sem autoridade direta","source_text":"Liderança e influência sem autoridade direta."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Comunicação","source_text":"Boa comunicação."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Resolução de problemas","source_text":"Resolução de problemas."},
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Formação em TI, Administração, Engenharia ou áreas correlatas","source_text":"Formação em TI, Administração, Engenharia ou correlatas."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Gestão de projetos de tecnologia","source_text":"Experiência com gestão de projetos de tecnologia."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"12423106",
    "source_url":"https://aegro.gupy.io/jobs/12423106?jobBoardSource=gupy_portal",
    "apply_url":"https://aegro.gupy.io/jobs/12423106?jobBoardSource=gupy_portal",
    "company_name":"Aegro","title":"Analista de Implementação Pleno - CS",
    "location_text":"Porto Alegre - RS | Híbrido","city":"Porto Alegre","state":"RS","country_code":"BR",
    "work_model":"HYBRID","seniority":"MID",
    "description_raw":"Implementação de alta complexidade com múltiplos módulos e integrações, mapeamento de processos, validação e migração de dados, capacitações, gestão de cronogramas, riscos e melhoria de fluxos na área de Customer Success.",
    "status":"ACTIVE",
    "requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Ensino superior completo em Agronomia, Administração, Contábeis, TI, Análise de Sistemas ou áreas afins","required_education_status":"COMPLETED","source_text":"Ensino superior completo em uma das áreas relacionadas."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Implementação, onboarding técnico ou configuração de sistemas de gestão","source_text":"Experiência em implementação, onboarding técnico ou configuração de sistemas."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Migração e validação de dados, integrações e diagnóstico de processos","source_text":"Experiência com dados, integrações e diagnóstico de processos."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Planilhas, leitura de dados e relatórios","source_text":"Domínio de planilhas, leitura de dados e relatórios."},
      {"kind":"TOOL","importance":"REQUIRED","value":"Ferramentas de IA e automação","required_level":"ADVANCED","source_text":"Uso avançado de IA e automação na rotina técnica."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Capacitação de usuários e comunicação com lideranças","source_text":"Comunicação segura em capacitações e conversas com lideranças."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Gestão de propriedades rurais","source_text":"Conhecimento de gestão rural é diferencial."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Zapier, Make ou n8n","source_text":"Automações com Zapier, Make ou n8n são diferenciais."},
      {"kind":"SKILL","importance":"PREFERRED","value":"Gestão de projetos","source_text":"Metodologias de gestão de projetos são diferenciais."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"11945108",
    "source_url":"https://validcarreiras-comercial.gupy.io/jobs/11945108?jobBoardSource=gupy_public_page",
    "apply_url":"https://validcarreiras-comercial.gupy.io/jobs/11945108?jobBoardSource=gupy_public_page",
    "company_name":"Valid","title":"Analista de Customer Success",
    "location_text":"São Paulo - SP | Híbrido","city":"São Paulo","state":"SP","country_code":"BR",
    "work_model":"HYBRID",
    "description_raw":"Gestão de carteira de clientes, acompanhamento de implantação, demandas entre Produto/Tecnologia/Operações/Suporte, reuniões de status, indicadores de sucesso, planos de ação, relatórios e identificação de oportunidades de expansão.",
    "status":"ACTIVE",
    "requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Ensino superior completo ou cursando em Administração, Gestão de Negócios, Tecnologia ou áreas correlatas","source_text":"Ensino superior completo ou cursando em área relacionada."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Atendimento ao cliente, relacionamento, Customer Success, Customer Experience ou Suporte","source_text":"Experiência em atendimento, relacionamento, CS, CX, suporte ou área relacionada."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Perfil analítico e identificação de melhorias","source_text":"Capacidade analítica e de identificar oportunidades de melhoria."},
      {"kind":"TOOL","importance":"REQUIRED","value":"Excel","source_text":"Conhecimento em Office, principalmente Excel."},
      {"kind":"TOOL","importance":"REQUIRED","value":"CRM ou plataforma de gestão de relacionamento","source_text":"Familiaridade com CRM ou plataforma de relacionamento."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Trabalho colaborativo entre áreas","source_text":"Capacidade de conectar áreas para resolver problemas."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Tecnologia, fintech, meios de pagamento, identidade digital, antifraude ou Cyber Security","source_text":"Experiência nesses segmentos é diferencial."},
      {"kind":"EXPERIENCE","importance":"PREFERRED","value":"Clientes corporativos B2B e múltiplos stakeholders","source_text":"Vivência B2B com múltiplos stakeholders é diferencial."},
      {"kind":"EXPERIENCE","importance":"PREFERRED","value":"Integrações entre sistemas, SLA ou gestão de demandas técnicas","source_text":"Experiência com integrações, SLA ou demandas técnicas é diferencial."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Power BI","source_text":"Power BI é diferencial."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"TOTVS Atração de Talentos","external_id":"75",
    "source_url":"https://atracaodetalentos.totvs.app/hsystem/75/analista-de-customer-success-onboarding-pl",
    "apply_url":"https://atracaodetalentos.totvs.app/hsystem/75/analista-de-customer-success-onboarding-pl",
    "company_name":"HSystem","title":"Analista de Customer Success Onboarding PL",
    "location_text":"Florianópolis - SC | Presencial","city":"Florianópolis","state":"SC","country_code":"BR",
    "work_model":"ONSITE","contract_type":"CLT","seniority":"MID",
    "salary_min":3046,"salary_max":4100,"salary_currency":"BRL","salary_period":"MONTH",
    "description_raw":"Condução ponta a ponta da implementação e onboarding de soluções HSystem, com configuração, diagnóstico e mapeamento de processos, gestão simultânea de onboardings, capacitação de usuários, métricas e transição para CS ongoing.",
    "status":"ACTIVE",
    "requirements":[
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Implementação, onboarding ou implantação de software SaaS","source_text":"Experiência comprovada em implementação, onboarding ou implantação de SaaS."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Comunicação verbal e escrita","source_text":"Excelente comunicação verbal e escrita."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Diagnóstico de cenários e resolução de problemas","source_text":"Capacidade analítica para diagnosticar cenários e propor soluções."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Organização e gestão de tempo para múltiplos onboardings","source_text":"Organização e gestão de tempo para múltiplos onboardings."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Integração de sistemas, configuração e personalização de software SaaS","source_text":"Conhecimento em integração, configuração e personalização de SaaS."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Customer Success","source_text":"Orientação a resultados e experiência do cliente com mindset de CS."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Relacionamento com clientes e stakeholders internos","source_text":"Trabalho colaborativo e construção de relacionamentos sólidos."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Mercado hoteleiro","source_text":"Conhecimento do mercado hoteleiro é diferencial."}
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
      holdout: 'Match v1.4 — Blind Holdout #3',
      attempted: jobs.length,
      created,
      conflicts,
      failures,
      match_queried: false,
      results
    },
    {
      headers: {
        'cache-control': 'no-store'
      }
    }
  );
};
