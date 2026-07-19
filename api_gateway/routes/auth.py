
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from jonex_core.common.config import get_config
from jonex_core.common.exceptions import CapabilityInvokeError

router = APIRouter()


async def _proxy_auth(request: Request, path: str):

    config = get_config()
    sidecar_url = config.SIDECAR_URL

    body = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.json()

    headers = {
        "X-API-Key": config.SIDECAR_API_KEY,
        "X-Request-ID": getattr(request.state, "request_id", ""),
        "X-Forwarded-For": request.client.host if request.client else "",
    }

    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header
    tenant_id = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id")
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if request.method == "GET":
                resp = await client.get(f"{sidecar_url}/auth/{path}", headers=headers)
            else:
                resp = await client.request(request.method, f"{sidecar_url}/auth/{path}", json=body, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = {"message": e.response.text}
            if isinstance(detail, dict) and "success" in detail and "message" in detail:
                return JSONResponse(content=detail, status_code=e.response.status_code)
            raise CapabilityInvokeError(
                message=detail.get("message", f"Authentication service error: HTTP {e.response.status_code}"),
            )


@router.post("/login")
async def login(request: Request):

    return await _proxy_auth(request, "login")


@router.get("/me")
async def me(request: Request):

    return await _proxy_auth(request, "me")


@router.post("/refresh")
async def refresh(request: Request):

    return await _proxy_auth(request, "refresh")


@router.post("/login-ticket")
async def login_ticket(request: Request):

    return await _proxy_auth(request, "login-ticket")


@router.post("/exchange-ticket")
async def exchange_ticket(request: Request):

    return await _proxy_auth(request, "exchange-ticket")


@router.post("/logout")
async def logout(request: Request):

    return await _proxy_auth(request, "logout")
