
from datetime import datetime
from typing import List, Literal, Optional, Union

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field




class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    user_id: int
    username: str
    display_name: Optional[str] = None
    tenant_id: str
    tenant_name: Optional[str] = None
    role: str


class LoginResponse(BaseModel):
    status: Literal["authenticated"] = "authenticated"
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


class TenantOption(BaseModel):
    tenant_id: str
    tenant_name: str


class TenantSelectionRequiredResponse(BaseModel):
    status: Literal["tenant_selection_required"] = "tenant_selection_required"
    tenant_options: List[TenantOption]


LoginFlowResponse = Union[LoginResponse, TenantSelectionRequiredResponse]


class LoginTicketRequest(BaseModel):
    appId: str
    redirectUri: str
    state: Optional[str] = None


class LoginTicketResponse(BaseModel):
    ticket: str
    expires_in: int


class ExchangeTicketRequest(BaseModel):
    appId: str
    ticket: str
    redirectUri: str
    state: Optional[str] = None
