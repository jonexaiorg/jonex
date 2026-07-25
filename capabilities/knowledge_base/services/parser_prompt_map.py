#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""解析器类目 → atomic-rag 主解析提示词 code 映射 + 轻量模板预校验。

见 docs/parser-prompt-integration-plan.md §2/§4.6。

本期 KB 只创建并生效 4 个 prompt_code：
  generic_prompt / vision_prompt / audio_global_prompt / video_global_prompt。
table/equation 等文档内模态一律用 atomic-rag 内置 prompt，KB 不维护。

权威占位符白名单校验在 atomic-rag 侧 create_prompt/update_prompt handler
（从 PROMPTS 派生）；KB 侧只做括号成对的轻量预检，提前拦明显错误。
"""
import string
from typing import Optional

from jonex_core.common.exceptions import InvalidParameterError
from jonex_core.common.i18n import translate


# parser_type -> (preset_name（元数据）, prompt_code（生效键）, category)
PARSER_PROMPT_MAP: dict[str, tuple[str, str, str]] = {
    "document": ("document", "generic_prompt", "analysis"),
    "txt": ("text_parse", "generic_prompt", "analysis"),
    "image": ("image", "vision_prompt", "analysis"),
    "audio": ("audio_transcribe", "audio_global_prompt", "analysis"),
    "video": ("video_full_pipeline", "video_global_prompt", "analysis"),
    "web": ("document", "generic_prompt", "analysis"),
    "cad": ("document", "generic_prompt", "analysis"),
}


def prompt_target(parser_type: str) -> Optional[tuple[str, str, str]]:
    """返回 (preset_name, prompt_code, category)；未映射类目返回 None（不下发 prompt）。"""
    return PARSER_PROMPT_MAP.get((parser_type or "").strip().lower())


def precheck_prompt_template(content: str) -> None:
    """KB 侧轻量预检：括号必须成对合法（否则解析时 .format 会崩）。

    仅拦明显语法错误；占位符白名单以 atomic-rag handler 为权威（会再校验一次）。
    违规抛 InvalidParameterError（→ 上层 400，解析器保存失败）。
    """
    if content is None:
        return
    try:
        # 触发 Formatter 解析；未成对/非法大括号会抛 ValueError
        list(string.Formatter().parse(content))
    except ValueError as e:
        raise InvalidParameterError(
            message=translate("err.prompt.template_brace_invalid", params={"error": str(e)}, fallback=f"提示词模板大括号非法：{e}。字面大括号请写成 {{{{ }}}}")  ,  # 原消息
            details={"error": str(e)},
        )


__all__ = ["PARSER_PROMPT_MAP", "prompt_target", "precheck_prompt_template"]
