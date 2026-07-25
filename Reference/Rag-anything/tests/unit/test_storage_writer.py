import pytest, tempfile, yaml
from pathlib import Path
from raganything.service.storage_writer import StorageWriter


@pytest.fixture
def storage():
    with tempfile.TemporaryDirectory() as d:
        yield StorageWriter(root=Path(d))


def test_create_staging_and_commit(storage):
    doc_id = "doc-test123"
    ts = "20260711T120000Z"
    staging = storage.create_staging("tenant_x", doc_id, ts)
    assert staging.exists()
    # Write task.yaml
    task_data = {"version": 1, "doc_id": doc_id, "stage": "parsed"}
    storage.write_task_yaml_atomic(staging / "task.yaml", task_data)
    assert (staging / "task.yaml").exists()
    # Commit
    final = storage.commit("tenant_x", doc_id, ts)
    assert final.exists()
    assert (final / "task.yaml").exists()
    # Staging cleaned up
    assert not staging.exists()


def test_staged_task_yaml_update(storage):
    doc_id = "doc-test456"
    ts = "20260711T130000Z"
    staging = storage.create_staging("tenant_x", doc_id, ts)
    yaml_path = staging / "task.yaml"

    # Stage 1: parsed
    storage.write_task_yaml_atomic(yaml_path, {"stage": "parsed", "entities": None})
    with open(yaml_path) as f:
        assert yaml.safe_load(f)["stage"] == "parsed"

    # Stage 2: indexed
    def updater(data):
        data["stage"] = "indexed"
        data["chunks"] = 109
    storage.update_task_yaml_atomic(yaml_path, updater)
    with open(yaml_path) as f:
        d = yaml.safe_load(f)
        assert d["stage"] == "indexed"
        assert d["chunks"] == 109

    storage.commit("tenant_x", doc_id, ts)


def test_rejects_invalid_path_components(storage):
    with pytest.raises(ValueError):
        storage.create_staging("bad/tenant", "doc", "ts")
    with pytest.raises(ValueError):
        storage.create_staging("tenant", "../doc", "ts")


def test_build_storage_info(storage):
    info = StorageWriter.build_storage_info(
        storage.root, "tenant_x", "doc-x",
        "20260711T120000Z", "http://cdn.example.com/mineru",
        has_mineru=True, has_video=False,
    )
    assert info["mineru_dir"] == "tenant_x/doc-x/versions/20260711T120000Z/mineru"
    assert info["asset_base_url"] == "http://cdn.example.com/mineru"
    assert info["latest_url"] == "http://cdn.example.com/mineru/tenant_x/doc-x/latest/mineru"
