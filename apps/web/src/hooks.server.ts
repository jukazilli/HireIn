import { dev } from '$app/environment';
import { redirect, type Handle } from '@sveltejs/kit';

import { pilotAuthConfigured, validPilotSession } from '$lib/server/pilot-auth';

const PUBLIC_PATHS = new Set(['/login', '/ops/holdout-4-run']);

export const handle: Handle = async ({ event, resolve }) => {
  const path = event.url.pathname;

  if (PUBLIC_PATHS.has(path) || path.startsWith('/_app/')) {
    return resolve(event);
  }

  if (!pilotAuthConfigured()) {
    if (dev) return resolve(event);
    return new Response('HireIn pilot authentication is not configured.', { status: 503 });
  }

  if (!validPilotSession(event.cookies)) {
    const next = `${event.url.pathname}${event.url.search}`;
    redirect(303, `/login?next=${encodeURIComponent(next)}`);
  }

  return resolve(event);
};
