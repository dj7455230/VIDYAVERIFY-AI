"""Test configuration and fixtures."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.security.auth import hash_password
from app.models.user import User, Role
from app.models.institution import Institution, InstitutionUserMembership
from app.models.academic import AcademicYear, Course, IntakeApproval, InstitutionApproval
from app.models.student import StudentRecord

# Test database
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://vidyaverify_user:vidyaverify_pass_2026@127.0.0.1:5432/vidyaverify_test",
)

engine = create_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create test database and all tables."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    """Get a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override get_db
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """Test client with database override."""
    return TestClient(app)


@pytest.fixture
def seed_test_user(db):
    """Create a test user with roles."""
    role = Role(name="SUPER_ADMIN", description="Test admin", is_system=True)
    db.add(role)
    db.flush()
    user = User(
        email="test@vidyaverify.ai",
        full_name="Test User",
        hashed_password=hash_password("Test@2026"),
    )
    db.add(user)
    user.roles.append(role)
    db.commit()
    return user


@pytest.fixture
def auth_token(client, seed_test_user):
    """Get an auth token for the test user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@vidyaverify.ai", "password": "Test@2026"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get auth headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def seed_basic_data(db):
    """Seed basic test data: institution, course, academic year, intake."""
    inst = Institution(
        code="TEST001",
        name="Test Institute",
        institution_type="college",
        state="Maharashtra",
        city="Pune",
        is_synthetic=True,
    )
    db.add(inst)

    ay = AcademicYear(year_code="2025-2026", is_active=True)
    db.add(ay)

    course = Course(code="TCS101", name="Test CS Course", course_type="ug", duration_years=4, is_synthetic=True)
    db.add(course)
    db.flush()

    approval = InstitutionApproval(
        institution_id=inst.id,
        academic_year_id=ay.id,
        approval_status="approved",
        is_synthetic=True,
    )
    db.add(approval)

    intake = IntakeApproval(
        institution_id=inst.id,
        course_id=course.id,
        academic_year_id=ay.id,
        approved_intake=120,
        is_synthetic=True,
    )
    db.add(intake)
    db.commit()

    return {"institution": inst, "course": course, "academic_year": ay, "intake": intake}
