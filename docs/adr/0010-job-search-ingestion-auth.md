# ADR 0010 — Dedicated authentication for job-search ingestion

## Status

Accepted for the private pilot.

## Context

The private web application and FastAPI currently share one backend token. Automated or agent-driven job discovery must be able to create job postings without receiving that broader pilot credential and without direct database access.

## Decision

Introduce a separate server-to-server credential for automated job ingestion.

- Secret environment variable: `HIREIN_JOB_INGESTION_TOKEN`.
- Request header: `X-HireIn-Ingestion-Token`.
- Authorized operation: only `POST /api/v1/jobs`.
- All read, update, profile, evaluation and Match endpoints remain unavailable to this credential.
- When the ingestion token is not configured, the alternate authentication path is disabled.
- The existing pilot backend token remains unchanged.

## Consequences

Search providers and research agents can publish normalized jobs through the same Job Core API used by the application, while keeping candidate/profile data and Match results inaccessible to the ingestion worker. This also preserves blind evaluation: discovery can insert a holdout set without being able to query Match scores.
