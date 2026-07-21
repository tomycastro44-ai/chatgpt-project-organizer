import { useMemo, useState } from "react";

import {
  workflowApi,
  type AnalysisRun,
  type AppliedOperation,
  type AuditEvent,
  type ImportBatch,
  type ProposalItem,
  type ProposalPreview,
  type ProposalRun,
  type SemanticCapability,
  type SemanticRun,
  type UndoOperation,
} from "../api/client";
import { IntegrityBanner } from "../components/IntegrityBanner";

interface Props {
  latestBatch: ImportBatch | null;
  latestAnalysis: AnalysisRun | null;
  latestSemanticRun: SemanticRun | null;
  latestProposalRun: ProposalRun | null;
  capability: SemanticCapability | null;
  onImported: (batch: ImportBatch) => void;
  onAnalyzed: (run: AnalysisRun) => void;
  onSemanticRun: (run: SemanticRun) => void;
  onProposalRun: (run: ProposalRun) => void;
}

export function ProposalsPage({
  latestBatch, latestAnalysis, latestSemanticRun, latestProposalRun, capability,
  onImported, onAnalyzed, onSemanticRun, onProposalRun,
}: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<ProposalPreview | null>(null);
  const [operation, setOperation] = useState<AppliedOperation | null>(null);
  const [undo, setUndo] = useState<UndoOperation | null>(null);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [selections, setSelections] = useState<Record<string, string>>({});
  const run = latestProposalRun;
  const safeItems = useMemo(() => run?.items?.filter((item) => !item.review_required) ?? [], [run]);
  const exceptions = useMemo(() => run?.items?.filter((item) => item.review_required) ?? [], [run]);

  async function ensureProposalRun() {
    setBusy(true); setError(null);
    try {
      let batch = latestBatch;
      if (!batch) { batch = await workflowApi.importDemo(); onImported(batch); }
      let analysis = latestAnalysis;
      if (!analysis || analysis.batch_id !== batch.id) { analysis = await workflowApi.runAnalysis(batch.id); onAnalyzed(analysis); }
      let semantic = latestSemanticRun;
      if (!semantic || semantic.analysis_run_id !== analysis.id) {
        semantic = await workflowApi.runSemantic(analysis.id, "DEMO"); onSemanticRun(semantic);
      }
      const proposals = await workflowApi.createProposalRun(semantic.id);
      onProposalRun(proposals); setPreview(null); setOperation(null); setUndo(null);
      setAudit(await workflowApi.proposalAudit(proposals.id));
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Proposal generation failed");
    } finally { setBusy(false); }
  }

  async function approveSafe() {
    if (!run) return;
    await action(async () => {
      const updated = await workflowApi.approveSafe(run.id); onProposalRun(updated);
      setAudit(await workflowApi.proposalAudit(run.id));
    });
  }

  async function review(item: ProposalItem, decision: "APPROVE" | "CORRECT" | "REJECT" | "KEEP_UNCHANGED") {
    if (!run) return;
    const correction = decision === "CORRECT" ? { project_key: selections[item.id] ?? item.candidate_project_keys[0] } : {};
    await action(async () => {
      const updated = await workflowApi.reviewProposal(run.id, item.id, decision, correction); onProposalRun(updated);
      setPreview(null); setAudit(await workflowApi.proposalAudit(run.id));
    });
  }

  async function generatePreview() {
    if (!run) return;
    await action(async () => { setPreview(await workflowApi.previewProposal(run.id)); setAudit(await workflowApi.proposalAudit(run.id)); });
  }

  async function apply() {
    if (!run) return;
    await action(async () => {
      const applied = await workflowApi.applyProposal(run.id); setOperation(applied);
      const updated = await workflowApi.proposalRun(run.id); onProposalRun(updated);
      setAudit(await workflowApi.proposalAudit(run.id));
    });
  }

  async function undoApplied() {
    if (!operation) return;
    await action(async () => {
      const restored = await workflowApi.undoOperation(operation.id); setUndo(restored);
      if (run) { onProposalRun(await workflowApi.proposalRun(run.id)); setAudit(await workflowApi.proposalAudit(run.id)); }
    });
  }

  async function action(callback: () => Promise<void>) {
    setBusy(true); setError(null);
    try { await callback(); }
    catch (reason: unknown) { setError(reason instanceof Error ? reason.message : "Operation failed"); }
    finally { setBusy(false); }
  }

  return (
    <main className="main-content">
      <header className="topbar"><span className="stage-tag">FASE 4 · O.T. 012</span><span>Review, preview, apply and Undo</span></header>
      <section className="page-content">
        <div className="hero">
          <div><p className="eyebrow">Controlled organization</p><h1>Approve one coherent plan and review only the exceptions</h1>
            <p className="lead">The organizer converts semantic memory into reversible proposals. Nothing reaches the simulated workspace until the safe batch is explicitly approved.</p></div>
          <IntegrityBanner />
        </div>
        {error && <div className="notice error">{error}</div>}

        {!run ? (
          <section className="card proposal-start">
            <div><p className="eyebrow">Ready</p><h2>Generate the global organization proposal</h2>
              <p className="muted-text">The approved demo reconstructs the full chain automatically: import, deterministic evidence, semantic projects and proposals.</p></div>
            <button className="primary-button" type="button" onClick={ensureProposalRun} disabled={busy}>{busy ? "Preparing…" : "Generate proposals"}</button>
          </section>
        ) : (
          <>
            <div className="metrics" aria-label="Proposal metrics">
              <Metric value={run.safe_count} label="Safe proposals" />
              <Metric value={run.exception_count} label="Exceptions" />
              <Metric value={run.reviewed_exception_count} label="Reviewed" />
              <Metric value={run.unresolved_exception_count} label="Unresolved" />
            </div>

            <section className="card safe-proposal-section">
              <div className="section-heading"><div><p className="eyebrow">Safe batch</p><h2>{run.safe_batch_approved ? "Safe proposals approved" : "Approve safe proposals as one batch"}</h2>
                <p className="muted-text">Every item is evidence-backed. Global approval is still required before simulated application.</p></div>
                <button className={run.safe_batch_approved ? "secondary-button" : "primary-button"} type="button" disabled={busy || run.safe_batch_approved} onClick={approveSafe}>
                  {run.safe_batch_approved ? "Approved" : `Approve ${run.safe_count} safe proposals`}
                </button></div>
              <div className="proposal-list">{safeItems.map((item) => <ProposalRow key={item.id} item={item} />)}</div>
            </section>

            <section className="card exception-section">
              <div className="section-heading"><div><p className="eyebrow">Review by exception</p><h2>Resolve only ambiguous cases</h2></div><span className="status-pill">{run.unresolved_exception_count} PENDING</span></div>
              <div className="review-grid">{exceptions.map((item) => (
                <article className="review-card" key={item.id}>
                  <div className="review-title"><div><strong>{item.title}</strong><small>{item.target_ids.join(" · ") || "Cross-project case"}</small></div><span className={`confidence confidence-${item.confidence.toLowerCase()}`}>{item.confidence}</span></div>
                  <p>{item.reason}</p>
                  {item.candidate_project_keys.length > 0 && (
                    <label className="project-choice">Correct destination<select value={selections[item.id] ?? item.candidate_project_keys[0]} onChange={(event) => setSelections((current) => ({ ...current, [item.id]: event.target.value }))}>
                      {item.candidate_project_keys.map((key) => <option value={key} key={key}>{key}</option>)}</select></label>
                  )}
                  <div className="review-actions">
                    {item.candidate_project_keys.length > 0 && <button className="primary-button compact" type="button" disabled={busy} onClick={() => review(item, "CORRECT")}>Correct & approve</button>}
                    {item.operation === "MARK_PARTIAL_DUPLICATE" && <button className="primary-button compact" type="button" disabled={busy} onClick={() => review(item, "APPROVE")}>Record relation</button>}
                    <button className="secondary-button" type="button" disabled={busy} onClick={() => review(item, "REJECT")}>Reject</button>
                  </div>
                  {item.latest_review && <div className="review-result">Decision: <strong>{item.latest_review.decision}</strong></div>}
                </article>
              ))}</div>
            </section>

            <section className="card preview-control">
              <div><p className="eyebrow">Mandatory preview</p><h2>Compare before and after before applying</h2><p className="muted-text">Unresolved exceptions stay protected. Rejected items remain unchanged.</p></div>
              <button className="primary-button" type="button" disabled={busy || !run.safe_batch_approved} onClick={generatePreview}>Generate preview</button>
            </section>

            {preview && <PreviewPanel preview={preview} />}

            {preview && !operation && (
              <section className="card apply-bar"><div><strong>{preview.approved_proposal_ids.length} approved operations ready</strong><span>{preview.unresolved_exception_ids.length} unresolved exceptions will remain protected.</span></div>
                <button className="success-button" type="button" disabled={busy} onClick={apply}>Apply simulated organization</button></section>
            )}

            {operation && !undo && (
              <section className="card result-card"><div className="result-mark">✓</div><div><p className="eyebrow">Applied</p><h2>{operation.state.projects.length} projects organized</h2>
                <p className="muted-text">Operation {operation.id}. Originals modified: 0. Audit recorded.</p></div><button className="danger-button" type="button" disabled={busy} onClick={undoApplied}>Undo operation</button></section>
            )}
            {undo && (
              <section className="card result-card undo-complete"><div className="result-mark">↶</div><div><p className="eyebrow">Restored</p><h2>Previous simulated state restored exactly</h2>
                <p className="muted-text">Hash {undo.restored_hash.slice(0, 12)}… · audit history preserved · originals modified: 0.</p></div></section>
            )}

            <section className="card audit-section"><div className="section-heading"><div><p className="eyebrow">Audit</p><h2>Immutable operation history</h2></div><span className="status-pill">{audit.length} EVENTS</span></div>
              <ol className="audit-list">{audit.map((event) => <li key={event.id}><span>{event.sequence}</span><div><strong>{event.event_type.replaceAll("_", " ")}</strong><small>{new Date(event.created_at).toLocaleString()}</small></div></li>)}</ol>
            </section>
          </>
        )}

        <section className="card contract-card"><div><p className="eyebrow">Integrity boundary</p><h2>Original conversations remain immutable</h2><p>Only derived workspace state is changed. Every apply stores before and after hashes; Undo restores the exact prior state without deleting audit history.</p></div><span className="status-pill">REVERSIBLE</span></section>
      </section>
    </main>
  );
}

