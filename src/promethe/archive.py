from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .io_utils import safe_component
from .layout import WORK_SUBDIRECTORIES

EXPECTED = (
    "metadata.json", "audio.webm", "segments.json", "transcription_brute.txt",
    "transcription_corrigee.txt", "index_video.json", "synthese_video.md",
    "etat_pipeline.json", "rapport_controle_qualite.md",
)


def archive_path(root: Path, metadata: dict[str, Any]) -> Path:
    upload = str(metadata.get("upload_date") or "00000000")
    try:
        parsed = datetime.strptime(upload, "%Y%m%d")
        year, date = str(parsed.year), parsed.strftime("%Y-%m-%d")
    except ValueError:
        year, date = "date_inconnue", "date_inconnue"
    channel = safe_component(str(metadata.get("channel") or metadata.get("uploader") or "chaine_inconnue"))
    video_id = safe_component(str(metadata["id"]))
    return root / channel / year / f"{date}_{video_id}"


def find_video(root: Path, video_id: str) -> Path | None:
    matches = list(root.glob(f"*/*/*_{safe_component(video_id)}")) if root.exists() else []
    if len(matches) > 1:
        raise RuntimeError(f"Plusieurs archives portent l'identifiant {video_id}")
    return matches[0] if matches else None


def verify_archive(directory: Path) -> dict[str, Any]:
    present = {name: (directory / name).is_file() for name in EXPECTED}
    layout = {
        **{f"travail/{name}": (directory / "travail" / name).is_dir() for name in WORK_SUBDIRECTORIES},
        "historique/anciennes_versions": (directory / "historique" / "anciennes_versions").is_dir(),
    }
    return {
        "archive": str(directory),
        "complete": all(present.values()) and all(layout.values()),
        "files": present,
        "layout": layout,
    }
