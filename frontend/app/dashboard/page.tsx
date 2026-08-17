import Link from "next/link";
import { ConversionLine, FunnelChart, IntentChart } from "@/components/Charts";
import { MetricCard } from "@/components/MetricCard";
import { getDashboardSummary, getDashboardTrends } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [summary, trends] = await Promise.all([getDashboardSummary(), getDashboardTrends()]);
  return (
    <>
      <div className="hero">
        <div>
          <div className="eyebrow">Estate Agency Intelligence Layer</div>
          <h1>Turn fragmented activity into decisions.</h1>
          <p className="muted">Applicant behaviour, property data, viewing feedback and conversations are converted into explainable recommendations.</p>
        </div>
        <Link className="button" href={`/applicants/${summary.demo_applicant_id}`}>Open Demo Applicant</Link>
      </div>

      <div className="grid cols-4">
        <MetricCard label="Total Applicants" value={summary.total_applicants} />
        <MetricCard label="High Intent" value={summary.high_intent_applicants} />
        <MetricCard label="Properties" value={summary.properties} />
        <MetricCard label="Applications" value={summary.applications} />
      </div>

      <div className="grid cols-3" style={{ marginTop: 18 }}>
        <section className="card">
          <h2>Applicant Funnel</h2>
          <FunnelChart data={trends.funnel} />
        </section>
        <section className="card">
          <h2>Intent Distribution</h2>
          <IntentChart data={trends.intent_distribution} />
        </section>
        <section className="card">
          <h2>Conversion Trend</h2>
          <ConversionLine data={trends.conversion_trends} />
        </section>
      </div>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Next Best Action Distribution</h2>
        <table className="table">
          <tbody>
            {trends.next_best_actions.map((row) => (
              <tr key={row.action}>
                <td><strong>{row.action.replaceAll("_", " ")}</strong></td>
                <td>{row.count}</td>
                <td><div className="bar"><span style={{ width: `${Math.min(row.count, 100)}%` }} /></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
