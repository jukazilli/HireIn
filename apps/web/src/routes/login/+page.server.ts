import { fail, redirect, type Actions, type PageServerLoad } from '@sveltejs/kit';

import {
  createPilotSession,
  pilotAuthConfigured,
  validPilotSession,
  verifyPilotPassword
} from '$lib/server/pilot-auth';

function safeNext(value: string | null): string {
  if (!value || !value.startsWith('/') || value.startsWith('//')) return '/pilot';
  return value;
}

export const load: PageServerLoad = async ({ cookies, url }) => {
  if (validPilotSession(cookies)) redirect(303, safeNext(url.searchParams.get('next')));
  return { configured: pilotAuthConfigured() };
};

export const actions: Actions = {
  default: async ({ cookies, request, url }) => {
    if (!pilotAuthConfigured()) {
      return fail(503, { message: 'O acesso privado do piloto ainda não foi configurado.' });
    }

    const data = await request.formData();
    const password = String(data.get('password') ?? '');
    if (!verifyPilotPassword(password)) {
      return fail(400, { message: 'Senha incorreta.' });
    }

    createPilotSession(cookies);
    redirect(303, safeNext(url.searchParams.get('next')));
  }
};
