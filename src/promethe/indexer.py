from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import PrometheError
from .io_utils import read_json, write_json, write_text
from .layout import request_path

INDEX_KEYS = {
    "schema_version", "video_id", "resume_general", "themes_principaux",
    "sujets_secondaires", "mots_cles", "variantes_lexicales", "personnes",
    "organismes", "concepts", "evenements_lois_reglementations", "reperes_temporels",
    "expressions_representatives", "citations_exactes", "arguments_positions",
    "lieux_periodes", "relations_documentaires",
}


def prompt_for(directory: Path) -> str:
    metadata = read_json(directory / "metadata.json")
    transcript = (directory / "transcription_corrigee.txt").read_text(encoding="utf-8")
    template = {key: ([] if key not in {"schema_version", "video_id", "resume_general"} else "") for key in sorted(INDEX_KEYS)}
    template["schema_version"] = "1.1"
    template["video_id"] = metadata["id"]
    return f"""Crée un index documentaire fidèle en JSON strict. Ne juge pas la véracité. Distingue pour personnes, organismes et événements le niveau 'mention' ou 'developpe'. N'invente rien. Les citations_exactes doivent être verbatim ; les expressions_representatives ne sont pas des citations. Chaque élément thématique utile porte si possible des horodatages. Retourne uniquement un objet suivant cette structure :\n{json.dumps(template, ensure_ascii=False, indent=2)}\n\nMÉTADONNÉES :\n{json.dumps(metadata, ensure_ascii=False, indent=2)}\n\nTRANSCRIPTION :\n{transcript}"""


def export_prompt(directory: Path, output: Path | None = None) -> Path:
    destination = output or request_path(directory, "requete_indexation.txt")
    write_text(destination, prompt_for(directory))
    return destination


def import_index(directory: Path, source: Path) -> dict[str, Any]:
    try:
        data = read_json(source)
    except (OSError, json.JSONDecodeError) as exc:
        raise PrometheError(f"Réponse d'index invalide : {exc}") from exc
    missing = INDEX_KEYS - set(data)
    if missing:
        raise PrometheError("Champs d'index manquants : " + ", ".join(sorted(missing)))
    video_id = read_json(directory / "metadata.json")["id"]
    if data["video_id"] != video_id or data["schema_version"] != "1.1":
        raise PrometheError("Identifiant vidéo ou version de schéma incorrect.")
    write_json(directory / "index_video.json", data)
    return data
