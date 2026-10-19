from __future__ import annotations

import re
from pathlib import Path

from .errors import PrometheError
from .io_utils import read_json, write_text
from .layout import request_path

LINE = re.compile(r"^\[(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\] ?(.*)$")


def _timings(content: str) -> list[tuple[str, str]]:
    result = []
    for number, line in enumerate(content.splitlines(), 1):
        match = LINE.match(line)
        if not match:
            raise PrometheError(f"Transcription invalide à la ligne {number} : horodatage absent ou altéré.")
        result.append((match.group(1), match.group(2)))
    return result


def prompt_for(directory: Path) -> str:
    metadata = read_json(directory / "metadata.json")
    raw = (directory / "transcription_brute.txt").read_text(encoding="utf-8")
    return f"""Corrige contextuellement la transcription horodatée ci-dessous.

Règles obligatoires : conserve exactement une ligne par segment et exactement les deux horodatages de chaque ligne ; ne résume pas ; ne reformule pas le registre oral ; corrige seulement les erreurs de reconnaissance établies par le contexte (noms propres, institutions, lieux, événements, termes techniques et expressions manifestement mal reconnues). Si une forme reste incertaine, conserve-la et ajoute immédiatement `[incertain]`. Retourne uniquement la transcription complète corrigée.

MÉTADONNÉES :
{metadata}

TRANSCRIPTION BRUTE :
{raw}"""


def export_prompt(directory: Path, output: Path | None = None) -> Path:
    destination = output or request_path(directory, "requete_correction.txt")
    write_text(destination, prompt_for(directory))
    return destination


def import_correction(directory: Path, source: Path) -> str:
    try:
        corrected = source.read_text(encoding="utf-8-sig").strip() + "\n"
        raw = (directory / "transcription_brute.txt").read_text(encoding="utf-8")
    except OSError as exc:
        raise PrometheError(f"Correction illisible : {exc}") from exc
    raw_times, corrected_times = _timings(raw), _timings(corrected)
    if raw_times != corrected_times:
        raise PrometheError("La correction a modifié le nombre, l’ordre ou les valeurs des horodatages.")
    write_text(directory / "transcription_corrigee.txt", corrected)
    return corrected
