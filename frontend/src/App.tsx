import { useEffect, useState } from "react";

import { workflowApi, type AnalysisRun, type DemoSummary, type HealthResponse, type ImportBatch, type ProposalRun, type SemanticCapability, type SemanticRun } from "./api/client";
import { ProjectSidebar, type WorkflowPage } from "./components/ProjectSidebar";
import { AnalysisPage } from "./pages/AnalysisPage";
import { ImportPage } from "./pages/ImportPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { ProposalsPage } from "./pages/ProposalsPage";

export default function App() {
  const [page, setPage] = useState<WorkflowPage>("proposals");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [summary, setSummary] = useState<DemoSummary | null>(null);
  const [history, setHistory] = useState<ImportBatch[]>([]);
  const [analyses, setAnalyses] = useState<AnalysisRun[]>([]);
  const [semanticRuns, setSemanticRuns] = useState<SemanticRun[]>([]);
  const [proposalRuns, setProposalRuns] = useState<ProposalRun[]>([]);
  const [capability, setCapability] = useState<SemanticCapability | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      workflowApi.health(controller.signal), workflowApi.demoSummary(controller.signal), workflowApi.imports(controller.signal),
      workflowApi.analyses(controller.signal), workflowApi.semanticCapabilities(controller.signal), workflowApi.semanticRuns(controller.signal),
      workflowApi.proposalRuns(controller.signal),
    ]).then(async ([healthResponse, summaryResponse, importHistory, analysisHistory, semanticCapability, semanticHistory, proposalHistory]) => {
      setHealth(healthResponse); setSummary(summaryResponse); setHistory(importHistory); setCapability(semanticCapability);
      if (analysisHistory[0]) setAnalyses([await workflowApi.analysis(analysisHistory[0].id, controller.signal)]);
      if (semanticHistory[0]) setSemanticRuns([await workflowApi.semanticRun(semanticHistory[0].id, controller.signal)]);
      if (proposalHistory[0]) setProposalRuns([await workflowApi.proposalRun(proposalHistory[0].id, controller.signal)]);
    }).catch((reason: unknown) => {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      setError(reason instanceof Error ? reason.message : "Unknown connection error");
    }).finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  const recordImport = (batch: ImportBatch) => setHistory((current) => [batch, ...current.filter((item) => item.id !== batch.id)]);
  const recordAnalysis = (run: AnalysisRun) => setAnalyses((current) => [run, ...current.filter((item) => item.id !== run.id)]);
  const recordSemanticRun = (run: SemanticRun) => setSemanticRuns((current) => [run, ...current.filter((item) => item.id !== run.id)]);
  const recordProposalRun = (run: ProposalRun) => setProposalRuns((current) => [run, ...current.filter((item) => item.id !== run.id)]);

  return <div className="app-shell">
    <ProjectSidebar active={page} onNavigate={setPage} />
    {page === "import" && <ImportPage health={health} summary={summary} history={history} initialError={error} loadingInitial={loading} onImported={recordImport} />}
    {page === "analysis" && <AnalysisPage latestBatch={history[0] ?? null} latestRun={analyses[0] ?? null} onImported={recordImport} onAnalyzed={recordAnalysis} />}
    {page === "projects" && <ProjectsPage latestBatch={history[0] ?? null} latestAnalysis={analyses[0] ?? null} latestSemanticRun={semanticRuns[0] ?? null} capability={capability} onImported={recordImport} onAnalyzed={recordAnalysis} onSemanticRun={recordSemanticRun} />}
    {page === "proposals" && <ProposalsPage latestBatch={history[0] ?? null} latestAnalysis={analyses[0] ?? null} latestSemanticRun={semanticRuns[0] ?? null} latestProposalRun={proposalRuns[0] ?? null} capability={capability} onImported={recordImport} onAnalyzed={recordAnalysis} onSemanticRun={recordSemanticRun} onProposalRun={recordProposalRun} />}
  </div>;
}
