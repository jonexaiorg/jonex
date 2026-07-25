import pytest
from raganything.service.validate_id import validate_id, workspace


class TestValidateId:
    def test_accepts_valid_id(self):
        assert validate_id("tenant_jonex_demo", "tenant_id") == "tenant_jonex_demo"
        assert validate_id("kb-123", "kb_id") == "kb-123"
        assert validate_id("abc_DEF_ghi-789", "test") == "abc_DEF_ghi-789"

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="Invalid tenant_id"):
            validate_id("", "tenant_id")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="Invalid kb_id"):
            validate_id("../etc", "kb_id")
        with pytest.raises(ValueError, match="Invalid kb_id"):
            validate_id("a/b", "kb_id")

    def test_rejects_double_underscore(self):
        with pytest.raises(ValueError, match="reserved '__'"):
            validate_id("a__b", "tenant_id")

    def test_rejects_null_bytes(self):
        with pytest.raises(ValueError, match="Invalid kb_id"):
            validate_id("kb\x00123", "kb_id")


class TestWorkspace:
    def test_tenant_only(self):
        assert workspace("t1", "") == "t1"

    def test_tenant_and_kb(self):
        assert workspace("t1", "kb1") == "t1|kb1"

    def test_custom_separator(self, monkeypatch):
        monkeypatch.setenv("WORKSPACE_SEPARATOR", "__")
        assert workspace("t1", "kb1") == "t1__kb1"
