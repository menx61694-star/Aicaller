from fastapi import APIRouter, Request
router = APIRouter(tags=["telephony"])
@router.post("/webhooks/telephony")
async def telephony_webhook(request: Request) -> dict[str, str]:
    return {"status":"accepted"}
