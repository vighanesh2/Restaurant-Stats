import base64
import httpx
from fastapi import HTTPException

client_id = "dda0778d-9486-47f8-bd80-6f2512f9bcdb"
secret = "ff5e51b6dcf84a829898d37449cbc47a"
auth_str = f"{client_id}:{secret}"
b64_auth_str = base64.b64encode(auth_str.encode()).decode()
KNOT_API_BASE = "https://development.knotapi.com"

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
