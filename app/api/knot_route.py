from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from services.knot_service import (
    compose_knot_sdk_config,
    create_knot_session_api_call,
    sync_transactions_api_call,
    sync_transactions_mock_api_call,
)
from services.mock_data import MOCK_ORDER_DATA

router = APIRouter()

@router.post("/session")
async def create_session(external_user_id: str):
    return await create_knot_session_api_call(external_user_id)


class LaunchSessionRequest(BaseModel):
    external_user_id: str
    product: str | None = None
    merchant_ids: list[int] | None = None
    entry_point: str | None = None
    use_categories: bool | None = None
    use_search: bool | None = None


@router.post("/session/launch")
async def launch_session(request: LaunchSessionRequest):
    session_response = await create_knot_session_api_call(request.external_user_id)
    session_id = session_response.get("session")
    if not session_id:
        raise ValueError("Knot session response missing 'session' key.")

    config = compose_knot_sdk_config(
        session_id=session_id,
        product=request.product,
        merchant_ids=request.merchant_ids,
        use_categories=True if request.use_categories is None else request.use_categories,
        use_search=True if request.use_search is None else request.use_search,
        entry_point=request.entry_point or "api",
    )
    return {
        "session": session_response,
        "sdkConfig": config,
    }


class TransactionSyncRequest(BaseModel):
    merchant_id: int
    external_user_id: str
    limit: int | None = None
    cursor: str | None = None


@router.post("/transactions/sync")
async def sync_transactions(request: TransactionSyncRequest):
    return await sync_transactions_api_call(
        merchant_id=request.merchant_id,
        external_user_id=request.external_user_id,
        limit=request.limit,
        cursor=request.cursor,
    )


class TransactionSyncMockRequest(BaseModel):
    merchant_id: int
    external_user_id: str
    limit: int | None = None


@router.post("/transactions/mock-sync")
async def sync_transactions_mock(request: TransactionSyncMockRequest):
    return await sync_transactions_mock_api_call(
        merchant_id=request.merchant_id,
        external_user_id=request.external_user_id,
        limit=request.limit,
    )


@router.post("/webhook")
async def webhook(request: Request, x_knot_event: str = Header(None)):
    payload = await request.json()
    if x_knot_event == "AUTHENTICATED":
        merchant_id = payload.get("merchantId")
        external_user_id = payload.get("externalUserId")
        # TODO: store merchant and user info here
        return {"status": "authenticated event handled"}
    return {"status": "ignored"}


@router.get("/mock-order")
async def get_mock_order():
    return MOCK_ORDER_DATA
