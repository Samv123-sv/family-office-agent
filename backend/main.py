import time

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from config import settings
from logging_config import configure_logging
from routers.alerts_router import router as alerts_router
from routers.deals_router import router as deals_router
from routers.documents_router import router as documents_router
from routers.health_router import router as health_router
from routers.memos_router import router as memos_router
from routers.pipeline_router import router as pipeline_router
from routers.thesis_router import router as thesis_router

configure_logging()
logger = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title="Family Office Deal Flow API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Middleware (last add_middleware = outermost = runs first) ──────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round((time.time() - start) * 1000, 1),
        ip=request.client.host if request.client else None,
    )
    return response


app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(pipeline_router, prefix="/api")
app.include_router(deals_router, prefix="/api")
app.include_router(memos_router, prefix="/api")
app.include_router(thesis_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(health_router, prefix="/api")
