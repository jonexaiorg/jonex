


from dataclasses import dataclass


@dataclass(frozen=True)
class RerankProfile:
    name: str
    prefix: str
    suffix: str
    instruct: str
    yes_set: frozenset
    no_set: frozenset
    template: str = (
        "{prefix}<Instruct>: {instruct}\n<Query>: {query}\n<Document>: {doc}{suffix}"
    )

    def render(self, query: str, doc: str) -> str:
        return self.template.format(
            prefix=self.prefix, instruct=self.instruct,
            query=query, doc=doc, suffix=self.suffix,
        )



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



_GEMMA = RerankProfile(
    name="gemma",
    prefix="<bos><start_of_turn>user\n",
    suffix="<end_of_turn>\n<start_of_turn>model\n",
    instruct="Given a query, judge whether the document is relevant. Answer Yes or No.",
    yes_set=frozenset({"yes", "y", "是"}),
    no_set=frozenset({"no", "n", "不"}),
)


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

    return _PROFILES.get(name, _QWEN3)


__all__ = ["RerankProfile", "get_profile"]
