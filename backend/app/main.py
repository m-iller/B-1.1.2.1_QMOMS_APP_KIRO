import traceback
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
    allow_origins=["*"],
    allow_credentials=False,
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
    # Print full traceback to uvicorn console for debugging
    traceback.print_exc()
    return _error_response(request, 500, str(exc), "Internal Server Error")


# ---------------------------------------------------------------------------
# Module routers
# ---------------------------------------------------------------------------
print("Loading module routers...")

try:
    from app.modules.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    print("✓ auth router loaded")
except Exception as e:
    print(f"✗ auth router failed: {e}")

try:
    from app.modules.machine.router import router as machine_router
    app.include_router(machine_router, prefix="/machines", tags=["machines"])
    print("✓ machine router loaded")
except Exception as e:
    print(f"✗ machine router failed: {e}")

try:
    from app.modules.telemetry.router import router as telemetry_router
    app.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])
    print("✓ telemetry router loaded")
except Exception as e:
    print(f"✗ telemetry router failed: {e}")

try:
    from app.modules.task.router import router as task_router
    app.include_router(task_router, tags=["tasks"])
    print("✓ task router loaded")
except Exception as e:
    print(f"✗ task router failed: {e}")

try:
    from app.modules.event.router import router as event_router
    app.include_router(event_router, tags=["events"])
    print("✓ event router loaded")
except Exception as e:
    print(f"✗ event router failed: {e}")

try:
    from app.modules.zone.router import router as zone_router
    app.include_router(zone_router, prefix="/zones", tags=["zones"])
    print("✓ zone router loaded")
except Exception as e:
    print(f"✗ zone router failed: {e}")

try:
    from app.modules.report.router import router as report_router
    app.include_router(report_router, prefix="/reports", tags=["reports"])
    print("✓ report router loaded")
except Exception as e:
    print(f"✗ report router failed: {e}")

try:
    from app.modules.notification.router import router as notification_router
    app.include_router(notification_router, prefix="/notifications", tags=["notifications"])
    print("✓ notification router loaded")
except Exception as e:
    print(f"✗ notification router failed: {e}")

try:
    from app.modules.map_config.router import router as map_config_router
    app.include_router(map_config_router, prefix="/map-config", tags=["map_config"])
    print("✓ map_config router loaded successfully")
except Exception as e:
    print(f"WARNING: Failed to load map_config router: {e}")
    traceback.print_exc()

try:
    from app.modules.dev.router import router as dev_router
    app.include_router(dev_router, tags=["DELETE_BEFORE_PROD"])
    print("✓ dev router loaded")
except Exception as e:
    print(f"✗ dev router failed: {e}")

try:
    from app.modules.analytics.router import router as analytics_router
    app.include_router(analytics_router, tags=["analytics"])
    print("✓ analytics router loaded")
except Exception as e:
    print(f"✗ analytics router failed: {e}")

try:
    from app.modules.route.router import router as route_router
    app.include_router(route_router, prefix="/routes", tags=["routes"])
    print("✓ route router loaded")
except Exception as e:
    print(f"✗ route router failed: {e}")

try:
    from app.modules.role_permissions.router import router as role_permissions_router
    app.include_router(role_permissions_router, prefix="/role-permissions", tags=["role-permissions"])
    print("✓ role_permissions router loaded")
except Exception as e:
    print(f"✗ role_permissions router failed: {e}")

print("Finished loading routers\n")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
