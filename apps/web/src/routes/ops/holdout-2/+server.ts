import { env } from '$env/dynamic/private';
import { json, type RequestHandler } from '@sveltejs/kit';

const EXPECTED_KEY_SHA256 = 'a4a586e0588d19fa74a471fc4ede357a996e73b387f8d55c1c46327a03a5cc1b';

const jobs = [
  {
    "source_kind": "ATS",
    "source_platform": "Gupy",
    "external_id": "12457936",
    "source_url": "https://techne.gupy.io/jobs/12457936?jobBoardSource=gupy_public_page",
    "apply_url": "https://techne.gupy.io/jobs/12457936?jobBoardSource=gupy_public_page",
    "company_name": "Techne",
    "title": "Analista de ERP Junior",
    "location_text": "Trabalho Remoto",
    "country_code": "BR",
    "work_model": "REMOTE",
    "contract_type": "CLT",
    "seniority": "JUNIOR",
    "description_raw": "Atuação na sustentação funcional do ERP educacional Lyceum, apoiando análise e resolução de demandas, configurações, testes, documentação, consultas SQL e treinamentos. A oportunidade é CLT e remota.",
    "status": "ACTIVE",
    "requirements": [
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Formação superior em Computação, Engenharia de Software, ADS ou áreas correlatas","source_text":"Formação superior em áreas de Computação, Engenharia de Software ou ADS."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Sustentação ou suporte de sistemas ERP","source_text":"Vivência com sistemas ERP em atividades de sustentação ou suporte."},
      {"kind":"TOOL","importance":"REQUIRED","value":"SQL","source_text":"Conhecimento de SQL, especialmente SELECT, WHERE e JOIN."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Análise e tratamento de demandas de sistemas","source_text":"Experiência com análise e tratamento de demandas relacionadas a sistemas."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Comunicação escrita e verbal","source_text":"Boa comunicação escrita e verbal."},
      {"kind":"TOOL","importance":"PREFERRED","value":"ERP Lyceum","source_text":"Experiência com o ERP Lyceum."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Educação","source_text":"Vivência em empresas ou projetos do segmento educacional."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Processos acadêmicos ou administrativos","source_text":"Conhecimento de processos acadêmicos ou administrativos de instituições de ensino."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Jira, Trello, Zendesk ou Redmine","source_text":"Experiência com ferramentas de gestão de chamados."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Ferramentas de IA e automação","source_text":"Conhecimento ou experiência com ferramentas de IA e automação."}
    ]
  },
  {
    "source_kind": "ATS",
    "source_platform": "Gupy",
    "external_id": "11639928",
    "source_url": "https://techne.gupy.io/jobs/11639928?jobBoardSource=gupy_public_page",
    "apply_url": "https://techne.gupy.io/jobs/11639928?jobBoardSource=gupy_public_page",
    "company_name": "Techne",
    "title": "Consultor de Implantação (E-social)",
    "location_text": "Rio de Janeiro - RJ",
    "city": "Rio de Janeiro",
    "state": "RJ",
    "country_code": "BR",
    "work_model": "HYBRID",
    "contract_type": "CLT",
    "description_raw": "Consultoria e implantação de soluções de folha de pagamento e eSocial para gestão pública, com levantamento de requisitos, parametrização, integrações, suporte, treinamento e acompanhamento de conformidade legal. Regime CLT e híbrido no Rio de Janeiro.",
    "status": "ACTIVE",
    "requirements": [
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Ensino superior em Contábeis, Administração, RH, Direito, Sistemas de Informação ou áreas correlatas","required_education_status":"COMPLETED","source_text":"Ensino Superior completo em áreas correlatas."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Implantação de soluções de Gestão de Pessoas","source_text":"Experiência como Analista ou Consultor de Implantação de soluções de Gestão de Pessoas."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"eSocial","source_text":"Experiência com implantação e parametrização de soluções de eSocial."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"SPED e EFD-Reinf","source_text":"Experiência com o projeto SPED, especialmente eSocial e EFD-Reinf."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Levantamento de requisitos","source_text":"Experiência com levantamento de requisitos junto aos clientes."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Documentação de requisitos","source_text":"Experiência com documentação de requisitos."},
      {"kind":"TOOL","importance":"REQUIRED","value":"SQL","source_text":"Experiência com linguagem SQL."},
      {"kind":"TOOL","importance":"REQUIRED","value":"Banco de dados relacional","source_text":"Experiência com banco de dados relacional."},
      {"kind":"OTHER","importance":"REQUIRED","value":"Disponibilidade para viagens","source_text":"Imprescindível ter disponibilidade para viagens."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Setor público","source_text":"Vivência em órgãos públicos ou consultoria para o setor público."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Auditoria de eSocial","source_text":"Experiência com auditorias relacionadas ao eSocial."}
    ]
  },
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"11929937","source_url":"https://techne.gupy.io/jobs/11929937?jobBoardSource=gupy_public_page","apply_url":"https://techne.gupy.io/jobs/11929937?jobBoardSource=gupy_public_page","company_name":"Techne","title":"Product Manager","location_text":"Trabalho Remoto","country_code":"BR","work_model":"REMOTE","contract_type":"CLT","description_raw":"Product Manager responsável pela evolução estratégica do Ergon, produto de RH, folha de pagamento e eSocial, conectando necessidades de clientes, requisitos regulatórios e objetivos de negócio. A vaga é CLT e remota.","status":"ACTIVE","requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Ensino superior em Sistemas de Informação ou áreas correlatas","required_education_status":"COMPLETED","source_text":"Ensino Superior Completo em Sistemas de Informação ou áreas correlatas."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Product Manager ou Product Owner Sênior em produtos digitais","source_text":"Experiência como Product Manager, Product Owner Sênior ou função equivalente em produtos digitais."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Roadmap de produto","source_text":"Experiência na construção, priorização e gestão de roadmaps de produto."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Gestão de backlog","source_text":"Experiência conduzindo gestão de backlog."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Product Discovery e validação de hipóteses","source_text":"Experiência em Discovery de Produtos e validação de hipóteses."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Métricas de produto e tomada de decisão por dados","source_text":"Experiência utilizando indicadores e métricas para tomada de decisão."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Metodologias ágeis","source_text":"Experiência em ambientes ágeis e conhecimento em metodologias ágeis."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Gestão de stakeholders","source_text":"Experiência trabalhando com múltiplos stakeholders."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Recursos Humanos, folha de pagamento ou gestão de pessoas","source_text":"Experiência com produtos de RH, Folha de Pagamento ou Gestão de Pessoas."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"B2B missão crítica","source_text":"Experiência em produtos B2B de missão crítica."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Ambientes regulados","source_text":"Vivência em ambientes regulados."}
    ]},
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"12066690","source_url":"https://pulsus.gupy.io/jobs/12066690?jobBoardSource=gupy_public_page","apply_url":"https://pulsus.gupy.io/jobs/12066690?jobBoardSource=gupy_public_page","company_name":"Pulsus","title":"Customer Success Manager: Inglês e Espanhol | Remoto | Brasil","location_text":"Brasil - Remoto","country_code":"BR","work_model":"REMOTE","description_raw":"Customer Success para carteira internacional em uma plataforma SaaS B2B de mobilidade/MDM, combinando gestão de clientes diretos e parceiros, expansão de receita, retenção, métricas SaaS e negociações executivas em inglês e espanhol.","status":"ACTIVE","requirements":[
      {"kind":"LANGUAGE","importance":"REQUIRED","value":"Inglês","required_language_proficiency":"ADVANCED","source_text":"Domínio avançado/fluente de Inglês."},
      {"kind":"LANGUAGE","importance":"REQUIRED","value":"Espanhol","required_language_proficiency":"ADVANCED","source_text":"Domínio avançado/fluente de Espanhol."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Customer Success e Account Management B2B enterprise/internacional","source_text":"Vivência sólida na gestão de contas B2B enterprise/internacionais com foco em expansão."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Gestão de canais e parceiros","source_text":"Experiência de atendimento e desenvolvimento de parceiros e revendas."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Negociação comercial B2B com C-Level","source_text":"Capacidade comprovada de negociar contratos e conduzir conversas de alto nível."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Métricas SaaS","source_text":"Domínio de Net MRR Expansion, MRR Churn, Logo Churn, NRR e LTV."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Apresentação de ROI","source_text":"Habilidade para transformar métricas em argumentos de valor financeiro e estratégico."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Gainsight, SenseData ou CustomerX","source_text":"Experiência com plataformas de Customer Success."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Salesforce, HubSpot ou Pipedrive","source_text":"Experiência com CRMs de Vendas."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"SaaS B2B, MDM ou Android Enterprise","source_text":"Conhecimento em SaaS B2B, MDM, Android Enterprise ou telecom/TI."}
    ]},
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"11673525","source_url":"https://pulsus.gupy.io/jobs/11673525?jobBoardSource=gupy_public_page","apply_url":"https://pulsus.gupy.io/jobs/11673525?jobBoardSource=gupy_public_page","company_name":"Pulsus","title":"Product Manager Sênior | Remoto | Brasil","location_text":"Brasil - Remoto","country_code":"BR","work_model":"REMOTE","seniority":"SENIOR","description_raw":"Product Manager Sênior de uma plataforma SaaS B2B/MDM, responsável por estratégia e roadmap, discovery, dados, requisitos, avaliação de riscos técnicos, go-to-market e acompanhamento de resultados em ambiente remote first.","status":"ACTIVE","requirements":[
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Product Manager em produtos SaaS","source_text":"Experiência sólida como Product Manager em produtos SaaS."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"SaaS B2B, MDM, ERP ou CRM","source_text":"Preferencialmente em ambientes B2B ou plataformas de gestão como MDM, ERP ou CRM."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Métricas, operações e estratégia de negócios","source_text":"Compreensão robusta sobre negócios, métricas, operações, mercado e estratégias."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Tradução de necessidades do cliente em requisitos de produto","source_text":"Traduzir necessidades dos clientes em requisitos claros e específicos de produto."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Discussão de riscos técnicos com Engenharia","source_text":"Capacidade de dominar e discutir riscos técnicos com o time de engenharia."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Análise de dados complexos","source_text":"Capacidade de instrumentar, coletar e extrair conclusões de dados complexos."},
      {"kind":"TOOL","importance":"REQUIRED","value":"Google Analytics, Mixpanel ou Amplitude","source_text":"Experiência com ferramentas de análise de experiência do usuário."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Inteligência Artificial e LLMs","source_text":"Experiência com tecnologias de inteligência artificial, LLMs e vibe coding."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Organização, documentação e comunicação remota","source_text":"Forte habilidade de organização, documentação e comunicação em ambiente 100% remoto."}
    ]},
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"12381605","source_url":"https://softexpert.gupy.io/jobs/12381605?jobBoardSource=gupy_public_page","apply_url":"https://softexpert.gupy.io/jobs/12381605?jobBoardSource=gupy_public_page","company_name":"SoftExpert","title":"Analista de Customer Success Júnior","location_text":"Joinville - SC","city":"Joinville","state":"SC","country_code":"BR","work_model":"HYBRID","seniority":"JUNIOR","description_raw":"Customer Success responsável por uma carteira de clientes da SoftExpert, acompanhando adoção, satisfação, retenção, renovações e oportunidades de expansão, além de relacionamento com stakeholders e times internos. A carreira oficial lista a vaga como híbrida em Joinville.","status":"ACTIVE","requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Ensino superior completo ou cursando","source_text":"Ensino superior completo ou cursando."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Customer Success com expansão de grandes contas","source_text":"Experiência em Customer Success, principalmente em expansão de grandes contas."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Métricas e modelos de Customer Success","source_text":"Sólida compreensão de métricas e modelos de atuação em Customer Success."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Comunicação e relacionamento interpessoal","source_text":"Fortes habilidades de comunicação e relacionamento interpessoal."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"B2B ou Life Science","source_text":"Experiência em empresas e relacionamento B2B ou segmento life science."},
      {"kind":"LANGUAGE","importance":"PREFERRED","value":"Espanhol","source_text":"Idioma espanhol."},
      {"kind":"TOOL","importance":"PREFERRED","value":"SoftExpert Suite","source_text":"Familiaridade com SoftExpert Suite."}
    ]},
  {
    "source_kind":"ATS","source_platform":"Lever","external_id":"18beddfd-b611-42ef-9adf-c7ec688ce7c2","source_url":"https://jobs.lever.co/flashapp/18beddfd-b611-42ef-9adf-c7ec688ce7c2","apply_url":"https://jobs.lever.co/flashapp/18beddfd-b611-42ef-9adf-c7ec688ce7c2/apply","company_name":"Flash","title":"Product Manager Especialista","location_text":"Remoto","country_code":"BR","work_model":"REMOTE","contract_type":"CLT","seniority":"SPECIALIST","description_raw":"Product Manager Especialista para a jornada de pagamentos e despesas corporativas, responsável por estratégia, roadmap, métricas, experimentação, IA, integrações e gestão de stakeholders em um produto financeiro B2B. Vaga CLT e remota.","status":"ACTIVE","requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Graduação em Administração, Engenharia, Economia, Ciência da Computação ou áreas correlatas","source_text":"Graduação em áreas correlatas."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Product Management","min_years":7,"context_qualifier":"inclui 3 a 5 anos como PM Sênior ou Especialista","source_text":"Mínimo de 7 a 10 anos como Product Manager, com 3 a 5 anos como Sênior ou Especialista."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Produtos de pagamentos, fintechs, despesas ou produtos financeiros B2B","min_years":3,"source_text":"Mínimo de 3 anos em produtos de pagamentos, fintechs, despesas ou produtos financeiros B2B."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Gestão de produtos com dependências externas","source_text":"Experiência com fornecedores, reguladores e integrações."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Pagamentos","source_text":"Conhecimento do ciclo de cartões, PIX, boleto e integrações."},
      {"kind":"TOOL","importance":"REQUIRED","value":"Metabase, Tableau ou Looker","source_text":"Experiência com dashboards e ferramentas de dados."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Testes A/B e experimentação","source_text":"Conhecimento em testes A/B, experimentação e validação de hipóteses."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"IA e automação aplicada a produtos","source_text":"Conhecimento prático em automação e IA aplicada a produtos."},
      {"kind":"LANGUAGE","importance":"REQUIRED","value":"Português","required_language_proficiency":"FLUENT","source_text":"Português fluente."},
      {"kind":"LANGUAGE","importance":"REQUIRED","value":"Inglês","required_language_proficiency":"INTERMEDIATE","source_text":"Inglês intermediário."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"LGPD, AML/KYC e regulação do Banco Central","source_text":"Conhecimento de regulação financeira é desejável."}
    ]},
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"12169152","source_url":"https://asaas.gupy.io/jobs/12169152?jobBoardSource=gupy_public_page","apply_url":"https://asaas.gupy.io/jobs/12169152?jobBoardSource=gupy_public_page","company_name":"Asaas","title":"Product Manager - Pague Contas (Cashout)","location_text":"Joinville - SC ou remoto no Brasil","country_code":"BR","work_model":"REMOTE","contract_type":"CLT","description_raw":"Product Manager para produtos financeiros de Cashout, DDA, coleta e liquidação, conectando visão estratégica, execução técnica, experimentação, dados e conformidade com normas do Banco Central. A empresa permite trabalho remoto para quem não reside em Joinville e a contratação é CLT.","status":"ACTIVE","requirements":[
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Product Manager","source_text":"Experiência consolidada como Product Manager, preferencialmente em fintechs ou bancos."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Pagamentos e core banking","source_text":"Profundo conhecimento em pagamentos e core banking: boletos, TED, SLC e DDA."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"SPB ou SPI","source_text":"Conhecimento de integração com SPB ou SPI."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Métricas de produto e análise de dados","source_text":"Familiaridade com métricas de produto, análise de dados e decisões orientadas por dados."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Comunicação verbal e escrita","source_text":"Excelentes habilidades de comunicação verbal e escrita."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"CNAB","source_text":"Familiaridade com arquivos CNAB de remessa e retorno."},
      {"kind":"TOOL","importance":"REQUIRED","value":"APIs","required_level":"ADVANCED","source_text":"Conhecimento avançado em APIs."},
      {"kind":"TOOL","importance":"PREFERRED","value":"SQL","source_text":"SQL é um diferencial."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"DDA e conciliação bancária","source_text":"Experiência com DDA, conciliação bancária e liquidação."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Ambiente regulado pelo Banco Central","source_text":"Histórico em ambiente regulado pelo Banco Central."}
    ]},
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"11552988","source_url":"https://bhs.gupy.io/jobs/11552988","apply_url":"https://bhs.gupy.io/jobs/11552988","company_name":"BHS","title":"Product Owner (Home Office)","location_text":"Home Office - Brasil","country_code":"BR","work_model":"REMOTE","description_raw":"Product Owner responsável pela evolução de produtos, atuando entre negócio, clientes e tecnologia, com gestão de backlog, planejamento de sprints, definição de valor, treinamento de clientes e garantia de qualidade do produto. A vaga é home office.","status":"ACTIVE","requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Graduação em áreas de Tecnologia ou correlatas","source_text":"Graduação em áreas de Tecnologia ou correlatas."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Scrum e Kanban","source_text":"Experiência com metodologias ágeis para desenvolvimento de produtos."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"SaaS B2B","source_text":"Atuações anteriores com Produto SaaS e B2B."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Criação de produtos digitais","source_text":"Experiência com criação de produtos digitais."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Priorização por valor para cliente e negócio","source_text":"Experiência na priorização de demandas com foco em geração de valor."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Inteligência Artificial","source_text":"Conhecimento e familiaridade com ferramentas de IA."},
      {"kind":"CERTIFICATION","importance":"PREFERRED","value":"Certificação em métodos ágeis","source_text":"Certificação nos métodos ágeis."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"Auditoria e Compliance","source_text":"Atuação com produtos ligados a Auditoria e Compliance."}
    ]},
  {
    "source_kind":"ATS","source_platform":"Gupy","external_id":"12381097","source_url":"https://uoledtech.gupy.io/jobs/12381097?jobBoardSource=gupy_public_page","apply_url":"https://uoledtech.gupy.io/jobs/12381097?jobBoardSource=gupy_public_page","company_name":"UOL EdTech","title":"Analista de Projetos Jr.","country_code":"BR","seniority":"JUNIOR","description_raw":"Analista de Projetos Júnior para conduzir implantação de produtos, acompanhar clientes, apresentar resultados, organizar informações no CRM e registrar necessidades como melhorias de produto, em contexto de educação e tecnologia.","status":"ACTIVE","requirements":[
      {"kind":"EDUCATION","importance":"REQUIRED","value":"Superior em Administração, Economia, Engenharia ou áreas correlatas","source_text":"Superior em Administração, Economia, Engenharia ou áreas correlatas."},
      {"kind":"SKILL","importance":"REQUIRED","value":"Gestão de projetos","source_text":"Conhecimento em conceitos de gestão de projetos."},
      {"kind":"DOMAIN","importance":"REQUIRED","value":"Gestão de desempenho","source_text":"Conhecimento em conceitos de gestão de desempenho."},
      {"kind":"EXPERIENCE","importance":"REQUIRED","value":"Implantação de software ou gestão de desempenho","source_text":"Experiência com projetos de implantação de software ou gestão de desempenho."},
      {"kind":"TOOL","importance":"REQUIRED","value":"Excel","required_level":"INTERMEDIATE","source_text":"Excel intermediário."},
      {"kind":"EXPERIENCE","importance":"PREFERRED","value":"Atendimento ao público de Recursos Humanos","source_text":"Experiência de atendimento com público de Recursos Humanos."},
      {"kind":"DOMAIN","importance":"PREFERRED","value":"OKRs e metas","source_text":"Experiência com metodologia OKRs/Metas."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Qulture.Rocks","source_text":"Experiência com a plataforma Qulture.Rocks."},
      {"kind":"TOOL","importance":"PREFERRED","value":"SQL","source_text":"Conhecimento em SQL."},
      {"kind":"TOOL","importance":"PREFERRED","value":"Power BI","source_text":"Conhecimento em Power BI."}
    ]}
];

