"""
Auth proxy route - pure transparent proxy to Sidecar's /auth/* endpoints.
Gateway does not perform any authentication logic, forwards requests and responses as-is.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from jonex_core.common import get_config, get_logger

router = APIRouter()
config = get_config()
logger = get_logger("api_auth")

SIDECAR_URL = config.SIDECAR_URL


async def _proxy_to_sidecar(method: str, path: str, request: Request) -> JSONResponse:
    import httpx

    url = f"{SIDECAR_URL}{path}"
    headers = {}
    for key in ("Authorization", "Content-Type", "X-Request-ID"):
        val = request.headers.get(key)
        if val:
            headers[key] = val

    body = None
    if method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.json()
        except Exception:
            body = None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            else:
                resp = await client.post(url, json=body, headers=headers)

        # Defend against non-JSON responses
        try:
            content = resp.json()
        except Exception:
            content = {"detail": resp.text or "(empty response)"}
        return JSONResponse(content=content, status_code=resp.status_code)
    except httpx.ConnectError:
        logger.error(f"Unable to connect to Sidecar: {url}")
        return JSONResponse(
            content={"detail": "Authentication service temporarily unavailable"},
            status_code=502,
        )


@router.post("/login")
async def login(request: Request):
    """Proxy to Sidecar POST /auth/login"""
    return await _proxy_to_sidecar("POST", "/auth/login", request)


@router.get("/me")
async def me(request: Request):
    """Proxy to Sidecar GET /auth/me, pass through Authorization"""
    return await _proxy_to_sidecar("GET", "/auth/me", request)


@router.post("/refresh")
async def refresh(request: Request):
    """Proxy to Sidecar POST /auth/refresh"""
    return await _proxy_to_sidecar("POST", "/auth/refresh", request)


@router.post("/login-ticket")
async def login_ticket(request: Request):
    """Proxy to Sidecar POST /auth/login-ticket, pass through Authorization"""
    return await _proxy_to_sidecar("POST", "/auth/login-ticket", request)


@router.post("/exchange-ticket")
async def exchange_ticket(request: Request):
    """Proxy to Sidecar POST /auth/exchange-ticket"""
    return await _proxy_to_sidecar("POST", "/auth/exchange-ticket", request)
