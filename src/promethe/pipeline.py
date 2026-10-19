from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .archive import archive_path, find_video
from .downloader import download_audio, inspect_url, normalized_metadata
from .errors import PrometheError
from .indexer import export_prompt
from .io_utils import write_json
from .layout import ensure_archive_layout
from .state import load_state, set_step
from .synthesizer import export_prompt as export_synthesis_prompt
from .transcriber import transcribe


def process(url: str, root: Path, model: str = "medium", stop_after: str | None = None) -> Path:
    info = inspect_url(url)
    metadata = normalized_metadata(info)
    existing = find_video(root, metadata["id"])
    directory = existing or archive_path(root, metadata)
    directory.mkdir(parents=True, exist_ok=True)
    ensure_archive_layout(directory)
    state = load_state(directory, metadata["id"])
    try:
        if state["steps"]["metadata"]["status"] != "complete":
            write_json(directory / "metadata.json", metadata)
            set_step(directory, state, "metadata", "complete")
        if stop_after == "metadata": return directory

        audio_files = [p for p in directory.glob("audio.*") if p.suffix not in {".part", ".ytdl"}]
        if state["steps"]["download"]["status"] != "complete" or not audio_files:
            audio = download_audio(url, directory)
            set_step(directory, state, "download", "complete", file=audio.name)
        else:
            audio = audio_files[0]
        if stop_after == "download": return directory

        if state["steps"]["transcription"]["status"] != "complete":
            transcribe(audio, directory, model)
            set_step(directory, state, "transcription", "complete", model=model, device="cuda")
        if stop_after == "transcription": return directory

        corrected = directory / "transcription_corrigee.txt"
        if not corrected.exists():
            shutil.copyfile(directory / "transcription_brute.txt", corrected)
            set_step(directory, state, "correction", "complete", mode="copie_identique_non_corrigee")
        elif state["steps"]["correction"]["status"] != "complete":
            identical = corrected.read_bytes() == (directory / "transcription_brute.txt").read_bytes()
            set_step(
                directory, state, "correction", "complete",
                mode="copie_identique_non_corrigee" if identical else "fichier_existant",
            )
        if stop_after == "correction": return directory

        if not (directory / "index_video.json").exists():
            prompt = export_prompt(directory)
            set_step(directory, state, "index", "waiting_manual", prompt=prompt.name,
                     error="Aucun fournisseur IA automatisé configuré")
            return directory
        if state["steps"]["index"]["status"] != "complete":
            set_step(directory, state, "index", "complete", source="fichier_existant")

        synthesis = directory / "synthese_video.md"
        if not synthesis.exists():
            prompt = export_synthesis_prompt(directory)
            set_step(directory, state, "synthesis", "waiting_manual", prompt=prompt.name,
                     error="Aucun fournisseur IA automatisé configuré")
        elif state["steps"]["synthesis"]["status"] != "complete":
            set_step(directory, state, "synthesis", "complete", source="fichier_existant")
        if synthesis.exists() and state["steps"]["quality_control"]["status"] == "pending":
            set_step(directory, state, "quality_control", "pending", optional=True,
                     note="Relecture IA facultative non effectuée")
        return directory
    except Exception as exc:
        current = next((name for name, value in state["steps"].items() if value["status"] == "pending"), "index")
        set_step(directory, state, current, "failed", error=str(exc))
        if isinstance(exc, PrometheError): raise
        raise


def process_file(path: Path, root: Path, model: str = "medium") -> list[tuple[str, str]]:
    results = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        url = line.strip()
        if not url or url.startswith("#"): continue
        try:
            results.append((url, str(process(url, root, model))))
        except Exception as exc:
            results.append((url, f"ERREUR: {exc}"))
    return results
