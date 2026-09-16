# Job Search Ingestion

## Purpose

The HireIn pilot can ingest job postings discovered by an external search process without exposing the private pilot credential used by the web frontend.

The ingestion path is intentionally narrow:

- endpoint: `POST /api/v1/jobs`;
- header: `X-HireIn-Ingestion-Token`;
- backend environment variable: `HIREIN_JOB_INGESTION_TOKEN`;
- the ingestion credential cannot read jobs, update jobs, access candidate data, access evaluations, or request Match results;
- the existing `X-HireIn-Pilot-Token` remains valid for the private web application and keeps its current behavior.

## Search-to-job flow

```text
Search provider / research agent
        ↓
Collect original job posting
        ↓
Normalize source metadata + explicit requirements
        ↓
POST /api/v1/jobs
        ↓
HireIn Job Core
        ↓
Human blind review
        ↓
Match reveal only after review
```

The search process must not use the candidate's Match score to decide which holdout jobs are inserted. For blind evaluation sets, the search sample should contain a mix of plausible and less-compatible jobs so the matcher is tested for both ranking quality and false positives.

## Normalization rules

Keep `description_raw` faithful to the source. Structured requirements may only represent requirements that are supported by the original posting. Do not infer language proficiency, education status, skill level, years of experience, work model, contract type, location, or domain qualifiers unless the source explicitly supports them.

Use the most specific source kind available (`ATS`, `JOB_BOARD`, or `COMPANY_SITE`) and preserve the original source/apply URLs and external job identifier when available. Duplicate source identities are rejected by the API.

## Security

The ingestion token is a server-to-server credential. It must be stored only in a secret/environment variable and never committed to the repository or exposed to the browser. When `HIREIN_JOB_INGESTION_TOKEN` is not configured, ingestion-token authentication is closed by default.
