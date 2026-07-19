#!/usr/bin/python3



from typing import Optional

from jonex_core.capability.atomic.llm.client import LLMClient, get_llm_client
from jonex_core.capability.domain.base import DomainCapability
from jonex_core.capability.models import (
    CapabilityMetadata,
    CapabilityRequest,
    CapabilityResponse,
    CapabilityType,
)
from jonex_core.common import get_logger, require_tenant
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("domain.text.summary")

_PROMPTS = {
    "short":
        "请为以下内容生成一个非常简短的摘要，控制在50字以内：\n\n{content}\n\n摘要：",
    "medium":
        "请为以下内容生成一个简洁的摘要，控制在200字以内，保留关键信息：\n\n{content}\n\n摘要：",
    "detailed":
        "请为以下内容生成一个详细的摘要，控制在500字以内，保留所有重要信息：\n\n{content}\n\n详细摘要：",
    "bullet_points":
        "请为以下内容提取关键要点，以项目符号形式列出，保留所有关键信息：\n\n{content}\n\n要点列表：",
}


class SummaryGeneratorCapability(DomainCapability):


    def __init__(self, llm_client: Optional[LLMClient] = None):
        super().__init__()
        self.llm_client = llm_client

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="text.summary_generator",
            capability_name="文本摘要生成",
            capability_type=CapabilityType.DOMAIN,
            version="v1",
            description="专业化的文本摘要生成能力，支持不同长度、风格的摘要",
            tags=["text", "summary"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        if not request.payload:
            raise InvalidParameterError(message="摘要生成请求 payload 不能为空")
        action = request.payload.get("action", "medium")
        if action not in _PROMPTS:
            raise InvalidParameterError(message=f"不支持的 action: {action}")
        if "content" not in request.payload:
            raise InvalidParameterError(message="必须提供 content 参数")
        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        await self.validate_input(request)

        tenant_id = require_tenant(request.tenant_id)
        action = request.payload.get("action", "medium")
        content = request.payload["content"]
        llm_client = self.llm_client or get_llm_client(tenant_id=tenant_id)

        try:
            logger.info(
                f"Generating summary: action={action}, content_length={len(content)}"
            )
            prompt = _PROMPTS[action].format(content=content)
            summary = await llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            return CapabilityResponse.ok(
                request_id=request.request_id,
                data={
                    "summary": summary,
                    "summary_type": action,
                    "original_length": len(content),
                    "summary_length": len(summary),
                },
                message="文本摘要生成成功",
            )
        except CapabilityInvokeError:
            raise
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise CapabilityInvokeError(
                message=f"摘要生成失败: {e}",
                details={"action": action, "content_length": len(content)},
                cause=e,
            )
