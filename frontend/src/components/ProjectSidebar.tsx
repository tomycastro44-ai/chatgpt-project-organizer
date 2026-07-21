export type WorkflowPage = "import" | "analysis" | "projects" | "proposals";

interface Props { active: WorkflowPage; onNavigate: (page: WorkflowPage) => void; }

export function ProjectSidebar({ active, onNavigate }: Props) {
  return (
    <aside className="sidebar" aria-label="Project navigation">
      <div className="brand"><span className="brand-mark">O</span><div><strong>Project Organizer</strong><small>Reviewable and reversible</small></div></div>
      <button className={`sidebar-action ${active === "proposals" ? "active-action" : ""}`} type="button" onClick={() => onNavigate("proposals")}>✦ Review organization</button>
      <p className="sidebar-heading">Current workflow</p>
      <nav>
        <button className={`project-link nav-button ${active === "import" ? "active" : ""}`} type="button" onClick={() => onNavigate("import")}><span className="state-dot state-active" /><span>Import</span></button>
        <button className={`project-link nav-button ${active === "analysis" ? "active" : ""}`} type="button" onClick={() => onNavigate("analysis")}><span className="state-dot state-active" /><span>Evidence</span></button>
        <button className={`project-link nav-button ${active === "projects" ? "active" : ""}`} type="button" onClick={() => onNavigate("projects")}><span className="state-dot state-active" /><span>Projects & memory</span></button>
        <button className={`project-link nav-button ${active === "proposals" ? "active" : ""}`} type="button" onClick={() => onNavigate("proposals")}><span className="state-dot state-active" /><span>Proposals & Undo</span></button>
      </nav>
      <div className="sidebar-footer">O.T. 012 reversible workflow<br />Originals remain immutable</div>
    </aside>
  );
}
