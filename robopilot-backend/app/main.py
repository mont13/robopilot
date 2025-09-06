from contextlib import asynccontextmanager

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
from app.controllers.agent_controller import router as agent_router
from app.controllers.llm_connection_controller import router as llm_connection_router
from app.controllers.stt_controller import router as stt_router
from app.controllers.tts_controller import router as tts_router
from app.controllers.user_controller import router as user_router
from app.utils import db_session
from app.utils.mcp_integration import (
    configure_mcp_servers,
    initialize_mcp_integration,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Connecting to postgres...")
    dsn = get_database_settings().url
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    cur.close()
    conn.close()
    print("Successfully connected to postgres...")

    # Initialize MCP integration
    print("Initializing MCP integration...")
    try:
        await initialize_mcp_integration()
        await configure_mcp_servers()
        print("MCP integration initialized successfully")
    except Exception as e:
        print(f"Warning: MCP integration failed to initialize: {e}")

    yield

    # Shutdown
    await db_session.shutdown()


def create_application() -> FastAPI:
    application = FastAPI(
        title="Fast Api Docker Poetry Docs",
        debug=False,
        lifespan=lifespan,
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
    application.include_router(user_router, prefix="/api")
    application.include_router(tts_router, prefix="/api")
    application.include_router(stt_router, prefix="/api")
    application.include_router(agent_router, prefix="/api")
    application.include_router(llm_connection_router, prefix="/api")

    return application


# Create the app instance for uvicorn
app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        access_log=True,
        reload=settings.app_reload,
    )
