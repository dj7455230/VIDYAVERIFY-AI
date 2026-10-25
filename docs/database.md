# VIDYAVERIFY AI — Database Design

## Overview

PostgreSQL 18 with 23 normalized tables. All timestamps are UTC. Soft deletion is used only where appropriate and documented.

## Entity Relationship Summary

### Core Entities
- **users** — Authenticated users with role assignments
- **roles** — System roles (SUPER_ADMIN, AICTE_ADMIN, INSTITUTION_ADMIN, FRAUD_ANALYST, AUDITOR)
- **user_roles** — Many-to-many between users and roles
- **institutions** — Fictional educational institutions
- **institution_user_memberships** — Maps users to accessible institutions
- **academic_years** — Academic year definitions
- **courses** — Course definitions

### Academic Records
- **institution_approvals** — Institution approval records per academic year
- **intake_approvals** — Approved intake per course per institution per year
- **student_records** — Student academic records (fictional APAAR references)
- **enrolments** — Course enrolment records

### Submissions and Validation
- **submission_batches** — Versioned submission batches
- **submission_file_metadata** — Uploaded file metadata (files stored outside public dir)
- **validation_issues** — Detected validation issues with codes, severity, evidence

### Intelligence
- **duplicate_candidates** — Potential duplicate pairs with match layers and scores
- **risk_cases** — Risk cases with explainable scores and factors
- **risk_factors** — Contributing factors to a risk score
- **risk_score_history** — History of risk score changes

### Investigations
- **investigation_cases** — Investigation cases with state machine
- **case_evidence** — Evidence items linked to cases
- **case_actions** — Action history (audit trail per case)

### Verification
- **student_identity_checks** — Identity verification checks
- **verification_requests** — Verification request records
- **verification_events** — Event log per verification request

### Workflow
- **clarification_requests** — Clarification requests to institutions

### Governance
- **audit_logs** — Append-only audit log (no updates or deletes)
- **notifications** — In-app notifications
- **integration_events** — External integration interaction log
- **configuration_settings** — Key-value configuration

## Key Constraints

- `student_records.apaar_reference` — UNIQUE, indexed
- `institutions.code` — UNIQUE, indexed
- `intake_approvals` — Unique per (institution, course, academic_year)
- `institution_approvals` — Unique per (institution, academic_year)
- `audit_logs` — Append-only (no UPDATE or DELETE)
- `student_records.is_synthetic` — Always true in demo mode

## Indexes

Key indexes are created on:
- All foreign keys
- Common search fields (code, name, status, email)
- Composite indexes for common query patterns:
  - `ix_student_inst_ay` — (institution_id, academic_year_id)
  - `ix_student_inst_course_ay` — (institution_id, course_id, academic_year_id)
  - `ix_enrol_inst_course_ay` — (institution_id, course_id, academic_year_id)

## Migrations

Managed with Alembic:
```bash
cd backend
alembic upgrade head      # Apply all migrations
alembic downgrade -1      # Roll back one migration
alembic revision --autogenerate -m "description"  # Generate new migration
```
