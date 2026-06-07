from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler, validation_error_handler
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id", str(uuid4()))
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.include_router(api_router, prefix=settings.api_prefix)
app.mount(
    settings.storage_public_url,
    StaticFiles(directory=settings.local_storage_path, check_dir=False),
    name="storage",
)


@app.get("/")
async def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs"}
