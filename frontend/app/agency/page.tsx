import Link from "next/link";
import { getDashboardSummary, getDashboardTrends, getApplicantIntelligence } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AgencyPage() {
  const [summary, trends, sarah] = await Promise.all([getDashboardSummary(), getDashboardTrends(), getApplicantIntelligence("A-DEMO-SARAH")]);
  const actions = trends.next_best_actions.slice(0, 3);
  return <>
    <section className="agency-welcome"><div><div className="eyebrow">Monday · Agency overview</div><h1>Good morning.</h1><p className="lead">Three signals need attention today. Start with the people most likely to move.</p></div><Link href="/agency/search" className="button">Open intelligence search</Link></section>
    <section className="priority-grid">
      <Link href="/agency/applicants/A-DEMO-SARAH" className="priority-card priority-featured"><div className="priority-top"><span className="signal-dot" /> High intent</div><h2>Sarah Mitchell</h2><p>99.5% match for P-DEMO-01 · Canary Wharf</p><div className="priority-action">{sarah.recommended_action.action.replaceAll("_", " ")} <b>→</b></div></Link>
      {actions.map((action) => <Link href="/agency/recommendations" className="priority-card" key={action.action}><div className="priority-top"><span className="signal-dot signal-amber" /> Recommended action</div><h2>{action.action.replaceAll("_", " ")}</h2><p>{action.count} applicants or properties are associated with this action.</p><span className="text-link">Review queue →</span></Link>)}
    </section>
    <section className="section-heading"><div><div className="eyebrow">Operational picture</div><h2>What is moving through the agency</h2></div><Link href="/agency/intelligence" className="text-link">View intelligence layer →</Link></section>
    <div className="metric-strip"><div><span>Active applicants</span><strong>{summary.active_applicants}</strong></div><div><span>High-intent applicants</span><strong>{summary.high_intent_applicants}</strong></div><div><span>Property enquiries</span><strong>{summary.upcoming_viewings}</strong></div><div><span>Applications</span><strong>{summary.applications}</strong></div></div>
    <section className="agency-lower"><div className="card operational-card"><div className="section-heading"><h2>Today’s focus</h2><span className="badge high">Live from synthetic CRM</span></div><div className="focus-row"><span className="focus-number">01</span><div><strong>Move high-intent applicants forward</strong><p className="muted">Sarah has completed viewings, positive feedback and application activity.</p></div><Link href="/agency/applicants/A-DEMO-SARAH" className="text-link">Open profile →</Link></div><div className="focus-row"><span className="focus-number">02</span><div><strong>Inspect evidence before contacting</strong><p className="muted">Every recommendation can be traced to a source record and indexed chunk.</p></div><Link href="/agency/search" className="text-link">Inspect RAG →</Link></div></div><div className="card"><div className="eyebrow">Signal summary</div><h2>Intent distribution</h2>{trends.intent_distribution.slice(0, 5).map((row) => <div className="signal-bar" key={row.intent}><div><span>{row.intent}</span><strong>{row.count}</strong></div><div className="bar"><span style={{ width: `${Math.min(100, row.count / Math.max(Number(summary.total_applicants) / 100, 1))}%` }} /></div></div>)}</div></section>
  </>;
}
