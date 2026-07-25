#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
提示词模板 space_id 迁移脚本。

用途：部署领域空间隔离修复后，为数据库中已有的 domain 模板（space_id=NULL）
自动推断并补全 space_id，使其在新隔离逻辑下可见可操作。

推断策略（优先级逐级下降）：
  1. 如果该模板被知识库解析设置引用 → 从 KB 的 space_id 继承
  2. 如果模板属于某租户但未被引用 → 尝试该租户的所有空间，匹配模板名称
  3. 以上都不行 → 走 fallback 空间

用法：
  # 仅预览（不修改）
  python scripts/migrate_prompt_template_space.py

  # 执行迁移
  python scripts/migrate_prompt_template_space.py --apply

  # 指定 fallback 空间
  python scripts/migrate_prompt_template_space.py --apply --default-space space_demo_test
"""

import argparse
import logging
import os
import sys

# 添加项目根目录到 sys.path，使 import 能找到 jonex_core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("migrate_pt_space")


async def run(args: argparse.Namespace) -> None:
    """主迁移逻辑"""
    from jonex_core.common import get_db_session, get_config
    from sqlalchemy import text

    # 加载配置（需要 DB 连接信息）
    config = get_config()
    default_space = args.default_space or "space_demo_test"
    batch: list[dict] = []

    async with get_db_session() as session:
        # ── 1. 查找所有 space_id IS NULL 的 domain 模板 ──
        rows = (
            await session.execute(
                text("""
                    SELECT id, tenant_id, name, category, scope
                    FROM business_domain.prompt_templates
                    WHERE scope = 'domain'
                      AND space_id IS NULL
                      AND is_deleted = 0
                    ORDER BY tenant_id, created_at
                """),
            )
        ).all()

        if not rows:
            logger.info("没有需要迁移的模板（所有 domain 模板已有 space_id）")
            return

        logger.info("发现 %d 个需要迁移的 domain 模板", len(rows))

        # ── 2. 预加载所有 KB → space_id 映射 ──
        kb_space_map: dict[str, str] = {
            row.id: row.space_id
            for row in (
                await session.execute(
                    text("SELECT id, space_id FROM knowledge_base.knowledge_info WHERE is_deleted = 0"),
                )
            ).all()
        }

        # ── 3. 预加载所有租户的空间列表 ──
        tenant_spaces: dict[str, list[str]] = {}
        for row in (
            await session.execute(
                text("SELECT DISTINCT tenant_id, space_id FROM knowledge_base.knowledge_info WHERE is_deleted = 0"),
            )
        ).all():
            tenant_spaces.setdefault(row.tenant_id, []).append(row.space_id)

        for r in rows:
            template_id = r.id
            tenant_id = r.tenant_id
            name = r.name

            inferred_space = None

            # ── 策略 1：从 KB 解析设置继承 ──
            setting_rows = (
                await session.execute(
                    text("""
                        SELECT DISTINCT kps.knowledge_base_id
                        FROM knowledge_base.knowledge_parser_settings kps
                        WHERE kps.prompt_template_id = :tid
                           OR kps.summary_template_id = :tid
                           OR kps.tag_template_id = :tid
                    """),
                    {"tid": template_id},
                )
            ).all()
            kb_ids = [s.knowledge_base_id for s in setting_rows]
            for kid in kb_ids:
                sp = kb_space_map.get(kid)
                if sp:
                    inferred_space = sp
                    break

            # ── 策略 2：该租户只有一个空间 → 直接用 ──
            if not inferred_space:
                spaces = tenant_spaces.get(tenant_id, [])
                if len(spaces) == 1:
                    inferred_space = spaces[0]

            # ── 策略 3：无参考 → 走默认 ──
            if not inferred_space:
                inferred_space = default_space

            batch.append({
                "id": template_id,
                "tenant_id": tenant_id,
                "name": name,
                "inferred_space": inferred_space,
                "kb_count": len(kb_ids),
                "tenant_space_count": len(tenant_spaces.get(tenant_id, [])),
            })

    # ── 4. 展示计划 ──
    logger.info("=" * 60)
    logger.info("迁移计划：")
    logger.info("%-4s %-36s %-20s %-16s → %s", "#", "模板 ID", "模板名称", "租户", "目标空间")
    logger.info("-" * 60)
    for i, item in enumerate(batch, 1):
        logger.info(
            "%-4d %-36s %-20s %-16s → %s",
            i, item["id"], item["name"][:18],
            item["tenant_id"][:14], item["inferred_space"],
        )
    logger.info("-" * 60)
    logger.info("总计 %d 条记录", len(batch))

    # ── 5. 统计推断来源 ──
    from_kb = sum(1 for b in batch if b["kb_count"] > 0)
    from_single_space = sum(1 for b in batch if b["kb_count"] == 0 and b["tenant_space_count"] == 1)
    from_default = sum(1 for b in batch if b["kb_count"] == 0 and b["tenant_space_count"] != 1)
    logger.info(
        "推断来源：KB 关联 %d | 单空间 %d | 默认空间 %d",
        from_kb, from_single_space, from_default,
    )

    if not args.apply:
        logger.info("")
        logger.info("这是预览模式，未做任何修改。")
        logger.info("执行请加 --apply 参数")
        return

    # ── 6. 执行迁移 ──
    async with get_db_session() as session:
        updated = 0
        for item in batch:
            await session.execute(
                text("""
                    UPDATE business_domain.prompt_templates
                    SET space_id = :space_id
                    WHERE id = :id AND space_id IS NULL
                """),
                {"space_id": item["inferred_space"], "id": item["id"]},
            )
            updated += 1

        await session.commit()
        logger.info("")
        logger.info("迁移完成！已更新 %d 条记录", updated)


def main():
    parser = argparse.ArgumentParser(description="提示词模板 space_id 迁移")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="执行迁移（默认仅预览）",
    )
    parser.add_argument(
        "--default-space",
        default="space_demo_test",
        help="无法推断空间时的默认空间 ID（默认: space_demo_test）",
    )
    args = parser.parse_args()

    import asyncio
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
