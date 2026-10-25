# VIDYAVERIFY AI — Security and Privacy

## Authentication
- JWT-based access and refresh tokens
- bcrypt password hashing (via passlib)
- Token expiration: access (60 min), refresh (7 days)
- Refresh token JTI tracking for revocation
- Account lockout after 5 failed login attempts
- Login and logout events recorded in audit log

## Authorization
- Server-side role enforcement on every protected endpoint
- 5 roles: SUPER_ADMIN, AICTE_ADMIN, INSTITUTION_ADMIN, FRAUD_ANALYST, AUDITOR
- Institution-level data isolation for INSTITUTION_ADMIN role
- No privilege escalation via frontend request modification

## Data Protection
- APAAR references are masked in tables and overview screens (showing first 4 and last 4 chars only)
- No Aadhaar numbers or other unnecessary sensitive identifiers are collected
- Uploaded files stored outside publicly served directories
- No raw student records in public static assets
- Parameterized database access (SQLAlchemy ORM, no raw SQL)

## Audit Trail
- Append-only audit log (no UPDATE or DELETE)
- Records: actor ID, role, action, entity type/ref, outcome, reason, timestamp
- No passwords, tokens, or complete sensitive identifiers logged
- Request correlation ID support

## API Security
- CORS restricted to configured origins
- Input validation via Pydantic schemas
- Output encoding via JSON responses
- No stack-trace leakage (global exception handler returns generic message)
- File upload size limits (configurable, default 10MB)

## Copilot Security
- No arbitrary model-generated SQL execution
- No unrestricted database access
- No bypass of backend authorization
- User input treated as untrusted data, not executable instructions
- Cannot change official records directly
- Grounded in authorized data scope only

## Known Limitations
- No formal regulatory compliance certification
- No rate limiting implemented in this prototype (configurable but not enforced)
- No data retention or deletion policy automation
- Demo credentials are documented for local demonstration only
- The verification provider is a simulated DEMO_SIMULATOR, not a real integration
- Risk scores are illustrative prototype weights, not validated policy or trained models

## What This Prototype Does NOT Claim
- It does not claim official APAAR or AICTE verification
- It does not guarantee detection of all fraudulent records
- It does not replace formal compliance assessment
- It does not connect to any real government system
