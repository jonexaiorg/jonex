#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""通义千问 LLM 适配器

对接阿里云通义千问 API，提供文本生成和向量检索能力。
"""

from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.llm.base_llm import BaseLLMCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse, CapabilityMetadata, CapabilityType
from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError
from jonex_core.common.i18n import translate

logger = get_logger("atomic.llm.qwen")


class QwenLLMCapability(BaseLLMCapability):
    """通义千问 LLM 能力适配器"""

    def _build_metadata(self) -> CapabilityMetadata:
        """构建能力元数据"""
        return CapabilityMetadata(
            capability_id="llm.qwen",
            capability_name="通义千问 LLM",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="阿里云通义千问大模型，支持文本生成和向量检索",
            tags=["llm", "qwen", "embedding"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:
        """验证输入参数"""
        if not request.payload:
            raise InvalidParameterError(message=translate("err.llm.payload_required", fallback="LLM 请求 payload 不能为空"))

        action = request.payload.get("action", "chat")

        if action == "chat":
            if "messages" not in request.payload:
                raise InvalidParameterError(message=translate("err.capability.missing_action_param", params={"action": "chat", "param": "messages"}, fallback="chat 模式必须提供 messages 参数"))
        elif action == "embedding":
            if "text" not in request.payload:
                raise InvalidParameterError(message=translate("err.capability.missing_action_param", params={"action": "embedding", "param": "text"}, fallback="embedding 模式必须提供 text 参数"))
        elif action == "summarize":
            if "content" not in request.payload:
                raise InvalidParameterError(message=translate("err.capability.missing_action_param", params={"action": "summarize", "param": "content"}, fallback="summarize 模式必须提供 content 参数"))
        else:
            raise InvalidParameterError(message=translate("err.capability.unsupported_action", params={"action": action}, fallback=f"不支持的 action: {action}"))

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:
        """执行 LLM 能力调用"""
        await self.validate_input(request)

        action = request.payload.get("action", "chat")

        try:
            if action == "chat":
                messages = request.payload["messages"]
                temperature = request.payload.get("temperature", 0.7)
                max_tokens = request.payload.get("max_tokens")
                result = await self.chat_completion(messages, temperature, max_tokens)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"result": result},
                    message="LLM 对话调用成功",
                )
            elif action == "embedding":
                text = request.payload["text"]
                vector = await self.embedding(text)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"vector": vector},
                    message="文本向量化成功",
                )
            elif action == "summarize":
                content = request.payload["content"]
                summary = await self._summarize(content)
                return CapabilityResponse.ok(
                    request_id=request.request_id,
                    data={"summary": summary},
                    message="文本摘要生成成功",
                )
        except Exception as e:
            logger.error(f"通义千问调用失败: {e}")
            raise CapabilityInvokeError(
                message=translate("err.llm.invoke_failed", fallback="LLM 调用失败"),
                details={"action": action},
                cause=e,
            )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        聊天补全接口

        注意：当前为 mock 实现，实际部署时需要接入真实的通义千问 API。
        """
        config = get_config()

        # Mock 实现：返回模拟响应
        if config.ENV == "dev":
            logger.warning("使用 Mock 模式调用通义千问，请在生产环境配置真实 API Key")
            last_message = messages[-1]["content"] if messages else ""
            return f"[Mock Qwen 响应] 收到消息：{last_message[:50]}...（模拟响应）"

        # TODO: 接入真实的通义千问 API
        # import dashscope
        # response = dashscope.Generation.call(
        #     model=dashscope.Generation.Models.qwen_turbo,
        #     messages=messages,
        #     api_key=config.LLM_API_KEY,
        # )
        # return response["output"]["text"]

        raise CapabilityInvokeError(message=translate("err.capability.service_not_configured", params={"service_name": "通义千问 API"}, fallback="通义千问 API 未配置"))

    async def embedding(self, text: str) -> List[float]:
        """
        文本向量化接口

        注意：当前为 mock 实现，实际部署时需要接入真实 API。
        """
        config = get_config()

        if config.ENV == "dev":
            # Mock 实现：返回随机向量
            import random
            return [random.uniform(-1, 1) for _ in range(1536)]

        # TODO: 接入真实的通义千问 Embedding API
        raise CapabilityInvokeError(message=translate("err.capability.service_not_configured", params={"service_name": "通义千问 Embedding API"}, fallback="通义千问 Embedding API 未配置"))

    async def _summarize(self, content: str) -> str:
        """文本摘要生成"""
        messages = [
            {"role": "system", "content": "请为以下内容生成简洁的摘要，控制在200字以内。"},
            {"role": "user", "content": content},
        ]
        return await self.chat_completion(messages, temperature=0.3)
