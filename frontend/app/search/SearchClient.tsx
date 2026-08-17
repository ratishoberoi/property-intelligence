"use client";

import { useState } from "react";
import Link from "next/link";
import { getRagProvenance, postSearch } from "@/lib/api";

export function SearchClient({ applicantId }: { applicantId?: string }) {
  const [query, setQuery] = useState("Why is Sarah a strong candidate for this property?");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [provenance, setProvenance] = useState<any>(null);
  const [provenanceLoading, setProvenanceLoading] = useState<string | null>(null);

  function submit() {
    setError(null);
    setResult(null);
    setProvenance(null);
    setPending(true);
    postSearch(query, applicantId)
      .then(setResult)
      .catch((err) => setError(err instanceof Error ? err.message : "Search failed"))
      .finally(() => setPending(false));
  }

  return (
    <div className="stack">
      <section className="card">
        <div className="searchbox">
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask about applicants, properties, demand or next actions" />
          <button className="button" onClick={submit} disabled={pending}>{pending ? "Searching..." : "Search"}</button>
        </div>
        <div className="split query-chips" style={{ marginTop: 12 }}>
          {["Find similar properties under £2800.", "Why is Sarah a high-value applicant?", "Which applicants should I contact today?", "Which properties have high demand but low application conversion?"].map((sample) => (
            <button className="button secondary" key={sample} onClick={() => setQuery(sample)}>{sample}</button>
          ))}
        </div>
      </section>
      {error ? <section className="card error-state"><strong>Search unavailable</strong><p className="muted">{error}</p><button className="button secondary" onClick={submit}>Retry</button></section> : null}
      {pending ? <section className="card loading-state"><strong>Running intelligence pipeline…</strong><p className="muted">Retrieving evidence, ranking candidates and preparing a grounded response.</p></section> : null}
      {result ? (
        <section className="card">
          <div className="insight-heading"><span className="badge high">AI INSIGHT</span><span className="muted">Grounded intelligence response</span></div>
          <h2>Answer</h2>
          <p className="insight-copy">{result.answer}</p>
          {result.generation ? <>
            <div className="generation-grid"><div><span className="label">EVIDENCE</span><p>{result.generation.evidence?.length ? result.generation.evidence.join(" ") : "No evidence was returned."}</p></div><div><span className="label">INFERENCE</span><p>{result.generation.inference}</p></div><div><span className="label">ACTION</span><p>{result.generation.action}</p></div></div>
            <div className="pipeline"><span>Query</span><b>→</b><span>Filters</span><b>→</b><span>Vector + lexical</span><b>→</b><span>Hybrid rerank</span><b>→</b><span>Cited answer</span></div>
          </> : null}
          {result.retrieval ? <details className="technical"><summary>Retrieval diagnostics</summary><div className="diagnostic-grid">{Object.entries(result.retrieval).map(([key, value]) => <div key={key}><span className="label">{key.replaceAll("_", " ")}</span><strong>{String(value)}</strong></div>)}</div></details> : null}
          {result.properties?.length ? <h2>Ranked Properties</h2> : null}
          <div className="stack">
            {result.properties?.map((match: any) => (
              <Link href={`/properties/${match.property.property_id}`} className="result-row" key={match.property.property_id}>
                <span><strong>{match.property.property_id}</strong><small>{match.property.area} · £{match.property.rent_pcm.toLocaleString()} pcm</small></span><span className="badge">{match.match_score}% match</span>
              </Link>
            ))}
          </div>
          {result.applicants?.length ? <h2 style={{ marginTop: 18 }}>Applicants</h2> : null}
          <div className="stack">
            {result.applicants?.map((applicant: any) => (
              <Link href={`/applicants/${applicant.applicant_id}`} key={applicant.applicant_id}>
                <strong>{applicant.name}</strong> · £{applicant.budget_max} · {applicant.preferred_areas}
              </Link>
            ))}
          </div>
          <h2 style={{ marginTop: 18 }}>Evidence</h2>
          <div className="stack">
            {result.citations?.map((citation: any, idx: number) => (
              <div key={idx}>
                <span className="badge">{citation.citation_id} · {citation.document_type.replaceAll("_", " ")}</span>
                <p><strong>{citation.source}</strong>{citation.timestamp ? ` · ${new Date(citation.timestamp).toLocaleDateString()}` : ""}</p>
                <p className="muted">{citation.excerpt}</p>
                <small className="muted">semantic {citation.semantic_score ?? "—"} · lexical {citation.lexical_score ?? "—"} · rerank {citation.rerank_score ?? citation.score}</small>
                <div><button className="button secondary source-button" onClick={async () => { setProvenanceLoading(citation.citation_id); try { setProvenance(await getRagProvenance(citation.citation_id, query)); } finally { setProvenanceLoading(null); } }}>{provenanceLoading === citation.citation_id ? "Loading source…" : "View source record"}</button></div>
              </div>
            ))}
          </div>
          {!result.citations?.length && !result.properties?.length && !result.applicants?.length ? <p className="muted">No matching records or evidence were found for this question.</p> : null}
          {provenance ? <section className="provenance-panel"><div className="insight-heading"><span className="badge high">SOURCE PROVENANCE</span><span className="muted">Database → RAG index → retrieval</span></div><div className="diagnostic-grid"><div><span className="label">SOURCE</span><strong>{provenance.source_type} · {provenance.source_table}</strong></div><div><span className="label">RECORD</span><strong>{provenance.source_record_id}</strong></div><div><span className="label">APPLICANT</span><strong>{provenance.applicant_name ?? "—"}</strong></div><div><span className="label">PROPERTY</span><strong>{provenance.property_id ?? "—"} · {provenance.property_area ?? "—"}</strong></div><div><span className="label">CHANNEL</span><strong>{provenance.channel ?? "—"}</strong></div><div><span className="label">SYNTHETIC DATASET</span><strong>{provenance.synthetic ? "YES" : "NO"}</strong></div></div><h3>Original database record</h3><pre>{JSON.stringify(provenance.source_record, null, 2)}</pre><h3>Indexed RAG chunk</h3><p>{provenance.rag_chunk.chunk_text}</p><div className="diagnostic-grid">{Object.entries(provenance.retrieval).map(([key, value]) => <div key={key}><span className="label">{key.replaceAll("_", " ")}</span><strong>{String(value)}</strong></div>)}</div></section> : null}
        </section>
      ) : null}
    </div>
  );
}
