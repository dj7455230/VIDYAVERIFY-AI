"""Course and academic year endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.security.dependencies import get_current_user
from app.models.user import User
from app.models.academic import Course, AcademicYear

router = APIRouter()


@router.get("/courses")
async def list_courses(
    search: Optional[str] = Query(None),
    course_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Course)
    if search:
        query = query.filter(Course.name.ilike(f"%{search}%") | Course.code.ilike(f"%{search}%"))
    if course_type:
        query = query.filter(Course.course_type == course_type)
    
    total = query.count()
    courses = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "course_type": c.course_type,
                "duration_years": c.duration_years,
            }
            for c in courses
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/academic-years")
async def list_academic_years(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    years = db.query(AcademicYear).filter(AcademicYear.is_active == True).all()
    return {
        "items": [
            {
                "id": y.id,
                "year_code": y.year_code,
                "start_date": y.start_date.isoformat() if y.start_date else None,
                "end_date": y.end_date.isoformat() if y.end_date else None,
            }
            for y in years
        ]
    }
