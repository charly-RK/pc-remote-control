"""Application settings persisted in a JSON file."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, fields
from pathlib import Path

from pcremote.domain.errors import ExecutionError
from pcremote.domain.settings import AppSettings
from pcremote.infrastructure.persistence._atomic import write_json_atomic

logger = logging.getLogger(__name__)


class FileSettingsStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> AppSettings:
        defaults = AppSettings()
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return defaults
        except (OSError, ValueError):
            logger.warning("Settings file is unreadable or corrupt; using defaults")
            return defaults
        if not isinstance(raw, dict):
            return defaults
        values = {}
        for field in fields(AppSettings):
            value = raw.get(field.name)
            if isinstance(value, type(getattr(defaults, field.name))):
                values[field.name] = value
        return AppSettings(**values)

    def save(self, settings: AppSettings) -> None:
        try:
            write_json_atomic(self._path, asdict(settings))
        except OSError as exc:
            raise ExecutionError(f"Could not persist settings: {exc}") from exc
