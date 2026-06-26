"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, approvals, documents, rules, settings
from app.config import get_settings
from app.db.database import init_db


def create_app() -> FastAPI:
    cfg = get_settings()
    init_db(cfg.database_path)
    app = FastAPI(title=cfg.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
    app.include_router(agents.router, prefix="/api/agent", tags=["agent"])
    app.include_router(approvals.router, prefix="/api/plans", tags=["plans"])
    app.include_router(rules.router, prefix="/api/rules", tags=["rules"])
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
    return app


app = create_app()
