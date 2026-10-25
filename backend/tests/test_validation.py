"""Tests for validation and risk scoring."""

import pytest
from app.security.auth import hash_password
from app.models.user import User, Role
from app.models.student import StudentRecord
from app.models.submission import SubmissionBatch, SubmissionFileMetadata
import os
import json


def test_risk_score_bounds():
    """Test that risk score calculation stays within 0-100."""
    from app.api.v1.risk import calculate_risk_score

    # Empty factors → score 0
    score, band, details = calculate_risk_score([])
    assert score == 0
    assert band == "low"

    # Single factor
    score, band, details = calculate_risk_score([
        {"rule_code": "CROSS_INSTITUTION_CONFLICT", "is_active": True, "description": "test"}
    ])
    assert score == 35
    assert band == "medium"

    # Multiple factors that would exceed 100
    score, band, details = calculate_risk_score([
        {"rule_code": "CROSS_INSTITUTION_CONFLICT", "is_active": True, "description": "test"},
        {"rule_code": "INTAKE_EXCEEDED", "is_active": True, "description": "test"},
        {"rule_code": "UNRESOLVED_VERIFICATION", "is_active": True, "description": "test"},
        {"rule_code": "ACADEMIC_FIELD_INCONSISTENCY", "is_active": True, "description": "test"},
        {"rule_code": "UNUSUAL_REPORTING_PATTERN", "is_active": True, "description": "test"},
    ])
    assert score <= 100
    assert band == "critical"
    assert score == 100  # 35+30+15+10+10 = 100, capped at 100


def test_risk_score_no_double_counting():
    """Test that duplicate rule codes are not double-counted."""
    from app.api.v1.risk import calculate_risk_score

    score, band, details = calculate_risk_score([
        {"rule_code": "CROSS_INSTITUTION_CONFLICT", "is_active": True, "description": "test"},
        {"rule_code": "CROSS_INSTITUTION_CONFLICT", "is_active": True, "description": "duplicate"},
    ])
    assert score == 35  # Only counted once


def test_risk_score_bands():
    """Test risk band classification."""
    from app.api.v1.risk import calculate_risk_score

    # Low: 0-30
    score, band, _ = calculate_risk_score([{"rule_code": "ACADEMIC_FIELD_INCONSISTENCY", "is_active": True}])
    assert score == 10
    assert band == "low"

    # Medium: 31-60
    score, band, _ = calculate_risk_score([{"rule_code": "CROSS_INSTITUTION_CONFLICT", "is_active": True}])
    assert score == 35
    assert band == "medium"

    # High: 61-80
    score, band, _ = calculate_risk_score([
        {"rule_code": "CROSS_INSTITUTION_CONFLICT", "is_active": True},
        {"rule_code": "INTAKE_EXCEEDED", "is_active": True},
    ])
    assert score == 65
    assert band == "high"

    # Critical: 81-100
    score, band, _ = calculate_risk_score([
        {"rule_code": "CROSS_INSTITUTION_CONFLICT", "is_active": True},
        {"rule_code": "INTAKE_EXCEEDED", "is_active": True},
        {"rule_code": "UNRESOLVED_VERIFICATION", "is_active": True},
        {"rule_code": "ACADEMIC_FIELD_INCONSISTENCY", "is_active": True},
    ])
    assert score == 90
    assert band == "critical"


def test_duplicate_name_normalization():
    """Test that name normalization works for duplicate detection."""
    from app.api.v1.duplicates import _normalize_name

    assert _normalize_name("  Aarav   Sharma ") == "aarav sharma"
    assert _normalize_name("Diya Verma") == "diya verma"
    assert _normalize_name("") == ""
    assert _normalize_name("  Multiple   Spaces  Here  ") == "multiple spaces here"


def test_csv_parsing():
    """Test that CSV files can be parsed correctly."""
    import pandas as pd
    import io

    csv_content = """apaar_reference,student_name,date_of_birth
APR2025000001SYN,Aarav Sharma,2003-05-15
APR2025000002SYN,Diya Verma,2003-08-22"""

    df = pd.read_csv(io.StringIO(csv_content), dtype=str, keep_default_na=False)
    assert len(df) == 2
    assert "apaar_reference" in df.columns
    assert df.iloc[0]["student_name"] == "Aarav Sharma"
