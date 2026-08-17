"use client";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <section className="card"><div className="eyebrow">Unable to load view</div><h2>The intelligence service did not respond.</h2><p className="muted">Check that the local backend is running, then retry.</p><button className="button" onClick={() => reset()}>Retry</button></section>;
}
