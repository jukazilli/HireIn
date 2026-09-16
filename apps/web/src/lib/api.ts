import type { components } from '../../../../packages/generated-client/src/schema';

const API_BASE = '/api/v1';
const COLD_START_RETRY_DELAYS_MS = [1500, 3000] as const;
const BACKEND_UNAVAILABLE_DETAIL = 'Backend do piloto indisponível.';

type Schemas = components['schemas'];

export type CandidateProfile = Schemas['CandidateProfileResponse'];
export type CandidateProfileUpsert = Schemas['CandidateProfileUpsert'];
export type JobPosting = Schemas['JobPostingResponse'];
export type JobPostingUpsert = Schemas['JobPostingUpsert'];
export type JobSummary = Schemas['JobSummaryResponse'];
export type JobMatch = Schemas['JobMatchResponse'];
export type PilotReviewJob = Schemas['PilotReviewJobResponse'];
export type PilotEvaluation = Schemas['PilotEvaluationResponse'];
export type PilotEvaluationUpsert = Schemas['PilotEvaluationUpsert'];
export type PilotEvalReport = Schemas['PilotEvalReportResponse'];
export type EvaluationErrorCategory = Schemas['EvaluationErrorCategory'];
export type WorkModel = Schemas['WorkModel'];
export type ContractType = Schemas['ContractType'];
export type Seniority = Schemas['Seniority'];
export type EducationStatus = Schemas['EducationStatus'];
export type LanguageProficiency = Schemas['LanguageProficiency'];
export type JobSourceKind = Schemas['JobSourceKind'];
export type JobStatus = Schemas['JobStatus'];
export type SalaryPeriod = Schemas['SalaryPeriod'];
export type RequirementKind = Schemas['RequirementKind'];
export type RequirementImportance = Schemas['RequirementImportance'];
export type FactKind = Schemas['FactKind'];

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly detail: unknown = null
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function errorMessage(body: unknown, status: number) {
  if (
    typeof body === 'object' &&
    body !== null &&
    'detail' in body &&
    typeof body.detail === 'string'
  ) {
    return body.detail;
  }
  return `A API respondeu com status ${status}.`;
}

function isReadRequest(init?: RequestInit): boolean {
  const method = (init?.method ?? 'GET').toUpperCase();
  return method === 'GET' || method === 'HEAD';
}

function isColdStartResponse(status: number, body: unknown): boolean {
  return (
    status === 502 &&
    typeof body === 'object' &&
    body !== null &&
    'detail' in body &&
    body.detail === BACKEND_UNAVAILABLE_DETAIL
  );
}

function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function fetchApi(path: string, init?: RequestInit): Promise<Response> {
  const retryDelays = isReadRequest(init) ? COLD_START_RETRY_DELAYS_MS : [];

  for (let attempt = 0; ; attempt += 1) {
    const response = await fetch(`${API_BASE}${path}`, init);

    if (attempt >= retryDelays.length || response.status !== 502) {
      return response;
    }

    const body = await response.clone().json().catch(() => null);
    if (!isColdStartResponse(response.status, body)) {
      return response;
    }

    await sleep(retryDelays[attempt]);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetchApi(path, init);

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(errorMessage(body, response.status), response.status, body);
  }

  return (await response.json()) as T;
}

async function requestOptional<T>(path: string): Promise<T | null> {
  const response = await fetchApi(path);
  if (response.status === 404) return null;

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(errorMessage(body, response.status), response.status, body);
  }

  return (await response.json()) as T;
}

const jsonRequest = (method: 'POST' | 'PUT', body: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body)
});

export const api = {
  getProfile: () => requestOptional<CandidateProfile>('/profile'),
  upsertProfile: (payload: CandidateProfileUpsert) =>
    request<CandidateProfile>('/profile', jsonRequest('PUT', payload)),

  listJobs: () => request<JobSummary[]>('/jobs'),
  createJob: (payload: JobPostingUpsert) =>
    request<JobPosting>('/jobs', jsonRequest('POST', payload)),
  getJob: (jobId: string) => request<JobPosting>(`/jobs/${jobId}`),
  replaceJob: (jobId: string, payload: JobPostingUpsert) =>
    request<JobPosting>(`/jobs/${jobId}`, jsonRequest('PUT', payload)),
  getJobMatch: (jobId: string) => request<JobMatch>(`/jobs/${jobId}/match`),

  listReviewJobs: () => request<PilotReviewJob[]>('/evals/jobs'),
  upsertEvaluation: (jobId: string, payload: PilotEvaluationUpsert) =>
    request<PilotEvaluation>(`/evals/jobs/${jobId}`, jsonRequest('PUT', payload)),
  getEvalReport: () => requestOptional<PilotEvalReport>('/evals/report')
};
