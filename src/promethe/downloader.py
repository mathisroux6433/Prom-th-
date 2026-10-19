from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .errors import PrometheError


def _ydl_class():
    try:
        from yt_dlp import YoutubeDL
    except ImportError as exc:
        raise PrometheError("yt-dlp manque dans cet environnement Python. Consultez README.md.") from exc
    return YoutubeDL


def ffmpeg_location() -> str | None:
    """Réutilise FFmpeg du PATH ou, sous Windows, celui fourni par Krita."""
    executable = shutil.which("ffmpeg")
    if executable:
        return str(Path(executable).parent)
    krita = Path(r"C:\Program Files\Krita (x64)\bin\ffmpeg.exe")
    companion = krita.with_name("ffprobe.exe")
    return str(krita.parent) if krita.is_file() and companion.is_file() else None


def inspect_url(url: str) -> dict[str, Any]:
    with _ydl_class()({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("_type") == "playlist":
        raise PrometheError("Une URL de vidéo unique est requise (playlist refusée).")
    return info


def inspect_playlist(url: str) -> list[str]:
    """Retourne les URL canoniques d'une playlist sans télécharger de média."""
    options = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": True}
    with _ydl_class()(options) as ydl:
        info = ydl.extract_info(url, download=False)
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


def download_audio(url: str, directory: Path) -> Path:
    template = str(directory / "audio.%(ext)s")
    options = {
        "format": "bestaudio/best", "outtmpl": template, "noplaylist": True,
        "quiet": False, "overwrites": False,
    }
    if location := ffmpeg_location():
        options["ffmpeg_location"] = location
    with _ydl_class()(options) as ydl:
        ydl.download([url])
    files = [p for p in directory.glob("audio.*") if p.suffix not in {".part", ".ytdl"}]
    if not files:
        raise PrometheError("yt-dlp n'a produit aucun fichier audio.")
    return files[0]
