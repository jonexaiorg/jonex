
from fastapi import APIRouter, Depends, Header, Request

from jonex_core.common.database import get_db
from jonex_core.common.response import success_response
from jonex_core.common.exceptions import TokenExpiredError
from capabilities.platform.auth.auth_service import AuthService
from capabilities.platform.dtos.auth import (
    LoginRequest,
    LoginTicketRequest,
    TenantSelectionRequiredResponse,
    ExchangeTicketRequest,
)

router = APIRouter()


@router.post("/login")
async def login(
    req: LoginRequest,
    request: Request,
    tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    db=Depends(get_db),
):
    svc = AuthService(db)

    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else None)
    )
    result = await svc.login(tenant_id, req, client_ip=client_ip)
    message = "Select a tenant" if isinstance(result, TenantSelectionRequiredResponse) else "success"
    return success_response(data=result.dict(), message=message)


@router.get("/me")
async def me(authorization: str = Header(...), db=Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise TokenExpiredError(message="Missing Bearer token")
    token = authorization[7:]
    svc = AuthService(db)
    result = await svc.me(token)
    return success_response(data=result.dict())


@router.post("/refresh")
async def refresh(authorization: str = Header(...), db=Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise TokenExpiredError(message="Missing Bearer token")
    token = authorization[7:]
    svc = AuthService(db)
    result = await svc.refresh(token)
    return success_response(data=result.dict())


@router.post("/login-ticket")
async def login_ticket(
    req: LoginTicketRequest,
    request: Request,
    authorization: str = Header(...),
    db=Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise TokenExpiredError(message="Missing Bearer token")
    token = authorization[7:]
    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("User-Agent", "")[:1024] if request else None
    svc = AuthService(db)
    result = await svc.create_login_ticket(req, token, client_ip, user_agent)
    return success_response(data=result.dict())


@router.post("/exchange-ticket")
async def exchange_ticket(req: ExchangeTicketRequest, db=Depends(get_db)):
    svc = AuthService(db)
    result = await svc.exchange_ticket(req)
    return success_response(data=result.dict())


@router.post("/logout")
async def logout():
    return success_response(message="Logged out successfully")
