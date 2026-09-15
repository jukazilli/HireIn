import { dev } from '$app/environment';
import { env } from '$env/dynamic/private';
import { json, type RequestHandler } from '@sveltejs/kit';

const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailers',
  'transfer-encoding',
  'upgrade'
]);

const BODY_METADATA_HEADERS = new Set(['content-encoding', 'content-length']);

function apiOrigin(): string | null {
  const configured = env.HIREIN_API_URL?.trim();
  if (configured) return configured.replace(/\/$/, '');
  if (dev) return 'http://127.0.0.1:8000';
  return null;
}

function responseHeaders(upstream: Response): Headers {
  const headers = new Headers();
  upstream.headers.forEach((value, key) => {
    const normalizedKey = key.toLowerCase();
    if (
      !HOP_BY_HOP_HEADERS.has(normalizedKey) &&
      !BODY_METADATA_HEADERS.has(normalizedKey) &&
      normalizedKey !== 'set-cookie'
    ) {
      headers.set(key, value);
    }
  });
  return headers;
}

const proxy: RequestHandler = async ({ params, request, url }) => {
  const origin = apiOrigin();
  if (!origin) {
    return json({ detail: 'Backend do piloto não configurado.' }, { status: 503 });
  }

  const target = new URL(`${origin}/api/v1/${params.path ?? ''}`);
  target.search = url.search;

  const headers = new Headers();
  const contentType = request.headers.get('content-type');
  const accept = request.headers.get('accept');
  if (contentType) headers.set('content-type', contentType);
  if (accept) headers.set('accept', accept);

  const backendToken = env.HIREIN_BACKEND_TOKEN?.trim();
  if (backendToken) headers.set('x-hirein-pilot-token', backendToken);

  const method = request.method.toUpperCase();
  const body = method === 'GET' || method === 'HEAD' ? undefined : await request.arrayBuffer();

  try {
    const upstream = await fetch(target, {
      method,
      headers,
      body,
      redirect: 'manual',
      signal: AbortSignal.timeout(20_000)
    });

    const responseBody =
      method === 'HEAD' || upstream.status === 204 || upstream.status === 304
        ? null
        : await upstream.arrayBuffer();

    return new Response(responseBody, {
      status: upstream.status,
      headers: responseHeaders(upstream)
    });
  } catch {
    return json({ detail: 'Backend do piloto indisponível.' }, { status: 502 });
  }
};

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
