"""TaskRepository — JSON file-based task persistence."""

import json
import os
from pathlib import Path
from raganything.service.models import TaskInfo


class TaskRepository:
    """Persist TaskInfo objects as JSON files under base_dir/{tenant}/{kb}/tasks/."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _task_path(self, tenant_id: str, kb_id: str, task_id: str) -> Path:
        kb = kb_id or "default_kb"
        return Path(self.base_dir) / tenant_id / kb / "tasks" / f"{task_id}.json"

    def save(self, task: TaskInfo) -> None:
        path = self._task_path(task.tenant_id, task.kb_id, task.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(
                task.model_dump(mode="json"), f, ensure_ascii=False, default=str,
            )
        os.replace(tmp, path)

    def load_all(self) -> dict[str, TaskInfo]:
        tasks: dict[str, TaskInfo] = {}
        base = Path(self.base_dir)
        if not base.is_dir():
            return tasks
        for task_file in base.rglob("*/tasks/*.json"):
            try:
                data = json.loads(task_file.read_text(encoding="utf-8"))
                task = TaskInfo(**data)
                tasks[task.task_id] = task
            except Exception:
                continue
        return tasks

    def delete(self, task_id: str, tenant_id: str, kb_id: str) -> None:
        path = self._task_path(tenant_id, kb_id, task_id)
        if path.exists():
            path.unlink()