async function sha256Hex(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function safeEqual(left: string, right: string): boolean {
  const maxLength = Math.max(left.length, right.length);
  let mismatch = left.length ^ right.length;
  for (let index = 0; index < maxLength; index += 1) mismatch |= (left.charCodeAt(index) || 0) ^ (right.charCodeAt(index) || 0);
  return mismatch === 0;
}

export const GET: RequestHandler = async ({ url }) => {
  const key = url.searchParams.get('key') ?? '';
  const keyHash = await sha256Hex(key);
  if (!safeEqual(keyHash, EXPECTED_KEY_SHA256)) return json({ detail: 'not found' }, { status: 404 });

  const origin = env.HIREIN_API_URL?.trim().replace(/\/$/, '');
  const backendToken = env.HIREIN_BACKEND_TOKEN?.trim();
  if (!origin || !backendToken) return json({ detail: 'pilot backend not configured' }, { status: 503 });

  const results: Array<Record<string, unknown>> = [];
  for (const job of jobs) {
    try {
      const response = await fetch(`${origin}/api/v1/jobs`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'x-hirein-pilot-token': backendToken },
        body: JSON.stringify(job),
        redirect: 'manual',
        signal: AbortSignal.timeout(20_000)
      });
      let body: unknown = null;
      try { body = await response.json(); } catch { body = await response.text(); }
      results.push({ external_id: job.external_id, company_name: job.company_name, title: job.title, status: response.status, body });
    } catch (error) {
      results.push({ external_id: job.external_id, company_name: job.company_name, title: job.title, status: 0, error: error instanceof Error ? error.message : 'unknown error' });
    }
  }

  const created = results.filter((result) => result.status === 201).length;
  const conflicts = results.filter((result) => result.status === 409).length;
  const failures = results.filter((result) => typeof result.status === 'number' && ![201, 409].includes(result.status as number)).length;

  return json({ holdout: 'Match v1.3 — Blind Holdout #2', attempted: jobs.length, created, conflicts, failures, match_queried: false, results }, { status: failures === 0 ? 200 : 207, headers: { 'cache-control': 'no-store' } });
};
