from fastapi import APIRouter
from aicaller.config import settings
router = APIRouter(tags=["health"])
@router.get("/health")
def health() -> dict[str, str]:
    return {"status":"ok","service":settings.app_name,"version":settings.app_version}
