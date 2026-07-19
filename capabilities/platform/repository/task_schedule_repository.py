from typing import Sequence

from sqlalchemy import select, func

from jonex_core.common.tenant import require_tenant

from capabilities.platform.models.task_schedule import TaskSchedule
from capabilities.platform.repository.base import BaseRepository


class TaskScheduleRepository(BaseRepository[TaskSchedule]):
    model = TaskSchedule

    async def list_by_tenant(
        self, tenant_id: str, offset: int = 0, limit: int = 20
    ) -> Sequence[TaskSchedule]:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(TaskSchedule)
            .where(TaskSchedule.tenant_id == tenant_id, TaskSchedule.is_deleted == 0)
            .order_by(TaskSchedule.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_tenant(self, tenant_id: str) -> int:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(func.count()).select_from(TaskSchedule).where(
                TaskSchedule.tenant_id == tenant_id, TaskSchedule.is_deleted == 0
            )
        )
        return result.scalar() or 0

    async def list_by_type(
        self, tenant_id: str, task_type: str
    ) -> Sequence[TaskSchedule]:
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(TaskSchedule).where(
                TaskSchedule.tenant_id == tenant_id,
                TaskSchedule.task_type == task_type,
                TaskSchedule.is_deleted == 0,
            )
        )
        return result.scalars().all()