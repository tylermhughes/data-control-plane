"""Version 1 of the public API. Each milestone adds its routers here."""

from fastapi import APIRouter

from app.api.v1 import api_keys, me, projects

router = APIRouter(prefix="/v1")
router.include_router(me.router)
router.include_router(projects.router)
router.include_router(api_keys.router)
