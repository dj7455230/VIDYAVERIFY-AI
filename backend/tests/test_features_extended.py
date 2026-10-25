"""Comprehensive integration and security tests for duplicate detection, risk calculation, verification adapter, and audit."""

import pytest
from app.models.student import StudentRecord
from app.models.duplicate import DuplicateCandidate
from app.models.verification import VerificationRequest
from app.models.audit import AuditLog
from app.models.investigation import InvestigationCase


def test_verification_simulator(client, auth_headers, seed_basic_data, db):
    """Test provider-independent verification adapter simulator."""
    data = seed_basic_data
    student = StudentRecord(
        apaar_reference="901200000001",
        student_name="Simulated Student",
        institution_id=data["institution"].id,
        course_id=data["course"].id,
        academic_year_id=data["academic_year"].id,
        admission_status="admitted",
        enrolment_status="active",
        is_synthetic=True,
    )
    db.add(student)
    db.commit()

    # Trigger verification via /api/v1/verification/request
    res = client.post(
        "/api/v1/verification/request",
        json={"student_id": student.id},
        headers=auth_headers,
    )
    assert res.status_code in (200, 201)
    body = res.json()
    assert "status" in body
    assert body.get("provider") == "DEMO_SIMULATOR"


def test_duplicates_listing_and_review(client, auth_headers, seed_basic_data, db):
    """Test duplicate detection query and analyst decision workflow."""
    data = seed_basic_data
    s1 = StudentRecord(
        apaar_reference="901200000002",
        student_name="Candidate One",
        institution_id=data["institution"].id,
        course_id=data["course"].id,
        academic_year_id=data["academic_year"].id,
        admission_status="admitted",
        enrolment_status="active",
        is_synthetic=True,
    )
    s2 = StudentRecord(
        apaar_reference="901200000003",
        student_name="Candidate One Dup",
        institution_id=data["institution"].id,
        course_id=data["course"].id,
        academic_year_id=data["academic_year"].id,
        admission_status="admitted",
        enrolment_status="active",
        is_synthetic=True,
    )
    db.add_all([s1, s2])
    db.commit()

    dup = DuplicateCandidate(
        student_record_id_1=s1.id,
        student_record_id_2=s2.id,
        match_score=98.5,
        match_layer="1",
        match_explanation="Exact APAAR reference match",
        is_cross_institution=False,
        reviewer_decision="unresolved",
    )
    db.add(dup)
    db.commit()

    # List duplicates
    list_res = client.get("/api/v1/duplicates", headers=auth_headers)
    assert list_res.status_code == 200
    items = list_res.json().get("items", [])
    assert any(i["id"] == dup.id for i in items)

    # Review duplicate
    review_res = client.post(
        f"/api/v1/duplicates/{dup.id}/review",
        json={"decision": "confirmed_duplicate", "reason": "Identical APAAR verified"},
        headers=auth_headers,
    )
    assert review_res.status_code == 200
    assert review_res.json()["decision"] == "confirmed_duplicate"


def test_audit_log_query(client, auth_headers):
    """Test audit log endpoint retrieves governance trail."""
    res = client.get("/api/v1/audit", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "items" in body
    assert "total" in body
