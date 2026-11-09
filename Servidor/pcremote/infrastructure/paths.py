"""Filesystem locations for user data and bundled resources."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "PCRemoteControl"


def app_data_dir() -> Path:
    """Return the per-user data directory, creating it when missing."""
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    path = root / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def resource_path(relative: str) -> Path:
    """Resolve a bundled resource path (PyInstaller aware)."""
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        base = Path(bundle_dir)
    else:
        # .../Servidor/pcremote/infrastructure/paths.py -> .../Servidor
        base = Path(__file__).resolve().parents[2]
    return base / relative
