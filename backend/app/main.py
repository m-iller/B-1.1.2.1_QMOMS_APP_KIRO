from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

app = FastAPI(
    title="Quarry Mining Monitor API",
    version="0.1.0",
    description="Backend API for the Quarry Mining Operations Monitoring System",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
def _error_response(request: Request, status_code: int, message: str, error: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "message": message,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error_map = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
    }
    error = error_map.get(exc.status_code, "HTTP Error")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _error_response(request, exc.status_code, message, error)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return _error_response(request, 500, "Internal server error", "Internal Server Error")


# ---------------------------------------------------------------------------
# Module routers (stub imports — routers will be implemented in later tasks)
# ---------------------------------------------------------------------------
try:
    from app.modules.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
except ImportError:
    pass

try:
    from app.modules.machine.router import router as machine_router
    app.include_router(machine_router, prefix="/machines", tags=["machines"])
except ImportError:
    pass

try:
    from app.modules.telemetry.router import router as telemetry_router
    app.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])
except ImportError:
    pass

try:
    from app.modules.task.router import router as task_router
    app.include_router(task_router, tags=["tasks"])
except ImportError:
    pass

try:
    from app.modules.event.router import router as event_router
    app.include_router(event_router, tags=["events"])
except ImportError:
    pass

try:
    from app.modules.zone.router import router as zone_router
    app.include_router(zone_router, prefix="/zones", tags=["zones"])
except ImportError:
    pass

try:
    from app.modules.report.router import router as report_router
    app.include_router(report_router, prefix="/reports", tags=["reports"])
except ImportError:
    pass

try:
    from app.modules.notification.router import router as notification_router
    app.include_router(notification_router, prefix="/notifications", tags=["notifications"])
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
