"""Authentication endpoints: login, refresh, logout, current user."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.security.auth import verify_password, create_access_token, create_refresh_token, decode_token
from app.security.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserOut, UserCreate
from app.config import get_settings
import uuid

router = APIRouter()
settings = get_settings()


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.is_locked = True
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    if user.is_locked:
        raise HTTPException(status_code=403, detail="Account is locked. Contact admin.")
    
    user.failed_login_attempts = 0
    user.last_login_at = datetime.now(timezone.utc)
    
    access_token = create_access_token({"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token({"sub": user.id})
    user.refresh_token_jti = decode_token(refresh_token).get("jti")
    db.commit()
    
    # Audit log
    db.add(AuditLog(
        actor_id=user.id,
        actor_role=user.roles[0].name if user.roles else None,
        action="login",
        entity_type="user",
        entity_ref=user.id,
        outcome="success",
    ))
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(User).filter(User.id == payload["sub"], User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if payload.get("jti") != user.refresh_token_jti:
        raise HTTPException(status_code=401, detail="Token has been revoked")
    
    access_token = create_access_token({"sub": user.id, "email": user.email})
    new_refresh = create_refresh_token({"sub": user.id})
    user.refresh_token_jti = decode_token(new_refresh).get("jti")
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.refresh_token_jti = None
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="logout",
        entity_type="user",
        entity_ref=current_user.id,
        outcome="success",
    ))
    db.commit()
    return {"message": "Logged out successfully"}


@router.get("/auth/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        roles=[r.name for r in current_user.roles],
        is_active=current_user.is_active,
        last_login_at=current_user.last_login_at,
    )


@router.post("/auth/users", response_model=UserOut)
async def create_user(
    request: UserCreate,
    current_user: User = Depends(require_roles("SUPER_ADMIN")),
    db: Session = Depends(get_db),
):
    from app.security.auth import hash_password
    from app.models.user import Role
    from app.models.institution import InstitutionUserMembership
    
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    user = User(
        email=request.email,
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    db.flush()
    
    for role_name in request.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            user.roles.append(role)
    
    for inst_id in request.institution_ids:
        db.add(InstitutionUserMembership(user_id=user.id, institution_id=inst_id))
    
    db.add(AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.roles[0].name if current_user.roles else None,
        action="create_user",
        entity_type="user",
        entity_ref=user.id,
        outcome="success",
    ))
    db.commit()
    
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        last_login_at=user.last_login_at,
    )
