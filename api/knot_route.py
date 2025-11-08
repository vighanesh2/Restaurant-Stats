from fastapi import APIRouter, HTTPException, Request, Header
from services.knot_service import create_knot_session_api_call

router = APIRouter()

@router.post("/session")
async def create_session(external_user_id: str):
    return await create_knot_session_api_call(external_user_id)

@router.post("/webhook")
async def webhook(request: Request, x_knot_event: str = Header(None)):
    payload = await request.json()
    if x_knot_event == "AUTHENTICATED":
        merchant_id = payload.get("merchantId")
        external_user_id = payload.get("externalUserId")
        # TODO: store merchant and user info here
        return {"status": "authenticated event handled"}
    return {"status": "ignored"}
