from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TypeVar
from urllib.parse import parse_qs, quote, urlparse

from .errors import PrometheError


DENO_ARCHIVE_URL = (
    "https://github.com/denoland/deno/releases/latest/download/"
    "deno-x86_64-pc-windows-msvc.zip"
)
DENO_CHECKSUM_URL = f"{DENO_ARCHIVE_URL}.sha256sum"
_BLOCK_MARKERS = (
    "sign in to confirm", "not a bot", "page needs to be reloaded",
    "no video formats found", "only images are available",
    "requested format is not available", "javascript runtime",
)
T = TypeVar("T")


@dataclass(frozen=True)
class YoutubeAccess:
    """Configuration du repli YouTube authentifié, sans stocker de cookie."""

    browser: str | None = "firefox"
    javascript_runtime: Path | None = None


def _ydl_class():
    try:
        from yt_dlp import YoutubeDL
    except ImportError as exc:
        raise PrometheError("yt-dlp manque dans cet environnement Python. Consultez README.md.") from exc
    return YoutubeDL


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ffmpeg_location() -> str | None:
    """Réutilise FFmpeg du PATH ou, sous Windows, celui fourni par Krita."""
    executable = shutil.which("ffmpeg")
    if executable:
        return str(Path(executable).parent)
    krita = Path(r"C:\Program Files\Krita (x64)\bin\ffmpeg.exe")
    companion = krita.with_name("ffprobe.exe")
    return str(krita.parent) if krita.is_file() and companion.is_file() else None


