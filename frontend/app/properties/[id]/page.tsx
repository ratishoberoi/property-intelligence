import Link from "next/link";
import { getPropertyIntelligence } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function PropertyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const intel = await getPropertyIntelligence(id);
  const property = intel.property;
  return (
    <>
      <div className="hero">
        <div>
          <div className="eyebrow">Property Intelligence</div>
          <h1>{property.property_id}</h1>
          <p className="muted">{property.bedrooms}-bed {property.property_type} in {property.area} · £{property.rent_pcm.toLocaleString()} pcm</p>
        </div>
        <Link className="button secondary" href="/applicants/A-DEMO-SARAH">Compare Sarah</Link>
      </div>
      <div className="grid cols-4">
        <section className="card"><div className="label">Demand</div><div className="metric">{intel.demand}</div></section>
        <section className="card"><div className="label">Qualified Applicants</div><div className="metric">{intel.qualified_applicants}</div></section>
        <section className="card"><div className="label">Strong Matches</div><div className="metric">{intel.strong_matches}</div></section>
        <section className="card"><div className="label">Application Conversion</div><div className="metric">{Math.round(intel.application_conversion * 100)}%</div></section>
      </div>
      <div className="grid cols-2" style={{ marginTop: 18 }}>
        <section className="card">
          <h2>Property Summary</h2>
          <p>{property.description}</p>
          <p><strong>Top concern:</strong> {intel.top_applicant_concern}</p>
          <p><strong>Top preference:</strong> {intel.top_applicant_preference}</p>
          <p><strong>Recommended action:</strong> {intel.recommended_action}</p>
        </section>
        <section className="card">
          <h2>Top Matching Applicants</h2>
          <table className="table">
            <tbody>
              {intel.top_matching_applicants.map((applicant) => (
                <tr key={applicant.applicant_id}>
                  <td><Link href={`/applicants/${applicant.applicant_id}`}><strong>{applicant.name}</strong></Link></td>
                  <td><span className="badge">{applicant.match_score}%</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
      <section className="card" style={{ marginTop: 18 }}>
        <h2>Evidence</h2>
        <p className="muted">Retrieved property activity and viewing evidence supporting this intelligence.</p>
        <div className="stack">
          {intel.sources?.map((source, idx) => (
            <div key={`${source.source}-${idx}`}>
              <span className="badge">{source.document_type.replaceAll("_", " ")}</span>
              <p><strong>{source.source}</strong>{source.timestamp ? ` · ${new Date(source.timestamp).toLocaleDateString()}` : ""}</p>
              <p className="muted">{source.excerpt}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
