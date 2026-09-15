# ADR 0009 — Private cloud single-user pilot

- Status: Accepted
- Date: 2026-09-14

## Context

ADR 0005 selected a local-first pilot to minimize cost and keep personal data on the pilot machine. The real pilot machine now has insufficient free storage for Docker/PostgreSQL and the local toolchain, which makes that operating model a blocker to validation.

The product goal has not changed: validate one candidate, 5 jobs first, then 30–50 human-labeled Brazilian jobs before choosing more AI or automation.

## Decision

For the individual pilot, use a private cloud runtime:

- SvelteKit on Vercel;
- FastAPI as a managed Python web service;
- Neon PostgreSQL in São Paulo;
- single-user password gate in SvelteKit;
- HttpOnly server session cookie;
- same-origin SvelteKit API proxy;
- independent backend-to-backend token protecting FastAPI;
- no direct database or protected backend credentials in the browser.

The domain architecture remains unchanged. This is an operational deployment decision, not a rewrite of the core.

## Consequences

### Positive

- no local Docker/PostgreSQL/Node/Python installation is required for the pilot user;
- the pilot can be used from a normal browser;
- database state survives the user's local-machine limitations;
- backend and database remain independently replaceable;
- the browser receives no database secret.

### Negative

- real candidate data now leaves the local machine and is processed by cloud subprocessors;
- secrets and authentication become mandatory before real data is entered;
- provider availability becomes part of the pilot runtime;
- privacy documentation must reflect the cloud processing boundary.

## Scope limitation

This password gate is not the final HireIn authentication architecture. It is authorized only for the single-user pilot.

Opening access to another candidate requires a new authentication/authorization decision and the private-beta LGPD/security gate.

## Relationship to ADR 0005

ADR 0005 remains historically valid for why local-first was originally chosen. This ADR supersedes its runtime choice for the active pilot because a concrete operational constraint invalidated the local assumption.
