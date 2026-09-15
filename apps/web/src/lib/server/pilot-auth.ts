import { dev } from '$app/environment';
import { env } from '$env/dynamic/private';
import type { Cookies } from '@sveltejs/kit';
import { timingSafeEqual } from 'node:crypto';

export const PILOT_SESSION_COOKIE = 'hirein_pilot_session';
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

function safeEqual(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  if (leftBuffer.length !== rightBuffer.length) return false;
  return timingSafeEqual(leftBuffer, rightBuffer);
}

export function pilotAuthConfigured(): boolean {
  return Boolean(env.PILOT_ACCESS_PASSWORD && env.PILOT_SESSION_TOKEN);
}

export function pilotAuthRequired(): boolean {
  return !dev;
}

export function verifyPilotPassword(candidate: string): boolean {
  const configured = env.PILOT_ACCESS_PASSWORD;
  return Boolean(configured && candidate && safeEqual(candidate, configured));
}

export function validPilotSession(cookies: Cookies): boolean {
  if (!pilotAuthConfigured()) return !pilotAuthRequired();
  const session = cookies.get(PILOT_SESSION_COOKIE);
  const configured = env.PILOT_SESSION_TOKEN;
  return Boolean(session && configured && safeEqual(session, configured));
}

export function createPilotSession(cookies: Cookies): void {
  const configured = env.PILOT_SESSION_TOKEN;
  if (!configured) throw new Error('PILOT_SESSION_TOKEN is not configured');

  cookies.set(PILOT_SESSION_COOKIE, configured, {
    path: '/',
    httpOnly: true,
    secure: !dev,
    sameSite: 'strict',
    maxAge: SESSION_MAX_AGE_SECONDS
  });
}

export function clearPilotSession(cookies: Cookies): void {
  cookies.delete(PILOT_SESSION_COOKIE, { path: '/' });
}
