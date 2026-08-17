import Link from "next/link";
import { getApplicantIntelligence, getPropertyIntelligence } from "@/lib/api";
import { ClientPropertyActions } from "@/components/ClientPropertyActions";

export const dynamic = "force-dynamic";

export default async function ClientPropertyPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [intel, applicantIntel] = await Promise.all([getPropertyIntelligence(id), getApplicantIntelligence("A-DEMO-SARAH")]);
  const property = intel.property;
  const match = applicantIntel.top_matches.find((item) => item.property.property_id === id);
  const reasons = match?.explanation.positives.slice(0, 4) || ["This property is in the agency's current synthetic stock."];
  return <>
    <Link href="/client" className="back-link">← Back to your matches</Link>
    <section className="client-detail-hero"><div className="property-visual property-visual-large"><span>Property visual</span><small>Premium synthetic listing preview</small></div><div className="client-detail-summary"><span className="eyebrow">{property.property_type} · {property.area}</span><h1>{property.bedrooms}-bedroom home in {property.area}</h1><p className="rent">£{property.rent_pcm.toLocaleString()} <span>pcm</span></p><div className="property-meta"><span>{property.bedrooms} bedrooms</span><span>{property.bathrooms} bathrooms</span><span>{property.size_sqft} sq ft</span></div>{match && <div className="detail-match"><strong>{match.match_score}%</strong><span>match for Sarah</span></div>}</div></section>
    <div className="client-detail-grid"><section className="card"><div className="eyebrow">Why we think this fits you</div><h2>Aligned with your search</h2><ul className="reason-list">{reasons.map((reason) => <li key={reason}><span>✓</span>{reason}</li>)}</ul><div className="amenity-list">{property.amenities.split("|").map((amenity) => <span className="tag" key={amenity}>{amenity.replaceAll("-", " ")}</span>)}</div></section><section className="card"><div className="eyebrow">Property details</div><h2>At a glance</h2><p>{property.description}</p><dl className="detail-list"><div><dt>Available</dt><dd>{property.available_date}</dd></div><div><dt>Furnished</dt><dd>{property.furnished ? "Yes" : "No"}</dd></div><div><dt>Parking</dt><dd>{property.parking ? "Available" : "Not listed"}</dd></div><div><dt>Pets</dt><dd>{property.pets_allowed ? "Allowed" : "Not listed"}</dd></div></dl></section></div>
    <ClientPropertyActions propertyId={id} />
  </>;
}
