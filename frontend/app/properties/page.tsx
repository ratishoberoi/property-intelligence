import Link from "next/link";
import { getProperties } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function PropertiesPage() {
  const properties = await getProperties();
  return (
    <>
      <div className="hero">
        <div>
          <div className="eyebrow">Properties</div>
          <h1>Stock performance and demand.</h1>
        </div>
      </div>
      <section className="card">
        <table className="table">
          <thead><tr><th>Property</th><th>Area</th><th>Rent</th><th>Bedrooms</th><th>Amenities</th></tr></thead>
          <tbody>
            {properties.map((property) => (
              <tr key={property.property_id}>
                <td><Link href={`/properties/${property.property_id}`}><strong>{property.property_id}</strong></Link><div className="muted">{property.property_type}</div></td>
                <td>{property.area}</td>
                <td>£{property.rent_pcm.toLocaleString()}</td>
                <td>{property.bedrooms}</td>
                <td>{property.amenities.replaceAll("|", ", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
