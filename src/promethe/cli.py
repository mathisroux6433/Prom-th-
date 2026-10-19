from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .archive import find_video, verify_archive
from .layout import migrate_archive_layout
from .errors import PrometheError
from .indexer import export_prompt, import_index
from .pipeline import process, process_file
from .quality import export_prompt as export_quality_prompt, import_review
from .state import load_state, set_step
from .synthesizer import export_prompt as export_synthesis_prompt, import_synthesis


def directory_for(root: Path, video_id: str) -> Path:
    directory = find_video(root, video_id)
    if not directory:
        raise PrometheError(f"Archive introuvable : {video_id}")
    return directory


def offer_quality_review(directory: Path) -> None:
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    state = load_state(directory, metadata["id"])
    if not (directory / "synthese_video.md").exists() or state["steps"]["quality_control"]["status"] != "pending":
        return
    try:
        answer = input("Voulez-vous effectuer une relecture IA pour affiner la synthèse ? [Oui / Plus tard / Non] ").strip().lower()
    except EOFError:
        answer = "plus tard"
    if answer in {"oui", "o", "yes", "y"}:
        prompt = export_quality_prompt(directory)
        set_step(directory, state, "quality_control", "waiting_manual", prompt=prompt.name, optional=True)
        print(f"Requête de relecture prête : {prompt}")
    elif answer in {"non", "n", "no"}:
        set_step(directory, state, "quality_control", "declined", optional=True)
        print("Relecture IA facultative refusée.")
    else:
        set_step(directory, state, "quality_control", "pending", optional=True,
                 note="Relecture reportée")
        print("Relecture IA laissée en attente.")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="promethe", description="Archives documentaires YouTube")
    p.add_argument("--archives", type=Path, default=Path("archives"))
    sub = p.add_subparsers(dest="command", required=True)
    one = sub.add_parser("traiter"); one.add_argument("url"); one.add_argument("--modele", default="medium")
    batch = sub.add_parser("lot"); batch.add_argument("fichier", type=Path); batch.add_argument("--modele", default="medium")
    resume = sub.add_parser("reprendre"); resume.add_argument("url"); resume.add_argument("--modele", default="medium")
    status = sub.add_parser("verifier"); status.add_argument("video_id", nargs="?")
    export = sub.add_parser("exporter-index"); export.add_argument("video_id"); export.add_argument("--sortie", type=Path)
    rebuild = sub.add_parser("regenerer-index"); rebuild.add_argument("video_id"); rebuild.add_argument("--importer", type=Path)
    synthesis = sub.add_parser("exporter-synthese"); synthesis.add_argument("video_id"); synthesis.add_argument("--sortie", type=Path)
    rebuild_synthesis = sub.add_parser("regenerer-synthese"); rebuild_synthesis.add_argument("video_id"); rebuild_synthesis.add_argument("--importer", type=Path)
    quality = sub.add_parser("exporter-controle"); quality.add_argument("video_id"); quality.add_argument("--sortie", type=Path)
    review = sub.add_parser("relire-synthese"); review.add_argument("video_id"); review.add_argument("--importer", type=Path); review.add_argument("--sortie", type=Path)
    migrate = sub.add_parser("migrer-archive"); migrate.add_argument("video_id")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command in {"traiter", "reprendre"}:
            directory = process(args.url, args.archives, args.modele)
            print(directory)
            offer_quality_review(directory)
            return 0
        if args.command == "lot":
            for url, result in process_file(args.fichier, args.archives, args.modele): print(f"{url}\t{result}")
            return 0
        if args.command == "verifier":
            dirs = [directory_for(args.archives, args.video_id)] if args.video_id else list(args.archives.glob("*/*/*_*"))
            reports = [verify_archive(path) for path in dirs]
            print(json.dumps(reports, ensure_ascii=False, indent=2)); return 0 if all(r["complete"] for r in reports) else 1
        directory = directory_for(args.archives, args.video_id)
        if args.command == "migrer-archive":
            operations = migrate_archive_layout(directory)
            print(json.dumps(operations, ensure_ascii=False, indent=2)); return 0
        if args.command == "exporter-index" or (args.command == "regenerer-index" and not args.importer):
            print(export_prompt(directory, getattr(args, "sortie", None))); return 0
        if args.command == "regenerer-index":
            import_index(directory, args.importer)
            state = load_state(directory, args.video_id); set_step(directory, state, "index", "complete", source=str(args.importer))
            print(directory / "index_video.json"); return 0
        if args.command == "exporter-synthese" or (args.command == "regenerer-synthese" and not args.importer):
            print(export_synthesis_prompt(directory, getattr(args, "sortie", None))); return 0
        if args.command == "regenerer-synthese":
            import_synthesis(directory, args.importer)
            state = load_state(directory, args.video_id); set_step(directory, state, "synthesis", "complete", source=str(args.importer))
            print(directory / "synthese_video.md"); return 0
        if args.command == "exporter-controle" or (args.command == "relire-synthese" and not args.importer):
            prompt = export_quality_prompt(directory, getattr(args, "sortie", None))
            state = load_state(directory, args.video_id)
            set_step(directory, state, "quality_control", "waiting_manual", prompt=prompt.name, optional=True)
            print(prompt); return 0
        try:
            result = import_review(directory, args.importer)
        except PrometheError as exc:
            state = load_state(directory, args.video_id)
            set_step(directory, state, "quality_control", "failed", error=str(exc),
                     source=str(args.importer), optional=True)
            raise
        state = load_state(directory, args.video_id)
        set_step(directory, state, "quality_control", "complete", source=str(args.importer),
                 report="rapport_controle_qualite.md", synthesis_changed=result["changed"], backup=result["backup"])
        print(directory / "rapport_controle_qualite.md"); return 0
    except PrometheError as exc:
        print(f"Erreur : {exc}", file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
