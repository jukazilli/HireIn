# HireIn — Engineering Guardrails for Coding Agents

Before changing code in this repository, read:

1. `README.md`
2. `docs/03-ARCHITECTURE.md`
3. `docs/04-ENGINEERING.md`
4. `docs/07-PRIVACY-SECURITY-LGPD.md`
5. `docs/09-IMPLEMENTATION-PLAN.md`
6. `docs/16-VISUAL-DIRECTION.md` for any frontend, UI, UX, copy, imagery or interaction work
7. `docs/18-PRIVATE-CLOUD-PILOT.md` for pilot hosting/security work
8. `docs/adr/README.md`
9. any ADR related to the task

## Product phase

HireIn is currently a **single-user private cloud pilot**.

Do not prematurely turn it into a public SaaS.

The first implementation exists to prove:

```text
candidate profile
→ real job
→ normalized requirements
→ explainable match
→ application draft
→ human review
```

## Architecture constraints

Current accepted direction:

- Web: SvelteKit + TypeScript
- Core API: Python + FastAPI
- Database: PostgreSQL + pgvector
- ORM/migrations: SQLAlchemy 2 + Alembic
- Browser automation later: Playwright Python
- Pilot job queue: PostgreSQL
- Pilot execution: private cloud, single-user
- Browser/API boundary: same-origin SvelteKit proxy
- API contracts: OpenAPI → generated TypeScript client

The active runtime decision is ADR-0009. ADR-0005 is historical/superseded.

Do not replace an accepted architectural decision without an ADR and concrete evidence.

## Architecture style

Start as a modular monolith.

Prefer domain boundaries such as:

```text
profile
jobs
matching
applications
documents
ai
ats
audit
shared
```

Domain code must not depend directly on:

- LLM SDKs;
- Playwright;
- Neon-specific SDKs;
- hosting-provider-specific SDKs;
- ATS-specific implementations.

Use ports/adapters at external boundaries.

## AI rules

There is intentionally no final default LLM or embedding model yet.

Do not choose one just because it is familiar or easy to integrate.

Any real selection must be based on evals for the HireIn workload, especially PT-BR.

AI-generated or inferred information is not automatically a professional fact.

Never fabricate:

- work experience;
- education;
- certifications;
- languages;
- tools;
- salaries;
- availability;
- achievements;
- personal conditions.

Structured output is preferred whenever AI feeds domain logic.

## Privacy and data

Never commit real user data.

Do not version:

- real resumes;
- CPF;
- phone numbers;
- personal addresses;
- cookies;
- browser sessions;
- passwords;
- tokens;
- `.env` files;
- authenticated page HTML;
- real ATS credentials;
- database connection strings.

Use synthetic fixtures in Git and CI.

Real pilot data belongs only in the private pilot datastore (currently managed PostgreSQL) or in explicitly ignored private storage. It must never be copied into fixtures, PR descriptions, CI artifacts or source files.

The browser must never receive database credentials or the backend-to-backend token.

Logs must avoid unnecessary PII and secrets.

## Private cloud pilot security

For the single-user cloud pilot:

- SvelteKit owns the user-facing login gate;
- the session cookie must be `HttpOnly`, `Secure` outside dev and `SameSite=Strict`;
- browser requests use the same-origin `/api/v1/*` proxy;
- SvelteKit injects the server-only backend token;
- FastAPI protects `/api/v1/*` when `PILOT_BACKEND_TOKEN` is configured;
- health endpoints may remain unauthenticated for provider health checks;
- missing production auth configuration must fail closed;
- secrets must be stored in provider secret/environment stores, never in Git.

This is not the final multi-user authentication design. Do not add registration, tenants or user tables merely because the pilot moved to cloud.

## Automation safety

No unrestricted Auto Apply in the first implementation.

Do not implement:

- CAPTCHA bypass;
- fingerprint spoofing;
- stealth patches intended to bypass platform protections;
- proxy rotation intended to evade platform limits;
- mass submission designed to defeat controls.

If automation reaches an unknown required field, CAPTCHA, blocked state, expired authentication or uncertain submit result, stop and request human intervention.

Never automatically retry an uncertain submission.

## Visual/UI guardrails

For any frontend, UI, UX, interaction, copy or imagery task, `docs/16-VISUAL-DIRECTION.md` is normative.

The primary visual objective is to avoid generic AI-generated SaaS UI.

Do not produce a screen from a generic dashboard template and recolor it purple.

Do not default to:

- KPI grids at the top of every page;
- bento layouts without a product reason;
- glassmorphism;
- decorative gradient blobs;
- purple/blue gradients used as universal emphasis;
- excessive cards, pills, shadows or rounded containers;
- sparkles, robots, brains or emojis as shorthand for AI;
- generic startup copy such as “Potencialize”, “Revolucione”, “Desbloqueie seu potencial” or “Transforme sua jornada”;
- `Inter` as the HireIn brand typeface;
- a copy of Tinder's visual language.

The product direction is:

- Satoshi for display/headings;
- General Sans for body/UI;
- `#6366F1` as primary brand indigo;
- `#A3E635` as a restrained lime accent;
- neutral/light surfaces as the majority of the UI;
- mobile-first composition;
- semantic HireIn components such as `OpportunityCard`, `MatchEvidence` and `GapMarker` rather than generic decorative cards;
- Tinder only as a reference for discovery behavior, fast decisions and optional swipe gestures;
- specific, natural Brazilian Portuguese copy;
- visual hierarchy driven by the user's current task.

Every meaningful UI change should pass the anti-generic checklist in `docs/16-VISUAL-DIRECTION.md` before merge.

A screen that compiles but could belong to any SaaS is not finished.

## Dependency policy

Do not add a dependency only to save a few lines of code.

Before adding one, consider:

- maintenance;
- license;
- security surface;
- package size/impact;
- removal difficulty;
- whether the platform already solves the problem.

Do not introduce Redis, RabbitMQ, Kafka, Elasticsearch, a dedicated vector database, Kubernetes or additional cloud services without a demonstrated need and an ADR.

## Testing priorities

Prioritize tests around risk:

- blockers;
- match rules;
- state transitions;
- provenance;
- idempotency;
- deduplication;
- structured AI outputs;
- migration correctness;
- API contracts;
- authentication/proxy boundaries;
- remote pilot smoke flow with synthetic data.

External ATS websites must not be required for normal CI.

## First-slice scope

Implement in this order unless the task explicitly says otherwise:

1. bootstrap;
2. Candidate Core;
3. Job Core;
4. deterministic Match v0;
5. pilot evaluation dataset tooling;
6. private cloud pilot runtime;
7. controlled AI tasks;
8. Application Draft.

Do not build the extension or browser agent before the matching/application-draft slice is validated.

## Definition of responsible change

A change is not complete merely because it runs once.

For critical flows, ensure:

- domain rule is explicit;
- failure states are handled;
- tests cover relevant risk;
- sensitive data is not leaked;
- contracts remain consistent;
- migrations are reproducible;
- cost impact is known for external AI;
- documentation/ADR is updated when architectural behavior changes;
- frontend changes respect the visual contract and avoid generic UI patterns.
