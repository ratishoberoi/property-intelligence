import Link from "next/link";
import { MatchList } from "@/components/MatchList";
import { getApplicantIntelligence, getApplicantTimeline, getClientWorkflow } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ApplicantDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [intel, timeline, workflow] = await Promise.all([getApplicantIntelligence(id), getApplicantTimeline(id), getClientWorkflow(id)]);
  const applicant = intel.applicant;
  return (
    <>
      <div className="hero">
        <div>
          <div className="eyebrow">Applicant Profile</div>
          <h1>{applicant.name}</h1>
          <p className="muted">Budget £{applicant.budget_min.toLocaleString()}-£{applicant.budget_max.toLocaleString()} · {applicant.preferred_areas.replaceAll("|", ", ")} · {applicant.bedrooms_required} bedrooms</p>
        </div>
        <Link className="button secondary" href={`/search?applicant=${applicant.applicant_id}`}>Ask About Applicant</Link>
      </div>

      <div className="grid cols-3">
        <section className="card"><div className="label">Intent</div><div className="metric">{intel.intent.intent}</div><span className="badge">{Math.round(intel.intent.confidence * 100)}% confidence</span></section>
        <section className="card"><div className="label">Conversion Probability</div><div className="metric">{Math.round(intel.conversion.conversion_probability * 100)}%</div><p className="muted">Prototype model trained on synthetic labels.</p></section>
        <section className="card"><div className="label">Next Best Action</div><div className="metric" style={{ fontSize: 23 }}>{intel.recommended_action.action.replaceAll("_", " ")}</div><span className="badge high">{intel.recommended_action.priority}</span></section>
      </div>

      <div className="grid cols-2" style={{ marginTop: 18 }}>
        <section>
          <h2>Top Matches</h2>
          <MatchList matches={intel.top_matches} />
        </section>
        <section className="stack">
          <div className="card">
            <h2>Why This Action</h2>
            <p>{intel.recommended_action.reason}</p>
            <p className="muted">{intel.explanation}</p>
          </div>
          <div className="card">
            <h2>Evidence</h2>
            <div className="stack">
              {intel.sources.map((source, idx) => (
                <div key={`${source.source}-${idx}`}>
                  <span className="badge">{source.document_type.replaceAll("_", " ")}</span>
                  <p><strong>{source.source}</strong></p>
                  <p className="muted">{source.excerpt}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Activity Timeline</h2>
        <div className="timeline">
          {timeline.slice(0, 12).map((event) => (
            <div className="timeline-item" key={event.interaction_id}>
              <strong>{event.event_type.replaceAll("_", " ")}</strong>
              <div className="muted">{new Date(event.timestamp).toLocaleDateString()} · {event.channel}</div>
              <p>{event.message}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="card" style={{ marginTop: 18 }}>
        <h2>Shared client workflow</h2>
        <p className="muted">Actions taken in the client portal are persisted here for the agency team.</p>
        <div className="workflow-summary"><span><strong>{workflow.viewing_requests.filter((item) => item.status === "PENDING").length}</strong> pending viewing requests</span><span><strong>{workflow.applications.length}</strong> applications</span><span><strong>{workflow.saved_properties.length}</strong> saved properties</span></div>
        <div className="workflow-row"><strong>Latest client action</strong><span>{workflow.activity[0]?.message || "No recent workflow activity"}</span></div>
      </section>
    </>
  );
}
