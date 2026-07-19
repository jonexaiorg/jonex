from typing import Optional, Sequence

from sqlalchemy import select, func

from capabilities.platform.models.system_config import SystemConfig
from capabilities.platform.repository.base import BaseRepository


class SystemConfigRepository(BaseRepository[SystemConfig]):
    model = SystemConfig

    async def get_by_key(self, config_key: str) -> Optional[SystemConfig]:
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.config_key == config_key)
        )
        return result.scalar_one_or_none()

    async def list_by_group(self, group: str) -> Sequence[SystemConfig]:
        result = await self.session.execute(
            select(SystemConfig).where(SystemConfig.config_group == group)
        )
        return result.scalars().all()

    async def get_value(self, config_key: str, default: str = None) -> Optional[str]:
        cfg = await self.get_by_key(config_key)
        return cfg.config_value if cfg else default