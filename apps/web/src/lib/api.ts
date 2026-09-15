import type { components } from '../../../../packages/generated-client/src/schema';

const API_BASE = '/api/v1';

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(errorMessage(body, response.status), response.status, body);
  }

  return (await response.json()) as T;
}

async function requestOptional<T>(path: string): Promise<T | null> {
  const response = await fetch(`${API_BASE}${path}`);
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
