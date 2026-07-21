import { useMemo, useState } from "react";

import {
  semanticApi,
  type AnalysisRun,
  type ImportBatch,
  type SemanticCapability,
  type SemanticProject,
  type SemanticRun,
} from "../api/client";
import { IntegrityBanner } from "../components/IntegrityBanner";

interface Props {
  latestBatch: ImportBatch | null;
  latestAnalysis: AnalysisRun | null;
  latestSemanticRun: SemanticRun | null;
  capability: SemanticCapability | null;
  onImported: (batch: ImportBatch) => void;
  onAnalyzed: (run: AnalysisRun) => void;
  onSemanticRun: (run: SemanticRun) => void;
}

export function ProjectsPage({
  latestBatch,
  latestAnalysis,
  latestSemanticRun,
  capability,
  onImported,
  onAnalyzed,
  onSemanticRun,
}: Props) {
  const [mode, setMode] = useState<"DEMO" | "LIVE">("DEMO");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(latestSemanticRun?.projects[0]?.project_key ?? null);
  const run = latestSemanticRun;
  const selected = useMemo(
    () => run?.projects.find((project) => project.project_key === selectedKey) ?? run?.projects[0] ?? null,
    [run, selectedKey],
  );

  async function reconstruct() {
    setBusy(true);
    setError(null);
    try {
      let batch = latestBatch;
      if (!batch) {
        batch = await semanticApi.importDemo();
        onImported(batch);
      }
      let analysis = latestAnalysis;
      if (!analysis || analysis.batch_id !== batch.id) {
        analysis = await semanticApi.runAnalysis(batch.id);
        onAnalyzed(analysis);
      }
      const semanticRun = await semanticApi.runSemantic(analysis.id, mode);
      onSemanticRun(semanticRun);
      setSelectedKey(semanticRun.projects[0]?.project_key ?? null);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Semantic reconstruction failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="main-content">
      <header className="topbar">
        <span className="stage-tag">FASE 4 · O.T. 011</span>
        <span>Semantic projects and operational memory</span>
      </header>

      <section className="page-content">
        <div className="hero">
          <div>
            <p className="eyebrow">Projects</p>
            <h1>Reconstruct project context instead of sorting chats one by one</h1>
            <p className="lead">
              GPT-5.6 or the explicitly labelled approved demo interprets the deterministic evidence, groups related conversations and builds a reversible operational memory for each project.
            </p>
          </div>
          <IntegrityBanner />
        </div>

        {error && <div className="notice error">{error}</div>}

        <section className="card semantic-control">
          <div>
            <p className="eyebrow">Execution mode</p>
            <h2>{mode === "DEMO" ? "Approved reproducible demo" : "Live GPT-5.6 analysis"}</h2>
            <p className="muted-text">
              {mode === "DEMO"
                ? "Uses the frozen O.T. 006 expected output. It is never presented as a live model result."
                : "Uses the OpenAI Responses API with strict structured output. The API key remains server-side."}
            </p>
          </div>
          <div className="semantic-actions">
            <label className="mode-choice">
              <span>Mode</span>
              <select value={mode} onChange={(event) => setMode(event.target.value as "DEMO" | "LIVE")}>
                <option value="DEMO">DEMO · reproducible</option>
                <option value="LIVE" disabled={!capability?.live_available}>LIVE · GPT-5.6</option>
              </select>
            </label>
            <button className="primary-button" type="button" onClick={reconstruct} disabled={busy}>
              {busy ? "Reconstructing…" : run ? "Run again" : "Reconstruct projects"}
            </button>
          </div>
        </section>

        <div className="metrics" aria-label="Semantic metrics">
          <Metric value={run?.project_count ?? "—"} label="Projects" />
          <Metric value={run?.membership_count ?? "—"} label="Memberships" />
          <Metric value={run?.exception_count ?? "—"} label="Exceptions" />
          <Metric value={run?.independent_chat_count ?? "—"} label="Independent chats" />
        </div>

        {!run ? (
          <section className="card analysis-empty">
            <p className="eyebrow">Ready</p>
            <h2>Evidence is ready for semantic reconstruction</h2>
            <p className="muted-text">The next action creates project memories only. It does not apply organization changes or modify original chats.</p>
          </section>
        ) : (
          <>
            <div className="semantic-run-banner">
              <div>
                <strong>{run.mode === "DEMO" ? "DEMO · PRECOMPUTED" : "LIVE · OPENAI RESPONSES API"}</strong>
                <span>{run.model} · {run.provider}</span>
              </div>
              <span className="status-pill">{run.status}</span>
            </div>

            <section className="memory-workspace">
              <aside className="project-memory-list card">
                <p className="eyebrow">Detected projects</p>
                {run.projects.map((project) => (
                  <button
                    type="button"
                    key={project.project_key}
                    className={`memory-project-button ${selected?.project_key === project.project_key ? "active" : ""}`}
                    onClick={() => setSelectedKey(project.project_key)}
                  >
                    <span><strong>{project.name}</strong><small>{project.memberships.length} chats</small></span>
                    <span className={`state-badge state-${project.state.toLowerCase()}`}>{project.state}</span>
                  </button>
                ))}
              </aside>

              {selected && <ProjectMemory project={selected} mode={run.mode} />}
            </section>

            <section className="card exception-section">
              <div className="section-heading">
                <div><p className="eyebrow">Review by exception</p><h2>{run.exceptions.length} cases need human attention</h2></div>
                <span className="status-pill">NOT APPLIED</span>
              </div>
              <div className="exception-grid">
                {run.exceptions.map((item) => (
                  <article className="semantic-exception" key={item.id}>
                    <div><strong>{item.chat_external_id ?? "Cross-project case"}</strong><span className={`confidence confidence-${item.confidence.toLowerCase()}`}>{item.confidence}</span></div>
                    <p>{item.reason}</p>
                    {item.candidate_project_keys.length > 0 && <small>Candidates: {item.candidate_project_keys.join(" · ")}</small>}
                  </article>
                ))}
              </div>
            </section>
          </>
        )}

        <section className="card contract-card">
          <div>
            <p className="eyebrow">Validated boundary</p>
            <h2>Projects and memory exist; organization is not applied</h2>
            <p>Proposal generation, user review, simulated application, audit and Undo remain disabled until the next O.T.</p>
          </div>
          <span className="status-pill">MEMORY LAYER ACTIVE</span>
        </section>
      </section>
    </main>
  );
}

function ProjectMemory({ project, mode }: { project: SemanticProject; mode: string }) {
  const [showEvidence, setShowEvidence] = useState(false);
  return (
    <article className="card project-memory-detail">
      <div className="section-heading">
        <div><p className="eyebrow">Operational memory</p><h2>{project.name}</h2><p className="muted-text">{project.description}</p></div>
        <div className="memory-heading-actions">
          <span className={`state-badge state-${project.state.toLowerCase()}`}>{project.state}</span>
          <button className="secondary-button" type="button" onClick={() => setShowEvidence((value) => !value)}>{showEvidence ? "Hide evidence" : "View evidence"}</button>
        </div>
      </div>

      <div className="memory-facts">
        <Fact label="Current version" value={project.current_version ?? "Not resolved"} />
        <Fact label="Current phase" value={project.phase ?? "Not resolved"} />
        <Fact label="Last confirmed advance" value={project.last_confirmed_advance ?? "Not resolved"} />
        <Fact label="Next probable step" value={project.next_probable_step ?? "Not resolved"} />
      </div>

      <MemoryList title="Approved decisions" values={project.approved_decisions} empty="No approved decisions detected" />
      <MemoryList title="Pending tasks" values={project.pending_tasks} empty="No pending tasks" />
      <div className="memory-columns">
        <MemoryList title="Previous versions" values={project.previous_versions} empty="None" />
        <MemoryList title="Discarded versions or items" values={[...project.discarded_versions, ...project.discarded_items]} empty="None" />
      </div>

      <div className="membership-list">
        <h3>Associated conversations</h3>
        {project.memberships.map((membership) => (
          <div className="membership-row" key={membership.id}>
            <span><strong>{membership.chat_external_id}</strong><small>{membership.chat_title}</small></span>
            <span className={`confidence confidence-${membership.confidence.toLowerCase()}`}>{membership.status} · {membership.confidence}</span>
          </div>
        ))}
      </div>

      {showEvidence && (
        <div className="project-evidence-list">
          <p className="eyebrow">Evidence · {mode}</p>
          {project.evidences.map((evidence) => (
            <blockquote key={evidence.id}>“{evidence.quote}”<footer>{evidence.chat_external_id} · precedence {evidence.precedence}</footer></blockquote>
          ))}
        </div>
      )}
    </article>
  );
}

function Metric({ value, label }: { value: number | string; label: string }) {
  return <article className="metric-card"><strong>{value}</strong><span>{label}</span></article>;
}
function Fact({ label, value }: { label: string; value: string }) {
  return <div className="memory-fact"><span>{label}</span><strong>{value}</strong></div>;
}
function MemoryList({ title, values, empty }: { title: string; values: string[]; empty: string }) {
  return <section className="memory-list-section"><h3>{title}</h3>{values.length ? <ul>{values.map((value) => <li key={value}>{value}</li>)}</ul> : <p className="muted-text">{empty}</p>}</section>;
}
