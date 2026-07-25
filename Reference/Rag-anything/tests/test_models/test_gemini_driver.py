"""Tests for GeminiDriver — message format conversion and response parsing."""

import base64
import json
import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from raganything.models.drivers.gemini import GeminiDriver, _guess_mime
from raganything.models.types import (
    ModelCapability,
    ModelContentFilterError,
    ModelDriverError,
    ModelResponse,
    ModelSpec,
)


@pytest.fixture
def driver():
    return GeminiDriver()


@pytest.fixture
def gemini_spec():
    return ModelSpec(
        model_id="gemini-2.0-flash",
        binding="gemini",
        host="https://generativelanguage.googleapis.com/v1beta",
        api_key="test-key-123",
        capability=ModelCapability(
            supports_vision=True,
            supports_vision_base64=True,
            supports_vision_url=True,
        ),
    )


# ── Test message format conversion ────────────────────────────────────


class TestBuildRequest:
    """OpenAI messages → Gemini generateContent request."""

    def test_simple_text(self, driver, gemini_spec):
        messages = [{"role": "user", "content": "Hello"}]
        body = driver._build_request(messages, gemini_spec)
        assert body["contents"] == [
            {"role": "user", "parts": [{"text": "Hello"}]},
        ]

    def test_system_prompt_to_system_instruction(self, driver, gemini_spec):
        messages = [
            {"role": "system", "content": "You are a physics teacher"},
            {"role": "user", "content": "Explain force"},
        ]
        body = driver._build_request(messages, gemini_spec)
        assert "systemInstruction" in body
        assert body["systemInstruction"]["parts"][0]["text"] == "You are a physics teacher"
        assert len(body["contents"]) == 1  # system not in contents

    def test_assistant_role_to_model(self, driver, gemini_spec):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]
        body = driver._build_request(messages, gemini_spec)
        assert body["contents"][1]["role"] == "model"
        assert body["contents"][1]["parts"][0]["text"] == "Hi there!"

    def test_max_tokens_in_generation_config(self, driver, gemini_spec):
        messages = [{"role": "user", "content": "Hi"}]
        body = driver._build_request(messages, gemini_spec, max_tokens=512)
        assert body["generationConfig"]["maxOutputTokens"] == 512

    def test_temperature_in_generation_config(self, driver, gemini_spec):
        messages = [{"role": "user", "content": "Hi"}]
        body = driver._build_request(messages, gemini_spec, temperature=0.7)
        assert body["generationConfig"]["temperature"] == 0.7

    def test_image_base64_to_inline_data(self, driver, gemini_spec):
        b64_img = base64.b64encode(b"\xff\xd8\xff\xe0" + b"\x00" * 100).decode()
        messages = [{"role": "user", "content": [
            {"type": "text", "text": "Describe"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}},
        ]}]
        body = driver._build_request(messages, gemini_spec)
        parts = body["contents"][0]["parts"]
        assert parts[0] == {"text": "Describe"}
        assert parts[1]["inlineData"]["mimeType"] == "image/jpeg"
        assert parts[1]["inlineData"]["data"] == b64_img

    def test_image_file_to_inline_data(self, driver, gemini_spec):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            tmp_path = f.name
        try:
            messages = [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"file://{tmp_path}"}},
            ]}]
            body = driver._build_request(messages, gemini_spec)
            inline = body["contents"][0]["parts"][0]["inlineData"]
            assert inline["mimeType"] == "image/jpeg"
            assert len(inline["data"]) > 0
        finally:
            os.unlink(tmp_path)

    def test_http_url_to_file_data(self, driver, gemini_spec):
        messages = [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "https://cos.example.com/img.jpg"}},
        ]}]
        body = driver._build_request(messages, gemini_spec)
        fd = body["contents"][0]["parts"][0]["fileData"]
        assert fd["mimeType"] == "image/jpeg"
        assert fd["fileUri"] == "https://cos.example.com/img.jpg"


# ── Test URL building ────────────────────────────────────────────────


class TestBuildURL:
    def test_api_key_auth_url(self, driver, gemini_spec):
        url = driver._build_url(gemini_spec)
        assert "gemini-2.0-flash:generateContent" in url
        assert "key=test-key-123" in url

    def test_no_api_key_in_url_for_non_google_host(self, driver):
        spec = ModelSpec(
            model_id="gemini-proxy", binding="gemini",
            host="https://my-proxy.example.com/v1beta",
            api_key="bearer-token",
        )
        url = driver._build_url(spec)
        assert "key=" not in url  # uses Bearer token instead


# ── Test response parsing ────────────────────────────────────────────


