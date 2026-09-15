import { redirect, type RequestHandler } from '@sveltejs/kit';

import { clearPilotSession } from '$lib/server/pilot-auth';

export const POST: RequestHandler = async ({ cookies }) => {
  clearPilotSession(cookies);
  redirect(303, '/login');
};
