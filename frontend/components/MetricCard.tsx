export function MetricCard({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <section className="card">
      <div className="label">{label}</div>
      <div className="metric">{value}</div>
      {detail ? <div className="muted">{detail}</div> : null}
    </section>
  );
}

