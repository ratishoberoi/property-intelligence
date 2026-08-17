import Link from "next/link";

export default function IntelligencePage() {
  return (
    <>
      <div className="hero">
        <div>
          <div className="eyebrow">System Workflow</div>
          <h1>Applicant to action.</h1>
          <p className="muted">Profile, retrieval, ranking, behaviour analysis, RAG evidence, agent orchestration, next best action.</p>
        </div>
        <Link className="button" href="/applicants/A-DEMO-SARAH">Run Sarah Workflow</Link>
      </div>
      <div className="grid cols-3">
        {["Candidate property retrieval", "Hybrid ranking", "Intent and conversion scoring", "RAG-grounded explanations", "Next-best-action policy", "Final aggregation"].map((item) => (
          <section className="card" key={item}>
            <span className="badge">Implemented</span>
            <h2 style={{ marginTop: 14 }}>{item}</h2>
            <p className="muted">Generated from structured data, model features, retrieval evidence and typed agent outputs.</p>
          </section>
        ))}
      </div>
    </>
  );
}

