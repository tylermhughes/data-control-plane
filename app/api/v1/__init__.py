"""Version 1 of the public API. Each milestone adds its routers here."""

from fastapi import APIRouter

from app.api.v1 import (
    allocations,
    api_keys,
    batches,
    capabilities,
    data_sources,
    datasets,
    me,
    projects,
    quality,
    reports,
    requests,
    specs,
    webhooks,
)

router = APIRouter(prefix="/v1")
router.include_router(me.router)
router.include_router(projects.router)
router.include_router(api_keys.router)
router.include_router(capabilities.router)
router.include_router(data_sources.router)
router.include_router(specs.router)
router.include_router(requests.router)
router.include_router(allocations.router)
router.include_router(batches.router)
router.include_router(webhooks.endpoints)
router.include_router(webhooks.deliveries)
router.include_router(webhooks.events)
router.include_router(datasets.router)
router.include_router(datasets.versions)
router.include_router(datasets.evals)
router.include_router(reports.router)
router.include_router(quality.router)
