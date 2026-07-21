import { useEffect, useMemo, useState } from "react";

import { api, type AnalysisFinding, type AnalysisRun, type ImportBatch } from "../api/client";
import { IntegrityBanner } from "../components/IntegrityBanner";

interface Props {
  latestBatch: ImportBatch | null;
  latestRun: AnalysisRun | null;
  onImported: (batch: ImportBatch) => void;
  onAnalyzed: (run: AnalysisRun) => void;
}

const GROUP_ORDER = [
  "EXACT_DUPLICATE",
  "PARTIAL_DUPLICATE",
  "VERSION_STATUS",
  "STATE_PRECEDENCE",
  "STATE_SIGNAL",
  "DECISION",
  "TASK",
];

export function AnalysisPage({ latestBatch, latestRun, onImported, onAnalyzed }: Props) {
  const [run, setRun] = useState<AnalysisRun | null>(latestRun);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    setRun(latestRun);
  }, [latestRun]);

  const grouped = useMemo(() => {
    const result = new Map<string, AnalysisFinding[]>();
    for (const finding of run?.findings ?? []) {
      const current = result.get(finding.finding_type) ?? [];
      current.push(finding);
      result.set(finding.finding_type, current);
    }
    return result;
  }, [run]);

  async function executeAnalysis() {
    setBusy(true);
    setError(null);
    try {
      let batch = latestBatch;
      if (!batch) {
        batch = await api.importDemo();
        onImported(batch);
      }
      const analysis = await api.runAnalysis(batch.id);
      setRun(analysis);
      onAnalyzed(analysis);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Analysis failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="main-content">
      <header className="topbar">
        <span className="stage-tag">FASE 4 · O.T. 010</span>
        <span>Deterministic analysis and evidence</span>
      </header>

      <section className="page-content">
        <div className="hero">
          <div>
            <p className="eyebrow">Analysis</p>
            <h1>Detect objective signals before semantic interpretation</h1>
            <p className="lead">
              Reproducible rules detect duplicates, version precedence, decisions, pending tasks and explicit project-state signals. Every finding retains the exact conversation evidence used.
            </p>
          </div>
          <IntegrityBanner />
        </div>

        {error && <div className="notice error">{error}</div>}

        <div className="analysis-toolbar">
          <div>
            <strong>{latestBatch ? `${latestBatch.imported_chats} normalized chats ready` : "No import batch available"}</strong>
            <p>{run ? `Run ${run.id.slice(0, 8)} · ${run.engine_version}` : "Run the approved demo dataset or analyze the latest import."}</p>
          </div>
          <button className="primary-button" type="button" disabled={busy} onClick={executeAnalysis}>
            {busy ? "Analyzing…" : latestBatch ? "Run deterministic analysis" : "Import demo and analyze"}
          </button>
        </div>

        <div className="metrics" aria-label="Analysis metrics">
          <Metric value={run?.finding_count ?? "—"} label="Findings" />
          <Metric value={run?.evidence_count ?? "—"} label="Evidence records" />
          <Metric value={run ? run.exact_duplicate_count + run.partial_duplicate_count : "—"} label="Duplicate relations" />
          <Metric value={run?.state_signal_count ?? "—"} label="State signals" />
        </div>

        {!run ? (
          <section className="card analysis-empty">
            <p className="eyebrow">Ready</p>
            <h2>The normalized batch can now be analyzed</h2>
            <p className="muted-text">This O.T. does not create projects or proposals. It produces an auditable evidence layer for the next construction step.</p>
          </section>
        ) : (
          <section className="analysis-layout">
            <article className="card analysis-summary-card">
              <p className="eyebrow">Completed run</p>
              <h2>{run.status}</h2>
              <Summary label="Exact duplicates" value={run.exact_duplicate_count} />
              <Summary label="Partial duplicates" value={run.partial_duplicate_count} />
              <Summary label="Resolved versions" value={run.version_count} />
              <Summary label="Decision signals" value={run.decision_count} />
              <Summary label="Pending-task signals" value={run.task_count} />
              <Summary label="State findings" value={run.state_signal_count} />
              <div className="analysis-integrity">✓ Originals modified: {run.originals_modified ? "YES" : "NO"}</div>
            </article>

            <div className="finding-groups">
              {GROUP_ORDER.filter((type) => grouped.has(type)).map((type) => (
                <article className="card finding-group" key={type}>
                  <div className="finding-group-heading">
                    <div><p className="eyebrow">{humanize(type)}</p><h2>{grouped.get(type)?.length} findings</h2></div>
                    <span className="status-pill">DETERMINISTIC</span>
                  </div>
                  <div className="finding-list">
                    {grouped.get(type)?.map((finding) => (
                      <div className="finding-row" key={finding.id}>
                        <button className="finding-toggle" type="button" onClick={() => setExpanded(expanded === finding.id ? null : finding.id)}>
                          <span>
                            <strong>{finding.subject}</strong>
                            <small>{finding.chat_external_id}{finding.related_chat_external_id ? ` ↔ ${finding.related_chat_external_id}` : ""}</small>
                          </span>
                          <span className={`confidence confidence-${finding.confidence.toLowerCase()}`}>{finding.confidence}</span>
                          <span className="classification">{finding.classification ?? "UNRESOLVED"}</span>
                        </button>
                        {expanded === finding.id && (
                          <div className="evidence-panel">
                            {finding.evidences.map((evidence) => (
                              <blockquote key={evidence.id}>
                                “{evidence.quote}”
                                <footer>{evidence.chat_external_id} · precedence {evidence.precedence}</footer>
                              </blockquote>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}

        <section className="card contract-card">
          <div>
            <p className="eyebrow">Validated boundary</p>
            <h2>Evidence is ready; project grouping remains disabled</h2>
            <p>GPT-5.6, semantic grouping, proposals, application and Undo are intentionally outside O.T. 010.</p>
          </div>
          <span className="status-pill">ANALYSIS LAYER ACTIVE</span>
        </section>
      </section>
    </main>
  );
}

function Metric({ value, label }: { value: string | number; label: string }) {
  return <article className="metric-card"><strong>{value}</strong><span>{label}</span></article>;
}
function Summary({ label, value }: { label: string; value: string | number }) {
  return <div className="analysis-summary-line"><span>{label}</span><strong>{value}</strong></div>;
}
function humanize(value: string) {
  return value.toLowerCase().replaceAll("_", " ");
}
