
from jonex_core.common.tenant import TenantContext


class CurrentUser:


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
