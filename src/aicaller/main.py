from fastapi import FastAPI
from aicaller.config import settings
from aicaller.api.routes.health import router as health_router
from aicaller.api.routes.webhooks import router as webhook_router

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(health_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")
