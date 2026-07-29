"""
平台上下文契约 — 给 Capability 提供只读平台信息。
Capability 通过此模块获取当前用户、租户信息，不可直接写平台数据。
"""
from jonex_core.common.tenant import TenantContext


class CurrentUser:
    """当前用户只读上下文"""

    def __init__(self, user_id: int, tenant_id: str, username: str, role: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.username = username
        self.role = role

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "username": self.username,
            "role": self.role,
        }
