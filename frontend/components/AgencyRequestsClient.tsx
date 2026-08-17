"use client";

import { useEffect, useState } from "react";
import { getAgencyInbox, patchApplication, patchViewing } from "@/lib/api";

type Inbox = { viewing_requests: any[]; applications: any[]; questions: any[] };

export function AgencyRequestsClient() {
  const [inbox, setInbox] = useState<Inbox | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  async function refresh() { try { setError(null); setInbox(await getAgencyInbox()); } catch (reason) { setError(reason instanceof Error ? reason.message : "Inbox unavailable"); } }
  useEffect(() => { refresh(); }, []);
  async function updateViewing(id: string, status: string) { setBusy(id); try { await patchViewing(id, status, status === "CONFIRMED" ? "Confirmed by the agency team." : "Updated by the agency team."); await refresh(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Viewing update failed"); } finally { setBusy(null); } }
  async function updateApplication(id: string, status: string) { setBusy(id); try { await patchApplication(id, status, status === "APPROVED" ? "Application approved by the agency team." : "Application moved to review."); await refresh(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Application update failed"); } finally { setBusy(null); } }
  if (!inbox && !error) return <section className="empty-state">Loading the agency inbox…</section>;
  return <>
    <div className="hero"><div><div className="eyebrow">Operations inbox</div><h1>Requests that need a response.</h1><p className="muted">Client activity is persisted in the shared demo workspace and appears here in real time.</p></div><button className="button secondary" onClick={refresh}>Refresh inbox</button></div>
    {error && <div className="error-state">{error}<button className="text-link" onClick={refresh}>Retry</button></div>}
    <div className="workflow-summary"><span><strong>{inbox?.viewing_requests.length ?? 0}</strong> viewing requests</span><span><strong>{inbox?.applications.length ?? 0}</strong> applications</span><span><strong>{inbox?.questions.length ?? 0}</strong> recent questions</span></div>
    <section className="workflow-section"><div className="section-heading"><div><div className="eyebrow">Viewings</div><h2>New viewing requests</h2></div></div>{inbox?.viewing_requests.length ? inbox.viewing_requests.map((item) => <article className="workflow-item" key={item.request_id}><div><span className="badge high">{item.status}</span><h3>{item.applicant_name} · {item.property_id}</h3><p className="muted">{item.property_area} · £{item.rent_pcm.toLocaleString()} pcm · requested {new Date(item.created_at).toLocaleDateString()}</p><p>{item.client_message || "Client requested a viewing."}</p></div><div className="workflow-actions"><button className="button" disabled={busy === item.request_id} onClick={() => updateViewing(item.request_id, "CONFIRMED")}>Confirm</button><button className="button secondary" disabled={busy === item.request_id} onClick={() => updateViewing(item.request_id, "TIME_PROPOSED")}>Suggest time</button><button className="text-link danger" disabled={busy === item.request_id} onClick={() => updateViewing(item.request_id, "DECLINED")}>Decline</button></div></article>) : <div className="empty-state">No pending viewing requests.</div>}</section>
    <section className="workflow-section"><div className="section-heading"><div><div className="eyebrow">Applications</div><h2>Applications awaiting action</h2></div></div>{inbox?.applications.length ? inbox.applications.map((item) => <article className="workflow-item" key={item.application_id}><div><span className="badge">{item.status}</span><h3>{item.applicant_name} · {item.property_id}</h3><p className="muted">{item.property_area} · £{item.rent_pcm.toLocaleString()} pcm · updated {new Date(item.updated_at).toLocaleDateString()}</p></div><div className="workflow-actions"><button className="button" disabled={busy === item.application_id} onClick={() => updateApplication(item.application_id, "APPROVED")}>Approve</button><button className="button secondary" disabled={busy === item.application_id} onClick={() => updateApplication(item.application_id, "UNDER_REVIEW")}>Review</button></div></article>) : <div className="empty-state">No applications are waiting for review.</div>}</section>
    <section className="workflow-section"><div className="section-heading"><div><div className="eyebrow">Questions</div><h2>Recent client questions</h2></div></div>{inbox?.questions.length ? inbox.questions.map((item) => <article className="workflow-item compact" key={item.event_id}><div><h3>{item.message}</h3><p className="muted">{item.property_id || "Applicant-level"} · {new Date(item.created_at).toLocaleString()}</p></div></article>) : <div className="empty-state">No recent property questions.</div>}</section>
  </>;
}
