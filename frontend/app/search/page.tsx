import { SearchClient } from "./SearchClient";

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ applicant?: string }> }) {
  const params = await searchParams;
  return (
    <>
      <div className="hero">
        <div>
          <div className="eyebrow">Natural Language Search</div>
          <h1>Ask operational questions.</h1>
          <p className="muted">Queries are parsed into applicant/property constraints, matching, retrieval and cited explanations.</p>
        </div>
      </div>
      <SearchClient applicantId={params.applicant} />
    </>
  );
}

