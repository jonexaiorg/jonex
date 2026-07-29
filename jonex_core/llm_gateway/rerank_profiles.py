# -*- coding:utf-8 -*-
"""生成式 reranker 的 prompt 模板 + yes/no 词表 profile 注册表。

生成式 reranker（Qwen3-Reranker / bge-reranker-v2-gemma 等）没有统一模板，
每个模型族的 prompt、特殊 token、yes/no 词表都不同。此处把「模板 + 算分词表」
抽象成 profile，由 LLMGW_RERANK_PROMPT_PROFILE 选择。

加新模型族 = 在 _PROFILES 增加一条，无需改 upstream 算分逻辑。

⚠️ 目前仅 `qwen3` profile 经本机实测（awenleven/Qwen3-Reranker-4B:Q4_K_M）；
   `gemma` / `plain` 为预留，接入前必须按目标模型卡校准 prefix/suffix/instruct
   与 yes_set/no_set（用实测 top_logprobs 候选核对）。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RerankProfile:
    name: str
    prefix: str                       # query/doc 之前的系统+用户起始段
    suffix: str                       # query/doc 之后的 assistant 起始段（强制下一 token=判定）
    instruct: str                     # <Instruct> 文案
    yes_set: frozenset               # yes 类 token（小写匹配，概率求和）
    no_set: frozenset                # no 类 token
    template: str = (
        "{prefix}<Instruct>: {instruct}\n<Query>: {query}\n<Document>: {doc}{suffix}"
    )

    def render(self, query: str, doc: str) -> str:
        return self.template.format(
            prefix=self.prefix, instruct=self.instruct,
            query=query, doc=doc, suffix=self.suffix,
        )


# 已本机实测：awenleven/Qwen3-Reranker-4B:Q4_K_M
_QWEN3 = RerankProfile(
    name="qwen3",
    prefix=(
        '<|im_start|>system\nJudge whether the Document meets the requirements '
        'based on the Query and the Instruct provided. Note that the answer can '
        'only be "yes" or "no".<|im_end|>\n<|im_start|>user\n'
    ),
    suffix="<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n",
    instruct="Given a web search query, retrieve relevant passages that answer the query",
    yes_set=frozenset({"yes", "y", "true", "是", "ye", "correct", "正确", "right"}),
    no_set=frozenset({"no", "n", "false", "不", "没有", "无", "not", "否", "无关", "错误", "未"}),
)

# 预留：bge-reranker-v2-gemma 等（接入时按其模型卡补全模板）
# ⚠️ 未经本机实测，接入前须校准模板与词表。
_GEMMA = RerankProfile(
    name="gemma",
    prefix="<bos><start_of_turn>user\n",
    suffix="<end_of_turn>\n<start_of_turn>model\n",
    instruct="Given a query, judge whether the document is relevant. Answer Yes or No.",
    yes_set=frozenset({"yes", "y", "是"}),
    no_set=frozenset({"no", "n", "不"}),
)

# 通用兜底：无特殊模板，直接问 yes/no（精度最低，仅救急）
_PLAIN = RerankProfile(
    name="plain",
    prefix="",
    suffix="\nAnswer only yes or no:",
    instruct="Judge whether the document is relevant to the query.",
    yes_set=frozenset({"yes", "y", "true", "是"}),
    no_set=frozenset({"no", "n", "false", "不"}),
)

_PROFILES = {p.name: p for p in (_QWEN3, _GEMMA, _PLAIN)}


def get_profile(name: str) -> RerankProfile:
    """按名取 profile；未知名回退 qwen3（唯一实测过的 profile）。"""
    return _PROFILES.get(name, _QWEN3)


__all__ = ["RerankProfile", "get_profile"]
