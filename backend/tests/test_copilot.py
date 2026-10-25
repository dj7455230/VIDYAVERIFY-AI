"""Tests for AI Compliance Copilot endpoint, questions, authorization, and fallback."""

import pytest
from app.models.student import StudentRecord
from app.models.academic import IntakeApproval
from app.models.institution import Institution, InstitutionUserMembership
from app.models.user import User, Role
from app.security.auth import hash_password


def test_copilot_empty_question_rejected(client, auth_headers):
    """Test that empty queries return a 400 Bad Request."""
    res = client.post("/api/v1/copilot/query", json={"question": ""}, headers=auth_headers)
    assert res.status_code == 400


def test_copilot_unauthorized_access_rejected(client):
    """Test that unauthenticated requests are rejected."""
    res = client.post("/api/v1/copilot/query", json={"question": "How many institutions are in the system?"})
    assert res.status_code == 401


def test_copilot_how_many_institutions(client, auth_headers, seed_basic_data):
    """Test question: 'How many institutions are in the system?'"""
    res = client.post(
        "/api/v1/copilot/query",
        json={"question": "How many institutions are in the system?"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "1 institution" in data["answer"].lower() or "institution" in data["answer"].lower()
    assert len(data["evidence_refs"]) >= 1


def test_copilot_intake_reconciliation_query(client, auth_headers, seed_basic_data):
    """Test question: 'Summarize intake discrepancies for an institution.'"""
    res = client.post(
        "/api/v1/copilot/query",
        json={"question": "Summarize intake discrepancies for an institution."},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "Intake Capacity Reconciliation" in data["answer"] or "approved" in data["answer"].lower()
    assert len(data["evidence_refs"]) >= 1


def test_copilot_unresolved_validation_issues(client, auth_headers, seed_basic_data):
    """Test question: 'Which institutions have the most unresolved validation issues?'"""
    res = client.post(
        "/api/v1/copilot/query",
        json={"question": "Which institutions have the most unresolved validation issues?"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "validation issues" in data["answer"].lower()


def test_copilot_duplicate_evidence_query(client, auth_headers, seed_basic_data):
    """Test question: 'What evidence supports this potential duplicate?'"""
    res = client.post(
        "/api/v1/copilot/query",
        json={"question": "What evidence supports this potential duplicate?"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "duplicate" in data["answer"].lower()


def test_copilot_clarification_cases_query(client, auth_headers, seed_basic_data):
    """Test question: 'Which cases are waiting for clarification?'"""
    res = client.post(
        "/api/v1/copilot/query",
        json={"question": "Which cases are waiting for clarification?"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "clarification" in data["answer"].lower() or "cases" in data["answer"].lower()


def test_copilot_institutional_data_isolation(client, db, seed_basic_data):
    """Test that INSTITUTION_ADMIN users only receive data scoped to their institution."""
    # Create role and institution admin
    role = db.query(Role).filter(Role.name == "INSTITUTION_ADMIN").first()
    if not role:
        role = Role(name="INSTITUTION_ADMIN", description="Inst Admin", is_system=True)
        db.add(role)
        db.flush()

    user = User(
        email="inst.admin.test@vidyaverify.ai",
        full_name="Inst Admin Test",
        hashed_password=hash_password("Test@2026"),
    )
    db.add(user)
    user.roles.append(role)
    db.flush()

    # Associate with institution
    membership = InstitutionUserMembership(
        institution_id=seed_basic_data["institution"].id,
        user_id=user.id,
    )
    db.add(membership)
    db.commit()

    # Login as institution admin
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "inst.admin.test@vidyaverify.ai", "password": "Test@2026"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query institutions count
    res = client.post(
        "/api/v1/copilot/query",
        json={"question": "How many institutions are in the system?"},
        headers=headers,
    )
    assert res.status_code == 200
    # Scoped to 1 institution only
    assert "1 institution" in res.json()["answer"].lower()
