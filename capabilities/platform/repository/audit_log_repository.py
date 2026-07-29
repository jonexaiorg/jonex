from datetime import datetime, timedelta
from typing import List, Optional, Sequence

from sqlalchemy import select, func, desc, distinct, or_, delete

from jonex_core.common.tenant import require_tenant

from capabilities.platform.models.audit_log import AuditLog
from capabilities.platform.repository.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def list_by_tenant(
        self,
        tenant_id: str,
        log_type: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        service_name: Optional[str] = None,
        user_id: Optional[int] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[AuditLog]:
        tenant_id = require_tenant(tenant_id)
        conditions = [AuditLog.tenant_id == tenant_id]

        if log_type:
            conditions.append(AuditLog.log_type == log_type)
        if action:
            conditions.append(AuditLog.action == action)
        if outcome:
            conditions.append(AuditLog.outcome == outcome)
        if service_name:
            conditions.append(AuditLog.service_name == service_name)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if keyword:
            conditions.append(
                or_(
                    AuditLog.username.ilike(f"%{keyword}%"),
                    AuditLog.resource_id.ilike(f"%{keyword}%"),
                )
            )
        if start_time:
            conditions.append(AuditLog.created_at >= start_time)
        if end_time:
            conditions.append(AuditLog.created_at <= end_time)

        result = await self.session.execute(
            select(AuditLog)
            .where(*conditions)
            .order_by(desc(AuditLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_tenant(
        self,
        tenant_id: str,
        log_type: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        service_name: Optional[str] = None,
        user_id: Optional[int] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        tenant_id = require_tenant(tenant_id)
        conditions = [AuditLog.tenant_id == tenant_id]

        if log_type:
            conditions.append(AuditLog.log_type == log_type)
        if action:
            conditions.append(AuditLog.action == action)
        if outcome:
            conditions.append(AuditLog.outcome == outcome)
        if service_name:
            conditions.append(AuditLog.service_name == service_name)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if keyword:
            conditions.append(
                or_(
                    AuditLog.username.ilike(f"%{keyword}%"),
                    AuditLog.resource_id.ilike(f"%{keyword}%"),
                )
            )
        if start_time:
            conditions.append(AuditLog.created_at >= start_time)
        if end_time:
            conditions.append(AuditLog.created_at <= end_time)

        result = await self.session.execute(
            select(func.count()).select_from(AuditLog).where(*conditions)
        )
        return result.scalar() or 0

    async def add_all(self, entries: List[AuditLog]):
        """批量写入"""
        self.session.add_all(entries)

    async def list_system_events(
        self,
        action: Optional[str] = None,
        service_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[AuditLog]:
        conditions = [AuditLog.tenant_id.is_(None)]
        if action:
            conditions.append(AuditLog.action == action)
        if service_name:
            conditions.append(AuditLog.service_name == service_name)
        if start_time:
            conditions.append(AuditLog.created_at >= start_time)
        if end_time:
            conditions.append(AuditLog.created_at <= end_time)
        result = await self.session.execute(
            select(AuditLog)
            .where(*conditions)
            .order_by(desc(AuditLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_system_events(
        self,
        action: Optional[str] = None,
        service_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        conditions = [AuditLog.tenant_id.is_(None)]
        if action:
            conditions.append(AuditLog.action == action)
        if service_name:
            conditions.append(AuditLog.service_name == service_name)
        if start_time:
            conditions.append(AuditLog.created_at >= start_time)
        if end_time:
            conditions.append(AuditLog.created_at <= end_time)
        result = await self.session.execute(
            select(func.count()).select_from(AuditLog).where(*conditions)
        )
        return result.scalar() or 0

    async def get_by_id_with_detail(self, log_id: int) -> Optional[AuditLog]:
        """获取单条完整详情（含 response_body / error_stack）"""
        result = await self.session.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def delete_expired(self, retention_days: int) -> int:
        """删除超过保留天数的过期记录，返回删除条数"""
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        result = await self.session.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        await self.session.commit()
        return result.rowcount

    async def list_distinct_actions(self, tenant_id: str) -> list[str]:
        """查询当前租户所有已使用的操作类型（去重后按字母排序）。"""
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(distinct(AuditLog.action))
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.action)
        )
        return list(result.scalars().all())

    async def list_distinct_resources(self, tenant_id: str) -> list[str]:
        """查询当前租户所有已使用的资源类型（去重后按字母排序）。"""
        tenant_id = require_tenant(tenant_id)
        result = await self.session.execute(
            select(distinct(AuditLog.resource))
            .where(AuditLog.tenant_id == tenant_id)
            .where(AuditLog.resource.isnot(None))
            .order_by(AuditLog.resource)
        )
        return list(result.scalars().all())
