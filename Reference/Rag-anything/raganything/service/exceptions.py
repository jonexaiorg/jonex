"""Custom exceptions for chunk write-back operations."""


class ChunkNotFoundError(Exception):
    """chunk_id 在 text_chunks 中不存在。"""

    def __init__(self, chunk_id: str) -> None:
        self.chunk_id = chunk_id
        super().__init__(f"chunk not found: {chunk_id}")


class ChunkContentTooLargeError(Exception):
    """new_content tokens 超过 MAX_CHUNK_TOKENS。"""

    def __init__(self, chunk_id: str, tokens: int, max_tokens: int) -> None:
        self.chunk_id = chunk_id
        self.tokens = tokens
        self.max_tokens = max_tokens
        super().__init__(
            f"new_content exceeds max token limit for chunk {chunk_id}: "
            f"{tokens} > {max_tokens}"
        )


class ChunkContentConflictError(Exception):
    """new_chunk_id 已存在且属于其他文档。"""

    def __init__(self, chunk_id: str, detail: str) -> None:
        self.chunk_id = chunk_id
        self.detail = detail
        super().__init__(f"content collision for chunk {chunk_id}: {detail}")


class ContentHashMismatchError(Exception):
    """乐观锁: expected_content_hash 与当前内容不匹配。"""

    def __init__(self, chunk_id: str) -> None:
        self.chunk_id = chunk_id
        super().__init__(f"content hash mismatch for chunk {chunk_id}: "
                         f"document has been modified by another request")


class StorageNotReadyError(Exception):
    """租户的 LightRAG 尚未初始化。"""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        super().__init__(f"storage not ready for tenant: {tenant_id}")
