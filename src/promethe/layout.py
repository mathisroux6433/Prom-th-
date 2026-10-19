from __future__ import annotations

from pathlib import Path
import hashlib
import shutil
from typing import Any

from .io_utils import read_json, write_json


WORK_SUBDIRECTORIES = ("requetes", "reponses", "candidates")


def ensure_archive_layout(directory: Path) -> None:
    """Create the non-documentary parts of the v1 archive layout."""
    for name in WORK_SUBDIRECTORIES:
        (directory / "travail" / name).mkdir(parents=True, exist_ok=True)
    (directory / "historique" / "anciennes_versions").mkdir(parents=True, exist_ok=True)


def request_path(directory: Path, filename: str) -> Path:
    ensure_archive_layout(directory)
    return directory / "travail" / "requetes" / filename


def history_path(directory: Path, filename: str) -> Path:
    ensure_archive_layout(directory)
    return directory / "historique" / "anciennes_versions" / filename


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _validated_move(source: Path, destination: Path) -> dict[str, Any]:
    """Copy, validate byte-for-byte, then remove the old pathname."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if _digest(source) != _digest(destination):
            raise RuntimeError(f"Conflit de migration : {destination}")
    else:
        shutil.copy2(source, destination)
    if source.stat().st_size != destination.stat().st_size or _digest(source) != _digest(destination):
        raise RuntimeError(f"Validation de copie échouée : {source}")
    digest = _digest(destination)
    source.unlink()
    return {"source": str(source), "destination": str(destination), "sha256": digest}


def migrate_archive_layout(directory: Path) -> list[dict[str, Any]]:
    """Migrate known temporary artifacts while leaving final documents at root."""
    ensure_archive_layout(directory)
    operations: list[dict[str, Any]] = []
    for source in sorted(directory.iterdir()):
        if not source.is_file():
            continue
        name = source.name
        destination: Path | None = None
        if name.startswith("requete_"):
            destination = directory / "travail" / "requetes" / name
        elif name.startswith("reponse_"):
            destination = directory / "travail" / "reponses" / name
        elif "candidate" in name:
            # A candidate referenced with @file must accompany its response JSON.
            response = directory / "travail" / "reponses" / "reponse_controle_qualite.json"
            bucket = "reponses" if response.exists() and name == "synthese_relue_candidate.md" else "candidates"
            destination = directory / "travail" / bucket / name
        elif name.startswith("synthese_video_avant_relecture"):
            destination = directory / "historique" / "anciennes_versions" / name
        if destination is not None:
            operations.append(_validated_move(source, destination))
    state_path = directory / "etat_pipeline.json"
    if state_path.exists() and operations:
        state = read_json(state_path)
        replacements = {
            Path(item["source"]).name: Path(item["destination"]).relative_to(directory).as_posix()
            for item in operations
        }

        def update(value: Any) -> Any:
            if isinstance(value, dict):
                return {key: update(item) for key, item in value.items()}
            if isinstance(value, list):
                return [update(item) for item in value]
            if isinstance(value, str):
                name = Path(value.replace("\\", "/")).name
                return replacements.get(name, value)
            return value

        write_json(state_path, update(state))
    return operations
