import pytest, tempfile, yaml
from pathlib import Path
from raganything.service.config_resolver import ConfigResolver
from raganything.service.models import CreateTaskRequest, TaskMode


@pytest.fixture
def tmp_config_dirs():
    with tempfile.TemporaryDirectory() as d:
        # Global preset
        presets = Path(d) / "presets"
        presets.mkdir()
        global_preset = {
            "llm": "global-llm",
            "parser": "mineru",
            "modalities": ["image"],
            "output_dir": "/default",
        }
        with open(presets / "test.yaml", "w") as f:
            yaml.dump(global_preset, f)

        # Tenant-level preset (only overrides llm)
        tenant_presets = Path(d) / "tenant_x" / "kb_y" / "presets"
        tenant_presets.mkdir(parents=True)
        tenant_preset = {"llm": "tenant-llm"}
        with open(tenant_presets / "test.yaml", "w") as f:
            yaml.dump(tenant_preset, f)

        yield d


def test_deep_merge_tenant_overrides_llm_only(tmp_config_dirs):
    resolver = ConfigResolver(
        profiles_dir=str(tmp_config_dirs),
        presets_dir=str(Path(tmp_config_dirs) / "presets"),
    )
    req = CreateTaskRequest(
        mode=TaskMode.PRESET, file_path="test.pdf",
        preset="test", kb_id="kb_y",
    )
    snapshot = resolver.resolve(req, tenant_id="tenant_x", kb_id="kb_y")
    # llm should be overridden by tenant, parser inherits global
    assert snapshot["llm_model"] == "tenant-llm"
    assert snapshot["parser"] == "mineru"
    assert snapshot["parser_output_dir"] == "/default"


def test_no_tenant_kb_falls_back_to_global(tmp_config_dirs):
    resolver = ConfigResolver(
        profiles_dir=str(tmp_config_dirs),
        presets_dir=str(Path(tmp_config_dirs) / "presets"),
    )
    req = CreateTaskRequest(
        mode=TaskMode.PRESET, file_path="test.pdf", preset="test",
    )
    snapshot = resolver.resolve(req)
    assert snapshot["llm_model"] == "global-llm"
