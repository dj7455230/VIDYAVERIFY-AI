"""Tests for authentication and authorization."""

import pytest


def test_login_success(client, seed_test_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@vidyaverify.ai", "password": "Test@2026"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, seed_test_user):
    """Test login with wrong password."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@vidyaverify.ai", "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@nowhere.com", "password": "pass"},
    )
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@vidyaverify.ai"
    assert "SUPER_ADMIN" in data["roles"]


def test_get_current_user_no_token(client):
    """Test accessing protected endpoint without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Test accessing protected endpoint with invalid token."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken123"},
    )
    assert response.status_code == 401


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "VIDYAVERIFY AI"


def test_dashboard_requires_auth(client):
    """Test that dashboard requires authentication."""
    response = client.get("/api/v1/dashboard/metrics")
    assert response.status_code == 401


def test_dashboard_with_auth(client, auth_headers):
    """Test dashboard with authentication."""
    response = client.get("/api/v1/dashboard/metrics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "total_institutions" in data["metrics"]
