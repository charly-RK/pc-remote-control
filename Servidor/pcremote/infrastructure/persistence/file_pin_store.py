"""PIN persistence in a small JSON file."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class FilePinStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> str | None:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, ValueError):
            logger.warning("PIN file is unreadable or corrupt; ignoring it")
            return None
        pin = data.get("pin") if isinstance(data, dict) else None
        return pin if isinstance(pin, str) and pin else None

    def save(self, pin: str) -> None:
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_text(json.dumps({"pin": pin}), encoding="utf-8")
            os.replace(tmp_path, self._path)
        except OSError:
            logger.warning("Could not persist the PIN", exc_info=True)

    def clear(self) -> None:
        try:
            self._path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove the PIN file", exc_info=True)
