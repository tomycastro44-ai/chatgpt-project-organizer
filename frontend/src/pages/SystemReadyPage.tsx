import type { DemoSummary, HealthResponse } from "../api/client";
import { IntegrityBanner } from "../components/IntegrityBanner";

interface Props {
  health: HealthResponse | null;
  summary: DemoSummary | null;
  error: string | null;
  loading: boolean;
}

export function SystemReadyPage({ health, summary, error, loading }: Props) {
  return (
    <main className="main-content">
      <header className="topbar">
        <span className="stage-tag">FASE 4 · O.T. 008</span>
        <span>Technical foundation</span>
      </header>

      <section className="page-content">
        <div className="hero">
          <div>
            <p className="eyebrow">Construction baseline</p>
            <h1>Repository and runtime are ready</h1>
            <p className="lead">
              The approved dataset and visual contracts are connected to an executable
              React and FastAPI foundation. No semantic analysis or real organization
              operation is enabled yet.
            </p>
          </div>
          <IntegrityBanner />
        </div>

        {loading && <div className="notice">Checking backend and approved fixtures…</div>}
        {error && <div className="notice error">{error}</div>}

        <div className="metrics" aria-label="Foundation metrics">
          <Metric value={health?.status === "ok" ? "OK" : "—"} label="Backend status" />
          <Metric value={summary?.chats ?? "—"} label="Approved chats" />
          <Metric value={summary?.projects ?? "—"} label="Expected projects" />
          <Metric value={summary?.acceptance_cases ?? "—"} label="Dataset test cases" />
        </div>

        <section className="foundation-grid">
          <article className="card">
            <h2>Foundation enabled</h2>
            <ul>
              <li>Versioned FastAPI routes.</li>
              <li>SQLite runtime initialization.</li>
              <li>React and TypeScript application shell.</li>
              <li>Read-only O.T. 006 fixture access.</li>
              <li>Automated backend and frontend tests.</li>
            </ul>
          </article>
          <article className="card muted-card">
            <h2>Deliberately not enabled</h2>
            <ul>
              <li>GPT-5.6 calls.</li>
              <li>Conversation import.</li>
              <li>Project analysis and proposals.</li>
              <li>Apply, audit, or undo operations.</li>
              <li>Authentication or multiuser behavior.</li>
            </ul>
          </article>
        </section>

        <section className="card contract-card">
          <div>
            <p className="eyebrow">Validated contract</p>
            <h2>One stable base for the next O.T.</h2>
            <p>
              Frontend and backend communicate through <code>/api/v1</code>. Runtime
              data is isolated from the approved demonstration sources.
            </p>
          </div>
          <span className="status-pill">READY FOR REVIEW</span>
        </section>
      </section>
    </main>
  );
}

function Metric({ value, label }: { value: string | number; label: string }) {
  return (
    <article className="metric-card">
      <strong>{value}</strong>
      <span>{label}</span>
    </article>
  );
}
