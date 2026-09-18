import { env } from '$env/dynamic/private';
import { json, type RequestHandler } from '@sveltejs/kit';

const EXPECTED_KEY_SHA256 = '50e12ce1a0faaf0872c564185e37cde36a189aa6bf1daf869aba9d2fbf0e3bf9';

const jobs = [
  { job_id: '9aafe2f9-41d9-4923-8aa9-148111be9cde', company_name: 'Gaudium', title: 'Analista de Implantação' },
  { job_id: '44529998-7492-4091-884c-4f10043756a9', company_name: 'Populos', title: 'Analista de Implementação ITSM Pleno' },
  { job_id: 'b842ddda-3d0a-427c-8ba2-96b9069b76ce', company_name: 'Grupo Autoglass', title: 'Analista de Projetos I - PMO' },
  { job_id: '5f1277ee-92b8-4d0d-b46b-9b59afce88bc', company_name: 'Neogrid', title: 'Product Manager Specialist I' },
  { job_id: '6d7fd341-4fbe-440c-9994-ed9597b95c69', company_name: 'NEXDOM Healthtech', title: 'Consultor de Implantação e Negócios Júnior' }
] as const;

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
  for (const job of jobs) {
    const response = await fetch(`${apiUrl}/api/v1/jobs/${job.job_id}/match`, {
      headers: { 'x-hirein-pilot-token': backendToken },
      signal: AbortSignal.timeout(20_000)
    });
    const payload = await response.json().catch(() => null);
    results.push({ ...job, status: response.status, match: payload });
  }

  return json(
    {
      experiment: 'Match v1.7 — Holdout #4 regression',
      blind_validation: false,
      results
    },
    { headers: { 'cache-control': 'no-store' } }
  );
};
