import type { Applicant, ApplicantIntelligence, Property, PropertyIntelligence } from "@/types/domain";

const API_BASE = typeof window === "undefined"
  ? (process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL)
  : process.env.NEXT_PUBLIC_API_BASE_URL;

function apiUrl(path: string): string {
  if (!API_BASE) {
    throw new Error("API URL is not configured. Set NEXT_PUBLIC_API_BASE_URL.");
  }
  return `${API_BASE}${path}`;
}

async function get<T>(path: string): Promise<T> {
  const response = await fetch(apiUrl(path), { next: { revalidate: 15 } });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function getDashboardSummary() {
  return get<Record<string, number | string>>("/api/dashboard/summary");
}

export async function getDashboardTrends() {
  return get<{
    funnel: Array<{ stage: string; count: number }>;
    intent_distribution: Array<{ intent: string; count: number }>;
    next_best_actions: Array<{ action: string; count: number }>;
    conversion_trends: Array<{ week: string; conversion: number }>;
  }>("/api/dashboard/trends");
}

export async function getApplicants() {
  return get<Applicant[]>("/api/applicants?limit=100");
}

export async function getApplicant(id: string) {
  return get<Applicant>(`/api/applicants/${id}`);
}

export async function getApplicantTimeline(id: string) {
  return get<Array<{ interaction_id: string; timestamp: string; event_type: string; channel: string; message: string; sentiment: number }>>(`/api/applicants/${id}/timeline`);
}

export async function getApplicantIntelligence(id: string) {
  return get<ApplicantIntelligence>(`/api/applicants/${id}/intelligence`);
}

export async function getProperties() {
  return get<Property[]>("/api/properties?limit=100");
}

export async function getProperty(id: string) {
  return get<Property>(`/api/properties/${id}`);
}

export async function getPropertyIntelligence(id: string) {
  return get<PropertyIntelligence>(`/api/properties/${id}/intelligence`);
}

export async function postSearch(query: string, applicantId?: string, propertyId?: string) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 20000);
  let response: Response;
  try {
    response = await fetch(apiUrl("/api/search"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ query, applicant_id: applicantId, property_id: propertyId, limit: 8 }),
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw new Error("Search timed out after 20 seconds. Try a narrower question.");
    throw new Error("Search service is unavailable. Check the local backend.");
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    const message = typeof detail?.detail === "object" ? detail.detail.message : detail?.message ?? detail?.detail;
    throw new Error(message || `Search failed: ${response.status}`);
  }
  return response.json();
}

export async function getRagProvenance(citationId: string, query: string) {
  return get<any>(`/api/rag/provenance/${citationId}?query=${encodeURIComponent(query)}`);
}

export async function postClientMatches(preferences: { budget_max: number; preferred_areas: string; bedrooms_required: number; amenities_preferences: string; move_in_date: string }) {
  const response = await fetch(`${API_BASE}/api/matching/client`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ applicant_id: "A-DEMO-SARAH", limit: 8, ...preferences }) });
  if (!response.ok) throw new Error("We could not refresh your matches.");
  return response.json();
}

export type WorkflowState = {
  preferences: { budget_max: number; preferred_areas: string; bedrooms_required: number; move_in_date: string; amenities_preferences: string } | null;
  saved_properties: Array<{ saved_id: string; property_id: string; created_at: string }>;
  viewing_requests: Array<{ request_id: string; property_id: string; property_area: string; rent_pcm: number; status: string; preferred_at: string | null; proposed_at: string | null; created_at: string; confirmed_at: string | null; client_message?: string }>;
  applications: Array<{ application_id: string; property_id: string; property_area: string; rent_pcm: number; status: string; created_at: string; updated_at: string; client_message?: string }>;
  activity: Array<{ event_id: string; event_type: string; message: string; property_id: string | null; property_area: string | null; created_at: string }>;
};

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(apiUrl(path), { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body), signal: controller.signal });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw new Error("The request timed out. Please try again.");
    throw error;
  } finally { window.clearTimeout(timeout); }
}

async function patchJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(apiUrl(path), { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export function getClientWorkflow(applicantId = "A-DEMO-SARAH") { return get<WorkflowState>(`/api/workflow/client/${applicantId}`); }
export function postWorkflowPreferences(body: { applicant_id?: string; budget_max: number; preferred_areas: string; bedrooms_required: number; amenities_preferences: string; move_in_date: string }) { return postJson(`/api/workflow/preferences`, body); }
export function postSaveProperty(propertyId: string, saved: boolean, applicantId = "A-DEMO-SARAH") { return postJson<{ status: string; property_id: string }>("/api/workflow/saved", { applicant_id: applicantId, property_id: propertyId, saved }); }
export function postViewingRequest(propertyId: string, preferredAt?: string, clientMessage = "", applicantId = "A-DEMO-SARAH") { return postJson<{ status: string }>("/api/workflow/viewings", { applicant_id: applicantId, property_id: propertyId, preferred_at: preferredAt, client_message: clientMessage }); }
export function postApplication(propertyId: string, clientMessage = "", applicantId = "A-DEMO-SARAH") { return postJson("/api/workflow/applications", { applicant_id: applicantId, property_id: propertyId, client_message: clientMessage }); }
export function postClientQuestion(propertyId: string, question: string, applicantId = "A-DEMO-SARAH") { return postJson<{ answer: string; evidence: string[]; inference: string[]; citations: any[] }>("/api/workflow/questions", { applicant_id: applicantId, property_id: propertyId, question }); }
export function getAgencyInbox() { return get<{ viewing_requests: any[]; applications: any[]; questions: any[] }>("/api/workflow/agency/inbox"); }
export function patchViewing(requestId: string, status: string, note = "", proposedAt?: string) { return patchJson(`/api/workflow/viewings/${requestId}`, { status, note, proposed_at: proposedAt }); }
export function patchApplication(applicationId: string, status: string, note = "") { return patchJson(`/api/workflow/applications/${applicationId}`, { status, note }); }
export function resetDemo() { return postJson("/api/workflow/reset", {}); }
