"""Paired devices persisted in a JSON file. Token hashes are never logged."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, replace
from pathlib import Path

from pcremote.domain.devices import PairedDevice
from pcremote.domain.errors import ExecutionError
from pcremote.infrastructure.persistence._atomic import write_json_atomic

logger = logging.getLogger(__name__)


class FileDeviceRepository:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._devices: dict[str, PairedDevice] = self._read()

    def list(self) -> list[PairedDevice]:
        with self._lock:
            return list(self._devices.values())

    def find_by_token_hash(self, token_hash: str) -> PairedDevice | None:
        with self._lock:
            return next((d for d in self._devices.values() if d.token_hash == token_hash), None)

    def add(self, device: PairedDevice) -> None:
        with self._lock:
            self._devices[device.device_id] = device
            self._write()

    def remove(self, device_id: str) -> bool:
        with self._lock:
            if self._devices.pop(device_id, None) is None:
                return False
            self._write()
            return True

    def touch(self, device_id: str, timestamp: float) -> None:
        with self._lock:
            device = self._devices.get(device_id)
            if device is None:
                return
            self._devices[device_id] = replace(device, last_seen=timestamp)
            self._write()

    def _read(self) -> dict[str, PairedDevice]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            logger.warning("Paired devices file is unreadable or corrupt; starting empty")
            return {}
        devices: dict[str, PairedDevice] = {}
        for item in raw if isinstance(raw, list) else []:
            try:
                device = PairedDevice(
                    device_id=str(item["device_id"]),
                    name=str(item["name"]),
                    token_hash=str(item["token_hash"]),
                    created_at=float(item["created_at"]),
                    last_seen=float(item["last_seen"]),
                )
            except (KeyError, TypeError, ValueError):
                logger.warning("Skipping an invalid paired device entry")
                continue
            devices[device.device_id] = device
        return devices

    def _write(self) -> None:
        try:
            write_json_atomic(self._path, [asdict(d) for d in self._devices.values()])
        except OSError as exc:
            raise ExecutionError(f"Could not persist paired devices: {exc}") from exc
