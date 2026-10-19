from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import PrometheError
from .io_utils import read_json, write_text
from .layout import request_path

REPORT_KEYS = {"schema_version", "video_id", "verdict", "problems", "revised_synthesis"}
PROBLEM_KEYS = {"category", "severity", "description", "source_evidence", "timestamp", "correction"}
VERDICTS = {"conforme", "corrigee", "echec"}


def prompt_for(directory: Path) -> str:
    metadata = read_json(directory / "metadata.json")
    synthesis = (directory / "synthese_video.md").read_text(encoding="utf-8")
    index = (directory / "index_video.json").read_text(encoding="utf-8")
    transcript = (directory / "transcription_corrigee.txt").read_text(encoding="utf-8")
    template = {
        "schema_version": "1.0",
        "video_id": metadata["id"],
        "verdict": "conforme ou corrigee",
        "problems": [{
            "category": "chiffre|date|population|sens|attribution|horodatage|citation|omission|coherence",
            "severity": "mineure|importante|critique",
            "description": "problème constaté",
            "source_evidence": "preuve précise tirée des sources archivées",
            "timestamp": "HH:MM:SS ou chaîne vide",
            "correction": "correction effectuée ou recommandée",
        }],
        "revised_synthesis": "texte Markdown intégral, ou @file:nom_du_fichier.md",
    }
    return f"""Effectue un contrôle qualité documentaire de la synthèse ci-dessous.

Compare-la uniquement à l'index et à la transcription corrigée archivés. N'effectue aucun fact-checking externe. Contrôle les chiffres, dates, pourcentages, populations statistiques, inversions de sens, raisonnements déformés, attributions, horodatages, citations exactes, arguments importants omis et la cohérence avec l'index.

Corrige seulement les erreurs confirmées par les sources. Ne réécris pas inutilement les passages conformes. Si une incertitude ne peut pas être tranchée, conserve la formulation prudente. Retourne uniquement un objet JSON strict suivant cette structure :
{json.dumps(template, ensure_ascii=False, indent=2)}

Le champ revised_synthesis doit toujours contenir le document Markdown complet : corrigé si nécessaire, sinon identique. Pour une synthèse très longue, il peut contenir `@file:nom_du_fichier.md` et le fichier Markdown doit être placé à côté du JSON de réponse ; seuls les noms de fichiers simples sont acceptés. Le verdict vaut "conforme" si aucune correction n'est requise, "corrigee" si des corrections ont été appliquées.

MÉTADONNÉES :
{json.dumps(metadata, ensure_ascii=False, indent=2)}

SYNTHÈSE À RELIRE :
{synthesis}

INDEX DOCUMENTAIRE :
{index}

TRANSCRIPTION CORRIGÉE :
{transcript}"""


def export_prompt(directory: Path, output: Path | None = None) -> Path:
    for required in ("synthese_video.md", "index_video.json", "transcription_corrigee.txt"):
        if not (directory / required).is_file():
            raise PrometheError(f"Contrôle qualité impossible : {required} est absent.")
    destination = output or request_path(directory, "requete_controle_qualite.txt")
    write_text(destination, prompt_for(directory))
    return destination


def _report_markdown(data: dict[str, Any], changed: bool) -> str:
    lines = [
        "# Rapport de contrôle qualité de la synthèse",
        "",
        f"- **Vidéo :** `{data['video_id']}`",
        f"- **Verdict :** `{data['verdict']}`",
        f"- **Problèmes signalés :** {len(data['problems'])}",
        f"- **Synthèse modifiée :** {'oui' if changed else 'non'}",
    ]
    lines.extend(["", "## Problèmes et corrections", ""])
    if not data["problems"]:
        lines.append("Aucun problème confirmé dans les sources archivées.")
    for number, problem in enumerate(data["problems"], 1):
        lines.extend([
            f"### {number}. {problem['category']} — {problem['severity']}", "",
            f"- **Constat :** {problem['description']}",
            f"- **Preuve interne :** {problem['source_evidence']}",
            f"- **Horodatage :** {problem['timestamp'] or 'non applicable'}",
            f"- **Correction :** {problem['correction']}", "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def import_review(directory: Path, source: Path) -> dict[str, Any]:
    try:
        data = read_json(source)
    except (OSError, json.JSONDecodeError) as exc:
        raise PrometheError(f"Réponse de contrôle qualité invalide : {exc}") from exc
    missing = REPORT_KEYS - set(data) if isinstance(data, dict) else REPORT_KEYS
    if missing:
        raise PrometheError("Champs de contrôle qualité manquants : " + ", ".join(sorted(missing)))
    metadata = read_json(directory / "metadata.json")
    if data["schema_version"] != "1.0" or data["video_id"] != metadata["id"]:
        raise PrometheError("Identifiant vidéo ou version de contrôle qualité incorrect.")
    if data["verdict"] not in VERDICTS or not isinstance(data["problems"], list):
        raise PrometheError("Verdict ou liste de problèmes invalide.")
    for problem in data["problems"]:
        if not isinstance(problem, dict) or PROBLEM_KEYS - set(problem):
            raise PrometheError("Un problème du rapport ne respecte pas le schéma attendu.")
    revised = data["revised_synthesis"]
    if isinstance(revised, str) and revised.startswith("@file:"):
        filename = revised.removeprefix("@file:")
        if not filename or Path(filename).name != filename:
            raise PrometheError("Référence de synthèse relue non sûre.")
        try:
            revised = (source.parent / filename).read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise PrometheError(f"Fichier de synthèse relue illisible : {exc}") from exc
    if not isinstance(revised, str) or len(revised.strip()) < 200 or not revised.lstrip().startswith("#"):
        raise PrometheError("La synthèse relue complète est absente ou invalide.")

    synthesis_path = directory / "synthese_video.md"
    previous = synthesis_path.read_text(encoding="utf-8")
    normalized = revised.strip() + "\n"
    changed = normalized != previous
    if changed:
        write_text(synthesis_path, normalized)
    write_text(directory / "rapport_controle_qualite.md", _report_markdown(data, changed))
    return {"data": data, "changed": changed}
