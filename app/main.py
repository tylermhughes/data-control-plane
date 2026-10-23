"""The API server. Run with: uvicorn app.main:app"""

import logging

from fastapi import FastAPI

from app.api import health, v1
from app.config import get_settings

logging.basicConfig(level=get_settings().log_level)

app = FastAPI(
    title="Data Control Plane API",
    version="0.1.0",
    description=(
        "The control plane for AI training data: plan, route, check and measure data "
        "from every source. Everything the product does is available through this API."
    ),
)
app.include_router(health.router)
app.include_router(v1.router)
