import psycopg2
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from httpx import HTTPError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, NoResultFound, ProgrammingError
from starlette.exceptions import HTTPException

from app.config import exception_config as exh
from app.config.settings import Environment, get_database_settings, get_settings
from app.controllers.stt_controller import router as stt_router
from app.controllers.tts_controller import router as tts_router
from app.controllers.user_controller import user_router
from app.controllers.lmstudio_controller import router as lmstudio_router
from app.utils import db_session

settings = get_settings()


def create_application() -> FastAPI:
    application = FastAPI(
        title="Fast Api Docker Poetry Docs",
        debug=False,
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.ALLOWED_CORS_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.environment == Environment.prod:
        application.openapi_url = None

    application.add_exception_handler(
        RequestValidationError, exh.req_validation_handler
    )
    application.add_exception_handler(ValidationError, exh.validation_handler)
    application.add_exception_handler(AttributeError, exh.attribute_error_handler)

    application.add_exception_handler(NoResultFound, exh.data_not_found_error_handler)
    application.add_exception_handler(IntegrityError, exh.sql_error_handler)
    application.add_exception_handler(ProgrammingError, exh.sql_error_handler)
    application.add_exception_handler(HTTPError, exh.http_error_handler)
    application.add_exception_handler(HTTPException, exh.http_exception_handler)

    # Include new routers
    # application.include_router(user_router, prefix="/api")
    application.include_router(tts_router, prefix="/api")
    application.include_router(stt_router, prefix="/api")
    application.include_router(lmstudio_router, prefix="/api")

    @application.on_event("startup")
    async def initialize():
        print("Connecting to postgres...")
        dsn = get_database_settings().url
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        print("Successfully connected to postgres...")

    @application.on_event("shutdown")
    async def shutdown():
        await db_session.shutdown()

    return application


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:create_application",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        access_log=True,
        reload=settings.app_reload,
    )
