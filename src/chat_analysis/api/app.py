"""FastAPI application factory."""

from fastapi import FastAPI

from chat_analysis.api.routers import chats, groups


def create_app() -> FastAPI:
    app = FastAPI(
        title="Chat Analysis API",
        description="API for generating and analyzing support chat conversations.",
        version="1.0.0",
    )
    app.include_router(groups.router)
    app.include_router(chats.router)
    return app


app = create_app()
