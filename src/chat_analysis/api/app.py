"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chat_analysis.api.routers import chats, groups
from chat_analysis.core.logging import setup_logging

setup_logging()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Chat Analysis API",
        description="API for generating and analyzing support chat conversations.",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(groups.router)
    app.include_router(chats.router)
    return app


app = create_app()
