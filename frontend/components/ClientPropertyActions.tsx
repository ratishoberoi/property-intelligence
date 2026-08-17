"use client";

import { useEffect, useState } from "react";
import { getClientWorkflow, postApplication, postClientQuestion, postSaveProperty, postViewingRequest } from "@/lib/api";

export function ClientPropertyActions({ propertyId }: { propertyId: string }) {
  const [saved, setSaved] = useState(false);
  const [viewing, setViewing] = useState(false);
  const [viewingStatus, setViewingStatus] = useState<string | null>(null);
  const [application, setApplication] = useState(false);
  const [preferredAt, setPreferredAt] = useState("2026-08-21T16:00");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => { getClientWorkflow().then((state) => { setSaved(state.saved_properties.some((item) => item.property_id === propertyId)); const currentViewing = state.viewing_requests.find((item) => item.property_id === propertyId && ["PENDING", "TIME_PROPOSED", "CONFIRMED"].includes(item.status)); setViewing(Boolean(currentViewing)); setViewingStatus(currentViewing?.status ?? null); setApplication(state.applications.some((item) => item.property_id === propertyId && item.status !== "DECLINED")); }).catch(() => undefined); }, [propertyId]);
  async function save() { setLoading(true); try { const result = await postSaveProperty(propertyId, !saved); setSaved(result.status === "saved"); } catch (error) { setAnswer(error instanceof Error ? error.message : "The property could not be saved."); } finally { setLoading(false); } }
  async function requestViewing() { setLoading(true); try { const result = await postViewingRequest(propertyId, new Date(preferredAt).toISOString(), "Please let me know if another time is more suitable."); setViewing(true); setViewingStatus(result.status); } catch (error) { setAnswer(error instanceof Error ? error.message : "The viewing request could not be sent."); } finally { setLoading(false); } }
  async function apply() { setLoading(true); try { await postApplication(propertyId); setApplication(true); } catch (error) { setAnswer(error instanceof Error ? error.message : "The application could not be submitted."); } finally { setLoading(false); } }
  async function ask() { if (!question.trim()) return; setLoading(true); setAnswer(null); try { const result = await postClientQuestion(propertyId, question); setAnswer(result.answer); } catch (error) { setAnswer(error instanceof Error ? error.message : "The question could not be answered."); } finally { setLoading(false); } }
  return <><div className="property-actions"><button className="button secondary" onClick={save} disabled={loading}>{saved ? "Saved" : "Save property"}</button><button className="button" onClick={requestViewing} disabled={loading}>{viewingStatus === "CONFIRMED" ? "Viewing confirmed" : viewing ? "Viewing requested" : "Request viewing"}</button><button className="button dark-button" onClick={apply} disabled={loading}>{application ? "Application submitted" : "Apply"}</button></div>{!viewing && <label className="inline-field">Preferred viewing time<input type="datetime-local" value={preferredAt} onChange={(event) => setPreferredAt(event.target.value)} /></label>}{viewingStatus === "CONFIRMED" && <div className="workflow-confirmation">Viewing confirmed by the agency team.</div>}<section className="ask-property card"><div><div className="eyebrow">Evidence-backed questions</div><h2>Ask about this property</h2><p className="muted">Answers use the synthetic property and applicant records, with citations available in Agency Search.</p></div><div className="searchbox"><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="e.g. Does this property have good transport?" /><button className="button" onClick={ask} disabled={loading}>{loading ? "Checking…" : "Ask"}</button></div>{answer && <div className="client-answer"><span className="badge high">GROUNDED ANSWER</span><p>{answer}</p></div>}</section></>;
}