def youtube_video_id(url: str) -> str | None:
    """Extrait sans réseau l'identifiant d'une URL YouTube usuelle."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":", 1)[0]
    if host in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.strip("/").split("/", 1)[0]
    elif host.endswith("youtube.com"):
        if parsed.path == "/watch":
            candidate = (parse_qs(parsed.query).get("v") or [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            candidate = parsed.path.strip("/").split("/", 1)[1].split("/", 1)[0]
        else:
            return None
    else:
        return None
    return candidate if re.fullmatch(r"[A-Za-z0-9_-]{6,}", candidate) else None


def canonical_playlist_url(url: str) -> str:
    """Normalise une URL watch/short youtu.be contenant un identifiant de playlist."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":", 1)[0]
    playlist_id = (parse_qs(parsed.query).get("list") or [None])[0]
    if playlist_id and (host.endswith("youtube.com") or host in {"youtu.be", "www.youtu.be"}):
        return f"https://www.youtube.com/playlist?list={quote(playlist_id, safe='')}"
    return url


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_javascript_runtime(requested: Path | None = None) -> Path:
    """Trouve Deno ou installe sa distribution Windows officielle après contrôle SHA-256."""
    if requested:
        executable = requested.expanduser().resolve()
        if not executable.is_file():
            raise PrometheError(f"Runtime JavaScript introuvable : {executable}")
        return executable
    if executable := shutil.which("deno"):
        return Path(executable)
    destination = project_root() / ".runtime" / "deno" / "deno.exe"
    if destination.is_file():
        return destination
    if os.name != "nt":
        raise PrometheError("Deno est requis pour le repli YouTube et doit être installé dans le PATH.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="promethe-deno-") as temporary:
            temporary_path = Path(temporary)
            archive = temporary_path / "deno.zip"
            checksum = temporary_path / "deno.zip.sha256sum"
            urllib.request.urlretrieve(DENO_ARCHIVE_URL, archive)
            urllib.request.urlretrieve(DENO_CHECKSUM_URL, checksum)
            checksum_text = checksum.read_text(encoding="utf-8", errors="replace")
            matches = re.findall(r"\b[0-9a-fA-F]{64}\b", checksum_text)
            if not matches or _sha256(archive).lower() != matches[0].lower():
                raise PrometheError("Le contrôle SHA-256 du runtime Deno a échoué.")
            with zipfile.ZipFile(archive) as bundle:
                member = next((name for name in bundle.namelist() if Path(name).name == "deno.exe"), None)
                if not member:
                    raise PrometheError("L'archive officielle Deno ne contient pas deno.exe.")
                staging = destination.with_suffix(".tmp")
                with bundle.open(member) as source, staging.open("wb") as target:
                    shutil.copyfileobj(source, target)
                staging.replace(destination)
    except PrometheError:
        raise
    except Exception as exc:
        raise PrometheError(f"Impossible de préparer automatiquement Deno : {exc}") from exc
    return destination


def _needs_authenticated_retry(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in _BLOCK_MARKERS)


def _authenticated_options(access: YoutubeAccess) -> dict[str, Any]:
    if not access.browser:
        return {}
    runtime = ensure_javascript_runtime(access.javascript_runtime)
    return {
        "cookiesfrombrowser": (access.browser,),
        "js_runtimes": {"deno": {"path": str(runtime)}},
        "remote_components": {"ejs:github"},
        "extractor_args": {"youtube": {"player_client": ["web_safari"]}},
    }


def _with_fallback(operation: Callable[[dict[str, Any]], T], access: YoutubeAccess | None) -> T:
    try:
        return operation({})
    except Exception as exc:
        access = access or YoutubeAccess()
        if not access.browser or not _needs_authenticated_retry(exc):
            raise
        print(
            "YouTube demande une authentification : nouvel essai automatique avec les cookies Firefox.",
            file=sys.stderr,
        )
        return operation(_authenticated_options(access))


def inspect_url(url: str, access: YoutubeAccess | None = None) -> dict[str, Any]:
    def extract(extra: dict[str, Any]) -> dict[str, Any]:
        options = {"quiet": True, "no_warnings": True, "skip_download": True, **extra}
        with _ydl_class()(options) as ydl:
            return ydl.extract_info(url, download=False)

    info = _with_fallback(extract, access)
    if info.get("_type") == "playlist":
        raise PrometheError("Une URL de vidéo unique est requise (playlist refusée).")
    return info


def inspect_playlist(url: str, access: YoutubeAccess | None = None) -> list[str]:
    """Retourne les URL canoniques d'une playlist sans télécharger de média."""
    url = canonical_playlist_url(url)
    def extract(extra: dict[str, Any]) -> dict[str, Any]:
        options = {
            "quiet": True, "no_warnings": True, "skip_download": True,
            "extract_flat": True, **extra,
        }
        with _ydl_class()(options) as ydl:
            return ydl.extract_info(url, download=False)

    info = _with_fallback(extract, access)
    if info.get("_type") != "playlist":
        raise PrometheError("Une URL de playlist est requise.")
    urls = []
    for entry in info.get("entries") or []:
        if not entry:
            continue
        video_id = entry.get("id")
        webpage_url = entry.get("webpage_url") or entry.get("url")
        if webpage_url and str(webpage_url).startswith("http"):
            urls.append(str(webpage_url))
        elif video_id:
            urls.append(f"https://www.youtube.com/watch?v={video_id}")
    if not urls:
        raise PrometheError("La playlist ne contient aucune vidéo exploitable.")
    return urls


def normalized_metadata(info: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0", "id": info["id"], "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "channel_id": info.get("channel_id") or info.get("uploader_id"),
        "upload_date": info.get("upload_date"), "duration_seconds": info.get("duration"),
        "webpage_url": info.get("webpage_url") or info.get("original_url"),
        "description": info.get("description"), "language": info.get("language"),
    }


def download_audio(url: str, directory: Path, access: YoutubeAccess | None = None) -> Path:
    template = str(directory / "audio.%(ext)s")

    def download(extra: dict[str, Any]) -> None:
        authenticated = bool(extra)
        options: dict[str, Any] = {
            "format": "bestaudio/18/best[height<=360]/best" if authenticated else "bestaudio/best",
            "outtmpl": template, "noplaylist": True, "quiet": False, "overwrites": False,
            **extra,
        }
        if location := ffmpeg_location():
            options["ffmpeg_location"] = location
        if authenticated:
            options["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "m4a"}]
        with _ydl_class()(options) as ydl:
            ydl.download([url])

    _with_fallback(download, access)
    files = [p for p in directory.glob("audio.*") if p.suffix not in {".part", ".ytdl"}]
    if not files:
        raise PrometheError("yt-dlp n'a produit aucun fichier audio.")
    return files[0]
