# VIDYAVERIFY AI — Technical Deliverables & Judge Overview

**Problem Statement SIH26263:** Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions.  
**Product Tagline:** *Verify Every Record. Build Trusted Education.*

---

## 1. System Architecture & Component Mapping

```
+-----------------------------------------------------------------------------------------+
|                                    VIDYAVERIFY AI UI                                    |
|   Next.js 16 + React 19 + TypeScript + Tailwind CSS v4 + @xyflow/react + Lucide Icons   |
+-----------------------------------------------------------------------------------------+
              |                                                     |
        (HTTP/JSON)                                            (HTTP/JSON)
              v                                                     v
+-----------------------------------------------------------------------------------------+
|                                  FastAPI Backend (v1)                                   |
|   - OAuth2 / JWT Authentication (Role-based access control: SUPER_ADMIN, AICTE_ADMIN,   |
|     INSTITUTION_ADMIN, FRAUD_ANALYST, AUDITOR)                                          |
|   - Institution-Level Row Security & Data Scoping                                       |
|   - Layered Anomaly & Duplicate Engine (Layer 1: Exact APAAR, Layer 2: RapidFuzz)       |
|   - Explainable Risk Engine (0-100, Intake violation & cross-institution weights)       |
|   - Verification Adapter (DEMO_SIMULATOR with synthetic provider outcomes)              |
|   - AI Compliance Copilot (Deterministic parameter query fallback + LLM integration)    |
|   - Immutable Audit Logging Service                                                     |
+-----------------------------------------------------------------------------------------+
                                            |
                                  (SQLAlchemy 2.0 ORM)
                                            v
+-----------------------------------------------------------------------------------------+
|                                PostgreSQL Database Engine                               |
|   - 25 Institutions, 12 Courses, 300 Intake Approvals, 22,153 Student Records           |
|   - 60 Batches, 200 Validation Issues, 200 Duplicate Candidates, 30 Cases, 101 Verifs   |
|   - 100% Deterministic Seeded Synthetic Demonstration Data                              |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Feature-to-Problem-Statement SIH26263 Matrix

| Problem Statement Requirement | VIDYAVERIFY AI Implementation | File Reference |
| :--- | :--- | :--- |
| **APAAR ID Ingestion & Validation** | Smart Upload Studio with schema auto-mapping, row-level format checking, duplicate check, and batch versioning. | [upload/page.tsx](file:///Users/devanshjain06/Desktop/VIDYAVERIFY%20AI/frontend/src/app/upload/page.tsx) |
| **Intake Ceiling Enforcement (AICTE Sec 10k)** | Deterministic validation flagging over-enrolment against configured intake caps with instant discrepancy alerts. | [validation/page.tsx](file:///Users/devanshjain06/Desktop/VIDYAVERIFY%20AI/frontend/src/app/validation/page.tsx) |
| **Cross-Institution Duplicate Detection** | Multi-layer detection: Layer 1 exact normalized APAAR, Layer 2 RapidFuzz token matching; manual analyst review required. | [duplicates/page.tsx](file:///Users/devanshjain06/Desktop/VIDYAVERIFY%20AI/frontend/src/app/duplicates/page.tsx) |
| **Explainable Risk Intelligence** | 0–100 scored risk bands (Low, Medium, High, Critical) with transparent itemized evidence penalties. | [risk/page.tsx](file:///Users/devanshjain06/Desktop/VIDYAVERIFY%20AI/frontend/src/app/risk/page.tsx) |
| **Academic Trust Graph** | Interactive node-edge visualization with @xyflow/react tracing Institutions, Students, Batches, Conflicts, and Approvals. | [graph/page.tsx](file:///Users/devanshjain06/Desktop/VIDYAVERIFY%20AI/frontend/src/app/graph/page.tsx) |
| **Investigation & Institutional Clarification** | End-to-end case workflow with evidence review, institutional response threads, and justification recording. | [cases/page.tsx](file:///Users/devanshjain06/Desktop/VIDYAVERIFY%20AI/frontend/src/app/cases/page.tsx) |
| **AI Compliance Copilot** | Role-scoped conversational assistant with deterministic query tools and clear fallback disclosure. | [copilot/page.tsx](file:///Users/devanshjain06/Desktop/VIDYAVERIFY%20AI/frontend/src/app/copilot/page.tsx) |
| **Verification Adapter** | Provider-independent adapter with simulated outcomes, avoiding fake government API claims. | [verification/page.tsx](file:///Users/devanshjain06/Desktop/VIDYAVERIFY%20AI/frontend/src/app/verification/page.tsx) |
| **Immutable Governance Audit Log** | Append-only audit trail logging every actor, role, timestamp, entity reference, and rationale. | [audit/page.tsx](file:///Users/devanshjain06/Desktop/VIDYAVERIFY%20AI/frontend/src/app/audit/page.tsx) |

---

## 3. Demonstration Workflow (5-Minute SIH Presentation)

1. **Sign-In:** Log in as `aicte.admin@vidyaverify.ai` (Password: `Demo@2026`) or `super.admin@vidyaverify.ai`.
2. **Command Centre:** Observe live database metrics: 25 Institutions, 22,153 Students, intake capacity reconciliation, and risk breakdown.
3. **Smart Upload Studio:** Click *Upload New Batch*, select *Clean Sample* or *Imperfect Sample*, and run validation to inspect deterministic row errors.
4. **Validation & Reconciliation:** Review the Section 10(k) intake comparison table where excess enrolments are flagged in red. Resolve an issue with justification note.
5. **Duplicate Registry:** Inspect Layer 1 and Layer 2 matches. Filter by *Cross-institution only*. Review and mark decision without automated destructive merges.
6. **Academic Trust Graph:** Select an institution to visualize student enrolments, course approvals, and conflicts with interactive pan/zoom.
7. **AI Copilot & Audit Trail:** Ask the Copilot to summarize unresolved intake discrepancies, then open the Audit Trail to verify the immutable log.
