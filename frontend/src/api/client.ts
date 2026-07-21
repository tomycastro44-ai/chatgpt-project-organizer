export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
}

export interface DemoSummary {
  dataset_id: string;
  chats: number;
  projects: number;
  proposals: number;
  safe_proposals: number;
  exceptions: number;
  acceptance_cases: number;
  source_files: number;
  originals_immutable: boolean;
}

export interface SourceFileResult {
  id: string;
  original_name: string;
  format: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  status: string;
  chat_count: number;
  message_count: number;
  error_count: number;
}

export interface ImportIssue {
  id: string;
  source_file_id: string | null;
  scope: string;
  code: string;
  severity: string;
  message: string;
  record_reference: string | null;
}

export interface ImportBatch {
  id: string;
  source_kind: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  total_files: number;
  accepted_files: number;
  rejected_files: number;
  imported_chats: number;
  imported_messages: number;
  issue_count: number;
  source_files: SourceFileResult[];
  issues: ImportIssue[];
  originals_immutable: boolean;
}

export interface AnalysisEvidence {
  id: string;
  kind: string;
  quote: string;
  precedence: number;
  occurred_at: string | null;
  chat_external_id: string;
  message_external_id: string | null;
}

export interface AnalysisFinding {
  id: string;
  stable_key: string;
  finding_type: string;
  subject: string;
  classification: string | null;
  confidence: "ALTA" | "MEDIA" | "BAJA";
  chat_external_id: string | null;
  related_chat_external_id: string | null;
  details: Record<string, unknown>;
  evidences: AnalysisEvidence[];
}

export interface AnalysisRunSummary {
  id: string;
  batch_id: string;
  engine_version: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  chat_count: number;
  finding_count: number;
  evidence_count: number;
  exact_duplicate_count: number;
  partial_duplicate_count: number;
  version_count: number;
  decision_count: number;
  task_count: number;
  state_signal_count: number;
  originals_modified: boolean;
}

export interface AnalysisRun extends AnalysisRunSummary {
  findings: AnalysisFinding[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { method: "GET", headers: { Accept: "application/json" }, signal });
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  return (await response.json()) as T;
}

async function post<T>(url: string, body?: BodyInit, json = false): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (json) headers["Content-Type"] = "application/json";
  const response = await fetch(url, { method: "POST", body, headers });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export const api = {
  health: (signal?: AbortSignal) => getJson<HealthResponse>("/api/v1/health", signal),
  demoSummary: (signal?: AbortSignal) => getJson<DemoSummary>("/api/v1/demo/summary", signal),
  importDemo: () => post<ImportBatch>("/api/v1/imports/demo"),
  importFiles: (files: File[]) => {
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    return post<ImportBatch>("/api/v1/imports", form);
  },
  imports: (signal?: AbortSignal) => getJson<ImportBatch[]>("/api/v1/imports", signal),
  analyses: (signal?: AbortSignal) => getJson<AnalysisRunSummary[]>("/api/v1/analysis-runs", signal),
  analysis: (runId: string, signal?: AbortSignal) => getJson<AnalysisRun>(`/api/v1/analysis-runs/${runId}`, signal),
  runAnalysis: (batchId: string) => post<AnalysisRun>(
    "/api/v1/analysis-runs",
    JSON.stringify({ batch_id: batchId }),
    true,
  ),
};

export interface SemanticCapability {
  demo_available: boolean;
  live_available: boolean;
  default_model: string;
  responses_api: boolean;
  structured_outputs: boolean;
}

export interface ProjectMembership {
  id: string;
  chat_external_id: string;
  chat_title: string;
  status: string;
  confidence: "ALTA" | "MEDIA" | "BAJA";
  rationale: string;
}

export interface ProjectEvidence {
  id: string;
  chat_external_id: string;
  message_external_id: string | null;
  kind: string;
  quote: string;
  precedence: number;
}

