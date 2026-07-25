import pytest
from raganything.service.path_utils import validate_path_component


def test_valid_components():
    assert validate_path_component("tenant_jonex_demo", "tenant_id") == "tenant_jonex_demo"
    assert validate_path_component("doc-dd501d79812495a6c82aa4396ebb8867", "doc_id") == "doc-dd501d79812495a6c82aa4396ebb8867"
    assert validate_path_component("kb_12345", "kb_id") == "kb_12345"
    assert validate_path_component("20260711T084300Z", "timestamp") == "20260711T084300Z"


def test_rejects_path_traversal():
    for bad in ["../../etc", "../passwd", "a/b", "a\\b", ".hidden", "some thing", "a@b"]:
        with pytest.raises(ValueError):
            validate_path_component(bad, "test")


def test_rejects_empty():
    for bad in ["", None]:
        with pytest.raises(ValueError):
            validate_path_component(bad, "test")
