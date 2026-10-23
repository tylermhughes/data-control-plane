"""Version 1 of the public API. Each milestone adds its routers here."""

from fastapi import APIRouter

from app.api.v1 import api_keys, capabilities, data_sources, me, projects, specs

router = APIRouter(prefix="/v1")
router.include_router(me.router)
router.include_router(projects.router)
router.include_router(api_keys.router)
router.include_router(capabilities.router)
router.include_router(data_sources.router)
router.include_router(specs.router)