export interface SemanticProject {
  id: string;
  project_key: string;
  name: string;
  description: string;
  state: string;
  confidence: "ALTA" | "MEDIA" | "BAJA";
  current_version: string | null;
  previous_versions: string[];
  discarded_versions: string[];
  phase: string | null;
  approved_decisions: string[];
  superseded_decisions: string[];
  discarded_items: string[];
  pending_tasks: string[];
  blockers: string[];
  last_confirmed_advance: string | null;
  next_probable_step: string | null;
  memberships: ProjectMembership[];
  evidences: ProjectEvidence[];
}

export interface SemanticException {
  id: string;
  chat_external_id: string | null;
  chat_title: string | null;
  kind: string;
  confidence: "ALTA" | "MEDIA" | "BAJA";
  candidate_project_keys: string[];
  reason: string;
}

export interface SemanticRunSummary {
  id: string;
  analysis_run_id: string;
  mode: "DEMO" | "LIVE";
  model: string;
  provider: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  input_digest: string;
  openai_response_id: string | null;
  project_count: number;
  membership_count: number;
  exception_count: number;
  independent_chat_count: number;
  unclassified_chat_count: number;
  originals_modified: boolean;
}

export interface SemanticRun extends SemanticRunSummary {
  projects: SemanticProject[];
  exceptions: SemanticException[];
  independent_chat_ids: string[];
  unclassified_chat_ids: string[];
}

Object.assign(api, {
  semanticCapabilities: (signal?: AbortSignal) => getJson<SemanticCapability>("/api/v1/semantic-runs/capabilities", signal),
  semanticRuns: (signal?: AbortSignal) => getJson<SemanticRunSummary[]>("/api/v1/semantic-runs", signal),
  semanticRun: (runId: string, signal?: AbortSignal) => getJson<SemanticRun>(`/api/v1/semantic-runs/${runId}`, signal),
  runSemantic: (analysisRunId: string, mode: "DEMO" | "LIVE") => post<SemanticRun>(
    "/api/v1/semantic-runs",
    JSON.stringify({ analysis_run_id: analysisRunId, mode }),
    true,
  ),
});

export const semanticApi = api as typeof api & {
  semanticCapabilities: (signal?: AbortSignal) => Promise<SemanticCapability>;
  semanticRuns: (signal?: AbortSignal) => Promise<SemanticRunSummary[]>;
  semanticRun: (runId: string, signal?: AbortSignal) => Promise<SemanticRun>;
  runSemantic: (analysisRunId: string, mode: "DEMO" | "LIVE") => Promise<SemanticRun>;
};


export interface UserReview {
  id: string;
  decision: "APPROVE" | "CORRECT" | "REJECT" | "KEEP_UNCHANGED";
  correction: Record<string, unknown>;
  note: string | null;
  created_at: string;
}

export interface ProposalItem {
  id: string;
  stable_key: string;
  operation: string;
  title: string;
  reason: string;
  confidence: "ALTA" | "MEDIA" | "BAJA";
  review_required: boolean;
  status: string;
  target_ids: string[];
  candidate_project_keys: string[];
  evidence_ids: string[];
  payload: Record<string, unknown>;
  latest_review: UserReview | null;
}

export interface ProposalRunSummary {
  id: string;
  semantic_run_id: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  safe_count: number;
  exception_count: number;
  safe_batch_approved: boolean;
  reviewed_exception_count: number;
  unresolved_exception_count: number;
  originals_modified: boolean;
}

export interface ProposalRun extends ProposalRunSummary {
  items: ProposalItem[];
}

export interface WorkspaceState {
  semantic_run_id: string;
  projects: Array<{
    project_key: string;
    name: string;
    state: string;
    current_version: string | null;
    previous_versions: string[];
    discarded_versions: string[];
    pending_tasks: string[];
    memberships: string[];
  }>;
  exact_duplicates: Array<{ duplicate_chat_id: string; canonical_chat_id: string | null }>;
  partial_duplicates: Array<{ chat_id: string; canonical_chat_id: string | null; merged: boolean }>;
  independent_chat_ids: string[];
  unclassified_chat_ids: string[];
  protected_chat_ids: string[];
  originals_modified: boolean;
}

