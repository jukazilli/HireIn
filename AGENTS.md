# HireIn — Engineering Guardrails for Coding Agents

Before changing code in this repository, read:

1. `README.md`
2. `docs/03-ARCHITECTURE.md`
3. `docs/04-ENGINEERING.md`
4. `docs/07-PRIVACY-SECURITY-LGPD.md`
5. `docs/09-IMPLEMENTATION-PLAN.md`
6. `docs/adr/README.md`
7. any ADR related to the task

## Product phase

HireIn is currently a **single-user local-first pilot**.

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
- Pilot execution: local-first
- API contracts: OpenAPI → generated TypeScript client

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
- Cloudflare-specific SDKs;
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
- real ATS credentials.

Use synthetic fixtures in Git.

Real pilot data belongs in ignored local storage such as `.local-data/`.

Logs must avoid unnecessary PII and secrets.

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
- API contracts.

External ATS websites must not be required for normal CI.

## First-slice scope

Implement in this order unless the task explicitly says otherwise:

1. bootstrap;
2. Candidate Core;
3. Job Core;
4. deterministic Match v0;
5. local evaluation dataset tooling;
6. controlled AI tasks;
7. Application Draft.

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
- documentation/ADR is updated when architectural behavior changes.
