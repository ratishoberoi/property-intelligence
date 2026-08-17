import Link from "next/link";
import { getApplicants } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ApplicantsPage() {
  const applicants = await getApplicants();
  return (
    <>
      <div className="hero">
        <div>
          <div className="eyebrow">Applicants</div>
          <h1>Applicant intelligence queue.</h1>
        </div>
        <Link className="button" href="/applicants/A-DEMO-SARAH">Sarah Mitchell Demo</Link>
      </div>
      <section className="card">
        <table className="table">
          <thead><tr><th>Name</th><th>Budget</th><th>Areas</th><th>Bedrooms</th><th>Requirements</th></tr></thead>
          <tbody>
            {applicants.map((applicant) => (
              <tr key={applicant.applicant_id}>
                <td><Link href={`/applicants/${applicant.applicant_id}`}><strong>{applicant.name}</strong></Link><div className="muted">{applicant.applicant_id}</div></td>
                <td>£{applicant.budget_min.toLocaleString()}-£{applicant.budget_max.toLocaleString()}</td>
                <td>{applicant.preferred_areas.replaceAll("|", ", ")}</td>
                <td>{applicant.bedrooms_required}</td>
                <td>{applicant.amenities_preferences.replaceAll("|", ", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
