"""Unit tests for LLM response transformers."""

import pytest
from raganything.models.transformers import (
    LLMResponseTransformer,
    NoOpTransformer,
    TokenHubTransformer,
    get_transformer,
    register_transformer,
    BINDING_TRANSFORMERS,
)


class TestNoOpTransformer:
    """NoOpTransformer — passthrough."""

    def test_passthrough(self):
        t = NoOpTransformer()
        assert t.transform("hello") == "hello"
        assert t.transform("") == ""
        assert t.transform("entity<|#|>name<|#|>type<|#|>desc") == (
            "entity<|#|>name<|#|>type<|#|>desc"
        )


class TestTokenHubTransformer:
    """TokenHubTransformer — deepseek response cleanup."""

    def setup_method(self):
        self.t = TokenHubTransformer()

    def test_passthrough_when_valid(self):
        text = "entity<|#|>Alice<|#|>person<|#|>A person\n<|COMPLETE|>"
        assert self.t.transform(text) == text

    def test_appends_missing_completion_delimiter(self):
        text = "entity<|#|>Alice<|#|>person<|#|>A person"
        result = self.t.transform(text)
        assert result.endswith("<|COMPLETE|>")
        assert "Alice" in result

    def test_does_not_double_append(self):
        text = "entity<|#|>x<|#|>y<|#|>z\n<|COMPLETE|>"
        result = self.t.transform(text)
        assert result.count("<|COMPLETE|>") == 1

    def test_removes_thinking_blocks(self):
        text = (
            "<thinking>Let me extract entities.</thinking>\n"
            "entity<|#|>Bob<|#|>person<|#|>A person"
        )
        result = self.t.transform(text)
        assert "<thinking>" not in result
        assert "Bob" in result

    def test_removes_thinking_with_attributes(self):
        text = (
            "<thinking type='reasoning'>I need to parse this.</thinking>\n"
            "entity<|#|>X<|#|>thing<|#|>desc"
        )
        result = self.t.transform(text)
        assert "<thinking" not in result
        assert "X" in result

    def test_normalizes_delimiter_whitespace(self):
        text = "entity <|#|> Alice <|#|> person <|#|> A person"
        result = self.t.transform(text)
        assert "entity<|#|>Alice<|#|>person<|#|>A person" in result

    def test_whitespace_not_removed_from_non_entity_lines(self):
        text = "entity<|#|>X<|#|>y<|#|>z\nSome free text with spaces"
        result = self.t.transform(text)
        assert "Some free text with spaces" in result

    def test_empty_text(self):
        assert self.t.transform("") == ""
        assert self.t.transform("   ") == ""

    def test_multiline_valid_output(self):
        text = (
            "entity<|#|>Alice<|#|>person<|#|>A researcher\n"
            "relation<|#|>Alice<|#|>Bob<|#|>colleague<|#|>They work together\n"
            "<|COMPLETE|>"
        )
        result = self.t.transform(text)
        assert "Alice" in result
        assert "Bob" in result
        assert result.endswith("<|COMPLETE|>")

    # ── Truncated line tests ───────────────────────────────────────────

    def test_removes_truncated_entity_line(self):
        """Truncated entity line (fewer than 3 delimiters) is removed."""
        text = (
            "entity<|#|>Alice<|#|>person<|#|>A researcher\n"
            "entity<|#|>Bob<|#|>person<|#"  # truncated
        )
        result = self.t.transform(text)
        assert "Bob" not in result
        assert "Alice" in result
        assert result.endswith("<|COMPLETE|>")

    def test_removes_truncated_relation_line(self):
        """Truncated relation line (fewer than 4 delimiters) is removed."""
        text = (
            "entity<|#|>X<|#|>type<|#|>desc\n"
            "relation<|#|>X<|#|>Y<|#|>kw<|"  # truncated
        )
        result = self.t.transform(text)
        assert "relation" not in result
        assert "X" in result

    def test_keeps_complete_entity_with_extra_text(self):
        """Complete entity line (3 delimiters) is preserved even with odd content."""
        text = "entity<|#|>名<|#|>TYPE<|#|>desc with extra text here"
        result = self.t.transform(text)
        assert "entity<|#|>名<|#|>TYPE<|#|>desc with extra text here" in result

    def test_keeps_non_entity_trailing_line(self):
        """Trailing line that is NOT entity/relation is preserved."""
        text = "entity<|#|>X<|#|>y<|#|>z\nSome concluding remark"
        result = self.t.transform(text)
        assert "Some concluding remark" in result


class TestGetTransformer:
    """Transformer selection with binding + model_id."""

    def test_returns_tokenhub_for_tokenhub_binding(self):
        t = get_transformer("tokenhub")
        assert isinstance(t, TokenHubTransformer)

    def test_returns_none_for_unknown_binding(self):
        t = get_transformer("openai")
        assert isinstance(t, NoOpTransformer)

    def test_returns_noop_for_anthropic_binding(self):
        t = get_transformer("anthropic")
        assert isinstance(t, NoOpTransformer)

    def test_returns_model_specific_when_registered(self):
        class TestTransformer(LLMResponseTransformer):
            def transform(self, text, context=None):
                return text.upper()

        register_transformer("openai", TestTransformer(), model_id="gpt-4o-mini")
        try:
            t = get_transformer("openai", model_id="gpt-4o-mini")
            assert isinstance(t, TestTransformer)
            # Other model on same binding still gets NoOp
            t2 = get_transformer("openai", model_id="gpt-4o")
            assert isinstance(t2, NoOpTransformer)
        finally:
            # Clean up
            BINDING_TRANSFORMERS.pop(("openai", "gpt-4o-mini"), None)

    def test_model_specific_falls_back_to_binding(self):
        """Unknown model_id falls back to binding-level transformer."""
        t = get_transformer("tokenhub", model_id="unknown-model")
        assert isinstance(t, TokenHubTransformer)

    def test_binding_transformers_has_tokenhub(self):
        assert "tokenhub" in BINDING_TRANSFORMERS


class TestRegisterTransformer:
    """register_transformer() utility."""

    def test_register_protocol_level(self):
        class T(LLMResponseTransformer):
            def transform(self, text, context=None):
                return text

        register_transformer("test_proto", T())
        try:
            assert "test_proto" in BINDING_TRANSFORMERS
        finally:
            BINDING_TRANSFORMERS.pop("test_proto", None)

    def test_register_model_level(self):
        class T(LLMResponseTransformer):
            def transform(self, text, context=None):
                return text

        register_transformer("test_proto", T(), model_id="test-model")
        try:
            assert ("test_proto", "test-model") in BINDING_TRANSFORMERS
        finally:
            BINDING_TRANSFORMERS.pop(("test_proto", "test-model"), None)