class TestParseResponse:
    def test_parse_standard_response(self, driver, gemini_spec):
        raw = {
            "candidates": [{
                "content": {
                    "role": "model",
                    "parts": [{"text": "Forces come in pairs..."}],
                },
                "finishReason": "STOP",
            }],
            "usageMetadata": {
                "promptTokenCount": 15,
                "candidatesTokenCount": 42,
                "totalTokenCount": 57,
            },
            "modelVersion": "gemini-2.0-flash",
        }
        resp = driver._parse_response(raw, gemini_spec)
        assert resp.text == "Forces come in pairs..."
        assert resp.reasoning is None
        assert resp.usage.prompt_tokens == 15
        assert resp.usage.completion_tokens == 42
        assert resp.metadata["finish_reason"] == "STOP"

    def test_parse_safety_filter(self, driver, gemini_spec):
        raw = {
            "candidates": [{
                "content": {"parts": [{"text": ""}]},
                "finishReason": "SAFETY",
            }],
        }
        with pytest.raises(ModelContentFilterError, match="SAFETY"):
            driver._parse_response(raw, gemini_spec)

    def test_parse_prompt_blocked(self, driver, gemini_spec):
        raw = {
            "promptFeedback": {"blockReason": "OTHER"},
        }
        with pytest.raises(ModelContentFilterError, match="blocked"):
            driver._parse_response(raw, gemini_spec)

    def test_parse_empty_candidates(self, driver, gemini_spec):
        raw = {"candidates": []}
        resp = driver._parse_response(raw, gemini_spec)
        assert resp.text == ""

    def test_parse_multiple_parts(self, driver, gemini_spec):
        raw = {
            "candidates": [{
                "content": {
                    "parts": [
                        {"text": "Part 1. "},
                        {"text": "Part 2."},
                    ],
                },
            }],
        }
        resp = driver._parse_response(raw, gemini_spec)
        assert resp.text == "Part 1. Part 2."

    def test_parse_thinking_model(self, driver):
        spec = ModelSpec(
            model_id="gemini-2.5-pro",
            binding="gemini",
            host="https://generativelanguage.googleapis.com/v1beta",
            capability=ModelCapability(supports_thinking=True),
        )
        raw = {
            "candidates": [{
                "content": {
                    "parts": [
                        {"thought": "Let me analyze this..."},
                        {"text": "The answer is 42."},
                    ],
                },
            }],
        }
        resp = driver._parse_response(raw, spec)
        assert resp.text == "The answer is 42."
        assert resp.reasoning == "Let me analyze this..."


# ── Test MIME guessing ──────────────────────────────────────────────


class TestMimeGuessing:
    def test_known_extensions(self):
        assert _guess_mime("photo.jpg") == "image/jpeg"
        assert _guess_mime("photo.jpeg") == "image/jpeg"
        assert _guess_mime("photo.png") == "image/png"
        assert _guess_mime("photo.webp") == "image/webp"
        assert _guess_mime("audio.mp3") == "audio/mp3"

    def test_unknown_extension(self):
        assert _guess_mime("file.xyz") == "image/jpeg"  # safe default


# ── Integration: three drivers, same test interface ──────────────────


class TestDriverAbstraction:
    """Verify OpenAIDriver, EchoDriver, GeminiDriver all satisfy the same
    complete(messages, spec, **kw) -> ModelResponse contract."""

    @pytest.fixture
    def three_drivers(self):
        from raganything.models.drivers.openai import OpenAIDriver
        from raganything.models.drivers.echo import EchoDriver
        return [OpenAIDriver(), EchoDriver(), GeminiDriver()]

    @pytest.fixture
    def specs_for_drivers(self):
        return {
            "openai": ModelSpec(model_id="test", binding="vllm", host="http://h"),
            "echo": ModelSpec(model_id="test", binding="echo", host="http://h"),
            "gemini": ModelSpec(
                model_id="test", binding="gemini",
                host="https://generativelanguage.googleapis.com/v1beta",
            ),
        }

    def test_all_drivers_have_bindings(self, three_drivers):
        for d in three_drivers:
            assert len(d.bindings) > 0
            assert isinstance(d.bindings, tuple)

    def test_normalize_images_text_only(self, three_drivers):
        cap = ModelCapability()
        messages = [{"role": "user", "content": "Hello"}]
        for d in three_drivers:
            result = d.normalize_images(messages, cap)
            assert result == messages

    def test_build_request_is_deterministic(self, driver, gemini_spec):
        """Same input → same Gemini request body."""
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "Hi"},
        ]
        body1 = driver._build_request(messages, gemini_spec)
        body2 = driver._build_request(messages, gemini_spec)
        assert body1 == body2
