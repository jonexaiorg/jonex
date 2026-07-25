import pytest
from pathlib import Path
from raganything.service.task_repository import TaskRepository
from raganything.service.models import TaskInfo, TaskStatus


@pytest.fixture
def repo(tmp_path):
    return TaskRepository(base_dir=str(tmp_path))


@pytest.fixture
def task():
    return TaskInfo(
        task_id="task-001",
        tenant_id="tenant_jonex_demo",
        kb_id="kb-123",
        name="test.pdf",
        file_path="/data/test.pdf",
        status=TaskStatus.PROCESSING,
    )


class TestTaskRepository:
    def test_save_and_load(self, repo, task):
        repo.save(task)
        loaded = repo.load_all()
        assert "task-001" in loaded
        assert loaded["task-001"].name == "test.pdf"

    def test_save_creates_correct_path(self, repo, task):
        repo.save(task)
        expected = (
            Path(repo.base_dir)
            / "tenant_jonex_demo" / "kb-123" / "tasks" / "task-001.json"
        )
        assert expected.exists()

    def test_delete_removes_file(self, repo, task):
        repo.save(task)
        repo.delete("task-001", task.tenant_id, task.kb_id)
        loaded = repo.load_all()
        assert "task-001" not in loaded

    def test_load_all_skips_nonexistent_dirs(self, repo):
        loaded = repo.load_all()
        assert loaded == {}
