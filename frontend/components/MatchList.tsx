import Link from "next/link";
import type { PropertyMatch } from "@/types/domain";

export function MatchList({ matches }: { matches: PropertyMatch[] }) {
  if (!matches.length) {
    return <div className="card muted">No eligible property matches found for the current constraints.</div>;
  }
  return (
    <div className="stack">
      {matches.map((match) => (
        <Link href={`/properties/${match.property.property_id}`} className="card" key={match.property.property_id}>
          <div className="split" style={{ justifyContent: "space-between" }}>
            <div>
              <strong>{match.property.property_id}</strong>
              <div>{match.property.bedrooms}-bed {match.property.property_type} in {match.property.area}</div>
              <div className="muted">£{match.property.rent_pcm.toLocaleString()} pcm</div>
            </div>
            <span className="badge high">{match.match_score}% match</span>
          </div>
          <div style={{ marginTop: 12 }} className="bar"><span style={{ width: `${match.match_score}%` }} /></div>
          <p className="muted">{match.explanation.positives[0]}</p>
        </Link>
      ))}
    </div>
  );
}

