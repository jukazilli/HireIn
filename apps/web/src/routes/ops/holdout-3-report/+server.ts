import { createHash } from 'node:crypto';
import { env } from '$env/dynamic/private';
import { json, type RequestHandler } from '@sveltejs/kit';

const ACCESS_HASH = 'c8d33a747221b593cc47ef6520dba2b48faba7ab40e0d50aae82b585cb3f7f37';

const JOB_IDS = [
  'd2c7fb83-fd83-4062-acf7-565db348d51b',
  '0c786fc6-1ef8-43dd-938d-b56632617f68',
  '1a28bddc-781b-4128-b8a8-4cb4029ba20a',
  'cefb282e-e53e-4799-b464-918feea52994',
  '0b740393-8b41-4623-8df5-359451d62e7a',
  '8093dcbe-2f7e-4fda-957e-be81c02e4edf',
  'd89d97d8-c066-4cd2-9745-df2d1b31ae64',
  '8789b930-035a-4829-99a1-7ab47cba2811',
  '4a6dcf03-ff27-4f95-a99e-f8589153d656',
  '3f16bb02-bb28-4ee1-9b88-e3c47a8cca75'
] as const;

function validAccess(value: string | null): boolean {
  if (!value) return false;
  return createHash('sha256').update(value).digest('hex') === ACCESS_HASH;
}

export const GET: RequestHandler = async ({ url, fetch }) => {
  if (!validAccess(url.searchParams.get('key'))) {
    return json({ detail: 'Not found.' }, { status: 404 });
  }

  const origin = env.HIREIN_API_URL?.trim().replace(/\/$/, '');
  const backendToken = env.HIREIN_BACKEND_TOKEN?.trim();
  if (!origin || !backendToken) {
    return json({ detail: 'Backend unavailable.' }, { status: 503 });
  }

  const results = [];
  for (const jobId of JOB_IDS) {
    const response = await fetch(`${origin}/api/v1/jobs/${jobId}/match`, {
      headers: { 'x-hirein-pilot-token': backendToken }
    });
    if (!response.ok) {
      return json({ detail: `Match failed for ${jobId}`, status: response.status }, { status: 502 });
    }
    results.push(await response.json());
  }

  return json({ experiment: 'Match v1.4 — Blind Holdout #3', count: results.length, matches: results });
};
