from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import PrometheError
from .io_utils import timestamp, write_json, write_text
from .nvidia_runtime import configure_nvidia_dlls


def transcribe(audio: Path, directory: Path, model_name: str = "medium") -> dict[str, Any]:
    configure_nvidia_dlls()
    try:
        from faster_whisper import WhisperModel
        from ctranslate2 import get_cuda_device_count
    except ImportError as exc:
        raise PrometheError("faster-whisper/CTranslate2 manque. Aucun repli CPU n'est autorisé.") from exc
    if get_cuda_device_count() < 1:
        raise PrometheError("CUDA est indisponible pour CTranslate2 ; transcription arrêtée, sans repli CPU.")

    model = WhisperModel(model_name, device="cuda", compute_type="float16")
    iterable, info = model.transcribe(str(audio), language="fr", vad_filter=True, beam_size=5)
    segments = []
    for number, segment in enumerate(iterable):
        segments.append({
            "id": number, "start": round(segment.start, 3), "end": round(segment.end, 3),
            "start_timestamp": timestamp(segment.start), "end_timestamp": timestamp(segment.end),
            "text": segment.text.strip(),
        })
    document = {
        "schema_version": "1.0", "engine": "faster-whisper", "model": model_name,
        "language": info.language, "language_probability": info.language_probability,
        "segments": segments,
    }
    write_json(directory / "segments.json", document)
    text = "\n".join(f"[{s['start_timestamp']} --> {s['end_timestamp']}] {s['text']}" for s in segments) + "\n"
    write_text(directory / "transcription_brute.txt", text)
    return document
