# Test Matrix

| ID | Area | Test | Expected | Actual | Status |
|---|---|---|---|---|---|
| AUTH-001 | Demo access | Landing to Agency | Agency shell and nav | Verified in browser | PASS |
| AUTH-002 | Demo access | Landing to Client | Client shell and nav | Verified in browser | PASS |
| CLIENT-001 | Onboarding | Submit Sarah preferences | API matching returns ranked results | Verified by API/UI | PASS |
| CLIENT-002 | Matching | Exact demo constraints | P-DEMO properties rank with reasons | Verified | PASS |
| CLIENT-003 | Empty state | Impossible constraints | Empty result, no fabricated match | API contract verified | PASS |
| CLIENT-004 | Property | Open P-DEMO-01 | DB-backed details render | Browser verified | PASS |
| WORKFLOW-001 | Save | Save property | Persisted saved row | Verified via workflow state | PASS |
| WORKFLOW-002 | Viewing | Client request | Pending row and event | Verified live | PASS |
| WORKFLOW-003 | Viewing | Agency confirm | Client receives confirmed status | Verified live UI loop | PASS |
| WORKFLOW-004 | Application | Submit and agency update | Shared status | `SUBMITTED → UNDER_REVIEW → APPROVED`, client reflection verified | PASS |
| RAG-001 | Retrieval | Client property question | Real citations and grounded answer | Verified through workflow API | PASS |
| RAG-002 | Grounding | Unsupported personal facts | Refusal, no unsupported claim | Dedicated tests added | PASS |
| RAG-003 | Provenance | Citation to source | Source record and chunk resolve | Existing provenance suite/API | PASS |
| AGENCY-001 | Inbox | Pending viewing appears | Agency inbox row | Verified live | PASS |
| AGENCY-002 | Applicant | Sarah workflow summary | Shared activity visible | Browser/API verified | PASS |
| DATA-001 | Reset | Reset demo | Canonical saved/confirmed/under-review state | Verified via API | PASS |
| UI-001 | Responsive | Desktop/mobile routes | No known overflow on tested routes | Prior browser checks pass | PASS |
| QA-001 | Backend | `pytest` | All tests pass | 6 passed | PASS |
| QA-002 | Frontend | lint/typecheck/build | Clean build | lint/typecheck/build passed | PASS |
| DEPLOY-001 | Docker | Compose runtime | Requires Compose plugin | Blocked: host lacks plugin/legacy binary | BLOCKED |
| DEPLOY-002 | Docker | Backend image build | Image builds | `property-intelligence-backend-audit` built | PASS |
| DEPLOY-003 | Docker | Frontend image build | Image builds | `property-intelligence-frontend-audit` built | PASS |

## Audit note

The API-level client→agency→client rehearsal passed end to end, including viewing and application status transitions. Browser route/responsive checks passed at 1440, 1280, 1024, 768 and 390 pixels with no overflow. A longer browser click rehearsal exposed local single-worker saturation during repeated SSR intelligence navigation; this is recorded as a performance limitation rather than marked as silently passing.
