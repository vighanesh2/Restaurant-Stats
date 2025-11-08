import base64
import httpx
from fastapi import HTTPException

client_id = "dda0778d-9486-47f8-bd80-6f2512f9bcdb"
secret = "884d84e855054c32a8e39d08fcd9845d"
auth_str = f"{client_id}:{secret}"
b64_auth_str = base64.b64encode(auth_str.encode()).decode()
KNOT_API_BASE = "https://development.knotapi.com"
KNOT_ENVIRONMENT = "development"
KNOT_DEFAULT_PRODUCT = "transaction_link"
KNOT_DEFAULT_MERCHANT_IDS = [19]
KNOT_TUNNEL_BASE = "https://knot.tunnel.tel"

async def create_knot_session_api_call(external_user_id: str):
    payload = {
        "type": "transaction_link",
        "external_user_id": external_user_id,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{KNOT_API_BASE}/session/create",
            headers={
                "Authorization": f"Basic {b64_auth_str}",
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
                "Authorization": f"Basic {b64_auth_str}",
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
        "clientId": client_id,
        "environment": KNOT_ENVIRONMENT,
        "product": resolved_product,
        "merchantIds": resolved_merchants,
        "useCategories": use_categories,
        "useSearch": use_search,
        "entryPoint": entry_point,
    }
