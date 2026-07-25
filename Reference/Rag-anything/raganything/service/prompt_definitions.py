"""
Built-in prompt definitions — maps each preset to the prompts used by its processors.

Each entry declares the PROMPTS key (code), a human-readable display name,
and a description of what the prompt does during content extraction.

This file serves as the canonical reference for:
  1. GET /api/v1/presets/{name}/prompts  — discover what prompts a preset uses
  2. The prompt-config CRUD APIs that let tenants override individual prompts
"""

from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field


class PromptDefItem(BaseModel):
    """A single prompt definition — describes one prompt template used in processing."""
    code: str = Field(..., description="PROMPTS registry key, e.g. 'vision_prompt'")
    display_name: str = Field(..., description="Human-readable name, e.g. '图片分析提示词'")
    description: str = Field(..., description="What this prompt does in the pipeline")
    category: str = Field(..., description="'system' | 'analysis' | 'chunk' | 'summary' | 'query'")


# ── Preset → prompt definitions ──────────────────────────────────────────────

PRESET_PROMPT_DEFINITIONS: dict[str, List[PromptDefItem]] = {
    # ── image ──────────────────────────────────────────────────────────────
    "image": [
        PromptDefItem(
            code="IMAGE_ANALYSIS_SYSTEM",
            display_name="图片分析系统提示词",
            description="图片分析时使用的 system prompt，定义模型角色为专业图片分析专家",
            category="system",
        ),
        PromptDefItem(
            code="IMAGE_ANALYSIS_FALLBACK_SYSTEM",
            display_name="图片分析回退系统提示词",
            description="当图片无法正常加载时使用的备用 system prompt",
            category="system",
        ),
        PromptDefItem(
            code="vision_prompt",
            display_name="图片视觉分析提示词",
            description="核心图片分析提示词模板，指导模型输出 detailed_description + entity_info JSON 结构",
            category="analysis",
        ),
        PromptDefItem(
            code="vision_prompt_with_context",
            display_name="图片上下文分析提示词",
            description="带周围文本上下文的图片分析提示词，用于结合文档上下文理解图片含义",
            category="analysis",
        ),
        PromptDefItem(
            code="text_prompt",
            display_name="图片文字回退提示词",
            description="当图片无法进行视觉分析时，基于图片路径、标题、脚注进行纯文本分析",
            category="analysis",
        ),
        PromptDefItem(
            code="image_chunk",
            display_name="图片知识块模板",
            description="构建图片知识块(chunk)的格式化模板，包含图片路径、标题、分析结果",
            category="chunk",
        ),
    ],

    # ── table ──────────────────────────────────────────────────────────────
    "table": [
        PromptDefItem(
            code="TABLE_ANALYSIS_SYSTEM",
            display_name="表格分析系统提示词",
            description="表格分析时使用的 system prompt，定义模型角色为专业数据分析师",
            category="system",
        ),
        PromptDefItem(
            code="table_prompt",
            display_name="表格分析提示词",
            description="核心表格分析提示词模板，提取表格结构、数据模式、统计洞察",
            category="analysis",
        ),
        PromptDefItem(
            code="table_prompt_with_context",
            display_name="表格上下文分析提示词",
            description="带周围文本上下文的表格分析提示词，结合文档上下文解释表格数据",
            category="analysis",
        ),
        PromptDefItem(
            code="table_chunk",
            display_name="表格知识块模板",
            description="构建表格知识块(chunk)的格式化模板，包含表格标题、结构、分析结果",
            category="chunk",
        ),
    ],

    # ── equation ───────────────────────────────────────────────────────────
    "equation": [
        PromptDefItem(
            code="EQUATION_ANALYSIS_SYSTEM",
            display_name="公式分析系统提示词",
            description="公式分析时使用的 system prompt，定义模型角色为数学专家",
            category="system",
        ),
        PromptDefItem(
            code="equation_prompt",
            display_name="公式分析提示词",
            description="核心公式分析提示词模板，提取数学含义、变量定义、应用领域",
            category="analysis",
        ),
        PromptDefItem(
            code="equation_prompt_with_context",
            display_name="公式上下文分析提示词",
            description="带周围文本上下文的公式分析提示词，结合文档上下文解释公式意义",
            category="analysis",
        ),
        PromptDefItem(
            code="equation_chunk",
            display_name="公式知识块模板",
            description="构建公式知识块(chunk)的格式化模板，包含公式文本、格式、分析结果",
            category="chunk",
        ),
    ],

    # ── generic ────────────────────────────────────────────────────────────
    "generic": [
        PromptDefItem(
            code="GENERIC_ANALYSIS_SYSTEM",
            display_name="通用内容分析系统提示词",
            description="通用内容分析时使用的 system prompt，根据 content_type 动态调整角色",
            category="system",
        ),
        PromptDefItem(
            code="generic_prompt",
            display_name="通用内容分析提示词",
            description="通用内容分析提示词模板，适用于未分类的多模态内容",
            category="analysis",
        ),
        PromptDefItem(
            code="generic_prompt_with_context",
            display_name="通用内容上下文分析提示词",
            description="带上下文的通用内容分析提示词",
            category="analysis",
        ),
        PromptDefItem(
            code="generic_chunk",
            display_name="通用知识块模板",
            description="构建通用知识块(chunk)的格式化模板",
            category="chunk",
        ),
    ],

    # ── audio ──────────────────────────────────────────────────────────────
    "audio": [
        PromptDefItem(
            code="AUDIO_ANALYSIS_SYSTEM",
            display_name="音频分析系统提示词",
            description="音频分析时使用的 system prompt，定义实体类型枚举(call/conversation/interview/lecture/meeting/podcast)",
            category="system",
        ),
        PromptDefItem(
            code="audio_group_summary_prompt",
            display_name="音频段摘要提示词",
            description="对单个音频段落进行摘要总结(3-5行)，提取主题、关键点、决策和行动项",
            category="summary",
        ),
        PromptDefItem(
            code="audio_reduce_prompt",
            display_name="音频摘要合并提示词",
            description="将多个段落摘要合并为更精炼的综合摘要(MapReduce reduce阶段)",
            category="summary",
        ),
        PromptDefItem(
            code="audio_global_prompt",
            display_name="音频全局综合提示词",
            description="最终全局综合提示词，输出 detailed_description + entity_info JSON",
            category="analysis",
        ),
        PromptDefItem(
            code="audio_chunk",
            display_name="音频知识块模板",
            description="构建音频知识块(chunk)的格式化模板，包含时间范围、转录文本、语言信息",
            category="chunk",
        ),
    ],

    # ── video ──────────────────────────────────────────────────────────────
    "video": [
        PromptDefItem(
            code="video_chunk",
            display_name="视频知识块模板",
            description="构建视频知识块(chunk)的格式化模板，包含时间范围、关键帧、转录文本",
            category="chunk",
        ),
        PromptDefItem(
            code="video_group_summary_prompt",
            display_name="视频段摘要提示词",
            description="对单个视频段落进行摘要总结(3-5行)，提取主题、关键点、决策和行动项",
            category="summary",
        ),
        PromptDefItem(
            code="video_reduce_prompt",
            display_name="视频摘要合并提示词",
            description="将多个段落摘要合并为更精炼的综合摘要(MapReduce reduce阶段)",
            category="summary",
        ),
        PromptDefItem(
            code="video_global_prompt",
            display_name="视频全局综合提示词",
            description="视频最终全局综合提示词，结合ASR转录和VLM视觉描述输出综合理解",
            category="analysis",
        ),
    ],

    # ── query (检索增强) ───────────────────────────────────────────────────
    "query": [
        PromptDefItem(
            code="QUERY_IMAGE_DESCRIPTION",
            display_name="检索-图片描述提示词",
            description="检索时对图片内容进行简要描述的用户提示词",
            category="query",
        ),
        PromptDefItem(
            code="QUERY_IMAGE_ANALYST_SYSTEM",
            display_name="检索-图片分析系统提示词",
            description="检索时图片分析的系统提示词",
            category="query",
        ),
        PromptDefItem(
            code="QUERY_TABLE_ANALYSIS",
            display_name="检索-表格分析提示词",
            description="检索时对表格数据进行分析的提示词，总结主要内容、数据特征和重要发现",
            category="query",
        ),
        PromptDefItem(
            code="QUERY_TABLE_ANALYST_SYSTEM",
            display_name="检索-表格分析系统提示词",
            description="检索时表格分析的系统提示词",
            category="query",
        ),
        PromptDefItem(
            code="QUERY_EQUATION_ANALYSIS",
            display_name="检索-公式分析提示词",
            description="检索时对数学公式进行解释的提示词，说明数学意义、应用场景和重要性",
            category="query",
        ),
        PromptDefItem(
            code="QUERY_EQUATION_ANALYST_SYSTEM",
            display_name="检索-公式分析系统提示词",
            description="检索时公式分析的系统提示词",
            category="query",
        ),
        PromptDefItem(
            code="QUERY_GENERIC_ANALYSIS",
            display_name="检索-通用内容分析提示词",
            description="检索时对通用类型内容进行特征提取的提示词",
            category="query",
        ),
        PromptDefItem(
            code="QUERY_GENERIC_ANALYST_SYSTEM",
            display_name="检索-通用内容分析系统提示词",
            description="检索时通用内容分析的系统提示词",
            category="query",
        ),
        PromptDefItem(
            code="QUERY_ENHANCEMENT_SUFFIX",
            display_name="检索增强后缀提示词",
            description="检索时追加到查询末尾的增强提示，指导模型基于多模态内容信息进行全面回答",
            category="query",
        ),
    ],

    # ── document (复合预设: image + table + equation + generic) ────────────
    "document": [
        # 合并 image, table, equation, generic 的全部提示词
        *(PromptDefItem(
            code="IMAGE_ANALYSIS_SYSTEM",
            display_name="图片分析系统提示词",
            description="图片分析时使用的 system prompt，定义模型角色为专业图片分析专家",
            category="system",
        ),),
        *(PromptDefItem(
            code="vision_prompt",
            display_name="图片视觉分析提示词",
            description="核心图片分析提示词模板，指导模型输出 detailed_description + entity_info JSON 结构",
            category="analysis",
        ),),
        *(PromptDefItem(
            code="vision_prompt_with_context",
            display_name="图片上下文分析提示词",
            description="带周围文本上下文的图片分析提示词，用于结合文档上下文理解图片含义",
            category="analysis",
        ),),
        *(PromptDefItem(
            code="IMAGE_ANALYSIS_FALLBACK_SYSTEM",
            display_name="图片分析回退系统提示词",
            description="当图片无法正常加载时使用的备用 system prompt",
            category="system",
        ),),
        *(PromptDefItem(
            code="text_prompt",
            display_name="图片文字回退提示词",
            description="当图片无法进行视觉分析时，基于图片路径、标题、脚注进行纯文本分析",
            category="analysis",
        ),),
        *(PromptDefItem(
            code="TABLE_ANALYSIS_SYSTEM",
            display_name="表格分析系统提示词",
            description="表格分析时使用的 system prompt，定义模型角色为专业数据分析师",
            category="system",
        ),),
        *(PromptDefItem(
            code="table_prompt",
            display_name="表格分析提示词",
            description="核心表格分析提示词模板，提取表格结构、数据模式、统计洞察",
            category="analysis",
        ),),
        *(PromptDefItem(
            code="table_prompt_with_context",
            display_name="表格上下文分析提示词",
            description="带周围文本上下文的表格分析提示词，结合文档上下文解释表格数据",
            category="analysis",
        ),),
        *(PromptDefItem(
            code="EQUATION_ANALYSIS_SYSTEM",
            display_name="公式分析系统提示词",
            description="公式分析时使用的 system prompt，定义模型角色为数学专家",
            category="system",
        ),),
        *(PromptDefItem(
            code="equation_prompt",
            display_name="公式分析提示词",
            description="核心公式分析提示词模板，提取数学含义、变量定义、应用领域",
            category="analysis",
        ),),
        *(PromptDefItem(
            code="equation_prompt_with_context",
            display_name="公式上下文分析提示词",
            description="带周围文本上下文的公式分析提示词，结合文档上下文解释公式意义",
            category="analysis",
        ),),
        *(PromptDefItem(
            code="GENERIC_ANALYSIS_SYSTEM",
            display_name="通用内容分析系统提示词",
            description="通用内容分析时使用的 system prompt，根据 content_type 动态调整角色",
            category="system",
        ),),
        *(PromptDefItem(
            code="generic_prompt",
            display_name="通用内容分析提示词",
            description="通用内容分析提示词模板，适用于未分类的多模态内容",
            category="analysis",
        ),),
        *(PromptDefItem(
            code="generic_prompt_with_context",
            display_name="通用内容上下文分析提示词",
            description="带上下文的通用内容分析提示词",
            category="analysis",
        ),),
        *(PromptDefItem(
            code="image_chunk",
            display_name="图片知识块模板",
            description="构建图片知识块(chunk)的格式化模板",
            category="chunk",
        ),),
        *(PromptDefItem(
            code="table_chunk",
            display_name="表格知识块模板",
            description="构建表格知识块(chunk)的格式化模板",
            category="chunk",
        ),),
        *(PromptDefItem(
            code="equation_chunk",
            display_name="公式知识块模板",
            description="构建公式知识块(chunk)的格式化模板",
            category="chunk",
        ),),
        *(PromptDefItem(
            code="generic_chunk",
            display_name="通用知识块模板",
            description="构建通用知识块(chunk)的格式化模板",
            category="chunk",
        ),),
    ],

    # ── audio_transcribe (音频转录复合预设) ────────────────────────────────
    "audio_transcribe": [
        # Same as "audio" but this is the preset name used in config/presets/
    ],

    # ── video_full_pipeline (视频全链路复合预设) ───────────────────────────
    "video_full_pipeline": [
        # video + audio prompts combined
    ],
}

