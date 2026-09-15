# HireIn — Private Cloud Pilot

> Status: planned implementation for the single-user pilot.

## Decision

The pilot no longer depends on running Docker, PostgreSQL, Python or Node on the candidate's computer.

The new P0 operating model is:

```text
browser
  ↓ HTTPS
SvelteKit / Vercel
  ↓ same-origin private API proxy
FastAPI / managed runtime
  ↓ TLS
Neon PostgreSQL / São Paulo
```

This is still a **single-user pilot**, not a public SaaS.

The architectural reason for the change is operational: the pilot machine has insufficient local storage. The product should adapt to that real constraint instead of forcing a local runtime that makes validation harder.

## Security boundary

The browser must never receive:

- the Neon connection string;
- the backend-to-backend token;
- the private FastAPI origin as a credential;
- database credentials;
- provider API keys.

The browser talks only to the SvelteKit origin.

SvelteKit is responsible for:

1. authenticating the single pilot user;
2. keeping the session in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie;
3. proxying `/api/v1/*` to FastAPI;
4. injecting the server-only backend token.

FastAPI accepts protected `/api/v1/*` requests only when the configured backend token is present. Health endpoints remain independent so the hosting provider can probe the service.

## Environments

### Production pilot

Real private pilot data:

- Candidate Profile;
- real vacancies;
- Match results derived from the profile/vacancies;
- human relevance labels;
- pilot evaluation report.

### CI

Synthetic data only. PostgreSQL ephemeral.

### Visual demo

Synthetic preview is not a security boundary and must not silently activate based only on hostname. Demo mode, if retained, must be explicitly enabled by configuration.

## Secrets

Expected server-only variables on the web host:

```text
HIREIN_API_URL
HIREIN_BACKEND_TOKEN
PILOT_ACCESS_PASSWORD
PILOT_SESSION_TOKEN
```

Expected server-only variables on the FastAPI host:

```text
DATABASE_URL
APP_ENV=pilot
LOG_LEVEL=INFO
PILOT_BACKEND_TOKEN
```

No real secret belongs in Git.

## Database

The pilot database is Neon PostgreSQL in the São Paulo region.

Schema evolution remains owned by Alembic. The backend deployment runs migrations before starting the API.

The database is not accessed directly from the browser.

## Authentication scope

This is deliberately **single-user pilot authentication**, not the final multi-user identity architecture.

It is sufficient for the current validation gate because:

- only one candidate uses the environment;
- no third-party beta exists yet;
- there is no account registration;
- there is no tenant isolation requirement yet.

Before opening HireIn to another person, authentication/authorization must receive its own ADR and privacy/security gate.

## Backend hosting

FastAPI remains Python/FastAPI. We do not rewrite domain logic to TypeScript merely to fit a hosting provider.

The hosting target must support:

- Python 3.13;
- long-lived HTTP service or equivalent managed web service;
- environment secrets;
- health checks;
- deploy from the GitHub repository;
- execution of Alembic migrations;
- outbound TLS access to Neon.

Browser automation/Playwright is explicitly not part of this runtime yet and may receive a separate worker later.

## Validation gate

The private cloud pilot is considered operational only when all of the following pass:

```text
login
  ↓
Candidate Profile write/read
  ↓
create real-shaped synthetic job
  ↓
Match
  ↓
human review
  ↓
evaluation report
```

The remote smoke test must use synthetic data. Real candidate data is entered only by the pilot user after the environment is proven healthy.

## Cost rule

Continue targeting the free/near-zero tier. A paid service should only be introduced after the free option proves insufficient for the pilot workload.
