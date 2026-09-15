"""
Shared Task Memory
-------------------
In-process store of task state. A prototype-scale stand-in for a real
DB/Redis-backed store — the interface is what matters (get/create/update),
so swapping the backing store later doesn't touch the orchestrator.
"""
import time
import uuid

_TASKS = {}


def new_task(original_task: str, task_type: str, difficulty: str) -> str:
    task_id = uuid.uuid4().hex[:12]
    _TASKS[task_id] = {
        "task_id": task_id,
        "original_task": original_task,
        "task_type": task_type,
        "difficulty": difficulty,
        "status": "running",
        "current_model": None,
        "history": [],
        "generated_files": [],
        "errors": [],
        "created_at": time.time(),
    }
    return task_id


def get_task(task_id: str) -> dict:
    return _TASKS.get(task_id)


def add_history(task_id: str, entry: dict):
    task = _TASKS.get(task_id)
    if task is None:
        return
    entry = dict(entry)
    entry["timestamp"] = time.time()
    task["history"].append(entry)
    if entry.get("model"):
        task["current_model"] = entry["model"]
    if entry.get("status") == "failed" and entry.get("error"):
        task["errors"].append({"model": entry.get("model"), "error": entry["error"]})


def set_status(task_id: str, status: str):
    task = _TASKS.get(task_id)
    if task is not None:
        task["status"] = status


def build_recovery_context(task_id: str) -> dict:
    """What we hand to the next model after a failure: the original
    task, whatever the previous model produced, and why it stopped."""
    task = _TASKS.get(task_id)
    if task is None:
        return {}
    last = task["history"][-1] if task["history"] else {}
    return {
        "original_task": task["original_task"],
        "previous_model": last.get("model"),
        "previous_partial_output": last.get("content", ""),
        "error": last.get("error", ""),
        "instruction": (
            "Continue this task from the previous model's current state. "
            "Do not restart unnecessarily. Use the previous output and "
            "error information to continue the unfinished work."
        ),
    }
