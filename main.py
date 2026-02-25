"""Uvicorn entry point for the Chat Analysis API."""

import uvicorn

from chat_analysis.api.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
