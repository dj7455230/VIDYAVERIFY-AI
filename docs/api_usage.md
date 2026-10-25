# VIDYAVERIFY AI — API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

Interactive docs available at: http://localhost:8000/docs

## Authentication

### Login
```
POST /api/v1/auth/login
Body: { "email": "...", "password": "..." }
Returns: { "access_token", "refresh_token", "token_type": "bearer", "expires_in" }
```

### Get Current User
```
GET /api/v1/auth/me
Headers: Authorization: Bearer <access_token>
```

### Refresh Token
```
POST /api/v1/auth/refresh
Body: { "refresh_token": "..." }
```

### Logout
```
POST /api/v1/auth/logout
Headers: Authorization: Bearer <access_token>
```

## Dashboard
```
GET /api/v1/dashboard/metrics
Query params: academic_year_id, institution_id, course_id, submission_status, risk_band
```

## Institutions
```
GET /api/v1/institutions
GET /api/v1/institutions/{id}
Query params: search, approval_status, academic_year_id, page, page_size
```

## Students
```
GET /api/v1/students
GET /api/v1/students/{id}
Query params: institution_id, course_id, academic_year_id, search, verification_status, page, page_size
```

## Submissions
```
POST /api/v1/submissions/upload (multipart: file, institution_id, academic_year_id)
POST /api/v1/submissions/{batch_id}/map-columns
POST /api/v1/submissions/{batch_id}/validate
GET /api/v1/submissions
GET /api/v1/submissions/{batch_id}
GET /api/v1/submissions/{batch_id}/preview
GET /api/v1/submissions/{batch_id}/issues
POST /api/v1/submissions/{batch_id}/issues/{issue_id}/resolve
```

## Duplicates
```
POST /api/v1/duplicates/detect
GET /api/v1/duplicates
POST /api/v1/duplicates/{candidate_id}/review
Query params: min_score, max_score, decision, cross_institution_only, page, page_size
```

## Risk Cases
```
POST /api/v1/risk/assess/{student_id}
GET /api/v1/risk/cases
GET /api/v1/risk/cases/{case_id}
POST /api/v1/risk/cases/{case_id}/override
Query params: risk_band, status, institution_id, page, page_size
```

## Trust Graph
```
GET /api/v1/graph
Query params: institution_id, student_id, case_id, limit
```

## Investigation Cases
```
GET /api/v1/cases
GET /api/v1/cases/{case_id}
POST /api/v1/cases/{case_id}/assign
POST /api/v1/cases/{case_id}/add-evidence
POST /api/v1/cases/{case_id}/add-note
POST /api/v1/cases/{case_id}/transition
```

## AI Copilot
```
POST /api/v1/copilot/query
Body: { "question": "..." }
Returns: { "answer", "evidence_refs", "provider", "is_llm" }
```

## Verification
```
POST /api/v1/verification/request
GET /api/v1/verification/requests
GET /api/v1/verification/provider-status
```

## Clarifications
```
GET /api/v1/clarifications
POST /api/v1/clarifications
POST /api/v1/clarifications/{id}/respond
```

## Reports (CSV export available with ?export=csv)
```
GET /api/v1/reports/institution-summary
GET /api/v1/reports/intake-reconciliation
GET /api/v1/reports/validation-issues
GET /api/v1/reports/risk-cases
GET /api/v1/reports/audit
```

## Audit
```
GET /api/v1/audit
Query params: action, entity_type, actor_id, outcome, page, page_size
```

## Notifications
```
GET /api/v1/notifications
POST /api/v1/notifications/{id}/read
POST /api/v1/notifications/mark-all-read
```

## Health
```
GET /api/v1/health
GET /api/v1/health/ready
```

## Response Format
All list endpoints return:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## Error Format
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"  // optional
}
```

## Status Codes
- 200: Success
- 201: Created
- 400: Bad request (validation error)
- 401: Unauthorized (invalid/expired token)
- 403: Forbidden (insufficient role or scope)
- 404: Not found
- 413: Payload too large (file upload)
- 422: Unprocessable entity
- 500: Internal error (generic message, no stack trace)
