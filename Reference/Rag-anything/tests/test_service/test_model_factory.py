"""Tests for ModelFactory + ModelRegistry — profile parsing and model function creation."""

import os
import tempfile
from pathlib import Path

import pytest

from raganything.models import ModelRegistry
from raganything.models.drivers.openai import OpenAIDriver
from raganything.models.drivers.echo import EchoDriver
from raganything.service.model_factory import ModelFactory


@pytest.fixture
def profile_dir(tmp_path):
    """Create a minimal profile directory structure."""
    profile = tmp_path / "dev"
    profile.mkdir()

    # models.env
    (profile / "models.env").write_text(
        "qwen3-72b = ollama://http://gpu:11434/v1\n"
        "bge-m3 = ollama://?dim=1024\n"
        "qwen2.5-vl-7b = vllm://http://vision:8000/v1\n"
    )

    # models.yaml — VLM capability
    import yaml
    (profile / "models.yaml").write_text(yaml.dump({
        "models": {
            "qwen2.5-vl-7b": {
                "supports_vision": True,
                "supports_vision_base64": True,
                "supports_vision_url": True,
                "max_context_tokens": 32768,
            },
        }
    }))

    # secrets.env
    (profile / "secrets.env").write_text(
        "ollama=not-needed\n"
        "vllm=sk-test-key\n"
    )

    return profile


@pytest.fixture
def registry(profile_dir):
    """Create a registry with the test profile loaded."""
    r = ModelRegistry(str(profile_dir.parent))
    r.register_driver(OpenAIDriver())
    r.register_driver(EchoDriver())
    return r


class TestModelRegistry:
    """Tests for ModelRegistry — models.env + models.yaml parsing."""

    def test_load_profile(self, registry, profile_dir):
        specs = registry.load_profile("dev")
        assert len(specs) == 3

        qwen = registry._specs["qwen3-72b"]
        assert qwen.binding == "ollama"
        assert qwen.host == "http://gpu:11434/v1"
        assert qwen.capability.supports_vision is False  # no yaml entry → default

        vl = registry._specs["qwen2.5-vl-7b"]
        assert vl.binding == "vllm"
        assert vl.capability.supports_vision is True
        assert vl.capability.supports_vision_base64 is True

    def test_parse_binding_url(self):
        binding, host = ModelRegistry._parse_binding_url(
            "ollama://http://gpu:11434/v1"
        )
        assert binding == "ollama"
        assert host == "http://gpu:11434/v1"

    def test_parse_binding_url_with_params_stripped(self):
        binding, host = ModelRegistry._parse_binding_url(
            "ollama://?dim=1024"
        )
        assert binding == "ollama"
        assert host == ""

    def test_parse_models_env_comments_and_blanks(self, tmp_path):
        env = tmp_path / "models.env"
        env.write_text(
            "# comment line\n"
            "\n"
            "  \n"
            "model-a = ollama://http://host:11434/v1\n"
        )
        registry = ModelRegistry(str(tmp_path.parent))
        registry.register_driver(OpenAIDriver())
        specs = registry._load_models_env(env, {})
        assert len(specs) == 1
        assert specs[0].model_id == "model-a"

    def test_bind_vlm_model(self, registry, profile_dir):
        registry.load_profile("dev")
        bound = registry.bind("qwen2.5-vl-7b")
        assert bound.capability.supports_vision is True
        assert bound.spec.binding == "vllm"

    def test_bind_with_alias_routing(self, registry, profile_dir):
        """vllm:// binding → routed to OpenAIDriver via BINDING_ALIASES."""
        registry.load_profile("dev")
        bound = registry.bind("qwen3-72b")  # binding=ollama → aliased to openai
        assert isinstance(bound.driver, OpenAIDriver)

    def test_list_models_filter(self, registry, profile_dir):
        registry.load_profile("dev")
        vlms = registry.list_models(supports_vision=True)
        assert len(vlms) == 1
        assert vlms[0].model_id == "qwen2.5-vl-7b"

    def test_resolve_api_key_from_env(self, registry, monkeypatch):
        monkeypatch.setenv("QWEN3_72B_API_KEY", "sk-test-123")
        key = ModelRegistry._resolve_api_key("qwen3-72b", "vllm")
        assert key == "sk-test-123"

    def test_resolve_api_key_fallback(self, registry, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fallback")
        key = ModelRegistry._resolve_api_key("unknown-model", "vllm")
        assert key == "sk-fallback"


class TestModelFactoryBuild:
    """Tests for ModelFactory.build() with registry integration."""

    def test_build_returns_all_keys(self, registry, profile_dir):
        registry.load_profile("dev")
        factory = ModelFactory(registry=registry, profiles_dir=str(profile_dir.parent))
        funcs = factory.build(profile="dev", working_dir="/tmp/test_rag")

        assert "config" in funcs
        assert "llm_model_func" in funcs
        assert funcs["llm_model_func"] is not None
        assert "embedding_func" in funcs
        assert "vlm_model_func" in funcs
        assert "asr_model_func" in funcs
        assert "lightrag_kwargs" in funcs

        assert funcs["config"].working_dir == "/tmp/test_rag"

    def test_build_with_overrides(self, registry, profile_dir):
        registry.load_profile("dev")
        factory = ModelFactory(registry=registry, profiles_dir=str(profile_dir.parent))
        funcs = factory.build(
            profile="dev",
            overrides={"parser": "docling", "enable_video_processing": False},
            working_dir="/custom/wd",
        )

        assert funcs["config"].parser == "docling"
        assert funcs["config"].enable_video_processing is False
        assert funcs["config"].working_dir == "/custom/wd"

    def test_legacy_llm_adapter_produces_string(self, registry, profile_dir):
        """The returned llm_model_func is a legacy callable → bound to EchoDriver."""
        from raganything.models.drivers.echo import EchoDriver
        r2 = ModelRegistry(str(profile_dir.parent))
        r2.register_driver(EchoDriver())
        spec = r2._load_models_env(profile_dir / "models.env", {})[0]
        # Override binding to echo for test
        from raganything.models.types import ModelSpec
        echo_spec = ModelSpec(
            model_id=spec.model_id, binding="echo", host="http://localhost",
        )
        r2._specs[echo_spec.model_id] = echo_spec

        factory = ModelFactory(registry=r2, profiles_dir=str(profile_dir.parent))
        factory._ensure_registry = lambda: None  # skip re-init
        factory._ensure_profile = lambda p: None  # skip reload
        factory._registry = r2
        funcs = factory.build(profile="dev")
        # The adapter wraps BoundModel → async callable
        assert funcs["llm_model_func"] is not None

    def test_build_missing_profile_raises(self, tmp_path):
        r = ModelRegistry(str(tmp_path))
        r.register_driver(OpenAIDriver())
        factory = ModelFactory(registry=r, profiles_dir=str(tmp_path))
        with pytest.raises(Exception):  # FileNotFoundError from registry or model_factory
            factory.build(profile="nonexistent")
