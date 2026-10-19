from __future__ import annotations

import json
from pathlib import Path

from .errors import PrometheError
from .io_utils import read_json, write_text
from .layout import request_path


def prompt_for(directory: Path) -> str:
    metadata = read_json(directory / "metadata.json")
    transcript = (directory / "transcription_corrigee.txt").read_text(encoding="utf-8")
    index_path = directory / "index_video.json"
    index = index_path.read_text(encoding="utf-8") if index_path.exists() else "(index absent)"
    return f"""Rédige une synthèse documentaire exhaustive en Markdown à partir des seules sources ci-dessous.
Ne vérifie pas les affirmations à l'extérieur et ne les transforme pas en faits établis. Distingue explicitement les propos de l'auteur, les personnes ou documents cités, les hypothèses et les incertitudes. N'invente rien.

Le document doit contenir le titre, l'auteur ou la chaîne, la date et l'URL, puis l'objet général et la thèse, des chapitres et sous-chapitres, tous les arguments importants, exemples, chiffres et liens logiques, et une conclusion fidèle. Ajoute des horodatages cliquables vers la vidéo. Toute citation entre guillemets doit être exactement vérifiable dans la transcription. Utilise l'index comme contrôle de couverture, sans recopier mécaniquement ses listes. La synthèse doit rester détaillée même pour une vidéo longue et dense.

MÉTADONNÉES :
{json.dumps(metadata, ensure_ascii=False, indent=2)}

INDEX DOCUMENTAIRE :
{index}

TRANSCRIPTION CORRIGÉE :
{transcript}"""


def export_prompt(directory: Path, output: Path | None = None) -> Path:
    destination = output or request_path(directory, "requete_synthese.txt")
    write_text(destination, prompt_for(directory))
    return destination


def import_synthesis(directory: Path, source: Path) -> str:
    try:
        content = source.read_text(encoding="utf-8-sig").strip()
    except OSError as exc:
        raise PrometheError(f"Réponse de synthèse illisible : {exc}") from exc
    if len(content) < 200 or not content.startswith("#") or "##" not in content:
        raise PrometheError("Synthèse invalide : Markdown structuré insuffisant.")
    write_text(directory / "synthese_video.md", content + "\n")
    return content
