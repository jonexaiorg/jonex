from typing import Optional, Sequence

from sqlalchemy import select, func

from capabilities.platform.models.application import Application
from capabilities.platform.repository.base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    model = Application

    async def get_by_code(self, app_code: str) -> Optional[Application]:
        result = await self.session.execute(
            select(Application).where(
                Application.app_code == app_code, Application.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> Sequence[Application]:
        result = await self.session.execute(
            select(Application)
            .where(Application.status == 1, Application.is_deleted == 0)
            .order_by(Application.sort_order)
        )
        return result.scalars().all()