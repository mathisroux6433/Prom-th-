import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from promethe.archive import archive_path, verify_archive
from promethe.cli import offer_quality_review
from promethe.downloader import ffmpeg_location
from promethe.indexer import INDEX_KEYS, export_prompt, import_index
from promethe.io_utils import timestamp, write_json, write_text
from promethe.layout import ensure_archive_layout, migrate_archive_layout
from promethe.nvidia_runtime import configure_nvidia_dlls
from promethe.pipeline import process
from promethe.quality import export_prompt as export_quality_prompt, import_review
from promethe.state import load_state
from promethe.synthesizer import export_prompt as export_synthesis_prompt, import_synthesis


class CoreTests(unittest.TestCase):
    def test_nvidia_runtime_configuration_is_idempotent(self):
        first = configure_nvidia_dlls()
        second = configure_nvidia_dlls()
        self.assertEqual(first, second)

    @patch("promethe.downloader.shutil.which", return_value="C:/tools/ffmpeg.exe")
    def test_ffmpeg_path_is_reused(self, _which):
        self.assertEqual(ffmpeg_location(), "C:\\tools")

    def test_archive_path_and_timestamp(self):
        path = archive_path(Path("archives"), {"id": "abc-12", "channel": "Chaîne / test", "upload_date": "20240102"})
        self.assertEqual(path, Path("archives/Chaîne_test/2024/2024-01-02_abc-12"))
        self.assertEqual(timestamp(3661.2344), "01:01:01.234")

    def test_verify_reports_missing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_json(directory / "metadata.json", {})
            ensure_archive_layout(directory)
            report = verify_archive(directory)
            self.assertFalse(report["complete"])
            self.assertTrue(report["files"]["metadata.json"])
            self.assertFalse(report["files"]["segments.json"])

    def test_index_export_and_validated_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_json(directory / "metadata.json", {"id": "vid", "title": "Titre"})
            write_text(directory / "transcription_corrigee.txt", "[00:00:00.000 --> 00:00:01.000] Bonjour\n")
            prompt = export_prompt(directory)
            self.assertIn("Bonjour", prompt.read_text(encoding="utf-8"))
            data = {key: [] for key in INDEX_KEYS}
            data.update(schema_version="1.0", video_id="vid", resume_general="Résumé")
            source = directory / "response.json"
            write_json(source, data)
            import_index(directory, source)
            self.assertEqual(json.loads((directory / "index_video.json").read_text(encoding="utf-8"))["video_id"], "vid")

    def test_synthesis_export_and_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_json(directory / "metadata.json", {"id": "vid", "title": "Titre"})
            write_text(directory / "transcription_corrigee.txt", "[00:00:00.000 --> 00:00:01.000] Bonjour\n")
            write_json(directory / "index_video.json", {"video_id": "vid", "resume_general": "Sujet"})
            prompt = export_synthesis_prompt(directory)
            self.assertIn("Bonjour", prompt.read_text(encoding="utf-8"))
            source = directory / "response.md"
            write_text(source, "# Titre\n\n## Objet\n\n" + "Synthèse documentaire. " * 20)
            import_synthesis(directory, source)
            self.assertTrue((directory / "synthese_video.md").is_file())

    def test_old_state_gains_pending_synthesis_step(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_json(directory / "etat_pipeline.json", {
                "schema_version": "1.0", "video_id": "vid", "steps": {"index": {"status": "complete", "error": None}}
            })
            state = load_state(directory, "vid")
            self.assertEqual(state["steps"]["synthesis"]["status"], "pending")
            self.assertEqual(state["steps"]["quality_control"]["status"], "pending")

    def test_quality_review_exports_imports_reports_and_backs_up(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_json(directory / "metadata.json", {"id": "vid", "title": "Titre"})
            write_text(directory / "transcription_corrigee.txt", "[00:00:00.000 --> 00:00:01.000] Le chiffre est 42.\n")
            write_json(directory / "index_video.json", {"video_id": "vid", "resume_general": "Le chiffre est 42."})
            original = "# Titre\n\n## Objet\n\n" + "Le chiffre est 41. " * 20 + "\n"
            revised = original.replace("41", "42")
            write_text(directory / "synthese_video.md", original)
            prompt = export_quality_prompt(directory)
            self.assertIn("Le chiffre est 42", prompt.read_text(encoding="utf-8"))
            response = directory / "review.json"
            write_json(response, {
                "schema_version": "1.0", "video_id": "vid", "verdict": "corrigee",
                "problems": [{
                    "category": "chiffre", "severity": "importante",
                    "description": "Valeur incorrecte.", "source_evidence": "La transcription indique 42.",
                    "timestamp": "00:00:00", "correction": "41 remplacé par 42.",
                }],
                "revised_synthesis": revised,
            })
            result = import_review(directory, response)
            self.assertTrue(result["changed"])
            backup = directory / "historique" / "anciennes_versions" / "synthese_video_avant_relecture.md"
            self.assertEqual(backup.read_text(encoding="utf-8"), original)
            self.assertIn("Le chiffre est 42", (directory / "synthese_video.md").read_text(encoding="utf-8"))
            self.assertIn("Valeur incorrecte", (directory / "rapport_controle_qualite.md").read_text(encoding="utf-8"))

    def test_quality_review_resolves_file_reference_next_to_response(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_json(directory / "metadata.json", {"id": "vid"})
            original = "# Titre\n\n## Version initiale\n\n" + "Texte initial. " * 20 + "\n"
            revised = "# Titre\n\n## Version relue\n\n" + "Texte corrigé. " * 20 + "\n"
            write_text(directory / "synthese_video.md", original)
            write_text(directory / "synthese_relue_candidate.md", revised)
            response = directory / "response.json"
            write_json(response, {
                "schema_version": "1.0", "video_id": "vid", "verdict": "corrigee",
                "problems": [], "revised_synthesis": "@file:synthese_relue_candidate.md",
            })
            result = import_review(directory, response)
            self.assertTrue(result["changed"])
            self.assertEqual((directory / "synthese_video.md").read_text(encoding="utf-8"), revised.strip() + "\n")

    def test_default_prompts_use_work_requests_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_json(directory / "metadata.json", {"id": "vid"})
            write_text(directory / "transcription_corrigee.txt", "Bonjour")
            self.assertEqual(
                export_prompt(directory),
                directory / "travail" / "requetes" / "requete_indexation.txt",
            )

    def test_layout_is_created_when_resuming_an_old_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            ensure_archive_layout(directory)
            report = verify_archive(directory)
            self.assertTrue(all(report["layout"].values()))

    def test_migration_validates_and_rehomes_temporary_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_text(directory / "requete_indexation.txt", "prompt")
            write_text(directory / "synthese_video_avant_relecture.md", "ancienne")
            write_json(directory / "etat_pipeline.json", {
                "steps": {"quality_control": {"backup": str(directory / "synthese_video_avant_relecture.md")}}
            })
            operations = migrate_archive_layout(directory)
            self.assertEqual(len(operations), 2)
            self.assertFalse((directory / "requete_indexation.txt").exists())
            self.assertEqual(
                (directory / "travail" / "requetes" / "requete_indexation.txt").read_text(encoding="utf-8"),
                "prompt",
            )
            self.assertTrue(
                (directory / "historique" / "anciennes_versions" / "synthese_video_avant_relecture.md").is_file()
            )
            state = json.loads((directory / "etat_pipeline.json").read_text(encoding="utf-8"))
            self.assertEqual(
                state["steps"]["quality_control"]["backup"],
                "historique/anciennes_versions/synthese_video_avant_relecture.md",
            )

    @patch("builtins.input", return_value="Plus tard")
    def test_interactive_quality_review_can_be_deferred(self, _input):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_json(directory / "metadata.json", {"id": "vid"})
            write_text(directory / "synthese_video.md", "# Synthèse\n")
            offer_quality_review(directory)
            state = load_state(directory, "vid")
            self.assertEqual(state["steps"]["quality_control"]["status"], "pending")
            self.assertEqual(state["steps"]["quality_control"]["note"], "Relecture reportée")

    @patch("promethe.pipeline.inspect_url")
    def test_resume_stops_before_completed_work(self, inspect):
        inspect.return_value = {"id": "v1", "title": "T", "channel": "C", "upload_date": "20230101", "webpage_url": "u"}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = process("u", root, stop_after="metadata")
            original = (first / "metadata.json").read_text(encoding="utf-8")
            second = process("u", root, stop_after="metadata")
            self.assertEqual(first, second)
            self.assertEqual((second / "metadata.json").read_text(encoding="utf-8"), original)



if __name__ == "__main__":
    unittest.main()
