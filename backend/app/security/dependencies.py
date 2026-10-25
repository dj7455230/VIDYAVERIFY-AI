"""Security dependencies for FastAPI: current user, role checks, institution scope."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.auth import decode_token
from app.models.user import User
from app.models.institution import InstitutionUserMembership

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    if user.is_locked:
        raise HTTPException(status_code=403, detail="Account is locked")
    return user


def require_roles(*role_names: str):
    """Dependency factory: require user to have one of the specified roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_any_role(list(role_names)):
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of: {', '.join(role_names)}",
            )
        return current_user
    return role_checker


def get_user_institution_ids(db: Session, user: User) -> list[str]:
    """Get institution IDs the user has access to."""
    if user.has_role("SUPER_ADMIN") or user.has_role("AICTE_ADMIN") or user.has_role("AUDITOR") or user.has_role("FRAUD_ANALYST"):
        # These roles have broader access
        return []
    memberships = db.query(InstitutionUserMembership).filter(
        InstitutionUserMembership.user_id == user.id
    ).all()
    return [m.institution_id for m in memberships]


def enforce_institution_scope(user: User, institution_id: str, db: Session) -> None:
    """Ensure user can only access their own institution data."""
    if user.has_role("SUPER_ADMIN") or user.has_role("AICTE_ADMIN") or user.has_role("AUDITOR") or user.has_role("FRAUD_ANALYST"):
        return  # Broad-access roles
    allowed = get_user_institution_ids(db, user)
    if institution_id not in allowed:
        raise HTTPException(status_code=403, detail="Not authorized for this institution")
