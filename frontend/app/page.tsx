import Link from "next/link";

export default function Home() {
  return (
    <main className="landing-page">
      <div className="landing-nav"><Link href="/" className="brand-mark"><span className="brand-symbol">PI</span><span><strong>Property</strong><strong>Intelligence</strong></span></Link><span className="environment-tag">Demo · Synthetic data</span></div>
      <section className="landing-hero"><div className="eyebrow">Property intelligence, made practical</div><h1>Better decisions for the people finding and letting homes.</h1><p>One intelligence layer for agencies. One clearer way for clients to find a property that fits the way they live.</p></section>
      <section className="role-grid">
        <Link href="/agency" className="role-card role-agency"><span className="role-kicker">For property teams</span><h2>Property Intelligence for your team</h2><p>Understand intent, match applicants, inspect evidence and know what to do next.</p><span className="role-cta">Continue as Agency <b>→</b></span></Link>
        <Link href="/client" className="role-card role-client"><span className="role-kicker">For people searching</span><h2>Find a property that actually fits you</h2><p>Share your priorities once and explore recommendations with clear reasons, not vague scores.</p><span className="role-cta">Continue as Client <b>→</b></span></Link>
      </section>
      <div className="landing-proof"><span>Structured data</span><b>→</b><span>Explainable matching</span><b>→</b><span>Evidence</span><b>→</b><span>Action</span></div>
    </main>
  );
}