# audio_transcribe reuses the "audio" definitions
PRESET_PROMPT_DEFINITIONS["audio_transcribe"] = PRESET_PROMPT_DEFINITIONS["audio"]

# video_full_pipeline combines video + audio
_video_prompts = list(PRESET_PROMPT_DEFINITIONS["video"])
_audio_prompts_for_video = [
    p for p in PRESET_PROMPT_DEFINITIONS["audio"]
    if p.code not in {"audio_chunk"}  # 视频不用 audio_chunk
]
PRESET_PROMPT_DEFINITIONS["video_full_pipeline"] = _video_prompts + _audio_prompts_for_video

# text_parse (纯文本解析 — 只用 generic)
PRESET_PROMPT_DEFINITIONS["text_parse"] = PRESET_PROMPT_DEFINITIONS["generic"]

# document_parse is the same as "document"
PRESET_PROMPT_DEFINITIONS["document_parse"] = PRESET_PROMPT_DEFINITIONS["document"]


def get_preset_prompts(preset_name: str) -> List[PromptDefItem]:
    """Return the prompt definitions for a given preset name.

    Returns empty list for unknown presets (caller decides whether to 404).
    """
    return PRESET_PROMPT_DEFINITIONS.get(preset_name, [])


def list_all_preset_names() -> List[str]:
    """Return all known preset names that have prompt definitions."""
    return sorted(PRESET_PROMPT_DEFINITIONS.keys())


def get_prompt_by_code(preset_name: str, code: str) -> PromptDefItem | None:
    """Look up a single prompt definition by preset + code."""
    for item in PRESET_PROMPT_DEFINITIONS.get(preset_name, []):
        if item.code == code:
            return item
    return None