function ProposalRow({ item }: { item: ProposalItem }) {
  return <div className="proposal-row"><span className={`proposal-status status-${item.status.toLowerCase()}`}>{item.status}</span><div><strong>{item.title}</strong><small>{item.reason}</small></div><span className={`confidence confidence-${item.confidence.toLowerCase()}`}>{item.confidence}</span></div>;
}

function PreviewPanel({ preview }: { preview: ProposalPreview }) {
  return <section className="preview-grid">
    <article className="card"><p className="eyebrow">Before</p><h2>{preview.before_state.projects.length} organized projects</h2><StateFacts state={preview.before_state} /></article>
    <div className="preview-arrow">→</div>
    <article className="card preview-after"><p className="eyebrow">After</p><h2>{preview.proposed_state.projects.length} organized projects</h2><StateFacts state={preview.proposed_state} />
      <div className="preview-projects">{preview.proposed_state.projects.map((project) => <div key={project.project_key}><strong>{project.name}</strong><span>{project.state} · {project.memberships.length} chats</span></div>)}</div>
    </article>
  </section>;
}

function StateFacts({ state }: { state: ProposalPreview["proposed_state"] }) {
  return <div className="state-facts"><span>{state.exact_duplicates.length} exact duplicates</span><span>{state.partial_duplicates.length} partial duplicates</span><span>{state.unclassified_chat_ids.length} unclassified</span><span>{state.protected_chat_ids.length} protected</span></div>;
}
function Metric({ value, label }: { value: number | string; label: string }) { return <article className="metric-card"><strong>{value}</strong><span>{label}</span></article>; }
