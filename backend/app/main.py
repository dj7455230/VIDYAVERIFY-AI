"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database import Base, engine
from app.api.v1 import auth, dashboard, institutions, courses, students, submissions, validation, duplicates, risk, graph, cases, copilot, verification, clarifications, reports, notifications, audit, health

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # Shutdown


app = FastAPI(
    title="VIDYAVERIFY AI",
    description="APAAR ID-Based Student Data Management and Verification Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler — prevent stack trace leakage
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again.",
            "code": "INTERNAL_ERROR",
        },
    )


# Include API routers
prefix = "/api/v1"
app.include_router(health.router, prefix=prefix, tags=["health"])
app.include_router(auth.router, prefix=prefix, tags=["auth"])
app.include_router(dashboard.router, prefix=prefix, tags=["dashboard"])
app.include_router(institutions.router, prefix=prefix, tags=["institutions"])
app.include_router(courses.router, prefix=prefix, tags=["courses"])
app.include_router(students.router, prefix=prefix, tags=["students"])
app.include_router(submissions.router, prefix=prefix, tags=["submissions"])
app.include_router(validation.router, prefix=prefix, tags=["validation"])
app.include_router(duplicates.router, prefix=prefix, tags=["duplicates"])
app.include_router(risk.router, prefix=prefix, tags=["risk"])
app.include_router(graph.router, prefix=prefix, tags=["graph"])
app.include_router(cases.router, prefix=prefix, tags=["cases"])
app.include_router(copilot.router, prefix=prefix, tags=["copilot"])
app.include_router(verification.router, prefix=prefix, tags=["verification"])
app.include_router(clarifications.router, prefix=prefix, tags=["clarifications"])
app.include_router(reports.router, prefix=prefix, tags=["reports"])
app.include_router(notifications.router, prefix=prefix, tags=["notifications"])
app.include_router(audit.router, prefix=prefix, tags=["audit"])


@app.get("/")
async def root():
    return {
        "name": "VIDYAVERIFY AI",
        "version": "1.0.0",
        "tagline": "Verify Every Record. Build Trusted Education.",
        "docs": "/docs",
        "demo_mode": settings.DEMO_MODE,
        "demo_label": settings.DEMO_LABEL if settings.DEMO_MODE else None,
    }
