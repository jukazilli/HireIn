import { env } from '$env/dynamic/private';
import { json, type RequestHandler } from '@sveltejs/kit';

const EXPECTED_KEY_SHA256 = '3af6903fc933449f47bcc2db6f43f9512cf202e7666b5ab69e33be9eb614c9ff';

const jobs = [
  {
    source_kind: 'ATS',
    source_platform: 'Gupy',
    external_id: '11967469',
    source_url: 'https://vempranexdom.gupy.io/jobs/11967469?jobBoardSource=gupy_public_page',
    apply_url: 'https://vempranexdom.gupy.io/jobs/11967469?jobBoardSource=gupy_public_page',
    company_name: 'NEXDOM Healthtech',
    title: 'Consultor de Implantação e Negócios Júnior',
    location_text: 'Brasil · Remote first',
    country_code: 'BR',
    work_model: 'REMOTE',
    seniority: 'JUNIOR',
    description_raw:
      'Consultoria de implantação de ERP para operadoras de planos de saúde, com treinamentos, validações, homologações, análise de impacto, documentação, melhoria de processos e atuação direta com clientes durante o ciclo de implantação.',
    status: 'ACTIVE',
    requirements: [
      {
        kind: 'EXPERIENCE',
        importance: 'REQUIRED',
        value: 'Consultoria e implantação de projetos em clientes',
        source_text: 'Experiência sólida como consultor de implantação e experiência prática com implantação de projetos em clientes.'
      },
      {
        kind: 'DOMAIN',
        importance: 'REQUIRED',
        value: 'Processos operacionais de operadoras de planos de saúde',
        source_text: 'Conhecimento de processos operacionais de operadoras e regras de negócios.'
      },
      {
        kind: 'SKILL',
        importance: 'REQUIRED',
        value: 'Metodologias de implantação de projetos',
        source_text: 'Vivência em metodologias de implantação de projetos.'
      },
      {
        kind: 'SKILL',
        importance: 'REQUIRED',
        value: 'Treinamentos, testes funcionais, unitários e integrados',
        source_text: 'Conhecimento de metodologia de implantação, treinamentos, testes funcionais, unitários e integrados.'
      },
      {
        kind: 'SKILL',
        importance: 'REQUIRED',
        value: 'Documentação e desenho de processos',
        source_text: 'Experiência com testes e em documentação e desenho de processos.'
      },
      {
        kind: 'SKILL',
        importance: 'REQUIRED',
        value: 'Comunicação, autonomia e influência técnica',
        source_text: 'Boa comunicação, autonomia e capacidade de influência técnica.'
      },
      {
        kind: 'TOOL',
        importance: 'PREFERRED',
        value: 'Sistema Unimed',
        source_text: 'Conhecimento no sistema Unimed será um diferencial.'
      },
      {
        kind: 'TOOL',
        importance: 'PREFERRED',
        value: 'SGU',
        source_text: 'Conhecimento em sistemas SGU será um diferencial.'
      }
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
      holdout: 'Match v1.5 — Blind Holdout #4 replacement',
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
