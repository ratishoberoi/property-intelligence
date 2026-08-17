import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from app.api.routes import agents, applicants, dashboard, intelligence, matching, properties, rag, recommendations, search, workflow
from app.config import get_settings
from app.db.models import Applicant, Conversation, Feedback, Interaction, Property, Viewing
from app.db.session import Base, SessionLocal, engine
from app.utils.logging import configure_logging, new_request_id, request_id_ctx
from app.utils.security import InMemoryRateLimiter

configure_logging()
settings = get_settings()

app = FastAPI(
    title="Property Intelligence API",
    description="AI intelligence layer for synthetic estate-agency property, applicant and CRM data.",
    version="0.1.0",
)
logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled API exception", extra={"extra": {"path": request.url.path, "error": str(exc)}})
    return JSONResponse(status_code=500, content={"error_code": "INTERNAL_ERROR", "message": "The intelligence request failed.", "request_id": request.headers.get("x-request-id", "-")})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(InMemoryRateLimiter, limit_per_minute=settings.rate_limit_per_minute)


@app.middleware("http")
async def request_tracing(request: Request, call_next):
    request_id = request.headers.get("x-request-id", new_request_id())
    token = request_id_ctx.set(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
    finally:
        latency = round((time.perf_counter() - start) * 1000, 2)
        request_id_ctx.reset(token)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        has_applicants = db.scalar(select(func.count()).select_from(Applicant)) or 0
        has_properties = db.scalar(select(func.count()).select_from(Property)) or 0
    if not has_applicants or not has_properties:
        logger.warning("Core synthetic tables are empty; loading the committed demo dataset")
        from app.db.bootstrap import seed_synthetic_dataset

        with SessionLocal() as db:
            seed_synthetic_dataset(db)
    with SessionLocal() as db:
        from app.api.routes.workflow import seed_demo_workflow
        seed_demo_workflow(db)


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception as exc:
        return {"status": "degraded", "database": "unavailable", "error": str(exc)}


app.include_router(applicants.router, prefix=settings.api_prefix)
app.include_router(properties.router, prefix=settings.api_prefix)
app.include_router(matching.router, prefix=settings.api_prefix)
app.include_router(intelligence.router, prefix=settings.api_prefix)
app.include_router(recommendations.router, prefix=settings.api_prefix)
app.include_router(search.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(rag.router, prefix=settings.api_prefix)
app.include_router(agents.router, prefix=settings.api_prefix)
app.include_router(workflow.router, prefix=settings.api_prefix)
