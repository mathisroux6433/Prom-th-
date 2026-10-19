"""Chargement isolé des DLL NVIDIA installées dans l'environnement Python."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_DLL_HANDLES: list[object] = []
_PATH_CONFIGURED = False


def configure_nvidia_dlls() -> list[Path]:
    """Ajoute les roues NVIDIA de ``sys.prefix`` à ce seul processus Windows.

    Les handles doivent rester vivants : leur fermeture retirerait les dossiers
    du chemin de recherche des DLL. Le PATH utilisateur/système n'est pas modifié.
    """
    if os.name != "nt":
        return []
    root = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    directories = [
        root / "cublas" / "bin",
        root / "cudnn" / "bin",
        root / "cuda_nvrtc" / "bin",
    ]
    available = [path for path in directories if path.is_dir()]
    global _PATH_CONFIGURED
    if not _DLL_HANDLES:
        _DLL_HANDLES.extend(os.add_dll_directory(str(path)) for path in available)
    if available and not _PATH_CONFIGURED:
        # CTranslate2 charge certaines DLL par leur nom avec LoadLibrary. Sous
        # Windows, ce chemin consulte le PATH du processus mais pas toujours les
        # répertoires ajoutés via AddDllDirectory.
        os.environ["PATH"] = os.pathsep.join(map(str, available)) + os.pathsep + os.environ.get("PATH", "")
        _PATH_CONFIGURED = True
    return available