export interface ProposalPreview {
  proposal_run_id: string;
  before_state: WorkspaceState;
  proposed_state: WorkspaceState;
  before_hash: string;
  proposed_hash: string;
  approved_proposal_ids: string[];
  unresolved_exception_ids: string[];
  originals_modified: boolean;
}

export interface AppliedOperation {
  id: string;
  proposal_run_id: string;
  status: string;
  before_hash: string;
  after_hash: string;
  applied_proposal_ids: string[];
  applied_at: string;
  undone_at: string | null;
  state: WorkspaceState;
  originals_modified: boolean;
}

export interface UndoOperation {
  id: string;
  applied_operation_id: string;
  status: string;
  restored_hash: string;
  created_at: string;
  audit_history_preserved: boolean;
  originals_modified: boolean;
  state: WorkspaceState;
}

export interface AuditEvent {
  id: string;
  sequence: number;
  event_type: string;
  payload: Record<string, unknown>;
  applied_operation_id: string | null;
  created_at: string;
}

Object.assign(semanticApi, {
  proposalRuns: (signal?: AbortSignal) => getJson<ProposalRunSummary[]>("/api/v1/proposal-runs", signal),
  proposalRun: (runId: string, signal?: AbortSignal) => getJson<ProposalRun>(`/api/v1/proposal-runs/${runId}`, signal),
  createProposalRun: (semanticRunId: string) => post<ProposalRun>(
    "/api/v1/proposal-runs", JSON.stringify({ semantic_run_id: semanticRunId }), true,
  ),
  approveSafe: (runId: string) => post<ProposalRun>(`/api/v1/proposal-runs/${runId}/approve-safe`),
  reviewProposal: (
    runId: string,
    itemId: string,
    decision: "APPROVE" | "CORRECT" | "REJECT" | "KEEP_UNCHANGED",
    correction: Record<string, unknown> = {},
  ) => post<ProposalRun>(
    `/api/v1/proposal-runs/${runId}/items/${itemId}/review`,
    JSON.stringify({ decision, correction }),
    true,
  ),
  previewProposal: (runId: string) => post<ProposalPreview>(`/api/v1/proposal-runs/${runId}/preview`),
  applyProposal: (runId: string) => post<AppliedOperation>(`/api/v1/proposal-runs/${runId}/apply`),
  undoOperation: (operationId: string) => post<UndoOperation>(`/api/v1/applied-operations/${operationId}/undo`),
  proposalAudit: (runId: string, signal?: AbortSignal) => getJson<AuditEvent[]>(`/api/v1/proposal-runs/${runId}/audit`, signal),
});

export const workflowApi = semanticApi as typeof semanticApi & {
  proposalRuns: (signal?: AbortSignal) => Promise<ProposalRunSummary[]>;
  proposalRun: (runId: string, signal?: AbortSignal) => Promise<ProposalRun>;
  createProposalRun: (semanticRunId: string) => Promise<ProposalRun>;
  approveSafe: (runId: string) => Promise<ProposalRun>;
  reviewProposal: (
    runId: string,
    itemId: string,
    decision: "APPROVE" | "CORRECT" | "REJECT" | "KEEP_UNCHANGED",
    correction?: Record<string, unknown>,
  ) => Promise<ProposalRun>;
  previewProposal: (runId: string) => Promise<ProposalPreview>;
  applyProposal: (runId: string) => Promise<AppliedOperation>;
  undoOperation: (operationId: string) => Promise<UndoOperation>;
  proposalAudit: (runId: string, signal?: AbortSignal) => Promise<AuditEvent[]>;
};
