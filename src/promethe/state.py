from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io_utils import read_json, write_json

STEPS = ("metadata", "download", "transcription", "correction", "index", "synthesis", "quality_control")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def initial_state(video_id: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "video_id": video_id,
        "updated_at": now(),
        "steps": {name: {"status": "pending", "error": None} for name in STEPS},
    }


def load_state(directory: Path, video_id: str) -> dict[str, Any]:
    path = directory / "etat_pipeline.json"
    state = read_json(path) if path.exists() else initial_state(video_id)
    steps = state.setdefault("steps", {})
    for name in STEPS:
        steps.setdefault(name, {"status": "pending", "error": None})
    return state


def set_step(directory: Path, state: dict[str, Any], step: str, status: str,
             error: str | None = None, **details: Any) -> None:
    state["steps"][step] = {"status": status, "error": error, **details}
    state["updated_at"] = now()
    write_json(directory / "etat_pipeline.json", state)
