import { useEffect, useRef, useState } from "react";

import { api, type DemoSummary, type HealthResponse, type ImportBatch } from "../api/client";
import { IntegrityBanner } from "../components/IntegrityBanner";

interface Props {
  health: HealthResponse | null;
  summary: DemoSummary | null;
  history: ImportBatch[];
  initialError: string | null;
  loadingInitial: boolean;
  onImported: (batch: ImportBatch) => void;
}

export function ImportPage({ health, summary, history, initialError, loadingInitial, onImported }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<ImportBatch | null>(history[0] ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (history[0]) setResult(history[0]);
  }, [history]);

  async function execute(action: () => Promise<ImportBatch>) {
    setBusy(true);
    setError(null);
    try {
      const batch = await action();
      setResult(batch);
      setFiles([]);
      if (inputRef.current) inputRef.current.value = "";
      onImported(batch);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Import failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="main-content">
      <header className="topbar">
        <span className="stage-tag">FASE 4 · O.T. 010</span>
        <span>Functional import and normalization</span>
      </header>

      <section className="page-content">
        <div className="hero">
          <div>
            <p className="eyebrow">Import</p>
            <h1>Load conversations without changing their source files</h1>
            <p className="lead">
              JSON, CSV and TXT sources are copied to protected runtime storage, normalized into a common model and persisted in SQLite. Invalid records are isolated instead of corrupting the batch.
            </p>
          </div>
          <IntegrityBanner />
        </div>

        {loadingInitial && <div className="notice">Checking backend and previous imports…</div>}
        {(initialError || error) && <div className="notice error">{initialError ?? error}</div>}

        <div className="metrics" aria-label="Import metrics">
          <Metric value={health?.status === "ok" ? "OK" : "—"} label="Backend status" />
          <Metric value={summary?.source_files ?? "—"} label="Demo source files" />
          <Metric value={result?.imported_chats ?? summary?.chats ?? "—"} label="Normalized chats" />
          <Metric value={result?.issue_count ?? 0} label="Import issues" />
        </div>

        <section className="import-grid">
          <article className="card import-card">
            <p className="eyebrow">Source selection</p>
            <h2>Choose JSON, CSV or TXT files</h2>
            <label className="file-picker">
              <input
                ref={inputRef}
                type="file"
                multiple
                accept=".json,.csv,.txt,application/json,text/csv,text/plain"
                onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
              />
              <span className="file-picker-icon" aria-hidden="true">⇧</span>
              <strong>Select source files</strong>
              <span>Maximum 20 files · 10 MB each</span>
            </label>
            <div className="selected-files" aria-live="polite">
              {files.length === 0 ? (
                <p className="muted-text">No local files selected.</p>
              ) : (
                files.map((file) => (
                  <div className="selected-file" key={`${file.name}-${file.size}`}>
                    <div><strong>{file.name}</strong><span>{formatBytes(file.size)}</span></div>
                    <span className="format-pill">{file.name.split(".").pop()?.toUpperCase()}</span>
                  </div>
                ))
              )}
            </div>
            <div className="button-row">
              <button className="secondary-button" type="button" disabled={busy} onClick={() => execute(api.importDemo)}>
                Import approved demo dataset
              </button>
              <button className="primary-button" type="button" disabled={busy || files.length === 0} onClick={() => execute(() => api.importFiles(files))}>
                {busy ? "Importing…" : "Validate and import"}
              </button>
            </div>
          </article>

          <article className="card result-card">
            <p className="eyebrow">Latest result</p>
            <h2>{result ? result.status.replaceAll("_", " ") : "No import executed"}</h2>
            {!result ? (
              <p className="muted-text">Run the approved dataset or select local files to create the first import batch.</p>
            ) : (
              <>
                <div className="result-summary">
                  <Summary label="Files" value={`${result.accepted_files}/${result.total_files} accepted`} />
                  <Summary label="Chats" value={String(result.imported_chats)} />
                  <Summary label="Messages" value={String(result.imported_messages)} />
                  <Summary label="Issues" value={String(result.issue_count)} />
                </div>
                <div className="source-results">
                  {result.source_files.map((source) => (
                    <div className="source-result" key={source.id}>
                      <div>
                        <strong>{source.original_name}</strong>
                        <span>{source.chat_count} chats · {source.message_count} messages · SHA-256 {source.sha256.slice(0, 12)}…</span>
                      </div>
                      <span className={`status-badge status-${source.status.toLowerCase()}`}>{source.status}</span>
                    </div>
                  ))}
                </div>
                {result.issues.length > 0 && (
                  <div className="issue-list">
                    <h3>Isolated issues</h3>
                    {result.issues.map((issue) => <p key={issue.id}><strong>{issue.code}</strong> · {issue.message}</p>)}
                  </div>
                )}
              </>
            )}
          </article>
        </section>

        <section className="card contract-card">
          <div>
            <p className="eyebrow">Validated contract</p>
            <h2>Normalized data is ready for deterministic analysis</h2>
            <p>Every batch has immutable source copies, SHA-256 evidence, isolated issues and a deterministic chat/message representation.</p>
          </div>
          <span className="status-pill">IMPORT LAYER ACTIVE</span>
        </section>
      </section>
    </main>
  );
}

function Metric({ value, label }: { value: string | number; label: string }) {
  return <article className="metric-card"><strong>{value}</strong><span>{label}</span></article>;
}
function Summary({ label, value }: { label: string; value: string }) {
  return <div><span>{label}</span><strong>{value}</strong></div>;
}
function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
