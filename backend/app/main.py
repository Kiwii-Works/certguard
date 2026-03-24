from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .core.auth import AuthException, StandardErrorResponse, ErrorItem
from .core.startup import initialize_app
from .modules.auth.router import router as auth_router
from .modules.certificates.router import router as certificates_router
from .modules.dashboard.router import router as dashboard_router
from .modules.logs.router import router as logs_router
from .modules.notifications.router import router as notifications_router
from .modules.users.router import router as users_router

app = FastAPI(title="CertGuard API", version="1.0.0",
              description="API for certificate request, notifications, logs, and users management.",
              docs_url="/swagger",
              redoc_url="/redoc",
              openapi_url="/openapi.json",)


class HealthResponse(BaseModel):
    success: bool = True
    message: str
    data: dict[str, str]


@app.on_event("startup")
def on_startup() -> None:
    initialize_app()


@app.exception_handler(AuthException)
def handle_auth_exception(_request, exc: AuthException):
    error = StandardErrorResponse(
        success=False,
        message=exc.message,
        errors=[ErrorItem(field=exc.field, detail=exc.message)],
    )
    return JSONResponse(status_code=exc.status_code, content=error.dict())


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(certificates_router)
app.include_router(notifications_router)
app.include_router(dashboard_router)
app.include_router(logs_router)


@app.get("/api/v1/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        success=True,
        message="Health check completed successfully.",
        data={"status": "ok", "app_name": "CertGuard"},
    )
