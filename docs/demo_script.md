# VIDYAVERIFY AI — 5-Minute Demo Script

## Setup (before demo)
```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open http://localhost:3000

## Demo Narrative: Upload → Validate → Detect → Explain → Graph → Copilot → Clarify → Correct → Reconcile → Audit

### Step 1: Login as AICTE Admin (30 sec)
- Go to http://localhost:3000
- Click "AICTE Admin" demo button (password auto-fills)
- Show the Dashboard: 25 institutions, 22K+ student records, cases by risk band
- Point out "SYNTHETIC DEMONSTRATION DATA" label
- Show intake reconciliation table — some courses exceed approved intake

### Step 2: Explore Risk Cases (45 sec)
- Click "Risk Cases" in sidebar
- Filter by "critical" band
- Click a critical case
- Show the risk score breakdown with contributing factors and weights
- Explain: "Each factor has evidence references. The score is deterministic and reproducible."
- Scroll to Score History — show audit trail of score changes

### Step 3: Potential Duplicates (45 sec)
- Click "Duplicates" in sidebar
- Enable "cross-institution only" filter
- Show a duplicate candidate with match score, explanation, and evidence
- Explain: "Similar names alone do not trigger an accusation. Records are NOT merged automatically."
- Demonstrate the review action (confirm / not duplicate / needs review)

### Step 4: Academic Trust Graph (45 sec)
- Click "Trust Graph" in sidebar
- Select an institution from the dropdown
- Show the graph with institution → courses → students → submissions → issues → risk cases
- Point out the dashed red lines for potential conflicts
- Explain: "All nodes and edges come from real database relationships, not a decorative static network."

### Step 5: AI Compliance Copilot (45 sec)
- Click "AI Copilot" in sidebar
- Ask: "Which institutions have the most unresolved validation issues?"
- Show the grounded answer with evidence references
- Point out: "Provider: deterministic_fallback" — no LLM is configured, so it falls back to parameterized queries
- Ask: "Show the intake reconciliation"
- Explain: "The copilot cannot execute arbitrary SQL or bypass authorization."

### Step 6: Upload and Validate (45 sec)
- Click "Upload Studio" in sidebar (login as institution admin first if needed)
- Select an institution and academic year
- Upload a sample CSV file
- Show the header detection and preview
- Click "Run Validation"
- Show the validation results: valid/invalid rows, issues by severity

### Step 7: Audit Trail (30 sec)
- Click "Audit Log" in sidebar
- Show the append-only log with all actions from the demo
- Filter by "login" or "validate_submission"
- Explain: "Every significant operation is recorded. This is append-only — no updates or deletes."

## Key Talking Points
- Evidence-backed, explainable risk scoring (not a black box)
- Institution-level data isolation enforced server-side
- Graph built from real relationships
- Copilot grounded in authorized data with deterministic fallback
- Verification is clearly labelled as simulated
- Full audit trail for all actions
- Before-and-after correction and reconciliation workflow
