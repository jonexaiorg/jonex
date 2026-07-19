#!/usr/bin/python3



from typing import Any, Dict, List, Optional

from jonex_core.capability.atomic.llm.base_llm import BaseLLMCapability
from jonex_core.capability.models import CapabilityRequest, CapabilityResponse, CapabilityMetadata, CapabilityType
from jonex_core.common import get_config, get_logger
from jonex_core.common.exceptions import CapabilityInvokeError, InvalidParameterError

logger = get_logger("atomic.llm.qwen")


class QwenLLMCapability(BaseLLMCapability):


    def _build_metadata(self) -> CapabilityMetadata:

        return CapabilityMetadata(
            capability_id="llm.qwen",
            capability_name="通义千问 LLM",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="阿里云通义千问大模型，支持文本生成和向量检索",
            tags=["llm", "qwen", "embedding"],
        )

    async def validate_input(self, request: CapabilityRequest) -> bool:

        if not request.payload:
            raise InvalidParameterError(message="LLM 请求 payload 不能为空")

        action = request.payload.get("action", "chat")

        if action == "chat":
            if "messages" not in request.payload:
                raise InvalidParameterError(message="chat 模式必须提供 messages 参数")
        elif action == "embedding":
            if "text" not in request.payload:
                raise InvalidParameterError(message="embedding 模式必须提供 text 参数")
        elif action == "summarize":
            if "content" not in request.payload:
                raise InvalidParameterError(message="summarize 模式必须提供 content 参数")
        else:
            raise InvalidParameterError(message=f"不支持的 action: {action}")

        return True

    async def execute(self, request: CapabilityRequest) -> CapabilityResponse:

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
            logger.error(f"Qwen invocation failed: {e}")
            raise CapabilityInvokeError(
                message=f"通义千问调用失败: {str(e)}",
                details={"action": action},
                cause=e,
            )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:

        config = get_config()


        if config.ENV == "dev":
            logger.warning("Invoking Qwen in Mock mode; configure a valid API key for production")
            last_message = messages[-1]["content"] if messages else ""
            return f"[Mock Qwen 响应] 收到消息：{last_message[:50]}...（模拟响应）"










        raise CapabilityInvokeError(message="通义千问 API 未配置")

    async def embedding(self, text: str) -> List[float]:

        config = get_config()

        if config.ENV == "dev":

            import random
            return [random.uniform(-1, 1) for _ in range(1536)]


        raise CapabilityInvokeError(message="通义千问 Embedding API 未配置")

    async def _summarize(self, content: str) -> str:

        messages = [
            {"role": "system", "content": "请为以下内容生成简洁的摘要，控制在200字以内。"},
            {"role": "user", "content": content},
        ]
        return await self.chat_completion(messages, temperature=0.3)
