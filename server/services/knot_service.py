import base64
import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

KNOT_CLIENT_ID = os.getenv("KNOT_CLIENT_ID")
KNOT_CLIENT_SECRET = os.getenv("KNOT_CLIENT_SECRET")
KNOT_API_BASE = os.getenv("KNOT_API_BASE", "https://development.knotapi.com")
KNOT_ENVIRONMENT = os.getenv("KNOT_ENVIRONMENT", "development")
KNOT_DEFAULT_PRODUCT = os.getenv("KNOT_DEFAULT_PRODUCT", "transaction_link")

_merchant_ids_raw = os.getenv("KNOT_DEFAULT_MERCHANT_IDS", "19")
try:
    KNOT_DEFAULT_MERCHANT_IDS = [int(x.strip()) for x in _merchant_ids_raw.split(",") if x.strip()]
except ValueError:
    KNOT_DEFAULT_MERCHANT_IDS = [19]

KNOT_TUNNEL_BASE = os.getenv("KNOT_TUNNEL_BASE", "https://knot.tunnel.tel")


def _get_b64_auth() -> str:
    if not KNOT_CLIENT_ID or not KNOT_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Knot credentials not configured")
    auth_str = f"{KNOT_CLIENT_ID}:{KNOT_CLIENT_SECRET}"
    return base64.b64encode(auth_str.encode()).decode()

async def create_knot_session_api_call(external_user_id: str):
    payload = {
        "type": "transaction_link",
        "external_user_id": external_user_id,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{KNOT_API_BASE}/session/create",
            headers={
                "Authorization": f"Basic {_get_b64_auth()}",
                "Content-Type": "application/json",
                "Knot-Version": "2.0",
            },
            json=payload,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to create Knot session")
        return resp.json()


async def sync_transactions_api_call(
    merchant_id: int,
    external_user_id: str,
    limit: int | None = None,
    cursor: str | None = None,
):
    payload: dict[str, object] = {
        "merchant_id": merchant_id,
        "external_user_id": external_user_id,
    }
    if limit is not None:
        payload["limit"] = limit
    if cursor:
        payload["cursor"] = cursor

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{KNOT_API_BASE}/transactions/sync",
            headers={
                "Authorization": f"Basic {_get_b64_auth()}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to sync transactions")
        return resp.json()


async def sync_transactions_mock_api_call(
    merchant_id: int,
    external_user_id: str,
    limit: int | None = None,
):
    payload: dict[str, object] = {
        "merchant_id": merchant_id,
        "external_user_id": external_user_id,
    }
    if limit is not None:
        payload["limit"] = limit

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{KNOT_TUNNEL_BASE}/transactions/sync",
            headers={
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to sync transactions (mock)")
        return resp.json()


def compose_knot_sdk_config(
    session_id: str,
    product: str | None = None,
    merchant_ids: list[int] | None = None,
    use_categories: bool = True,
    use_search: bool = True,
    entry_point: str = "api",
) -> dict[str, object]:
    resolved_product = product or KNOT_DEFAULT_PRODUCT
    resolved_merchants = merchant_ids if merchant_ids is not None else KNOT_DEFAULT_MERCHANT_IDS
    return {
        "sessionId": session_id,
        "clientId": KNOT_CLIENT_ID,
        "environment": KNOT_ENVIRONMENT,
        "product": resolved_product,
        "merchantIds": resolved_merchants,
        "useCategories": use_categories,
        "useSearch": use_search,
        "entryPoint": entry_point,
    }
