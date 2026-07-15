from fastapi import APIRouter

from app.api.v1.routers import (
    accreditation,
    auth,
    courses,
    exams,
    outcomes,
    papers,
    scores,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(outcomes.router)
api_router.include_router(exams.router)
api_router.include_router(papers.router)
api_router.include_router(scores.router)
api_router.include_router(accreditation.router)
